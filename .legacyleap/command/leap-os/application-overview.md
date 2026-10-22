You are orchestrating a comprehensive **Application Overview Analysis** based on specification documents. This multi-phase process will analyze the Functional Specification Documentation, Technical Specification Documentation, and MCM to generate a complete overview covering architecture, technology stack, dependencies, and application structure.

## Modes

This command supports two modes:

- **Detailed mode** (default): Runs 4 analysis sub-agents in sequence, producing detailed reports + a synthesis overview. Use for deep technical analysis.
- **Concise mode** (`--concise`): Runs the `app-overview-generator` agent to produce a single 10–15 page client-ready document with images and LegacyLeap branding. Use for stakeholder presentations.

If `--concise` is passed, **skip directly to the concise generation** using the `app-overview-generator` agent (located in `application_overview_agents` directory), then display the final output. The concise agent reads FSD, TSD, and MCM directly and produces `APPLICATION_OVERVIEW.md`.

## Overview

The Application Overview Analysis consists of four parallel sub-agent analyses that generate four specific outputs:

**PHASE 1:** Application Structure Analysis (via application-structure-analyzer-agent) → `application_structure.md`
**PHASE 2:** Technology Stack Analysis (via tech-stack-analyzer-agent) → `tech_stack_analysis.md`
**PHASE 3:** Architecture Pattern Analysis (via architecture-analyzer-agent) → `architecture_patterns.md`
**PHASE 4:** Dependencies & Integration Analysis (via dependencies-analyzer-agent) → `dependencies_integrations.md`

**FINAL OUTPUT:** Generate comprehensive `APPLICATION_OVERVIEW.md`

Carefully read and execute the instructions in the following files IN SEQUENCE, following their numbered phases. Only proceed to the next numbered phase once the previous phase has been executed.

Instructions to follow in sequence:

# PHASE 0: Auto-Discover Specification Documents

## Step 1: Check Command Parameters

Check if the user provided any of the following:

**Required Document Paths:**
- `--fsd <path>` - Path to Functional Specification Document
- `--tsd <path>` - Path to Technical Specification Document  
- `--mcm <path>` - Path to Meta Cognitive Model (JSON)

**Optional Configuration:**
- `--base-path <path>` - Project base directory (where comprehend/ and scan_assessment_reports/ folders are)
- `--output <path>` - Output directory for generated reports

**Environment Variables:**
- `$LEAP_PROJECT_BASE` - Default project base path if not specified

If ALL required inputs (FSD, TSD, MCM) were provided explicitly, **SKIP to PHASE 1** directly.

Otherwise, proceed to auto-discovery using the base path.

## Step 2: Auto-Discover from Default Location

If any inputs are missing, perform auto-discovery from the project's configuration:

**Path Resolution (in priority order):**
1. **`.legacyleap/metadata.json`** (BEST) — Every LegacyLeap project has this file. It contains pre-resolved absolute paths:
   - `project_path` → project base directory
   - `comprehend` → comprehend folder path  
   - `scan_assessment_reports` → MCM and scan outputs folder path
   - `legacy_code` → legacy source code path
2. `--base-path` parameter provided by user
3. `$LEAP_PROJECT_BASE` environment variable
4. Current working directory (`pwd`)

When opened in the IDE (Cursor/agent), the working directory is the project root, so `.legacyleap/metadata.json` will always be available.

**Required sub-folders:** `comprehend/` and `scan_assessment_reports/`

**Expected Folder Structure (complete):**
```
<PROJECT_BASE>/                                (project root, e.g. NAS-LDAP/)
├── .legacyleap/                               (project configuration)
│   ├── metadata.json                          (*** ALL paths are here ***)
│   ├── leap.properties                        (service configs, credentials)
│   └── system_config.json                     (system description, feedback)
├── comprehend/                                (generated documentation)
│   ├── functional_doc/                        (FSD versions — independent)
│   │   ├── v_0/
│   │   │   └── Latest_FSD_Document/
│   │   │       ├── Latest_fsd.md              (markdown — for agent analysis)
│   │   │       ├── Latest_fsd.json            (structured JSON — for programmatic use)
│   │   │       ├── Latest_fsd.docx            (Word — for client delivery)
│   │   │       └── mermaid_diagram_images/    (.mmd sources + .png renders)
│   │   └── v_1/                               (← latest: highest version number)
│   │       └── Latest_FSD_Document/
│   │           ├── Latest_fsd.md
│   │           ├── Latest_fsd.json
│   │           ├── Latest_fsd.docx
│   │           └── mermaid_diagram_images/
│   └── technical_doc/                         (TSD versions — independent from FSD)
│       └── v_0/
│           └── Latest_TSD_Document/
│               ├── Latest_tsd.md              (markdown)
│               ├── Latest_tsd.json            (structured JSON)
│               ├── Latest_tsd.docx            (Word)
│               ├── mermaid_diagram_images/    (.mmd + .png)
│               └── media/                     (embedded images with hash names)
├── legacy_code/                               (actual source code)
│   └── <legacy_project_name>/                 (e.g. IdapUtils/)
│       ├── src/main/java/...                  (Java source files)
│       ├── build.gradle / pom.xml             (build config)
│       ├── .classpath, .project               (IDE config)
│       └── .git/                              (source repo)
├── scan_assessment_reports/                   (MCM and scan outputs)
│   ├── meta_cognitive_model.json              (MCM — single file for project)
│   ├── mcm_documents.json                     (enriched content per part)
│   ├── mcm_visualization.html                 (visual graph)
│   ├── bom_analysis_report.txt                (BOM analysis)
│   ├── scan_results/                          (detailed scan outputs)
│   ├── code/                                  (code analysis artifacts)
│   └── .checkpoints/                          (pipeline checkpoints)
├── microservice/                              (microservice outputs)
├── modernize/                                 (modernized code)
├── metrics/                                   (analysis metrics)
├── safety_nets/                               (safety net tests)
├── leap-os/                                   (LeapOS config for this project)
│   └── config.yml                             (profile, feature flags)
├── legacyleap.json                            (model/TUI settings)
└── tmp/                                       (temporary files)
```

**Key structural notes:**
- **`.legacyleap/metadata.json` is the single source of truth** for all folder paths
- FSD and TSD are in **separate** sub-folders (`functional_doc/` and `technical_doc/`) with **independent versioning**
- Versions are named `v_0`, `v_1`, `v_2`... — always pick the **highest number**
- Each doc version has **three formats**: `.md` (agent analysis), `.json` (programmatic), `.docx` (client delivery)
- MCM folder is `scan_assessment_reports/` (not scan_assessment_results)
- `legacy_code/` contains actual source code for **correctness validation**
- Mermaid diagrams may have `.mmd` sources without rendered `.png` — agents should read `.mmd` directly

### Step 2.1: Determine Base Path

