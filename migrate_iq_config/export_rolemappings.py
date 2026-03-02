import requests
import json

# Configuration - SOURCE instance
IQ_URL = "http://localhost:8070"
USERNAME = "admin"
PASSWORD = "admin123"

OUTPUT_FILE = "iq_role_mappings_export.json"

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers.update({"Content-Type": "application/json"})


def get_organizations():
    """Retrieve all organizations."""
    resp = session.get(f"{IQ_URL}/api/v2/organizations")
    resp.raise_for_status()
    return resp.json().get("organizations", [])


def get_applications():
    """Retrieve all applications."""
    resp = session.get(f"{IQ_URL}/api/v2/applications")
    resp.raise_for_status()
    return resp.json().get("applications", [])


def get_role_memberships_org(org_id):
    """Get role memberships for a specific organization."""
    resp = session.get(f"{IQ_URL}/api/v2/roleMemberships/organization/{org_id}")
    resp.raise_for_status()
    return resp.json()


def get_role_memberships_app(app_internal_id):
    """Get role memberships for a specific application."""
    resp = session.get(f"{IQ_URL}/api/v2/roleMemberships/application/{app_internal_id}")
    resp.raise_for_status()
    return resp.json()


def get_global_role_memberships():
    """Get global (administrator) role memberships."""
    resp = session.get(f"{IQ_URL}/api/v2/roleMemberships/global")
    resp.raise_for_status()
    return resp.json()


def get_roles():
    """Retrieve all roles for reference."""
    resp = session.get(f"{IQ_URL}/api/v2/roles")
    resp.raise_for_status()
    return {r["id"]: r["name"] for r in resp.json().get("roles", [])}


def main():
    role_map = get_roles()
    export = {}

    # Global role memberships
    print("Fetching global role memberships...")
    export["global"] = get_global_role_memberships()

    # Organization role memberships
    orgs = get_organizations()
    export["organizations"] = []
    for org in orgs:
        org_id = org["id"]
        org_name = org.get("name", org_id)
        print(f"Fetching role memberships for org: {org_name} ({org_id})")
        memberships = get_role_memberships_org(org_id)
        export["organizations"].append({
            "organizationId": org_id,
            "organizationName": org_name,
            "roleMemberships": memberships
        })

    # Application role memberships
    apps = get_applications()
    export["applications"] = []
    for app in apps:
        app_id = app["id"]  # internal ID
        app_name = app.get("name", app_id)
        app_public_id = app.get("publicId")  # public ID for cross-instance lookup
        print(f"Fetching role memberships for app: {app_name} ({app_id})")
        memberships = get_role_memberships_app(app_id)
        export["applications"].append({
            "applicationId": app_id,
            "applicationPublicId": app_public_id,
            "applicationName": app_name,
            "roleMemberships": memberships
        })

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        json.dump(export, f, indent=2)

    print(f"\nExport complete. Results saved to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()

    