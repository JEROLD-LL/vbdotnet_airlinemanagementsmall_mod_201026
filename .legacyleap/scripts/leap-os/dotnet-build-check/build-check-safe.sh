#!/bin/bash
set -uo pipefail
# Safe Build Script for dotnet-build-check
# Purpose: Builds .NET solution WITHOUT modifying source directory
# Input: $1 = solution_path (optional, auto-detected), $2 = configuration (optional, default: Debug), $3 = output_file (optional), $4 = timeout (optional, default: 600)
# Output: Build output to stdout and optionally to file
# Exit: 0 on success, 1 on failure
# Example: ./build-check-safe.sh "MusicStore.sln" "Debug" ".legacyleap/.agent-state/.tmp/build-output.txt" "600"
#
# SAFETY GUARANTEES:
# - NEVER creates or modifies global.json
# - NEVER creates build artifacts in source directory
# - Uses -p:BaseOutputPath and -p:BaseIntermediateOutputPath to redirect all output to temporary location
# - Artifacts stored in: .legacyleap/.agent-state/.tmp/build-artifacts/
# - Safe for read-only builds on source code

SOLUTION_PATH="$1"
CONFIGURATION="${2:-Debug}"
OUTPUT_FILE="$3"
TIMEOUT="${4:-600}"

# Directory for build artifacts (temporary, isolated from source)
BUILD_ARTIFACTS_DIR=".legacyleap/.agent-state/.tmp/build-artifacts"

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

# Create temporary artifacts directory
mkdir -p "$BUILD_ARTIFACTS_DIR"

echo "INFO: Building $(basename "$SOLUTION_PATH") in $CONFIGURATION configuration..."
echo "INFO: Build artifacts will be stored in: $BUILD_ARTIFACTS_DIR"

# Create live build log for real-time monitoring (Fix #6)
LIVE_BUILD_LOG=".legacyleap/.agent-state/.tmp/build-live.log"
mkdir -p "$(dirname "$LIVE_BUILD_LOG")"

# Build with output redirection using BaseOutputPath and BaseIntermediateOutputPath
# This prevents creation of bin/ and obj/ in source directory
# Stream output to both console AND live log file for real-time monitoring
BUILD_OUTPUT=$(timeout "$TIMEOUT" dotnet build "$SOLUTION_PATH" \
    -c "$CONFIGURATION" \
    -p:BaseOutputPath="$BUILD_ARTIFACTS_DIR" \
    -p:BaseIntermediateOutputPath="$BUILD_ARTIFACTS_DIR/obj/" \
    2>&1 | tee "$LIVE_BUILD_LOG")

BUILD_EXIT_CODE=$?

# Save output to file if specified (temporary file, will be deleted after parsing)
if [ -n "$OUTPUT_FILE" ]; then
    # Use atomic write for reliability (Fix #3)
    TEMP_OUTPUT="${OUTPUT_FILE}.tmp"
    echo "$BUILD_OUTPUT" > "$TEMP_OUTPUT" || {
        echo "ERROR: Failed to write to temporary output file: $TEMP_OUTPUT" >&2
        exit 1
    }
    
    # Atomic move to finalize (Fix #3)
    mv "$TEMP_OUTPUT" "$OUTPUT_FILE" || {
        echo "ERROR: Failed to finalize build output file: $OUTPUT_FILE" >&2
        rm -f "$TEMP_OUTPUT"
        exit 1
    }
    
    # Validate file was created successfully (Fix #1)
    if [ ! -f "$OUTPUT_FILE" ]; then
        echo "ERROR: Failed to create build output file: $OUTPUT_FILE" >&2
        exit 1
    fi
    
    # Validate file has content (Fix #1)
    if [ ! -s "$OUTPUT_FILE" ]; then
        echo "ERROR: Build output file is empty: $OUTPUT_FILE" >&2
        exit 1
    fi
    
    # Validate output contains expected dotnet summary patterns (Fix #4)
    if ! grep -q "Build\|Restore\|error\|warning\|succeeded\|failed" "$OUTPUT_FILE"; then
        echo "WARNING: Build output file may be incomplete or corrupted" >&2
    fi
    
    echo "INFO: Build output saved to temporary file: $OUTPUT_FILE"
    echo "INFO: This file will be automatically deleted after parsing"
fi

# Output build result
echo "$BUILD_OUTPUT"

# Handle exit codes
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
