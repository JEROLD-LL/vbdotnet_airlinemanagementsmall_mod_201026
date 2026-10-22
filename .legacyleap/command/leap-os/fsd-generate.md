---
description: "Self-contained FSD pipeline: activates the legacyleap env, generates the MCM (skipped if a valid MCM already exists) + meta-layer visualization, generates the FSD (skipped if an FSD already exists), then runs the FULL inlined FSD refinement loop (baseline evaluation → decision gate → versioned copy → doc-quality improvement → re-evaluation → loop until ≥ 9.5/10) by calling the /fsd-evaluate and /doc-quality-improve leaf subagents directly, and finally converts the best FSD version to .docx."
agent: fsd-generate-orchestrator
---

# FSD Generate

This command turns legacy source code into a client-ready Functional Specification Documentation. It is **self-contained**: it does not delegate to `/leap-os/fsd-refine`. Instead it **inlines the full FSD refinement pipeline** and calls the individual `/fsd-evaluate` and `/doc-quality-improve` subagents directly. It also reuses work that already exists so it can be safely re-run.

The pipeline:

1. Generate the **MCM** from source code via `run-mcm-scan.sh` — **skipped** when a valid MCM already exists (`check-mcm-exists.sh`).
2. Render the **MCM meta-layer visualization** via `run-meta-layer-visualization.sh`.
3. Generate the **FSD** via `run-functional-doc.sh` — **skipped** when an FSD already exists (`fsd-refine-utils.sh latest`).
4. **Refine the FSD in place** — inlined baseline evaluation → decision gate → versioned copy → doc-quality improvement → re-evaluation → loop until the evaluation score reaches at least `9.5/10` or the refinement cap is hit.
5. Convert the **best FSD version** to **`.docx`**.

**Customer delight is the ultimate goal.** All deliverables carry the **LegacyLeap** watermark and branding.

## Pipeline Overview

```
Phase 0: Environment Setup & Project Discovery
    ├─ conda activate legacyleap
    ├─ Read .legacyleap/metadata.json + leap.properties
    └─ Locate legacy source code
    ↓
Phase 1: MCM Generation & Visualization
    ├─ check-mcm-exists.sh → skip scan if a valid MCM already exists
    ├─ take-leap-job.sh launch mcm-scan -- run-mcm-scan.sh   (detached, long-running; poll with await)
    └─ run-meta-layer-visualization.sh     (wraps take-leap meta-layer-visualization)
    ↓
Phase 2: FSD Generation
    ├─ fsd-refine-utils.sh latest → skip generation if an FSD already exists
    └─ take-leap-job.sh launch fsd -- run-functional-doc.sh  (detached, ≈2h; poll with await until DONE)
    ↓
Phase 3: Baseline FSD Evaluation (inlined /fsd-evaluate)
    ├─ project-digest-builder
    ├─ 5 evaluators in parallel (coverage, correctness, depth, domain, diagrams)
    ├─ readability + weighted score
    ├─ fsd-improvement-recommender, fsd-evaluation-quality-checker, fsd-evaluation-reporter
    └─ fsd-refine-utils.sh normalize-report + assert-fresh-evaluation + parse-score
    ↓
Phase 4: Baseline Decision Gate  (score ≥ 9.5 → done; else refine)
    ↓
Phase 5: Create Next Version Copy  (fsd-refine-utils.sh create-next)
    ↓
Phase 6: Document Quality Improvement (inlined /doc-quality-improve)
    ├─ doc-correctness-analyzer → doc-structure-optimizer → doc-diagram-renderer → doc-quality-verifier → doc-splitter
    ├─ .docx generation
    └─ fsd-refine-utils.sh assert-updated-file (+ sibling-version guard)
    ↓
Phase 7: Refined FSD Evaluation (inlined /fsd-evaluate)  → assert-fresh-evaluation + parse-score
    ↓
Phase 8: Decision Gate & Loop  (score ≥ 9.5 or cap → stop; else loop to Phase 5)
    ↓
Phase 9: Package Best FSD
    └─ pandoc md → .docx of the best FSD version
```

## Agents Used

`/fsd-generate` calls these subagents directly. It does **not** delegate to `fsd-evaluation-orchestrator`, `doc-quality-orchestrator`, or `fsd-refinement-orchestrator`.

| Agent | Role | Pipeline Origin | Called In |
|-------|------|-----------------|-----------|
| `project-digest-builder` | Distills MCM into a compact cached digest | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-coverage-evaluator` | FSD structural coverage against MCM inventory | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-correctness-evaluator` | Spot-checks claims against MCM data | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-depth-evaluator` | Flags vague/placeholder content | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-domain-evaluator` | FSD-style discipline and terminology | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-diagram-evaluator` | Image references and diagram coverage | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-improvement-recommender` | Ranked recommendations and draft additions | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-evaluation-quality-checker` | Self-reflection on evaluation scores | `/fsd-evaluate` | Phases 3, 7 |
| `fsd-evaluation-reporter` | Final evaluation report | `/fsd-evaluate` | Phases 3, 7 |
| `doc-correctness-analyzer` | Verifies accuracy against source code, MCM, domain | `/doc-quality-improve` | Phase 6 |
| `doc-structure-optimizer` | Reduces to 20-25 pages, fixes issues, client-presentable | `/doc-quality-improve` | Phase 6 |
| `doc-diagram-renderer` | Professional diagrams via Mermaid service | `/doc-quality-improve` | Phase 6 |
| `doc-quality-verifier` | Scores quality across 5 dimensions | `/doc-quality-improve` | Phase 6 |
| `doc-splitter` | Splits large documents into sub-documents | `/doc-quality-improve` | Phase 6 |

## Sub-Commands & Scripts (each callable independently)

| Step | Can Run Alone? | What It Does |
|------|----------------|--------------|
| `bash .legacyleap/scripts/leap-os/code-intelligence/check-mcm-exists.sh` | ✅ Yes | Exit 0 if a valid MCM already exists (skip scan), non-zero if it must be generated |
| `bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh` | ✅ Yes | Runs a long-running wrapper as a **detached, idempotent** job: `launch <job> -- <cmd>`, `await <job>` (bounded poll), `status`, `logs`, `clean`. Prevents duplicate multi-hour runs |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh` | ✅ Yes | Wrapper around `take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion`; generates MCM from source code (long-running — launch via `take-leap-job.sh`) |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh` | ✅ Yes | Wrapper around `take-leap meta-layer-visualization`; generates standalone MCM visualization HTML |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh` | ✅ Yes | Wrapper around `take-leap functional-doc --ingest_vectorstore`; generates FSD (≈2h — launch via `take-leap-job.sh`) |
| `bash .legacyleap/scripts/leap-os/fsd-refine/fsd-refine-utils.sh` | ✅ Yes | Deterministic helper: `latest`, `create-next`, `normalize-report`, `assert-fresh-evaluation`, `assert-updated-file`, `parse-score`, `score-ok` — owns versioning, artifact/freshness checks, and score parsing |

> **Why scripts instead of inline `take-leap` commands?** The wrappers in `profiles/default/scripts/code-intelligence/` (deployed to `.legacyleap/scripts/leap-os/code-intelligence/`) enforce that the `take-leap` CLI is executed directly in the calling shell, validate prerequisites (conda env, MCM presence), stream output to a log file, and verify the expected artifact was produced. The orchestrator MUST call these scripts via the `Bash` tool — never rewrite the underlying `take-leap` command inline or delegate it to a sub-agent.

> **Why the long jobs run detached.** `take-leap scan` (MCM) and `take-leap functional-doc` (FSD) can run for hours. Running them as blocking foreground calls causes agents to abandon the call on a tool timeout and then re-launch the same multi-hour job. `take-leap-job.sh` runs the wrapper **detached** (survives the tool call), captures its **exit code** as the authoritative completion signal, uses the log tail only for **stall/liveness** detection, and makes `launch` **idempotent** so a repeated launch while active/complete is a safe no-op. The agent launches once, then calls `await` repeatedly (each call ≤ 10 min) until `STATUS=DONE` — it must **never** wrap `await` in a shell loop and **never** relaunch a job that is `RUNNING` or `DONE`.

> **Artifact & freshness checks.** After every evaluation and every doc-quality pass the pipeline verifies the generated artifacts using `fsd-refine-utils.sh` (`assert-fresh-evaluation`, `assert-updated-file`, `normalize-report`, `parse-score`). This is how the pipeline confirms each subagent actually produced fresh output before a score is trusted — do not reimplement these checks inline.

## Usage

```bash
/fsd-generate
```

Refinement tuning is available via environment variables (defaults shown): `THRESHOLD=9.5`, `DOC_QUALITY_ITERATIONS=1`, `DOC_QUALITY_THRESHOLD=10`, `MAX_REFINEMENT_ITERATIONS=5`.

