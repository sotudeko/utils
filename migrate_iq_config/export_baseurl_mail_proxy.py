import os, json, requests
from config import SOURCE_URL, SOURCE_AUTH, HEADERS, DATA_DIR

def export_item(endpoint, filename):
    print(f"-> Exporting {filename}...")
    res = requests.get(f"{SOURCE_URL}{endpoint}", auth=SOURCE_AUTH)
    if res.status_code == 200:
        with open(os.path.join(DATA_DIR, filename), 'w') as f:
            json.dump(res.json(), f, indent=4)
    else:
        print(f"   [!] Failed: {res.status_code}")

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    export_item("/api/v2/config/?property=baseUrl", "baseUrl.json")
    export_item("/api/v2/config/httpProxyServer", "proxy.json")
    export_item("/api/v2/config/mail", "mail.json")
    print("Done.")
