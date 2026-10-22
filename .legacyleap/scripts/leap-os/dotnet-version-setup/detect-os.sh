#!/bin/bash
# Detect OS Script
# Output: "macos", "linux", or "windows" (stdout) or error (stderr)
# Exit: 0 on success, 1 on failure

set -euo pipefail

OS_TYPE=""
UNAME_S=$(uname -s 2>/dev/null || echo "")

# macOS Detection
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$UNAME_S" == "Darwin" ]]; then
    OS_TYPE="macos"
# Linux Detection
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$UNAME_S" == "Linux" ]]; then
    OS_TYPE="linux"
# Windows Detection
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || \
     [[ -n "$WINDIR" ]] || [[ "$UNAME_S" == "MINGW"* ]] || \
     [[ "$UNAME_S" == "MSYS"* ]]; then
    OS_TYPE="windows"
else
    echo "ERROR: Unknown operating system. OSTYPE: $OSTYPE, uname -s: $UNAME_S" >&2
    exit 1
fi

echo "$OS_TYPE"
exit 0

