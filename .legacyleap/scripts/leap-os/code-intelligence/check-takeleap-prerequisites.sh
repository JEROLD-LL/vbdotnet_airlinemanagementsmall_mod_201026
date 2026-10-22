#!/bin/bash
set -uo pipefail
# Check Take-Leap Prerequisites Script
# Purpose: Validates that the take-leap CLI is available, the legacyleap conda env is
#          active (or can be activated), and .legacyleap/metadata.json exists.
# Input:   None
# Output:  Informational / error messages to stdout / stderr
# Exit:    0 on success, 1 on failure
# Example: ./check-takeleap-prerequisites.sh

ERRORS=0

# Check 1: Conda environment
if [ -z "${CONDA_DEFAULT_ENV:-}" ] || [ "${CONDA_DEFAULT_ENV:-}" != "legacyleap" ]; then
    echo "INFO: Not in 'legacyleap' conda env (current: ${CONDA_DEFAULT_ENV:-none}) — attempting activation..."
    if command -v conda &> /dev/null; then
        CONDA_BASE=$(conda info --base 2>/dev/null || echo "")
        if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
            # shellcheck disable=SC1091
            source "$CONDA_BASE/etc/profile.d/conda.sh"
            if ! conda activate legacyleap 2>/dev/null; then
                echo "ERROR: Failed to activate conda env 'legacyleap'" >&2
                echo "       Create it with: conda create -n legacyleap python=3.11" >&2
                ERRORS=$((ERRORS + 1))
            else
                echo "INFO: Activated conda env 'legacyleap'"
            fi
        else
            echo "ERROR: conda profile script not found at $CONDA_BASE/etc/profile.d/conda.sh" >&2
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "ERROR: conda command not found in PATH" >&2
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "INFO: Conda env 'legacyleap' is active"
fi

# Check 2: take-leap CLI availability
if ! command -v take-leap &> /dev/null; then
    echo "ERROR: take-leap CLI not found in PATH" >&2
    echo "       Ensure the LegacyLeap platform is installed in the 'legacyleap' conda env." >&2
    ERRORS=$((ERRORS + 1))
else
    TAKELEAP_PATH=$(command -v take-leap)
    echo "INFO: take-leap CLI found: $TAKELEAP_PATH"
fi

# Check 3: .legacyleap/metadata.json exists
METADATA_FILE=".legacyleap/metadata.json"
if [ ! -f "$METADATA_FILE" ]; then
    echo "ERROR: $METADATA_FILE not found in $(pwd)" >&2
    echo "       The current directory does not appear to be a LegacyLeap-initialized project." >&2
    ERRORS=$((ERRORS + 1))
else
    echo "INFO: LegacyLeap metadata: $METADATA_FILE"
fi

# Check 4: python3 availability (used to parse metadata.json)
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found in PATH (required to parse metadata.json)" >&2
    ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
    echo "ERROR: Take-Leap prerequisites check failed with $ERRORS error(s)" >&2
    exit 1
fi

echo "SUCCESS: All Take-Leap prerequisites met"
exit 0
