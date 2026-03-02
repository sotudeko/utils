import requests
import json

# Configuration - TARGET instance
IQ_URL = "http://localhost:8077"
USERNAME = "admin"
PASSWORD = "admin123"

INPUT_FILE = "iq_role_mappings_export.json"

session = requests.Session()
session.auth = (USERNAME, PASSWORD)
session.headers.update({"Content-Type": "application/json"})


def get_app_internal_id_by_public_id(public_id):
    """Look up the internal ID of an application on the TARGET instance by its public ID."""
    resp = session.get(f"{IQ_URL}/api/v2/applications", params={"publicId": public_id})
    resp.raise_for_status()
    apps = resp.json().get("applications", [])
    if apps:
        return apps[0]["id"]
    return None


def grant_role_global(role_id, member_type, member_name):
    """Grant a role globally (administrator roles)."""
    url = f"{IQ_URL}/api/v2/roleMemberships/global/role/{role_id}/{member_type}/{member_name}"
    resp = session.put(url)
    resp.raise_for_status()


def grant_role_org(org_id, role_id, member_type, member_name):
    """Grant a role to a user/group for an organization."""
    url = f"{IQ_URL}/api/v2/roleMemberships/organization/{org_id}/role/{role_id}/{member_type}/{member_name}"
    resp = session.put(url)
    resp.raise_for_status()


def grant_role_app(app_id, role_id, member_type, member_name):
    """Grant a role to a user/group for an application."""
    url = f"{IQ_URL}/api/v2/roleMemberships/application/{app_id}/role/{role_id}/{member_type}/{member_name}"
    resp = session.put(url)
    resp.raise_for_status()


def main():
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    # Import global role memberships
    print("Importing global role memberships...")
    global_memberships = data.get("global", {})
    for mapping in global_memberships.get("memberMappings", []):
        role_id = mapping["roleId"]
        for member in mapping.get("members", []):
            member_type = member["type"].lower()
            member_name = member["userOrGroupName"]
            try:
                grant_role_global(role_id, member_type, member_name)
                print(f"  [OK] Granted global role {role_id} to {member_type} '{member_name}'")
            except requests.HTTPError as e:
                print(f"  [WARN] Failed: {e}")

    # Import organization role memberships
    print("\nImporting organization role memberships...")
    for org_entry in data.get("organizations", []):
        org_id = org_entry["organizationId"]
        org_name = org_entry["organizationName"]
        print(f"  Org: {org_name} ({org_id})")
        memberships = org_entry.get("roleMemberships", {})
        for mapping in memberships.get("memberMappings", []):
            role_id = mapping["roleId"]
            for member in mapping.get("members", []):
                # Only import members directly assigned to this org (not inherited)
                if member.get("ownerType") == "ORGANIZATION" and member.get("ownerId") == org_id:
                    member_type = member["type"].lower()
                    member_name = member["userOrGroupName"]
                    try:
                        grant_role_org(org_id, role_id, member_type, member_name)
                        print(f"    [OK] Granted role {role_id} to {member_type} '{member_name}'")
                    except requests.HTTPError as e:
                        print(f"    [WARN] Failed: {e}")

    # Import application role memberships
    print("\nImporting application role memberships...")
    for app_entry in data.get("applications", []):
        src_app_id = app_entry["applicationId"]
        app_name = app_entry["applicationName"]
        app_public_id = app_entry.get("applicationPublicId")

        # Resolve target internal ID using public ID
        target_app_id = None
        if app_public_id:
            target_app_id = get_app_internal_id_by_public_id(app_public_id)
        if not target_app_id:
            print(f"  [SKIP] App '{app_name}' (publicId: {app_public_id}) not found on target instance. Skipping.")
            continue

        print(f"  App: {app_name} -> target ID: {target_app_id}")
        memberships = app_entry.get("roleMemberships", {})
        for mapping in memberships.get("memberMappings", []):
            role_id = mapping["roleId"]
            for member in mapping.get("members", []):
                # Only import members directly assigned to this app (not inherited)
                if member.get("ownerType") == "APPLICATION" and member.get("ownerId") == src_app_id:
                    member_type = member["type"].lower()
                    member_name = member["userOrGroupName"]
                    try:
                        grant_role_app(target_app_id, role_id, member_type, member_name)
                        print(f"    [OK] Granted role {role_id} to {member_type} '{member_name}'")
                    except requests.HTTPError as e:
                        print(f"    [WARN] Failed: {e}")

    print("\nImport complete.")


if __name__ == "__main__":
    main()

    