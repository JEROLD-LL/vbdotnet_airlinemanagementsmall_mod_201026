#!/bin/bash
set -euo pipefail
# Build Solution Script
# Purpose: Builds .NET solution or project file with specified configuration and timeout
# Input: $1 = solution_path (optional, auto-detected), $2 = configuration (optional, default: Debug), $3 = output_file (optional), $4 = timeout (optional, default: 600)
# Output: Build output to stdout and optionally to file
# Exit: 0 on success, 1 on failure
# Example: ./build-solution.sh "MusicStore.sln" "Debug" ".legacyleap/build-output.txt" "600"
# Example Output: Build output with compilation results, errors, and warnings

SOLUTION_PATH="$1"
CONFIGURATION="${2:-Debug}"
OUTPUT_FILE="$3"
TIMEOUT="${4:-600}"

# Auto-detect solution file if not provided
if [ -z "$SOLUTION_PATH" ]; then
    SOLUTION_PATH=$(find . -maxdepth 1 -name "*.sln" | head -1)
    if [ -z "$SOLUTION_PATH" ]; then
        SOLUTION_PATH=$(find . -name "*.csproj" -type f | head -1)
    fi
fi

if [ -z "$SOLUTION_PATH" ] || [ ! -f "$SOLUTION_PATH" ]; then
    echo "ERROR: Solution or project file not found" >&2
    exit 1
fi

# Get project root directory (parent of solution file or current directory)
PROJECT_ROOT=$(dirname "$(realpath "$SOLUTION_PATH")" 2>/dev/null || echo ".")

# Create .tmp directory if it doesn't exist
mkdir -p .legacyleap/.agent-state/.tmp

# Step 1: Verify SDK version before build
# Try reading from consolidated execution-state.json first, fallback to legacy file
DETECTED_VERSION=""
if [ -f ".legacyleap/.agent-state/execution-state.json" ] && [ -f ".legacyleap/scripts/shared/manage-execution-state.sh" ]; then
    VERSION_DATA=$(bash ".legacyleap/scripts/shared/manage-execution-state.sh" "read_version" 2>/dev/null)
    if [ -n "$VERSION_DATA" ] && [ "$VERSION_DATA" != "{}" ]; then
        DETECTED_VERSION=$(echo "$VERSION_DATA" | jq -r '.version // empty' 2>/dev/null || echo "")
    fi
fi

# Fallback to legacy dotnet-version.json
if [ -z "$DETECTED_VERSION" ] && [ -f ".legacyleap/dotnet-version.json" ]; then
    if command -v jq &> /dev/null; then
        DETECTED_VERSION=$(jq -r '.version // empty' ".legacyleap/dotnet-version.json" 2>/dev/null || echo "")
        
        if [ -n "$DETECTED_VERSION" ]; then
            # Verify global.json exists and matches
            if [ -f "$PROJECT_ROOT/global.json" ]; then
                GLOBAL_VERSION=$(jq -r '.sdk.version // empty' "$PROJECT_ROOT/global.json" 2>/dev/null || echo "")
                if [ -n "$GLOBAL_VERSION" ] && [ "$GLOBAL_VERSION" != "$DETECTED_VERSION" ]; then
                    echo "WARNING: global.json version ($GLOBAL_VERSION) does not match detected version ($DETECTED_VERSION)" >&2
                    echo "INFO: Updating global.json to match detected version..." >&2
                    # Update global.json
                    if [ -f ".legacyleap/scripts/dotnet-version-setup/create-global-json.sh" ]; then
                        bash ".legacyleap/scripts/dotnet-version-setup/create-global-json.sh" "$DETECTED_VERSION" "$PROJECT_ROOT" || true
                    fi
                fi
            else
                # Create global.json if it doesn't exist
                echo "INFO: global.json not found, creating with detected version: $DETECTED_VERSION" >&2
                if [ -f ".legacyleap/scripts/dotnet-version-setup/create-global-json.sh" ]; then
                    bash ".legacyleap/scripts/dotnet-version-setup/create-global-json.sh" "$DETECTED_VERSION" "$PROJECT_ROOT" || true
                fi
            fi
            
            # Verify SDK version before build
            if [ -f ".legacyleap/scripts/shared/verify-sdk-version.sh" ]; then
                VERIFY_RESULT=$(bash ".legacyleap/scripts/shared/verify-sdk-version.sh" "$DETECTED_VERSION" "$PROJECT_ROOT" 2>&1 || echo "mismatch:unknown")
                if [[ "$VERIFY_RESULT" == "match" ]]; then
                    echo "INFO: Verified SDK version matches detected version: $DETECTED_VERSION"
                elif [[ "$VERIFY_RESULT" == mismatch:* ]]; then
                    ACTUAL_VERSION="${VERIFY_RESULT#mismatch:}"
                    echo "WARNING: SDK version mismatch. Detected: $DETECTED_VERSION, Actual: $ACTUAL_VERSION" >&2
                    echo "WARNING: Build will proceed, but version inconsistency may cause issues" >&2
                fi
            fi
        fi
    fi
