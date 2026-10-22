#!/bin/bash
set -uo pipefail
# Run MCM Scan Script
# Purpose: Executes `take-leap scan --latest` in the CURRENT shell session to generate
#          the Meta Cognitive Model (MCM) from legacy source code. This MUST NOT be
#          delegated to another agent or substituted with synthetic data.
# Input:   $1 = log_file (optional, default: .legacyleap/.agent-state/logs/mcm_scan.log)
# Output:  take-leap stdout/stderr streamed to terminal AND tee'd to the log file.
#          MCM written to <scan_assessment_reports>/meta_cognitive_model.json.
# Exit:    0 on success, 1 on failure
# Example: ./run-mcm-scan.sh
# Example: ./run-mcm-scan.sh "/tmp/mcm_scan.log"

LOG_FILE="${1:-.legacyleap/.agent-state/logs/mcm_scan.log}"
mkdir -p "$(dirname "$LOG_FILE")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Verify prerequisites (conda env, take-leap CLI, metadata.json)
if [ -f "$SCRIPT_DIR/check-takeleap-prerequisites.sh" ]; then
    if ! bash "$SCRIPT_DIR/check-takeleap-prerequisites.sh"; then
        echo "ERROR: Prerequisites check failed — cannot run MCM scan" >&2
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

# Step 2: Resolve MCM output location from metadata.json
METADATA_FILE=".legacyleap/metadata.json"
SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('scan_assessment_reports',''))" 2>/dev/null || echo "")
if [ -z "$SCAN_REPORTS_PATH" ]; then
    echo "ERROR: 'scan_assessment_reports' key not found in $METADATA_FILE" >&2
    exit 1
fi

MCM_PATH="$SCAN_REPORTS_PATH/meta_cognitive_model.json"
mkdir -p "$SCAN_REPORTS_PATH"

MCM_BEFORE_MTIME=""
if [ -f "$MCM_PATH" ]; then
    MCM_BEFORE_MTIME=$(stat -c %Y "$MCM_PATH" 2>/dev/null || stat -f %m "$MCM_PATH" 2>/dev/null || echo "")
fi

echo "INFO: Starting MCM scan"
echo "INFO: Command:   take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion"
echo "INFO: Log file:  $LOG_FILE"
echo "INFO: MCM path:  $MCM_PATH"
echo ""

START_TS=$(date +%s)

# Step 3: Execute the actual take-leap command. Stream output to both terminal and log file.
# IMPORTANT: This is the line that MUST run directly in the caller's shell — do not delegate.
set +e
take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion 2>&1 | tee "$LOG_FILE"
SCAN_EXIT_CODE=${PIPESTATUS[0]}
set -e

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))
echo ""
echo "INFO: Scan duration: ${DURATION}s"
echo "INFO: Scan exit code: $SCAN_EXIT_CODE"

if [ "$SCAN_EXIT_CODE" -ne 0 ]; then
    echo "ERROR: take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion failed with exit code $SCAN_EXIT_CODE" >&2
    echo "ERROR: See full output in: $LOG_FILE" >&2
    exit 1
fi

# Step 4: Verify MCM output exists and was updated
if [ ! -f "$MCM_PATH" ]; then
    echo "ERROR: Scan reported success but MCM was not produced at $MCM_PATH" >&2
    exit 1
fi

MCM_AFTER_MTIME=$(stat -c %Y "$MCM_PATH" 2>/dev/null || stat -f %m "$MCM_PATH" 2>/dev/null || echo "")
if [ -n "$MCM_BEFORE_MTIME" ] && [ "$MCM_BEFORE_MTIME" = "$MCM_AFTER_MTIME" ]; then
    echo "WARNING: MCM file was not updated during scan (mtime unchanged)" >&2
fi

# Step 5: Summarize MCM contents (parts + relationships)
python3 - "$MCM_PATH" <<'PY'
import json, sys
mcm_path = sys.argv[1]
try:
    with open(mcm_path) as f:
        mcm = json.load(f)
    parts = len(mcm.get('nodes', {}).get('parts', []))
    rels = len(mcm.get('relationships', []))
    print(f"SUCCESS: MCM ready — {parts} parts, {rels} relationships")
except Exception as e:
    print(f"ERROR: Failed to parse MCM at {mcm_path}: {e}", file=sys.stderr)
    sys.exit(1)
PY

exit 0
