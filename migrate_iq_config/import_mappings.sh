#!/bin/sh
IQ_URL="http://localhost:8070"
CREDENTIALS="admin:admin123"
INPUT_FILE="role_memberships_export.json"
ROLE_MAP_FILE="/tmp/role_map.txt"

# Step 1: Build role name-to-id map from TARGET server
curl -s -u $CREDENTIALS "$IQ_URL/api/v2/roles" | \
  jq -r '.roles[] | "\(.name)=\(.id)"' > "$ROLE_MAP_FILE"

echo "Role ID map built."

# Helper: look up role ID by name
get_role_id() {
  grep "^${1}=" "$ROLE_MAP_FILE" | cut -d'=' -f2
}

# Step 2: Import global memberships
jq -c '.global.memberMappings[]' "$INPUT_FILE" | while IFS= read -r mapping; do
  ROLE_ID=$(echo "$mapping" | jq -r '.roleId')

  ROLE_NAME=$(jq -r --arg rid "$ROLE_ID" \
    '.roles.roles[] | select(.id == $rid) | .name' "$INPUT_FILE")
  TARGET_ROLE_ID=$(get_role_id "$ROLE_NAME")

  if [ -z "$TARGET_ROLE_ID" ]; then
    echo "WARNING: No matching role found for '$ROLE_NAME' on target. Skipping."
    continue
  fi

  echo "$mapping" | jq -c '.members[]' | while IFS= read -r member; do
    MEMBER_TYPE=$(echo "$member" | jq -r '.type' | tr '[:upper:]' '[:lower:]')
    MEMBER_NAME=$(echo "$member" | jq -r '.userOrGroupName')

    curl -s -u $CREDENTIALS -X PUT \
      "$IQ_URL/api/v2/roleMemberships/global/role/$TARGET_ROLE_ID/$MEMBER_TYPE/$MEMBER_NAME"
    echo "Assigned $MEMBER_NAME ($MEMBER_TYPE) to role '$ROLE_NAME'"
  done
done

echo "Import complete."