fi

echo "INFO: Building $(basename "$SOLUTION_PATH") in $CONFIGURATION configuration..."

# Build with timeout and capture output
BUILD_OUTPUT=$(timeout "$TIMEOUT" dotnet build "$SOLUTION_PATH" -c "$CONFIGURATION" --no-restore 2>&1)
BUILD_EXIT_CODE=$?

# Save output to file if specified (temporary file, will be deleted after parsing)
if [ -n "$OUTPUT_FILE" ]; then
    echo "$BUILD_OUTPUT" > "$OUTPUT_FILE"
    echo "INFO: Build output saved to temporary file: $OUTPUT_FILE"
    echo "INFO: This file will be automatically deleted after parsing"
fi

# Output build result
echo "$BUILD_OUTPUT"

# Step 2: Verify SDK version after build
# Try reading from consolidated execution-state.json first, fallback to legacy file
if [ -z "$DETECTED_VERSION" ]; then
    if [ -f ".legacyleap/.agent-state/execution-state.json" ] && [ -f ".legacyleap/scripts/shared/manage-execution-state.sh" ]; then
        VERSION_DATA=$(bash ".legacyleap/scripts/shared/manage-execution-state.sh" "read_version" 2>/dev/null)
        if [ -n "$VERSION_DATA" ] && [ "$VERSION_DATA" != "{}" ]; then
            DETECTED_VERSION=$(echo "$VERSION_DATA" | jq -r '.version // empty' 2>/dev/null || echo "")
        fi
    fi
fi

# Fallback to legacy dotnet-version.json
if [ -z "$DETECTED_VERSION" ] && [ -f ".legacyleap/dotnet-version.json" ] && [ -f ".legacyleap/scripts/shared/verify-sdk-version.sh" ]; then
    if command -v jq &> /dev/null; then
        DETECTED_VERSION=$(jq -r '.version // empty' ".legacyleap/dotnet-version.json" 2>/dev/null || echo "")
        
        if [ -n "$DETECTED_VERSION" ]; then
            VERIFY_RESULT=$(bash ".legacyleap/scripts/shared/verify-sdk-version.sh" "$DETECTED_VERSION" "$PROJECT_ROOT" 2>&1 || echo "mismatch:unknown")
            if [[ "$VERIFY_RESULT" == "match" ]]; then
                echo "INFO: Post-build verification: SDK version matches detected version: $DETECTED_VERSION"
            elif [[ "$VERIFY_RESULT" == mismatch:* ]]; then
                ACTUAL_VERSION="${VERIFY_RESULT#mismatch:}"
                echo "ERROR: Post-build verification failed: SDK version mismatch" >&2
                echo "ERROR: Detected version: $DETECTED_VERSION, Actual version used: $ACTUAL_VERSION" >&2
                echo "ERROR: This indicates the build may have used a different SDK than expected" >&2
                # Don't fail the build, but log the error
            fi
        fi
    fi
fi

if [ $BUILD_EXIT_CODE -eq 124 ]; then
    echo "ERROR: Build timed out after ${TIMEOUT} seconds" >&2
    exit 1
elif [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Build completed successfully"
    exit 0
else
    echo "ERROR: Build failed with exit code: $BUILD_EXIT_CODE" >&2
    exit 1
fi

