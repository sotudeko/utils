import json
import requests
import os
import glob
from requests.auth import HTTPBasicAuth

# --- TARGET CONFIG ---
TARGET_URL = "http://localhost:8077"
AUTH = HTTPBasicAuth("admin", "admin123")
DATA_DIR = "./migration_data/orgs"

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url):
    res = requests.get(url, auth=AUTH)
    return res.json() if res.status_code == 200 else None

def get_tag_map(org_id):
    raw_t = get_data(f"{TARGET_URL}/api/v2/applicationCategories/organization/{org_id}")
    t_list = raw_t if isinstance(raw_t, list) else (raw_t.get("categories", []) if raw_t else [])
    return {clean(t['name']).lower(): t['id'] for t in t_list}

def main():
    print("--- STARTING FORCE-SYNC IMPORT ---")
    
    # Get the Root ID once
    root_payload = get_data(f"{TARGET_URL}/api/v2/organizations")
    target_orgs = {o['name']: o['id'] for o in root_payload.get("organizations", [])}
    root_id = target_orgs.get("Root Organization")
    root_tag_map = get_tag_map(root_id)

    # Find all JSON files
    files = sorted(glob.glob(f"{DATA_DIR}/*.json"))
    if not files:
        print(f"Error: No JSON files found in {DATA_DIR}")
        return

    for file_path in files:
        with open(file_path, "r") as f:
            org_data = json.load(f)
        
        o_name = org_data['org_name']
        print(f"\nProcessing Org: {o_name}")

        # Ensure Org exists and get ID
        if o_name not in target_orgs:
            res = requests.post(f"{TARGET_URL}/api/v2/organizations", auth=AUTH, json={"name": o_name})
            target_org_id = res.json()['id']
            target_orgs[o_name] = target_org_id
        else:
            target_org_id = target_orgs[o_name]

        # 1. Create Tags (Always include description)
        local_tag_map = get_tag_map(target_org_id)
        for t_req in org_data.get('tags', []):
            t_name = t_req['name']
            if clean(t_name).lower() not in local_tag_map and clean(t_name).lower() not in root_tag_map:
                print(f"  Creating tag: {t_name}")
                requests.post(f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", 
                              auth=AUTH, 
                              json={"name": t_name, "description": "Migrated tag", "color": "light-blue"})
        
        # Refresh maps
        local_tag_map = get_tag_map(target_org_id)
        combined_map = {**root_tag_map, **local_tag_map}

        # 2. Process Apps (Force checking even if they exist)
        apps_to_process = org_data.get('apps', [])
        print(f"  Found {len(apps_to_process)} apps in JSON.")

        for app_export in apps_to_process:
            app_name = app_export['name']
            app_pid = app_export['publicId']
            
            # Find internal ID on target
            search = get_data(f"{TARGET_URL}/api/v2/applications?publicId={app_pid}")
            apps_found = search.get("applications", []) if search else []
            
            if not apps_found:
                print(f"    Creating app: {app_name}")
                res = requests.post(f"{TARGET_URL}/api/v2/applications", auth=AUTH, 
                                    json={"publicId": app_pid, "name": app_name, "organizationId": target_org_id})
                app_obj = res.json()
            else:
                app_obj = apps_found[0]

            # Assign Tags via PUT
            tag_payload = []
            for t_name in app_export.get('tags', []):
                lookup = clean(t_name).lower()
                if lookup in combined_map:
                    tag_payload.append({"tagId": combined_map[lookup]})
            
            app_obj['applicationTags'] = tag_payload
            res = requests.put(f"{TARGET_URL}/api/v2/applications/{app_obj['id']}", auth=AUTH, json=app_obj)
            
            if len(app_export.get('tags', [])) > 0:
                print(f"    - {app_name}: Linked {len(tag_payload)}/{len(app_export['tags'])} tags (Status: {res.status_code})")

if __name__ == "__main__":
    main()
    