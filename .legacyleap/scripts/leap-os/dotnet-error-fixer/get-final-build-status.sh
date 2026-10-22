#!/bin/bash
set -euo pipefail
# Get Final Build Status Script
# Purpose: Extracts final build status (success/failure) and error/warning counts from build output
# Input: $1 = build_output_file, $2 = format (default: json)
# Output: Build status JSON to stdout
# Exit: 0 on success, 1 on failure
# Example: ./get-final-build-status.sh ".legacyleap/build-output.txt" "json"
# Example Output:
# {
#   "buildSucceeded": false,
#   "error_count": 5,
#   "warning_count": 3
# }

BUILD_OUTPUT_FILE="$1"
FORMAT="${2:-json}"

if [ -z "$BUILD_OUTPUT_FILE" ] || [ ! -f "$BUILD_OUTPUT_FILE" ]; then
    echo "ERROR: Build output file not found: $BUILD_OUTPUT_FILE" >&2
    exit 1
fi

# Extract build status
BUILD_SUCCESS=$(grep -i "Build succeeded\|Build FAILED" "$BUILD_OUTPUT_FILE" | tail -1 || echo "")

# Count errors (CS#### pattern)
ERROR_COUNT=$(grep -c "error CS" "$BUILD_OUTPUT_FILE" 2>/dev/null || echo "0")

# Count warnings (CS#### pattern)
WARNING_COUNT=$(grep -c "warning CS" "$BUILD_OUTPUT_FILE" 2>/dev/null || echo "0")

# Determine build status
if echo "$BUILD_SUCCESS" | grep -qi "succeeded"; then
    BUILD_STATUS="SUCCESS"
elif echo "$BUILD_SUCCESS" | grep -qi "FAILED"; then
    BUILD_STATUS="FAILED"
else
    # Check if errors found
    if [ "$ERROR_COUNT" -gt 0 ]; then
        BUILD_STATUS="FAILED"
    else
        BUILD_STATUS="SUCCESS"
    fi
fi

# Extract build summary line if available
BUILD_SUMMARY=$(grep -i "Build succeeded\|Build FAILED" "$BUILD_OUTPUT_FILE" | tail -1 || echo "")

if [ "$FORMAT" = "json" ]; then
    # JSON format
    if command -v jq &> /dev/null; then
        jq -n \
            --arg status "$BUILD_STATUS" \
            --argjson error_count "$ERROR_COUNT" \
            --argjson warning_count "$WARNING_COUNT" \
            --arg summary "$BUILD_SUMMARY" \
            '{
                build_status: $status,
                error_count: $error_count,
                warning_count: $warning_count,
                build_summary: $summary
            }'
    else
        echo "{\"build_status\":\"$BUILD_STATUS\",\"error_count\":$ERROR_COUNT,\"warning_count\":$WARNING_COUNT,\"build_summary\":\"$BUILD_SUMMARY\"}"
    fi
else
    # For markdown/text formats, output simplified version
    echo "Build Status: $BUILD_STATUS"
    echo "Errors: $ERROR_COUNT"
    echo "Warnings: $WARNING_COUNT"
fi

exit 0

