import os, json, requests
from config import SOURCE_URL, SOURCE_AUTH, DATA_DIR

def run():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    
    print(f"-> Exporting Custom Roles from {SOURCE_URL}...")
    try:
        res = requests.get(f"{SOURCE_URL}/api/v2/roles", auth=SOURCE_AUTH)
        res.raise_for_status()
        roles_data = res.json().get('roles', [])
        
        # Filter: Ignore "builtIn": true
        custom_roles = [r for r in roles_data if not r.get('builtIn', False)]
        
        # Clean IDs for re-import
        for r in custom_roles:
            r.pop('id', None)
            
        with open(os.path.join(DATA_DIR, "roles.json"), 'w') as f:
            json.dump(custom_roles, f, indent=4)
        print(f"   Done. Saved {len(custom_roles)} custom roles.")
    except Exception as e:
        print(f"   [!] Export Failed: {e}")

if __name__ == "__main__":
    run()
    