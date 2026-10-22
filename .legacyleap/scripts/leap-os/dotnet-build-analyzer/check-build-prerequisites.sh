#!/bin/bash
set -euo pipefail
# Check Build Prerequisites Script
# Input: $1 = project_root (optional, default: current directory)
# Exit code: 0 on success, 1 on failure

PROJECT_ROOT="${1:-.}"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project root directory not found: $PROJECT_ROOT" >&2
    exit 1
fi

ERRORS=0

# Check 1: Verify dotnet CLI is available
if ! command -v dotnet &> /dev/null; then
    echo "ERROR: dotnet CLI not found in PATH" >&2
    ERRORS=$((ERRORS + 1))
else
    DOTNET_VERSION=$(dotnet --version 2>/dev/null)
    echo "INFO: dotnet CLI found: $DOTNET_VERSION"
fi

# Check 2: Verify solution file exists
SOLUTION_FILE=$(find "$PROJECT_ROOT" -maxdepth 1 -name "*.sln" | head -1)
if [ -z "$SOLUTION_FILE" ]; then
    echo "ERROR: No solution file (.sln) found in $PROJECT_ROOT" >&2
    ERRORS=$((ERRORS + 1))
else
    echo "INFO: Solution file found: $(basename "$SOLUTION_FILE")"
fi

# Check 3: Verify project files exist
PROJECT_COUNT=$(find "$PROJECT_ROOT/src" -name "*.csproj" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PROJECT_COUNT" -eq 0 ]; then
    echo "WARNING: No .csproj files found in src/ directory" >&2
    # Not a fatal error, might be building from different location
else
    echo "INFO: Found $PROJECT_COUNT project file(s)"
fi

# Check 4: Verify required .NET SDK version (if Directory.Build.props exists)
if [ -f "$PROJECT_ROOT/Directory.Build.props" ]; then
    TARGET_FRAMEWORK=$(grep -o 'TargetFramework[^>]*net[0-9]\+\.[0-9]\+' "$PROJECT_ROOT/Directory.Build.props" 2>/dev/null | \
                       sed 's/.*net\([0-9]\+\.[0-9]\+\).*/\1/' | head -1)
    if [ -n "$TARGET_FRAMEWORK" ]; then
        MAJOR_VERSION=$(echo "$TARGET_FRAMEWORK" | cut -d. -f1)
        INSTALLED_SDKS=$(dotnet --list-sdks 2>/dev/null | grep "^${MAJOR_VERSION}\." | head -1)
        if [ -z "$INSTALLED_SDKS" ]; then
            echo "WARNING: Required .NET SDK version ${MAJOR_VERSION}.x not found" >&2
            echo "WARNING: Installed SDKs: $(dotnet --list-sdks 2>/dev/null | head -3 | tr '\n' ' ')" >&2
        else
            echo "INFO: Required .NET SDK version ${MAJOR_VERSION}.x is available"
        fi
    fi
fi

# Check 5: Verify project structure (src/ directory)
if [ ! -d "$PROJECT_ROOT/src" ]; then
    echo "WARNING: src/ directory not found" >&2
else
    echo "INFO: Project structure validated"
fi

if [ $ERRORS -gt 0 ]; then
    echo "ERROR: Build prerequisites check failed with $ERRORS error(s)" >&2
    exit 1
fi

echo "SUCCESS: All build prerequisites met"
exit 0

