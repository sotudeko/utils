#!/bin/sh
IQ_URL="http://localhost:8070"
CREDENTIALS="admin:admin123"
OUTPUT_FILE="role_memberships_export.json"

GLOBAL=$(curl -s -u $CREDENTIALS "$IQ_URL/api/v2/roleMemberships/global")
ROLES=$(curl -s -u $CREDENTIALS "$IQ_URL/api/v2/roles")

jq -n \
  --argjson global "$GLOBAL" \
  --argjson roles "$ROLES" \
  '{"global": $global, "roles": $roles}' > "$OUTPUT_FILE"

echo "Export complete: $OUTPUT_FILE"