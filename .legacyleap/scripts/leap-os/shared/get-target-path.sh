#!/bin/bash
set -euo pipefail
# Get Target Path Script
# Purpose: Reads target path from metadata.json (at same level as .legacyleap), returns absolute path or current directory
# Output: Absolute path to stdout
# Exit: 0 on success, 1 on error
# Example: ./get-target-path.sh
# Example Output: /absolute/path/to/target/ or .

# Find metadata.json (at same level as .legacyleap)
# Try current directory first
if [ -f "metadata.json" ]; then
    METADATA_FILE="metadata.json"
    BASE_DIR="$(pwd)"
# Try parent directory (if .legacyleap is in current dir)
elif [ -f "../metadata.json" ] && [ -d ".legacyleap" ]; then
    METADATA_FILE="../metadata.json"
    BASE_DIR="$(cd .. && pwd)"
# Try walking up to find .legacyleap and metadata.json
else
    CURRENT_DIR="$(pwd)"
    FOUND=false
    
    while [ "$CURRENT_DIR" != "/" ]; do
        if [ -d "$CURRENT_DIR/.legacyleap" ] && [ -f "$CURRENT_DIR/metadata.json" ]; then
            METADATA_FILE="$CURRENT_DIR/metadata.json"
            BASE_DIR="$CURRENT_DIR"
            FOUND=true
            break
        fi
        CURRENT_DIR=$(dirname "$CURRENT_DIR")
    done
    
    if [ "$FOUND" = false ]; then
        # No metadata.json found - return current directory
        echo "."
        exit 0
    fi
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "WARNING: jq not found, cannot parse metadata.json" >&2
    echo "."
    exit 0
fi

# Validate JSON
if ! jq empty "$METADATA_FILE" 2>/dev/null; then
    echo "ERROR: Invalid JSON in metadata.json: $METADATA_FILE" >&2
    exit 1
fi

# Read the modernize path
PATH_VALUE=$(jq -r '.modernize // "."' "$METADATA_FILE" 2>/dev/null)

# Check if path was found
if [ -z "$PATH_VALUE" ] || [ "$PATH_VALUE" = "." ] || [ "$PATH_VALUE" = "null" ]; then
    # No modernize key or it's empty/null - return current directory
    echo "."
    exit 0
fi

# Resolve to absolute path
if [[ "$PATH_VALUE" = /* ]]; then
    # Absolute path provided
    RESOLVED_PATH="$PATH_VALUE"
else
    # Relative path - resolve from metadata.json location
    RESOLVED_PATH=$(cd "$BASE_DIR" && cd "$PATH_VALUE" && pwd 2>/dev/null || echo "")
fi

# Validate resolved path
if [ -z "$RESOLVED_PATH" ]; then
    echo "ERROR: Failed to resolve path: $PATH_VALUE (from: $BASE_DIR)" >&2
    exit 1
fi

# Validate path exists
if [ ! -d "$RESOLVED_PATH" ]; then
    echo "ERROR: Target path does not exist: $RESOLVED_PATH" >&2
    exit 1
fi

# Output resolved absolute path
echo "$RESOLVED_PATH"
exit 0

