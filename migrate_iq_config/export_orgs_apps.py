import requests
import json
import os
import config

# --- Configuration ---
IQ_URL = config.SOURCE_URL
USERNAME = config.SOURCE_USER
PASSWORD = config.SOURCE_PASS
OUTPUT_DIR = config.DATA_DIR
OUTPUT_FILE = os.path.join(OUTPUT_DIR, config.ORGS_APPS_FILE)

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers.update({"Content-Type": "application/json"})

def get(path):
    response = session.get(f"{IQ_URL}{path}")
    response.raise_for_status()
    return response.json()

print("Exporting organizations...")
organizations = get("/api/v2/organizations").get("organizations", [])
print(f"  Found {len(organizations)} organizations")

print("Exporting applications...")
applications = get("/api/v2/applications").get("applications", [])
print(f"  Found {len(applications)} applications")

export = {
    "organizations": organizations,
    "applications": applications
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(export, f, indent=2)

print(f"\nExport complete. Saved to {OUTPUT_FILE}")