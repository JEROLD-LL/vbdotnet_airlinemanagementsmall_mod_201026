#!/bin/bash
set -euo pipefail
# Read Version Info Script
# Purpose: Reads .NET version information from consolidated execution-state.json or falls back to detection
# Input: $1 = fallback_to_detection (true/false, default: true)
# Output: Version info in JSON format to stdout
# Exit: 0 on success, 1 on failure
# Example: ./read-version-info.sh "true"
# Example Output:
# {
#   "version": "8.0.0",
#   "source": "global.json",
#   "sdk_installed": true,
#   "timestamp": "2024-01-01T00:00:00Z"
# }

FALLBACK_TO_DETECTION="${1:-true}"

# Try to read from consolidated execution-state.json first
if [ -f ".legacyleap/.agent-state/execution-state.json" ]; then
    if [ -f ".legacyleap/scripts/shared/manage-execution-state.sh" ]; then
        VERSION_DATA=$(bash ".legacyleap/scripts/shared/manage-execution-state.sh" "read_version" 2>/dev/null)
        if [ -n "$VERSION_DATA" ] && [ "$VERSION_DATA" != "{}" ]; then
            # Check if version field exists and is not empty
            if echo "$VERSION_DATA" | jq -e '.version // empty | length > 0' > /dev/null 2>&1; then
                echo "$VERSION_DATA"
                exit 0
            fi
        fi
    fi
fi

# Fallback: Check legacy dotnet-version.json (for backward compatibility during migration)
if [ -f ".legacyleap/dotnet-version.json" ]; then
    if command -v jq &> /dev/null; then
        if jq empty ".legacyleap/dotnet-version.json" 2>/dev/null; then
            cat ".legacyleap/dotnet-version.json"
            exit 0
        fi
    else
        cat ".legacyleap/dotnet-version.json"
        exit 0
    fi
fi

# File doesn't exist, fall back to detection if enabled
if [ "$FALLBACK_TO_DETECTION" = "true" ]; then
    echo "INFO: Version file not found, falling back to detection" >&2
    # Call detect-version-from-files script
    if [ -f ".legacyleap/scripts/dotnet-version-setup/detect-version-from-files.sh" ]; then
        bash ".legacyleap/scripts/dotnet-version-setup/detect-version-from-files.sh"
        exit $?
    else
        echo "ERROR: Version file not found and detect-version-from-files.sh not available" >&2
        exit 1
    fi
else
    echo "ERROR: Version file not found: .legacyleap/.agent-state/execution-state.json" >&2
    exit 1
fi

