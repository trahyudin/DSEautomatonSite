import requests
from automation.image_hosts import upload_gofile, upload_pixeldrain, upload_catbox

def upload_cloud_file(situs_domain, file_path):
    """
    Handles file upload for cloud storage platforms.
    For anonymous cloud hosts (Gofile, Pixeldrain, Catbox), uploads directly.
    """
    domain_clean = situs_domain.lower()
    
    if 'gofile.io' in domain_clean:
        return upload_gofile(file_path)
    elif 'pixeldrain' in domain_clean:
        return upload_pixeldrain(file_path)
    elif 'catbox' in domain_clean:
        return upload_catbox(file_path)
    else:
        # Default anonymous cloud host fallback
        return upload_catbox(file_path)
