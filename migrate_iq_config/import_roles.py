import os, json, requests
from config import TARGET_URL, AUTH, HEADERS, DATA_DIR

def run():
    filepath = os.path.join(DATA_DIR, "roles.json")
    if not os.path.exists(filepath):
        print(f"!! No roles file found at {filepath}")
        return

    print(f"<- Importing Custom Roles to {TARGET_URL}...")
    with open(filepath, 'r') as f:
        roles = json.load(f)
    
    for role in roles:
        res = requests.post(f"{TARGET_URL}/api/v2/roles", auth=AUTH, headers=HEADERS, json=role)
        print(f"   Role '{role.get('name')}': {res.status_code}")

if __name__ == "__main__":
    run()
    