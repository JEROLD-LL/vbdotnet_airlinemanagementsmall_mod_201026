#!/bin/bash
set -euo pipefail
# Cleanup Temporary Files Script
# Purpose: Cleans up temporary files created during execution
# Input: $1 = file_pattern (optional, default: all temp files in .agent-state/.tmp/)
# Output: None (deletes files)
# Exit: 0 on success, 1 on failure
# Example: ./cleanup-temp-files.sh "build-output.txt"
# Example: ./cleanup-temp-files.sh (cleans all temp files)

FILE_PATTERN="${1:-*}"

TEMP_DIR=".legacyleap/.agent-state/.tmp"

if [ ! -d "$TEMP_DIR" ]; then
    # Directory doesn't exist, nothing to clean
    exit 0
fi

# Delete files matching pattern
if [ "$FILE_PATTERN" = "*" ]; then
    # Clean all temporary files
    find "$TEMP_DIR" -type f -name "*" -delete 2>/dev/null || true
    echo "INFO: Cleaned all temporary files from $TEMP_DIR"
else
    # Clean specific pattern
    find "$TEMP_DIR" -type f -name "$FILE_PATTERN" -delete 2>/dev/null || true
    echo "INFO: Cleaned files matching pattern: $FILE_PATTERN from $TEMP_DIR"
fi

exit 0

