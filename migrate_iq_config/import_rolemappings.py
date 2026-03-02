import json
import requests
import os
import config

def get_target_lookup(endpoint):
    url = f"{config.TARGET_URL}/api/v2/{endpoint}"
    res = requests.get(url, auth=config.TARGET_AUTH)
    if res.status_code == 200:
        data = res.json()
        items = data.get(endpoint if endpoint != 'roles' else 'roles', [])
        return {item['name'].lower(): item['id'] for item in items}
    return {}

def main():
    print("--- STARTING FIELD-AGNOSTIC IMPORT ---")
    
    input_file = os.path.join(config.DATA_DIR, "all_role_memberships.json")
    with open(input_file, "r") as f:
        data = json.load(f)

    # 1. Target ID Lookups
    target_roles = get_target_lookup("roles")
    target_orgs = get_target_lookup("organizations")
    target_apps = get_target_lookup("applications")
    target_root_id = target_orgs.get("root organization")

    # Mapping Source UUIDs to Target Role Names
    role_id_map = {
        "b9646757e98e486da7d730025f5245f8": "policy administrator",
        "764b8595856747f3945480749179366a": "owner",
        "838d172e2d93427387d812d47756f708": "developer",
        "1b92fae3e55a411793a091fb821c422d": "application evaluator", 
        "3278aac26e9243cfb95cb59ad903f277": "system administrator", 
        "1cddabf7fdaa47d6833454af10e0a3ef": "claim components"
    }

    success_count = 0

    for scope, content in data.items():
        if not content: continue
        print(f"\nProcessing {scope}...")
        
        # --- LOGIC FOR GLOBAL / REPOSITORY_CONTAINER (Dictionary Structure) ---
        if scope in ['global', 'repository_container']:
            mappings = content.get('memberMappings', [])
            owner_id = target_root_id 
            o_type = "organization" if scope == 'global' else "repository_container"
            
            for m_group in mappings:
                role_name = role_id_map.get(m_group.get('roleId'), '').lower()
                t_role_id = target_roles.get(role_name)
                if not t_role_id: continue

                for member in m_group.get('members', []):
                    # FIX: Try multiple common identity keys
                    m_identity = member.get('name') or member.get('userOrGroupId') or member.get('id')
                    m_type = member.get('type') or member.get('ownerType') # Fallback for some export types
                    
                    if not m_identity or not m_type:
                        continue

                    url = f"{config.TARGET_URL}/api/v2/rolePrivileges/{o_type}/{owner_id}/role/{t_role_id}"
                    res = requests.post(url, auth=config.TARGET_AUTH, json={"type": m_type, "name": m_identity})
                    
                    if res.status_code in [200, 204]:
                        print(f"  [SUCCESS] {m_identity.ljust(15)} -> {role_name} ({scope})")
                        success_count += 1

        # --- LOGIC FOR ORGANIZATIONS / APPLICATIONS (List Structure) ---
        elif scope in ['organizations', 'applications']:
            o_type = "organization" if scope == 'organizations' else "application"
            target_map = target_orgs if scope == 'organizations' else target_apps
            
            for item in content:
                item_name = item.get('name', '').lower()
                target_id = target_map.get(item_name)
                if not target_id: continue

                # Diagnostic showed 'memberships' is the key here
                for m_group in item.get('memberships', []):
                    role_name = role_id_map.get(m_group.get('roleId'), '').lower()
                    t_role_id = target_roles.get(role_name)
                    if not t_role_id: continue

                    for member in m_group.get('members', []):
                        m_identity = member.get('name') or member.get('userOrGroupId') or member.get('id')
                        m_type = member.get('type')
                        
                        if not m_identity: continue

                        url = f"{config.TARGET_URL}/api/v2/rolePrivileges/{o_type}/{target_id}/role/{t_role_id}"
                        res = requests.post(url, auth=config.TARGET_AUTH, json={"type": m_type, "name": m_identity})
                        
                        if res.status_code in [200, 204]:
                            print(f"  [SUCCESS] {m_identity.ljust(15)} -> {role_name} ({item['name']})")
                            success_count += 1

    print(f"\n--- FINISHED. Total assignments: {success_count} ---")

if __name__ == "__main__":
    main()

    