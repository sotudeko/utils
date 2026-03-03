#!/usr/bin/env python3
import json
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOURCE_BASE = "http://localhost:8070"
TARGET_BASE = "http://localhost:8077"

SOURCE_AUTH = ("admin", "admin123")
TARGET_AUTH = ("admin", "admin123")

EXPORT_FILE = "iq_role_mappings_export.json"

# ---------------------------------------------------------------------------
# Target IQ helpers (documented APIs)
# ---------------------------------------------------------------------------

def get_target_organizations():
    url = f"{TARGET_BASE.rstrip('/')}/api/v2/organizations"
    print(f"[INFO] Fetching target organizations from {url}")
    r = requests.get(url, auth=TARGET_AUTH)
    r.raise_for_status()
    data = r.json()
    orgs = data.get("organizations", [])
    print(f"[INFO] Target: {len(orgs)} organizations")
    return orgs

def get_target_applications():
    url = f"{TARGET_BASE.rstrip('/')}/api/v2/applications"
    print(f"[INFO] Fetching target applications from {url}")
    r = requests.get(url, auth=TARGET_AUTH)
    r.raise_for_status()
    data = r.json()
    apps = data.get("applications", [])
    print(f"[INFO] Target: {len(apps)} applications")
    return apps

def get_roles(base_url, auth, label):
    url = f"{base_url.rstrip('/')}/api/v2/roles"
    print(f"[INFO] Fetching {label} roles from {url}")
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    data = r.json()
    roles = data.get("roles", [])
    print(f"[INFO] {label}: {len(roles)} roles")
    return roles

def grant_role_membership(owner_type, owner_id, role_id, member_type, member_name):
    """
    PUT /api/v2/roleMemberships/{ownerType}/{internalOwnerId}/role/{roleId}/{memberType}/{memberName}
    """
    url = (
        f"{TARGET_BASE.rstrip('/')}/api/v2/roleMemberships/"
        f"{owner_type}/{owner_id}/role/{role_id}/{member_type}/{member_name}"
    )
    print(f"[HTTP] PUT {url}")
    r = requests.put(url, auth=TARGET_AUTH)
    if r.status_code in (200, 204):
        print(f"[OK]   Granted roleId={role_id} to {member_type} '{member_name}' "
              f"on {owner_type} {owner_id}")
    else:
        print(f"[ERROR] Failed to grant role: {r.status_code} {r.text}")

# ---------------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------------

def build_name_to_id_map(items, name_key, id_key, label):
    m = {}
    for it in items:
        n = it.get(name_key)
        i = it.get(id_key)
        if n and i:
            m[n] = i
    print(f"[MAP] Built {len(m)} {label} name->id mappings")
    return m

def build_role_id_to_name_map(roles):
    m = {}
    for r in roles:
        rid = r.get("id")
        name = r.get("name")
        if rid and name:
            m[rid] = name
    print(f"[MAP] Built {len(m)} source roleId->name mappings")
    return m

def build_role_name_to_id_map(roles):
    m = {}
    for r in roles:
        rid = r.get("id")
        name = r.get("name")
        if rid and name:
            m[name] = rid
    print(f"[MAP] Built {len(m)} target roleName->id mappings")
    return m

# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------

def migrate_global(global_section, source_role_id_to_name, target_role_name_to_id):
    if not global_section:
        print("[INFO] No 'global' section in export; skipping global memberships")
        return

    mappings = global_section.get("memberMappings", [])
    print(f"[INFO] Migrating global memberships: {len(mappings)} role mappings")

    for mapping in mappings:
        src_role_id = mapping.get("roleId")
        src_role_name = source_role_id_to_name.get(src_role_id)
        if not src_role_name:
            print(f"[WARN] Global: unknown source roleId={src_role_id}; skipping")
            continue

        tgt_role_id = target_role_name_to_id.get(src_role_name)
        if not tgt_role_id:
            print(f"[WARN] Global: role '{src_role_name}' not found in target; skipping")
            continue

        members = mapping.get("members", [])
        print(f"[INFO]  Global role '{src_role_name}' ({len(members)} members)")

        for m in members:
            owner_id = m.get("ownerId")
            owner_type = m.get("ownerType")
            member_type = (m.get("type") or "").lower()
            member_name = m.get("userOrGroupName")

            if owner_type != "GLOBAL":
                print(f"[INFO]   Skipping non-GLOBAL ownerType={owner_type} for '{member_name}'")
                continue

            if owner_id != "global":
                print(f"[INFO]   Skipping unexpected global ownerId={owner_id} for '{member_name}'")
                continue

            if member_type not in ("user", "group"):
                print(f"[WARN]   Unknown member type '{member_type}' for '{member_name}'; skipping")
                continue

            print(f"[IMPORT] Global: role='{src_role_name}', memberType={member_type}, "
                  f"memberName='{member_name}'")
            grant_role_membership("global", "global", tgt_role_id, member_type, member_name)

