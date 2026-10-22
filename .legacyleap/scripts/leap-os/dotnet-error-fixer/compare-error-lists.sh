#!/bin/bash
set -euo pipefail
# Compare Error Lists Script
# Input: $1 = before_errors_json, $2 = after_errors_json
# Exit code: 0 on success, 1 on failure
# Output: Comparison result in JSON format

BEFORE_JSON="$1"
AFTER_JSON="$2"

if [ -z "$BEFORE_JSON" ] || [ -z "$AFTER_JSON" ]; then
    echo "ERROR: Both error lists required" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Create temporary files
BEFORE_FILE=$(mktemp)
AFTER_FILE=$(mktemp)
echo "$BEFORE_JSON" > "$BEFORE_FILE"
echo "$AFTER_JSON" > "$AFTER_FILE"

# Extract all errors (flatten categorized structure)
BEFORE_ERRORS=$(jq -c '[.errors[]? // .compilation_errors[]? // .reference_errors[]? // .syntax_errors[]? // .type_errors[]? // .nullable_errors[]? // .other_errors[]?]' "$BEFORE_FILE")
AFTER_ERRORS=$(jq -c '[.errors[]? // .compilation_errors[]? // .reference_errors[]? // .syntax_errors[]? // .type_errors[]? // .nullable_errors[]? // .other_errors[]?]' "$AFTER_FILE")

BEFORE_COUNT=$(echo "$BEFORE_ERRORS" | jq 'length')
AFTER_COUNT=$(echo "$AFTER_ERRORS" | jq 'length')

# Compare errors by file:line:code
# Fixed errors: in before but not in after
# Remaining errors: in both
# New errors: in after but not in before

FIXED_ERRORS=$(jq -c --argjson after "$AFTER_ERRORS" '
    map(select(
        . as $err |
        ($after | map(.file + ":" + (.line | tostring) + ":" + .code) | index($err.file + ":" + ($err.line | tostring) + ":" + $err.code)) == null
    ))
' <<< "$BEFORE_ERRORS")

REMAINING_ERRORS=$(jq -c --argjson after "$AFTER_ERRORS" '
    map(select(
        . as $err |
        ($after | map(.file + ":" + (.line | tostring) + ":" + .code) | index($err.file + ":" + ($err.line | tostring) + ":" + $err.code)) != null
    ))
' <<< "$BEFORE_ERRORS")

NEW_ERRORS=$(jq -c --argjson before "$BEFORE_ERRORS" '
    map(select(
        . as $err |
        ($before | map(.file + ":" + (.line | tostring) + ":" + .code) | index($err.file + ":" + ($err.line | tostring) + ":" + $err.code)) == null
    ))
' <<< "$AFTER_ERRORS")

FIXED_COUNT=$(echo "$FIXED_ERRORS" | jq 'length')
REMAINING_COUNT=$(echo "$REMAINING_ERRORS" | jq 'length')
NEW_COUNT=$(echo "$NEW_ERRORS" | jq 'length')

# Calculate success rate
if [ "$BEFORE_COUNT" -gt 0 ]; then
    if command -v bc &> /dev/null; then
        SUCCESS_RATE=$(echo "scale=2; $FIXED_COUNT * 100 / $BEFORE_COUNT" | bc)
    else
        # Fallback calculation without bc
        SUCCESS_RATE=$(awk "BEGIN {printf \"%.2f\", $FIXED_COUNT * 100 / $BEFORE_COUNT}")
    fi
else
    SUCCESS_RATE=100
fi

# Output comparison result
jq -n \
    --argjson before_count "$BEFORE_COUNT" \
    --argjson after_count "$AFTER_COUNT" \
    --argjson fixed_count "$FIXED_COUNT" \
    --argjson remaining_count "$REMAINING_COUNT" \
    --argjson new_count "$NEW_COUNT" \
    --argjson success_rate "$SUCCESS_RATE" \
    --argjson fixed_errors "$FIXED_ERRORS" \
    --argjson remaining_errors "$REMAINING_ERRORS" \
    --argjson new_errors "$NEW_ERRORS" \
    '{
        before_count: $before_count,
        after_count: $after_count,
        fixed_count: $fixed_count,
        remaining_count: $remaining_count,
        new_count: $new_count,
        success_rate: $success_rate,
        fixed_errors: $fixed_errors,
        remaining_errors: $remaining_errors,
        new_errors: $new_errors
    }'

# Cleanup
rm -f "$BEFORE_FILE" "$AFTER_FILE"
exit 0

