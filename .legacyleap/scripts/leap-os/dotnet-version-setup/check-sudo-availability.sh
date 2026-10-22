#!/bin/bash
# Check Sudo Availability Script
# Output: "available_passwordless", "available_with_password", or "not_available" (stdout)
# Exit: 0 on success, 1 on failure

set -euo pipefail

# Check if sudo command exists
if ! command -v sudo &> /dev/null; then
    echo "ERROR: sudo command not found" >&2
    echo "not_available" >&2
    exit 1
fi

# Check if user has sudo privileges (passwordless)
if sudo -n true 2>/dev/null; then
    echo "available_passwordless"
    exit 0
fi

# Check if user has sudo privileges (may require password)
if sudo -v 2>/dev/null; then
    # Check if password is cached
    if sudo -n true 2>/dev/null; then
        echo "available_passwordless"
    else
        echo "available_with_password"
    fi
    exit 0
else
    # Check if we're already root
    if [ "$(id -u)" -eq 0 ]; then
        echo "available_passwordless"
        exit 0
    fi
    
    # Sudo exists but user doesn't have privileges
    echo "ERROR: sudo is available but user does not have sudo privileges" >&2
    echo "not_available" >&2
    exit 1
fi

