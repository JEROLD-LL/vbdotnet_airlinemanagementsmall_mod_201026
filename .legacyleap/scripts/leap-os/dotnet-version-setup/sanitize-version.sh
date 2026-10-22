#!/bin/bash
# Sanitize Version Script
# Input: $1 = raw version string
# Output: sanitized version string (stdout) or error (stderr)
# Exit: 0 on success, 1 on failure

set -euo pipefail

VERSION_RAW="$1"

if [ -z "$VERSION_RAW" ]; then
    echo "ERROR: Version string is empty" >&2
    exit 1
fi

# Step 1: Sanitize - remove all non-numeric and non-dot characters
SANITIZED=$(echo "$VERSION_RAW" | sed 's/[^0-9.]//g')

if [ -z "$SANITIZED" ]; then
    echo "ERROR: Invalid version format: $VERSION_RAW (no valid characters found)" >&2
    exit 1
fi

# Step 2: Validate format matches X.Y.Z pattern
if ! [[ "$SANITIZED" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Invalid version format: $VERSION_RAW (sanitized: $SANITIZED). Expected format: X.Y.Z" >&2
    exit 1
fi

# Step 3: Validate range - major version must be between 1 and 20
MAJOR=$(echo "$SANITIZED" | cut -d. -f1)
if [ "$MAJOR" -lt 1 ] || [ "$MAJOR" -gt 20 ]; then
    echo "ERROR: Version out of range: $SANITIZED (major version must be 1-20)" >&2
    exit 1
fi

# Step 4: Return sanitized version
echo "$SANITIZED"
exit 0