```bash
# =================================================================
# STEP 1: Determine project base path and ALL folder paths
# Priority order:
#   1. .legacyleap/metadata.json (BEST — has all resolved paths)
#   2. User provided via --base-path parameter
#   3. Environment variable $LEAP_PROJECT_BASE
#   4. Current working directory
# =================================================================

METADATA_FILE=""
for candidate in "$(pwd)/.legacyleap/metadata.json" \
                 "${USER_PROVIDED_BASE:-.}/.legacyleap/metadata.json" \
                 "${LEAP_PROJECT_BASE:-.}/.legacyleap/metadata.json"; do
    if [ -f "$candidate" ]; then
        METADATA_FILE="$candidate"
        break
    fi
done

if [ -n "$METADATA_FILE" ]; then
    echo "✅ Found .legacyleap/metadata.json — reading ALL paths from project metadata"
    
    # Extract ALL folder paths from metadata.json
    # metadata.json stores absolute paths for every project folder
    python3 -c "
import json, os
with open('$METADATA_FILE') as f:
    meta = json.load(f)

# Core paths (always present)
paths = {
    'PROJECT_BASE':       meta.get('project_path', ''),
    'COMPREHEND_PATH':    meta.get('comprehend', ''),
    'SCAN_REPORTS_PATH':  meta.get('scan_assessment_reports', ''),
    'LEGACY_CODE_PATH':   meta.get('legacy_code', ''),
    'MICROSERVICE_PATH':  meta.get('microservice', ''),
    'MODERNIZE_PATH':     meta.get('modernize', ''),
    'METRICS_PATH':       meta.get('metrics', ''),
    'SAFETY_NETS_PATH':   meta.get('safety_nets', ''),
}

# Project metadata
print(f'PROJECT_NAME={meta.get(\"name\", \"Unknown\")}')
print(f'LEGACY_PROJECT_NAME={meta.get(\"legacy_project_name\", \"\")}')
print(f'LEGACY_BACKEND={meta.get(\"legacy_backend\", \"\")}')
print(f'LEGACY_FRAMEWORK={meta.get(\"legacy_framework\", \"\")}')
print(f'APP_TYPE={meta.get(\"legacy_application_type\", \"\")}')

for key, val in paths.items():
    exists = '✅' if val and os.path.isdir(val) else '❌'
    print(f'{exists} {key}={val}')
"
    
    # Read into shell variables
    PROJECT_BASE=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['project_path'])")
    COMPREHEND_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['comprehend'])")
    SCAN_REPORTS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE'))['scan_assessment_reports'])")
    LEGACY_CODE_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_code',''))")
    MICROSERVICE_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('microservice',''))")
    MODERNIZE_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('modernize',''))")
    METRICS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('metrics',''))")
    SAFETY_NETS_PATH=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('safety_nets',''))")
    LEGACY_PROJECT_NAME=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_project_name',''))")
    LEGACY_BACKEND=$(python3 -c "import json; print(json.load(open('$METADATA_FILE')).get('legacy_backend',''))")
    
else
    echo "⚠️  No .legacyleap/metadata.json found — falling back to manual resolution"
    
    if [ -n "$USER_PROVIDED_BASE" ]; then
        PROJECT_BASE="$USER_PROVIDED_BASE"
    elif [ -n "$LEAP_PROJECT_BASE" ]; then
        PROJECT_BASE="$LEAP_PROJECT_BASE"
    else
        PROJECT_BASE="$(pwd)"
    fi
    
    COMPREHEND_PATH="${PROJECT_BASE}/comprehend"
    SCAN_REPORTS_PATH="${PROJECT_BASE}/scan_assessment_reports"
    LEGACY_CODE_PATH="${PROJECT_BASE}/legacy_code"
    MICROSERVICE_PATH="${PROJECT_BASE}/microservice"
    MODERNIZE_PATH="${PROJECT_BASE}/modernize"
    METRICS_PATH="${PROJECT_BASE}/metrics"
    SAFETY_NETS_PATH="${PROJECT_BASE}/safety_nets"
    LEGACY_PROJECT_NAME=""
    LEGACY_BACKEND=""
fi

# =================================================================
# STEP 2: Discover FSD and TSD (latest version by version number)
# =================================================================

FSD_BASE="${COMPREHEND_PATH}/functional_doc"
TSD_BASE="${COMPREHEND_PATH}/technical_doc"

# Verify core folders exist
for folder_name in "comprehend" "scan_assessment_reports" "legacy_code"; do
    eval folder_path=\$"$(echo $folder_name | tr '[:lower:]' '[:upper:]')_PATH"
    # Use the paths we already have
done

[ ! -d "$COMPREHEND_PATH" ] && echo "❌ comprehend/ not found at: ${COMPREHEND_PATH}"
[ ! -d "$SCAN_REPORTS_PATH" ] && echo "❌ scan_assessment_reports/ not found at: ${SCAN_REPORTS_PATH}"
[ ! -d "$LEGACY_CODE_PATH" ] && echo "⚠️  legacy_code/ not found at: ${LEGACY_CODE_PATH}"

# Find latest version folder by VERSION NUMBER (v_0, v_1, v_2 → pick highest)
# Sort numerically by the number after 'v_', not by modification time
LATEST_FSD_VERSION=$(ls -d ${FSD_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1)
LATEST_TSD_VERSION=$(ls -d ${TSD_BASE}/v_*/ 2>/dev/null | sort -t_ -k2 -n | tail -1)

echo "FSD versions available: $(ls -d ${FSD_BASE}/v_*/ 2>/dev/null | xargs -I{} basename {})"
echo "FSD latest: $(basename ${LATEST_FSD_VERSION:-none})"
echo "TSD versions available: $(ls -d ${TSD_BASE}/v_*/ 2>/dev/null | xargs -I{} basename {})"
echo "TSD latest: $(basename ${LATEST_TSD_VERSION:-none})"
```

**Discovery Strategy:**
1. **PRIMARY: Read `.legacyleap/metadata.json`** — this file is auto-created when the project is set up via LegacyLeap. It contains pre-resolved absolute paths for ALL project folders: `project_path`, `comprehend`, `scan_assessment_reports`, `legacy_code`, `microservice`, `modernize`, `metrics`, `safety_nets`, plus project metadata (`name`, `legacy_project_name`, `legacy_backend`, `legacy_framework`, etc.)
2. **FALLBACK:** If metadata.json doesn't exist, use `--base-path` parameter, `$LEAP_PROJECT_BASE` env var, or current working directory
3. FSD versions are in `comprehend/functional_doc/v_N/` — pick highest version number (v_0, v_1, v_2...)
4. TSD versions are in `comprehend/technical_doc/v_N/` — pick highest version number (independent from FSD)
5. MCM is at project level in `scan_assessment_reports/` (not version-specific)
6. Legacy source code is at `legacy_code/<project_name>/` (project_name from metadata.json)

### Step 2.2: Discover Meta Cognitive Model (MCM) and Scan Reports

Look for: `meta_cognitive_model.json` in the **scan_assessment_reports** folder at **project level** (NOT in version folder)

