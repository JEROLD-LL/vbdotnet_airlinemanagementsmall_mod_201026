#!/bin/bash
set -euo pipefail
# Manage Execution State Script
# Purpose: Manages consolidated execution-state.json file (merges, doesn't overwrite)
# Input: $1 = operation (update_version|update_build_analysis|update_metadata|read|read_version|read_build_analysis)
#        $2 = data_json (for update operations)
# Output: JSON output for read operations, none for update operations
# Exit: 0 on success, 1 on failure
# Example: ./manage-execution-state.sh "update_version" '{"version":"8.0.0","source":"global.json","sdk_installed":true}'

OPERATION="$1"
DATA_JSON="${2:-{}}"

if [ -z "$OPERATION" ]; then
    echo "ERROR: Operation not provided" >&2
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "ERROR: jq command not found. Please install jq for JSON parsing." >&2
    exit 1
fi

# Create .agent-state directory if it doesn't exist
mkdir -p .legacyleap/.agent-state

STATE_FILE=".legacyleap/.agent-state/execution-state.json"

# Initialize state file if it doesn't exist
if [ ! -f "$STATE_FILE" ]; then
    jq -n '{
        version: {},
        build_analysis: {},
        execution_metadata: {}
    }' > "$STATE_FILE"
fi

# Validate existing state file
if ! jq empty "$STATE_FILE" 2>/dev/null; then
    echo "ERROR: Invalid JSON in execution-state.json" >&2
    exit 1
fi

case "$OPERATION" in
    update_version)
        # Merge version info into execution-state.json
        if ! echo "$DATA_JSON" | jq empty 2>/dev/null; then
            echo "ERROR: Invalid JSON data provided" >&2
            exit 1
        fi
        
        # Add timestamp and detected_by if not present
        UPDATED_DATA=$(echo "$DATA_JSON" | jq --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            '. + {
                timestamp: ($timestamp),
                detected_by: (.detected_by // "dotnet-version-setup")
            }')
        
        # Merge into state file
        jq --argjson version_data "$UPDATED_DATA" '.version = $version_data' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        # Update execution metadata
        jq --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '.execution_metadata.last_updated = $timestamp' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        echo "SUCCESS: Version info updated in execution-state.json"
        ;;
    
    update_build_analysis)
        # Merge build analysis into execution-state.json
        if ! echo "$DATA_JSON" | jq empty 2>/dev/null; then
            echo "ERROR: Invalid JSON data provided" >&2
            exit 1
        fi
        
        # Merge into state file
        jq --argjson build_data "$DATA_JSON" '.build_analysis = $build_data' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        # Update execution metadata
        jq --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '.execution_metadata.last_updated = $timestamp' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        echo "SUCCESS: Build analysis updated in execution-state.json"
        ;;
    
    update_metadata)
        # Update execution metadata
        if ! echo "$DATA_JSON" | jq empty 2>/dev/null; then
            echo "ERROR: Invalid JSON data provided" >&2
            exit 1
        fi
        
        # Merge metadata (don't overwrite, merge)
        jq --argjson metadata "$DATA_JSON" '.execution_metadata = (.execution_metadata + $metadata)' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        # Update last_updated
        jq --arg timestamp "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" '.execution_metadata.last_updated = $timestamp' "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        echo "SUCCESS: Execution metadata updated"
        ;;
    
    read)
        # Read entire execution state
        cat "$STATE_FILE"
        ;;
    
    read_version)
        # Read only version section
        jq '.version // {}' "$STATE_FILE"
        ;;
    
    read_build_analysis)
        # Read only build_analysis section
        jq '.build_analysis // {}' "$STATE_FILE"
        ;;
    
    *)
        echo "ERROR: Unknown operation: $OPERATION" >&2
        echo "Valid operations: update_version, update_build_analysis, update_metadata, read, read_version, read_build_analysis" >&2
        exit 1
        ;;
esac

exit 0

