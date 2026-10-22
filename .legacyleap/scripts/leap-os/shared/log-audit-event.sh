#!/bin/bash
set -euo pipefail
# Log Audit Event Script
# Purpose: Logs structured audit events to persistent log files for troubleshooting and compliance
# Input: $1 = event_type, $2 = message, $3 = details (JSON, optional), $4 = result (success/failure/warning/info, default: info)
# Output: Log entry to file and stderr, errors to stderr
# Exit: 0 on success, 1 on failure
# Example: ./log-audit-event.sh "phase_start" "Step 1: Environment Preparation" '{"agent":"dotnet-version-setup"}' "info"
# Example Output: "[2024-01-01T00:00:00Z] [info] phase_start: Step 1: Environment Preparation" (to stderr)

EVENT_TYPE="$1"
MESSAGE="$2"
DETAILS="${3:-{}}"
RESULT="${4:-info}"

if [ -z "$EVENT_TYPE" ] || [ -z "$MESSAGE" ]; then
    echo "ERROR: Missing required parameters: event_type and message" >&2
    exit 1
fi

# Create logs directory if it doesn't exist
LOG_DIR=".legacyleap/logs"
mkdir -p "$LOG_DIR"

# Generate log filename with date (YYYY-MM-DD format)
LOG_DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/dotnet-auto-fix-${LOG_DATE}.log"

# Rotate logs older than 30 days
find "$LOG_DIR" -name "dotnet-auto-fix-*.log" -mtime +30 -delete 2>/dev/null || true

# Generate timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create structured log entry (JSON format)
LOG_ENTRY=$(cat <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "event_type": "${EVENT_TYPE}",
  "result": "${RESULT}",
  "message": "${MESSAGE//\"/\\\"}",
  "details": ${DETAILS}
}
EOF
)

# Append to log file
if echo "$LOG_ENTRY" >> "$LOG_FILE" 2>/dev/null; then
    # Also output to stderr for immediate visibility (non-JSON format)
    echo "[${TIMESTAMP}] [${RESULT}] ${EVENT_TYPE}: ${MESSAGE}" >&2
    exit 0
else
    echo "ERROR: Failed to write to log file: $LOG_FILE" >&2
    exit 1
fi

