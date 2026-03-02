import os
import json
import glob
import requests
from config import TARGET_URL, AUTH, DATA_DIR

# Path to the organization bundles created by the export script
ORG_DATA_DIR = os.path.join(DATA_DIR, "orgs")

def clean(text):
    return " ".join(text.split()).strip() if text else ""

def get_data(endpoint):
    """Helper to fetch data using the shared config TARGET_URL."""
    try:
        res = requests.get(f"{TARGET_URL}{endpoint}", auth=AUTH)
        return res.json() if res.status_code == 200 else None
    except Exception as e:
        print(f"   [!] Connection Error: {e}")
        return None

def get_tag_map(org_id):
    """Fetches tags for a specific org and returns a name-to-ID lookup map."""
    endpoint = f"/api/v2/applicationCategories/organization/{org_id}"
    raw_t = get_data(endpoint)
    # Handle both list responses and dictionary responses
    t_list = raw_t if isinstance(raw_t, list) else (raw_t.get("categories", []) if raw_t else [])
    return {clean(t['name']).lower(): t['id'] for t in t_list}

def run():
    print(f"--- STARTING FORCE-SYNC IMPORT TO {TARGET_URL} ---")
    
    # 1. Get current Organizations on the target to avoid duplicates
    root_payload = get_data("/api/v2/organizations")
    if not root_payload:
        print("!! Could not connect to Target. Aborting.")
        return

    target_orgs = {o['name']: o['id'] for o in root_payload.get("organizations", [])}
    
    # Identify Root Organization and its tags (global tags)
    root_id = target_orgs.get("Root Organization")
    root_tag_map = get_tag_map(root_id) if root_id else {}

    # 2. Find all exported JSON files
    search_path = os.path.join(ORG_DATA_DIR, "*.json")
    files = sorted(glob.glob(search_path))
    
    if not files:
        print(f"Error: No JSON files found in {ORG_DATA_DIR}")
        return

    for file_path in files:
        with open(file_path, "r") as f:
            org_data = json.load(f)
        
        o_name = org_data['org_name']
        print(f"\nProcessing Org: {o_name}")

        # Ensure Org exists on Target; create it if missing
        if o_name not in target_orgs:
            print(f"  Creating Organization: {o_name}")
            res = requests.post(f"{TARGET_URL}/api/v2/organizations", auth=AUTH, json={"name": o_name})
            if res.status_code in [200, 201]:
                target_org_id = res.json()['id']
                target_orgs[o_name] = target_org_id
            else:
                print(f"  [!] Failed to create Org: {res.status_code}")
                continue
        else:
            target_org_id = target_orgs[o_name]

        # 3. Synchronize Tags (Categories)
        local_tag_map = get_tag_map(target_org_id)
        for t_req in org_data.get('tags',
                                  