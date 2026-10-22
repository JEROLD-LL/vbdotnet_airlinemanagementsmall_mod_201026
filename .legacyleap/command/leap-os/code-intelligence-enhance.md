---
description: "Single command: activates env → scans & enhances MCM → improves MCM (batch validate & correct) → runs tech assessment → generates meta-layer visualization → FSD→TSD sequential → versions originals → quality improvement (max 3 iters, 95%) → packages .docx → Application Overview → Modernization Recommendations → Dependency Mapping → Code Modernization (actual code transforms, with per-recommendation confirmation) → Impact Assessment → dashboard refresh"
agent: code-intelligence-orchestrator
---

# Code Intelligence Enhancement & Comprehension Documents

This is the **single master command** that orchestrates the entire code intelligence and comprehension pipeline end-to-end. It internally calls sub-commands (which can also be run independently) in the correct sequence.

**Customer delight is the ultimate goal.** All deliverables carry the **LegacyLeap** watermark and branding, and should make clients feel confident about the modernization journey.

## Pipeline Overview

```
Phase 0: Environment Setup & Project Discovery
    ├─ conda activate legacyleap
    └─ Read .legacyleap/metadata.json + leap.properties
    ↓
Phase 1: MCM Generation, Verification, Enhancement & Improvement
    ├─ bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh   (wraps take-leap scan --latest)
    ├─ Verify MCM correctness against source code
    ├─ Enhance MCM with code intelligence (enrich empty fields)
    └─ Improve MCM accuracy (validate & correct all fields)
    ↓
Phase 1b: Technical Debt Assessment
    ├─ Reuse the technical debt assessment command with the improved MCM
    ├─ Reuse saved custom_rules.json if present
    └─ Otherwise default to Bug, Code_Smell, Cognitive_complexity
    ↓
Phase 1c: Meta-Layer Visualization
    └─ bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh (wraps take-leap meta-layer-visualization)
    ↓
Phase 2: Comprehension Document Generation (Sequential: FSD → TSD)
    ├─ bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh (wraps take-leap functional-doc --latest --ingest_vectorstore)
    ├─ Wait for FSD completion
    ├─ bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh  (wraps take-leap technical-doc --latest --ingest_vectorstore)
    └─ Wait for TSD completion
    ↓
Phase 2b: Version & Preserve Originals
    ├─ Copy originals to new version folder (v_N → v_N+1)
    └─ All subsequent edits happen on the COPIES only
    ↓
Phase 3: Document Quality Improvement (max 3 iterations)
    ├─ Correctness analysis (vs source code + MCM + domain)
    ├─ Structure optimization (20-25 pages target)
    ├─ Diagram rendering (beautiful professional diagrams)
    ├─ Quality scoring → iterate until ≥ 90% or 3 iterations
    └─ /doc-quality-improve                             (sub-command)
    ↓
Phase 4: Document Packaging with LegacyLeap Branding
    ├─ Generate .docx versions with TOC, section numbers
    └─ Package as client-ready deliverables
    ↓
Phase 5: Application Overview (10-15 pages)
    └─ /application-overview --concise                  (sub-command)
    ↓
Phase 5b: Modernization Recommendations (5-6 pages)
    └─ Architecture options, tech stack upgrades, pros/cons
    ↓
Phase 5c: Dependency Mapping
    └─ Dependency graph, version health, CVE analysis
    ↓
Phase 5d: Modernization Execution (if approved)
    └─ Version upgrades, security fixes, code transforms
    ↓
Phase 5e: Impact Assessment
    └─ Before/after comparison, value delivered, ROI
    ↓
Phase 5f: Dashboard Refresh
    └─ Regenerate interactive dashboard HTML/JS from sheet JSONs
    ↓
Phase 6: Final Report & Summary
```

## Sub-Commands (each callable independently)

| Sub-Command | Can Run Alone? | What It Does |
|-------------|---------------|-------------|
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh` | ✅ Yes | Wrapper around `take-leap scan --latest`; generates MCM from source code |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh` | ✅ Yes | Wrapper around `take-leap meta-layer-visualization`; generates standalone MCM visualization HTML |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh` | ✅ Yes | Wrapper around `take-leap functional-doc --latest --ingest_vectorstore`; generates FSD |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh` | ✅ Yes | Wrapper around `take-leap technical-doc --latest --ingest_vectorstore`; generates TSD |
| `/tech-assessment` | ✅ Yes | Runs the standalone technical debt assessment flow; use `--non-interactive` when invoked from parent pipelines |
| `/doc-quality-improve` | ✅ Yes | Improves document quality (correctness, diagrams, structure) |
| `/application-overview` | ✅ Yes | Generates Application Overview report |
| `/application-overview --concise` | ✅ Yes | Generates concise 10-15 page overview |

> **Why scripts instead of inline `take-leap` commands?** The wrappers in `profiles/default/scripts/code-intelligence/` (deployed to `.legacyleap/scripts/leap-os/code-intelligence/`) enforce that the `take-leap` CLI is executed directly in the calling shell, validate prerequisites (conda env, MCM presence), stream output to a log file, and verify the expected artifact was produced. Agents MUST call these scripts via the `Bash` tool — never rewrite the underlying `take-leap` command inline or delegate it to a sub-agent.

## Usage

```bash
# Full pipeline (recommended) — runs everything end-to-end
/code-intelligence-enhance

# Skip MCM scan (MCM already exists and is recent)
/code-intelligence-enhance --skip-scan

# Skip MCM enhancement (MCM is already high quality)
/code-intelligence-enhance --skip-mcm-enhance

# Skip MCM improvement (MCM is already validated and accurate)
/code-intelligence-enhance --skip-mcm-improve

# Skip technical debt assessment
/code-intelligence-enhance --skip-tech-assessment

# Skip .docx packaging
/code-intelligence-enhance --skip-packaging

# Generate concise overview (10-15 pages) instead of detailed
/code-intelligence-enhance --overview-mode concise

# Control quality improvement iterations (default: 3)
/code-intelligence-enhance --max-quality-iterations 2
```

## LegacyLeap Branding

All generated documents include:
- **LegacyLeap logo** in the header
- **"Powered by LegacyLeap"** footer on every page
- **Watermark** in .docx files
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

# Parse CLI flags (use while + shift so flags with values work; orchestrator passes "$@")
SKIP_SCAN=false
SKIP_MCM_ENHANCE=false
SKIP_MCM_IMPROVE=false
SKIP_TECH_ASSESSMENT=false
SKIP_PACKAGING=false
SKIP_QUALITY=false
OVERVIEW_MODE="detailed"
MAX_QUALITY_ITERATIONS=3
QUALITY_THRESHOLD=9.5

while [ $# -gt 0 ]; do
    case $1 in
        --skip-scan) SKIP_SCAN=true; shift ;;
        --skip-mcm-enhance) SKIP_MCM_ENHANCE=true; shift ;;
        --skip-mcm-improve) SKIP_MCM_IMPROVE=true; shift ;;
        --skip-tech-assessment) SKIP_TECH_ASSESSMENT=true; shift ;;
        --skip-packaging) SKIP_PACKAGING=true; shift ;;
        --skip-quality) SKIP_QUALITY=true; shift ;;
        --overview-mode)
            shift
            OVERVIEW_MODE="${1:-detailed}"
            shift
            ;;
        --max-quality-iterations)
            shift
            MAX_QUALITY_ITERATIONS="${1:-3}"
            shift
            ;;
        *) shift ;;
    esac
done
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

python3 -c "
import json, os
with open('$METADATA_FILE') as f:
    meta = json.load(f)

paths = {
    'PROJECT_BASE': meta.get('project_path', ''),
    'COMPREHEND_PATH': meta.get('comprehend', ''),
    'SCAN_REPORTS_PATH': meta.get('scan_assessment_reports', ''),
    'LEGACY_CODE_PATH': meta.get('legacy_code', ''),
}

print(f'Project: {meta.get(\"name\", \"Unknown\")}')
print(f'Backend: {meta.get(\"legacy_backend\", \"\")} / {meta.get(\"legacy_framework\", \"\")}')
print()
for key, val in paths.items():
    exists = '✅' if val and os.path.isdir(val) else '❌'
    print(f'{exists} {key}={val}')
"

PROJECT_BASE=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['project_path'])")
COMPREHEND_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['comprehend'])")
SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['scan_assessment_reports'])")
LEGACY_CODE_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_code',''))")
LEGACY_PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_project_name',''))")
PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('name','Unknown'))")
PROJECT_ID=$(python3 -c "import json; m=json.load(open('$METADATA_FILE')); print(m.get('project_id') or m.get('name',''))")
TECHNOLOGY=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacyleap_plugin',''))")
FRAMEWORK=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_framework',''))")
APP_TYPE=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_application_type',''))")
ARCHITECTURE=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('current_architecture',''))")
LEGACY_FRONTEND=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_frontend',''))")
LEGACY_BACKEND=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_backend',''))")

