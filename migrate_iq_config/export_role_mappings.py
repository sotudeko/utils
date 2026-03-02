import requests
import json
import config # Use your existing config.py (ensure SOURCE_URL/AUTH are set)

def get_source_data(endpoint):
    res = requests.get(f"{config.SOURCE_URL}/api/v2/{endpoint}", auth=config.SOURCE_AUTH)
    return res.json() if res.status_code == 200 else {}

def main():
    print("--- STARTING CLEAN EXPORT (NAME-BASED) ---")
    
    # 1. Map Role IDs to Names so we don't use UUIDs in the export
    roles_data = get_source_data("roles")
    role_id_to_name = {r['id']: r['name'] for r in roles_data.get('roles', [])}
    
    # 2. Get all Orgs and Apps to iterate through them
    orgs = get_source_data("organizations").get('organizations', [])
    apps = get_source_data("applications").get('applications', [])
    
    clean_export = []

    # 3. Process Organizations
    for org in orgs:
        org_name = org['name']
        org_id = org['id']
        # Fetch memberships for this specific Org
        mappings = get_source_data(f"rolePrivileges/organization/{org_id}")
        
        for m in mappings.get('rolePrivileges', []):
            role_name = role_id_to_name.get(m['roleId'])
            if role_name and m.get('members'):
                clean_export.append({
                    "ownerName": org_name,
                    "ownerType": "organization",
                    "roleName": role_name,
                    "members": m['members'] # List of {'type': 'USER', 'name': 'admin'}
                })

    # 4. Process Applications
    for app in apps:
        app_name = app['name']
        app_id = app['id']
        mappings = get_source_data(f"rolePrivileges/application/{app_id}")
        
        for m in mappings.get('rolePrivileges', []):
            role_name = role_id_to_name.get(m['roleId'])
            if role_name and m.get('members'):
                clean_export.append({
                    "ownerName": app_name,
                    "ownerType": "application",
                    "roleName": role_name,
                    "members": m['members']
                })

    with open("data/clean_role_mappings.json", "w") as f:
        json.dump(clean_export, f, indent=2)
    
    print(f"--- EXPORT FINISHED: {len(clean_export)} mappings saved ---")

if __name__ == "__main__":
    main()

    