#!/bin/bash
# Check SDK Installed Script
# Input: $1 = sanitized version (X.Y.Z format)
# Output: "exact", "compatible:<version>", or "not_found" (stdout)
# Exit: 0 on success, 1 on failure

set -euo pipefail

REQUIRED_VERSION="$1"

if [ -z "$REQUIRED_VERSION" ]; then
    echo "ERROR: Version not provided" >&2
    exit 1
fi

# Step 1: Check if dotnet command exists
if ! command -v dotnet &> /dev/null; then
    # Check common installation locations
    DOTNET_PATHS=(
        "/usr/local/share/dotnet/dotnet"
        "$HOME/.dotnet/dotnet"
        "/usr/share/dotnet/dotnet"
        "/opt/dotnet/dotnet"
    )
    
    DOTNET_FOUND=false
    for path in "${DOTNET_PATHS[@]}"; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            export PATH="$(dirname "$path"):$PATH"
            DOTNET_FOUND=true
            break
        fi
    done
    
    if [ "$DOTNET_FOUND" = false ]; then
        echo "not_found"
        exit 0
    fi
fi

# Step 2: Get installed SDKs
INSTALLED_SDKS=$(dotnet --list-sdks 2>/dev/null || echo "")

if [ -z "$INSTALLED_SDKS" ]; then
    echo "not_found"
    exit 0
fi

# Step 3: Check for exact match
if echo "$INSTALLED_SDKS" | grep -q "^${REQUIRED_VERSION}"; then
    echo "exact"
    exit 0
fi

# Step 4: Check for compatible minor version (X.Y.*)
MAJOR_MINOR=$(echo "$REQUIRED_VERSION" | cut -d. -f1,2)
COMPATIBLE=$(echo "$INSTALLED_SDKS" | grep "^${MAJOR_MINOR}\." | head -1 | awk '{print $1}')

if [ -n "$COMPATIBLE" ]; then
    echo "compatible:$COMPATIBLE"
    exit 0
fi

# Step 5: Not found
echo "not_found"
exit 0