# Read leap.properties for service config
if [ -f "$PROPERTIES_FILE" ]; then
    MERMAID_URL=$(grep '^MERMAID_URL=' "$PROPERTIES_FILE" | cut -d= -f2 | tr -d ' ')
    DB_URL=$(grep '^DB_URL=' "$PROPERTIES_FILE" | cut -d= -f2- | tr -d ' ')
    DB_USERNAME=$(grep '^DB_USERNAME=' "$PROPERTIES_FILE" | cut -d= -f2 | tr -d ' ')
    DB_PASSWORD=$(grep '^DB_PASSWORD=' "$PROPERTIES_FILE" | cut -d= -f2 | tr -d ' ')
    DB_NAME=$(grep '^DB_NAME=' "$PROPERTIES_FILE" | cut -d= -f2 | tr -d ' ')
    CHROMA_HOST=$(grep '^CHROMA_HOST=' "$PROPERTIES_FILE" | cut -d= -f2 | tr -d ' ')
    echo "✅ Mermaid service: $MERMAID_URL"
    [ -n "$DB_URL" ] && echo "✅ Neo4j: $DB_URL (database: ${DB_NAME:-legacyleap})" || echo "ℹ️  Neo4j: not configured (using file-based MCM)"
    [ -n "$CHROMA_HOST" ] && echo "✅ Chroma: $CHROMA_HOST"
fi

# Start execution timer
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