```bash
# MCM is at project level, not version-specific
MCM_PATH="${SCAN_REPORTS_PATH}/meta_cognitive_model.json"
MCM_DOCS_PATH="${SCAN_REPORTS_PATH}/mcm_documents.json"
BOM_REPORT_PATH="${SCAN_REPORTS_PATH}/bom_analysis_report.txt"
MCM_VIZ_PATH="${SCAN_REPORTS_PATH}/mcm_visualization.html"

# Scan results sub-folder (may contain additional analysis)
SCAN_RESULTS_PATH="${SCAN_REPORTS_PATH}/scan_results"
SCAN_CODE_PATH="${SCAN_REPORTS_PATH}/code"

echo "=== Scan Assessment Reports ==="
[ -f "$MCM_PATH" ]       && echo "✅ MCM: $MCM_PATH"       || echo "❌ MCM not found"
[ -f "$MCM_DOCS_PATH" ]  && echo "✅ MCM Docs: $MCM_DOCS_PATH"  || echo "⚠️  MCM Docs not found"
[ -f "$BOM_REPORT_PATH" ] && echo "✅ BOM Report: $BOM_REPORT_PATH" || echo "⚠️  BOM Report not found"
[ -d "$SCAN_RESULTS_PATH" ] && echo "✅ Scan Results: $SCAN_RESULTS_PATH" || echo "⚠️  Scan Results not found"
[ -d "$SCAN_CODE_PATH" ]    && echo "✅ Scan Code: $SCAN_CODE_PATH"       || echo "⚠️  Scan Code not found"
```

**Expected Path Pattern:** `<PROJECT_BASE>/scan_assessment_reports/meta_cognitive_model.json`

**Important:** MCM is **NOT version-specific**. There is a single MCM file at the project level that represents the overall application structure. The companion file `mcm_documents.json` contains enriched markdown content per part/assembly for deeper analysis.

If found, set: `MCM_PATH = ${SCAN_REPORTS_PATH}/meta_cognitive_model.json`

### Step 2.3: Discover Latest FSD

Look for FSD in: `Latest_FSD_Document` folder inside the **highest version number** under `comprehend/functional_doc/`

Each version folder contains **three formats** of the same document:
- `.md` — Markdown (primary for agent analysis)
- `.json` — Structured JSON (for programmatic parsing)
- `.docx` — Word document (for human/client delivery)

```bash
# FSD folder is inside the latest functional_doc version
FSD_FOLDER="${LATEST_FSD_VERSION}/Latest_FSD_Document"

if [ -d "$FSD_FOLDER" ]; then
    # All three formats should be present
    FSD_MD_PATH="${FSD_FOLDER}/Latest_fsd.md"
    FSD_JSON_PATH="${FSD_FOLDER}/Latest_fsd.json"
    FSD_DOCX_PATH="${FSD_FOLDER}/Latest_fsd.docx"
    
    # Primary: Use .md for agent analysis
    if [ -f "$FSD_MD_PATH" ]; then
        FSD_PATH="$FSD_MD_PATH"
    else
        # Fallback: find any .md file
        FSD_PATH=$(find ${FSD_FOLDER} -maxdepth 1 -type f -iname "*.md" 2>/dev/null | head -1)
    fi
    
    # Check diagram assets
    FSD_DIAGRAMS_DIR="${FSD_FOLDER}/mermaid_diagram_images"
    
    echo "=== FSD Discovery ($(basename ${LATEST_FSD_VERSION})) ==="
    [ -f "$FSD_MD_PATH" ]   && echo "✅ FSD .md:   $FSD_MD_PATH"   || echo "❌ FSD .md not found"
    [ -f "$FSD_JSON_PATH" ] && echo "✅ FSD .json: $FSD_JSON_PATH" || echo "⚠️  FSD .json not found"
    [ -f "$FSD_DOCX_PATH" ] && echo "✅ FSD .docx: $FSD_DOCX_PATH" || echo "⚠️  FSD .docx not found"
    if [ -d "$FSD_DIAGRAMS_DIR" ]; then
        FSD_PNG_COUNT=$(find "$FSD_DIAGRAMS_DIR" -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
        FSD_MMD_COUNT=$(find "$FSD_DIAGRAMS_DIR" -name "*.mmd" 2>/dev/null | wc -l | tr -d ' ')
        echo "✅ Diagrams: ${FSD_PNG_COUNT} PNGs, ${FSD_MMD_COUNT} Mermaid sources"
    fi
else
    echo "❌ FSD folder not found: $FSD_FOLDER"
fi
```

**Expected Path Pattern:** `<base>/comprehend/functional_doc/<highest_v_N>/Latest_FSD_Document/Latest_fsd.md`

**Discovery Strategy:**
1. Navigate to `functional_doc/` inside comprehend
2. Pick the **highest version number** folder (v_0 < v_1 < v_2, sorted numerically)
3. Look for `Latest_FSD_Document/Latest_fsd.md` (primary for analysis)
4. Also note `.json` (structured companion) and `.docx` (client-ready) formats
5. Check `mermaid_diagram_images/` for `.mmd` source and `.png` renders

If found, set: `FSD_PATH = <discovered .md path>`

### Step 2.4: Discover Latest TSD

Look for TSD in: `Latest_TSD_Document` folder inside the **highest version number** under `comprehend/technical_doc/`

**Important:** TSD has its own independent versioning under `technical_doc/`, separate from FSD.

```bash
# TSD folder is inside the latest technical_doc version
TSD_FOLDER="${LATEST_TSD_VERSION}/Latest_TSD_Document"

if [ -d "$TSD_FOLDER" ]; then
    # All three formats should be present
    TSD_MD_PATH="${TSD_FOLDER}/Latest_tsd.md"
    TSD_JSON_PATH="${TSD_FOLDER}/Latest_tsd.json"
    TSD_DOCX_PATH="${TSD_FOLDER}/Latest_tsd.docx"
    
    # Primary: Use .md for agent analysis
    if [ -f "$TSD_MD_PATH" ]; then
        TSD_PATH="$TSD_MD_PATH"
    else
        # Fallback: find any .md file
        TSD_PATH=$(find ${TSD_FOLDER} -maxdepth 1 -type f -iname "*.md" 2>/dev/null | head -1)
    fi
    
    # Check diagram and media assets
    TSD_DIAGRAMS_DIR="${TSD_FOLDER}/mermaid_diagram_images"
    TSD_MEDIA_DIR="${TSD_FOLDER}/media"
    
    echo "=== TSD Discovery ($(basename ${LATEST_TSD_VERSION})) ==="
    [ -f "$TSD_MD_PATH" ]   && echo "✅ TSD .md:   $TSD_MD_PATH"   || echo "❌ TSD .md not found"
    [ -f "$TSD_JSON_PATH" ] && echo "✅ TSD .json: $TSD_JSON_PATH" || echo "⚠️  TSD .json not found"
    [ -f "$TSD_DOCX_PATH" ] && echo "✅ TSD .docx: $TSD_DOCX_PATH" || echo "⚠️  TSD .docx not found"
    if [ -d "$TSD_DIAGRAMS_DIR" ]; then
        TSD_PNG_COUNT=$(find "$TSD_DIAGRAMS_DIR" -name "*.png" 2>/dev/null | wc -l | tr -d ' ')
        TSD_MMD_COUNT=$(find "$TSD_DIAGRAMS_DIR" -name "*.mmd" 2>/dev/null | wc -l | tr -d ' ')
        echo "✅ Diagrams: ${TSD_PNG_COUNT} PNGs, ${TSD_MMD_COUNT} Mermaid sources"
    fi
    [ -d "$TSD_MEDIA_DIR" ] && echo "✅ Media folder: $(find "$TSD_MEDIA_DIR" -type f | wc -l | tr -d ' ') embedded images" || true
else
    echo "❌ TSD folder not found: $TSD_FOLDER"
fi
```

