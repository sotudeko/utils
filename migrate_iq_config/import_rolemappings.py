import os, json, requests
from config import TARGET_URL, AUTH, HEADERS, DATA_DIR

def run():
    filepath = os.path.join(DATA_DIR, "all_role_memberships.json")
    if not os.path.exists(filepath):
        print(f"!! No mapping file found at {filepath}")
        return

    print(f"<- Importing Role Memberships to {TARGET_URL}...")
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Global & Repo
    requests.put(f"{TARGET_URL}/api/v2/roleMemberships/global", auth=AUTH, headers=HEADERS, json=data["global"])
    requests.put(f"{TARGET_URL}/api/v2/roleMemberships/repository_container", auth=AUTH, headers=HEADERS, json=data["repository_container"])
    
    # Orgs
    for o in data["organizations"]:
        requests.put(f"{TARGET_URL}/api/v2/roleMemberships/organization/{o['id']}", auth=AUTH, headers=HEADERS, json=o["memberships"])
    
    # Apps
    for a in data["applications"]:
        requests.put(f"{TARGET_URL}/api/v2/roleMemberships/application/{a['id']}", auth=AUTH, headers=HEADERS, json=a["memberships"])
    
    print("   Done.")

if __name__ == "__main__":
    run()
    