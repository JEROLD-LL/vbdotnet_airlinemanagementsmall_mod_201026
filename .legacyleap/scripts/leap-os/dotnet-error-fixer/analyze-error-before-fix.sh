#!/bin/bash
set -euo pipefail
# Analyze Error Before Fix Script
# Input: $1 = error_json, $2 = file_content (optional), $3 = dotnet_version
# Exit code: 0 on success, 1 on failure
# Output: Analysis result with fix recommendation and confidence level

ERROR_JSON="$1"
FILE_CONTENT="${2:-}"
DOTNET_VERSION="$3"

if [ -z "$ERROR_JSON" ] || [ -z "$DOTNET_VERSION" ]; then
    echo "ERROR: Missing required parameters" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Extract error details
ERROR_FILE=$(echo "$ERROR_JSON" | jq -r '.file')
ERROR_LINE=$(echo "$ERROR_JSON" | jq -r '.line')
ERROR_CODE=$(echo "$ERROR_JSON" | jq -r '.code')
ERROR_MESSAGE=$(echo "$ERROR_JSON" | jq -r '.message')

# Read file content if not provided
if [ -z "$FILE_CONTENT" ] && [ -f "$ERROR_FILE" ]; then
    FILE_CONTENT=$(cat "$ERROR_FILE")
fi

if [ -z "$FILE_CONTENT" ]; then
    echo "ERROR: File content not available" >&2
    exit 1
fi

# Extract context (5 lines before and after error line)
CONTEXT_START=$((ERROR_LINE - 5))
CONTEXT_END=$((ERROR_LINE + 5))
if [ $CONTEXT_START -lt 1 ]; then
    CONTEXT_START=1
fi

CONTEXT=$(echo "$FILE_CONTENT" | sed -n "${CONTEXT_START},${CONTEXT_END}p")

# Basic validation: Check if error line exists in file
TOTAL_LINES=$(echo "$FILE_CONTENT" | wc -l | tr -d ' ')
if [ "$ERROR_LINE" -gt "$TOTAL_LINES" ]; then
    echo "ERROR: Error line $ERROR_LINE exceeds file length $TOTAL_LINES" >&2
    exit 1
fi

# Extract error line content
ERROR_LINE_CONTENT=$(echo "$FILE_CONTENT" | sed -n "${ERROR_LINE}p")

# Extract method signature if error is in a method (for API contract preservation)
# Look for method declaration before error line
METHOD_SIGNATURE=""
if [[ "$ERROR_CODE" =~ ^CS(0029|0266|1503|1504|0246) ]]; then
    # Type mismatch or reference errors - check for method signature
    # Look backwards from error line for method declaration
    for i in $(seq $ERROR_LINE -1 1); do
        LINE_CONTENT=$(echo "$FILE_CONTENT" | sed -n "${i}p")
        if [[ "$LINE_CONTENT" =~ ^[[:space:]]*(public|private|protected|internal)[[:space:]]+(static[[:space:]]+)?[[:alnum:]_<>\[\]]+[[:space:]]+[[:alnum:]_]+[[:space:]]*\( ]]; then
            METHOD_SIGNATURE="$LINE_CONTENT"
            break
        fi
    done
fi

# Output analysis structure (LLM will fill in details)
jq -n \
    --arg file "$ERROR_FILE" \
    --argjson line "$ERROR_LINE" \
    --arg code "$ERROR_CODE" \
    --arg message "$ERROR_MESSAGE" \
    --arg context "$CONTEXT" \
    --arg error_line_content "$ERROR_LINE_CONTENT" \
    --arg method_signature "$METHOD_SIGNATURE" \
    --arg dotnet_version "$DOTNET_VERSION" \
    '{
        error: {
            file: $file,
            line: $line,
            code: $code,
            message: $message
        },
        context: $context,
        error_line_content: $error_line_content,
        method_signature: $method_signature,
        dotnet_version: $dotnet_version,
        api_contract_preservation: true,
        contract_change_allowed: false,
        requires_llm_analysis: true,
        confidence_level: null,
        fix_recommendation: null,
        should_fix: false,
        type_mismatch_root_cause: null
    }'

exit 0