## LegacyLeap Branding

All FSD deliverables include:
- **LegacyLeap logo** in the header
- **"Powered by LegacyLeap"** footer on every page
- **Watermark** in `.docx` files
- **Logo path**: `profiles/default/assets/legacyleap-logo.png` (bundled with LeapOS)

---

# PHASE 0: Environment Setup & Project Discovery

## Step 1: Activate Conda Environment

```bash
echo "🔧 Activating LegacyLeap environment..."
conda activate legacyleap

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate conda environment 'legacyleap'"
    echo "   Create it with: conda create -n legacyleap python=3.11"
    exit 1
fi
echo "✅ Conda environment: legacyleap"
```

## Step 2: Read Project Configuration

```bash
METADATA_FILE="$(pwd)/.legacyleap/metadata.json"
PROPERTIES_FILE="$(pwd)/.legacyleap/leap.properties"

if [ ! -f "$METADATA_FILE" ]; then
    echo "❌ No .legacyleap/metadata.json found."
    echo "   This project has not been set up with LegacyLeap."
    echo "   Run project setup first, then try again."
    exit 1
fi

PROJECT_BASE=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['project_path'])")
COMPREHEND_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['comprehend'])")
SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['scan_assessment_reports'])")
LEGACY_CODE_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_code',''))")
LEGACY_PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_project_name',''))")
PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('name','Unknown'))")

echo "Project: $PROJECT_NAME"
echo "  Comprehend:   $COMPREHEND_PATH"
echo "  Scan reports: $SCAN_REPORTS_PATH"

PIPELINE_START=$(date +%s)
```

## Step 3: Locate Legacy Source Code

```bash
if [ -n "$LEGACY_PROJECT_NAME" ] && [ -d "${LEGACY_CODE_PATH}/${LEGACY_PROJECT_NAME}" ]; then
    LEGACY_SRC_ROOT="${LEGACY_CODE_PATH}/${LEGACY_PROJECT_NAME}"
else
    LEGACY_SRC_ROOT=$(ls -d ${LEGACY_CODE_PATH}/*/ 2>/dev/null | head -1)
fi

if [ -z "$LEGACY_SRC_ROOT" ] || [ ! -d "$LEGACY_SRC_ROOT" ]; then
    echo "❌ Legacy source code not found at: $LEGACY_CODE_PATH"
    exit 1
fi

echo "✅ Legacy source: $LEGACY_SRC_ROOT"

mkdir -p "${PROJECT_BASE}/.legacyleap/.agent-state"
```

## Step 4: Initialize Pipeline State

```json
{
  "pipeline": "fsd-generate",
  "project": "<PROJECT_NAME>",
  "started_at": "<timestamp>",
  "phases": {
    "mcm_scan": { "status": "pending" },
    "mcm_visualization": { "status": "pending" },
    "fsd_generation": { "status": "pending" },
    "baseline_evaluation": { "status": "pending" },
    "refinement": { "status": "pending", "iterations": 0 },
    "fsd_docx": { "status": "pending" }
  },
  "current_phase": "mcm_scan",
  "branding": {
    "watermark": "LegacyLeap",
    "footer": "Powered by LegacyLeap"
  }
}
```

Write to `.legacyleap/.agent-state/fsd-generate-state.json`.

```
🚀 FSD GENERATE INITIALIZED

Project: <name>
Source:  <LEGACY_SRC_ROOT>
Environment: legacyleap (conda)

Pipeline:
  1a. MCM Generation      ⏳ Pending  (check-mcm-exists.sh → run-mcm-scan.sh)
  1b. MCM Visualization   ⏳ Pending  (run-meta-layer-visualization.sh)
  2.  FSD Generation      ⏳ Pending  (fsd-refine-utils.sh latest → run-functional-doc.sh)
  3.  Baseline Evaluation ⏳ Pending  (inlined /fsd-evaluate)
  4-8. Refinement Loop    ⏳ Pending  (copy → doc-quality → re-evaluate → gate)
  9.  Package Best FSD    ⏳ Pending  (md → .docx)

Starting Phase 1...
```

---

# PHASE 1: MCM Generation & Visualization

**Purpose:** Ensure a valid MCM exists (generating it only when needed), then render its standalone meta-layer visualization.

## Step 1: Generate MCM via Scan (Skip If Already Generated)

First ask the dedicated bash check whether a valid MCM already exists. **The existence check is owned by `check-mcm-exists.sh` — do not reimplement it inline.** Only run the scan when the check fails.

**CRITICAL: THE MCM SCAN IS A LONG-RUNNING JOB — LAUNCH IT DETACHED, THEN POLL.** `take-leap scan` can run for a very long time. **Never run it as a blocking foreground call** (a tool timeout would leave you unsure whether it finished, tempting a wasteful re-run). Instead launch `run-mcm-scan.sh` as a detached job via `take-leap-job.sh` and poll it. Launch is **idempotent** — re-running `launch` while the job is active or already done is a safe no-op, so you can never accidentally start a second multi-hour scan. `run-mcm-scan.sh` still wraps `take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion`, verifies the MCM, and its exit code is captured authoritatively. **Never delegate this to another agent, create synthetic MCM data, or rewrite the `take-leap` command inline.**

```bash
MCM_PATH="${SCAN_REPORTS_PATH}/meta_cognitive_model.json"
JOB=".legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh"

echo "🔍 Phase 1a: Checking for an existing MCM..."
if bash .legacyleap/scripts/leap-os/code-intelligence/check-mcm-exists.sh; then
    echo "⏭️ MCM already generated — skipping MCM scan"
else
    echo "🔍 No valid MCM found — launching detached MCM scan..."
    bash "$JOB" launch mcm-scan -- bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh
fi
```

**Then poll to completion — one `await` call per step (do NOT wrap this in a shell loop):**

Call the following **repeatedly as separate steps**. Each call blocks at most 10 minutes and then returns the authoritative status, so you regain control every 10 minutes instead of blocking for the whole scan. Keep calling it until `STATUS=DONE`. **Do not call `launch` again between polls.**

```bash
bash "$JOB" await mcm-scan --max-wait 600
```

- `STATUS=RUNNING` → the scan is still going; call `await` again.
- `STATUS=DONE` → proceed.
- `STATUS=FAILED` → the scan exited non-zero; `bash "$JOB" logs mcm-scan --lines 60` and STOP (do not relaunch blindly).
- `STATUS=STALLED` → alive but no new log output for a long time; inspect `logs`, and only relaunch with `launch mcm-scan --force` if truly hung.
- `STATUS=DIED` → the process vanished without an exit code; inspect `logs`, then `launch mcm-scan --force`.

(If the check reported the MCM already exists, skip polling entirely.) Once `DONE`, verify the artifact:

```bash
if [ ! -f "$MCM_PATH" ]; then
    echo "❌ MCM not available at $MCM_PATH after Phase 1a"
    exit 1
fi

python3 -c "
import json
with open('$MCM_PATH') as f:
    mcm = json.load(f)
parts = len(mcm.get('nodes',{}).get('parts',[]))
rels = len(mcm.get('relationships',[]))
print(f'✅ MCM ready: {parts} parts, {rels} relationships')
"
```

Update state: `mcm_scan.status = "completed"` (or `"skipped"` when a valid MCM already existed).

## Step 2: Generate Meta-Layer Visualization

**Purpose:** Render the standalone MCM visualization HTML from the active MCM.

**CRITICAL: EXECUTE THE PREDEFINED SCRIPT DIRECTLY — DO NOT DELEGATE.** Invoke `run-meta-layer-visualization.sh` via the `Bash` tool. The script wraps `take-leap meta-layer-visualization`, requires the MCM from Step 1, streams output, and verifies `mcm_visualization.html` was produced.

```bash
MCM_VIZ_PATH="${SCAN_REPORTS_PATH}/mcm_visualization.html"

echo "🕸️ Phase 1b: Generating Meta-Layer Visualization..."
bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh
MCM_VIZ_EXIT=$?

if [ $MCM_VIZ_EXIT -ne 0 ]; then
    echo "❌ Meta-layer visualization failed (exit: $MCM_VIZ_EXIT)"
    echo "   See log: .legacyleap/.agent-state/logs/meta_layer_visualization.log"
    exit 1
fi

if [ ! -f "$MCM_VIZ_PATH" ]; then
    echo "❌ Meta-layer visualization command completed but no visualization file was found at $MCM_VIZ_PATH"
    exit 1
fi

VIZ_SIZE=$(wc -c < "$MCM_VIZ_PATH" | tr -d ' ')
echo "✅ Meta-layer visualization ready: $MCM_VIZ_PATH (${VIZ_SIZE} bytes)"
```

