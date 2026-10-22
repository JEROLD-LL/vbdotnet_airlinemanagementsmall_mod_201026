#!/bin/bash
set -euo pipefail
# Detect Version From Files Script
# Purpose: Detects .NET SDK version from project files (global.json, Directory.Build.props, or README.md)
# Input: $1 = project_root (optional, default: current directory)
# Output: Version string (X.Y.Z format) to stdout, errors to stderr
# Exit: 0 on success, 1 on failure
# Example: ./detect-version-from-files.sh "."
# Example Output: "8.0.0"

set -euo pipefail

PROJECT_ROOT="${1:-.}"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "ERROR: Project root directory not found: $PROJECT_ROOT" >&2
    exit 1
fi

VERSION=""

# Priority 1: Check global.json
GLOBAL_JSON="$PROJECT_ROOT/global.json"
if [ -f "$GLOBAL_JSON" ]; then
    # Extract sdk.version using grep and sed (works without jq)
    VERSION=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$GLOBAL_JSON" 2>/dev/null | \
              sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
    
    if [ -n "$VERSION" ]; then
        # Validate it's a valid version format
        if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$VERSION"
            exit 0
        fi
    fi
fi

# Priority 2: Check Directory.Build.props
BUILD_PROPS="$PROJECT_ROOT/Directory.Build.props"
if [ -f "$BUILD_PROPS" ]; then
    # Extract TargetFramework values
    TARGET_FRAMEWORKS=$(grep -o 'TargetFramework[^>]*net[0-9]\+\.[0-9]\+' "$BUILD_PROPS" 2>/dev/null | \
                        sed 's/.*net\([0-9]\+\.[0-9]\+\).*/\1/' | sort -V -r | head -1)
    
    if [ -n "$TARGET_FRAMEWORKS" ]; then
        # Convert netX.Y to X.Y.0
        MAJOR=$(echo "$TARGET_FRAMEWORKS" | cut -d. -f1)
        MINOR=$(echo "$TARGET_FRAMEWORKS" | cut -d. -f2)
        VERSION="${MAJOR}.${MINOR}.0"
        
        if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "$VERSION"
            exit 0
        fi
    fi
fi

# Priority 3: Check README.md (Last Resort)
README="$PROJECT_ROOT/README.md"
if [ -f "$README" ]; then
    # Search for .NET version patterns
    VERSIONS=$(grep -oE '\.NET [0-9]+' "$README" 2>/dev/null | \
               sed 's/\.NET //' | sort -u)
    
    VERSION_COUNT=$(echo "$VERSIONS" | grep -c . || echo "0")
    
    if [ "$VERSION_COUNT" -eq 0 ]; then
        # Try other patterns
        VERSIONS=$(grep -oE 'Framework:[[:space:]]*\.NET [0-9]+' "$README" 2>/dev/null | \
                   sed 's/.*\.NET //' | sort -u)
        VERSION_COUNT=$(echo "$VERSIONS" | grep -c . || echo "0")
    fi
    
    if [ "$VERSION_COUNT" -eq 1 ]; then
        MAJOR=$(echo "$VERSIONS" | head -1)
        VERSION="${MAJOR}.0.0"
        echo "$VERSION"
        exit 0
    elif [ "$VERSION_COUNT" -gt 1 ]; then
        echo "ERROR: Multiple .NET versions found in README.md: $(echo "$VERSIONS" | tr '\n' ' ')" >&2
        echo "Please specify the required version in global.json or Directory.Build.props" >&2
        exit 1
    fi
fi

# No version found
echo "ERROR: Unable to determine required .NET SDK version." >&2
echo "Please specify the version in one of: global.json, Directory.Build.props, or README.md" >&2
exit 1

