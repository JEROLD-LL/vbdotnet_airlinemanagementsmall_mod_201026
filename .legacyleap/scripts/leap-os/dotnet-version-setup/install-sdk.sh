#!/bin/bash
# Install SDK Script
# Input: $1 = os_type, $2 = pkg_mgr, $3 = version (sanitized)
# Exit: 0 on success, 1 on failure

set -euo pipefail

OS_TYPE="$1"
PKG_MGR="$2"
VERSION="$3"
TIMEOUT=1800  # 30 minutes

if [ -z "$OS_TYPE" ] || [ -z "$PKG_MGR" ] || [ -z "$VERSION" ]; then
    echo "ERROR: Missing required parameters: os_type, pkg_mgr, version" >&2
    exit 1
fi

# Validate version format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Invalid version format: $VERSION" >&2
    exit 1
fi

INSTALL_SUCCESS=false

case "$OS_TYPE" in
    "macos")
        if [ "$PKG_MGR" = "brew" ]; then
            if timeout "$TIMEOUT" brew install --cask "dotnet-sdk@${VERSION}" 2>&1; then
                INSTALL_SUCCESS=true
            else
                echo "ERROR: Homebrew installation failed" >&2
                exit 1
            fi
        fi
        ;;
    "linux")
        case "$PKG_MGR" in
            "apt")
                # Verify version exists
                if ! apt-cache search "dotnet-sdk-${VERSION}" 2>/dev/null | grep -q "dotnet-sdk-${VERSION}"; then
                    echo "ERROR: Version ${VERSION} not available in repository" >&2
                    exit 1
                fi
                if timeout "$TIMEOUT" sudo apt-get update && \
                   timeout "$TIMEOUT" sudo apt-get install -y "dotnet-sdk-${VERSION}" 2>&1; then
                    INSTALL_SUCCESS=true
                else
                    echo "ERROR: apt-get installation failed" >&2
                    exit 1
                fi
                ;;
            "dnf")
                if ! dnf search "dotnet-sdk-${VERSION}" 2>/dev/null | grep -q "dotnet-sdk-${VERSION}"; then
                    echo "ERROR: Version ${VERSION} not available in repository" >&2
                    exit 1
                fi
                if timeout "$TIMEOUT" sudo dnf install -y "dotnet-sdk-${VERSION}" 2>&1; then
                    INSTALL_SUCCESS=true
                else
                    echo "ERROR: dnf installation failed" >&2
                    exit 1
                fi
                ;;
            "pacman")
                if timeout "$TIMEOUT" sudo pacman -S --noconfirm dotnet-sdk 2>&1; then
                    INSTALL_SUCCESS=true
                else
                    echo "ERROR: pacman installation failed" >&2
                    exit 1
                fi
                ;;
        esac
        ;;
    "windows")
        case "$PKG_MGR" in
            "winget")
                if timeout "$TIMEOUT" winget install "Microsoft.DotNet.SDK.${VERSION}" --version "${VERSION}" --accept-package-agreements --accept-source-agreements 2>&1; then
                    INSTALL_SUCCESS=true
                else
                    echo "ERROR: winget installation failed" >&2
                    exit 1
                fi
                ;;
            "choco")
                if timeout "$TIMEOUT" choco install dotnet-sdk --version "${VERSION}" -y 2>&1; then
                    INSTALL_SUCCESS=true
                else
                    echo "ERROR: Chocolatey installation failed" >&2
                    exit 1
                fi
                ;;
        esac
        ;;
    *)
        echo "ERROR: Unsupported OS type: $OS_TYPE" >&2
        exit 1
        ;;
esac

if [ "$INSTALL_SUCCESS" = true ]; then
    exit 0
else
    echo "ERROR: Installation failed" >&2
    exit 1
fi