Update state: `mcm_visualization.status = "completed"`.

---

# PHASE 2: FSD Generation (Skip If Already Generated)

**Purpose:** Ensure an FSD exists, generating it from the MCM only when one is not already present.

Set up the deterministic FSD helper first, then ask it whether an FSD already exists in its intended versioned location. **The existence check is owned by `fsd-refine-utils.sh latest` — do not reimplement it inline.** If it succeeds, skip generation. Only generate when no FSD is found.

**CRITICAL: FSD GENERATION IS A LONG-RUNNING JOB (≈ 2 HOURS) — LAUNCH IT DETACHED, THEN POLL.** **Never run it as a blocking foreground call.** Launch `run-functional-doc.sh` as a detached job via `take-leap-job.sh` and poll it. Launch is **idempotent**, so re-running `launch` while the job is active or already done is a safe no-op — you can never accidentally start a second 2-hour run. `run-functional-doc.sh` still wraps `take-leap functional-doc --ingest_vectorstore`, validates the MCM input, verifies `Latest_fsd.md`, and its exit code is captured authoritatively. **Never delegate this to another agent or rewrite the `take-leap` command inline.**

```bash
# Resolve the deterministic fsd-refine helper (used from here through Phase 8)
UTIL=".legacyleap/scripts/leap-os/fsd-refine/fsd-refine-utils.sh"
if [ ! -x "$UTIL" ]; then
  UTIL="profiles/default/scripts/fsd-refine/fsd-refine-utils.sh"
fi
if [ ! -x "$UTIL" ]; then
  echo "❌ FATAL: fsd-refine utility script not found or not executable."
  exit 1
fi

eval_util_output() {
  local output
  local line
  output="$("$UTIL" "$@")"
  if [ -z "$output" ]; then
    echo "FATAL: fsd-refine utility produced no output for: $*" >&2
    exit 1
  fi
  while IFS= read -r line; do
    case "$line" in
      [A-Z_]*=*) ;;
      *)
        echo "FATAL: unexpected fsd-refine utility output: $line" >&2
        exit 1
        ;;
    esac
  done <<< "$output"
  eval "$output"
}

JOB=".legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh"

echo "📝 Phase 2: Checking for an existing FSD..."
if bash "$UTIL" latest >/dev/null 2>&1; then
    echo "⏭️ FSD already exists — skipping FSD generation"
    FSD_JOB_LAUNCHED=false
else
    echo "📝 No FSD found — launching detached FSD generation (this can take ~2 hours)..."
    bash "$JOB" launch fsd -- bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
    FSD_JOB_LAUNCHED=true
fi
```

**Then, only if a job was launched, poll to completion — one `await` call per step (do NOT wrap this in a shell loop):**

Call the following **repeatedly as separate steps**. Each call blocks at most 10 minutes, so you regain control every 10 minutes instead of blocking for the full ~2 hours. Keep calling until `STATUS=DONE`. **Do not call `launch` again between polls.**

```bash
bash "$JOB" await fsd --max-wait 600
```

- `STATUS=RUNNING` → still generating; call `await` again.
- `STATUS=DONE` → the FSD was produced and verified; proceed to Phase 3.
- `STATUS=FAILED` → `bash "$JOB" logs fsd --lines 60` and STOP (do not relaunch blindly).
- `STATUS=STALLED` → alive but no new log output for a long time; inspect `logs`, relaunch with `launch fsd --force` only if truly hung.
- `STATUS=DIED` → the process vanished without an exit code; inspect `logs`, then `launch fsd --force`.

Update state: `fsd_generation.status = "completed"` (or `"skipped"` when an FSD already existed).

---

# PHASE 3: Baseline FSD Evaluation (Inlined /fsd-evaluate Pipeline)

**Purpose:** Run the full FSD evaluation pipeline on the latest existing FSD before creating any copy. This phase inlines all steps that `/fsd-evaluate` would perform, calling evaluation subagents directly.

## Step 3.0: Refinement Parameters & Path Resolution

```bash
set -euo pipefail

THRESHOLD="${THRESHOLD:-9.5}"
DOC_QUALITY_ITERATIONS="${DOC_QUALITY_ITERATIONS:-1}"
DOC_QUALITY_THRESHOLD="${DOC_QUALITY_THRESHOLD:-10}"
MAX_REFINEMENT_ITERATIONS="${MAX_REFINEMENT_ITERATIONS:-5}"
SOURCE_VERSION_PATH=""
PREVIOUS_EVALUATION_REPORT=""
REFINEMENT_ITERATIONS=0
FINAL_STATUS=""
SHOULD_REFINE=true

case "$MAX_REFINEMENT_ITERATIONS" in
  ''|*[!0-9]*)
    echo "FATAL: MAX_REFINEMENT_ITERATIONS must be a positive integer."
    exit 1
    ;;
esac
[ "$MAX_REFINEMENT_ITERATIONS" -ge 1 ] || { echo "FATAL: MAX_REFINEMENT_ITERATIONS must be at least 1."; exit 1; }

# Resolve the latest FSD version + deterministic evaluation paths
eval_util_output latest
echo "Latest FSD version: $LATEST_VERSION_PATH"

# MCM_PATH is already resolved in Phase 1; validate structure for the evaluators
if [ -f "$MCM_PATH" ]; then
  python3 -c "
import json, sys
try:
    with open('$MCM_PATH') as f:
        mcm = json.load(f)
    print(f'MCM valid: {len(mcm.get(\"nodes\",{}).get(\"parts\", []))} parts')
except Exception as e:
    print(f'MCM validation failed: {e}'); sys.exit(1)
"
fi

# Detect the project source directory from MCM metadata (forwarded to evaluators)
PROJECT_PATH="${PROJECT_PATH:-}"
if [ -z "$PROJECT_PATH" ] && [ -f "$MCM_PATH" ]; then
  PROJECT_ID=$(python3 -c "
import json
with open('$MCM_PATH') as f:
    mcm = json.load(f)
print(mcm.get('metadata', {}).get('id', '') or mcm.get('metadata', {}).get('name', ''))
" 2>/dev/null || true)
  if [ -n "$PROJECT_ID" ] && [ -d "$PROJECT_ID" ]; then
    PROJECT_PATH="$PROJECT_ID"
  elif [ -d "$LEGACY_SRC_ROOT" ]; then
    PROJECT_PATH="$LEGACY_SRC_ROOT"
  fi
fi
echo "Project directory: ${PROJECT_PATH:-<none>}"
echo "Legacy code path:  ${LEGACY_CODE_PATH:-<none>}"
```

Initialize/refresh `.legacyleap/.agent-state/fsd-generate-state.json` with `current_phase = "baseline_evaluation"`.

## Step 3.1: Initialize Evaluation State

Create `.legacyleap/.agent-state/fsd-evaluation-state.json`:

```json
{
  "fsd_path": "$LATEST_FSD_MARKDOWN",
  "mcm_path": "$MCM_PATH",
  "project_path": "$PROJECT_PATH",
  "legacy_code_path": "$LEGACY_CODE_PATH",
  "output_dir": "$LATEST_EVALUATION_DIR",
  "evaluation_date": "<current-iso-timestamp>",
  "status": "initialized",
  "digest_status": "pending",
  "evaluations": {
    "coverage": { "status": "pending", "score": null },
    "correctness": { "status": "pending", "score": null },
    "depth": { "status": "pending", "score": null },
    "domain": { "status": "pending", "score": null },
    "diagrams": { "status": "pending", "score": null },
    "readability": { "status": "pending", "score": null }
  },
  "overall_score": null,
  "outcome": null
}
```

Set `OUTPUT_DIR` to `$LATEST_EVALUATION_DIR` so that evaluation subagents write outputs there, and capture the evaluation start time **now** (before any subagent runs) for the freshness check in Step 3.9:

```bash
export OUTPUT_DIR="$LATEST_EVALUATION_DIR"
BASELINE_EVALUATION_STARTED_AT=$(date +%s)
```

## Step 3.2: Build Project Digest

Invoke `project-digest-builder` using the Task tool with the following prompt:

> Build a project digest from the MCM.
>
> **Inputs:**
> - MCM path: `$MCM_PATH`
> - Project path: `$PROJECT_PATH`
> - Output path: `.legacyleap/.agent-state/project-digest.json`
>
> Parse the MCM and extract project metadata, assemblies, entities, forms, enums, operations, integrations, business rules, and statistics into a compact cached JSON digest. Use MCM SHA-256 for cache validation — if an existing digest matches the current MCM hash, reuse it.

**Validation:**

