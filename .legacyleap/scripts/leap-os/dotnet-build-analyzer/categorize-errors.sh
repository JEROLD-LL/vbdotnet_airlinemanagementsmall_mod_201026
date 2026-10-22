#!/bin/bash
set -euo pipefail
# Categorize Errors Script
# Purpose: Categorizes compilation errors by type (compilation, reference, syntax, type, nullable, other)
# Input: $1 = errors_json (JSON array of errors)
# Output: Categorized errors JSON to stdout
# Exit: 0 on success, 1 on failure
# Example: ./categorize-errors.sh '{"errors":[{"file":"src/File.cs","line":10,"code":"CS1001","message":"..."}]}'
# Example Output:
# {
#   "total_count": 1,
#   "by_category": {
#     "compilation_errors": [...],
#     "reference_errors": [...],
#     "syntax_errors": [...],
#     "type_errors": [...],
#     "nullable_errors": [...],
#     "other_errors": [...]
#   }
# }

ERRORS_JSON="$1"

if [ -z "$ERRORS_JSON" ]; then
    echo "ERROR: Errors JSON not provided" >&2
    exit 1
fi

# Parse JSON and categorize (using jq if available, otherwise basic parsing)
if command -v jq &> /dev/null; then
    CATEGORIZED=$(echo "$ERRORS_JSON" | jq -r '
    {
        compilation_errors: [.[] | select(.code | startswith("CS0") or startswith("CS1"))],
        reference_errors: [.[] | select(.message | contains("reference") or contains("namespace") or contains("assembly"))],
        syntax_errors: [.[] | select(.code | startswith("CS1") and (.message | contains("syntax") or contains("expected")))],
        type_errors: [.[] | select(.message | contains("cannot convert") or contains("type") or contains("implicitly"))],
        nullable_errors: [.[] | select(.code | startswith("CS8"))],
        other_errors: [.[] | select(.code | (startswith("CS0") or startswith("CS1")) and (.message | (contains("reference") | not) and (contains("syntax") | not) and (contains("type") | not)))]
    }')
    
    echo "$CATEGORIZED"
else
    # Fallback: Basic categorization without jq
    echo "{\"error\": \"jq not available, cannot categorize errors\"}" >&2
    echo "$ERRORS_JSON"
fi

exit 0

