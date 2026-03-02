import requests
import json
import config

# --- Configuration ---
TARGET_IQ_URL = config.TARGET_URL
TARGET_USERNAME = config.TARGET_USER
TARGET_PASSWORD = config.TARGET_PASS
INPUT_FILE = "./migration_data/hierarchy_export.json"

session = requests.Session()
session.auth = (TARGET_USERNAME, TARGET_PASSWORD)
session.headers.update({"Content-Type": "application/json"})

def get(path):
    response = session.get(f"{TARGET_IQ_URL}{path}")
    response.raise_for_status()
    return response.json()

def post(path, payload):
    response = session.post(f"{TARGET_IQ_URL}{path}", json=payload)
    response.raise_for_status()
    return response.json()

# --- Load export ---
with open(INPUT_FILE, "r") as f:
    export = json.load(f)

# --- Build a topological order for organizations (parents before children) ---
def topological_sort(orgs):
    org_by_id = {org["id"]: org for org in orgs}
    sorted_orgs = []
    visited = set()

    def visit(org_id):
        if org_id in visited:
            return
        visited.add(org_id)
        org = org_by_id.get(org_id)
        if org is None:
            return  # ROOT_ORGANIZATION_ID or already exists
        parent_id = org.get("parentOrganizationId")
        if parent_id and parent_id != "ROOT_ORGANIZATION_ID" and parent_id in org_by_id:
            visit(parent_id)
        sorted_orgs.append(org)

    for org in orgs:
        visit(org["id"])

    return sorted_orgs

# --- Get existing organizations on target to avoid duplicates ---
print("Fetching existing organizations on target...")
existing_orgs = get("/api/v2/organizations").get("organizations", [])
existing_org_names = {org["name"]: org["id"] for org in existing_orgs}

# Map source org ID -> target org ID
src_to_tgt_org_id = {}

# Root org always maps to ROOT_ORGANIZATION_ID
src_to_tgt_org_id["ROOT_ORGANIZATION_ID"] = "ROOT_ORGANIZATION_ID"

# Also map any source org whose parentOrganizationId is ROOT_ORGANIZATION_ID
# (handled implicitly below)

print("\nImporting organizations...")
sorted_orgs = topological_sort(export.get("organizations", []))

for org in sorted_orgs:
    name = org["name"]
    src_id = org["id"]
    src_parent_id = org.get("parentOrganizationId", "ROOT_ORGANIZATION_ID")

    # Resolve parent ID on target
    tgt_parent_id = src_to_tgt_org_id.get(src_parent_id, "ROOT_ORGANIZATION_ID")

    if name in existing_org_names:
        tgt_id = existing_org_names[name]
        print(f"  [EXISTS] Org '{name}' already exists on target ({tgt_id})")
        src_to_tgt_org_id[src_id] = tgt_id
        continue

    payload = {
        "name": name,
        "parentOrganizationId": tgt_parent_id
    }

    try:
        result = post("/api/v2/organizations", payload)
        tgt_id = result["id"]
        src_to_tgt_org_id[src_id] = tgt_id
        print(f"  [CREATED] Org '{name}' -> target ID {tgt_id}")
    except Exception as e:
        print(f"  [ERROR] Failed to create org '{name}': {e}")

# --- Get existing applications on target to avoid duplicates ---
print("\nFetching existing applications on target...")
existing_apps = get("/api/v2/applications").get("applications", [])
existing_app_public_ids = {app["publicId"] for app in existing_apps}

print("\nImporting applications...")
for app in export.get("applications", []):
    name = app["name"]
    public_id = app["publicId"]
    src_org_id = app["organizationId"]

    tgt_org_id = src_to_tgt_org_id.get(src_org_id)
    if not tgt_org_id:
        print(f"  [SKIP] App '{name}': parent org not mapped — skipping")
        continue

    if public_id in existing_app_public_ids:
        print(f"  [EXISTS] App '{name}' (publicId: {public_id}) already exists — skipping")
        continue

    payload = {
        "publicId": public_id,
        "name": name,
        "organizationId": tgt_org_id
    }

    try:
        result = post("/api/v2/applications", payload)
        print(f"  [CREATED] App '{name}' (publicId: {public_id}) -> target ID {result['id']}")
    except Exception as e:
        print(f"  [ERROR] Failed to create app '{name}': {e}")

print("\nImport complete.")