**Expected Path Pattern:** `<base>/comprehend/technical_doc/<highest_v_N>/Latest_TSD_Document/Latest_tsd.md`

**Discovery Strategy:**
1. Navigate to `technical_doc/` inside comprehend
2. Pick the **highest version number** folder (sorted numerically, independent from FSD)
3. Look for `Latest_TSD_Document/Latest_tsd.md` (primary for analysis)
4. Also note `.json` (structured companion) and `.docx` (client-ready) formats
5. Check `mermaid_diagram_images/` for diagrams and `media/` for embedded images

If found, set: `TSD_PATH = <discovered .md path>`

### Step 2.5: Discover Legacy Source Code

The legacy source code is essential for **correctness validation** — cross-referencing FSD/TSD/MCM claims against actual code.

```bash
echo "=== Legacy Code Discovery ==="

if [ -d "$LEGACY_CODE_PATH" ]; then
    # Find the actual project folder (usually named after legacy_project_name from metadata)
    if [ -n "$LEGACY_PROJECT_NAME" ] && [ -d "${LEGACY_CODE_PATH}/${LEGACY_PROJECT_NAME}" ]; then
        LEGACY_SRC_ROOT="${LEGACY_CODE_PATH}/${LEGACY_PROJECT_NAME}"
    else
        # Fallback: first subdirectory in legacy_code/
        LEGACY_SRC_ROOT=$(ls -d ${LEGACY_CODE_PATH}/*/ 2>/dev/null | head -1)
    fi
    
    if [ -n "$LEGACY_SRC_ROOT" ]; then
        echo "✅ Legacy project root: $LEGACY_SRC_ROOT"
        
        # Count source files by type
        JAVA_COUNT=$(find "$LEGACY_SRC_ROOT" -name "*.java" -not -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
        CS_COUNT=$(find "$LEGACY_SRC_ROOT" -name "*.cs" -not -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
        PY_COUNT=$(find "$LEGACY_SRC_ROOT" -name "*.py" -not -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')
        
        echo "   Java files: $JAVA_COUNT"
        echo "   C# files:   $CS_COUNT"
        echo "   Python files: $PY_COUNT"
        
        # Detect build system
        [ -f "${LEGACY_SRC_ROOT}/pom.xml" ]         && echo "   Build: Maven (pom.xml)"
        [ -f "${LEGACY_SRC_ROOT}/build.gradle" ]     && echo "   Build: Gradle (build.gradle)"
        [ -f "${LEGACY_SRC_ROOT}/build.gradle.kts" ] && echo "   Build: Gradle Kotlin (build.gradle.kts)"
        [ -f "${LEGACY_SRC_ROOT}/*.sln" ]            && echo "   Build: .NET (solution)"
        [ -f "${LEGACY_SRC_ROOT}/*.csproj" ]         && echo "   Build: .NET (project)"
        
        # List source files for cross-referencing
        echo "   Source files:"
        find "$LEGACY_SRC_ROOT" -name "*.java" -o -name "*.cs" -o -name "*.py" \
            | grep -v "/.git/" | sort | while read f; do
            echo "     - $(basename $f)"
        done
    else
        echo "⚠️  No project found inside legacy_code/"
    fi
else
    echo "⚠️  legacy_code/ not found — source code correctness checks will be limited"
fi
```

**Why Legacy Code Matters for Application Overview:**
The legacy source code allows agents to **validate** what FSD, TSD, and MCM claim:
- Do the classes/methods mentioned in MCM actually exist in the source?
- Are the business workflows described in FSD implemented in the code?
- Does the architecture described in TSD match the actual code structure?
- Are there source files not covered by MCM/FSD/TSD?

## Step 3: Verify Auto-Discovery Results

After auto-discovery, display the complete discovered state:

```
🔍 AUTO-DISCOVERY RESULTS:

Project: <PROJECT_NAME> (<APP_TYPE>)
Base Path: <PROJECT_BASE>
Backend: <LEGACY_BACKEND> / Framework: <LEGACY_FRAMEWORK>
Source: .legacyleap/metadata.json ✅ (or "manual fallback")

=== Core Documents ===
FSD (v_N): <FSD_PATH>           [.md ✅] [.json ✅] [.docx ✅]
TSD (v_N): <TSD_PATH>           [.md ✅] [.json ✅] [.docx ✅]
MCM:       <MCM_PATH>           ✅

=== Source Code ===
Legacy Code: <LEGACY_SRC_ROOT>
  Files: N Java | Build: Gradle/Maven

=== Scan Reports ===
MCM Docs:    <MCM_DOCS_PATH>    ✅/❌
BOM Report:  <BOM_REPORT_PATH>  ✅/❌
Scan Results: <SCAN_RESULTS_PATH> ✅/❌

=== Diagram Assets ===
FSD: N PNGs, N Mermaid sources
TSD: N PNGs, N Mermaid sources, N embedded media
```

## Step 4: Handle Missing Files

If ANY required file (FSD, TSD, MCM) is still missing after auto-discovery, prompt the user:

```
⚠️ Could not auto-discover all required files

Searched in: 
- .legacyleap/metadata.json: [Found/Not found]
- Project Base: <PROJECT_BASE>
- FSD: <COMPREHEND_PATH>/functional_doc/<latest_v_N>/Latest_FSD_Document/
- TSD: <COMPREHEND_PATH>/technical_doc/<latest_v_N>/Latest_TSD_Document/
- MCM: <SCAN_REPORTS_PATH>/

Missing:
[List missing files]

Please provide paths manually or ensure files are generated:
- FSD: run `bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh`
- TSD: run `bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh`
- MCM: run `bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh`
```

WAIT for the user to provide missing paths before proceeding.

## Step 5: Confirm and Proceed

Once all required files are available (FSD, TSD, MCM, and optionally legacy code), display:

```
✅ ALL INPUTS READY

Core Documents:
- FSD: [FSD_PATH] (version: v_N)
- TSD: [TSD_PATH] (version: v_N)
- MCM: [MCM_PATH]

Source Code (for correctness validation):
- Legacy Code: [LEGACY_SRC_ROOT] (N source files)

Proceeding to analysis...
```

