#!/bin/bash
set -euo pipefail
# Restore NuGet Packages Script
# Input: $1 = solution_path (optional, auto-detect), $2 = timeout (optional, default: 300)
# Exit code: 0 on success, 1 on failure

SOLUTION_PATH="$1"
TIMEOUT="${2:-300}"

# Auto-detect solution file if not provided
if [ -z "$SOLUTION_PATH" ]; then
    SOLUTION_PATH=$(find . -maxdepth 1 -name "*.sln" | head -1)
    if [ -z "$SOLUTION_PATH" ]; then
        # Try to find a project file
        SOLUTION_PATH=$(find . -name "*.csproj" -type f | head -1)
    fi
fi

if [ -z "$SOLUTION_PATH" ] || [ ! -f "$SOLUTION_PATH" ]; then
    echo "ERROR: Solution or project file not found" >&2
    exit 1
fi

echo "INFO: Restoring NuGet packages for: $(basename "$SOLUTION_PATH")"

# Restore packages with timeout
if timeout "$TIMEOUT" dotnet restore "$SOLUTION_PATH" 2>&1; then
    echo "SUCCESS: NuGet packages restored successfully"
    exit 0
else
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "ERROR: Package restore timed out after ${TIMEOUT} seconds" >&2
    else
        echo "ERROR: Package restore failed" >&2
    fi
    exit 1
fi

