#!/bin/bash
set -euo pipefail
# Format Error List Script
# Input: $1 = categorized_errors_json, $2 = categorized_warnings_json (optional), $3 = code_quality_issues_json (optional), $4 = dependency_issues_json (optional), $5 = format (markdown, text, json, default: json)
# Exit code: 0 on success, 1 on failure

CATEGORIZED_JSON="$1"
CATEGORIZED_WARNINGS_JSON="${2:-}"
CODE_QUALITY_ISSUES_JSON="${3:-}"
DEPENDENCY_ISSUES_JSON="${4:-}"
FORMAT="${5:-json}"

if [ -z "$CATEGORIZED_JSON" ]; then
    echo "ERROR: Categorized errors JSON not provided" >&2
    exit 1
fi

# Use jq if available for JSON parsing
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Extract counts
TOTAL_ERRORS=$(echo "$CATEGORIZED_JSON" | jq '[.compilation_errors, .reference_errors, .syntax_errors, .type_errors, .nullable_errors, .other_errors] | map(length) | add')
COMPILATION_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.compilation_errors | length')
REFERENCE_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.reference_errors | length')
SYNTAX_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.syntax_errors | length')
TYPE_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.type_errors | length')
NULLABLE_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.nullable_errors | length')
OTHER_COUNT=$(echo "$CATEGORIZED_JSON" | jq '.other_errors | length')

# Extract warning counts if provided
if [ -n "$CATEGORIZED_WARNINGS_JSON" ] && [ "$CATEGORIZED_WARNINGS_JSON" != "null" ] && [ "$CATEGORIZED_WARNINGS_JSON" != "" ]; then
    CODE_QUALITY_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.code_quality_warnings | length')
    NULLABLE_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.nullable_warnings | length')
    OBSOLETE_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.obsolete_warnings | length')
    XML_DOC_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.xml_documentation_warnings | length')
    SECURITY_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.security_warnings | length')
    PERFORMANCE_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.performance_warnings | length')
    OTHER_WARNINGS_COUNT=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '.other_warnings | length')
    TOTAL_WARNINGS=$(echo "$CATEGORIZED_WARNINGS_JSON" | jq '[.code_quality_warnings, .nullable_warnings, .obsolete_warnings, .xml_documentation_warnings, .security_warnings, .performance_warnings, .other_warnings] | map(length) | add')
else
    TOTAL_WARNINGS=0
    CODE_QUALITY_WARNINGS_COUNT=0
    NULLABLE_WARNINGS_COUNT=0
    OBSOLETE_WARNINGS_COUNT=0
    XML_DOC_WARNINGS_COUNT=0
    SECURITY_WARNINGS_COUNT=0
    PERFORMANCE_WARNINGS_COUNT=0
    OTHER_WARNINGS_COUNT=0
fi

# Extract code quality issues if provided
if [ -n "$CODE_QUALITY_ISSUES_JSON" ] && [ "$CODE_QUALITY_ISSUES_JSON" != "null" ] && [ "$CODE_QUALITY_ISSUES_JSON" != "" ]; then
    CODE_QUALITY_TOTAL=$(echo "$CODE_QUALITY_ISSUES_JSON" | jq '.total_issues')
    UNREACHABLE_COUNT=$(echo "$CODE_QUALITY_ISSUES_JSON" | jq '.summary.unreachable_code_count')
    UNUSED_VAR_COUNT=$(echo "$CODE_QUALITY_ISSUES_JSON" | jq '.summary.unused_variables_count')
    UNUSED_USING_COUNT=$(echo "$CODE_QUALITY_ISSUES_JSON" | jq '.summary.unused_using_count')
    NULLABLE_ISSUES_COUNT=$(echo "$CODE_QUALITY_ISSUES_JSON" | jq '.summary.nullable_issues_count')
else
    CODE_QUALITY_TOTAL=0
    UNREACHABLE_COUNT=0
    UNUSED_VAR_COUNT=0
    UNUSED_USING_COUNT=0
    NULLABLE_ISSUES_COUNT=0
fi

# Extract dependency issues if provided
if [ -n "$DEPENDENCY_ISSUES_JSON" ] && [ "$DEPENDENCY_ISSUES_JSON" != "null" ] && [ "$DEPENDENCY_ISSUES_JSON" != "" ]; then
    DUPLICATE_PACKAGES_COUNT=$(echo "$DEPENDENCY_ISSUES_JSON" | jq '.duplicate_count')
    OUTDATED_PACKAGES_COUNT=$(echo "$DEPENDENCY_ISSUES_JSON" | jq '.outdated_count')
    VULNERABLE_PACKAGES_COUNT=$(echo "$DEPENDENCY_ISSUES_JSON" | jq '.vulnerable_count')
    TOTAL_PACKAGES=$(echo "$DEPENDENCY_ISSUES_JSON" | jq '.total_packages')
else
    DUPLICATE_PACKAGES_COUNT=0
    OUTDATED_PACKAGES_COUNT=0
    VULNERABLE_PACKAGES_COUNT=0
    TOTAL_PACKAGES=0
fi

if [ "$FORMAT" = "json" ]; then
    # JSON format - combine all data
    jq -n \
        --argjson errors "$CATEGORIZED_JSON" \
        --argjson warnings "$(if [ -n "$CATEGORIZED_WARNINGS_JSON" ] && [ "$CATEGORIZED_WARNINGS_JSON" != "null" ] && [ "$CATEGORIZED_WARNINGS_JSON" != "" ]; then echo "$CATEGORIZED_WARNINGS_JSON"; else echo "{}"; fi)" \
        --argjson code_quality "$(if [ -n "$CODE_QUALITY_ISSUES_JSON" ] && [ "$CODE_QUALITY_ISSUES_JSON" != "null" ] && [ "$CODE_QUALITY_ISSUES_JSON" != "" ]; then echo "$CODE_QUALITY_ISSUES_JSON"; else echo "{}"; fi)" \
        --argjson dependencies "$(if [ -n "$DEPENDENCY_ISSUES_JSON" ] && [ "$DEPENDENCY_ISSUES_JSON" != "null" ] && [ "$DEPENDENCY_ISSUES_JSON" != "" ]; then echo "$DEPENDENCY_ISSUES_JSON"; else echo "{}"; fi)" \
        '{
            buildSucceeded: false,
            errors: {
                total_count: ([$errors.compilation_errors, $errors.reference_errors, $errors.syntax_errors, $errors.type_errors, $errors.nullable_errors, $errors.other_errors] | map(length) | add),
                by_category: $errors
            },
            warnings: {
                total_count: (if $warnings == {} then 0 else ([$warnings.code_quality_warnings, $warnings.nullable_warnings, $warnings.obsolete_warnings, $warnings.xml_documentation_warnings, $warnings.security_warnings, $warnings.performance_warnings, $warnings.other_warnings] | map(length) | add) end),
                by_category: $warnings
            },
            code_quality_issues: $code_quality,
            dependency_issues: $dependencies
        }'
else
    # For markdown/text formats, output simplified version (agent can format if needed)
    echo "$CATEGORIZED_JSON"
fi

exit 0