## Step 6: Pre-Flight Content Quality Check (MANDATORY)

Before starting analysis, scan all input documents for known issues. This prevents agents from producing empty or broken output.

### 6.1: Detect "Content Generation Failed" Sections

Scan both FSD and TSD for the literal text `Content generation failed` (case-insensitive). This is a known issue from the document generation pipeline.

```bash
# Check FSD for generation failures
grep -in "content generation failed" "$FSD_PATH" || echo "✅ FSD: No generation failures"

# Check TSD for generation failures
grep -in "content generation failed" "$TSD_PATH" || echo "✅ TSD: No generation failures"
```

If found, **log which sections failed** (e.g., "Glossary") and instruct all agents to:
- Note the failed section in their report as a **known gap**
- Skip analysis of that section rather than producing empty/broken tables
- Add a recommendation to regenerate the failed section

### 6.2: Detect Broken Diagram References

FSD and TSD reference diagram images as `![...](./mermaid_diagram_images/diagram_N_diagram.png)`. These PNG files may NOT exist — only Mermaid source `.mmd` files may be present.

```bash
# Check if diagram PNGs actually exist (FSD)
FSD_DIR=$(dirname "$FSD_PATH")
if [ -d "${FSD_DIR}/mermaid_diagram_images" ]; then
    PNG_COUNT=$(find "${FSD_DIR}/mermaid_diagram_images" -name "*.png" 2>/dev/null | wc -l)
    MMD_COUNT=$(find "${FSD_DIR}/mermaid_diagram_images" -name "*.mmd" 2>/dev/null | wc -l)
    echo "FSD Diagrams: ${PNG_COUNT} PNGs, ${MMD_COUNT} Mermaid sources"
fi

# Check TSD diagrams
TSD_DIR=$(dirname "$TSD_PATH")
if [ -d "${TSD_DIR}/mermaid_diagram_images" ]; then
    PNG_COUNT=$(find "${TSD_DIR}/mermaid_diagram_images" -name "*.png" 2>/dev/null | wc -l)
    MMD_COUNT=$(find "${TSD_DIR}/mermaid_diagram_images" -name "*.mmd" 2>/dev/null | wc -l)
    echo "TSD Diagrams: ${PNG_COUNT} PNGs, ${MMD_COUNT} Mermaid sources"
fi
```

If `.mmd` files exist but `.png` files are missing:
- Instruct architecture-analyzer to **read the `.mmd` files directly** for architecture diagram understanding
- Note the broken image references in the report
- Recommend rendering mermaid diagrams to PNG

### 6.3: Validate MCM JSON Structure

```bash
# Verify MCM has required top-level keys
python3 -c "
import json, sys
with open('$MCM_PATH') as f:
    mcm = json.load(f)
required = ['nodes', 'relationships', 'metadata']
for key in required:
    status = '✅' if key in mcm else '❌'
    print(f'{status} {key}')
if 'nodes' in mcm:
    parts = len(mcm['nodes'].get('parts', []))
    assemblies = len(mcm['nodes'].get('assemblies', []))
    print(f'   Parts: {parts}, Assemblies: {assemblies}')
rels = len(mcm.get('relationships', []))
print(f'   Relationships: {rels}')
" 2>/dev/null || echo "⚠️ Python not available — skip MCM validation"
```

### 6.4: Check for TSD Title Mismatch

The TSD document title may incorrectly say "Functional Specification Document (FSD)" due to template issues. Detect and warn:

```bash
head -20 "$TSD_PATH" | grep -i "functional specification" && \
    echo "⚠️ WARNING: TSD file has incorrect title — says 'Functional Specification' but is a Technical Specification. Agents should verify content, not title."
```

### 6.5: Display Pre-Flight Results

```
📋 PRE-FLIGHT QUALITY CHECK:

Content Failures:
- FSD Glossary: ❌ "Content generation failed" (agents will skip this section)
- Other sections: ✅ All generated

Diagram Status:
- FSD: [n] Mermaid sources, [n] PNG renders (⚠️ PNGs missing — agents will read .mmd directly)
- TSD: [n] Mermaid sources, [n] PNG renders

MCM Validation:
- Structure: ✅ Valid (nodes, relationships, metadata present)
- Parts: [n], Assemblies: [n], Relationships: [n]

Known Issues:
- [list any detected issues]

Proceeding with analysis (agents aware of known gaps)...
```

**Pass these pre-flight findings to ALL agents** so they handle gaps gracefully rather than failing silently.

# PHASE 1: Application Structure Analysis

Now perform application structure analysis based on the discovered/provided FSD, TSD, and MCM.

## Step 1: Verify Required Inputs

At this point, you should have:

1. **FSD_PATH** - Path to Functional Specification Document (.md)
2. **FSD_JSON_PATH** - Path to FSD structured JSON (optional, for programmatic parsing)
3. **TSD_PATH** - Path to Technical Specification Document (.md)
4. **TSD_JSON_PATH** - Path to TSD structured JSON (optional, for programmatic parsing)
5. **MCM_PATH** - Path to Meta Cognitive Model JSON
6. **MCM_DOCS_PATH** - Path to MCM documents JSON (optional, enriched content per part)
7. **LEGACY_SRC_ROOT** - Path to legacy source code root (for correctness validation)
8. **Output Directory** (optional) - Where to write reports (default: `workspace/application-overview/`)

All paths are now confirmed and available.

## Step 2: Delegate to Application Structure Analyzer Agent

Once you have all required inputs, invoke the **application-structure-analyzer-agent**.

**Agent Name:** `application-structure-analyzer-agent`

**Agent Location:** This agent is located in the `application_overview_agents` directory. The exact path may vary depending on your LeapOS installation and profile configuration.

**Inputs to Agent:**
- FSD: Read from [FSD_PATH]
- TSD: Read from [TSD_PATH]
- MCM: Read from [MCM_PATH]
- MCM Docs: Read from [MCM_DOCS_PATH] (if available)
- Legacy Source: [LEGACY_SRC_ROOT] (for correctness cross-referencing)
- Output Directory: [OUTPUT_DIR] (default: `workspace/application-overview/`)

**Expected Output:** `application_structure.md`

Execute the application structure analysis as specified in the agent definition.

## Step 3: Confirm Completion

Once application_structure.md has been created, display:

```
✅ PHASE 1 COMPLETE: Application Structure Analysis

Report generated: [path to application_structure.md]

Summary:
- Total Components (from MCM): [count]
- Functional Areas: [list]
- Main Modules: [count]
- Layers Identified: [list]

NEXT STEP 👉 Proceed to PHASE 2: Technology Stack Analysis
```

# PHASE 2: Technology Stack Analysis

Now we need to analyze the technology stack, frameworks, libraries, and platform dependencies based on the TSD and MCM.

