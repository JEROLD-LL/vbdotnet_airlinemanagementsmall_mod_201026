#!/bin/bash
set -euo pipefail
# Native Parse Build Output Script
# Purpose: Parses .NET build/restore output using NATIVE dotnet summary format
#          Extracts error and warning counts from the native dotnet CLI output summary
#          Format: "Restore/Build failed/succeeded with X error(s) and Y warning(s)"
# Input: $1 = build_output_file (or '-' for stdin)
# Output: Parsed error/warning counts in JSON format to stdout
# Exit: 0 on success, 1 on failure
# Example: ./parse-build-output-native.sh ".legacyleap/.agent-state/.tmp/build-output.txt"
# Example Output:
# {
#   "error_count": 1,
#   "warning_count": 7,
#   "build_status": "failed",
#   "summary_line": "Restore failed with 1 error(s) and 7 warning(s) in 0.5s"
# }

BUILD_OUTPUT_FILE="$1"

if [ -z "$BUILD_OUTPUT_FILE" ]; then
    echo "ERROR: Build output file not provided" >&2
    exit 1
fi

# Read build output
if [ "$BUILD_OUTPUT_FILE" = "-" ]; then
    BUILD_OUTPUT=$(cat)
else
    if [ ! -f "$BUILD_OUTPUT_FILE" ]; then
        echo "ERROR: Build output file not found: $BUILD_OUTPUT_FILE" >&2
        exit 1
    fi
    BUILD_OUTPUT=$(cat "$BUILD_OUTPUT_FILE")
fi

# Initialize counters
ERROR_COUNT=0
WARNING_COUNT=0
BUILD_STATUS="unknown"
SUMMARY_LINE=""

# Parse native dotnet summary format
# Supports multiple output formats:
# 1. "Build/Restore (succeeded|failed) with X error(s) and Y warning(s)"
# 2. Indented summary lines: "    X Error(s)" and "    Y Warning(s)"
# 3. Individual error/warning lines: "path : error/warning CODE: message"

# First, try to find the summary line format (format 1)
while IFS= read -r line; do
    # Match pattern: "Restore failed with 1 error(s) and 7 warning(s) in 0.5s"
    if [[ "$line" =~ (Build|Restore)[[:space:]]+(succeeded|failed|completed)[[:space:]]+with[[:space:]]+([0-9]+)[[:space:]]+error\(s\)[[:space:]]+and[[:space:]]+([0-9]+)[[:space:]]+warning\(s\) ]]; then
        BUILD_STATUS="${BASH_REMATCH[2]}"  # succeeded/failed/completed
        ERROR_COUNT="${BASH_REMATCH[3]}"
        WARNING_COUNT="${BASH_REMATCH[4]}"
        SUMMARY_LINE="$line"
        # Don't break - keep searching for the last (most authoritative) summary line
    fi
done <<< "$BUILD_OUTPUT"

# If no summary line found, try to extract from indented count lines (format 2)
# These appear as "    X Error(s)" and "    Y Warning(s)"
if [ -z "$SUMMARY_LINE" ]; then
    while IFS= read -r line; do
        # Match indented error count: "    1 Error(s)"
        if [[ "$line" =~ ^[[:space:]]+([0-9]+)[[:space:]]+Error\(s\) ]]; then
            ERROR_COUNT="${BASH_REMATCH[1]}"
        fi
        # Match indented warning count: "    7 Warning(s)"
        if [[ "$line" =~ ^[[:space:]]+([0-9]+)[[:space:]]+Warning\(s\) ]]; then
            WARNING_COUNT="${BASH_REMATCH[1]}"
        fi
    done <<< "$BUILD_OUTPUT"
    
    # If we found counts via indented format, determine status
    if [ "$ERROR_COUNT" -gt 0 ] || [ "$WARNING_COUNT" -gt 0 ]; then
        if [ "$ERROR_COUNT" -gt 0 ]; then
            BUILD_STATUS="failed"
        else
            BUILD_STATUS="succeeded"
        fi
        SUMMARY_LINE="(Extracted from indented summary format: $ERROR_COUNT error(s) and $WARNING_COUNT warning(s))"
    fi
fi

# If still no data, try to extract from specific error/warning lines (format 3)
if [ -z "$SUMMARY_LINE" ]; then
    # Fallback: Count error and warning lines from diagnostic output
    # Format: "path : error/warning CODE: message"
    # The path can contain colons, so we look for " : error " and " : warning " patterns
    
    # Count lines with " : error " pattern (handles "error NU1605: ...")
    ERROR_LINES=$(echo "$BUILD_OUTPUT" | grep -c " : error " || true)
    
    # Count lines with " : warning " pattern, but exclude those marked as "Warning As Error"
    WARNING_LINES=$(echo "$BUILD_OUTPUT" | grep " : warning " | grep -v "Warning As Error" | wc -l || true)
    
    # If we have any matches, use them
    if [ "$ERROR_LINES" -gt 0 ] || [ "$WARNING_LINES" -gt 0 ]; then
        ERROR_COUNT=$ERROR_LINES
        WARNING_COUNT=$WARNING_LINES
        BUILD_STATUS="failed"
        SUMMARY_LINE="(Extracted from individual error/warning lines)"
    fi
fi

# If still no data, check for specific success patterns
if [ -z "$SUMMARY_LINE" ] && [ "$ERROR_COUNT" -eq 0 ] && [ "$WARNING_COUNT" -eq 0 ]; then
    # Look for success pattern without errors
    if echo "$BUILD_OUTPUT" | grep -q "Build succeeded" || echo "$BUILD_OUTPUT" | grep -q "Restore completed"; then
        BUILD_STATUS="succeeded"
        ERROR_COUNT=0
        WARNING_COUNT=0
        SUMMARY_LINE="(Build/Restore succeeded with 0 errors and 0 warnings)"
    fi
fi

# Output JSON result
echo "{"
echo "  \"error_count\": $ERROR_COUNT,"
echo "  \"warning_count\": $WARNING_COUNT,"
echo "  \"build_status\": \"$BUILD_STATUS\","
echo "  \"summary_line\": \"$SUMMARY_LINE\""
echo "}"

exit 0
