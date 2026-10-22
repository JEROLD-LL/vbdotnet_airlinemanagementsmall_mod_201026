#!/bin/bash
set -euo pipefail
# Detect Code Quality Issues Script
# Input: $1 = build_output_file (optional), $2 = project_root (optional), $3 = warnings_json (optional)
# Exit code: 0 on success, 1 on failure
# Output: Code quality issues in JSON format

BUILD_OUTPUT_FILE="$1"
PROJECT_ROOT="${2:-.}"
WARNINGS_JSON="$3"

# Initialize arrays
UNREACHABLE_CODE=()
UNUSED_VARIABLES=()
UNUSED_USING=()
NULLABLE_ISSUES=()

# If warnings JSON provided, analyze it
if [ -n "$WARNINGS_JSON" ]; then
    if command -v jq &> /dev/null; then
        # Extract unreachable code warnings (CS0162)
        UNREACHABLE_CODE=$(echo "$WARNINGS_JSON" | jq '[.[] | select(.code == "CS0162")]')
        
        # Extract unused variable warnings (CS0168, CS0219, CS0414, CS0649)
        UNUSED_VARIABLES=$(echo "$WARNINGS_JSON" | jq '[.[] | select(.code == "CS0168" or .code == "CS0219" or .code == "CS0414" or .code == "CS0649")]')
        
        # Extract unused using warnings (CS8019)
        UNUSED_USING=$(echo "$WARNINGS_JSON" | jq '[.[] | select(.code == "CS8019")]')
        
        # Extract nullable warnings (CS8600-CS8769)
        NULLABLE_ISSUES=$(echo "$WARNINGS_JSON" | jq '[.[] | select(.code | startswith("CS860") or startswith("CS861") or startswith("CS862") or startswith("CS863") or startswith("CS876"))]')
    fi
fi

# If build output file provided, parse it for additional issues
if [ -n "$BUILD_OUTPUT_FILE" ] && [ -f "$BUILD_OUTPUT_FILE" ]; then
    # Extract unreachable code from build output
    while IFS= read -r line; do
        if [[ "$line" =~ warning[[:space:]]+CS0162 ]]; then
            # Extract file and line from warning
            if [[ "$line" =~ ^([^:]+)\(([0-9]+) ]]; then
                FILE="${BASH_REMATCH[1]}"
                LINE="${BASH_REMATCH[2]}"
                UNREACHABLE_CODE+=("{\"file\":\"$FILE\",\"line\":$LINE,\"type\":\"unreachable_code\",\"code\":\"CS0162\",\"message\":\"Unreachable code detected\"}")
            fi
        fi
    done < "$BUILD_OUTPUT_FILE"
fi

# Output JSON
if command -v jq &> /dev/null; then
    jq -n \
        --argjson unreachable_code "$(if [ -n "$WARNINGS_JSON" ]; then echo "$UNREACHABLE_CODE"; else echo "[]"; fi)" \
        --argjson unused_variables "$(if [ -n "$WARNINGS_JSON" ]; then echo "$UNUSED_VARIABLES"; else echo "[]"; fi)" \
        --argjson unused_using "$(if [ -n "$WARNINGS_JSON" ]; then echo "$UNUSED_USING"; else echo "[]"; fi)" \
        --argjson nullable_issues "$(if [ -n "$WARNINGS_JSON" ]; then echo "$NULLABLE_ISSUES"; else echo "[]"; fi)" \
        '{
            total_issues: ($unreachable_code | length) + ($unused_variables | length) + ($unused_using | length) + ($nullable_issues | length),
            unreachable_code: $unreachable_code,
            unused_variables: $unused_variables,
            unused_using_directives: $unused_using,
            nullable_issues: $nullable_issues,
            summary: {
                unreachable_code_count: ($unreachable_code | length),
                unused_variables_count: ($unused_variables | length),
                unused_using_count: ($unused_using | length),
                nullable_issues_count: ($nullable_issues | length)
            }
        }'
else
    # Fallback without jq
    echo "{\"error\": \"jq not available, cannot generate JSON output\"}" >&2
    exit 1
fi

exit 0

