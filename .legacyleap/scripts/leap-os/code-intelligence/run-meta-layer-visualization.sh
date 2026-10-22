#!/bin/bash
set -uo pipefail
# Run Meta-Layer Visualization Script
# Purpose: Executes `take-leap meta-layer-visualization` in the CURRENT shell session
#          to generate the standalone HTML visualization from the active MCM.
#          This MUST NOT be delegated to another agent or substituted with synthetic data.
# Input:   $1 = log_file (optional, default: .legacyleap/.agent-state/logs/meta_layer_visualization.log)
# Output:  take-leap stdout/stderr streamed to terminal AND tee'd to the log file.
#          Visualization written to <scan_assessment_reports>/mcm_visualization.html.
# Exit:    0 on success, 1 on failure
# Example: ./run-meta-layer-visualization.sh
# Example: ./run-meta-layer-visualization.sh "/tmp/meta_layer_visualization.log"

LOG_FILE="${1:-.legacyleap/.agent-state/logs/meta_layer_visualization.log}"
mkdir -p "$(dirname "$LOG_FILE")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Verify prerequisites (conda env, take-leap CLI, metadata.json)
if [ -f "$SCRIPT_DIR/check-takeleap-prerequisites.sh" ]; then
    if ! bash "$SCRIPT_DIR/check-takeleap-prerequisites.sh"; then
        echo "ERROR: Prerequisites check failed — cannot run meta-layer visualization" >&2
        exit 1
    fi
fi

# Re-activate conda in THIS shell (check script runs in a subshell, so env is not inherited)
if [ "${CONDA_DEFAULT_ENV:-}" != "legacyleap" ] && command -v conda &> /dev/null; then
    CONDA_BASE=$(conda info --base 2>/dev/null || echo "")
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        # shellcheck disable=SC1091
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate legacyleap || true
    fi
fi

# Step 2: Resolve input/output locations from metadata.json and verify MCM exists
METADATA_FILE=".legacyleap/metadata.json"
SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('scan_assessment_reports',''))" 2>/dev/null || echo "")
if [ -z "$SCAN_REPORTS_PATH" ]; then
    echo "ERROR: 'scan_assessment_reports' key not found in $METADATA_FILE" >&2
    exit 1
fi

MCM_PATH="$SCAN_REPORTS_PATH/meta_cognitive_model.json"
if [ ! -f "$MCM_PATH" ]; then
    echo "ERROR: MCM not found at $MCM_PATH — run the MCM scan first" >&2
    exit 1
fi

VIZ_PATH="$SCAN_REPORTS_PATH/mcm_visualization.html"
mkdir -p "$SCAN_REPORTS_PATH"

VIZ_BEFORE_MTIME=""
if [ -f "$VIZ_PATH" ]; then
    VIZ_BEFORE_MTIME=$(stat -c %Y "$VIZ_PATH" 2>/dev/null || stat -f %m "$VIZ_PATH" 2>/dev/null || echo "")
fi

echo "INFO: Starting meta-layer visualization"
echo "INFO: Command:            take-leap meta-layer-visualization"
echo "INFO: Log file:           $LOG_FILE"
echo "INFO: MCM input:          $MCM_PATH"
echo "INFO: Visualization path: $VIZ_PATH"
echo ""

START_TS=$(date +%s)

# Step 3: Execute the actual take-leap command. Stream output to both terminal and log file.
# IMPORTANT: This is the line that MUST run directly in the caller's shell — do not delegate.
set +e
take-leap meta-layer-visualization 2>&1 | tee "$LOG_FILE"
VIZ_EXIT_CODE=${PIPESTATUS[0]}
set -e

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))
echo ""
echo "INFO: Visualization duration: ${DURATION}s"
echo "INFO: Visualization exit code: $VIZ_EXIT_CODE"

if [ "$VIZ_EXIT_CODE" -ne 0 ]; then
    echo "ERROR: take-leap meta-layer-visualization failed with exit code $VIZ_EXIT_CODE" >&2
    echo "ERROR: See full output in: $LOG_FILE" >&2
    exit 1
fi

# Step 4: Normalize and verify visualization output
if [ ! -f "$VIZ_PATH" ]; then
    ALT_VIZ=""
    for candidate in \
        "$SCAN_REPORTS_PATH/meta_layer_visualization.html" \
        "$SCAN_REPORTS_PATH/meta-layer-visualization.html"
    do
        if [ -f "$candidate" ]; then
            ALT_VIZ="$candidate"
            break
        fi
    done

    if [ -z "$ALT_VIZ" ]; then
        ALT_VIZ=$(find "$SCAN_REPORTS_PATH" -maxdepth 2 -type f \( -iname '*visualization*.html' -o -iname '*layer*.html' \) | head -1)
    fi

    if [ -n "$ALT_VIZ" ] && [ "$ALT_VIZ" != "$VIZ_PATH" ]; then
        cp "$ALT_VIZ" "$VIZ_PATH"
        echo "INFO: Normalized visualization output to $VIZ_PATH from $ALT_VIZ"
    fi
fi

if [ ! -f "$VIZ_PATH" ]; then
    echo "ERROR: Visualization reported success but expected HTML was not produced at $VIZ_PATH" >&2
    exit 1
fi

VIZ_AFTER_MTIME=$(stat -c %Y "$VIZ_PATH" 2>/dev/null || stat -f %m "$VIZ_PATH" 2>/dev/null || echo "")
if [ -n "$VIZ_BEFORE_MTIME" ] && [ "$VIZ_BEFORE_MTIME" = "$VIZ_AFTER_MTIME" ]; then
    echo "WARNING: Visualization file was not updated during execution (mtime unchanged)" >&2
fi

VIZ_SIZE=$(wc -c < "$VIZ_PATH" | tr -d ' ')
echo "SUCCESS: Meta-layer visualization ready — $VIZ_PATH (${VIZ_SIZE} bytes)"

exit 0
