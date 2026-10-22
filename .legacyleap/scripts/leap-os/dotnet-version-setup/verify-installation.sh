#!/bin/bash
# Verify Installation Script
# Input: $1 = version (sanitized), $2 = max_retries (optional, default: 3)
# Exit: 0 on success, 1 on failure

set -euo pipefail

REQUIRED_VERSION="$1"
MAX_RETRIES="${2:-3}"
RETRY_COUNT=0
RETRY_DELAY=2
VERIFICATION_SUCCESS=false

if [ -z "$REQUIRED_VERSION" ]; then
    echo "ERROR: Version not provided" >&2
    exit 1
fi

# Validate version format
if ! [[ "$REQUIRED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Invalid version format: $REQUIRED_VERSION" >&2
    exit 1
fi

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check if dotnet command exists
    if ! command -v dotnet &> /dev/null; then
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "WARNING: dotnet command not found in PATH (attempt $RETRY_COUNT/$MAX_RETRIES)" >&2
            sleep $RETRY_DELAY
            continue
        else
            echo "ERROR: dotnet command not found after $MAX_RETRIES attempts" >&2
            exit 1
        fi
    fi
    
    # Get installed SDKs
    INSTALLED_SDKS=$(dotnet --list-sdks 2>/dev/null || echo "")
    
    if [ -z "$INSTALLED_SDKS" ]; then
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "WARNING: No SDKs found (attempt $RETRY_COUNT/$MAX_RETRIES)" >&2
            sleep $RETRY_DELAY
            continue
        fi
    else
        # Check for exact version
        if echo "$INSTALLED_SDKS" | grep -q "^${REQUIRED_VERSION}"; then
            echo "SUCCESS: .NET SDK ${REQUIRED_VERSION} verified"
            VERIFICATION_SUCCESS=true
            break
        fi
        
        # Check for compatible minor version
        MAJOR_MINOR=$(echo "$REQUIRED_VERSION" | cut -d. -f1,2)
        COMPATIBLE=$(echo "$INSTALLED_SDKS" | grep "^${MAJOR_MINOR}\." | head -1 | awk '{print $1}')
        
        if [ -n "$COMPATIBLE" ]; then
            echo "SUCCESS: Compatible .NET SDK version found: $COMPATIBLE (required: $REQUIRED_VERSION)"
            VERIFICATION_SUCCESS=true
            break
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "Retrying verification... ($RETRY_COUNT/$MAX_RETRIES)" >&2
        sleep $RETRY_DELAY
    fi
done

if [ "$VERIFICATION_SUCCESS" = false ]; then
    echo "ERROR: Verification failed after $MAX_RETRIES attempts" >&2
    exit 1
fi

exit 0

