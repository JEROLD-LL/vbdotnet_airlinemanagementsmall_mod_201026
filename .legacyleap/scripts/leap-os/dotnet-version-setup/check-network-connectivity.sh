#!/bin/bash
# Check Network Connectivity Script
# Input: $1 = url (optional, default: https://dot.net)
# Exit: 0 on success, 1 on failure

set -euo pipefail

URL="${1:-https://dot.net}"
TIMEOUT=5

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "ERROR: curl command not found. Cannot check network connectivity." >&2
    exit 1
fi

# Check connectivity with SSL validation
if curl -sSL --max-time "$TIMEOUT" --fail --show-error \
    --cert-status \
    --location \
    "$URL" > /dev/null 2>&1; then
    echo "SUCCESS: Network connectivity verified to $URL"
    exit 0
else
    EXIT_CODE=$?
    case $EXIT_CODE in
        6)
            echo "ERROR: DNS resolution failed for $URL" >&2
            ;;
        7)
            echo "ERROR: Cannot connect to $URL (connection refused)" >&2
            ;;
        28)
            echo "ERROR: Network check timed out after ${TIMEOUT} seconds" >&2
            ;;
        *)
            echo "ERROR: No network connectivity to $URL (exit code: $EXIT_CODE)" >&2
            ;;
    esac
    exit 1
fi

