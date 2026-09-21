import threading
import time
import os
import uuid
from tracker_manager import TrackerManager, categorize_site
from automation.image_hosts import upload_image_to_site, create_text_banner_image
from automation.paste_hosts import upload_text_to_site
from automation.cloud_storage import upload_cloud_file
from automation.browser_human import HumanBrowserAutomation
from site_inspector import inspect_single_site, inspect_single_site_fast

# Global active job tracker
ACTIVE_JOBS = {}

def get_default_user_data_dir():
    """Menggunakan profil khusus robot di dalam folder project agar tidak diblokir Chrome security."""
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    return os.path.join(project_dir, "BotProfile")

import subprocess
import socket
import glob
import json

def get_profile_directory_by_name(display_name="Default"):
    return display_name

def is_cdp_active(port=9222):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.5):
            return True
    except OSError:
        return False



def find_chrome_executable():
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def launch_browser_safely(p, headless=False, use_persistent_session=False, profile_name="Profile 1"):
    """
    Launches browser trying default chromium, system msedge, or system chrome.
    If use_persistent_session is True, attempts to launch Chrome via CDP 
    (Chrome DevTools Protocol) to fully bypass anti-bot and reuse native sessions.
    """
    user_data_dir = get_default_user_data_dir()
    
    if use_persistent_session and user_data_dir:
        chrome_path = find_chrome_executable()
        if chrome_path:
            # 1. Check if Chrome CDP is already running
            if is_cdp_active(9222):
                print("CDP already active on 9222. Connecting...", flush=True)
                return p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            # 2. Launch Chrome manually with CDP port
            print("Launching Chrome via subprocess with CDP port 9222...", flush=True)
            actual_profile_dir = get_profile_directory_by_name(profile_name)
            cmd = [
                chrome_path,
                "--remote-debugging-port=9222",
                f"--user-data-dir={user_data_dir}",
                f"--profile-directory={actual_profile_dir}",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            # Playwright handles maximized visually better when not headless, but we pass standard args
            if headless:
                cmd.append("--headless")
            else:
                cmd.append("--start-maximized")
                
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 3. Wait and connect
            for _ in range(15):
                time.sleep(1)
                if is_cdp_active(9222):
                    print("CDP Connection established!", flush=True)
                    return p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            
            print("Warning: Failed to connect to CDP after launching Chrome. Falling back to default Playwright launch.", flush=True)

    print("Executing fallback to standard Playwright launch...", flush=True)
    for channel in [None, "msedge", "chrome"]:
        kwargs = {
            "headless": headless,
            "args": [
                "--start-maximized", 
                "--disable-blink-features=AutomationControlled",
            ]
        }
        if use_persistent_session:
            actual_profile_dir = get_profile_directory_by_name(profile_name)
            kwargs["args"].append(f"--profile-directory={actual_profile_dir}")
            
        if channel:
            kwargs["channel"] = channel
            
        try:
            if use_persistent_session and user_data_dir:
                return p.chromium.launch_persistent_context(user_data_dir, **kwargs)
            else:
                return p.chromium.launch(**kwargs)
        except Exception as e:
            # If persistent session fails (likely due to browser already running and profile locked),
            # fallback to non-persistent session for the same channel.
            safe_error = str(e).encode('ascii', 'replace').decode('ascii')
            if use_persistent_session:
                print(f"Fallback warning: Persistent session locked or failed for channel={channel}. Trying non-persistent... Error: {safe_error}", flush=True)
                try:
                    return p.chromium.launch(**kwargs)
                except Exception as inner_e:
                    safe_inner = str(inner_e).encode('ascii', 'replace').decode('ascii')
                    print(f"Fallback warning: Non-persistent launch also failed for channel={channel}. Error: {safe_inner}", flush=True)
            continue
            
    raise RuntimeError("Could not launch Chromium, Edge, or Chrome browser.")

class BatchUploadJob:
    def __init__(self, job_id, campaign_name, target_sites, payload, tracker_manager=None):
        self.job_id = job_id
        self.campaign_name = campaign_name
        self.target_sites = target_sites
        self.payload = payload  # {title, content_text, file_path, visible_browser, tokens}
        self.tracker_manager = tracker_manager or TrackerManager()
        
        self.status = "INITIALIZING" # RUNNING, COMPLETED, FAILED
        self.total = len(target_sites)
        self.completed = 0
        self.success_count = 0
        self.fail_count = 0
        self.logs = []
        self.results = {}  # {situs_domain: link_url}
        self.current_site = None
        self.current_tier = None
        self.thread = None

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        log_str = f"[{timestamp}] {message}"
        self.logs.append(log_str)
        print(log_str)

    def start(self):
        self.status = "RUNNING"
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        # Sort target sites to prioritize 🟢 MUDAH (Direct API) sites first!
        sites_info = [inspect_single_site_fast(s) for s in self.target_sites]
        tier_priority = {"Mudah": 1, "Sedang": 2, "Sulit": 3}
        sites_info.sort(key=lambda s: (tier_priority.get(s['tier'], 9), s['situs']))
        
        ordered_sites = [s['situs'] for s in sites_info]

        visible_browser = self.payload.get('visible_browser', True)
        browser_mode_str = "👁️ Visible Headed Browser Window" if visible_browser else "⚡ Headless Background Mode"

        self.log(f"Starting batch upload for Campaign: '{self.campaign_name}' on {self.total} target platforms.")
        self.log(f"Execution Mode: {browser_mode_str} | Priority: 🟢 MUDAH -> 🟡 SEDANG -> 🔴 SULIT")

        title = self.payload.get('title', 'Auto Post Content')
        content_text = self.payload.get('content_text', '')
        file_path = self.payload.get('file_path')
        tokens = self.payload.get('tokens', {})

        human_browser = HumanBrowserAutomation()

        for idx, situs in enumerate(ordered_sites):
            category = categorize_site(situs)
            site_info = inspect_single_site_fast(situs)
            tier = site_info['tier']
            tier_badge = f"[{tier}]"
            self.current_site = situs
            self.current_tier = tier
            
            self.log(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            self.log(f"[{idx+1}/{self.total}] {tier_badge} Target: '{situs}' ({category})")
            
            if category == "Blacklisted":
                self.log("🛑 Site is BLACKLISTED. Skipping execution to save time.")
                self.fail_count += 1
                self.results.append({"site": situs, "status": "failed", "message": "Skipped (Blacklisted)"})
                continue
                
            self.log(f"⚙️ Selected Automation Strategy: {site_info['upload_method']}")
            
            success = False
            link = None
            msg = ""

            try:
                # -------------------------------------------------------------
                # 🟢 MUDAH (Direct API / Multipart Upload)
                # -------------------------------------------------------------
                if tier == "Mudah":
                    if category == "Image Host":
                        target_file = file_path
                        if not target_file or not os.path.exists(target_file):
                            target_file = create_text_banner_image(title, content_text)
                            self.log(f"🖼️ Auto-generated text banner image '{os.path.basename(target_file)}'")

                        if target_file and os.path.exists(target_file):
                            self.log(f"🚀 Sending direct API multipart upload to {situs}...")
                            success, link, msg = upload_image_to_site(situs, target_file)
                        else:
                            success, link, msg = False, None, "No image attachment available"
                    elif category == "Text / Paste Host":
                        self.log(f"🚀 Sending text payload to {situs} API...")
                        success, link, msg = upload_text_to_site(situs, title, content_text)
                    elif category == "Cloud Storage":
                        if file_path and os.path.exists(file_path):
                            self.log(f"🚀 Uploading cloud storage file to {situs}...")
                            success, link, msg = upload_cloud_file(situs, file_path)
                        else:
                            success, link, msg = upload_text_to_site(situs, title, content_text)
                    else:
                        success, link, msg = upload_text_to_site(situs, title, content_text)

                # -------------------------------------------------------------
                # 🟡 SEDANG & 🔴 SULIT (Universal Heuristics + Persistent Session)
                # -------------------------------------------------------------
                else:
                    # 🚦 URL Auto-Router (Mengarahkan homepage ke halaman Editor/Create Post)
                    auto_router = {
                        "medium.com": "https://medium.com/new-story",
                        "tumblr.com": "https://www.tumblr.com/new",
                        "wordpress.com": "https://wordpress.com/post",
                        "blogger.com": "https://www.blogger.com/post-create.g",
                        "hubspot.com": "https://app.hubspot.com/blog/new",
                        "livejournal.com": "https://www.livejournal.com/update.bml",
                        "weebly.com": "https://www.weebly.com/weebly/main.php",
                        "wix.com": "https://manage.wix.com/dashboard"
                    }
                    
                    target_url = situs
                    for domain, routed_url in auto_router.items():
                        if domain in situs.lower() and len(situs.split('/')) <= 4:
                            target_url = routed_url
                            self.log(f"🚦 URL Auto-Router aktif: Mengalihkan {situs} -> {target_url}")
                            break

                    try:
                        from playwright.sync_api import sync_playwright
                        with sync_playwright() as p:
                            self.log(f"🌐 Launching browser window (Visible: {visible_browser}, Persistent Session: True, Profile: 'BotProfile')...")
                            browser_or_context = launch_browser_safely(p, headless=not visible_browser, use_persistent_session=True, profile_name="BotProfile")
                            
                            if hasattr(browser_or_context, 'contexts') and browser_or_context.contexts:
                                context = browser_or_context.contexts[0]
                            elif hasattr(browser_or_context, 'new_page'): 
                                context = browser_or_context
                            else:
                                context = browser_or_context.new_context(viewport={'width': 1280, 'height': 800})
                            
                            pages = getattr(context, 'pages', [])
                            page = context.new_page()

                            success, link, msg = human_browser.run_human_form_fill(
                                page, target_url, title, content_text, file_path, log_fn=self.log
                            )
                            
                            # Close only the specific page we opened, so the main Chrome Robot stays open!
                            if hasattr(page, 'close'):
                                page.close()
                            
                            if hasattr(browser_or_context, 'disconnect'):
                                browser_or_context.disconnect()
                    except Exception as pe:
                        self.log(f"⚠️ Playwright Universal Heuristics error: {str(pe)}")
                        success = False
                        
                    if not success:
                        msg = "Failed in Playwright form automation."

            except Exception as e:
                success, link, msg = False, None, f"Execution exception: {str(e)}"

            self.completed += 1
            if success and link:
                self.success_count += 1
                self.results[situs] = link
                self.log(f"✅ SUCCESS [{situs}]: {link}")
            else:
                self.fail_count += 1
                self.log(f"❌ FAILED / SKIPPED [{situs}]: {msg}")

            time.sleep(0.5)

        self.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.log("📊 Updating campaign results back into tracker-posting.xlsx...")
        updated_rows = self.tracker_manager.update_batch_results(self.campaign_name, self.results)
        self.log(f"💾 Saved {updated_rows} generated links into Excel file!")
        
        self.status = "COMPLETED"
        self.log("🎉 Batch automation workflow completed successfully!")

def create_batch_job(campaign_name, target_sites, payload):
    job_id = str(uuid.uuid4())[:8]
    job = BatchUploadJob(job_id, campaign_name, target_sites, payload)
    ACTIVE_JOBS[job_id] = job
    job.start()
    return job_id
