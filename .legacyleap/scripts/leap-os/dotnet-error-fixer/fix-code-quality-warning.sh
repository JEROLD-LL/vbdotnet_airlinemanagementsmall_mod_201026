#!/bin/bash
set -euo pipefail
# Fix Code Quality Warning Script
# Input: $1 = warning_json, $2 = file_content (optional), $3 = dotnet_version
# Exit code: 0 on success, 1 on failure
# Output: Fix result with status

WARNING_JSON="$1"
FILE_CONTENT="${2:-}"
DOTNET_VERSION="$3"

if [ -z "$WARNING_JSON" ] || [ -z "$DOTNET_VERSION" ]; then
    echo "ERROR: Missing required parameters" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Extract warning details
WARNING_FILE=$(echo "$WARNING_JSON" | jq -r '.file')
WARNING_LINE=$(echo "$WARNING_JSON" | jq -r '.line')
WARNING_CODE=$(echo "$WARNING_JSON" | jq -r '.code')
WARNING_MESSAGE=$(echo "$WARNING_JSON" | jq -r '.message')

# Read file content if not provided
if [ -z "$FILE_CONTENT" ] && [ -f "$WARNING_FILE" ]; then
    FILE_CONTENT=$(cat "$WARNING_FILE")
fi

if [ -z "$FILE_CONTENT" ]; then
    echo "ERROR: File content not available" >&2
    exit 1
fi

# Determine fix type based on warning code
FIX_TYPE=""
case "$WARNING_CODE" in
    CS0162)
        FIX_TYPE="unreachable_code"  # Remove unreachable code
        ;;
    CS0168|CS0219|CS0414|CS0649)
        FIX_TYPE="unused_variable"  # Remove unused variable
        ;;
    CS8019)
        FIX_TYPE="unused_using"  # Remove unused using directive
        ;;
    CS8600|CS8601|CS8602|CS8603|CS8604|CS8605|CS8606|CS8607|CS8608|CS8609|CS8610|CS8611|CS8612|CS8613|CS8614|CS8615|CS8616|CS8617|CS8618|CS8619|CS8620|CS8621|CS8622|CS8624|CS8625|CS8629|CS8631|CS8632|CS8633|CS8634|CS8767|CS8768|CS8769)
        FIX_TYPE="nullable_annotation"  # Fix nullable annotation
        ;;
    *)
        FIX_TYPE="unknown"
        ;;
esac

# Output fix structure (LLM will fill in details)
jq -n \
    --arg file "$WARNING_FILE" \
    --argjson line "$WARNING_LINE" \
    --arg code "$WARNING_CODE" \
    --arg message "$WARNING_MESSAGE" \
    --arg fix_type "$FIX_TYPE" \
    --arg dotnet_version "$DOTNET_VERSION" \
    '{
        warning: {
            file: $file,
            line: $line,
            code: $code,
            message: $message
        },
        fix_type: $fix_type,
        dotnet_version: $dotnet_version,
        requires_llm_analysis: true,
        confidence_level: null,
        fix_recommendation: null,
        should_fix: false
    }'

exit 0

