#!/bin/bash
set -euo pipefail
# Save Version Info Script
# Purpose: Saves .NET version information to consolidated execution-state.json file
# Input: $1 = version (X.Y.Z format), $2 = source (file name), $3 = sdk_installed (true/false)
# Output: None (writes to .legacyleap/.agent-state/execution-state.json)
# Exit: 0 on success, 1 on failure
# Example: ./save-version-info.sh "8.0.0" "global.json" true
# Example Output: Updates .legacyleap/.agent-state/execution-state.json with version info

set -euo pipefail

VERSION="$1"
SOURCE="$2"
SDK_INSTALLED="${3:-false}"

if [ -z "$VERSION" ]; then
    echo "ERROR: Version not provided" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Create version info JSON
VERSION_INFO=$(jq -n \
    --arg version "$VERSION" \
    --arg source "${SOURCE:-unknown}" \
    --argjson sdk_installed "$(if [ "$SDK_INSTALLED" = "true" ]; then echo "true"; else echo "false"; fi)" \
    '{
        version: $version,
        source: $source,
        sdk_installed: $sdk_installed
    }')

# Use manage-execution-state.sh to update version info
if [ -f ".legacyleap/scripts/shared/manage-execution-state.sh" ]; then
    bash ".legacyleap/scripts/shared/manage-execution-state.sh" "update_version" "$VERSION_INFO"
    exit $?
else
    echo "ERROR: manage-execution-state.sh not found" >&2
    exit 1
fi

