#!/bin/bash
set -uo pipefail
# Run Technical Specification Documentation Script
# Purpose: Executes `take-leap technical-doc --latest --ingest_vectorstore` in the
#          CURRENT shell session to generate the Technical Specification Documentation
#          (TSD) from the MCM. MUST NOT be delegated.
# Input:   $1 = log_file (optional, default: .legacyleap/.agent-state/logs/tsd.log)
# Output:  take-leap stdout/stderr streamed to terminal AND tee'd to the log file.
#          TSD written under <comprehend>/technical_doc/v_N/Latest_TSD_Document/.
# Exit:    0 on success, 1 on failure
# Example: ./run-technical-doc.sh
# Example: ./run-technical-doc.sh "/tmp/tsd.log"

LOG_FILE="${1:-.legacyleap/.agent-state/logs/tsd.log}"
mkdir -p "$(dirname "$LOG_FILE")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Verify prerequisites
if [ -f "$SCRIPT_DIR/check-takeleap-prerequisites.sh" ]; then
    if ! bash "$SCRIPT_DIR/check-takeleap-prerequisites.sh"; then
        echo "ERROR: Prerequisites check failed — cannot generate TSD" >&2
        exit 1
    fi
fi

# Re-activate conda in THIS shell
if [ "${CONDA_DEFAULT_ENV:-}" != "legacyleap" ] && command -v conda &> /dev/null; then
    CONDA_BASE=$(conda info --base 2>/dev/null || echo "")
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        # shellcheck disable=SC1091
        source "$CONDA_BASE/etc/profile.d/conda.sh"
        conda activate legacyleap || true
    fi
fi

# Step 2: Resolve paths from metadata.json and verify MCM exists
METADATA_FILE=".legacyleap/metadata.json"
SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('scan_assessment_reports',''))" 2>/dev/null || echo "")
COMPREHEND_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('comprehend',''))" 2>/dev/null || echo "")

if [ -z "$SCAN_REPORTS_PATH" ] || [ -z "$COMPREHEND_PATH" ]; then
    echo "ERROR: Required paths not found in $METADATA_FILE (scan_assessment_reports, comprehend)" >&2
    exit 1
fi

MCM_PATH="$SCAN_REPORTS_PATH/meta_cognitive_model.json"
if [ ! -f "$MCM_PATH" ]; then
    echo "ERROR: MCM not found at $MCM_PATH — run the MCM scan first" >&2
    exit 1
fi

TSD_ROOT="$COMPREHEND_PATH/technical_doc"
mkdir -p "$TSD_ROOT"

TSD_LATEST_BEFORE=$(ls -d "${TSD_ROOT}"/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1 | grep -o 'v_[0-9]*' | cut -d_ -f2 || echo "")
TSD_LATEST_BEFORE="${TSD_LATEST_BEFORE:-none}"

echo "INFO: Starting TSD generation"
echo "INFO: Command:         take-leap technical-doc --latest --ingest_vectorstore"
echo "INFO: Log file:        $LOG_FILE"
echo "INFO: MCM input:       $MCM_PATH"
echo "INFO: Comprehend root: $TSD_ROOT"
echo "INFO: Latest TSD v:    $TSD_LATEST_BEFORE"
echo ""

START_TS=$(date +%s)

# Step 3: Execute the take-leap command
set +e
take-leap technical-doc --latest --ingest_vectorstore 2>&1 | tee "$LOG_FILE"
TSD_EXIT_CODE=${PIPESTATUS[0]}
set -e

END_TS=$(date +%s)
DURATION=$((END_TS - START_TS))
echo ""
echo "INFO: TSD generation duration: ${DURATION}s"
echo "INFO: TSD exit code:           $TSD_EXIT_CODE"

if [ "$TSD_EXIT_CODE" -ne 0 ]; then
    echo "ERROR: take-leap technical-doc failed with exit code $TSD_EXIT_CODE" >&2
    echo "ERROR: See full output in: $LOG_FILE" >&2
    exit 1
fi

# Step 4: Verify TSD output
TSD_LATEST_AFTER=$(ls -d "${TSD_ROOT}"/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1)
if [ -z "$TSD_LATEST_AFTER" ]; then
    echo "ERROR: No TSD version folder produced under $TSD_ROOT" >&2
    exit 1
fi

TSD_MD="${TSD_LATEST_AFTER}Latest_TSD_Document/Latest_tsd.md"
if [ ! -f "$TSD_MD" ]; then
    echo "ERROR: Expected TSD markdown not found: $TSD_MD" >&2
    exit 1
fi

TSD_WORDS=$(wc -w < "$TSD_MD" | tr -d ' ')
echo "SUCCESS: TSD ready — $TSD_MD (${TSD_WORDS} words)"

exit 0