def migrate_orgs(orgs, source_role_id_to_name,
                 target_org_name_to_id, target_role_name_to_id):
    print(f"[INFO] Migrating organization-level memberships for {len(orgs)} orgs")
    for org in orgs:
        src_org_name = org.get("organizationName")
        src_org_id = org.get("organizationId")
        rm = org.get("roleMemberships", {}) or {}
        mappings = rm.get("memberMappings", [])

        print(f"[ORG] '{src_org_name}' (sourceId={src_org_id}), {len(mappings)} role mappings")

        tgt_org_id = target_org_name_to_id.get(src_org_name)
        if not tgt_org_id:
            print(f"[WARN] No target organization named '{src_org_name}'; skipping org")
            continue

        for mapping in mappings:
            src_role_id = mapping.get("roleId")
            src_role_name = source_role_id_to_name.get(src_role_id)
            if not src_role_name:
                print(f"[WARN] Org '{src_org_name}': unknown source roleId={src_role_id}; skipping")
                continue

            tgt_role_id = target_role_name_to_id.get(src_role_name)
            if not tgt_role_id:
                print(f"[WARN] Org '{src_org_name}': role '{src_role_name}' not in target; skipping")
                continue

            members = mapping.get("members", [])
            print(f"[INFO]  Org '{src_org_name}': role '{src_role_name}' ({len(members)} members)")

            for m in members:
                owner_id = m.get("ownerId")
                owner_type = m.get("ownerType")
                member_type = (m.get("type") or "").lower()
                member_name = m.get("userOrGroupName")

                if owner_type != "ORGANIZATION":
                    print(f"[INFO]   Skipping non-ORGANIZATION ownerType={owner_type} "
                          f"for '{member_name}'")
                    continue

                if owner_id == "ROOT_ORGANIZATION_ID":
                    target_owner_id = "ROOT_ORGANIZATION_ID"
                    print(f"[INFO]   ROOT_ORGANIZATION_ID membership for '{member_name}' "
                          f"with role '{src_role_name}'")
                else:
                    if owner_id != src_org_id:
                        print(f"[INFO]   Skipping inherited membership for '{member_name}' "
                              f"(ownerId={owner_id})")
                        continue
                    target_owner_id = tgt_org_id

                if member_type not in ("user", "group"):
                    print(f"[WARN]   Unknown member type '{member_type}' for '{member_name}'; skipping")
                    continue

                print(f"[IMPORT] Org '{src_org_name}' -> targetOrgId={target_owner_id}, "
                      f"role='{src_role_name}', memberType={member_type}, "
                      f"memberName='{member_name}'")
                grant_role_membership("organization", target_owner_id,
                                      tgt_role_id, member_type, member_name)

def migrate_apps(apps, source_role_id_to_name,
                 target_app_name_to_id, target_role_name_to_id):
    print(f"[INFO] Migrating application-level memberships for {len(apps)} apps")
    for app in apps:
        src_app_name = app.get("applicationName")
        src_app_id = app.get("applicationId")
        rm = app.get("roleMemberships", {}) or {}
        mappings = rm.get("memberMappings", [])

        print(f"[APP] '{src_app_name}' (sourceId={src_app_id}), {len(mappings)} role mappings")

        tgt_app_id = target_app_name_to_id.get(src_app_name)
        if not tgt_app_id:
            print(f"[WARN] No target application named '{src_app_name}'; skipping app")
            continue

        for mapping in mappings:
            src_role_id = mapping.get("roleId")
            src_role_name = source_role_id_to_name.get(src_role_id)
            if not src_role_name:
                print(f"[WARN] App '{src_app_name}': unknown source roleId={src_role_id}; skipping")
                continue

            tgt_role_id = target_role_name_to_id.get(src_role_name)
            if not tgt_role_id:
                print(f"[WARN] App '{src_app_name}': role '{src_role_name}' not in target; skipping")
                continue

            members = mapping.get("members", [])
            print(f"[INFO]  App '{src_app_name}': role '{src_role_name}' ({len(members)} members)")

            for m in members:
                owner_id = m.get("ownerId")
                owner_type = m.get("ownerType")
                member_type = (m.get("type") or "").lower()
                member_name = m.get("userOrGroupName")

                if owner_type != "APPLICATION":
                    print(f"[INFO]   Skipping non-APPLICATION ownerType={owner_type} "
                          f"for '{member_name}'")
                    continue

                if owner_id != src_app_id:
                    print(f"[INFO]   Skipping inherited membership for '{member_name}' "
                          f"(ownerId={owner_id})")
                    continue

                if member_type not in ("user", "group"):
                    print(f"[WARN]   Unknown member type '{member_type}' for '{member_name}'; skipping")
                    continue

                print(f"[IMPORT] App '{src_app_name}' -> targetAppId={tgt_app_id}, "
                      f"role='{src_role_name}', memberType={member_type}, "
                      f"memberName='{member_name}'")
                grant_role_membership("application", tgt_app_id,
                                      tgt_role_id, member_type, member_name)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"[INFO] Loading export file: {EXPORT_FILE}")
    path = Path(EXPORT_FILE)
    if not path.is_file():
        print(f"[FATAL] File not found: {EXPORT_FILE}")
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    orgs = data.get("organizations", [])
    apps = data.get("applications", [])
    global_section = data.get("global", {})

    print(f"[INFO] Export contains: {len(orgs)} organizations, {len(apps)} applications")

    # Build source roleId -> roleName map from source IQ
    source_roles = get_roles(SOURCE_BASE, SOURCE_AUTH, "source")
    source_role_id_to_name = build_role_id_to_name_map(source_roles)

    # Build target maps from live target IQ
    target_orgs = get_target_organizations()
    target_apps = get_target_applications()
    target_roles = get_roles(TARGET_BASE, TARGET_AUTH, "target")

    target_org_name_to_id = build_name_to_id_map(
        target_orgs, "name", "id", "target org"
    )
    target_app_name_to_id = build_name_to_id_map(
        target_apps, "name", "id", "target app"
    )
    target_role_name_to_id = build_role_name_to_id_map(target_roles)

    # Migrate
    migrate_global(global_section, source_role_id_to_name, target_role_name_to_id)
    migrate_orgs(orgs, source_role_id_to_name,
                 target_org_name_to_id, target_role_name_to_id)
    migrate_apps(apps, source_role_id_to_name,
                 target_app_name_to_id, target_role_name_to_id)

    print("[INFO] Import completed")

if __name__ == "__main__":
    main()

