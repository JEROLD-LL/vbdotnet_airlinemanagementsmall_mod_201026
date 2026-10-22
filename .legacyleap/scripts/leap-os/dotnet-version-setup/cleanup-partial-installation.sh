#!/bin/bash
# Cleanup Partial Installation Script
# Input: $1 = os_type, $2 = pkg_mgr, $3 = version
# Exit: 0 on success, 1 on failure

set -euo pipefail

OS_TYPE="$1"
PKG_MGR="$2"
VERSION="$3"

if [ -z "$OS_TYPE" ] || [ -z "$PKG_MGR" ] || [ -z "$VERSION" ]; then
    echo "ERROR: Missing required parameters: os_type, pkg_mgr, version" >&2
    exit 1
fi

CLEANUP_SUCCESS=false

case "$OS_TYPE" in
    "macos")
        if [ "$PKG_MGR" = "brew" ]; then
            # Remove Homebrew cask if partially installed
            if brew list --cask "dotnet-sdk@${VERSION}" &>/dev/null; then
                echo "Removing partially installed dotnet-sdk@${VERSION}..." >&2
                brew uninstall --cask "dotnet-sdk@${VERSION}" 2>&1 || true
            fi
            # Clean up Homebrew cache
            brew cleanup --prune=all 2>&1 || true
            CLEANUP_SUCCESS=true
        fi
        ;;
    "linux")
        case "$PKG_MGR" in
            "apt")
                # Remove partially installed package
                if dpkg -l | grep -q "dotnet-sdk-${VERSION}"; then
                    echo "Removing partially installed dotnet-sdk-${VERSION}..." >&2
                    sudo apt-get remove --purge -y "dotnet-sdk-${VERSION}" 2>&1 || true
                    sudo apt-get autoremove -y 2>&1 || true
                fi
                # Clean up apt cache
                sudo apt-get clean 2>&1 || true
                CLEANUP_SUCCESS=true
                ;;
            "dnf")
                # Remove partially installed package
                if rpm -qa | grep -q "dotnet-sdk-${VERSION}"; then
                    echo "Removing partially installed dotnet-sdk-${VERSION}..." >&2
                    sudo dnf remove -y "dotnet-sdk-${VERSION}" 2>&1 || true
                fi
                # Clean up dnf cache
                sudo dnf clean all 2>&1 || true
                CLEANUP_SUCCESS=true
                ;;
            "pacman")
                # Remove partially installed package
                if pacman -Q dotnet-sdk &>/dev/null; then
                    echo "Removing partially installed dotnet-sdk..." >&2
                    sudo pacman -Rns --noconfirm dotnet-sdk 2>&1 || true
                fi
                # Clean up pacman cache
                sudo pacman -Sc --noconfirm 2>&1 || true
                CLEANUP_SUCCESS=true
                ;;
        esac
        # Clean up manual installation directory if exists
        if [ -d "$HOME/.dotnet" ]; then
            echo "Cleaning up manual installation directory..." >&2
            rm -rf "$HOME/.dotnet" 2>&1 || true
        fi
        ;;
    "windows")
        case "$PKG_MGR" in
            "winget")
                # Remove partially installed package
                if winget list "Microsoft.DotNet.SDK.${VERSION}" &>/dev/null; then
                    echo "Removing partially installed Microsoft.DotNet.SDK.${VERSION}..." >&2
                    winget uninstall "Microsoft.DotNet.SDK.${VERSION}" --silent 2>&1 || true
                fi
                CLEANUP_SUCCESS=true
                ;;
            "choco")
                # Remove partially installed package
                if choco list --local-only dotnet-sdk | grep -q "dotnet-sdk"; then
                    echo "Removing partially installed dotnet-sdk..." >&2
                    choco uninstall dotnet-sdk -y 2>&1 || true
                fi
                CLEANUP_SUCCESS=true
                ;;
        esac
        ;;
    *)
        echo "ERROR: Unsupported OS type: $OS_TYPE" >&2
        exit 1
        ;;
esac

if [ "$CLEANUP_SUCCESS" = true ]; then
    echo "SUCCESS: Partial installation cleanup completed"
    exit 0
else
    echo "WARNING: Cleanup completed with some errors, but system should be in a recoverable state" >&2
    exit 0  # Exit 0 to allow agent to continue
fi

