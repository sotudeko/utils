import os
import json
import requests
from config import SOURCE_URL, SOURCE_AUTH, DATA_DIR

# Specific subdirectory for organization bundles
ORG_DATA_DIR = os.path.join(DATA_DIR, "orgs")

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(endpoint):
    """Helper to fetch data using the shared config URL and AUTH."""
    try:
        res = requests.get(f"{SOURCE_URL}{endpoint}", auth=SOURCE_AUTH)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        print(f"   [!] Connection Error: {e}")
    return None

def run():
    if not os.path.exists(ORG_DATA_DIR):
        os.makedirs(ORG_DATA_DIR, exist_ok=True)

    print(f"--- STARTING HYBRID-SCAN EXPORT FROM {SOURCE_URL} ---")
    
    # 1. Fetch ALL Tag Definitions globally to resolve IDs across the instance
    print("Pre-fetching global tag definitions...")
    all_tags = {}
    orgs_payload = get_data("/api/v2/organizations")
    orgs = orgs_payload.get("organizations", []) if orgs_payload else []

    for org in orgs:
        # Fetch tags (categories) for each organization
        t_raw = get_data(f"/api/v2/applicationCategories/organization/{org['id']}")
        t_list = t_raw if isinstance(t_raw, list) else (t_raw.get("categories", []) if t_raw else [])
        for t in t_list:
            all_tags[t['id']] = clean(t['name'])

    # 2. Process Orgs
    for org in orgs:
        o_id, o_name = org['id'], org['name']
        print(f"\nProcessing Org: {o_name}")

        # Fetch apps with categories included to see the links
        apps_url = f"/api/v2/applications/organization/{o_id}?includeCategories=true"
        apps_payload = get_data(apps_url)
        apps_raw = apps_payload.get("applications", []) if apps_payload else []
        
        apps_list = []
        for a in apps_raw:
            # Extract tag IDs assigned to this specific app
            tag_ids = [t.get('tagId') for t in a.get('applicationTags', []) if t.get('tagId')]
            
            # Resolve those IDs using the Global Map we built in step 1
            resolved_names = [all_tags[tid] for tid in tag_ids if tid in all_tags]
            
            if resolved_names:
                print(f"    - {a['name'].ljust(20)} Found Tags: {resolved_names}")

            apps_list.append({
                "name": clean(a['name']),
                "publicId": clean(a['publicId']),
                "tags": resolved_names
            })

        # 3. Build the Org Bundle
        org_tags_raw = get_data(f"/api/v2/applicationCategories/organization/{o_id}")
        org_tags = org_tags_raw if isinstance(org_tags_raw, list) else (org_tags_raw.get("categories", []) if org_tags_raw else [])

        # Create a filesystem-safe filename
        safe_name = "".join([c for c in o_name if c.isalnum() or c in (' ', '_')]).strip().replace(" ", "_")
        filepath = os.path.join(ORG_DATA_DIR, f"{safe_name}.json")
        
        with open(filepath, "w") as f:
            json.dump({
                "org_name": o_name, 
                "tags": [{"name": clean(t['name'])} for t in org_tags], 
                "apps": apps_list
            }, f, indent=2)

    print(f"\n--- EXPORT FINISHED: Files saved to {ORG_DATA_DIR} ---")

if __name__ == "__main__":
    run()
    