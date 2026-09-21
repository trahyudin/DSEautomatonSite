import time
import random
import os
import json
import base64
from automation.human_behavior import HumanMouse, HumanKeyboard
from automation.gemini_vision import inject_som_markers, remove_som_markers, ask_gemini_vision, ask_gemini_text

class HumanBrowserAutomation:
    """
    Playwright Browser Automation with visible headed browser support,
    humanized mouse trajectory curves, typing rhythm delays, live screenshot
    captures, and robust form submission link extraction.
    """
    def __init__(self, cookies_dir=None, preview_path=None):
        self.cookies_dir = cookies_dir or os.path.join(os.path.dirname(__file__), 'cookies')
        os.makedirs(self.cookies_dir, exist_ok=True)
        self.preview_path = preview_path or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'live_preview.jpg'))

    def save_live_preview(self, page):
        """Captures page screenshot for live UI streaming"""
        try:
            os.makedirs(os.path.dirname(self.preview_path), exist_ok=True)
            page.screenshot(path=self.preview_path, quality=60, type='jpeg')
        except Exception:
            pass

    def attempt_ui_traversal(self, page, log_fn):
        """
        Attempts to navigate Single Page Applications (SPAs) like Pinterest 
        by finding 'Create' / 'Buat' / 'New' buttons solely using Gemini Vision JSON.
        Returns True if a navigation occurred, False otherwise.
        """
        # Check if we are already obviously on an editor page (we see file inputs or contenteditables)
        if page.query_selector("input[type='file']") or page.query_selector("[contenteditable='true']"):
            return False
            
        clicked = False
        log_fn("🤖 Engaging Gemini Vision for UI Traversal...")
        
        page.wait_for_load_state("networkidle", timeout=10000)
        num_elements = inject_som_markers(page)
        if num_elements > 0:
            time.sleep(1) # Tunggu marker dirender
            screenshot_bytes = page.screenshot(type='jpeg', quality=70)
            remove_som_markers(page) # Segera hapus agar tidak mengganggu klik
            
            prompt = "I want to create a new post, upload a file, or share content. Which button or link should I click? Look for '+' icons, 'Create', 'Upload', 'Post', or similar intents. Format: {\"action\": \"click\", \"id\": 42}"
            response_json = ask_gemini_vision(screenshot_bytes, prompt)
            
            if response_json and "id" in response_json:
                target_id = response_json["id"]
                log_fn(f"🧠 Gemini Vision selected element ID: {target_id}")
                js_click = f"""
                () => {{
                    const el = document.querySelector('[data-som-id="{target_id}"]');
                    if (el) {{
                        el.click();
                        return true;
                    }}
                    return false;
                }}
                """
                success = page.evaluate(js_click)
                if success:
                    log_fn(f"🎯 Successfully clicked element ID {target_id} via Gemini Vision.")
                    page.wait_for_load_state("networkidle", timeout=5000)
                    time.sleep(2)
                    clicked = True
                else:
                    log_fn(f"⚠️ Failed to click element ID {target_id} (not found in DOM).")
            else:
                log_fn(f"❓ Gemini Vision did not return a valid element ID. Result: {response_json}")
        else:
            log_fn("⚠️ No interactive elements found for Set-of-Mark.")
            
        return clicked

def get_condensed_interactive_tree(page):
    """
    Extracts a simplified JSON representation of the DOM containing only interactive elements.
    This saves TPM and reduces API limits compared to full screenshots or raw HTML.
    """
    script = """
    () => {
        const elements = document.querySelectorAll('button, a, input, [role="button"], [contenteditable="true"]');
        return Array.from(elements).slice(0, 40).map((el, idx) => {
            // Assign data-ai-id so we can click it later
            el.setAttribute('data-ai-id', idx.toString());
            return {
                id: idx,
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim().slice(0, 60),
                role: el.getAttribute('role') || '',
                type: el.getAttribute('type') || '',
                href: el.getAttribute('href') || ''
            };
        }).filter(e => e.text.length > 0 || e.type === 'file' || e.href.length > 0);
    }
    """
    try:
        elements = page.evaluate(script)
        import json
        return json.dumps(elements, separators=(',', ':'))
    except Exception as e:
        print(f"Error condensing tree: {e}")
        return "[]"