## Step 1: Delegate to Technology Stack Analyzer Agent

Invoke the **tech-stack-analyzer-agent**.

**Agent Name:** `tech-stack-analyzer-agent`

**Agent Location:** This agent is located in the `application_overview_agents` directory. The exact path may vary depending on your LeapOS installation and profile configuration.

**Inputs to Agent:**
- TSD: Read from [TSD_PATH]
- MCM: Read from [MCM_PATH]
- FSD: Read from [FSD_PATH] (for context if needed)
- Legacy Source: [LEGACY_SRC_ROOT] (to verify tech stack from actual build files/imports)
- Output Directory: [OUTPUT_DIR] (default: `workspace/application-overview/`)

**Expected Output:** `tech_stack_analysis.md`

Execute the tech stack analysis as specified in the agent definition.

## Step 2: Confirm Completion

Once tech_stack_analysis.md has been created, display:

```
✅ PHASE 2 COMPLETE: Technology Stack Analysis

Report generated: [path to tech_stack_analysis.md]

Summary:
- Primary Language(s): [list]
- Frameworks: [list]
- Total Dependencies: [count]
- Platform: [platform]

NEXT STEP 👉 Proceed to PHASE 3: Architecture Pattern Analysis
```

# PHASE 3: Architecture Pattern Analysis

Now we need to identify architectural patterns, design principles, and structural organization based on TSD and MCM.

## Step 1: Delegate to Architecture Analyzer Agent

Invoke the **architecture-analyzer-agent**.

**Agent Name:** `architecture-analyzer-agent`

**Agent Location:** This agent is located in the `application_overview_agents` directory. The exact path may vary depending on your LeapOS installation and profile configuration.

**Inputs to Agent:**
- TSD: Read from [TSD_PATH]
- MCM: Read from [MCM_PATH]
- FSD: Read from [FSD_PATH] (for functional context)
- Legacy Source: [LEGACY_SRC_ROOT] (to verify architecture from actual code structure)
- application_structure.md (from Phase 1)
- tech_stack_analysis.md (from Phase 2)
- Output Directory: [OUTPUT_DIR] (default: `workspace/application-overview/`)

**Expected Output:** `architecture_patterns.md`

Execute the architecture analysis as specified in the agent definition.

## Step 2: Confirm Completion

Once architecture_patterns.md has been created, display:

```
✅ PHASE 3 COMPLETE: Architecture Pattern Analysis

Report generated: [path to architecture_patterns.md]

Summary:
- Architectural Style: [style]
- Design Patterns: [count]
- Layering Approach: [approach]
- Key Patterns: [list]

NEXT STEP 👉 Proceed to PHASE 4: Dependencies & Integration Analysis
```

# PHASE 4: Dependencies & Integration Analysis

Now we need to analyze external dependencies, integrations, APIs, and third-party services based on TSD and MCM.

## Step 1: Delegate to Dependencies Analyzer Agent

Invoke the **dependencies-analyzer-agent**.

**Agent Name:** `dependencies-analyzer-agent`

**Agent Location:** This agent is located in the `application_overview_agents` directory. The exact path may vary depending on your LeapOS installation and profile configuration.

**Inputs to Agent:**
- TSD: Read from [TSD_PATH]
- MCM: Read from [MCM_PATH]
- FSD: Read from [FSD_PATH] (for functional context)
- Legacy Source: [LEGACY_SRC_ROOT] (to verify dependencies from actual build files/imports)
- tech_stack_analysis.md (from Phase 2)
- Output Directory: [OUTPUT_DIR] (default: `workspace/application-overview/`)

**Expected Output:** `dependencies_integrations.md`

Execute the dependencies analysis as specified in the agent definition.

## Step 2: Confirm Completion

Once dependencies_integrations.md has been created, display:

```
✅ PHASE 4 COMPLETE: Dependencies & Integration Analysis

Report generated: [path to dependencies_integrations.md]

Summary:
- External Dependencies: [count]
- Third-Party Services: [count]
- API Integrations: [count]
- Database Systems: [list]

NEXT STEP 👉 Proceed to PHASE 5: Synthesize Application Overview Report
```

# PHASE 5: Synthesize Comprehensive Application Overview Report

Now that all four sub-analyses are complete, synthesize them into one comprehensive application overview report.

## Step 1: Read All Sub-Reports

Read the following reports in their entirety:
1. `application_structure.md`
2. `tech_stack_analysis.md`
3. `architecture_patterns.md`
4. `dependencies_integrations.md`

## Step 2: Synthesize Comprehensive Report

Create a comprehensive `APPLICATION_OVERVIEW.md` that consolidates findings from all four sub-reports.

### CRITICAL: Report Quality Requirements

Before generating the report, apply these mandatory quality standards:

#### Anti-Duplication Rules (MANDATORY)

| Rule | Description | Example Violation to Avoid |
|------|-------------|---------------------------|
| **Single Metric Location** | Each statistic appears ONCE | Don't repeat "15 microservices" in multiple sections |
| **No Repeated Tech Lists** | Tech stack appears in Section 2 only | Don't list frameworks in Executive Summary AND Tech Stack |
| **Consolidated Dependencies** | Dependencies in Section 5 only | Don't list libraries in multiple sections |
| **Cross-Reference, Don't Copy** | Use "See Section X" for related info | Don't restate architecture patterns in multiple places |

#### Section Ownership (Who Owns What)

| Information Type | Authoritative Section | Other Sections |
|-----------------|----------------------|----------------|
| File Counts & Structure | Section 2 (Codebase) | Reference only |
| Technology Stack | Section 3 | Reference only |
| Architecture Patterns | Section 4 | Reference only |
| Dependencies | Section 5 | Reference only |
| Recommendations | Conclusion | Reference only |

#### Table-First Formatting Rules

**MANDATORY Table Format For:**
- All metric summaries (file counts, component counts, etc.)
- Technology stack inventories
- Architecture pattern listings
- Dependency lists
- Integration points

**Narrative Allowed Only For:**
- Executive Summary context (max 3 short paragraphs)
- Conclusion (max 2 paragraphs)
- Complex architectural explanations

#### Length Constraints

| Section | Maximum Length |
|---------|---------------|
| Executive Summary | 200 words + metrics table |
| Each Subsection | 100 words + tables |
| Conclusion | 150 words |
| **Total Report** | Aim for conciseness and clarity |

### Report Structure

