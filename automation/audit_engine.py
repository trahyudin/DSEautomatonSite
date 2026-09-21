import time
import os
import json
import threading
from playwright.sync_api import sync_playwright

AUDIT_STATE = {
    "is_running": False,
    "progress": {"completed": 0, "total": 0},
    "stats": {"READY": 0, "NYASAR": 0, "LOGIN_REQUIRED": 0, "TIMEOUT_OR_BLOCKED": 0, "ERROR": 0},
    "results": [],
    "last_updated": time.time()
}

def get_audit_state():
    return AUDIT_STATE

def run_mass_audit(rows, auto_router):
    if AUDIT_STATE["is_running"]:
        return False
        
    AUDIT_STATE["is_running"] = True
    AUDIT_STATE["progress"]["total"] = len(rows)
    AUDIT_STATE["progress"]["completed"] = 0
    AUDIT_STATE["stats"] = {"READY": 0, "NYASAR": 0, "LOGIN_REQUIRED": 0, "TIMEOUT_OR_BLOCKED": 0, "ERROR": 0}
    AUDIT_STATE["results"] = []
    
    def _audit_thread():
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, channel="msedge", args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(viewport={'width': 1280, 'height': 800})
                
                for idx, row in enumerate(rows):
                    if not AUDIT_STATE["is_running"]: # Allow cancellation
                        break
                        
                    situs = row["situs"]
                    if not situs.startswith('http'):
                        situs = f"https://{situs}"
                        
                    target_url = situs
                    routed = False
                    for domain, routed_url in auto_router.items():
                        if domain in situs.lower() and len(situs.split('/')) <= 4:
                            target_url = routed_url
                            routed = True
                            break
                            
                    result_entry = {
                        "situs": row["situs"],
                        "category": row.get("category", "Unknown"),
                        "routed": routed,
                        "target_url": target_url,
                        "status": "ERROR",
                        "msg": "Unknown error"
                    }
                    
                    page = None
                    try:
                        page = context.new_page()
                        page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
                        time.sleep(1.5)
                        
                        current_url = page.url
                        
                        # Check login
                        pwd_count = page.locator("input[type='password']").count()
                        if any(k in current_url.lower() for k in ['login', 'signin', 'auth', 'register']) or pwd_count > 0:
                            result_entry["status"] = "LOGIN_REQUIRED"
                            result_entry["msg"] = "Halaman meminta login/registrasi."
                        else:
                            has_title = page.locator("input[type='text']:not([hidden]), input[name*='title' i], input[placeholder*='title' i]").count() > 0
                            has_body = page.locator("textarea, div[contenteditable='true'], div.ql-editor, div.ProseMirror, div.monaco-editor, iframe.tox-edit-area__iframe").count() > 0
                            submit_sel = "button[type='submit'], input[type='submit'], button:has-text('Upload'), button:has-text('Publish'), button:has-text('Post'), button:has-text('Submit'), button:has-text('Save'), a:has-text('Publish')"
                            has_submit = page.locator(submit_sel).count() > 0
                            
                            if has_title and has_body:
                                result_entry["status"] = "READY"
                                result_entry["msg"] = "Formulir siap diisi!"
                            else:
                                result_entry["status"] = "NYASAR"
                                result_entry["msg"] = f"Elemen tidak lengkap. Title:{has_title}, Body:{has_body}, Submit:{has_submit}"
                                
                    except Exception as e:
                        err_str = str(e).lower()
                        if "timeout" in err_str or "target closed" in err_str:
                            result_entry["status"] = "TIMEOUT_OR_BLOCKED"
                            result_entry["msg"] = "Gagal memuat halaman (Timeout/Cloudflare)."
                        else:
                            result_entry["status"] = "ERROR"
                            result_entry["msg"] = str(e)[:100]
                    finally:
                        if page:
                            try:
                                page.close()
                            except:
                                pass
                                
                    AUDIT_STATE["results"].append(result_entry)
                    AUDIT_STATE["stats"][result_entry["status"]] += 1
                    AUDIT_STATE["progress"]["completed"] += 1
                    AUDIT_STATE["last_updated"] = time.time()
                    
                browser.close()
        except Exception as ex:
            print(f"[Audit Engine] Critical Error: {ex}", flush=True)
        finally:
            AUDIT_STATE["is_running"] = False
            
    thread = threading.Thread(target=_audit_thread, daemon=True)
    thread.start()
    return True