SRC_COUNT=$(find "$LEGACY_SRC_ROOT" -type f \( -name "*.java" -o -name "*.cs" -o -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.go" -o -name "*.rb" -o -name "*.php" -o -name "*.kt" -o -name "*.scala" -o -name "*.cbl" -o -name "*.vb" \) | grep -v "/.git/" | grep -v "/node_modules/" | wc -l | tr -d ' ')
echo "✅ Legacy source: $LEGACY_SRC_ROOT ($SRC_COUNT source files)"

mkdir -p "${PROJECT_BASE}/.legacyleap/.agent-state"
mkdir -p "${PROJECT_BASE}/.legacyleap/reports"
```

## Step 4: Copy LegacyLeap Logo to Project

```bash
LOGO_SRC="$(dirname $(dirname $(dirname $(dirname "$0"))))/assets/legacyleap-logo.png"
LOGO_DEST="${PROJECT_BASE}/.legacyleap/assets/legacyleap-logo.png"

mkdir -p "${PROJECT_BASE}/.legacyleap/assets"
if [ -f "$LOGO_SRC" ]; then
    cp "$LOGO_SRC" "$LOGO_DEST"
elif [ -f "profiles/default/assets/legacyleap-logo.png" ]; then
    cp "profiles/default/assets/legacyleap-logo.png" "$LOGO_DEST"
fi
echo "✅ LegacyLeap logo: $LOGO_DEST"
```

## Step 5: Create Clean Output Folder Structure

Every pipeline run produces outputs in clearly separated, versioned directories. This step ensures the structure exists.

```bash
# Determine current run number (increments each run)
RUN_LOG="${PROJECT_BASE}/.legacyleap/.agent-state/run_counter.txt"
CURRENT_RUN=$(cat "$RUN_LOG" 2>/dev/null || echo "0")
NEXT_RUN=$((CURRENT_RUN + 1))
echo "$NEXT_RUN" > "$RUN_LOG"

echo "📂 Pipeline run #${NEXT_RUN} — Creating output structure..."

# === Output Directory Map ===
#
# $PROJECT_BASE/
# ├── .legacyleap/
# │   ├── metadata.json                          (project config — READ ONLY)
# │   ├── leap.properties                        (service config — READ ONLY)
# │   ├── assets/legacyleap-logo.png             (branding)
# │   ├── templates/reference.docx               (pandoc template)
# │   ├── templates/pagebreak.lua                (pandoc lua filter)
# │   ├── .agent-state/
# │   │   ├── code-intelligence-state.json       (pipeline state)
# │   │   ├── doc-quality-state.json             (quality scores)
# │   │   └── run_counter.txt                    (run number)
# │   └── reports/
# │       ├── code-intelligence-report.md        (final pipeline report)
# │       └── mcm_enhancement_report.md          (MCM enhancement log)
# │
# ├── scan_assessment_reports/                    (MCM — platform-managed)
# │   ├── meta_cognitive_model.json              (original MCM)
# │   └── meta_cognitive_model_enhanced.json     (enhanced MCM)
# │   ├── mcm_visualization.html                 (standalone MCM visualization)
# │   ├── mcm_assessment/
# │   │   └── file_to_mcm_mapping.json           (tech assessment file ↔ MCM mapping)
# │   └── tech_assessment/
# │       ├── Source_code_JSONs/
# │       ├── sheet1.json ... sheet9.json
# │       ├── technical_assessment_report.xlsx
# │       └── technical_assessment_dashboard.html
# │
# ├── comprehend/
# │   ├── functional_doc/
# │   │   ├── v_0/Latest_FSD_Document/           (original — NEVER modified)
# │   │   └── v_1/Latest_FSD_Document/           (enhanced version)
# │   │       ├── Latest_fsd.md
# │   │       ├── Latest_fsd.docx
# │   │       └── mermaid_diagram_images/
# │   └── technical_doc/
# │       ├── v_0/Latest_TSD_Document/           (original — NEVER modified)
# │       └── v_1/Latest_TSD_Document/           (enhanced version)
# │           ├── Latest_tsd.md
# │           ├── Latest_tsd.docx
# │           └── mermaid_diagram_images/
# │
# ├── application-overview/                       (Application Overview output)
# │   ├── APPLICATION_OVERVIEW.md
# │   ├── APPLICATION_OVERVIEW.docx
# │   └── mermaid_diagram_images/
# │
# └── modernization/                              (All modernization outputs — versioned)
#     └── v_1/
#         ├── recommendations/
#         │   ├── MODERNIZATION_RECOMMENDATIONS.md
#         │   ├── MODERNIZATION_RECOMMENDATIONS.docx
#         │   └── mermaid_diagram_images/
#         ├── dependencies/
#         │   ├── DEPENDENCY_MAP.md
#         │   └── DEPENDENCY_MAP.docx
#         ├── execution/
#         │   ├── MODERNIZATION_EXECUTION_REPORT.md
#         │   ├── MODERNIZATION_EXECUTION_REPORT.docx
#         │   ├── change_manifest.json
#         │   └── modernized_code/
#         ├── impact/
#         │   ├── MODERNIZATION_IMPACT_ASSESSMENT.md
#         │   └── MODERNIZATION_IMPACT_ASSESSMENT.docx
#         └── mermaid_diagram_images/

# Create directories
mkdir -p "${PROJECT_BASE}/.legacyleap/templates"
mkdir -p "${PROJECT_BASE}/.legacyleap/.agent-state"
mkdir -p "${PROJECT_BASE}/.legacyleap/reports"
mkdir -p "${PROJECT_BASE}/application-overview/mermaid_diagram_images"
mkdir -p "${SCAN_REPORTS_PATH}/mcm_assessment"
mkdir -p "${SCAN_REPORTS_PATH}/tech_assessment/Source_code_JSONs"

echo "✅ Output folder structure ready"
```

## Step 6: Initialize Pipeline State

```json
{
  "pipeline": "code-intelligence-enhance",
  "project": "<PROJECT_NAME>",
  "started_at": "<timestamp>",
  "run_number": "<NEXT_RUN>",
  "phases": {
    "mcm_scan": { "status": "pending" },
    "mcm_enhance": { "status": "pending" },
    "mcm_improve": { "status": "pending" },
    "tech_assessment": { "status": "pending" },
    "meta_layer_visualization": { "status": "pending" },
    "comprehend_gen": { "status": "pending" },
    "versioning": { "status": "pending", "fsd_original": null, "fsd_enhanced": null, "tsd_original": null, "tsd_enhanced": null },
    "doc_quality": { "status": "pending" },
    "document_packaging": { "status": "pending" },
    "app_overview": { "status": "pending" },
    "recommendations": { "status": "pending" },
    "dependency_mapping": { "status": "pending" },
    "modernization_execution": { "status": "pending" },
    "impact_assessment": { "status": "pending" },
    "dashboard_generation": { "status": "pending" }
  },
  "current_phase": "mcm_scan",
  "branding": {
    "logo": ".legacyleap/assets/legacyleap-logo.png",
    "watermark": "LegacyLeap",
    "footer": "Powered by LegacyLeap"
  },
  "infrastructure": {
    "mcm_source": "neo4j | file",
    "db_url": "<DB_URL from leap.properties or null>",
    "mermaid_url": "<from leap.properties>",
    "chroma_host": "<from leap.properties>"
  },
  "performance": {
    "started_at": "<timestamp>",
    "phase_timings": {}
  }
}
```

Write to `.legacyleap/.agent-state/code-intelligence-state.json`.

```
🚀 CODE INTELLIGENCE ENHANCEMENT INITIALIZED

Project: <name>
Source: <src_count> files
Environment: legacyleap (conda)
Branding: LegacyLeap watermark enabled

Infrastructure:
  MCM Source: Neo4j ($DB_URL) / File fallback
  Mermaid: $MERMAID_URL

Pipeline:
  1.  MCM Scan & Generation             ⏳ Pending
  2.  MCM Verification & Enhancement    ⏳ Pending  (Neo4j paginated / file)
  2b. MCM Improvement (Validate & Fix)  ⏳ Pending  (batch 10-20, all fields)
  2c. Technical Debt Assessment         ⏳ Pending  (reuse existing rules or default 3 issue types)
  2d. Meta-Layer Visualization          ⏳ Pending  (standalone HTML from the active MCM)
  3.  Comprehension Doc Generation      ⏳ Pending  (FSD first, then TSD)
  3b. Version & Preserve Originals      ⏳ Pending  (v_N → v_N+1, never modify originals)
  4.  Document Quality Improvement      ⏳ Pending  (max 3 iterations → 95%)
  5.  Document Packaging & Branding     ⏳ Pending
  6.  Application Overview              ⏳ Pending  (10-15 pages)
  7.  Modernization Recommendations     ⏳ Pending  (5-6 pages)
  8.  Dependency Mapping                ⏳ Pending
  9.  Modernization Execution           ⏳ Pending  (if approved)
  10. Impact Assessment                 ⏳ Pending  (before/after, ROI)
  10b. Dashboard Refresh               ⏳ Pending  (HTML + JS regenerated from sheet JSONs)

Starting Phase 1...
```

---

# PHASE 1: MCM Generation, Verification, Enhancement & Improvement

**Purpose:** Generate (or refresh) the MCM from source code, verify its correctness, enrich it with code intelligence (empty fields), then validate and correct all fields in batches. Better MCM = better comprehension documents from the start.

## Step 1: Generate MCM via Scan

**CRITICAL: EXECUTE THE PREDEFINED SCRIPT DIRECTLY — DO NOT DELEGATE**

This step must execute the predefined wrapper script `.legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh` in the current shell session via the `Bash` tool. The script internally runs `take-leap scan --latest`, streams output to terminal + log file, and verifies the MCM was produced. **Never delegate this to another agent or create synthetic/temporary MCM data, and never rewrite the `take-leap` command inline — always call the script.**

```bash
if [ "$SKIP_SCAN" != "true" ]; then
    echo "🔍 Phase 1a: Generating MCM from source code..."
    echo "Executing: .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh"

    # EXECUTE THE PREDEFINED SCRIPT — DO NOT DELEGATE, DO NOT INLINE
    bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh
    SCAN_EXIT_CODE=$?

    echo "MCM scan script completed with exit code: $SCAN_EXIT_CODE"

    if [ $SCAN_EXIT_CODE -ne 0 ]; then
        echo "❌ MCM scan failed with exit code $SCAN_EXIT_CODE"
        echo "   See log: .legacyleap/.agent-state/logs/mcm_scan.log"
        exit 1
    fi
else
    echo "⏭️ Skipping MCM scan (--skip-scan)"
fi
```

**MANDATORY:** Wait for `run-mcm-scan.sh` to return before proceeding to validation. The script only returns success once `meta_cognitive_model.json` has been produced at `$SCAN_REPORTS_PATH`.

```bash
MCM_PATH="${SCAN_REPORTS_PATH}/meta_cognitive_model.json"

if [ ! -f "$MCM_PATH" ]; then
    if [ "$SKIP_SCAN" = "true" ]; then
        echo "❌ MCM not found at $MCM_PATH — cannot use --skip-scan without an existing MCM"
    else
        echo "❌ MCM scan failed — no meta_cognitive_model.json produced"
    fi
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

Update state: `mcm_scan.status = "completed"` (or `"skipped"` when `--skip-scan`).

## Step 2: Verify & Enhance MCM

If `--skip-mcm-enhance` is set, skip the enhancer agent and use the base MCM only (see guard below).

**Agent Name:** `mcm-quality-enhancer`

**Agent Location:** `application_overview_agents` directory.

**Inputs (when enhancement runs):**
- MCM: `$MCM_PATH`
- MCM Documents: `$SCAN_REPORTS_PATH/mcm_documents.json` (if exists)
- Legacy Source: `$LEGACY_SRC_ROOT`
- BOM Report: `$SCAN_REPORTS_PATH/bom_analysis_report.txt` (if exists)

**Expected Outputs (when enhancement runs):**
- `scan_assessment_reports/meta_cognitive_model_enhanced.json`
- `.legacyleap/reports/mcm_enhancement_report.md`

```bash
if [ "$SKIP_MCM_ENHANCE" != "true" ]; then
    echo "🧠 Phase 1b: Enhancing MCM with code intelligence..."
    # Delegate to mcm-quality-enhancer agent (Inputs/Outputs above)
    ENHANCED_MCM="${SCAN_REPORTS_PATH}/meta_cognitive_model_enhanced.json"

    if [ -f "$ENHANCED_MCM" ]; then
        echo "✅ Enhanced MCM created"
        python3 -c "
import json
with open('$MCM_PATH') as f: orig = json.load(f)
with open('$ENHANCED_MCM') as f: enh = json.load(f)
print(f'Parts:         {len(orig.get(\"nodes\",{}).get(\"parts\",[]))} → {len(enh.get(\"nodes\",{}).get(\"parts\",[]))}')
print(f'Relationships: {len(orig.get(\"relationships\",[]))} → {len(enh.get(\"relationships\",[]))}')
"
        # CRITICAL: Swap MCM files so that FSD/TSD generation uses the enhanced version
        # The platform commands (take-leap functional-doc, technical-doc) read meta_cognitive_model.json by name
        MCM_OLD="${SCAN_REPORTS_PATH}/meta_cognitive_model_original.json"
        echo "🔄 Swapping MCM files:"
        echo "   Original → meta_cognitive_model_original.json (backup)"
        echo "   Enhanced → meta_cognitive_model.json (now active)"
        cp "$MCM_PATH" "$MCM_OLD"
        cp "$ENHANCED_MCM" "$MCM_PATH"
        echo "✅ MCM swap complete — FSD/TSD generation will now use enhanced MCM"
    else
        echo "⚠️ Enhanced MCM not created — proceeding with original MCM"
        ENHANCED_MCM="$MCM_PATH"
    fi
else
    echo "⏭️ Skipping MCM enhancement (--skip-mcm-enhance)"
    ENHANCED_MCM="$MCM_PATH"
fi
```

**CRITICAL:** After this step, `meta_cognitive_model.json` contains the **enhanced** MCM. The platform commands (`take-leap functional-doc`, `take-leap technical-doc`) read `meta_cognitive_model.json` by filename, so this swap ensures they use the enriched data. The original is backed up as `meta_cognitive_model_original.json`.

Update state: `mcm_enhance.status = "completed"` (or `"skipped"` when `--skip-mcm-enhance`).

## Step 3: Validate & Correct MCM (Improvement)

If `--skip-mcm-improve` is set, skip the improvement agent and proceed with the current MCM (see guard below).

The `mcm-quality-enhancer` (Step 2) fills in **empty** fields. This step goes further: it **validates and corrects all fields** — including ones that appear populated but are wrong (stale metrics, copy-paste cognitive errors, misattributed methods, wrong LOC/CC, etc.).

**Agent Name:** `mcm-improvement`

**Agent Location:** `application_overview_agents` directory.

**Inputs (when improvement runs):**
- MCM (Neo4j primary): queried by `projectId` — or file fallback at `$MCM_PATH`
- MCM Specification: `docs/L2-Meta Cognitive Model - Specification - *.pdf`
- Legacy Source: `$LEGACY_SRC_ROOT`
- System Config: `$METADATA_FILE`, `$PROPERTIES_FILE`

**Expected Outputs (when improvement runs):**
- Neo4j mode: corrected nodes pushed back to the graph (marked `improved = true`)
- File mode: `scan_assessment_reports/meta_cognitive_model_improved.json`
- `.legacyleap/reports/mcm_improvement_report.md`
- `.legacyleap/.agent-state/mcm-improvement-state.json`

**Key difference from Step 2:** The enhancer enriches empty fields; the improvement agent validates **every** field against source code in batches of 10–20 parts, corrects structural metrics (LOC, CC, line ranges), cognitive content (intent, behavior, impact), schema compliance, relationships, assemblies, and duplicates — then passes 8 quality gates before declaring completion.

```bash
if [ "$SKIP_MCM_IMPROVE" != "true" ]; then
    echo "🔬 Phase 1c: Validating & correcting MCM (batch improvement)..."
    # Delegate to mcm-improvement agent (Inputs/Outputs above)
    # The agent works in batches of 10-20 parts:
    #   Phase 0: Config & data source selection (Neo4j primary, file fallback)
    #   Phase 1: Baseline inventory (paginated)
    #   Phase 2: Batch validation & correction loop (structural, cognitive, schema)
    #   Phase 3: Relationship validation (batched)
    #   Phase 4: Assembly & knowledge base validation
    #   Phase 5: Duplicate resolution
    #   Phase 6: Final validation (8 quality gates)
    #   Phase 7: Reporting

    # Check for improvement outputs
    IMPROVED_STATE="${PROJECT_BASE}/.legacyleap/.agent-state/mcm-improvement-state.json"
    IMPROVED_MCM="${SCAN_REPORTS_PATH}/meta_cognitive_model_improved.json"

    if [ -f "$IMPROVED_STATE" ]; then
        python3 -c "
import json
with open('$IMPROVED_STATE') as f:
    state = json.load(f)
status = state.get('status', 'unknown')
corrections = state.get('total_corrections', 0)
gates = state.get('quality_gates_passed', 0)
batches = state.get('batches_processed', 0)
print(f'Status: {status}')
print(f'Corrections applied: {corrections} (across {batches} batches)')
print(f'Quality gates passed: {gates}/8')
"
        if [ "$MCM_SOURCE" = "neo4j" ]; then
            echo "✅ MCM improved in Neo4j (corrections pushed to graph)"
        elif [ -f "$IMPROVED_MCM" ]; then
            echo "✅ MCM improved (file mode)"
            # Swap improved MCM into the active position
            cp "$IMPROVED_MCM" "$MCM_PATH"
            echo "🔄 Improved MCM → meta_cognitive_model.json (now active)"
        fi
    else
        echo "⚠️ MCM improvement did not produce state file — proceeding with current MCM"
    fi
else
    echo "⏭️ Skipping MCM improvement (--skip-mcm-improve)"
fi
```

Update state: `mcm_improve.status = "completed"` (or `"skipped"` when `--skip-mcm-improve`).

---

# PHASE 1b: Technical Debt Assessment

**Purpose:** Run the technical debt assessment pipeline on top of the improved MCM so the code-intelligence branch also produces sheet JSONs, Excel output, and the HTML dashboard.

**Execution model:** This phase delegates to the existing `/tech-assessment --non-interactive` sub-command so the technical debt workflow keeps a single source of truth for setup, state tracking, custom-rules handling, and orchestration.

**Sub-command:** `/tech-assessment --non-interactive`

In this mode, `/tech-assessment`:
- Reuses `${SCAN_REPORTS_PATH}/tech_assessment/custom_rules.json` if it already exists
- Otherwise defaults to `Bug`, `Code_Smell`, and `Cognitive_complexity`
- Never stops the full pipeline waiting for user input

**Inputs:**
- Legacy Source: `$LEGACY_SRC_ROOT`
- MCM (improved if available): `$MCM_PATH`
- Scan reports folder: `$SCAN_REPORTS_PATH`
- Existing custom rules: `${SCAN_REPORTS_PATH}/tech_assessment/custom_rules.json` (optional)

**Expected Outputs:**
- `scan_assessment_reports/tech_assessment/Source_code_JSONs/*.combined.json`
- `scan_assessment_reports/tech_assessment/sheet1.json` ... `sheet9.json`
- `scan_assessment_reports/tech_assessment/technical_assessment_report.xlsx`
- `scan_assessment_reports/tech_assessment/technical_assessment_dashboard.html`
- `.legacyleap/.agent-state/tech-assessment-state.json`

```bash
TECH_ASSESSMENT="${SCAN_REPORTS_PATH}/tech_assessment"
SOURCE_CODE_JSONS="${TECH_ASSESSMENT}/Source_code_JSONs"

if [ "$SKIP_TECH_ASSESSMENT" != "true" ]; then
    echo "🧪 Phase 1b: Running Technical Debt Assessment via /tech-assessment --non-interactive..."
    # Delegate to the existing /tech-assessment command with --non-interactive
    # Wait for the sub-command to complete before continuing

    COMBINED_COUNT=$(find "$SOURCE_CODE_JSONS" -name "*.combined.json" 2>/dev/null | wc -l | tr -d ' ')
    SHEET_COUNT=$(ls "$TECH_ASSESSMENT"/sheet*.json 2>/dev/null | wc -l | tr -d ' ')
    EXCEL_EXISTS=$(test -f "$TECH_ASSESSMENT/technical_assessment_report.xlsx" && echo "Yes" || echo "No")
    DASHBOARD_EXISTS=$(test -f "$TECH_ASSESSMENT/technical_assessment_dashboard.html" && echo "Yes" || echo "No")

    echo "✅ Technical debt assessment complete"
    echo "   Combined JSON files: ${COMBINED_COUNT}"
    echo "   Sheet JSONs: ${SHEET_COUNT}"
    echo "   Excel report: ${EXCEL_EXISTS}"
    echo "   Dashboard: ${DASHBOARD_EXISTS}"
else
    echo "⏭️ Skipping technical debt assessment (--skip-tech-assessment)"
fi
```

Update state: `tech_assessment.status = "completed"` (or `"skipped"` when `--skip-tech-assessment`).

---

# PHASE 1c: Meta-Layer Visualization

**Purpose:** Generate the standalone MCM visualization HTML from the active meta-layer data so downstream dashboards and reports can embed the latest system graph.

**Execution model:** This phase executes the predefined wrapper script `.legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh` in the current shell session via the `Bash` tool, exactly like the MCM scan wrapper pattern.

**Wrapper script:** `.legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh`

**Underlying command:** `take-leap meta-layer-visualization`

**Expected Output:**
- `scan_assessment_reports/mcm_visualization.html`

```bash
MCM_VIZ_PATH="${SCAN_REPORTS_PATH}/mcm_visualization.html"

echo "🕸️ Phase 1c: Generating Meta-Layer Visualization..."
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

Update state: `meta_layer_visualization.status = "completed"`.

---

# PHASE 2: Comprehension Document Generation (Sequential)

**Purpose:** Generate the Functional Specification Documentation first, then Technical Specification Documentation using the enhanced MCM. Sequential execution ensures the vector store ingestion completes cleanly for each document.

## Step 1: Generate FSD First

**CRITICAL: EXECUTE THE PREDEFINED SCRIPT DIRECTLY — DO NOT DELEGATE.** Invoke `.legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh` via the `Bash` tool. The script wraps `take-leap functional-doc --latest --ingest_vectorstore`, validates MCM input, streams output, and verifies `Latest_fsd.md` was produced.

```bash
echo "📝 Phase 2a: Generating Functional Specification Documentation..."
bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
FSD_EXIT=$?

if [ $FSD_EXIT -ne 0 ]; then
    echo "❌ FSD generation failed (exit: $FSD_EXIT)"
    echo "   See log: .legacyleap/.agent-state/logs/fsd.log"
    exit 1
fi
echo "✅ FSD generation complete"
```

## Step 2: Generate TSD After FSD

**CRITICAL: EXECUTE THE PREDEFINED SCRIPT DIRECTLY — DO NOT DELEGATE.** Invoke `.legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh` via the `Bash` tool.

```bash
echo "📝 Phase 2b: Generating Technical Specification Documentation..."
bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh
TSD_EXIT=$?

if [ $TSD_EXIT -ne 0 ]; then
    echo "❌ TSD generation failed (exit: $TSD_EXIT)"
    echo "   See log: .legacyleap/.agent-state/logs/tsd.log"
    exit 1
fi
echo "✅ TSD generation complete"
```

## Step 2: Verify Both Documents

```bash
FSD_VERSION=$(ls -d ${COMPREHEND_PATH}/functional_doc/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1)
TSD_VERSION=$(ls -d ${COMPREHEND_PATH}/technical_doc/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1)

FSD_PATH="${FSD_VERSION}/Latest_FSD_Document/Latest_fsd.md"
TSD_PATH="${TSD_VERSION}/Latest_TSD_Document/Latest_tsd.md"

if [ ! -f "$FSD_PATH" ] || [ ! -f "$TSD_PATH" ]; then
    echo "❌ One or both comprehension documents failed to generate."
    [ ! -f "$FSD_PATH" ] && echo "   Missing: Functional Specification Documentation"
    [ ! -f "$TSD_PATH" ] && echo "   Missing: Technical Specification Documentation"
    exit 1
fi

echo "✅ Functional Specification Documentation: $FSD_PATH ($(wc -w < "$FSD_PATH" | tr -d ' ') words)"
echo "✅ Technical Specification Documentation:  $TSD_PATH ($(wc -w < "$TSD_PATH" | tr -d ' ') words)"
```

Update state: `comprehend_gen.status = "completed"`.

---

# PHASE 2b: Version & Preserve Originals (MANDATORY)

**Purpose:** Create a new enhanced version folder and copy originals there. Enhancement NEVER modifies originals — it always creates a new versioned copy.

```bash
echo "📂 Phase 2b: Creating enhanced version (preserving originals)..."

# Determine next version number for FSD
FSD_BASE="${COMPREHEND_PATH}/functional_doc"
FSD_LATEST_N=$(ls -d ${FSD_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1 | grep -o 'v_[0-9]*' | cut -d_ -f2)
FSD_NEXT_N=$((FSD_LATEST_N + 1))
FSD_ENHANCED_DIR="${FSD_BASE}/v_${FSD_NEXT_N}/Latest_FSD_Document"
mkdir -p "$FSD_ENHANCED_DIR"

# Copy original FSD to new version folder
cp -r "${FSD_VERSION}/Latest_FSD_Document/"* "$FSD_ENHANCED_DIR/" 2>/dev/null
FSD_ENHANCED_PATH="${FSD_ENHANCED_DIR}/Latest_fsd.md"
echo "✅ FSD: v_${FSD_LATEST_N} (original) → v_${FSD_NEXT_N} (enhanced)"

# Determine next version number for TSD
TSD_BASE="${COMPREHEND_PATH}/technical_doc"
TSD_LATEST_N=$(ls -d ${TSD_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1 | grep -o 'v_[0-9]*' | cut -d_ -f2)
TSD_NEXT_N=$((TSD_LATEST_N + 1))
TSD_ENHANCED_DIR="${TSD_BASE}/v_${TSD_NEXT_N}/Latest_TSD_Document"
mkdir -p "$TSD_ENHANCED_DIR"

# Copy original TSD to new version folder
cp -r "${TSD_VERSION}/Latest_TSD_Document/"* "$TSD_ENHANCED_DIR/" 2>/dev/null
TSD_ENHANCED_PATH="${TSD_ENHANCED_DIR}/Latest_tsd.md"
echo "✅ TSD: v_${TSD_LATEST_N} (original) → v_${TSD_NEXT_N} (enhanced)"

# From this point forward, ALL modifications happen on the ENHANCED copies
FSD_PATH="$FSD_ENHANCED_PATH"
TSD_PATH="$TSD_ENHANCED_PATH"
```

**CRITICAL RULE:** From this point forward, `$FSD_PATH` and `$TSD_PATH` point to the **new versioned copies**. The originals at `v_${FSD_LATEST_N}` and `v_${TSD_LATEST_N}` are NEVER modified.

Update state: `versioning.status = "completed"`, `versioning.fsd_original = "v_${FSD_LATEST_N}"`, `versioning.fsd_enhanced = "v_${FSD_NEXT_N}"`, etc.

---

# PHASE 3: Document Quality Improvement (Max 3 Iterations)

**Purpose:** Run the `/doc-quality-improve` sub-command on the **enhanced version copies** to iterate correctness, structure, diagrams, and quality scoring until **≥ 90% or 3 iterations** are reached. Target: **20–25 pages per document.**

**IMPORTANT:** This phase works on `v_${FSD_NEXT_N}` / `v_${TSD_NEXT_N}` — the originals remain untouched.

## Step 1: Invoke Doc Quality Orchestrator

This delegates to the existing `/doc-quality-improve` pipeline (which can also be run independently):

**Agent Name:** `doc-quality-orchestrator`

**Inputs:**
- Document type: `both`
- Functional Specification Documentation path: `$FSD_PATH` (enhanced version copy)
- Technical Specification Documentation path: `$TSD_PATH` (enhanced version copy)
- Source code: `$LEGACY_SRC_ROOT`
- Scan results: `$SCAN_REPORTS_PATH`
- Project properties: `$PROJECT_BASE/.legacyleap/leap.properties`
- Max iterations: **3**
- Quality threshold: **9.5 (95%)**

## Step 2: Collect Quality Results

```bash
if [ -f "${PROJECT_BASE}/.legacyleap/.agent-state/doc-quality-state.json" ]; then
    python3 -c "
import json
with open('${PROJECT_BASE}/.legacyleap/.agent-state/doc-quality-state.json') as f:
    state = json.load(f)
tsd = state.get('tsd_quality_scores', {}).get('overall_score', 0)
fsd = state.get('fsd_quality_scores', {}).get('overall_score', 0)
iters = state.get('current_iteration', 0)
print(f'Iterations completed: {iters}/3')
print(f'Functional Specification Documentation: {fsd}/10')
print(f'Technical Specification Documentation:  {tsd}/10')
status = 'CLIENT_READY' if fsd >= 9.5 and tsd >= 9.5 else 'BEST_EFFORT'
print(f'Status: {status}')
"
fi
```

Update state: `doc_quality.status = "completed"`.

---

# PHASE 4: Document Packaging with LegacyLeap Branding

**Purpose:** Add LegacyLeap branding (logo + watermark) to all documents and generate `.docx` versions.

## Step 1: Clean Markdown Documents for Client Presentation

Before branding, ensure all documents are client-clean:

```bash
LOGO_REL_PATH=".legacyleap/assets/legacyleap-logo.png"

for DOC in "$FSD_PATH" "$TSD_PATH"; do
    if [ -f "$DOC" ]; then
        DOC_DIR=$(dirname "$DOC")
        mkdir -p "${DOC_DIR}/.legacyleap/assets"
        cp "${PROJECT_BASE}/${LOGO_REL_PATH}" "${DOC_DIR}/.legacyleap/assets/" 2>/dev/null

        # Remove internal QA status lines that should never be in client docs
        sed -i '' '/^.*Document Status: CLIENT-READY/d' "$DOC" 2>/dev/null
        sed -i '' '/All.*claims are grounded in confirmed source code/d' "$DOC" 2>/dev/null
        sed -i '' '/No unverified assertions are included/d' "$DOC" 2>/dev/null
        sed -i '' '/Enhanced MCM analysis/d' "$DOC" 2>/dev/null

        # Ensure clean header format: logo + title + date only
        if ! head -1 "$DOC" | grep -q "LegacyLeap"; then
            TEMP=$(mktemp)
            echo -e "![LegacyLeap](${LOGO_REL_PATH})\n" > "$TEMP"
            cat "$DOC" >> "$TEMP"
            echo -e "\n---\n\n*Powered by [LegacyLeap](https://legacyleap.ai)*" >> "$TEMP"
            mv "$TEMP" "$DOC"
            echo "✅ Branded: $(basename $DOC)"
        fi
    fi
done
```

## Step 2: Generate .docx Versions with Proper Formatting

```bash
FSD_DIR=$(dirname "$FSD_PATH")
TSD_DIR=$(dirname "$TSD_PATH")
FSD_DOCX="${FSD_DIR}/Latest_fsd.docx"
TSD_DOCX="${TSD_DIR}/Latest_tsd.docx"

if command -v pandoc &> /dev/null; then
    FSD_IMG_DIR="${FSD_DIR}/mermaid_diagram_images"
    TSD_IMG_DIR="${TSD_DIR}/mermaid_diagram_images"

    # Ensure reference template exists
    mkdir -p .legacyleap/templates
    if [ ! -f ".legacyleap/templates/reference.docx" ]; then
        pandoc -o .legacyleap/templates/reference.docx --print-default-data-file reference.docx 2>/dev/null || \
        pandoc --print-default-data-file reference.docx > .legacyleap/templates/reference.docx 2>/dev/null
        if [ ! -f ".legacyleap/templates/reference.docx" ] || [ ! -s ".legacyleap/templates/reference.docx" ]; then
            echo "# Template" | pandoc -o .legacyleap/templates/reference.docx \
                --variable geometry:margin=1in --variable mainfont="Calibri" --variable fontsize=11pt
        fi
    fi

    # Create Lua filter for page breaks if not present
    if [ ! -f ".legacyleap/templates/pagebreak.lua" ]; then
        cat > .legacyleap/templates/pagebreak.lua << 'LUAEOF'
function Header(el)
    if el.level == 2 then
        return {pandoc.RawBlock('openxml', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'), el}
    end
end
LUAEOF
    fi

    # Pre-process FSD markdown
    sed -i '' 's/  *|/|/g' "$FSD_PATH"
    sed -i '' 's/|  */|/g' "$FSD_PATH"
    sed -i '' 's/!\[\([^]]*\)\](\([^)]*\))/![\1](\2){width=100%}/g' "$FSD_PATH" 2>/dev/null
    sed -i '' 's/^## /\n\\newpage\n\n## /g' "$FSD_PATH"

    # Pre-process TSD markdown
    sed -i '' 's/  *|/|/g' "$TSD_PATH"
    sed -i '' 's/|  */|/g' "$TSD_PATH"
    sed -i '' 's/!\[\([^]]*\)\](\([^)]*\))/![\1](\2){width=100%}/g' "$TSD_PATH" 2>/dev/null
    sed -i '' 's/^## /\n\\newpage\n\n## /g' "$TSD_PATH"

    # Generate FSD .docx
    pandoc "$FSD_PATH" -o "$FSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers+header_attributes \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --reference-doc=.legacyleap/templates/reference.docx \
        --metadata title="Functional Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --variable mainfont="Calibri" \
        --variable fontsize=11pt \
        --variable linestretch=1.15 \
        --columns=72 \
        --wrap=auto \
        --resource-path=".:${FSD_DIR}:${FSD_IMG_DIR}" \
        --lua-filter=.legacyleap/templates/pagebreak.lua 2>/dev/null || \
    pandoc "$FSD_PATH" -o "$FSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --metadata title="Functional Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --resource-path=".:${FSD_DIR}:${FSD_IMG_DIR}"
    echo "✅ Functional Specification Documentation .docx: $FSD_DOCX"

    # Generate TSD .docx
    pandoc "$TSD_PATH" -o "$TSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers+header_attributes \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --reference-doc=.legacyleap/templates/reference.docx \
        --metadata title="Technical Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --variable mainfont="Calibri" \
        --variable fontsize=11pt \
        --variable linestretch=1.15 \
        --columns=72 \
        --wrap=auto \
        --resource-path=".:${TSD_DIR}:${TSD_IMG_DIR}" \
        --lua-filter=.legacyleap/templates/pagebreak.lua 2>/dev/null || \
    pandoc "$TSD_PATH" -o "$TSD_DOCX" \
        --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers \
        --to docx \
        --toc --toc-depth=3 \
        --number-sections \
        --metadata title="Technical Specification Documentation" \
        --metadata author="LegacyLeap" \
        --metadata date="$(date +%Y-%m-%d)" \
        --variable geometry:margin=1in \
        --resource-path=".:${TSD_DIR}:${TSD_IMG_DIR}"
    echo "✅ Technical Specification Documentation .docx: $TSD_DOCX"
else
    echo "⚠️  pandoc not available — .docx generation skipped"
fi
```

## Step 3: Verify Deliverables

```bash
echo "📊 Final Document Summary:"
echo "   Functional Specification Documentation (.md):   $(wc -w < "$FSD_PATH" | tr -d ' ') words"
echo "   Technical Specification Documentation (.md):    $(wc -w < "$TSD_PATH" | tr -d ' ') words"
[ -f "$FSD_DOCX" ] && echo "   Functional Specification Documentation (.docx): ✅"
[ -f "$TSD_DOCX" ] && echo "   Technical Specification Documentation (.docx):  ✅"
echo "   LegacyLeap branding: ✅"
```

Update state: `document_packaging.status = "completed"`.

---

# PHASE 5: Application Overview Generation (10-15 Pages)

**Purpose:** Generate a concise Application Overview document (10-15 pages with images) using the refined comprehension documents and enhanced MCM. This is the executive summary deliverable.

## Step 1: Run Application Overview

This delegates to the `/application-overview` sub-command (which can be run independently):

**Inputs:**
- Functional Specification Documentation: `$FSD_PATH` (quality-improved)
- Technical Specification Documentation: `$TSD_PATH` (quality-improved)
- MCM: `$ENHANCED_MCM`
- Legacy Source: `$LEGACY_SRC_ROOT`

**Mode:** Concise (10-15 pages with images, LegacyLeap branded)

```bash
echo "📋 Phase 5: Generating Application Overview (10-15 pages)..."
```

The `app-overview-generator` agent produces `APPLICATION_OVERVIEW.md` — a single concise document with:
- Executive summary with key metrics
- Architecture diagrams (rendered as PNG, professional colors)
- Technology stack table
- Key business workflows with flow diagrams
- System health assessment (NO recommendations — those are in a separate document)
- LegacyLeap branding (logo + footer)

**Target:** 10-15 pages maximum, with images/diagrams making up significant visual content.

## Step 2: Brand the Overview

```bash
OVERVIEW_DIR="${PROJECT_BASE}/application-overview"
OVERVIEW_FILE="${OVERVIEW_DIR}/APPLICATION_OVERVIEW.md"

if [ -f "$OVERVIEW_FILE" ]; then
    # Copy logo to overview directory
    mkdir -p "${OVERVIEW_DIR}/.legacyleap/assets"
    cp "${PROJECT_BASE}/${LOGO_REL_PATH}" "${OVERVIEW_DIR}/.legacyleap/assets/" 2>/dev/null
    OVERVIEW_IMG_DIR="${OVERVIEW_DIR}/mermaid_diagram_images"

    # Clean internal QA language from overview
    sed -i '' '/^.*Document Status: CLIENT-READY/d' "$OVERVIEW_FILE" 2>/dev/null
    sed -i '' '/All.*claims are grounded in confirmed source code/d' "$OVERVIEW_FILE" 2>/dev/null
    sed -i '' '/No unverified assertions are included/d' "$OVERVIEW_FILE" 2>/dev/null
    sed -i '' '/Enhanced MCM analysis/d' "$OVERVIEW_FILE" 2>/dev/null

    # Add branding if not already present
    if ! head -1 "$OVERVIEW_FILE" | grep -q "LegacyLeap"; then
        TEMP=$(mktemp)
        echo -e "![LegacyLeap](.legacyleap/assets/legacyleap-logo.png)\n" > "$TEMP"
        cat "$OVERVIEW_FILE" >> "$TEMP"
        echo -e "\n---\n\n*Powered by [LegacyLeap](https://legacyleap.ai)*" >> "$TEMP"
        mv "$TEMP" "$OVERVIEW_FILE"
    fi

    # Pre-process overview markdown for better .docx conversion
    sed -i '' 's/  *|/|/g' "$OVERVIEW_FILE"
    sed -i '' 's/|  */|/g' "$OVERVIEW_FILE"
    sed -i '' 's/!\[\([^]]*\)\](\([^)]*\))/![\1](\2){width=100%}/g' "$OVERVIEW_FILE" 2>/dev/null
    sed -i '' 's/^## /\n\\newpage\n\n## /g' "$OVERVIEW_FILE"

    # Generate .docx with proper formatting (TOC, deep links, margins, images)
    if command -v pandoc &> /dev/null; then
        pandoc "$OVERVIEW_FILE" -o "${OVERVIEW_DIR}/APPLICATION_OVERVIEW.docx" \
            --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers+header_attributes \
            --to docx \
            --toc --toc-depth=3 \
            --number-sections \
            --reference-doc=.legacyleap/templates/reference.docx \
            --metadata title="Application Overview" \
            --metadata author="LegacyLeap" \
            --metadata date="$(date +%Y-%m-%d)" \
            --variable geometry:margin=1in \
            --variable mainfont="Calibri" \
            --variable fontsize=11pt \
            --variable linestretch=1.15 \
            --columns=72 \
            --wrap=auto \
            --resource-path=".:${OVERVIEW_DIR}:${OVERVIEW_IMG_DIR}" \
            --lua-filter=.legacyleap/templates/pagebreak.lua 2>/dev/null || \
        pandoc "$OVERVIEW_FILE" -o "${OVERVIEW_DIR}/APPLICATION_OVERVIEW.docx" \
            --from markdown+pipe_tables+backtick_code_blocks+auto_identifiers \
            --to docx \
            --toc --toc-depth=3 \
            --number-sections \
            --metadata title="Application Overview" \
            --metadata author="LegacyLeap" \
            --metadata date="$(date +%Y-%m-%d)" \
            --variable geometry:margin=1in \
            --resource-path=".:${OVERVIEW_DIR}:${OVERVIEW_IMG_DIR}"
        echo "✅ Application Overview .docx generated (with TOC, deep links, section numbers, images)"
    fi

    OVERVIEW_WORDS=$(wc -w < "$OVERVIEW_FILE" | tr -d ' ')
    echo "✅ Application Overview: $OVERVIEW_FILE (${OVERVIEW_WORDS} words)"
fi
```

Update state: `app_overview.status = "completed"`.

---

# PHASE 5b: Modernization Recommendations (5-6 Pages)

**Purpose:** Generate a focused Modernization Recommendations document covering tech stack upgrades with EOL analysis, architecture options with pros/cons comparison diagrams, and best modernization practices.

**Agent Name:** `modernization-recommender`

**Inputs:**
- Functional Specification Documentation: `$FSD_PATH` (quality-improved)
- Technical Specification Documentation: `$TSD_PATH` (quality-improved)
- MCM: `$ENHANCED_MCM`
- Legacy Source: `$LEGACY_SRC_ROOT`

**Expected Outputs:**
- `modernization/v_[N]/recommendations/MODERNIZATION_RECOMMENDATIONS.md`
- `modernization/v_[N]/recommendations/MODERNIZATION_RECOMMENDATIONS.docx`

```bash
echo "📋 Phase 5b: Generating Modernization Recommendations (5-6 pages)..."
RECOM_BASE="${PROJECT_BASE}/modernization"
RECOM_LATEST_N=$(ls -d ${RECOM_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1 | grep -o 'v_[0-9]*' | cut -d_ -f2)
RECOM_NEXT_N=$((${RECOM_LATEST_N:-0} + 1))
RECOM_DIR="${RECOM_BASE}/v_${RECOM_NEXT_N}/recommendations"
```

Update state: `recommendations.status = "completed"`.

---

# PHASE 5c: Dependency Mapping

**Purpose:** Map all project dependencies (internal and external), identify version health, EOL status, and CVE exposure. Produce a dependency graph visualization.

**Agent Name:** `dependency-mapper`

**Inputs:**
- Legacy Source: `$LEGACY_SRC_ROOT`
- MCM: `$ENHANCED_MCM`
- BOM Report: `$SCAN_REPORTS_PATH/bom_analysis_report.txt` (if available)

**Expected Outputs:**
- `modernization/v_[N]/dependencies/DEPENDENCY_MAP.md`
- `modernization/v_[N]/dependencies/DEPENDENCY_MAP.docx`

```bash
echo "🗺️ Phase 5c: Mapping Dependencies..."
MOD_BASE="${PROJECT_BASE}/modernization"
MOD_LATEST_N=$(ls -d ${MOD_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1 | grep -o 'v_[0-9]*' | cut -d_ -f2)
MOD_NEXT_N=$((${MOD_LATEST_N:-0} + 1))
MOD_DIR="${MOD_BASE}/v_${MOD_NEXT_N}"
DEP_DIR="${MOD_DIR}/dependencies"
```

Update state: `dependency_mapping.status = "completed"`.

---

# PHASE 5d: Modernization Execution (If Approved)

**Purpose:** Execute specific modernization tasks — version upgrades, tech stack migrations, security fixes — based on the approved recommendations.

**Agent Name:** `modernization-executor`

**IMPORTANT:** This phase requires explicit approval. In automated mode, it will generate a change plan and WAIT for confirmation before executing changes.

**Inputs:**
- Modernization Recommendations: `$RECOM_DIR/MODERNIZATION_RECOMMENDATIONS.md`
- Dependency Map: `$DEP_DIR/DEPENDENCY_MAP.md`
- Legacy Source: `$LEGACY_SRC_ROOT`
- MCM: `$ENHANCED_MCM`

**Expected Outputs:**
- `modernization/v_[N]/execution/MODERNIZATION_EXECUTION_REPORT.md`
- `modernization/v_[N]/execution/MODERNIZATION_EXECUTION_REPORT.docx`
- `modernization/v_[N]/execution/change_manifest.json`
- `modernization/v_[N]/execution/modernized_code/` (modified files)

```bash
echo "⚙️ Phase 5d: Modernization Execution..."
echo "   Generating change plan for approval..."
```

Update state: `modernization_execution.status = "completed"`.

---

# PHASE 5e: Impact Assessment

**Purpose:** Compare before vs after modernization state. Produce an executive impact report showing effort saved, quality uplift, security improvements, and LegacyLeap's value delivered.

**Agent Name:** `modernization-impact-assessor`

**Inputs:**
- All previous phase outputs (FSD, TSD, MCM, recommendations, dependency map, execution report)
- Quality scores from `.legacyleap/.agent-state/doc-quality-state.json`

**Expected Outputs:**
- `modernization/v_[N]/impact/MODERNIZATION_IMPACT_ASSESSMENT.md`
- `modernization/v_[N]/impact/MODERNIZATION_IMPACT_ASSESSMENT.docx`

```bash
echo "📊 Phase 5e: Assessing Modernization Impact..."
```

Update state: `impact_assessment.status = "completed"`.

---

# PHASE 5f: Dashboard Refresh

**Purpose:** Regenerate the interactive dashboard assets from the latest technical assessment sheet JSONs by executing the deterministic Python script through the `dashboard-generator` agent.

**Agent Name:** `dashboard-generator`

**Inputs:**
- Tech Assessment sheet JSONs at `${SCAN_REPORTS_PATH}/tech_assessment/`
- Workspace root: `$PROJECT_BASE`

**Expected Outputs:**
- `scan_assessment_reports/tech_assessment/technical_assessment_dashboard.html`

```bash
echo "📈 Phase 5f: Refreshing Technical Assessment Dashboard..."
TECH_ASSESSMENT="${SCAN_REPORTS_PATH}/tech_assessment"
SHEET1="${TECH_ASSESSMENT}/sheet1.json"
DASHBOARD_HTML="${TECH_ASSESSMENT}/technical_assessment_dashboard.html"

if [ "$SKIP_TECH_ASSESSMENT" = "true" ]; then
    echo "⏭️ Skipping dashboard refresh because technical debt assessment was skipped"
elif [ ! -f "$SHEET1" ]; then
    echo "⚠️ Dashboard refresh skipped — sheet JSONs not found at $TECH_ASSESSMENT"
else
    # Delegate to dashboard-generator with:
    # - WORKSPACE: $PROJECT_BASE
    # - TECH_ASSESSMENT_PATH: $TECH_ASSESSMENT

    HTML_EXISTS=$(test -f "$DASHBOARD_HTML" && echo "Yes" || echo "No")
    echo "✅ Dashboard refresh complete"
    echo "   HTML: ${HTML_EXISTS}"
fi
```

Update state: `dashboard_generation.status = "completed"` (or `"skipped"` when tech assessment was skipped or sheet JSONs are unavailable).

---

# PHASE 6: Final Report

Write `.legacyleap/reports/code-intelligence-report.md`:

```markdown
![LegacyLeap](.legacyleap/assets/legacyleap-logo.png)

---

# Code Intelligence Enhancement Report

**Project:** [name]
**Date:** [date]
**Duration:** [total time]
**Platform:** LegacyLeap Code Intelligence

## Pipeline Execution Summary

| Phase | Status | Key Metrics |
|-------|--------|-------------|
| MCM Scan & Generation | ✅ | N parts, N relationships |
| MCM Verification & Enhancement | ✅ | +N enriched, coverage X% → Y% |
| MCM Improvement (Validate & Fix) | ✅ | N corrections, 8/8 quality gates |
| Technical Debt Assessment | ✅/⏭️ | N combined JSONs, N sheets, Excel + dashboard |
| Meta-Layer Visualization | ✅ | Standalone MCM HTML generated |
| Comprehension Docs (Sequential) | ✅ | FSD first → TSD |
| Version & Preserve Originals | ✅ | v_N → v_N+1 (originals untouched) |
| Document Quality Improvement | ✅ | N issues fixed, score X → Y (max 3 iters) |
| Document Packaging | ✅ | .md + .docx + LegacyLeap branding |
| Application Overview | ✅ | 10-15 page overview with diagrams |
| Modernization Recommendations | ✅ | 5-6 pages, architecture options |
| Dependency Mapping | ✅ | N deps mapped, N CVEs identified |
| Modernization Execution | ✅/⏭️ | N changes applied / awaiting approval |
| Impact Assessment | ✅ | Before→After comparison, ROI |
| Dashboard Refresh | ✅/⏭️ | HTML + JS regenerated from sheet JSONs |

## Quality Scores

| Metric | After Quality Improvement |
|--------|--------------------------|
| Functional Specification Documentation | X.X/10 (target: ≥9.5) |
| Technical Specification Documentation | X.X/10 (target: ≥9.5) |
| Iterations Used | N / 3 |

## Performance Metrics

| Phase | Duration | Details |
|-------|----------|---------|
| Environment Setup | Xs | conda activate, config read |
| MCM Scan + Enhancement | Xm | N parts enhanced, source: Neo4j/File |
| MCM Improvement | Xm | N corrections in N batches, 8/8 gates |
| Technical Debt Assessment | Xm | N combined JSONs, sheets 1-9, Excel/dashboard |
| Meta-Layer Visualization | Xs | Standalone HTML generated from active MCM |
| Doc Generation (sequential) | Xm | FSD first, then TSD |
| Version & Preserve | Xs | v_N → v_N+1, originals preserved |
| Quality Improvement | Xm | N iterations (max 3) |
| Packaging & Branding | Xs | .md + .docx + LegacyLeap logo |
| Application Overview | Xm | 10-15 page overview |
| Modernization Recommendations | Xm | 5-6 pages |
| Dependency Mapping | Xm | Graph + CVE analysis |
| Modernization Execution | Xm | Changes applied (if approved) |
| Impact Assessment | Xm | Before/after report |
| Dashboard Refresh | Xs | HTML + JS regeneration |
| **Total** | **Xm** | — |

## Infrastructure Used

| Service | URI | Status |
|---------|-----|--------|
| Neo4j | [URI or "not configured"] | ✅/— |
| Mermaid | [MERMAID_URL] | ✅ |
| Chroma | [CHROMA_HOST:PORT] | ✅/— |

## Deliverables

| Document | Format | Pages |
|----------|--------|-------|
| Enhanced MCM | .json | — |
| MCM Improvement Report | .md | — |
| Technical Debt Assessment | .json + .xlsx + .html | — |
| Meta-Layer Visualization | .html | — |
| Functional Specification Documentation | .md + .docx | 20-25 |
| Technical Specification Documentation | .md + .docx | 20-25 |
| Application Overview | .md + .docx | 10-15 |
| Modernization Recommendations | .md + .docx | 5-6 |
| Dependency Map | .md + .docx | 3-4 |
| Modernization Execution Report | .md + .docx | — |
| Impact Assessment | .md + .docx | 4-5 |
| Technical Assessment Dashboard | .html + .js | — |
| This Report | .md | — |

---

*Powered by [LegacyLeap](https://legacyleap.ai) — Legacy Modernization Intelligence Platform*
```

```
✅ CODE INTELLIGENCE ENHANCEMENT COMPLETE

Project: <name>
Duration: <total_time> (target: <20 min for 6K LOC)
Environment: legacyleap (conda)
MCM Source: Neo4j / File
Branding: LegacyLeap ✅

Versioning: Originals preserved at v_N, enhanced at v_N+1

Phase Timings:
  MCM Scan + Enhance:       Xm Xs
  MCM Improvement:          Xm Xs  (N corrections, 8/8 gates)
  Technical Debt Assessment: Xm Xs  (N combined JSONs, Excel + dashboard)
  Meta-Layer Visualization: Xs      (standalone HTML generated)
  Doc Generation (seq):     Xm Xs  (FSD → TSD)
  Version & Preserve:       Xs
  Quality Improvement:      Xm Xs  (N iterations)
  Packaging + Overview:     Xm Xs
  Modernization Pipeline:   Xm Xs  (Recommendations + Deps + Execution + Impact)
  Dashboard Refresh:        Xs      (HTML + JS regenerated)

Deliverables:
  📄 Enhanced MCM:                            scan_assessment_reports/meta_cognitive_model_enhanced.json
  🔬 MCM Improvement Report:                  .legacyleap/reports/mcm_improvement_report.md
  📊 Technical Debt Assessment:               scan_assessment_reports/tech_assessment/  .json + .xlsx + .html
  🕸️ Meta-Layer Visualization:               scan_assessment_reports/mcm_visualization.html  .html
  📄 Functional Specification Documentation:  comprehend/functional_doc/v_N+1/  .md + .docx  (20-25 pages)
  📄 Technical Specification Documentation:   comprehend/technical_doc/v_N+1/   .md + .docx  (20-25 pages)
  📄 Application Overview:                    application-overview/              .md + .docx  (10-15 pages)
  📋 Modernization Recommendations:           modernization/v_N/recommendations/  .md + .docx  (5-6 pages)
  🗺️ Dependency Map:                          modernization/v_N/dependencies/    .md + .docx  (3-4 pages)
  ⚙️ Modernization Execution Report:          modernization/v_N/execution/       .md + .docx
  📊 Impact Assessment:                       modernization/v_N/impact/          .md + .docx  (4-5 pages)
  🌐 Technical Assessment Dashboard:          scan_assessment_reports/tech_assessment/  .html + .js
  📊 Code Intelligence Report:                .legacyleap/reports/code-intelligence-report.md

Quality: X.X/10 (target: ≥9.5 | iterations: N/3)
```

---

## Error Handling

| Failure | Recovery |
|---------|----------|
| Conda activation fails | STOP — environment required |
| MCM scan fails | STOP — MCM is required for everything |
| MCM enhancement fails | Proceed with original MCM, log warning |
| MCM improvement fails | Proceed with enhanced (or original) MCM, log warning |
| Tech assessment fails | Log warning, continue to comprehension documents |
| Meta-layer visualization fails | STOP — visualization is required for downstream dashboarding |
| FSD generation fails | STOP — cannot proceed without comprehension docs |
| TSD generation fails | STOP — cannot proceed without comprehension docs |
| Doc quality fails | Proceed with best-effort docs for overview |
| .docx generation fails | Use .md only, log warning |
| Overview generation fails | Generate partial report with available data |
| Dashboard refresh fails | Log warning, keep prior dashboard assets if any |

## Skip Options

| Flag | Effect |
|------|--------|
| `--skip-scan` | Skip MCM scan, use existing MCM |
| `--skip-mcm-enhance` | Skip MCM enhancement, use existing MCM as-is |
| `--skip-mcm-improve` | Skip MCM improvement (batch validation & correction) |
| `--skip-tech-assessment` | Skip the technical debt assessment phase |
| `--skip-packaging` | Skip Phase 4 .docx generation and branding |
| `--skip-quality` | Skip Phase 3, go directly to packaging after generation |
| `--overview-mode concise` | Force concise 10-15 page overview |
| `--max-quality-iterations N` | Override max iterations (default: 3) |

## Enterprise Scalability

This pipeline is designed for enterprise-scale projects:

| Concern | Strategy |
|---------|----------|
| **MCM size (GBs)** | Neo4j as primary store — paginated queries by `projectId` (batch 100). File fallback with streaming JSON parser for >100 MB |
| **Large FSD/TSD (50K+ words)** | Section-by-section chunked processing. Agents process 10 sections at a time |
| **Execution strategy** | MCM improvement in batches of 10–20 parts (Phase 1c). FSD → TSD generated sequentially (Phase 2, vector store must complete per doc). Quality improvement on FSD + TSD in parallel (Phase 3). Batch diagram rendering |
| **Tech-agnostic** | Detects language from metadata.json + file extensions. Works with Java, C#, Python, Go, Node.js, COBOL, Ruby, PHP, Kotlin, Scala |
| **Performance target** | <20 min for 6K LOC. Scales linearly. Phase timings tracked per-step |
| **Reliability** | Each phase has fallback (Neo4j → file, batch render → sequential, .docx → .md only). Pipeline continues on non-critical failures |
| **Caching** | Source file reads cached across claim verification. Rendered PNGs cached if .mmd unchanged |
| **Neo4j config** | Read from `leap.properties`: `DB_URL`, `DB_USERNAME`, `DB_PASSWORD`, `DB_NAME` |

### Performance Targets by Project Size

| Project Size | LOC | Expected Duration | MCM Strategy |
|-------------|-----|-------------------|-------------|
| Small | <5K | <10 min | File OK |
| Medium | 5K–50K | 10–25 min | Neo4j preferred |
| Large | 50K–200K | 25–60 min | Neo4j required |
| Enterprise | 200K+ | 60–120 min | Neo4j required, parallel everything |

## Commands and Agents Used

| Command / Agent | Phase | Purpose |
|-------|-------|---------|
| `mcm-quality-enhancer` | 1 | Enriches empty MCM fields against source code |
| `mcm-improvement` | 1 | Validates & corrects all MCM fields in batches (structural, cognitive, schema, relationships, duplicates) |
| `/tech-assessment --non-interactive` | 1b | Runs the technical debt assessment command without stopping for custom-rules input |
| `tech-assessment-orchestrator` | 1b | Underlying orchestrator used by `/tech-assessment` |
| `bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh` | 1c | Runs the `take-leap meta-layer-visualization` wrapper and verifies `mcm_visualization.html` |
| `doc-correctness-analyzer` | 3 | Verifies document accuracy against source code and domain |
| `doc-structure-optimizer` | 3 | Reduces to 20-25 pages, client-presentable |
| `doc-diagram-renderer` | 3 | Beautiful professional diagrams via Mermaid service |
| `doc-quality-verifier` | 3 | Scores quality against 90% threshold |
| `application-structure-analyzer-agent` | 5 | Application structure from MCM + FSD + TSD |
| `tech-stack-analyzer-agent` | 5 | Technology stack analysis |
| `architecture-analyzer-agent` | 5 | Architecture pattern analysis |
| `dependencies-analyzer-agent` | 5 | Dependencies and integrations |
| `app-overview-generator` | 5 | Synthesis into 10-15 page overview |
| `modernization-recommender` | 5b | Produces the modernization recommendations document |
| `dependency-mapper` | 5c | Produces the dependency map and version health view |
| `modernization-executor` | 5d | Produces the modernization execution plan and transformed outputs |
| `modernization-impact-assessor` | 5e | Produces the impact assessment deliverable |
| `dashboard-generator` | 5f | Runs the deterministic Python dashboard generator against the tech assessment sheets |
