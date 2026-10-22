#!/bin/bash
# Persist PATH Script
# Input: $1 = dotnet_path, $2 = shell_type (optional, auto-detected)
# Exit: 0 on success, 1 on failure

set -euo pipefail

DOTNET_PATH="$1"
SHELL_TYPE="$2"

if [ -z "$DOTNET_PATH" ]; then
    echo "ERROR: dotnet_path not provided" >&2
    exit 1
fi

# Auto-detect shell type if not provided
if [ -z "$SHELL_TYPE" ]; then
    if [ -n "$ZSH_VERSION" ]; then
        SHELL_TYPE="zsh"
    elif [ -n "$BASH_VERSION" ]; then
        SHELL_TYPE="bash"
    else
        SHELL_TYPE="bash"  # Default to bash
    fi
fi

# Determine shell profile file
case "$SHELL_TYPE" in
    "bash")
        PROFILE_FILE="$HOME/.bashrc"
        # Also check .bash_profile for macOS
        if [[ "$OSTYPE" == "darwin"* ]] && [ -f "$HOME/.bash_profile" ]; then
            PROFILE_FILE="$HOME/.bash_profile"
        fi
        ;;
    "zsh")
        PROFILE_FILE="$HOME/.zshrc"
        ;;
    *)
        echo "ERROR: Unsupported shell type: $SHELL_TYPE" >&2
        exit 1
        ;;
esac

# Check if dotnet path already exists in PATH
if grep -q "export PATH.*dotnet" "$PROFILE_FILE" 2>/dev/null; then
    echo "WARNING: dotnet PATH entry already exists in $PROFILE_FILE" >&2
    echo "Skipping PATH modification to avoid duplicates" >&2
    exit 0
fi

# Create profile file if it doesn't exist
if [ ! -f "$PROFILE_FILE" ]; then
    touch "$PROFILE_FILE"
    echo "Created shell profile: $PROFILE_FILE" >&2
fi

# Add dotnet to PATH with clear comment
{
    echo ""
    echo "# Added by .NET Version Setup Agent on $(date +%Y-%m-%d)"
    echo "# Add .NET SDK to PATH"
    echo "export PATH=\"\$PATH:$DOTNET_PATH\""
} >> "$PROFILE_FILE"

if [ $? -eq 0 ]; then
    echo "SUCCESS: Added dotnet to PATH in $PROFILE_FILE"
    exit 0
else
    echo "ERROR: Failed to modify $PROFILE_FILE" >&2
    exit 1
fi

