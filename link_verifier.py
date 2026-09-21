import concurrent.futures
import requests
from tracker_manager import TrackerManager

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def verify_single_url(situs, campaign, url):
    if not url or not str(url).startswith('http'):
        return {
            "situs": situs,
            "campaign": campaign,
            "url": url,
            "status_code": None,
            "status": "Empty",
            "is_alive": False
        }
    
    try:
        resp = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        code = resp.status_code
        if code == 405: # Method Not Allowed for HEAD, fallback to GET
            resp = requests.get(url, headers=HEADERS, timeout=8, stream=True)
            code = resp.status_code
            
        is_alive = 200 <= code < 400
        return {
            "situs": situs,
            "campaign": campaign,
            "url": url,
            "status_code": code,
            "status": "Active" if is_alive else f"Error ({code})",
            "is_alive": is_alive
        }
    except Exception as e:
        return {
            "situs": situs,
            "campaign": campaign,
            "url": url,
            "status_code": 0,
            "status": f"Unreachable ({type(e).__name__})",
            "is_alive": False
        }

class LinkVerifier:
    def __init__(self, tracker_manager=None):
        self.tracker_manager = tracker_manager or TrackerManager()

    def verify_campaign(self, campaign_name=None, max_workers=10):
        data = self.tracker_manager.get_data()
        rows = data.get("rows", [])
        
        tasks = []
        for r in rows:
            situs = r.get("situs")
            c_links = r.get("campaigns", {})
            
            if campaign_name:
                url = c_links.get(campaign_name)
                if url:
                    tasks.append((situs, campaign_name, url))
            else:
                for c, url in c_links.items():
                    if url:
                        tasks.append((situs, c, url))

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(verify_single_url, t[0], t[1], t[2]): t for t in tasks}
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as exc:
                    pass
                    
        total = len(results)
        alive = sum(1 for r in results if r["is_alive"])
        dead = total - alive
        
        return {
            "total_checked": total,
            "alive_count": alive,
            "dead_count": dead,
            "success_rate": round((alive / total * 100), 1) if total > 0 else 0,
            "results": results
        }
