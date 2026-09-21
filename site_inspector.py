import json
import os
import requests
import concurrent.futures
from tracker_manager import TrackerManager, categorize_site

SITE_CAPABILITIES_FILE = r'd:\Kerja praktek\dse automation\site_capabilities.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Known API or Direct Upload Platforms
DIRECT_API_SITES = [
    'catbox.moe', 'uguu.se', 'pixeldrain.com', 'gofile.io', 'freeimage.host',
    'imgbb.com', 'postimages.org', 'gifyu.com', 'telegra.ph', 'justpaste.it', 'jpst.it'
]

# Known Complex / Login Required Platforms
COMPLEX_LOGIN_SITES = [
    'pinterest.com', 'medium.com', 'blogger.com', 'tumblr.com', 'livejournal.com',
    'wix.com', 'weebly.com', 'wordpress.com', 'facebook.com', 'instagram.com',
    'twitter.com', 'x.com', 'reddit.com', 'behance.net', 'flipboard.com', 'wattpad.com',
    'notion.com', 'substack.com', 'hubspot.com', 'squarespace.com', 'dribbble.com'
]

def inspect_single_site_fast(situs):
    situs_clean = situs.lower().replace('http://', '').replace('https://', '').strip('/')
    category = categorize_site(situs)
    
    # 1. Determine Difficulty Tier
    tier = "Sedang"
    tier_code = "MEDIUM"
    method = "Playwright Web Form + AI Heuristics"
    
    if any(k in situs_clean for k in DIRECT_API_SITES):
        tier = "Mudah"
        tier_code = "EASY"
        method = "Direct API / Multipart Upload"

    return {
        "situs": situs,
        "category": category,
        "tier": tier,
        "tier_code": tier_code,
        "upload_method": method,
        "accessible": True, # Assume true for fast sorting
        "status_code": 200
    }

def inspect_single_site(situs):
    situs_clean = situs.lower().replace('http://', '').replace('https://', '').strip('/')
    category = categorize_site(situs)
    
    # 1. Determine Difficulty Tier
    tier = "Sedang"
    tier_code = "MEDIUM"
    method = "Playwright Web Form + AI Heuristics"
    
    if any(k in situs_clean for k in DIRECT_API_SITES):
        tier = "Mudah"
        tier_code = "EASY"
        method = "Direct API / Multipart Upload"

    # 2. Check site HTTP accessibility (fast 3s timeout)
    url = situs if situs.startswith('http') else f"https://{situs}"
    accessible = False
    status_code = 0
    
    try:
        resp = requests.head(url, headers=HEADERS, timeout=3, allow_redirects=True)
        status_code = resp.status_code
        if status_code == 405: # Fallback to GET
            resp = requests.get(url, headers=HEADERS, timeout=3, stream=True)
            status_code = resp.status_code
        accessible = (200 <= status_code < 400)
    except Exception:
        accessible = False
        status_code = 0

    return {
        "situs": situs,
        "category": category,
        "tier": tier,
        "tier_code": tier_code,
        "upload_method": method,
        "accessible": accessible,
        "status_code": status_code
    }

class SiteInspector:
    def __init__(self, tracker_manager=None):
        self.tracker_manager = tracker_manager or TrackerManager()

    def run_full_audit(self, max_workers=30):
        data = self.tracker_manager.get_data()
        rows = data.get("rows", [])
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_site = {executor.submit(inspect_single_site, r['situs']): r['situs'] for r in rows}
            for future in concurrent.futures.as_completed(future_to_site):
                try:
                    res = future.result()
                    results.append(res)
                except Exception:
                    pass

        # Sort by original site order
        site_order = {r['situs']: idx for idx, r in enumerate(rows)}
        results.sort(key=lambda x: site_order.get(x['situs'], 999))

        tier_counts = {
            "Mudah": sum(1 for r in results if r['tier'] == "Mudah"),
            "Sedang": sum(1 for r in results if r['tier'] == "Sedang"),
            "Sulit": sum(1 for r in results if r['tier'] == "Sulit")
        }

        audit_data = {
            "total_sites": len(results),
            "tier_counts": tier_counts,
            "results": results
        }

        # Save to site_capabilities.json
        with open(SITE_CAPABILITIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)

        return audit_data

    def load_cached_capabilities(self):
        if os.path.exists(SITE_CAPABILITIES_FILE):
            try:
                with open(SITE_CAPABILITIES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return self.run_full_audit()
