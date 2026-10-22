#!/bin/bash
set -euo pipefail
# Analyze Root Cause Script
# Input: $1 = remaining_errors_json, $2 = fix_attempts, $3 = comparison_history_json (optional), $4 = dotnet_version (optional)
# Exit code: 0 on success, 1 on failure
# Output: Root cause analysis in JSON format

REMAINING_ERRORS_JSON="$1"
FIX_ATTEMPTS="$2"
COMPARISON_HISTORY_JSON="${3:-}"
DOTNET_VERSION="${4:-}"

if [ -z "$REMAINING_ERRORS_JSON" ] || [ -z "$FIX_ATTEMPTS" ]; then
    echo "ERROR: Missing required parameters" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Parse remaining errors
REMAINING_ERRORS=$(echo "$REMAINING_ERRORS_JSON" | jq -c '[.errors[]? // .compilation_errors[]? // .reference_errors[]? // .syntax_errors[]? // .type_errors[]? // .nullable_errors[]? // .other_errors[]?]')

ERROR_COUNT=$(echo "$REMAINING_ERRORS" | jq 'length')

# Analyze error patterns
ERROR_CODES=$(echo "$REMAINING_ERRORS" | jq -r '.[].code' | sort | uniq -c | sort -rn)
MOST_COMMON_CODE=$(echo "$ERROR_CODES" | head -1 | awk '{print $2}' || echo "")

ERROR_FILES=$(echo "$REMAINING_ERRORS" | jq -r '.[].file' | sort | uniq -c | sort -rn)
MOST_AFFECTED_FILE=$(echo "$ERROR_FILES" | head -1 | awk '{print $2}' || echo "")

# Categorize by error type
COMPILATION_COUNT=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.code | startswith("CS0") or startswith("CS1"))] | length')
REFERENCE_COUNT=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.message | contains("reference") or contains("namespace") or contains("assembly"))] | length')
SYNTAX_COUNT=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.code | startswith("CS1") and (.message | contains("syntax") or contains("expected")))] | length')
TYPE_COUNT=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.message | contains("cannot convert") or contains("type") or contains("implicitly"))] | length')
NULLABLE_COUNT=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.code | startswith("CS8"))] | length')

# Check for .NET version compatibility issues
DOTNET_VERSION_ISSUES=0
DOTNET_VERSION_ERRORS="[]"
if [ -n "$DOTNET_VERSION" ]; then
    # Check for errors that might require different .NET versions
    VERSION_RELATED=$(echo "$REMAINING_ERRORS" | jq '[.[] | select(.code == "CS0246" or .code == "CS0103" or (.message | contains("does not exist") or contains("not found")))]')
    DOTNET_VERSION_ISSUES=$(echo "$VERSION_RELATED" | jq 'length')
    DOTNET_VERSION_ERRORS="$VERSION_RELATED"
fi

# Determine root cause category
if [ "$DOTNET_VERSION_ISSUES" -gt 0 ] && [ -n "$DOTNET_VERSION" ]; then
    ROOT_CAUSE="Potential .NET version compatibility issues - some errors may require different .NET version"
    RECOMMENDATION="Review errors for .NET version requirements. Current version: $DOTNET_VERSION. Some fixes may require upgrading .NET version (manual action required)."
elif [ "$REFERENCE_COUNT" -gt "$((ERROR_COUNT / 2))" ]; then
    ROOT_CAUSE="Missing dependencies or incorrect project references"
    RECOMMENDATION="Check project references, NuGet packages, and using directives"
elif [ "$TYPE_COUNT" -gt "$((ERROR_COUNT / 2))" ]; then
    ROOT_CAUSE="Type mismatches or incompatible types"
    RECOMMENDATION="Review type definitions, interfaces, and inheritance hierarchies"
elif [ "$NULLABLE_COUNT" -gt "$((ERROR_COUNT / 2))" ]; then
    ROOT_CAUSE="Nullable reference type issues"
    RECOMMENDATION="Review nullable annotations and null checks"
elif [ "$SYNTAX_COUNT" -gt "$((ERROR_COUNT / 2))" ]; then
    ROOT_CAUSE="Syntax errors requiring manual code review"
    RECOMMENDATION="Review code syntax and structure manually"
else
    ROOT_CAUSE="Multiple error types requiring comprehensive review"
    RECOMMENDATION="Review codebase structure, dependencies, and type definitions"
fi

# Generate analysis
jq -n \
    --argjson error_count "$ERROR_COUNT" \
    --argjson fix_attempts "$FIX_ATTEMPTS" \
    --arg most_common_code "$MOST_COMMON_CODE" \
    --arg most_affected_file "$MOST_AFFECTED_FILE" \
    --argjson compilation_count "$COMPILATION_COUNT" \
    --argjson reference_count "$REFERENCE_COUNT" \
    --argjson syntax_count "$SYNTAX_COUNT" \
    --argjson type_count "$TYPE_COUNT" \
    --argjson nullable_count "$NULLABLE_COUNT" \
    --argjson dotnet_version_issues "$DOTNET_VERSION_ISSUES" \
    --argjson dotnet_version_errors "$DOTNET_VERSION_ERRORS" \
    --arg dotnet_version "$DOTNET_VERSION" \
    --arg root_cause "$ROOT_CAUSE" \
    --arg recommendation "$RECOMMENDATION" \
    '{
        error_count: $error_count,
        fix_attempts: $fix_attempts,
        most_common_error_code: $most_common_code,
        most_affected_file: $most_affected_file,
        error_breakdown: {
            compilation: $compilation_count,
            reference: $reference_count,
            syntax: $syntax_count,
            type: $type_count,
            nullable: $nullable_count
        },
        dotnet_version_issues: $dotnet_version_issues,
        dotnet_version_errors: $dotnet_version_errors,
        dotnet_version: $dotnet_version,
        root_cause: $root_cause,
        recommendation: $recommendation
    }'

exit 0