```markdown
# Application Overview Report

**Application:** [Application Name] | **Date:** [Current Date] | **Analyst:** Application Overview Command

| Aspect | Details |
|--------|---------|
| Primary Language(s) | [Languages] |
| Primary Framework(s) | [Frameworks] |
| Application Type | [Web/Desktop/Mobile/API/etc.] |

---

## Executive Summary

[Maximum 3 short paragraphs: (1) Application purpose and scope, (2) Key technical characteristics, (3) Overall assessment. No detailed statistics here—they go in the tables below.]

### Application Metrics

| Metric | Value |
|--------|-------|
| Total Files | [count] |
| Lines of Code | [count] |
| Primary Language(s) | [list] |
| Main Components | [count] |
| External Dependencies | [count] |
| Architecture Style | [style] |

### Quick Stats

| Category | Count |
|----------|-------|
| Modules/Packages | [n] |
| Classes/Components | [n] |
| Functions/Methods | [n] |
| Configuration Files | [n] |
| Test Files | [n] |

---

## 1. Application Purpose & Scope

### 1.1 Application Type

| Aspect | Description |
|--------|-------------|
| Application Category | [Web App / API / Desktop / Mobile / CLI / etc.] |
| Primary Use Case | [Brief description] |
| Target Users | [End users / Developers / Internal / etc.] |

### 1.2 Core Functionality

| Feature Area | Description |
|--------------|-------------|
| [Area 1] | [Description] |
| [Area 2] | [Description] |
| [Area 3] | [Description] |

**Detailed Report:** `application_structure.md`

---

## 2. Codebase Structure

### 2.1 Directory Organization

| Directory | Purpose | File Count |
|-----------|---------|------------|
| [/src] | [Source code] | [n] |
| [/tests] | [Test files] | [n] |
| [/config] | [Configuration] | [n] |
| [/docs] | [Documentation] | [n] |

### 2.2 File Distribution

| File Type | Count | Percentage |
|-----------|-------|------------|
| [.js/.ts] | [n] | [X]% |
| [.py] | [n] | [X]% |
| [.java] | [n] | [X]% |
| [Config files] | [n] | [X]% |
| [Test files] | [n] | [X]% |
| **Total** | [n] | 100% |

### 2.3 Key Components

| Component | Location | Purpose | Size |
|-----------|----------|---------|------|
| [Component 1] | [path] | [Purpose] | [LOC] |
| [Component 2] | [path] | [Purpose] | [LOC] |
| [Component 3] | [path] | [Purpose] | [LOC] |

**Detailed Report:** `application_structure.md`

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Language | [Language] | [Version] | Primary development language |
| Runtime | [Runtime] | [Version] | Execution environment |
| Framework | [Framework] | [Version] | Application framework |

### 3.2 Frontend Technologies (if applicable)

| Technology | Version | Purpose |
|------------|---------|---------|
| [React/Angular/Vue] | [Version] | UI Framework |
| [CSS Framework] | [Version] | Styling |
| [State Management] | [Version] | State handling |

### 3.3 Backend Technologies (if applicable)

| Technology | Version | Purpose |
|------------|---------|---------|
| [Framework] | [Version] | Backend framework |
| [ORM] | [Version] | Database access |
| [API Framework] | [Version] | API development |

### 3.4 Development Tools

| Tool | Purpose |
|------|---------|
| [Build Tool] | Build automation |
| [Package Manager] | Dependency management |
| [Testing Framework] | Testing |
| [Linter] | Code quality |

**Detailed Report:** `tech_stack_analysis.md`

---

## 4. Architecture & Design Patterns

### 4.1 Architectural Style

| Aspect | Details |
|--------|---------|
| Architecture Type | [Monolithic / Microservices / Layered / etc.] |
| Design Approach | [MVC / MVVM / Clean / Hexagonal / etc.] |
| Communication Style | [REST / GraphQL / Event-Driven / etc.] |

### 4.2 Layering Structure

| Layer | Components | Responsibilities |
|-------|------------|------------------|
| [Presentation] | [Components] | [Responsibilities] |
| [Business Logic] | [Components] | [Responsibilities] |
| [Data Access] | [Components] | [Responsibilities] |
| [Infrastructure] | [Components] | [Responsibilities] |

### 4.3 Design Patterns Identified

| Pattern | Usage Location | Purpose |
|---------|---------------|---------|
| [Singleton] | [Location] | [Purpose] |
| [Factory] | [Location] | [Purpose] |
| [Repository] | [Location] | [Purpose] |
| [Dependency Injection] | [Location] | [Purpose] |

### 4.4 Code Organization Principles

| Principle | Implementation | Adherence |
|-----------|----------------|-----------|
| [Single Responsibility] | [How implemented] | ✅/⚠️/❌ |
| [Separation of Concerns] | [How implemented] | ✅/⚠️/❌ |
| [DRY] | [How implemented] | ✅/⚠️/❌ |

**Detailed Report:** `architecture_patterns.md`

---

## 5. Dependencies & Integrations

### 5.1 External Dependencies Summary

| Category | Count | Risk Level |
|----------|-------|------------|
| Production Dependencies | [n] | [Low/Medium/High] |
| Development Dependencies | [n] | [Low/Medium/High] |
| Total Dependencies | [n] | - |

### 5.2 Key Dependencies

| Dependency | Version | Purpose | Update Status |
|------------|---------|---------|---------------|
| [Dependency 1] | [Version] | [Purpose] | ✅ Current / ⚠️ Outdated |
| [Dependency 2] | [Version] | [Purpose] | ✅ Current / ⚠️ Outdated |
| [Dependency 3] | [Version] | [Purpose] | ✅ Current / ⚠️ Outdated |

### 5.3 Third-Party Services & APIs

| Service | Purpose | Integration Type |
|---------|---------|------------------|
| [Service 1] | [Purpose] | [REST/SDK/etc.] |
| [Service 2] | [Purpose] | [REST/SDK/etc.] |

### 5.4 Database Systems

| Database | Type | Purpose |
|----------|------|---------|
| [PostgreSQL] | [Relational] | [Primary data store] |
| [Redis] | [Cache] | [Session/cache storage] |

### 5.5 Communication Protocols

| Protocol | Usage | Components |
|----------|-------|------------|
| [HTTP/REST] | [API communication] | [Components] |
| [WebSockets] | [Real-time updates] | [Components] |
| [gRPC] | [Service-to-service] | [Components] |

**Detailed Report:** `dependencies_integrations.md`

---

## 6. Configuration & Environment

### 6.1 Configuration Files

| File | Purpose | Environment |
|------|---------|-------------|
| [config.json] | [Purpose] | [All] |
| [.env] | [Secrets] | [Dev/Prod] |

### 6.2 Environment Support

| Environment | Configuration | Status |
|-------------|---------------|--------|
| Development | [Config details] | ✅ Configured |
| Testing | [Config details] | ✅ Configured |
| Staging | [Config details] | ✅ Configured |
| Production | [Config details] | ✅ Configured |

---

## 7. Testing & Quality

### 7.1 Testing Framework

| Aspect | Details |
|--------|---------|
| Testing Framework | [Framework name and version] |
| Test Runner | [Runner name] |
| Coverage Tool | [Tool name] |

### 7.2 Test Distribution

| Test Type | Count | Coverage |
|-----------|-------|----------|
| Unit Tests | [n] | [X]% |
| Integration Tests | [n] | [X]% |
| E2E Tests | [n] | [X]% |
| **Total** | [n] | [X]% |

### 7.3 Code Quality Tools

| Tool | Purpose | Status |
|------|---------|--------|
| [Linter] | Code linting | ✅ Active |
| [Formatter] | Code formatting | ✅ Active |
| [Static Analyzer] | Static analysis | ✅ Active |

---

## 8. Build & Deployment

### 8.1 Build Process

| Aspect | Details |
|--------|---------|
| Build Tool | [Tool name] |
| Build Time | [Duration] |
| Output Type | [Artifacts] |

### 8.2 Deployment Configuration

| Aspect | Details |
|--------|---------|
| Deployment Type | [Docker/VM/Serverless/etc.] |
| CI/CD Platform | [Platform name] |
| Deployment Targets | [Targets] |

---

## 9. Security & Compliance

### 9.1 Security Measures

| Measure | Implementation | Status |
|---------|----------------|--------|
| Authentication | [Method] | ✅/⚠️/❌ |
| Authorization | [Method] | ✅/⚠️/❌ |
| Data Encryption | [Method] | ✅/⚠️/❌ |
| Input Validation | [Method] | ✅/⚠️/❌ |

### 9.2 Security Dependencies

| Tool | Purpose |
|------|---------|
| [Tool 1] | [Purpose] |
| [Tool 2] | [Purpose] |

---

## 10. Documentation

### 10.1 Available Documentation

| Document Type | Location | Status |
|---------------|----------|--------|
| README | [Path] | ✅/⚠️/❌ |
| API Documentation | [Path] | ✅/⚠️/❌ |
| Architecture Docs | [Path] | ✅/⚠️/❌ |
| Setup Guide | [Path] | ✅/⚠️/❌ |
| Deployment Guide | [Path] | ✅/⚠️/❌ |

---

## 11. System Health Summary

### 11.1 Strengths

| Strength | Details |
|----------|---------|
| [Strength 1] | [Description] |
| [Strength 2] | [Description] |

### 11.2 Areas for Attention

| Area | Current State | Impact |
|------|---------------|--------|
| [Area 1] | [State] | High/Medium/Low |
| [Area 2] | [State] | High/Medium/Low |

> **Note:** Detailed modernization recommendations, architecture upgrades, technology stack migration plans, and implementation roadmaps are provided in the separate **Modernization Recommendations** document (generated by the `modernization-recommender` agent).

---

## 12. Conclusion

[Maximum 2 paragraphs: (1) Overall application assessment and maturity level. (2) Key takeaways. Do NOT repeat statistics—reference appropriate sections. Do NOT include recommendations here—those are in the separate Modernization Recommendations document.]

**Maturity Assessment:** 🟢 Mature | 🟡 Developing | 🔴 Early Stage

---

## Appendices

### A: Report References

| Report | File | Purpose |
|--------|------|---------|
| Application Structure | `application_structure.md` | Component organization and functional areas |
| Tech Stack | `tech_stack_analysis.md` | Technologies and frameworks |
| Architecture | `architecture_patterns.md` | Design patterns and structure |
| Dependencies | `dependencies_integrations.md` | External dependencies and integrations |

### B: Methodology
[1-2 sentences on analysis approach. Do not elaborate.]

### C: Glossary
[Table format for terms. Maximum 10 most important terms.]

### D: Analysis Metadata

| Aspect | Details |
|--------|---------|
| Analysis Date | [Date] |
| Analyst | Application Overview Command |
| Application Version | [Version] |
```

