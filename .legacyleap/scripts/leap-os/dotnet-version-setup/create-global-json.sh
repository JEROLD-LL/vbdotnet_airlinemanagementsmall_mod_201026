#!/bin/bash
set -euo pipefail
# Create Global JSON Script
# Purpose: Creates or updates global.json file to pin .NET SDK version
# Input: $1 = version (X.Y.Z format), $2 = project_root (optional, default: current directory)
# Output: Creates/updates global.json in project root
# Exit: 0 on success, 1 on failure
# Example: ./create-global-json.sh "8.0.0" "."
# Example Output: Creates/updates global.json with SDK version pinning

VERSION="$1"
PROJECT_ROOT="${2:-.}"

if [ -z "$VERSION" ]; then
    echo "ERROR: Version not provided" >&2
    exit 1
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project root directory not found: $PROJECT_ROOT" >&2
    exit 1
fi

# Validate version format (X.Y.Z)
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Invalid version format. Expected X.Y.Z format, got: $VERSION" >&2
    exit 1
fi

GLOBAL_JSON="$PROJECT_ROOT/global.json"

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON manipulation." >&2
    exit 1
fi

# Create or update global.json
if [ -f "$GLOBAL_JSON" ]; then
    # Update existing global.json
    # Check if it's valid JSON first
    if ! jq empty "$GLOBAL_JSON" 2>/dev/null; then
        echo "WARNING: Existing global.json is invalid JSON, will be overwritten" >&2
        # Create new structure
        jq -n \
            --arg version "$VERSION" \
            '{
                sdk: {
                    version: $version,
                    rollForward: "latestMinor"
                }
            }' > "$GLOBAL_JSON"
    else
        # Update existing valid JSON
        # Check if sdk section exists
        if jq -e '.sdk' "$GLOBAL_JSON" > /dev/null 2>&1; then
            # Update version in existing sdk section
            jq --arg version "$VERSION" '.sdk.version = $version' "$GLOBAL_JSON" > "$GLOBAL_JSON.tmp" && mv "$GLOBAL_JSON.tmp" "$GLOBAL_JSON"
        else
            # Add sdk section
            jq --arg version "$VERSION" '. + {sdk: {version: $version, rollForward: "latestMinor"}}' "$GLOBAL_JSON" > "$GLOBAL_JSON.tmp" && mv "$GLOBAL_JSON.tmp" "$GLOBAL_JSON"
        fi
    fi
    echo "INFO: Updated global.json with SDK version: $VERSION"
else
    # Create new global.json
    jq -n \
        --arg version "$VERSION" \
        '{
            sdk: {
                version: $version,
                rollForward: "latestMinor"
            }
        }' > "$GLOBAL_JSON"
    echo "INFO: Created global.json with SDK version: $VERSION"
fi

# Verify the file was created/updated correctly
if [ ! -f "$GLOBAL_JSON" ]; then
    echo "ERROR: Failed to create/update global.json" >&2
    exit 1
fi

# Validate the created JSON
if ! jq empty "$GLOBAL_JSON" 2>/dev/null; then
    echo "ERROR: Created global.json is invalid JSON" >&2
    exit 1
fi

# Verify version was set correctly
ACTUAL_VERSION=$(jq -r '.sdk.version // empty' "$GLOBAL_JSON")
if [ "$ACTUAL_VERSION" != "$VERSION" ]; then
    echo "ERROR: Version mismatch in global.json. Expected: $VERSION, Got: $ACTUAL_VERSION" >&2
    exit 1
fi

echo "SUCCESS: global.json created/updated with SDK version: $VERSION"
exit 0

