#!/bin/bash
# Restore PATH Script
# Input: $1 = backup_file path
# Exit: 0 on success, 1 on failure

set -euo pipefail

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file path not provided" >&2
    exit 1
fi

# Step 1: Validate backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

# Step 2: Security validation - ensure file is in home directory
if [[ "$BACKUP_FILE" != "$HOME"/* ]]; then
    echo "ERROR: Invalid backup file path (path traversal detected): $BACKUP_FILE" >&2
    exit 1
fi

# Step 3: Read backup
BACKUP_PATH=$(cat "$BACKUP_FILE" 2>/dev/null)

if [ -z "$BACKUP_PATH" ]; then
    echo "ERROR: Backup file is empty: $BACKUP_FILE" >&2
    exit 1
fi

# Step 4: Restore PATH
export PATH="$BACKUP_PATH"

# Step 5: Verify restoration
if [ "$PATH" = "$BACKUP_PATH" ]; then
    echo "SUCCESS: PATH restored from backup"
    exit 0
else
    echo "WARNING: PATH restoration may have failed. Expected: $BACKUP_PATH, Got: $PATH" >&2
    exit 1
fi

