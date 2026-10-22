#!/bin/bash
set -euo pipefail
# Apply Error Fix Script
# Purpose: Applies error fix to source file using specified fix type (replace_line, insert_line, delete_line, replace_text)
# Input: $1 = file_path, $2 = line_number, $3 = fix_type, $4 = old_text, $5 = new_text, $6 = backup (true/false)
# Output: Success message to stdout, errors to stderr
# Exit: 0 on success, 1 on failure
# Example: ./apply-error-fix.sh "src/File.cs" 10 "replace_line" "old code" "new code" "true"
# Example Output: "SUCCESS: Fix applied to src/File.cs at line 10"

FILE_PATH="$1"
LINE_NUMBER="$2"
FIX_TYPE="$3"
OLD_TEXT="$4"
NEW_TEXT="$5"
BACKUP="${6:-true}"

if [ -z "$FILE_PATH" ] || [ -z "$LINE_NUMBER" ] || [ -z "$FIX_TYPE" ]; then
    echo "ERROR: Missing required parameters" >&2
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "ERROR: File not found: $FILE_PATH" >&2
    exit 1
fi

# Create backup if requested
if [ "$BACKUP" = "true" ]; then
    BACKUP_FILE="${FILE_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$FILE_PATH" "$BACKUP_FILE"
    echo "INFO: Backup created: $BACKUP_FILE"
fi

# Apply fix based on type
case "$FIX_TYPE" in
    replace_line)
        if [ -z "$OLD_TEXT" ] || [ -z "$NEW_TEXT" ]; then
            echo "ERROR: old_text and new_text required for replace_line" >&2
            exit 1
        fi
        sed -i "${LINE_NUMBER}s|.*|${NEW_TEXT}|" "$FILE_PATH"
        ;;
    insert_line)
        if [ -z "$NEW_TEXT" ]; then
            echo "ERROR: new_text required for insert_line" >&2
            exit 1
        fi
        sed -i "${LINE_NUMBER}i\\${NEW_TEXT}" "$FILE_PATH"
        ;;
    delete_line)
        sed -i "${LINE_NUMBER}d" "$FILE_PATH"
        ;;
    replace_text)
        if [ -z "$OLD_TEXT" ] || [ -z "$NEW_TEXT" ]; then
            echo "ERROR: old_text and new_text required for replace_text" >&2
            exit 1
        fi
        # Escape special characters for sed
        OLD_TEXT_ESC=$(printf '%s\n' "$OLD_TEXT" | sed 's/[[\.*^$()+?{|]/\\&/g')
        sed -i "s|${OLD_TEXT_ESC}|${NEW_TEXT}|g" "$FILE_PATH"
        ;;
    *)
        echo "ERROR: Unknown fix type: $FIX_TYPE" >&2
        exit 1
        ;;
esac

if [ $? -eq 0 ]; then
    echo "SUCCESS: Fix applied to $FILE_PATH at line $LINE_NUMBER"
    exit 0
else
    echo "ERROR: Failed to apply fix" >&2
    exit 1
fi

