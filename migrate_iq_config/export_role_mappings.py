import os, json, requests
from config import SOURCE_URL, SOURCE_AUTH, DATA_DIR

def run():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    print(f"-> Exporting Role Memberships from {SOURCE_URL}...")
    
    export_data = {"global": {}, "repository_container": {}, "organizations": [], "applications": []}
    
    # Global & Repos
    export_data["global"] = requests.get(f"{SOURCE_URL}/api/v2/roleMemberships/global", auth=SOURCE_AUTH).json()
    export_data["repository_container"] = requests.get(f"{SOURCE_URL}/api/v2/roleMemberships/repository_container", auth=SOURCE_AUTH).json()
    
    # Organizations
    orgs = requests.get(f"{SOURCE_URL}/api/v2/organizations", auth=SOURCE_AUTH).json().get("organizations", [])
    for org in orgs:
        m = requests.get(f"{SOURCE_URL}/api/v2/roleMemberships/organization/{org['id']}", auth=SOURCE_AUTH).json()
        export_data["organizations"].append({"id": org['id'], "name": org['name'], "memberships": m})
        
    # Applications
    apps = requests.get(f"{SOURCE_URL}/api/v2/applications", auth=SOURCE_AUTH).json().get("applications", [])
    for app in apps:
        m = requests.get(f"{SOURCE_URL}/api/v2/roleMemberships/application/{app['id']}", auth=SOURCE_AUTH).json()
        export_data["applications"].append({"id": app['id'], "name": app['name'], "memberships": m})

    with open(os.path.join(DATA_DIR, "all_role_memberships.json"), 'w') as f:
        json.dump(export_data, f, indent=4)
    print("   Done. All memberships exported.")

if __name__ == "__main__":
    run()
