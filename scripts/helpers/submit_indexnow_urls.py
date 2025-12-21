import os
import json
import requests

# Configuration
SITE_ROOT = "https://frankvaneykelen.github.io/lineup-radar/"
KEY = "7d805aec05b542568304858c593db541"
KEY_LOCATION = SITE_ROOT + "7d805aec05b542568304858c593db541.txt"
DOCS_DIR = "docs"

def get_all_urls(docs_dir, site_root):
    urls = []
    for root, _, files in os.walk(docs_dir):
        for file in files:
            if file.startswith('.'):
                continue
            rel_path = os.path.relpath(os.path.join(root, file), docs_dir)
            # Convert Windows backslashes to URL slashes
            url_path = rel_path.replace(os.sep, '/')
            urls.append(site_root + url_path)
    return urls

def submit_to_indexnow(urls):
    payload = {
        "host": SITE_ROOT,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls
    }
    headers = {"Content-Type": "application/json; charset=utf-8"}
    print("Submitting the following URLs to IndexNow:")
    for url in urls:
        print(f"  {url}")
    response = requests.post("https://api.indexnow.org/IndexNow", data=json.dumps(payload), headers=headers)
    print("Status:", response.status_code)
    print("Response:", response.text)

if __name__ == "__main__":
    urls = get_all_urls(DOCS_DIR, SITE_ROOT)
    print(f"Submitting {len(urls)} URLs to IndexNow...")
    submit_to_indexnow(urls)