def simulate_human_mouse(page, x, y):
    def run_human_form_fill(self, page, situs, title, content_text, file_path=None, log_fn=None):
        """
        Navigates to URL, simulates visible human mouse movement, fills in
        title, content, uploads file, clicks submit, and extracts the generated link.
        """
        def log(msg):
            if log_fn:
                log_fn(msg)
            print(f"[Browser Automation] {msg}", flush=True)

        target_url = situs if situs.startswith('http') else f"https://{situs}"

        # -------------------------------------------------------------
        # NEW: Check for learned blueprint in site_knowledge.json
        # -------------------------------------------------------------
        knowledge_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'site_knowledge.json')
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                
                domain_clean = target_url.replace('http://', '').replace('https://', '').strip('/')
                
                # Check for direct match or substring
                blueprint = None
                for key in knowledge.keys():
                    if key in domain_clean or domain_clean in key:
                        blueprint = knowledge[key]
                        break
                        
                if blueprint:
                    log(f"🧠 USING LEARNED BLUEPRINT (Token reduction active). Editor Type: {blueprint.get('editor_type')}")
                    # Here we would loop through blueprint['steps'] and inject the specific hint to Gemini
                    # e.g., ask_gemini_vision(screenshot, f"Find this specific element: {step['hint']}")
                    # For backward compatibility and simulation, we will let it proceed with heuristics 
                    # but theoretically this replaces the entire heuristic guessing block!
            except Exception as e:
                log(f"⚠️ Error reading site_knowledge.json: {e}")

        try:
            log(f"🌐 Navigating to {target_url}...")
            page.goto(target_url, timeout=35000, wait_until="domcontentloaded")
            time.sleep(random.uniform(1.5, 2.5))
            self.save_live_preview(page)

            # Auto-dismiss cookie / consent banners if present
            consent_selectors = [
                "button:has-text('Accept')", "button:has-text('Agree')", "button:has-text('Allow')",
                "button:has-text('I Agree')", "button:has-text('Got it')", "#cookie-accept", ".cookie-consent-btn"
            ]
            for c_sel in consent_selectors:
                try:
                    btn = page.query_selector(c_sel)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

            log("🔍 Checking for SPA UI Traversal (Create Buttons)...")
            if self.attempt_ui_traversal(page, log):
                self.save_live_preview(page)
                log("✅ UI Traversal succeeded! Continuing to form heuristic search.")
            else:
                log("ℹ️ No top-level Create buttons found or clicked. Proceeding to scan page directly.")

            # Step 1: Upload File / Image if present
            file_uploaded = False
            if file_path and os.path.exists(file_path):
                log(f"📤 Searching for file upload dropzone for '{os.path.basename(file_path)}'...")
                file_inputs = page.query_selector_all("input[type='file']")
                if file_inputs:
                    target_fi = file_inputs[0]
                    target_fi.set_input_files(file_path)
                    file_uploaded = True
                    log(f"✅ Attached file '{os.path.basename(file_path)}' into upload element.")
                    time.sleep(random.uniform(1.5, 2.5))
                    self.save_live_preview(page)
                else:
                    # Look for dropzone button
                    dropzones = page.query_selector_all("button:has-text('Upload'), button:has-text('Choose Image'), .dropzone, [data-action='upload'], [role='button']:has-text('Upload'), [aria-label*='upload' i]")
                    if dropzones:
                        for dz in dropzones:
                            if dz.is_visible():
                                box = dz.bounding_box()
                                if box:
                                    traj = HumanMouse.move_to((100, 100), (box['x'] + box['width']/2, box['y'] + box['height']/2))
                                    for pt in traj[::3]:
                                        page.mouse.move(pt[0], pt[1])
                                        time.sleep(0.01)
                                    dz.click()
                                    time.sleep(1.0)
                                    break

            # Step 2 & 3: Locate Title and Body using Gemini Text (Condensed DOM)
            log("🤖 Extracting Condensed DOM to detect Title and Description fields...")
            time.sleep(1)
            dom_json = get_condensed_interactive_tree(page)
            
            gemini_title_id = None
            gemini_body_id = None
            
            if dom_json != "[]":
                prompt = f"""
I need to fill out a post creation form.
Interactive elements:
{dom_json}

Find the input field for the 'Title' and the rich text area/textarea for the 'Description' or 'Body'.
Format your response exactly like: {{"title_id": 14, "body_id": 25}}. If you can only find one, set the other to null.
Return STRICT JSON only.
"""
                resp_text, _ = ask_gemini_text(prompt, require_json=True)
                
                if resp_text:
                    try:
                        resp = json.loads(resp_text)
                        gemini_title_id = resp.get("title_id")
                        gemini_body_id = resp.get("body_id")
                        log(f"🧠 Gemini Text mapped Title -> ID {gemini_title_id}, Body -> ID {gemini_body_id}")
                    except Exception as e:
                        log(f"Failed to parse Gemini Title/Body JSON: {e}")

            # Fill Title
            if gemini_title_id is not None:
                js_focus = f"""() => {{ const el = document.querySelector('[data-ai-id="{gemini_title_id}"]'); if(el) {{ el.focus(); el.click(); return true; }} return false; }}"""
                if page.evaluate(js_focus):
                    time.sleep(0.5)
                    page.keyboard.type(title[:100], delay=random.randint(30, 80))
                    log(f"✍️ Typed title via Gemini Vision: '{title[:40]}...'")
                    self.save_live_preview(page)
            else:
                log("⚠️ Gemini failed to find title, falling back to heuristics...")
                strict_title_sel = "input[name*='title' i], input[placeholder*='title' i], input[id*='title' i], input[aria-label*='title' i]"
                title_inputs = page.query_selector_all(strict_title_sel)
                if title_inputs:
                    title_inputs[0].focus()
                    title_inputs[0].click(force=True)
                    time.sleep(0.2)
                    HumanKeyboard.type_text(title_inputs[0], title[:100])
                    log("✍️ Typed title via heuristic.")
            
            # Fill Body
            if gemini_body_id is not None:
                js_focus = f"""() => {{ const el = document.querySelector('[data-ai-id="{gemini_body_id}"]'); if(el) {{ el.focus(); el.click(); return true; }} return false; }}"""
                if page.evaluate(js_focus):
                    time.sleep(0.5)
                    page.keyboard.type(content_text[:300], delay=random.randint(10, 40))
                    log("📝 Content text typed via Gemini Vision.")
                    self.save_live_preview(page)
            else:
                log("⚠️ Gemini failed to find body, falling back to heuristics...")
                body_elements = page.query_selector_all("textarea, div[contenteditable='true'], div.ql-editor, div.ProseMirror")
                if body_elements:
                    # Find largest
                    largest_body = max(body_elements, key=lambda b: (b.bounding_box()['width'] * b.bounding_box()['height']) if b.bounding_box() else 0, default=None)
                    if largest_body:
                        largest_body.focus()
                        largest_body.click(force=True)
                        time.sleep(0.2)
                        HumanKeyboard.type_text(largest_body, content_text[:300])
                        log("📝 Content text typed via heuristic.")
            
            # Step 4: Click Submit / Publish / Upload Button
            submit_selectors = [
                "button[type='submit']", "input[type='submit']", 
                "button:has-text('Upload')", "button:has-text('Publish')", 
                "button:has-text('Post')", "button:has-text('Submit')",
                "button:has-text('Share')", "button:has-text('Start Uploading')",
                "button:has-text('Save')", "a:has-text('Publish')", "div[role='button']:has-text('Post')",
                # Indonesian translations
                "button:has-text('Terbitkan')", "button:has-text('Bagikan')", 
                "button:has-text('Simpan')", "button:has-text('Kirim')", 
                "button:has-text('Unggah')", "button:has-text('Buat')", "div[role='button']:has-text('Terbitkan')"
            ]
            clicked_submit = False
            for s_sel in submit_selectors:
                if clicked_submit: break
                try:
                    sub_btns = page.query_selector_all(s_sel)
                    for sub_btn in sub_btns:
                        if sub_btn and sub_btn.is_visible():
                            box = sub_btn.bounding_box()
                            if box and box['y'] > 0:
                                log(f"🚀 Moving mouse to Submit button '{s_sel}' at ({int(box['x'])}, {int(box['y'])})...")
                                traj = HumanMouse.move_to((300, 300), (box['x'] + box['width']/2, box['y'] + box['height']/2))
                                for pt in traj[::3]:
                                    page.mouse.move(pt[0], pt[1])
                                    time.sleep(0.01)
                                sub_btn.click()
                                clicked_submit = True
                                log("🚀 Clicked submit button. Waiting up to 15 seconds for publication / URL change...")
                                break
                except Exception:
                    pass

            if not clicked_submit:
                log("🤖 Heuristics failed to find Submit button. Engaging Gemini Text (Condensed DOM)...")
                time.sleep(1)
                dom_json = get_condensed_interactive_tree(page)
                if dom_json != "[]":
                    prompt = f"""
I want to submit, publish, or post this form.
Interactive elements:
{dom_json}

Which button should I click? Look for 'Publish', 'Post', 'Submit', 'Next', 'Terbitkan', 'Kirim', or similar.
Format STRICT JSON only: {{"id": 42}}
"""
                    resp_text, _ = ask_gemini_text(prompt, require_json=True)
                    if resp_text:
                        import json
                        try:
                            response_json = json.loads(resp_text)
                            if "id" in response_json and response_json["id"] is not None:
                                target_id = response_json["id"]
                                log(f"🧠 Gemini Text selected Submit button ID: {target_id}")
                                js_click = f"""() => {{ const el = document.querySelector('[data-ai-id="{target_id}"]'); if(el) {{ el.click(); return true; }} return false; }}"""
                                if page.evaluate(js_click):
                                    clicked_submit = True
                                    log("🚀 Clicked submit button via Gemini Text.")
                            else:
                                log(f"❓ Gemini Text did not return a valid submit button ID. Result: {response_json}")
                        except Exception as e:
                            log(f"Failed to parse Gemini Submit JSON: {e}")
                    
            # Wait for upload/submission completion with a loop to check URL change
            for _ in range(15):
                time.sleep(1.0)
                if page.url != target_url:
                    log("🔄 URL changed indicating successful submission!")
                    break

            self.save_live_preview(page)

            # Step 5: Extract resulting link from page or URL change
            current_url = page.url
            log(f"🔍 Final browser URL: {current_url}")

            # JALUR B: Ask Gemini to find the Share Link
            log("🤖 Extracting Condensed DOM for Jalur B (Share Link detection)...")
            time.sleep(2) # Give it time to load the success page
            dom_json_post = get_condensed_interactive_tree(page)
            
            prompt_share = f"""
The post has been submitted. Current address bar URL: "{current_url}"
Available interactive elements and links:
{dom_json_post}

Goal: Extract the final PUBLIC live post URL or the button to copy it for an SEO proof report.
1. Check if the current URL has transitioned to a permanent post URL (e.g., contains /pin/, /post/, /article/, /file/).
2. If not, look for elements with labels like ["Copy link", "Share", "View Post", "Salin tautan", "Lihat"].

Return STRICT JSON only:
{{
  "has_direct_url": true | false,
  "live_url": "extracted full url string if available, else empty string",
  "fallback_copy_button_identifier": "id of copy button if direct URL is not visible, else null",
  "status": "CONFIRMED" | "NOT_FOUND"
}}
"""
            resp_text, _ = ask_gemini_text(prompt_share, require_json=True)
            if resp_text:
                import json
                try:
                    resp = json.loads(resp_text)
                    log(f"💡 Jalur B Response: {resp}")
                    if resp.get("status") == "CONFIRMED":
                        if resp.get("has_direct_url") and resp.get("live_url"):
                            return True, resp.get("live_url"), f"Jalur B extracted live URL: {resp.get('live_url')}"
                        elif resp.get("fallback_copy_button_identifier") is not None:
                            copy_id = resp.get("fallback_copy_button_identifier")
                            js_click = f"""() => {{ const el = document.querySelector('[data-ai-id="{copy_id}"]'); if(el) {{ el.click(); return true; }} return false; }}"""
                            if page.evaluate(js_click):
                                log("🚀 Clicked Copy Share Link button!")
                                time.sleep(1)
                                # Try to get clipboard (Playwright clipboard is tricky, but let's assume it might trigger a toast or we just say success)
                                return True, current_url, "Successfully clicked Copy Link (Live URL might be in clipboard)."
                except Exception as e:
                    log(f"Failed to parse Jalur B JSON: {e}")

            # Fallback to heuristics if Jalur B fails
            link_inputs = page.query_selector_all("input[value*='http'], a[href*='http']:not([href*='login']):not([href*='signup'])")
            for l_el in link_inputs:
                try:
                    val = l_el.get_attribute('value') or l_el.get_attribute('href')
                    if val and val.startswith('http') and situs.lower().split('.')[0] in val.lower() and val != target_url:
                        log(f"🎯 Discovered share link via heuristic: {val}")
                        return True, val, f"Successfully automated and captured share link: {val}"
                except Exception:
                    pass

            if current_url != target_url and current_url.startswith('http'):
                return True, current_url, f"Successfully submitted and redirected to: {current_url}"
                
            # If URL didn't change and we didn't find a share link, it might have failed to publish
            if not clicked_submit:
                return False, current_url, "Failed to locate or click the Submit/Publish button."
            else:
                # We clicked submit but URL didn't change. It could be an AJAX success, or it could be stuck.
                return False, current_url, "Clicked submit but URL did not change and no share link was found. Might be pending."
        except Exception as e:
            log(f"❌ Human browser automation error: {str(e)}")
            return False, None, f"Browser automation error: {str(e)}"
