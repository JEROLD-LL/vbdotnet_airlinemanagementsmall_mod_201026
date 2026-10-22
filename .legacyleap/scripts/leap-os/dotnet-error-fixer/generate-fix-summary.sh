#!/bin/bash
set -euo pipefail
# Generate Fix Summary Script
# Input: $1 = comparison_result_json, $2 = root_cause_analysis_json (optional), $3 = iteration_history_json (optional), $4 = format (default: json)
# Exit code: 0 on success, 1 on failure

COMPARISON_JSON="$1"
ROOT_CAUSE_JSON="${2:-}"
ITERATION_HISTORY_JSON="${3:-}"
FORMAT="${4:-json}"

if [ -z "$COMPARISON_JSON" ]; then
    echo "ERROR: Comparison result JSON required" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Extract values
BEFORE_COUNT=$(echo "$COMPARISON_JSON" | jq -r '.before_count')
AFTER_COUNT=$(echo "$COMPARISON_JSON" | jq -r '.after_count')
FIXED_COUNT=$(echo "$COMPARISON_JSON" | jq -r '.fixed_count')
REMAINING_COUNT=$(echo "$COMPARISON_JSON" | jq -r '.remaining_count')
NEW_COUNT=$(echo "$COMPARISON_JSON" | jq -r '.new_count')
SUCCESS_RATE=$(echo "$COMPARISON_JSON" | jq -r '.success_rate')

if [ "$FORMAT" = "json" ]; then
    # JSON format - combine all data
    jq -n \
        --argjson comparison "$COMPARISON_JSON" \
        --argjson root_cause "$(if [ -n "$ROOT_CAUSE_JSON" ] && [ "$ROOT_CAUSE_JSON" != "null" ] && [ "$ROOT_CAUSE_JSON" != "" ]; then echo "$ROOT_CAUSE_JSON"; else echo "{}"; fi)" \
        --argjson iteration_history "$(if [ -n "$ITERATION_HISTORY_JSON" ] && [ "$ITERATION_HISTORY_JSON" != "null" ] && [ "$ITERATION_HISTORY_JSON" != "" ]; then echo "$ITERATION_HISTORY_JSON"; else echo "[]"; fi)" \
        '{
            summary: {
                initial_errors: $comparison.before_count,
                fixed_errors: $comparison.fixed_count,
                remaining_errors: $comparison.remaining_count,
                new_errors: $comparison.new_count,
                success_rate: $comparison.success_rate
            },
            comparison: $comparison,
            root_cause_analysis: $root_cause,
            iteration_history: $iteration_history
        }'
else
    # For markdown/text formats, output simplified version (agent can format if needed)
    echo "$COMPARISON_JSON"
fi

exit 0