```bash
if [ -f ".legacyleap/.agent-state/project-digest.json" ]; then
    echo "Project digest created"
    python3 -c "
import json
with open('.legacyleap/.agent-state/project-digest.json') as f:
    digest = json.load(f)
print(f'Project: {digest[\"project\"][\"id\"]}')
print(f'Primary language: {digest[\"project\"][\"primary_language\"]}')
print(f'Entities: {len(digest.get(\"entities\", []))}')
print(f'Forms: {len(digest.get(\"forms\", []))}')
print(f'Operations: {len(digest.get(\"operations\", []))}')
print(f'Integrations: {len(digest.get(\"integrations\", []))}')
print(f'Business rules: {len(digest.get(\"business_rules_seen_in_code\", []))}')
print(f'MCM SHA-256: {digest[\"stats\"][\"mcm_sha256\"][:16]}...')
"
else
    echo "ERROR: project-digest-builder failed to create digest"
    exit 1
fi
```

Update state: `digest_status = "completed"`.

## Step 3.3: Parallel Evaluators (5 Dimensions)

Launch all 5 evaluator subagents **in parallel** using the Task tool. Wait for all 5 to complete before proceeding.

### Task 1: Coverage Evaluation

Invoke `fsd-coverage-evaluator` using the Task tool with the following prompt:

> Evaluate FSD coverage against expected sections and MCM inventory.
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH` (for targeted lookups if needed)
>
> Check the FSD structure against the expected section taxonomy (mandatory and recommended sections). Cross-reference MCM-derived inventories (entities, forms, integrations, enums) against what the FSD documents. Write coverage findings (score, missing_sections, coverage_percentage) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.coverage`.

### Task 2: Correctness Evaluation

Invoke `fsd-correctness-evaluator` using the Task tool with the following prompt:

> Spot-check FSD claims against MCM data and optionally legacy source code.
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH`
> - Legacy code path: `$LEGACY_CODE_PATH` (if available, for source-level spot checks)
>
> Verify 20-30 specific claims from the FSD against MCM data: entity fields, role/permission values, integration names, form names, business rule triggers, data flow descriptions. Mark each claim as SUPPORTED, UNSUPPORTED, or FALSE with evidence. Write correctness findings (score, claims[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.correctness`.

### Task 3: Depth Evaluation

Invoke `fsd-depth-evaluator` using the Task tool with the following prompt:

> Flag placeholder and vague content in the FSD.
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN`
>
> Scan the FSD for empty or near-empty sections, placeholder text (TBD, TODO, N/A), vague/generic content, journeys without steps, business rules without trigger conditions, decision points without outcomes, data entities without field descriptions. Spawn subagents for extensive sections with many subsections. Write depth findings (score, vague_sections[], placeholder_count) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.depth`.

### Task 4: Domain Alignment Evaluation

Invoke `fsd-domain-evaluator` using the Task tool with the following prompt:

