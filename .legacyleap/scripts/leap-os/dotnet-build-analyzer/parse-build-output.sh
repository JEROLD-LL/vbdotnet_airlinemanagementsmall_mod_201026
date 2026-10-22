#!/bin/bash
set -euo pipefail
# Parse Build Output Script
# Purpose: Parses .NET build output and extracts errors and warnings in structured format
# Input: $1 = build_output_file (or '-' for stdin), $2 = output_format (json or text, default: json)
# Output: Parsed errors and warnings in specified format to stdout
# Exit: 0 on success, 1 on failure
# Example: ./parse-build-output.sh ".legacyleap/build-output.txt" "json"
# Example Output:
# {
#   "errors": [
#     {
#       "file": "src/File.cs",
#       "line": 10,
#       "column": 5,
#       "code": "CS1001",
#       "message": "Identifier expected"
#     }
#   ],
#   "warnings": [
#     {
#       "file": "src/File.cs",
#       "line": 5,
#       "column": 3,
#       "code": "CS0219",
#       "message": "Variable is assigned but never used"
#     }
#   ],
#   "error_count": 1,
#   "warning_count": 1
# }

BUILD_OUTPUT_FILE="$1"
OUTPUT_FORMAT="${2:-json}"

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

# Initialize arrays for errors and warnings
ERRORS=()
WARNINGS=()
ERROR_COUNT=0
WARNING_COUNT=0

# Parse errors (format: "path(line,col): error CS####: message")
while IFS= read -r line; do
    # Match error pattern: path(line,col): error CS####: message
    if [[ "$line" =~ ^([^:]+)\(([0-9]+),([0-9]+)\):[[:space:]]*error[[:space:]]+(CS[0-9]+):[[:space:]]*(.+)$ ]]; then
        FILE="${BASH_REMATCH[1]}"
        LINE="${BASH_REMATCH[2]}"
        COL="${BASH_REMATCH[3]}"
        CODE="${BASH_REMATCH[4]}"
        MESSAGE="${BASH_REMATCH[5]}"
        
        ERRORS+=("{\"file\":\"$FILE\",\"line\":$LINE,\"column\":$COL,\"code\":\"$CODE\",\"message\":\"${MESSAGE//\"/\\\"}\"}")
        ERROR_COUNT=$((ERROR_COUNT + 1))
    # Match warning pattern: path(line,col): warning CS####: message
    elif [[ "$line" =~ ^([^:]+)\(([0-9]+),([0-9]+)\):[[:space:]]*warning[[:space:]]+(CS[0-9]+):[[:space:]]*(.+)$ ]]; then
        FILE="${BASH_REMATCH[1]}"
        LINE="${BASH_REMATCH[2]}"
        COL="${BASH_REMATCH[3]}"
        CODE="${BASH_REMATCH[4]}"
        MESSAGE="${BASH_REMATCH[5]}"
        
        WARNINGS+=("{\"file\":\"$FILE\",\"line\":$LINE,\"column\":$COL,\"code\":\"$CODE\",\"message\":\"${MESSAGE//\"/\\\"}\"}")
        WARNING_COUNT=$((WARNING_COUNT + 1))
    fi
done <<< "$BUILD_OUTPUT"

# Output in requested format
if [ "$OUTPUT_FORMAT" = "json" ]; then
    echo "{"
    echo "  \"error_count\": $ERROR_COUNT,"
    echo "  \"warning_count\": $WARNING_COUNT,"
    echo "  \"errors\": ["
    if [ ${#ERRORS[@]} -gt 0 ]; then
        for i in "${!ERRORS[@]}"; do
            echo "    ${ERRORS[$i]}"
            if [ $i -lt $((${#ERRORS[@]} - 1)) ]; then
                echo ","
            fi
        done
    fi
    echo "  ],"
    echo "  \"warnings\": ["
    if [ ${#WARNINGS[@]} -gt 0 ]; then
        for i in "${!WARNINGS[@]}"; do
            echo "    ${WARNINGS[$i]}"
            if [ $i -lt $((${#WARNINGS[@]} - 1)) ]; then
                echo ","
            fi
        done
    fi
    echo "  ]"
    echo "}"
else
    # Text format
    echo "=== Build Analysis ==="
    echo "Errors: $ERROR_COUNT"
    echo "Warnings: $WARNING_COUNT"
    echo ""
    if [ $ERROR_COUNT -gt 0 ]; then
        echo "=== ERRORS ==="
        for i in "${!ERRORS[@]}"; do
            ERROR_JSON="${ERRORS[$i]}"
            FILE=$(echo "$ERROR_JSON" | grep -o '"file":"[^"]*"' | cut -d'"' -f4)
            LINE=$(echo "$ERROR_JSON" | grep -o '"line":[0-9]*' | cut -d':' -f2)
            CODE=$(echo "$ERROR_JSON" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
            MESSAGE=$(echo "$ERROR_JSON" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
            echo "$((i + 1)). $FILE($LINE): $CODE - $MESSAGE"
        done
        echo ""
    fi
    if [ $WARNING_COUNT -gt 0 ]; then
        echo "=== WARNINGS ==="
        for i in "${!WARNINGS[@]}"; do
            WARNING_JSON="${WARNINGS[$i]}"
            FILE=$(echo "$WARNING_JSON" | grep -o '"file":"[^"]*"' | cut -d'"' -f4)
            LINE=$(echo "$WARNING_JSON" | grep -o '"line":[0-9]*' | cut -d':' -f2)
            CODE=$(echo "$WARNING_JSON" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
            MESSAGE=$(echo "$WARNING_JSON" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
            echo "$((i + 1)). $FILE($LINE): $CODE - $MESSAGE"
        done
    fi
fi

exit 0

