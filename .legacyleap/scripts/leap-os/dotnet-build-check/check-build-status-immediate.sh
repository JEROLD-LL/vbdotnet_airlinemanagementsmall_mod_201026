#!/bin/bash
set -euo pipefail
# Immediate Build Status Check Script (Fix #8)
# Purpose: Check build logs immediately for status patterns
#          Enables early failure detection without waiting for file creation
# Input: $1 = build_log_file
# Output: JSON with status, detection method, and error count to stdout
# Exit: 0 on success
# Example: ./check-build-status-immediate.sh ".legacyleap/.agent-state/.tmp/build-live.log"
# Example Output:
# {
#   "status": "failed",
#   "method": "native_summary",
#   "error_count": 3,
#   "warning_count": 5,
#   "summary_line": "Build failed with 3 error(s) and 5 warning(s) in 0.53s"
# }

BUILD_LOG="$1"

if [ -z "$BUILD_LOG" ]; then
    echo "ERROR: Build log file not provided" >&2
    exit 1
fi

if [ ! -f "$BUILD_LOG" ]; then
    echo "{\"status\":\"unknown\",\"method\":\"log_not_found\",\"error_count\":0,\"warning_count\":0,\"summary_line\":\"Log file not found: $BUILD_LOG\"}"
    exit 0
fi

BUILD_LOG_CONTENT=$(cat "$BUILD_LOG")

# Initialize defaults
BUILD_STATUS="unknown"
DETECTION_METHOD="none"
ERROR_COUNT=0
WARNING_COUNT=0
SUMMARY_LINE=""

# Pattern 1: Native dotnet summary - Build failed (most reliable)
if echo "$BUILD_LOG_CONTENT" | grep -q "Build failed with"; then
    SUMMARY_LINE=$(echo "$BUILD_LOG_CONTENT" | grep "Build failed with" | tail -1)
    ERROR_COUNT=$(echo "$SUMMARY_LINE" | sed -n 's/.*with \([0-9]*\) error.*/\1/p')
    WARNING_COUNT=$(echo "$SUMMARY_LINE" | sed -n 's/.*and \([0-9]*\) warning.*/\1/p')
    BUILD_STATUS="failed"
    DETECTION_METHOD="native_summary_build_failed"
fi

# Pattern 2: Native dotnet summary - Restore failed
if [ "$BUILD_STATUS" = "unknown" ] && echo "$BUILD_LOG_CONTENT" | grep -q "Restore failed with"; then
    SUMMARY_LINE=$(echo "$BUILD_LOG_CONTENT" | grep "Restore failed with" | tail -1)
    ERROR_COUNT=$(echo "$SUMMARY_LINE" | sed -n 's/.*with \([0-9]*\) error.*/\1/p')
    WARNING_COUNT=$(echo "$SUMMARY_LINE" | sed -n 's/.*and \([0-9]*\) warning.*/\1/p')
    BUILD_STATUS="failed"
    DETECTION_METHOD="native_summary_restore_failed"
fi

# Pattern 3: Native dotnet summary - Build succeeded
if [ "$BUILD_STATUS" = "unknown" ] && echo "$BUILD_LOG_CONTENT" | grep -q "Build succeeded with 0 error"; then
    SUMMARY_LINE=$(echo "$BUILD_LOG_CONTENT" | grep "Build succeeded" | tail -1)
    BUILD_STATUS="succeeded"
    DETECTION_METHOD="native_summary_build_succeeded"
    ERROR_COUNT=0
    WARNING_COUNT=$(echo "$SUMMARY_LINE" | sed -n 's/.*and \([0-9]*\) warning.*/\1/p')
fi

# Pattern 4: Restore succeeded with 0 errors
if [ "$BUILD_STATUS" = "unknown" ] && echo "$BUILD_LOG_CONTENT" | grep -q "Restore completed"; then
    SUMMARY_LINE=$(echo "$BUILD_LOG_CONTENT" | grep "Restore completed" | tail -1)
    BUILD_STATUS="succeeded"
    DETECTION_METHOD="native_summary_restore_completed"
    ERROR_COUNT=0
    WARNING_COUNT=0
fi

# Pattern 5: Fallback - Check for individual error/warning lines
if [ "$BUILD_STATUS" = "unknown" ]; then
    ERROR_LINES=$(echo "$BUILD_LOG_CONTENT" | grep -c " : error " || true)
    WARNING_LINES=$(echo "$BUILD_LOG_CONTENT" | grep -c " : warning " || true)
    
    if [ "$ERROR_LINES" -gt 0 ] || [ "$WARNING_LINES" -gt 0 ]; then
        ERROR_COUNT=$ERROR_LINES
        WARNING_COUNT=$WARNING_LINES
        BUILD_STATUS="failed"
        DETECTION_METHOD="error_warning_lines"
        SUMMARY_LINE="(Extracted from individual error/warning lines: $ERROR_COUNT error(s) and $WARNING_COUNT warning(s))"
    fi
fi

# Output JSON result
echo "{"
echo "  \"status\": \"$BUILD_STATUS\","
echo "  \"method\": \"$DETECTION_METHOD\","
echo "  \"error_count\": $ERROR_COUNT,"
echo "  \"warning_count\": $WARNING_COUNT,"
echo "  \"summary_line\": \"$SUMMARY_LINE\""
echo "}"

exit 0
