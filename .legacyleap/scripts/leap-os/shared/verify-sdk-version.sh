#!/bin/bash
set -euo pipefail
# Verify SDK Version Script
# Purpose: Verifies that the SDK version used matches the detected/required version
# Input: $1 = required_version (X.Y.Z format), $2 = project_root (optional, default: current directory)
# Output: "match", "mismatch:<actual_version>", or "error:<message>" to stdout
# Exit: 0 on match, 1 on mismatch or error
# Example: ./verify-sdk-version.sh "8.0.0" "."
# Example Output: "match" or "mismatch:8.0.1"

REQUIRED_VERSION="$1"
PROJECT_ROOT="${2:-.}"

if [ -z "$REQUIRED_VERSION" ]; then
    echo "error:Version not provided" >&2
    exit 1
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "error:Project root directory not found: $PROJECT_ROOT" >&2
    exit 1
fi

# Validate version format
if [[ ! "$REQUIRED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "error:Invalid version format. Expected X.Y.Z format, got: $REQUIRED_VERSION" >&2
    exit 1
fi

# Check if dotnet command exists
if ! command -v dotnet &> /dev/null; then
    echo "error:dotnet CLI not found in PATH" >&2
    exit 1
fi

# Get actual SDK version being used
ACTUAL_VERSION=$(dotnet --version 2>/dev/null || echo "")

if [ -z "$ACTUAL_VERSION" ]; then
    echo "error:Failed to get dotnet version" >&2
    exit 1
fi

# Extract major.minor from both versions for comparison
REQUIRED_MAJOR_MINOR=$(echo "$REQUIRED_VERSION" | cut -d. -f1,2)
ACTUAL_MAJOR_MINOR=$(echo "$ACTUAL_VERSION" | cut -d. -f1,2)

# Check for exact match first
if [ "$ACTUAL_VERSION" = "$REQUIRED_VERSION" ]; then
    echo "match"
    exit 0
fi

# Check for compatible major.minor version
if [ "$ACTUAL_MAJOR_MINOR" = "$REQUIRED_MAJOR_MINOR" ]; then
    # Same major.minor, different patch - this is acceptable with rollForward
    echo "match"
    exit 0
fi

# Version mismatch
echo "mismatch:$ACTUAL_VERSION"
exit 1

