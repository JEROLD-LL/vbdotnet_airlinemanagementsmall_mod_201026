#!/bin/bash
# Check Disk Space Script
# Input: $1 = required_space_gb (default: 2.0), $2 = install_path (optional)
# Exit: 0 on success, 1 on failure

set -euo pipefail

REQUIRED_SPACE_GB="${1:-2.0}"
INSTALL_PATH="${2:-}"

# Determine installation path if not provided
if [ -z "$INSTALL_PATH" ]; then
    case "$OSTYPE" in
        darwin*)
            if [ -d "/usr/local" ]; then
                INSTALL_PATH="/usr/local"
            else
                INSTALL_PATH="$HOME/.dotnet"
            fi
            ;;
        linux*)
            if [ -d "/usr/share" ]; then
                INSTALL_PATH="/usr/share"
            else
                INSTALL_PATH="$HOME/.dotnet"
            fi
            ;;
        *)
            INSTALL_PATH="$HOME/.dotnet"
            ;;
    esac
fi

# Get available disk space
if [[ "$OSTYPE" == "darwin"* ]]; then
    AVAILABLE_GB=$(df -g "$INSTALL_PATH" | tail -1 | awk '{print $4}')
elif [[ "$OSTYPE" == "linux"* ]]; then
    AVAILABLE_BYTES=$(df -B1 "$INSTALL_PATH" | tail -1 | awk '{print $4}')
    AVAILABLE_GB=$(echo "scale=2; $AVAILABLE_BYTES / 1073741824" | bc)
else
    AVAILABLE_BYTES=$(df -B1 "$INSTALL_PATH" 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -z "$AVAILABLE_BYTES" ]; then
        echo "ERROR: Cannot determine available disk space for $INSTALL_PATH" >&2
        exit 1
    fi
    AVAILABLE_GB=$(echo "scale=2; $AVAILABLE_BYTES / 1073741824" | bc)
fi

# Compare available space with required space
if (( $(echo "$AVAILABLE_GB < $REQUIRED_SPACE_GB" | bc -l) )); then
    echo "ERROR: Insufficient disk space" >&2
    echo "Required: ${REQUIRED_SPACE_GB} GB" >&2
    echo "Available: ${AVAILABLE_GB} GB at $INSTALL_PATH" >&2
    exit 1
fi

echo "SUCCESS: Sufficient disk space available"
exit 0

