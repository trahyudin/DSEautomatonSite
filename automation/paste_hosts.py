import requests
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def create_telegraph_page(title, content_text, author_name="AutoPost Matrix"):
    """
    Creates an instant publish page on Telegraph (telegra.ph) via official API.
    """
    try:
        # Step 1: Create account if needed
        acc_url = "https://api.telegra.ph/createAccount"
        acc_resp = requests.get(acc_url, params={'short_name': 'AutoPost', 'author_name': author_name}, headers=HEADERS, timeout=8)
        access_token = None
        if acc_resp.status_code == 200:
            res_json = acc_resp.json()
            if res_json.get('ok') and 'access_token' in res_json.get('result', {}):
                access_token = res_json['result']['access_token']
                
        if not access_token:
            access_token = "d3b25fe6e8896941f0123d8f10255a9ec26aee6170eab2763163c0740000" # Fallback public token
            
        # Format content paragraphs for Telegraph node format
        lines = [line.strip() for line in content_text.split('\n') if line.strip()]
        nodes = []
        for line in lines:
            if line.startswith('http://') or line.startswith('https://'):
                nodes.append({"tag": "p", "children": [{"tag": "a", "attrs": {"href": line}, "children": [line]}]})
            else:
                nodes.append({"tag": "p", "children": [line]})
                
        create_url = "https://api.telegra.ph/createPage"
        payload = {
            "access_token": access_token,
            "title": title[:200],
            "author_name": author_name,
            "content": json.dumps(nodes),
            "return_content": False
        }
        
        resp = requests.post(create_url, data=payload, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            res_json = resp.json()
            if res_json.get('ok') and 'url' in res_json.get('result', {}):
                return True, res_json['result']['url'], "Successfully published to Telegraph"
        return False, None, f"Telegraph publish failed ({resp.status_code})"
    except Exception as e:
        return False, None, f"Telegraph error: {str(e)}"

def create_justpaste(title, content_text):
    """
    Publishes text content to JustPaste.it
    """
    url = "https://justpaste.it/api/v1/pages"
    try:
        payload = {
            "title": title,
            "body": content_text,
            "language": "id"
        }
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        if resp.status_code in [200, 201]:
            data = resp.json()
            if 'url' in data:
                return True, data['url'], "Successfully published to JustPaste.it"
        return False, None, f"JustPaste publish failed ({resp.status_code})"
    except Exception as e:
        return False, None, f"JustPaste error: {str(e)}"

PASTE_HANDLERS = {
    'telegra.ph': create_telegraph_page,
    'justpaste.it': create_justpaste,
    'jpst.it': create_justpaste,
}

def upload_text_to_site(situs_domain, title, content_text):
    domain_clean = situs_domain.lower().replace('http://', '').replace('https://', '').strip('/')
    
    for key, handler in PASTE_HANDLERS.items():
        if key in domain_clean or domain_clean in key:
            return handler(title, content_text)
            
    # Return explicit unsupported response for unhandled domains
    return False, None, f"No direct API handler for '{situs_domain}'"
