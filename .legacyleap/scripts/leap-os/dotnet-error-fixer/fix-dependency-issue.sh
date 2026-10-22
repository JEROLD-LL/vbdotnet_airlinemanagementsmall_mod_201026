#!/bin/bash
set -euo pipefail
# Fix Dependency Issue Script
# Input: $1 = duplicate_package_json, $2 = action (remove_duplicate or unify_version)
# Exit code: 0 on success, 1 on failure
# Output: Fix result with status

DUPLICATE_JSON="$1"
ACTION="${2:-remove_duplicate}"

if [ -z "$DUPLICATE_JSON" ]; then
    echo "ERROR: Duplicate package JSON not provided" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Extract duplicate package details
PACKAGE_NAME=$(echo "$DUPLICATE_JSON" | jq -r '.package')
VERSION1=$(echo "$DUPLICATE_JSON" | jq -r '.version1')
FILE1=$(echo "$DUPLICATE_JSON" | jq -r '.file1')
VERSION2=$(echo "$DUPLICATE_JSON" | jq -r '.version2')
FILE2=$(echo "$DUPLICATE_JSON" | jq -r '.file2')

if [ -z "$PACKAGE_NAME" ] || [ -z "$FILE1" ] || [ -z "$FILE2" ]; then
    echo "ERROR: Invalid duplicate package JSON" >&2
    exit 1
fi

# Determine which version to keep (prefer higher version)
if [ "$(printf '%s\n' "$VERSION1" "$VERSION2" | sort -V | tail -1)" = "$VERSION1" ]; then
    KEEP_VERSION="$VERSION1"
    KEEP_FILE="$FILE1"
    REMOVE_FILE="$FILE2"
    REMOVE_VERSION="$VERSION2"
else
    KEEP_VERSION="$VERSION2"
    KEEP_FILE="$FILE2"
    REMOVE_FILE="$FILE1"
    REMOVE_VERSION="$VERSION1"
fi

# Create backup
if [ -f "$REMOVE_FILE" ]; then
    BACKUP_FILE="${REMOVE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$REMOVE_FILE" "$BACKUP_FILE"
    echo "INFO: Backup created: $BACKUP_FILE"
fi

# Remove duplicate package reference
if [ "$ACTION" = "remove_duplicate" ]; then
    # Remove PackageReference from REMOVE_FILE
    if command -v xmlstarlet &> /dev/null; then
        # Use xmlstarlet if available
        xmlstarlet ed -d "//PackageReference[@Include='$PACKAGE_NAME']" "$REMOVE_FILE" > "${REMOVE_FILE}.tmp" && mv "${REMOVE_FILE}.tmp" "$REMOVE_FILE"
    else
        # Fallback: Use sed to remove PackageReference line
        sed -i.bak "/PackageReference.*Include=\"$PACKAGE_NAME\"/d" "$REMOVE_FILE"
        rm -f "${REMOVE_FILE}.bak"
    fi
    
    echo "SUCCESS: Removed duplicate package reference: $PACKAGE_NAME ($REMOVE_VERSION) from $REMOVE_FILE"
    echo "INFO: Kept version: $KEEP_VERSION in $KEEP_FILE"
elif [ "$ACTION" = "unify_version" ]; then
    # Update both files to use the same version (prefer higher)
    if command -v xmlstarlet &> /dev/null; then
        xmlstarlet ed -u "//PackageReference[@Include='$PACKAGE_NAME']/@Version" -v "$KEEP_VERSION" "$FILE1" > "${FILE1}.tmp" && mv "${FILE1}.tmp" "$FILE1"
        xmlstarlet ed -u "//PackageReference[@Include='$PACKAGE_NAME']/@Version" -v "$KEEP_VERSION" "$FILE2" > "${FILE2}.tmp" && mv "${FILE2}.tmp" "$FILE2"
    else
        # Fallback: Use sed
        sed -i.bak "s|PackageReference.*Include=\"$PACKAGE_NAME\".*Version=\"[^\"]*\"|PackageReference Include=\"$PACKAGE_NAME\" Version=\"$KEEP_VERSION\"|g" "$FILE1"
        sed -i.bak "s|PackageReference.*Include=\"$PACKAGE_NAME\".*Version=\"[^\"]*\"|PackageReference Include=\"$PACKAGE_NAME\" Version=\"$KEEP_VERSION\"|g" "$FILE2"
        rm -f "${FILE1}.bak" "${FILE2}.bak"
    fi
    
    echo "SUCCESS: Unified package version: $PACKAGE_NAME to $KEEP_VERSION in both files"
fi

# Output result
jq -n \
    --arg package "$PACKAGE_NAME" \
    --arg action "$ACTION" \
    --arg keep_version "$KEEP_VERSION" \
    --arg remove_version "$REMOVE_VERSION" \
    --arg keep_file "$KEEP_FILE" \
    --arg remove_file "$REMOVE_FILE" \
    '{
        package: $package,
        action: $action,
        keep_version: $keep_version,
        remove_version: $remove_version,
        keep_file: $keep_file,
        remove_file: $remove_file,
        status: "success"
    }'

exit 0

