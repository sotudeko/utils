import json
import requests
import os
import glob
import time
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
    if not org_id: return {}
    raw_t = get_data(f"{TARGET_URL}/api/v2/applicationCategories/organization/{org_id}")
    t_list = raw_t if isinstance(raw_t, list) else (raw_t.get("categories", []) if raw_t else [])
    return {clean(t['name']).lower(): t['id'] for t in t_list}

def main():
    print("--- STARTING STRICT-VALIDATION IMPORT ---")
    
    orgs_payload = get_data(f"{TARGET_URL}/api/v2/organizations")
    if not orgs_payload:
        print("Error: Target server unreachable.")
        return
    
    target_orgs = {o['name']: o['id'] for o in orgs_payload.get("organizations", [])}
    
    # Pre-fetch Global Table
    print("Building global tag lookup table...")
    global_tag_lookup = {}
    for o_name, o_id in target_orgs.items():
        o_map = get_tag_map(o_id)
        for t_name, t_id in o_map.items():
            if t_name not in global_tag_lookup:
                global_tag_lookup[t_name] = t_id

    for file_path in sorted(glob.glob(f"{DATA_DIR}/*.json")):
        with open(file_path, "r") as f:
            org_data = json.load(f)
        
        o_name = org_data['org_name']
        if o_name == "Root Organization": continue

        print(f"\nProcessing Org: {o_name}")
        target_org_id = target_orgs.get(o_name)
        if not target_org_id: continue

        # 1. Sync Local Tags with MANDATORY DESCRIPTION
        local_map = get_tag_map(target_org_id)
        for t_req in org_data.get('tags', []):
            t_name = t_req['name']
            lookup = clean(t_name).lower()
            
            if lookup not in local_map and lookup not in global_tag_lookup:
                print(f"  Creating tag: {t_name}")
                payload = {
                    "name": t_name,
                    "description": f"Standard description for {t_name}", # MANDATORY FIX
                    "color": "light-blue"
                }
                res = requests.post(
                    f"{TARGET_URL}/api/v2/applicationCategories/organization/{target_org_id}", 
                    auth=AUTH, 
                    json=payload
                )
                if res.status_code not in [200, 201, 204]:
                    print(f"  ! STILL FAILED: {res.status_code} - {res.text}")
            
        # Refresh local map
        local_map = get_tag_map(target_org_id)
        global_tag_lookup.update(local_map)

        # 2. Process Apps
        for app_export in org_data.get('apps', []):
            app_pid = app_export['publicId']
            search_res = get_data(f"{TARGET_URL}/api/v2/applications?publicId={app_pid}")
            apps_found = search_res.get("applications", []) if search_res else []
            if not apps_found: continue
            
            app_obj = apps_found[0]
            tag_payload = []

            for t_name in app_export.get('tags', []):
                lookup = clean(t_name).lower()
                t_id = local_map.get(lookup) or global_tag_lookup.get(lookup)
                
                if t_id:
                    tag_payload.append({"tagId": t_id})

            app_obj['applicationTags'] = tag_payload
            put_res = requests.put(f"{TARGET_URL}/api/v2/applications/{app_obj['id']}", 
                                   auth=AUTH, json=app_obj)
            
            if len(app_export.get('tags', [])) > 0:
                print(f"    - {app_export['name']}: Assigned {len(tag_payload)}/{len(app_export['tags'])} tags.")

if __name__ == "__main__":
    main()