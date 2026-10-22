#!/bin/bash
set -euo pipefail
# Validate Fix Impact Script
# Input: $1 = file_path, $2 = fix_applied, $3 = original_method_signature (optional), $4 = dotnet_version (optional)
# Exit code: 0 on success (valid), 1 on failure (invalid)
# Output: Validation result

FILE_PATH="$1"
FIX_APPLIED="${2:-}"
ORIGINAL_METHOD_SIGNATURE="${3:-}"
DOTNET_VERSION="${4:-}"

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    echo "ERROR: File not found: $FILE_PATH" >&2
    exit 1
fi

# Validate API contract if original method signature provided
if [ -n "$ORIGINAL_METHOD_SIGNATURE" ]; then
    # Extract method name and return type from original signature
    ORIGINAL_METHOD_NAME=$(echo "$ORIGINAL_METHOD_SIGNATURE" | grep -oE '[[:alnum:]_]+\s*\(' | head -1 | tr -d ' (' || echo "")
    ORIGINAL_RETURN_TYPE=$(echo "$ORIGINAL_METHOD_SIGNATURE" | grep -oE '(public|private|protected|internal)\s+(static\s+)?[[:alnum:]_<>\[\]]+' | awk '{print $NF}' || echo "")
    
    # Check if method signature still exists and matches
    if [ -n "$ORIGINAL_METHOD_NAME" ]; then
        CURRENT_SIGNATURE=$(grep -E "^\s*(public|private|protected|internal)\s+(static\s+)?[[:alnum:]_<>\[\]]+\s+${ORIGINAL_METHOD_NAME}\s*\(" "$FILE_PATH" | head -1 || echo "")
        CURRENT_RETURN_TYPE=$(echo "$CURRENT_SIGNATURE" | grep -oE '(public|private|protected|internal)\s+(static\s+)?[[:alnum:]_<>\[\]]+' | awk '{print $NF}' || echo "")
        
        if [ -n "$CURRENT_SIGNATURE" ] && [ -n "$ORIGINAL_RETURN_TYPE" ] && [ "$CURRENT_RETURN_TYPE" != "$ORIGINAL_RETURN_TYPE" ]; then
            echo "ERROR: API contract changed - return type changed from $ORIGINAL_RETURN_TYPE to $CURRENT_RETURN_TYPE" >&2
            exit 1
        fi
    fi
fi

# Basic syntax checks for C# files
if [[ "$FILE_PATH" =~ \.(cs)$ ]]; then
    # Check for balanced braces
    OPEN_BRACES=$(grep -o '{' "$FILE_PATH" | wc -l | tr -d ' ')
    CLOSE_BRACES=$(grep -o '}' "$FILE_PATH" | wc -l | tr -d ' ')
    
    if [ "$OPEN_BRACES" -ne "$CLOSE_BRACES" ]; then
        echo "ERROR: Unbalanced braces detected (Open: $OPEN_BRACES, Close: $CLOSE_BRACES)" >&2
        exit 1
    fi
    
    # Check for balanced parentheses
    OPEN_PARENS=$(grep -o '(' "$FILE_PATH" | wc -l | tr -d ' ')
    CLOSE_PARENS=$(grep -o ')' "$FILE_PATH" | wc -l | tr -d ' ')
    
    if [ "$OPEN_PARENS" -ne "$CLOSE_PARENS" ]; then
        echo "ERROR: Unbalanced parentheses detected (Open: $OPEN_PARENS, Close: $CLOSE_PARENS)" >&2
        exit 1
    fi
    
    # Check for balanced brackets
    OPEN_BRACKETS=$(grep -o '\[' "$FILE_PATH" | wc -l | tr -d ' ')
    CLOSE_BRACKETS=$(grep -o ']' "$FILE_PATH" | wc -l | tr -d ' ')
    
    if [ "$OPEN_BRACKETS" -ne "$CLOSE_BRACKETS" ]; then
        echo "ERROR: Unbalanced brackets detected (Open: $OPEN_BRACKETS, Close: $CLOSE_BRACKETS)" >&2
        exit 1
    fi
    
    # Validate .NET version not changed (if .csproj file and version provided)
    if [[ "$FILE_PATH" =~ \.(csproj)$ ]] && [ -n "$DOTNET_VERSION" ]; then
        # Extract TargetFramework from .csproj file
        TARGET_FW=$(grep -oE '<TargetFramework[^>]*>([^<]+)</TargetFramework>' "$FILE_PATH" | head -1 | sed 's/.*>\(.*\)<.*/\1/' || echo "")
        if [ -z "$TARGET_FW" ]; then
            TARGET_FW=$(grep -oE '<TargetFrameworks[^>]*>([^<]+)</TargetFrameworks>' "$FILE_PATH" | head -1 | sed 's/.*>\(.*\)<.*/\1/' | cut -d';' -f1 || echo "")
        fi
        
        # Check if TargetFramework changed (basic check - if it contains a different major version)
        if [ -n "$TARGET_FW" ]; then
            # Extract major version from TargetFramework (e.g., net8.0 -> 8, net10.0 -> 10)
            FW_MAJOR=$(echo "$TARGET_FW" | grep -oE 'net([0-9]+)' | grep -oE '[0-9]+' | head -1 || echo "")
            VERSION_MAJOR=$(echo "$DOTNET_VERSION" | grep -oE '^([0-9]+)' | head -1 || echo "")
            
            if [ -n "$FW_MAJOR" ] && [ -n "$VERSION_MAJOR" ] && [ "$FW_MAJOR" != "$VERSION_MAJOR" ]; then
                echo "ERROR: .NET version changed - TargetFramework is $TARGET_FW but expected .NET $DOTNET_VERSION" >&2
                exit 1
            fi
        fi
    fi
fi

echo "SUCCESS: Basic syntax validation passed"
exit 0

