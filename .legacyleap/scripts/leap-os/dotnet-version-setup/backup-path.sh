#!/bin/bash
# Backup PATH Script
# Output: backup file path (stdout) or error (stderr)
# Exit: 0 on success, 1 on failure

set -euo pipefail

if [ -z "$PATH" ]; then
    echo "ERROR: PATH is empty, nothing to backup" >&2
    exit 1
fi

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S 2>/dev/null || echo "$(date +%s)")
BACKUP_FILE="$HOME/.dotnet-path-backup-${TIMESTAMP}.txt"

# Security validation: Ensure backup file is in home directory
if [[ "$BACKUP_FILE" != "$HOME"/* ]]; then
    echo "ERROR: Invalid backup file path (path traversal detected): $BACKUP_FILE" >&2
    exit 1
fi

# Create backup
if echo "$PATH" > "$BACKUP_FILE" 2>/dev/null; then
    # Verify file was created and is readable
    if [ -f "$BACKUP_FILE" ] && [ -r "$BACKUP_FILE" ]; then
        echo "$BACKUP_FILE"
        exit 0
    else
        echo "ERROR: Backup file could not be created or verified: $BACKUP_FILE" >&2
        exit 1
    fi
else
    echo "ERROR: Failed to create backup file: $BACKUP_FILE" >&2
    exit 1
fi