> Validate FSD-style discipline and terminology consistency.
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
>
> Check for TSD leakage (SQL queries, class names, method signatures, code snippets, API endpoints), terminology consistency (domain terms used uniformly), and audience appropriateness (written for business stakeholders, not developers). Write domain findings (score, tsd_leakage[], terminology_issues[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.domain`.

### Task 5: Diagram Evaluation

Invoke `fsd-diagram-evaluator` using the Task tool with the following prompt:

> Verify diagram references and coverage in the FSD.
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN`
>
> Check all `![...]()` image references resolve to existing files. Identify sections that should have diagrams but don't (Business Overview, User Journeys, Business Workflows, Data Flow, Decision Points, Integration Points). Write diagram findings (score, broken_references[], missing_diagrams[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.diagrams`.

Wait for all 5 tasks to complete before proceeding to Step 3.4.

## Step 3.4: Readability Score (Orchestrator-Computed)

Compute the readability score directly (this is orchestrator-owned, not a subagent):

```bash
python3 -c "
import json, re

with open('$LATEST_FSD_MARKDOWN') as f:
    fsd_content = f.read()

with open('.legacyleap/.agent-state/fsd-evaluation-state.json') as f:
    state = json.load(f)

word_count = len(fsd_content.split())
section_count = len(re.findall(r'^## ', fsd_content, re.MULTILINE))
subsection_count = len(re.findall(r'^### ', fsd_content, re.MULTILINE))

target_words = 9000
word_score = 10 if 8000 <= word_count <= 10000 else max(0, 10 - abs(word_count - target_words) / 1000)
if word_count < 3000:
    word_score = min(word_score, 5.0)
elif word_count > 15000:
    word_score = min(word_score, 6.0)

structure_score = 10 if section_count >= 10 and subsection_count >= 30 else 7.0
readability_score = (word_score + structure_score) / 2

state['evaluations']['readability'] = {
    'status': 'completed',
    'score': round(readability_score, 1),
    'word_count': word_count,
    'section_count': section_count,
    'subsection_count': subsection_count
}

with open('.legacyleap/.agent-state/fsd-evaluation-state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f'Readability score: {readability_score:.1f} / 10')
"
```

## Step 3.5: Weighted Overall Score

```bash
python3 -c "
import json

with open('.legacyleap/.agent-state/fsd-evaluation-state.json') as f:
    state = json.load(f)

evals = state['evaluations']
coverage = evals['coverage'].get('score', 0) or 0
correctness = evals['correctness'].get('score', 0) or 0
depth = evals['depth'].get('score', 0) or 0
domain = evals['domain'].get('score', 0) or 0
diagrams = evals['diagrams'].get('score', 0) or 0
readability = evals['readability'].get('score', 0) or 0

overall = (coverage*0.25 + correctness*0.25 + depth*0.15 + domain*0.15 + diagrams*0.10 + readability*0.10)

if overall >= 9.0:
    outcome = 'EXCELLENT'
elif overall >= 7.5:
    outcome = 'ACCEPTABLE'
elif overall >= 5.0:
    outcome = 'NEEDS_IMPROVEMENT'
else:
    outcome = 'INSUFFICIENT'

state['overall_score'] = round(overall, 1)
state['outcome'] = outcome
state['status'] = 'scored'

with open('.legacyleap/.agent-state/fsd-evaluation-state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f'Overall Score: {overall:.1f} / 10 ({outcome})')
"
```

## Step 3.6: Improvement Recommender

Invoke `fsd-improvement-recommender` using the Task tool with the following prompt:

> Synthesize all evaluation findings and draft proposed additions for the FSD.
>
> **Environment:** `OUTPUT_DIR=$LATEST_EVALUATION_DIR`
>
> **Inputs:**
> - FSD path: `$LATEST_FSD_MARKDOWN` (to match writing style)
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (contains all evaluator findings)
> - Project digest: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH` (for drafting new content)
>
> Read findings from all 5 evaluators plus readability. Synthesize into ranked recommendations (priority, effort, impact). Draft proposed Markdown content for missing or weak sections. Write recommendations to the state file and create `$OUTPUT_DIR/fsd-proposed-additions.md` with the draft content.

**Validation:**

```bash
if [ -f "$LATEST_EVALUATION_DIR/fsd-proposed-additions.md" ]; then
    echo "Proposed additions file created"
    wc -l "$LATEST_EVALUATION_DIR/fsd-proposed-additions.md"
else
    echo "WARNING: fsd-proposed-additions.md not created (no additions needed?)"
fi
```

## Step 3.7: Quality Checker

Invoke `fsd-evaluation-quality-checker` using the Task tool with the following prompt:

> Review and validate the evaluation scorecard for consistency, accuracy, and evidence justification.
>
> **Inputs:**
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (with all evaluator findings and scores)
> - FSD path: `$LATEST_FSD_MARKDOWN` (for spot-checking claims)
> - Project digest: `.legacyleap/.agent-state/project-digest.json`
>
> Perform self-reflection on the evaluation scorecard: review each dimension's score against its collected evidence, detect score-evidence mismatches (e.g., score 8/10 but findings show major issues), check for hallucinated findings not supported by FSD/MCM, validate scoring consistency across dimensions. Adjust scores if justified by evidence. Update `.legacyleap/.agent-state/fsd-evaluation-state.json` with quality-checked scores and quality check metadata.

The quality checker may adjust dimension scores and recompute `overall_score` and `outcome`.

## Step 3.8: Reporter

Invoke `fsd-evaluation-reporter` using the Task tool with the following prompt:

> Generate the final FSD evaluation report.
>
> **Environment:** `OUTPUT_DIR=$LATEST_EVALUATION_DIR`
>
> **Inputs:**
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (with all findings and quality-checked scores)
> - FSD path: `$LATEST_FSD_MARKDOWN` (for metadata — word count, sections)
> - MCM path: `$MCM_PATH` (for project context)
>
> Generate `$OUTPUT_DIR/fsd-evaluation-report.md` with: executive summary and overall score, detailed scorecard across 6 dimensions with justifications, top 10 recommendations (prioritized), top 10 missing items, top 10 weakest sections, claim verification table, and next steps.

**Validation:**

```bash
if [ -f "$LATEST_EVALUATION_DIR/fsd-evaluation-report.md" ]; then
    echo "Evaluation report created"
    wc -l "$LATEST_EVALUATION_DIR/fsd-evaluation-report.md"
else
    echo "ERROR: fsd-evaluation-report.md not created"
    exit 1
fi
```

## Step 3.9: Consolidate and Verify Artifacts, Parse Score

Copy state + digest into the evaluation output dir, then use the helper to **verify the artifacts are fresh** (this is the artifact check for this evaluation) and parse the score:

```bash
cp .legacyleap/.agent-state/fsd-evaluation-state.json "$LATEST_EVALUATION_DIR/"
cp .legacyleap/.agent-state/project-digest.json "$LATEST_EVALUATION_DIR/" 2>/dev/null || true

"$UTIL" normalize-report --output-dir "$LATEST_EVALUATION_DIR" --report "$LATEST_EVALUATION_REPORT_PATH"
"$UTIL" assert-fresh-evaluation \
  --report "$LATEST_EVALUATION_REPORT_PATH" \
  --state "$LATEST_EVALUATION_STATE_PATH" \
  --started-at "$BASELINE_EVALUATION_STARTED_AT"

BASELINE_SCORE=$("$UTIL" parse-score --report "$LATEST_EVALUATION_REPORT_PATH" --state "$LATEST_EVALUATION_STATE_PATH")
echo "Baseline evaluation score for $LATEST_VERSION: $BASELINE_SCORE/10"
```

`assert-fresh-evaluation` fails the pipeline if the report/state were not produced fresh (missing, empty, stale, or missing `overall_score`) — do not parse a score until it passes.

Update state: `baseline_evaluation.status = "completed"`.

---

# PHASE 4: Baseline Decision Gate

If `BASELINE_SCORE >= THRESHOLD`, the latest FSD is already client-ready — record it as final and skip refinement:

```bash
if "$UTIL" score-ok --score "$BASELINE_SCORE" --threshold "$THRESHOLD"; then
  FINAL_FSD_VERSION="$LATEST_VERSION_PATH"
  FINAL_FSD_MARKDOWN="$LATEST_FSD_MARKDOWN"
  FINAL_EVALUATION_SCORE="$BASELINE_SCORE"
  FINAL_EVALUATION_REPORT="$LATEST_EVALUATION_REPORT_PATH"
  FINAL_STATUS="CLIENT_READY"
  SHOULD_REFINE=false
else
  SOURCE_VERSION_PATH="$LATEST_VERSION_PATH"
  PREVIOUS_EVALUATION_REPORT="$LATEST_EVALUATION_REPORT_PATH"
fi
```

When `SHOULD_REFINE=false`, Phases 5–8 are skipped (the loop below does not execute) and the pipeline continues at Phase 9.

---

# PHASE 5: Create Next Version Copy

**Purpose:** Copy the source FSD version into the next `v_N` folder. Version creation is owned here — the doc-quality subagents in Phase 6 must NOT create new versions. This phase opens the refinement loop that Phases 6–8 run inside; the loop is closed in Phase 8.

```bash
while [ "$SHOULD_REFINE" = true ]; do
  CREATE_ARGS=(create-next --fsd-root "$FSD_ROOT")
  if [ -n "$SOURCE_VERSION_PATH" ]; then
    CREATE_ARGS+=(--source "$SOURCE_VERSION_PATH")
  fi

  eval_util_output "${CREATE_ARGS[@]}"
  REFINEMENT_ITERATIONS=$((REFINEMENT_ITERATIONS + 1))

  echo "Refinement iteration: $REFINEMENT_ITERATIONS"
  echo "Source FSD version: $SOURCE_VERSION_PATH"
  echo "Copied FSD version: $NEXT_VERSION_PATH"
```

---

# PHASE 6: Document Quality Improvement (Inlined /doc-quality-improve Pipeline)

**Purpose:** Run the full `/doc-quality-improve` pipeline on the copied FSD version, calling doc-quality subagents directly. Use the source version's evaluation report as feedback.

## Step 6.0: Initialize Doc-Quality State

Create `.legacyleap/.agent-state/doc-quality-state.json` for this pass and capture the doc-quality start time (for the Step 6.7 freshness check):

```json
{
  "doc_type": "fsd",
  "documents": {
    "fsd": {
      "path": "$NEXT_FSD_MARKDOWN",
      "exists": true
    }
  },
  "source_code_path": "$LEGACY_CODE_PATH",
  "scan_results_path": "$SCAN_REPORTS_PATH",
  "evaluation_report_feedback": "$PREVIOUS_EVALUATION_REPORT",
  "max_iterations": "$DOC_QUALITY_ITERATIONS",
  "quality_threshold": "$DOC_QUALITY_THRESHOLD",
  "target_word_count": 10000,
  "current_iteration": 0,
  "status": "initialized"
}
```

```bash
DOC_QUALITY_STARTED_AT=$(date +%s)
```

Read `.legacyleap/leap.properties` for service configuration (MERMAID_URL, CHROMA settings).

## Step 6.1: Correctness Analysis

Invoke `doc-correctness-analyzer` using the Task tool with the following prompt:

> Analyze the FSD for correctness against source code, MCM, domain conventions, and diagrams.
>
> **Inputs:**
> - Document path: `$NEXT_FSD_MARKDOWN`
> - Document type: `fsd`
> - Source code path: `$LEGACY_CODE_PATH`
> - Scan results path: `$SCAN_REPORTS_PATH` (contains MCM, BOM report, scan results)
> - Project properties path: `.legacyleap/leap.properties` (contains MERMAID_URL, CHROMA settings)
> - Previous FSD evaluation report: `$PREVIOUS_EVALUATION_REPORT` — use this as targeted feedback; focus your analysis on the weaknesses and gaps the evaluators identified in this report.
>
> Compare document claims against actual source code. Identify:
> - Incorrect technical details (wrong class names, method signatures, API endpoints)
> - Fabricated or hallucinated content not supported by the codebase
> - Missing critical components that exist in code but not in the document
> - Domain terminology errors
> - Broken or missing diagrams
> - Client-presentation issues (internal notes, sensitive info, alarming language)
>
> Write your findings to `.legacyleap/.agent-state/doc-quality-state.json`.

**Validation:**
- Check `.legacyleap/.agent-state/doc-quality-state.json` for the correctness report (issue count and severity levels). It feeds Step 6.2 for the optimizer to fix.

## Step 6.2: Structure Optimization

Invoke `doc-structure-optimizer` using the Task tool with the following prompt:

> Optimize the FSD structure — fix all correctness issues, reduce to 20-25 pages, and ensure client-presentable quality.
>
> **Inputs:**
> - Document path: `$NEXT_FSD_MARKDOWN` — **write the optimized document back to this same path**
> - Document type: `fsd`
> - Correctness report: read issues from `doc-correctness-analyzer` in `.legacyleap/.agent-state/doc-quality-state.json`
> - Source code path: `$LEGACY_CODE_PATH` (for reference when fixing correctness issues)
> - Target word count: `10000`
> - Previous FSD evaluation report: `$PREVIOUS_EVALUATION_REPORT` — use this as targeted feedback to prioritize which improvements matter most.
>
> Apply all corrections from the correctness analysis and optimize the document:
> - Fix all correctness issues identified by `doc-correctness-analyzer`
> - Reduce document to 20-25 pages (~8,000-10,000 words)
> - Remove verbose, repetitive, or filler content
> - Convert lengthy paragraphs to tables and diagrams where possible
> - Eliminate redundant sections that add no value
> - Remove all internal notes, generator disclaimers, and non-client-facing content
> - Ensure consistent formatting and terminology
> - Use full forms: "Technical Specification Documentation" and "Functional Specification Documentation"

**Validation:**
- Document file at `$NEXT_FSD_MARKDOWN` has been updated (mtime check)
- Word count reduced toward target (~10,000 words)
- No structural corruption (headings, tables, code blocks intact)
- No internal notes or generator artifacts remain

## Step 6.3: Diagram Rendering

Invoke `doc-diagram-renderer` using the Task tool with the following prompt:

> Generate beautiful professional diagrams with validated Mermaid syntax, render via the project Mermaid service, and ensure every section has a diagram.
>
> **Inputs:**
> - Document path: `$NEXT_FSD_MARKDOWN`
> - Document type: `fsd`
> - Image output directory: `$(dirname "$NEXT_FSD_MARKDOWN")/mermaid_diagram_images`
> - Source code path: `$LEGACY_CODE_PATH` (for generating accurate diagrams based on actual code structure)
> - Project properties path: `.legacyleap/leap.properties` (contains `MERMAID_URL`, `MERMAID_DIAGRAM_WIDTH`, `MERMAID_DIAGRAM_HEIGHT`, `MERMAID_DIAGRAM_SCALE`, `MERMAID_PNG_DPI`)
>
> Ensure all diagrams are present, beautiful, and correctly rendered:
> - Scan document for broken or missing image references
> - Identify sections that should have diagrams but don't — every H2/H3 section should have a diagram
> - Generate Mermaid code with professional color styling (blues, greens, teals — not gray defaults)
> - Validate Mermaid syntax before rendering — zero tolerance for syntax errors
> - Render via project's Mermaid service (`MERMAID_URL` from `leap.properties`) as primary method
> - Insert rendered images into the document
> - Verify no existing images were broken

**Validation:**
- All image references in the document point to existing files
- No broken `![...]()` links
- New diagrams rendered as PNG files with `.mmd` sources saved alongside
- Diagram colors use the professional palette (not default gray)

## Step 6.4: Quality Verification

Invoke `doc-quality-verifier` using the Task tool with the following prompt:

> Score the FSD quality and determine if it is ready for client delivery at the quality threshold.
>
> **Inputs:**
> - Document path: `$NEXT_FSD_MARKDOWN`
> - Source code path: `$LEGACY_CODE_PATH` (for spot-checking correctness claims)
> - Document type: `fsd`
> - Iteration number: `$CURRENT_DOC_QUALITY_ITERATION`
>
> Assess the document against client delivery standards and score each dimension:
> - Correctness (0-10, weight: 25%): Are technical/functional details accurate?
> - Completeness (0-10, weight: 20%): Are all expected sections present with substance?
> - Readability (0-10, weight: 25%): Is it clear, concise, and well-structured?
> - Visual quality (0-10, weight: 15%): Are diagrams present, beautiful, and properly rendered?
> - Presentation (0-10, weight: 15%): Is it suitable for client presentation? Customer delight?
> - Overall score (0-10): Weighted average of the above.
>
> Write all scores to `.legacyleap/.agent-state/doc-quality-state.json`.

**Validation:** Quality scores written to `.legacyleap/.agent-state/doc-quality-state.json`.

**Iteration Logic** (for the doc-quality inner loop):

```text
current_iteration = current_iteration + 1

If overall_score >= DOC_QUALITY_THRESHOLD:
    Mark as CLIENT_READY → proceed to Step 6.5

If current_iteration >= DOC_QUALITY_ITERATIONS:
    Mark as BEST_EFFORT → proceed to Step 6.5 (log: "Maximum doc-quality iterations reached.")

If overall_score < DOC_QUALITY_THRESHOLD AND current_iteration < DOC_QUALITY_ITERATIONS:
    Log improvement delta from previous iteration
    If no improvement (scores did not increase by >= 0.1):
        Mark as PLATEAU → proceed to Step 6.5
    Else:
        Loop back to Step 6.1 with focused feedback from the quality report
```

## Step 6.5: Document Splitting (Conditional)

**Trigger:** Document exceeds ~10,000 words (~25 pages) AND content cannot be further condensed. **Skip** if the document is within 25 pages.

Invoke `doc-splitter` using the Task tool with the following prompt:

> Split the large FSD into logical sub-documents with an overview document.
>
> **Inputs:**
> - Document path: `$NEXT_FSD_MARKDOWN`
> - Output directory: `$(dirname "$NEXT_FSD_MARKDOWN")/sections`
> - Document type: `fsd`
>
> Break the document into navigable sub-documents:
> - Split into logical sections, each as a separate file in the output directory
> - Transform the main document into an overview that links to each sub-document
> - Never split mid-section — each sub-document must be a complete, self-contained topic
> - Aim for 5,000-10,000 words per sub-document

**Validation:** Sub-documents + overview/index created, no content lost, each sub-document self-contained.

## Step 6.6: .docx Generation

Generate `.docx` via pandoc (same process as `/doc-quality-improve`):

```bash
DOC_DIR=$(dirname "$NEXT_FSD_MARKDOWN")
DOC_NAME=$(basename "$NEXT_FSD_MARKDOWN" .md)
IMAGE_DIR="${DOC_DIR}/mermaid_diagram_images"
OUTPUT_DOCX="${DOC_DIR}/${DOC_NAME}.docx"
TITLE="$(head -5 "$NEXT_FSD_MARKDOWN" | grep '^# ' | sed 's/^# //')"

mkdir -p .legacyleap/templates
if [ ! -f ".legacyleap/templates/reference.docx" ]; then
    pandoc -o .legacyleap/templates/reference.docx --print-default-data-file reference.docx 2>/dev/null || \
    pandoc --print-default-data-file reference.docx > .legacyleap/templates/reference.docx 2>/dev/null
    if [ ! -f ".legacyleap/templates/reference.docx" ] || [ ! -s ".legacyleap/templates/reference.docx" ]; then
        echo "# Template" | pandoc -o .legacyleap/templates/reference.docx \
            --variable geometry:margin=1in --variable mainfont="Calibri" --variable fontsize=11pt
    fi
fi

if [ ! -f ".legacyleap/templates/pagebreak.lua" ]; then
    cat > .legacyleap/templates/pagebreak.lua << 'LUAEOF'
function Header(el)
    if el.level == 2 then
        return {pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'), el}
    end
end
LUAEOF
fi

sed -i 's/  *|/|/g' "$NEXT_FSD_MARKDOWN"
sed -i 's/|  */|/g' "$NEXT_FSD_MARKDOWN"
sed -i 's/!\[\([^]]*\)\](\([^)]*\))/![\1](\2){width=100%}/g' "$NEXT_FSD_MARKDOWN" 2>/dev/null
sed -i 's/^## /\n\\newpage\n\n## /g' "$NEXT_FSD_MARKDOWN"

pandoc "$NEXT_FSD_MARKDOWN" \
  -o "${OUTPUT_DOCX}" \
  --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers+header_attributes \
  --to docx \
  --toc --toc-depth=3 \
  --number-sections \
  --reference-doc=.legacyleap/templates/reference.docx \
  --metadata title="$TITLE" \
  --metadata author="LegacyLeap" \
  --metadata date="$(date +%Y-%m-%d)" \
  --variable geometry:margin=1in \
  --variable mainfont="Calibri" \
  --variable fontsize=11pt \
  --variable linestretch=1.15 \
  --columns=72 \
  --wrap=auto \
  --resource-path=".:${DOC_DIR}:${IMAGE_DIR}" \
  --lua-filter=.legacyleap/templates/pagebreak.lua 2>/dev/null || \
pandoc "$NEXT_FSD_MARKDOWN" \
  -o "${OUTPUT_DOCX}" \
  --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers \
  --to docx \
  --toc --toc-depth=3 \
  --number-sections \
  --metadata title="$TITLE" \
  --metadata author="LegacyLeap" \
  --metadata date="$(date +%Y-%m-%d)" \
  --variable geometry:margin=1in \
  --resource-path=".:${DOC_DIR}:${IMAGE_DIR}"
```

## Step 6.7: Post-Improvement Validation (Artifact Check)

Verify the copied FSD target was actually modified and that no unexpected sibling version was created:

```bash
"$UTIL" assert-updated-file --file "$NEXT_FSD_MARKDOWN" --started-at "$DOC_QUALITY_STARTED_AT" --allow-unchanged

ACTUAL_LATEST=-1
for VERSION_DIR in "$FSD_ROOT"/v_*; do
  [ -d "$VERSION_DIR" ] || continue
  VERSION_NAME=$(basename "$VERSION_DIR")
  case "$VERSION_NAME" in
    v_[0-9]*) VERSION_NUMBER="${VERSION_NAME#v_}" ;;
    *) continue ;;
  esac
  if [ "$VERSION_NUMBER" -gt "$ACTUAL_LATEST" ]; then
    ACTUAL_LATEST="$VERSION_NUMBER"
  fi
done

if [ "$ACTUAL_LATEST" != "$NEXT_VERSION_NUMBER" ]; then
  echo "FATAL: A doc-quality subagent created an unexpected sibling version folder v_$ACTUAL_LATEST."
  echo "Version creation is owned by this command."
  exit 1
fi
```

---

# PHASE 7: Refined FSD Evaluation (Inlined /fsd-evaluate Pipeline)

**Purpose:** Run the full FSD evaluation pipeline on the improved copied FSD version. Same structure as Phase 3, but targeting the refined version at `$NEXT_FSD_MARKDOWN` and writing to `$EVALUATION_DIR`.

## Step 7.0: Re-initialize Evaluation State

Write a fresh `.legacyleap/.agent-state/fsd-evaluation-state.json` targeting `$NEXT_FSD_MARKDOWN`, set `OUTPUT_DIR`, and capture the evaluation start time:

```bash
export OUTPUT_DIR="$EVALUATION_DIR"
REFINED_EVALUATION_STARTED_AT=$(date +%s)
```

## Step 7.1: Build or Reuse Project Digest

Invoke `project-digest-builder` using the Task tool with the following prompt:

> Build a project digest from the MCM. If an existing cached digest at `.legacyleap/.agent-state/project-digest.json` matches the current MCM SHA-256 hash, reuse it.
>
> **Inputs:**
> - MCM path: `$MCM_PATH`
> - Project path: `$PROJECT_PATH`
> - Output path: `.legacyleap/.agent-state/project-digest.json`

Validate the digest using the same checks as Step 3.2.

## Step 7.2: Parallel Evaluators (5 Dimensions)

Launch all 5 evaluator subagents **in parallel** using the Task tool. All target the **refined** FSD at `$NEXT_FSD_MARKDOWN`. Wait for all 5 to complete before proceeding.

### Task 1: Coverage Evaluation

Invoke `fsd-coverage-evaluator` using the Task tool with the following prompt:

> Evaluate FSD coverage against expected sections and MCM inventory.
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH` (for targeted lookups if needed)
>
> Check the FSD structure against the expected section taxonomy (mandatory and recommended sections). Cross-reference MCM-derived inventories (entities, forms, integrations, enums) against what the FSD documents. Write coverage findings (score, missing_sections, coverage_percentage) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.coverage`.

### Task 2: Correctness Evaluation

Invoke `fsd-correctness-evaluator` using the Task tool with the following prompt:

> Spot-check FSD claims against MCM data and optionally legacy source code.
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH`
> - Legacy code path: `$LEGACY_CODE_PATH` (if available, for source-level spot checks)
>
> Verify 20-30 specific claims from the FSD against MCM data: entity fields, role/permission values, integration names, form names, business rule triggers, data flow descriptions. Mark each claim as SUPPORTED, UNSUPPORTED, or FALSE with evidence. Write correctness findings (score, claims[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.correctness`.

### Task 3: Depth Evaluation

Invoke `fsd-depth-evaluator` using the Task tool with the following prompt:

> Flag placeholder and vague content in the FSD.
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
>
> Scan the FSD for empty or near-empty sections, placeholder text (TBD, TODO, N/A), vague/generic content, journeys without steps, business rules without trigger conditions, decision points without outcomes, data entities without field descriptions. Spawn subagents for extensive sections with many subsections. Write depth findings (score, vague_sections[], placeholder_count) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.depth`.

### Task 4: Domain Alignment Evaluation

Invoke `fsd-domain-evaluator` using the Task tool with the following prompt:

> Validate FSD-style discipline and terminology consistency.
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
> - Project digest path: `.legacyleap/.agent-state/project-digest.json`
>
> Check for TSD leakage (SQL queries, class names, method signatures, code snippets, API endpoints), terminology consistency (domain terms used uniformly), and audience appropriateness (written for business stakeholders, not developers). Write domain findings (score, tsd_leakage[], terminology_issues[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.domain`.

### Task 5: Diagram Evaluation

Invoke `fsd-diagram-evaluator` using the Task tool with the following prompt:

> Verify diagram references and coverage in the FSD.
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
>
> Check all `![...]()` image references resolve to existing files. Identify sections that should have diagrams but don't (Business Overview, User Journeys, Business Workflows, Data Flow, Decision Points, Integration Points). Write diagram findings (score, broken_references[], missing_diagrams[]) to `.legacyleap/.agent-state/fsd-evaluation-state.json` under `evaluations.diagrams`.

Wait for all 5 tasks to complete before proceeding to Step 7.3.

## Step 7.3: Readability Score

Compute the readability score directly using the same logic as Step 3.4, but targeting `$NEXT_FSD_MARKDOWN`.

## Step 7.4: Weighted Overall Score

Compute the weighted score from all 6 dimensions using the same logic as Step 3.5.

## Step 7.5: Improvement Recommender

Invoke `fsd-improvement-recommender` using the Task tool with the following prompt:

> Synthesize all evaluation findings and draft proposed additions for the refined FSD.
>
> **Environment:** `OUTPUT_DIR=$EVALUATION_DIR`
>
> **Inputs:**
> - FSD path: `$NEXT_FSD_MARKDOWN`
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (contains all evaluator findings)
> - Project digest: `.legacyleap/.agent-state/project-digest.json`
> - MCM path: `$MCM_PATH` (for drafting new content)
>
> Read findings from all 5 evaluators plus readability. Synthesize into ranked recommendations (priority, effort, impact). Draft proposed Markdown content for missing or weak sections. Write recommendations to the state file and create `$OUTPUT_DIR/fsd-proposed-additions.md` with the draft content.

## Step 7.6: Quality Checker

Invoke `fsd-evaluation-quality-checker` using the Task tool with the following prompt:

> Review and validate the evaluation scorecard for consistency, accuracy, and evidence justification.
>
> **Inputs:**
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (with all evaluator findings and scores)
> - FSD path: `$NEXT_FSD_MARKDOWN` (for spot-checking claims)
> - Project digest: `.legacyleap/.agent-state/project-digest.json`
>
> Perform self-reflection on the evaluation scorecard: review each dimension's score against its collected evidence, detect score-evidence mismatches, check for hallucinated findings, validate scoring consistency across dimensions. Adjust scores if justified by evidence. Update `.legacyleap/.agent-state/fsd-evaluation-state.json` with quality-checked scores and quality check metadata.

## Step 7.7: Reporter

Invoke `fsd-evaluation-reporter` using the Task tool with the following prompt:

> Generate the final FSD evaluation report for the refined version.
>
> **Environment:** `OUTPUT_DIR=$EVALUATION_DIR`
>
> **Inputs:**
> - State file: `.legacyleap/.agent-state/fsd-evaluation-state.json` (with all findings and quality-checked scores)
> - FSD path: `$NEXT_FSD_MARKDOWN` (for metadata — word count, sections)
> - MCM path: `$MCM_PATH` (for project context)
>
> Generate `$OUTPUT_DIR/fsd-evaluation-report.md` with: executive summary and overall score, detailed scorecard across 6 dimensions with justifications, top 10 recommendations (prioritized), top 10 missing items, top 10 weakest sections, claim verification table, and next steps.

## Step 7.8: Consolidate and Verify Artifacts, Parse Score

```bash
cp .legacyleap/.agent-state/fsd-evaluation-state.json "$EVALUATION_DIR/"
cp .legacyleap/.agent-state/project-digest.json "$EVALUATION_DIR/" 2>/dev/null || true

"$UTIL" normalize-report --output-dir "$EVALUATION_DIR" --report "$EVALUATION_REPORT_PATH"
"$UTIL" assert-fresh-evaluation \
  --report "$EVALUATION_REPORT_PATH" \
  --state "$EVALUATION_STATE_PATH" \
  --started-at "$REFINED_EVALUATION_STARTED_AT"

SCORE=$("$UTIL" parse-score --report "$EVALUATION_REPORT_PATH" --state "$EVALUATION_STATE_PATH")
echo "Evaluation score for $NEXT_VERSION: $SCORE/10"
```

---

# PHASE 8: Decision Gate & Loop

Evaluate the refined FSD score and decide whether to stop or loop. This phase closes the refinement loop opened in Phase 5.

**Case 1 — Score meets threshold:** `SCORE >= THRESHOLD` → `FINAL_STATUS = "CLIENT_READY"` and stop.

**Case 2 — Max iterations reached:** `REFINEMENT_ITERATIONS >= MAX_REFINEMENT_ITERATIONS` → `FINAL_STATUS = "BEST_EFFORT"` and stop.

**Case 3 — Score below threshold and iterations remain:** loop back to Phase 5. Create a new `v_N+1` copy from the current refined version (`$NEXT_VERSION_PATH` becomes the new source), then run **ALL** of Phase 6 (every doc-quality subagent) and **ALL** of Phase 7 (every evaluation subagent) again, passing the current evaluation report as `$PREVIOUS_EVALUATION_REPORT`. **Do NOT skip any steps on subsequent iterations.**

```bash
  if "$UTIL" score-ok --score "$SCORE" --threshold "$THRESHOLD"; then
    FINAL_FSD_VERSION="$NEXT_VERSION_PATH"
    FINAL_FSD_MARKDOWN="$NEXT_FSD_MARKDOWN"
    FINAL_EVALUATION_SCORE="$SCORE"
    FINAL_EVALUATION_REPORT="$EVALUATION_REPORT_PATH"
    FINAL_STATUS="CLIENT_READY"
    break
  fi

  if [ "$REFINEMENT_ITERATIONS" -ge "$MAX_REFINEMENT_ITERATIONS" ]; then
    FINAL_FSD_VERSION="$NEXT_VERSION_PATH"
    FINAL_FSD_MARKDOWN="$NEXT_FSD_MARKDOWN"
    FINAL_EVALUATION_SCORE="$SCORE"
    FINAL_EVALUATION_REPORT="$EVALUATION_REPORT_PATH"
    FINAL_STATUS="BEST_EFFORT"
    break
  fi

  # Score below threshold and iterations remain — loop back to Phase 5
  SOURCE_VERSION_PATH="$NEXT_VERSION_PATH"
  PREVIOUS_EVALUATION_REPORT="$EVALUATION_REPORT_PATH"
  echo "Score $SCORE < threshold $THRESHOLD — looping: Phase 5 -> Phase 6 (ALL steps) -> Phase 7 (ALL steps) -> Phase 8"
done
```

Update state: `refinement.status = "completed"`, `refinement.iterations = $REFINEMENT_ITERATIONS`.

---

# PHASE 9: Package Best FSD as .docx

**Purpose:** Convert the best FSD version to `.docx`. The "best" version is the one recorded as final by the decision gates (`$FINAL_FSD_MARKDOWN`), falling back to the latest FSD version on disk.

```bash
echo "📦 Phase 9: Converting the best FSD version to .docx..."

BEST_FSD_MD="${FINAL_FSD_MARKDOWN:-}"
if [ -z "$BEST_FSD_MD" ] || [ ! -f "$BEST_FSD_MD" ]; then
    eval_util_output latest
    BEST_FSD_MD="$LATEST_FSD_MARKDOWN"
fi

if [ ! -f "$BEST_FSD_MD" ]; then
    echo "❌ Could not locate the best FSD markdown to convert"
    exit 1
fi

FSD_DIR=$(dirname "$BEST_FSD_MD")
FSD_DOCX="${FSD_DIR}/Latest_fsd.docx"
FSD_IMG_DIR="${FSD_DIR}/mermaid_diagram_images"
echo "   Best FSD markdown: $BEST_FSD_MD"

if command -v pandoc &> /dev/null; then
    mkdir -p .legacyleap/templates
    if [ ! -f ".legacyleap/templates/reference.docx" ]; then
        pandoc -o .legacyleap/templates/reference.docx --print-default-data-file reference.docx 2>/dev/null || \
        pandoc --print-default-data-file reference.docx > .legacyleap/templates/reference.docx 2>/dev/null || true
    fi
    if [ ! -f ".legacyleap/templates/pagebreak.lua" ]; then
        cat > .legacyleap/templates/pagebreak.lua << 'LUAEOF'
function Header(el)
    if el.level == 2 then
        return {pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'), el}
    end
end
LUAEOF
    fi

    pandoc "$BEST_FSD_MD" -o "$FSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers+header_attributes \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --reference-doc=.legacyleap/templates/reference.docx \
        --metadata title="Functional Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --resource-path=".:${FSD_DIR}:${FSD_IMG_DIR}" \
        --lua-filter=.legacyleap/templates/pagebreak.lua 2>/dev/null || \
    pandoc "$BEST_FSD_MD" -o "$FSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --metadata title="Functional Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --resource-path=".:${FSD_DIR}:${FSD_IMG_DIR}"

    if [ -f "$FSD_DOCX" ]; then
        echo "✅ Best FSD .docx: $FSD_DOCX"
    else
        echo "⚠️ pandoc ran but no .docx was produced — keeping markdown only"
    fi
else
    echo "⚠️ pandoc not available — .docx conversion skipped"
fi
```

Update state: `fsd_docx.status = "completed"` (or `"skipped"` when pandoc is unavailable).

---

# Final Report

Print exactly:

```text
Completion status: <CLIENT_READY|BEST_EFFORT>
Final FSD version: <FINAL_FSD_VERSION>
Final evaluation score: <FINAL_EVALUATION_SCORE>/10
Refinement iterations performed: <REFINEMENT_ITERATIONS>
Final evaluation report: <FINAL_EVALUATION_REPORT>
Best FSD .docx: <FSD_DOCX>
```

`Refinement iterations performed` counts only copied-version improvement attempts. If the baseline latest FSD already met the threshold, this value is `0`.

```
✅ FSD GENERATE COMPLETE

Project: <name>
Duration: <total_time>
Environment: legacyleap (conda)

Phase Results:
  1a. MCM Generation:    ✅ / ⏭️  scan_assessment_reports/meta_cognitive_model.json
  1b. MCM Visualization: ✅       scan_assessment_reports/mcm_visualization.html
  2.  FSD Generation:    ✅ / ⏭️  comprehend/functional_doc/v_N/Latest_FSD_Document/Latest_fsd.md
  3.  Baseline Eval:     ✅       <baseline score>/10
  4-8. Refinement Loop:  ✅       <iterations> iteration(s), final <score>/10
  9.  Best FSD .docx:    ✅       <best-version>/Latest_FSD_Document/Latest_fsd.docx
```

---

## Error Handling

| Failure | Recovery |
|---------|----------|
| Conda activation fails | STOP — environment required |
| MCM scan job `STATUS=FAILED` | STOP — MCM is required for everything downstream; inspect `take-leap-job.sh logs mcm-scan` |
| MCM/FSD job `STATUS=STALLED` | Inspect `logs`; relaunch only with `launch <job> --force` if genuinely hung. Never wait indefinitely |
| MCM/FSD job `STATUS=DIED` | Process vanished without an exit code; inspect `logs`, then `launch <job> --force` |
| Long job `STATUS=RUNNING` | Not a failure — keep calling `await` (≤10 min each). Never relaunch a RUNNING/DONE job |
| Meta-layer visualization fails | STOP — visualization is a required Phase 1 deliverable |
| FSD generation job `STATUS=FAILED` | STOP — cannot refine without an FSD; inspect `take-leap-job.sh logs fsd` |
| `assert-fresh-evaluation` fails | STOP — an evaluation subagent did not produce fresh artifacts; do not parse or trust the score |
| A doc-quality subagent creates a new `v_N` folder | STOP — version creation is owned by this command |
| `.docx` conversion fails | Keep the FSD markdown, log a warning |

## Invariants

- Evaluate the latest existing FSD version before creating any refinement copy.
- Never modify an existing source FSD version in place — every refinement attempt operates on a newly copied `v_N` folder.
- Version creation belongs only to this command (via `fsd-refine-utils.sh create-next`); doc-quality subagents improve the provided copied folder in place only.
- Evaluation reports live in deterministic paths owned by `fsd-refine-utils.sh`; reject stale reports (`assert-fresh-evaluation`) before parsing a score.
- Preserve all previous FSD versions and evaluation reports.
- Do NOT call `fsd-evaluation-orchestrator`, `doc-quality-orchestrator`, or `fsd-refinement-orchestrator` — call the leaf subagents directly.

## Commands and Scripts Used

| Command / Script | Phase | Purpose |
|------------------|-------|---------|
| `bash .legacyleap/scripts/leap-os/code-intelligence/check-mcm-exists.sh` | 1 | Decides whether a valid MCM already exists so the scan can be skipped |
| `bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh` | 1, 2 | Launches the long MCM/FSD wrappers detached and idempotently; `await` polls to `DONE` without a blocking foreground call |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh` | 1 | Runs the `take-leap scan --latest --enable-raganything-ingestion --enable-vector-ingestion` wrapper and verifies `meta_cognitive_model.json` (launched via `take-leap-job.sh`) |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh` | 1 | Runs the `take-leap meta-layer-visualization` wrapper and verifies `mcm_visualization.html` |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh` | 2 | Runs the `take-leap functional-doc --ingest_vectorstore` wrapper and verifies `Latest_fsd.md` (launched via `take-leap-job.sh`) |
| `bash .legacyleap/scripts/leap-os/fsd-refine/fsd-refine-utils.sh` | 2-8 | `latest` / `create-next` / `normalize-report` / `assert-fresh-evaluation` / `assert-updated-file` / `parse-score` / `score-ok` |
| `project-digest-builder` + 5 evaluators + recommender + quality-checker + reporter | 3, 7 | Inlined `/fsd-evaluate` pipeline |
| `doc-correctness-analyzer` + `doc-structure-optimizer` + `doc-diagram-renderer` + `doc-quality-verifier` + `doc-splitter` | 6 | Inlined `/doc-quality-improve` pipeline |
| `pandoc` | 6, 9 | Converts FSD markdown to `.docx` |
