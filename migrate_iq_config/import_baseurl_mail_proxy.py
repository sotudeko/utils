import os, json, requests
from config import TARGET_URL, TARGET_AUTH, HEADERS, DATA_DIR

def import_item(endpoint, filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath): return
    print(f"<- Importing {filename}...")
    with open(filepath, 'r') as f:
        data = json.load(f)
    res = requests.put(f"{TARGET_URL}{endpoint}", auth=TARGET_AUTH, headers=HEADERS, json=data)
    print(f"   Status: {res.status_code}")

if __name__ == "__main__":
    import_item("/api/v2/config/?property=baseUrl", "baseUrl.json")
    import_item("/api/v2/config/httpProxyServer", "proxy.json")
    import_item("/api/v2/config/mail", "mail.json")
    