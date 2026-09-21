import os
import json
import uuid
import time
import threading
import random
from urllib.parse import urlparse
import google.generativeai as genai
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Assuming these are defined in your project structure based on the instruction
# You may need to adjust imports if they are in different modules
from automation.gemini_vision import ask_gemini_text
from automation.browser_human import get_condensed_interactive_tree

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

HINTS_FILE = os.path.join(os.path.dirname(__file__), 'search_hints.json')
KNOWLEDGE_FILE = os.path.join(os.path.dirname(__file__), 'site_knowledge.json')
FAILED_SITES_FILE = os.path.join(os.path.dirname(__file__), 'failed_sites.log')

# Global active learning jobs
ACTIVE_LEARNING_JOBS = {}

# Global active learning jobs
def build_upload_prompt(filtered_elements_json):
    return f"""
Analyze these interactive UI elements from the target web page:
{filtered_elements_json}

Goal: Find the SINGLE most relevant button/link to START creating a new post or uploading a file.
Priority patterns: ["Create", "New Post", "Upload", "Add", "+", "Postingan Baru", file input dropzones].

Return STRICT JSON only:
{{
  "found": true,
  "action_type": "click_button",
  "target_identifier": "the exact ID to target",
  "confidence": 0.0 to 1.0
}}
"""

class HintGeneratorJob:
    def __init__(self, target_sites):
        self.job_id = str(uuid.uuid4())[:8]
        self.target_sites = target_sites
        self.total = len(target_sites)
        self.completed = 0
        self.status = "PENDING"
        self.current_site = None
        self.logs = []
        self.results = {}
        self.thread = None

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        log_str = f"[{timestamp}] [PHASE A] {message}"
        self.logs.append(log_str)
        print(log_str, flush=True)

    def start(self):
        self.status = "RUNNING"
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        self.log(f"🔍 Starting Phase A: Upload Button Detection (Jalur A) for {self.total} sites...")
        
        knowledge = {}
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
            except Exception:
                pass

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for situs in self.target_sites:
                self.current_site = situs
                self.log(f"Navigating to {situs} for DOM extraction...")
                
                try:
                    context = browser.new_context()
                    page = context.new_page()
                    target_url = situs if situs.startswith("http") else f"https://{situs}"
                    page.goto(target_url, timeout=45000, wait_until="networkidle")
                    time.sleep(3)
                    
                    self.log("Extracting Condensed DOM...")
                    dom_json = get_condensed_interactive_tree(page)
                    
                    self.log("Asking Gemini (Jalur A) to find Create/Upload button...")
                    prompt = build_upload_prompt(dom_json)
                    resp_text, err = ask_gemini_text(prompt, require_json=True)
                    
                    if not resp_text:
                        self.log(f"API Error on {situs}: {err}")
                    else:
                        try:
                            # Use json to parse the LLM's strict JSON response
                            resp_data = json.loads(resp_text)
                            self.log(f"💡 Gemini Response: {resp_data}")
                            if resp_data.get("found"):
                                ai_id = resp_data.get("target_identifier")
                                self.log(f"✅ Found button with data-ai-id: {ai_id}. Saving to knowledge.")
                                knowledge[situs] = {
                                    "editor_type": "dom_mapped",
                                    "steps": [resp_data]
                                }
                            else:
                                self.log(f"❓ Gemini could not find an upload button.")
                        except Exception as parse_err:
                            self.log(f"Failed to parse JSON response: {parse_err}")
                            
                    context.close()
                except Exception as e:
                    self.log(f"❌ Error on {situs}: {e}")
                
                with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(knowledge, f, indent=4)
                    
                self.completed += 1
                
            browser.close()
            
        self.status = "COMPLETED"
        self.log(f"🎉 Phase A Completed! Button selectors saved to site_knowledge.json.")

class SiteLearnerJob:
    def __init__(self, target_sites):
        self.job_id = str(uuid.uuid4())[:8]
        self.target_sites = target_sites
        self.total = len(target_sites)
        self.completed = 0
        self.status = "PENDING"
        self.current_site = None
        self.logs = []
        self.results = {}
        self.thread = None

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        log_str = f"[{timestamp}] [PHASE B] {message}"
        self.logs.append(log_str)
        print(log_str, flush=True)

    def start(self):
        self.status = "RUNNING"
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        self.log(f"🤖 Phase B is now integrated into Phase A (Upload) and Bulk Upload (Share).")
        self.log(f"No further action required here. You can proceed to Start Upload.")
        self.completed = self.total
        self.status = "COMPLETED"

def create_hint_job(target_sites):
    job = HintGeneratorJob(target_sites)
    ACTIVE_LEARNING_JOBS[job.job_id] = job
    job.start()
    return job.job_id

def create_learning_job(target_sites):
    job = SiteLearnerJob(target_sites)
    ACTIVE_LEARNING_JOBS[job.job_id] = job
    job.start()
    return job.job_id
