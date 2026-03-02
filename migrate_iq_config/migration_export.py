import json
import requests
import os
from requests.auth import HTTPBasicAuth

# --- CONFIG ---
SOURCE_URL = "http://localhost:8070"
AUTH = HTTPBasicAuth("admin", "admin123")
DATA_DIR = "./migration_data/orgs"

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(url):
    try:
        res = requests.get(url, auth=AUTH)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def main():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    print("--- STARTING HYBRID-SCAN EXPORT ---")
    
    # 1. Fetch ALL Tag Definitions globally so we can resolve IDs regardless of Org
    print("Pre-fetching global tag definitions...")
    all_tags = {}
    orgs_payload = get_data(f"{SOURCE_URL}/api/v2/organizations")
    orgs = orgs_payload.get("organizations", []) if orgs_payload else []

    for org in orgs:
        t_raw = get_data(f"{SOURCE_URL}/api/v2/applicationCategories/organization/{org['id']}")
        t_list = t_raw if isinstance(t_raw, list) else (t_raw.get("categories", []) if t_raw else [])
        for t in t_list:
            all_tags[t['id']] = clean(t['name'])

    # 2. Process Orgs
    for org in orgs:
        o_id, o_name = org['id'], org['name']
        print(f"\nProcessing Org: {o_name}")

        # Fetch apps with categories included
        apps_url = f"{SOURCE_URL}/api/v2/applications/organization/{o_id}?includeCategories=true"
        apps_payload = get_data(apps_url)
        apps_raw = apps_payload.get("applications", []) if apps_payload else []
        
        apps_list = []
        for a in apps_raw:
            # Check 'applicationTags' (which holds the ID links)
            tag_ids = [t.get('tagId') for t in a.get('applicationTags', []) if t.get('tagId')]
            
            # Resolve those IDs using our Global Map
            resolved_names = []
            for tid in tag_ids:
                if tid in all_tags:
                    resolved_names.append(all_tags[tid])
            
            if resolved_names:
                print(f"    - {a['name'].ljust(20)} Found Tags: {resolved_names}")

            apps_list.append({
                "name": clean(a['name']),
                "publicId": clean(a['publicId']),
                "tags": resolved_names
            })

        # 3. Save Org Bundle
        org_tags_raw = get_data(f"{SOURCE_URL}/api/v2/applicationCategories/organization/{o_id}")
        org_tags = org_tags_raw if isinstance(org_tags_raw, list) else (org_tags_raw.get("categories", []) if org_tags_raw else [])

        safe_name = "".join([c for c in o_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        with open(f"{DATA_DIR}/{safe_name}.json", "w") as f:
            json.dump({
                "org_name": o_name, 
                "tags": [{"name": clean(t['name'])} for t in org_tags], 
                "apps": apps_list
            }, f, indent=2)

    print(f"\n--- EXPORT FINISHED ---")

if __name__ == "__main__":
    main()
    