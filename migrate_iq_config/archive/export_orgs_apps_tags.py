import requests
import json
import os
import config

def get_iq_data(endpoint):
    res = requests.get(f"{config.SOURCE_URL}/api/v2/{endpoint}", auth=config.SOURCE_AUTH)
    return res.json() if res.status_code == 200 else None

def main():
    print("--- STARTING HIERARCHICAL TREE EXPORT ---")
    
    # 1. Get all raw data
    all_orgs = get_iq_data("organizations").get('organizations', [])
    all_apps = get_iq_data("applications").get('applications', [])
    
    # 2. Build a Map for quick lookup
    org_map = {org['id']: org for org in all_orgs}
    
    # 3. Identify children for each parent
    hierarchy = {}
    for org in all_orgs:
        p_id = org.get('parentId')
        if p_id not in hierarchy:
            hierarchy[p_id] = {'orgs': [], 'apps': []}
        hierarchy[p_id]['orgs'].append(org)

    for app in all_apps:
        p_id = app.get('organizationId')
        if p_id not in hierarchy:
            hierarchy[p_id] = {'orgs': [], 'apps': []}
        hierarchy[p_id]['apps'].append(app)

    # 4. Recursive function to build the nested tree
    def build_tree(parent_id):
        current_node = hierarchy.get(parent_id, {'orgs': [], 'apps': []})
        tree = []
        
        for org in current_node['orgs']:
            org_node = {
                "name": org['name'],
                "id": org['id'],
                "type": "organization",
                "tags": org.get('tags', []),
                "children": build_tree(org['id']), # Recursive call
                "applications": hierarchy.get(org['id'], {}).get('apps', [])
            }
            tree.append(org_node)
        return tree

    # Find the Root (usually has parentId None or is the only one at the top)
    # Most IQ setups have one 'Root Organization'
    root_org = next((o for o in all_orgs if o['name'] == 'Root Organization'), all_orgs[0])
    
    final_tree = {
        "root": {
            "name": root_org['name'],
            "id": root_org['id'],
            "tags": root_org.get('tags', []),
            "content": build_tree(root_org['id'])
        }
    }

    output_path = os.path.join(config.DATA_DIR, "hierarchical_export.json")
    with open(output_path, "w") as f:
        json.dump(final_tree, f, indent=2)

    print(f"--- FINISHED ---")
    print(f"Tree structure saved to: {output_path}")

if __name__ == "__main__":
    main()
    