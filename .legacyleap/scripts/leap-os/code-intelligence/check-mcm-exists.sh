#!/bin/bash
set -uo pipefail
# Check MCM Exists Script
# Purpose: Determine whether a valid Meta Cognitive Model (MCM) has ALREADY been
#          generated for this project, so callers can skip the MCM scan entirely.
#          A valid MCM means meta_cognitive_model.json exists, parses as JSON, and
#          contains at least one part (i.e. the scan actually produced a model).
# Input:   none (resolves scan_assessment_reports from .legacyleap/metadata.json)
# Output:  A single "MCM_CHECK: ..." status line describing the outcome.
# Exit:    0 if a valid MCM already exists (SKIP the scan)
#          1 if the MCM is missing/empty/invalid (RUN the scan)
# Example: if bash check-mcm-exists.sh; then echo "skip scan"; else echo "run scan"; fi

METADATA_FILE=".legacyleap/metadata.json"
if [ ! -f "$METADATA_FILE" ]; then
    echo "MCM_CHECK: $METADATA_FILE not found — cannot verify MCM" >&2
    exit 1
fi

SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('scan_assessment_reports',''))" 2>/dev/null || echo "")
if [ -z "$SCAN_REPORTS_PATH" ]; then
    echo "MCM_CHECK: 'scan_assessment_reports' not set in $METADATA_FILE" >&2
    exit 1
fi

MCM_PATH="$SCAN_REPORTS_PATH/meta_cognitive_model.json"
if [ ! -f "$MCM_PATH" ]; then
    echo "MCM_CHECK: no MCM at $MCM_PATH — scan required"
    exit 1
fi

# Validate the MCM is real (parseable + has at least one part). The exit code of
# this python block becomes the script's exit code.
python3 - "$MCM_PATH" <<'PY'
import json, sys

path = sys.argv[1]
try:
    with open(path) as f:
        mcm = json.load(f)
except Exception as exc:
    print(f"MCM_CHECK: MCM at {path} is not valid JSON ({exc}) — scan required")
    sys.exit(1)

parts = len(mcm.get("nodes", {}).get("parts", []))
rels = len(mcm.get("relationships", []))

if parts == 0:
    print(f"MCM_CHECK: MCM at {path} has no parts — treat as not generated, scan required")
    sys.exit(1)

print(f"MCM_CHECK: valid MCM already present — {parts} parts, {rels} relationships ({path})")
sys.exit(0)
PY
