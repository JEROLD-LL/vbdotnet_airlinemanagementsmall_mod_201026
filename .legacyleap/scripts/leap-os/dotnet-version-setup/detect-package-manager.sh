#!/bin/bash
# Detect Package Manager Script
# Input: $1 = os_type (macos, linux, windows)
# Output: package manager name (stdout) or error (stderr)
# Exit: 0 on success, 1 on failure

set -euo pipefail

OS_TYPE="$1"

if [ -z "$OS_TYPE" ]; then
    echo "ERROR: OS type not provided" >&2
    exit 1
fi

PKG_MGR=""

case "$OS_TYPE" in
    "macos")
        if command -v brew &> /dev/null; then
            PKG_MGR="brew"
        else
            echo "ERROR: Homebrew not found. Please install Homebrew first." >&2
            echo "Visit: https://brew.sh" >&2
            exit 1
        fi
        ;;
    "linux")
        if command -v apt-get &> /dev/null; then
            PKG_MGR="apt"
        elif command -v dnf &> /dev/null; then
            PKG_MGR="dnf"
        elif command -v pacman &> /dev/null; then
            PKG_MGR="pacman"
        else
            echo "ERROR: No supported package manager found (apt-get, dnf, or pacman)." >&2
            echo "Please install one of the supported package managers." >&2
            exit 1
        fi
        ;;
    "windows")
        if command -v winget &> /dev/null 2>&1; then
            PKG_MGR="winget"
        elif command -v choco &> /dev/null 2>&1; then
            PKG_MGR="choco"
        else
            echo "ERROR: No package manager found. Please install winget or Chocolatey." >&2
            echo "winget: Usually pre-installed on Windows 11/10" >&2
            echo "Chocolatey: Visit https://chocolatey.org" >&2
            exit 1
        fi
        ;;
    *)
        echo "ERROR: Unsupported OS type: $OS_TYPE" >&2
        exit 1
        ;;
esac

echo "$PKG_MGR"
exit 0