## Step 3: Display Final Confirmation

Once APPLICATION_OVERVIEW.md has been created, display:

```
✅ APPLICATION OVERVIEW ANALYSIS COMPLETE

Input Files Used:
- FSD: [FSD_PATH]
- TSD: [TSD_PATH]
- MCM: [MCM_PATH]

Reports Generated:
1. Application Structure: [path to application_structure.md]
2. Tech Stack Analysis: [path to tech_stack_analysis.md]
3. Architecture Patterns: [path to architecture_patterns.md]
4. Dependencies & Integrations: [path to dependencies_integrations.md]
5. Application Overview: [path to APPLICATION_OVERVIEW.md]

---

## Application Summary

**Primary Language(s):** [Languages]
**Framework(s):** [Frameworks]
**Architecture Style:** [Style]
**Total Components:** [count from MCM]
**Dependencies:** [count]

---

**Use Cases:**
- Onboarding new developers
- Technical due diligence
- Architecture reviews
- Modernization planning
- Documentation baseline
- Spec validation and verification

The Application Overview provides a comprehensive snapshot of the application's technical landscape based on FSD, TSD, and MCM.

---

**Note:** Files were auto-discovered from: <PROJECT_BASE>

Discovery:
- FSD: comprehend/functional_doc/<latest_version>/Latest_FSD_Document/Latest_fsd.md
- TSD: comprehend/technical_doc/<latest_version>/Latest_TSD_Document/Latest_tsd.md
- MCM: scan_assessment_reports/meta_cognitive_model.json

To use custom paths, provide them explicitly:
/leap-os/application-overview --fsd <path> --tsd <path> --mcm <path>
```

---

### Execution Notes
- All four sub-agent analyses (PHASES 1-4) can potentially run in parallel if desired
- Auto-discovered file paths are displayed before analysis begins
- If any sub-agent analysis fails or cannot be completed due to missing specifications, note this in the final report with explanations
- The synthesis phase should not introduce new analysis—only consolidate and contextualize existing findings
- All reports should be stored in a consistent directory (suggest: `workspace/application-overview/`)
- Maintain consistent date format and metadata across all reports
- Primary analysis is based on FSD, TSD, and MCM documents
- **Legacy source code is used for correctness validation** — cross-referencing spec claims against actual code (classes, methods, imports, build config). This ensures the overview is grounded in reality, not just what the docs claim.

---

## MANDATORY: Pre-Submission Quality Checklist

Before finalizing the Application Overview report, verify compliance with these QA requirements:

### Deduplication Verification

| Check | Verification Action |
|-------|---------------------|
| ✅ Statistics appear once | Search for counts—each should appear in ONE section only |
| ✅ Tech stack not repeated | Technology lists only in Section 3 |
| ✅ Architecture not repeated | Pattern details only in Section 4 |
| ✅ Dependencies consolidated | All dependencies only in Section 5 |
| ✅ Recommendations consolidated | All recommendations only in Section 11 |

### Table Format Verification

| Check | Verification Action |
|-------|---------------------|
| ✅ Metrics in tables | No metrics buried in paragraphs |
| ✅ Tech stacks in tables | No technology lists as bullet points |
| ✅ Dependencies in tables | Single consolidated dependency table |
| ✅ Patterns in tables | Architecture patterns in table format |

### Length Verification

| Section | Maximum | Actual |
|---------|---------|--------|
| Executive Summary | 200 words | [ ] |
| Conclusion | 150 words | [ ] |
| Each subsection | 100 words | [ ] |
| Total narrative (non-table) | 30% of report | [ ] |

**If any check fails, revise before submission.**
