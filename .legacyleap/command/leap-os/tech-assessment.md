# Technical Debt Assessment

Run a complete technical debt assessment on the codebase. This command extracts project context, sets up directories, then delegates to **tech-assessment-orchestrator** which drives all phases end-to-end.

## Step 1: Extract Project Context

Read `.legacyleap/metadata.json` once and resolve ALL paths and configuration. Every sub-agent receives this context block — they must NOT re-read metadata.json themselves.

```bash
WORKSPACE=$(pwd)
echo "Workspace: $WORKSPACE"

# Verify metadata exists
if [ ! -f ".legacyleap/metadata.json" ]; then
  echo "FATAL: .legacyleap/metadata.json not found. Cannot proceed."
  exit 1
fi

# Extract all fields in a single Python call
eval "$(python3 -c "
import json, os, sys
m = json.load(open('.legacyleap/metadata.json'))
cwd = os.getcwd()

def resolve(val, default):
    if not val:
        return os.path.join(cwd, default)
    return val if os.path.isabs(val) else os.path.join(cwd, val)

lc = resolve(m.get('legacy_code'), 'legacy_code')
sr = resolve(m.get('scan_assessment_reports'), 'scan_assessment_reports')

print(f'PROJECT_NAME=\"{m.get(\"name\", \"unknown\")}\"')
print(f'PROJECT_ID=\"{m.get(\"project_id\", \"\")}\"')
print(f'TECHNOLOGY=\"{m.get(\"legacyleap_plugin\", \"\")}\"')
print(f'FRAMEWORK=\"{m.get(\"legacy_framework\", \"\")}\"')
print(f'APP_TYPE=\"{m.get(\"legacy_application_type\", \"\")}\"')
print(f'ARCHITECTURE=\"{m.get(\"current_architecture\", \"\")}\"')
print(f'LEGACY_CODE=\"{lc}\"')
print(f'SCAN_REPORTS=\"{sr}\"')
print(f'LEGACY_PROJECT_NAME=\"{m.get(\"legacy_project_name\", \"\")}\"')
print(f'LEGACY_FRONTEND=\"{m.get(\"legacy_frontend\", \"\")}\"')
print(f'LEGACY_BACKEND=\"{m.get(\"legacy_backend\", \"\")}\"')
")"

TECH_ASSESSMENT="${SCAN_REPORTS}/tech_assessment"
SOURCE_CODE_JSONS="${TECH_ASSESSMENT}/Source_code_JSONs"
MCM_JSON="${SCAN_REPORTS}/meta_cognitive_model.json"

echo ""
echo "=== PROJECT CONTEXT ==="
echo "  Project: $PROJECT_NAME (ID: $PROJECT_ID)"
echo "  Technology: $TECHNOLOGY | Framework: $FRAMEWORK | Type: $APP_TYPE"
echo "  Architecture: $ARCHITECTURE"
echo "  Legacy Code: $LEGACY_CODE"
echo "  Scan Reports: $SCAN_REPORTS"
echo "  Tech Assessment: $TECH_ASSESSMENT"
echo "  Source Code JSONs: $SOURCE_CODE_JSONS"
echo "  MCM JSON: $MCM_JSON"
echo "========================"
```

## Step 2: Verify Prerequisites

```bash
PREREQ_OK=true

if [ ! -d "$LEGACY_CODE" ]; then
  echo "WARNING: Legacy code directory not found: $LEGACY_CODE"
fi

if [ ! -f "$MCM_JSON" ]; then
  echo "WARNING: MCM JSON not found: $MCM_JSON (Neo4j will be used as primary source)"
fi

echo "Prerequisites checked."
```

## Step 3: Create Output Directories

```bash
mkdir -p "$TECH_ASSESSMENT/Source_code_JSONs"
mkdir -p "$SCAN_REPORTS/mcm_assessment"
mkdir -p ".legacyleap/.agent-state"
echo "Output directories created."
```

## Step 4: Initialize State Tracking

```bash
cat > .legacyleap/.agent-state/tech-assessment-state.json << 'STATEJSON'
{
  "started_at": "TIMESTAMP",
  "current_phase": "setup",
  "phases": {
    "setup": {"status": "completed"},
    "file_discovery": {"status": "pending"},
    "mcm_mapping": {"status": "pending"},
    "custom_rules": {"status": "pending"},
    "file_analysis": {"status": "pending"},
    "sheet_generation": {"status": "pending"},
    "output_generation": {"status": "pending"}
  }
}
STATEJSON

python3 -c "
import json
from datetime import datetime
s = json.load(open('.legacyleap/.agent-state/tech-assessment-state.json'))
s['started_at'] = datetime.now().isoformat() + 'Z'
json.dump(s, open('.legacyleap/.agent-state/tech-assessment-state.json', 'w'), indent=2)
"
echo "State tracking initialized."
```

## Step 5: Check Skip Flags

The user may have specified skip flags in their invocation. Check the message for:
- `--skip-analysis` — skip Phase 1, reuse existing `.combined.json` files
- `--skip-sheets` — skip sheet generation, reuse existing sheet JSONs
- `--skip-excel` — skip Excel report generation
- `--skip-dashboard` — skip HTML dashboard generation
- `--skip-mongo` — skip MongoDB ingestion
- `--non-interactive` — do not prompt for custom rules; reuse existing `custom_rules.json` if present, otherwise skip custom rules and continue with the defaults

Parse these from the user message. Default: run all phases.

## Step 6: Custom Rules

If `--non-interactive` is specified, do **not** ask the user anything:

- If `custom_rules.json` exists, set `CUSTOM_RULES_STATUS="loaded"` and continue directly to Step 8
- If `custom_rules.json` does **not** exist, set `CUSTOM_RULES_STATUS="skipped"` and continue directly to Step 8
- In non-interactive mode, the default analysis types remain `Bug`, `Code_Smell`, and `Cognitive_complexity`

Only when `--non-interactive` is **not** specified should you ask the user and stop after setup, as described below.

## Step 6a: Interactive Custom Rules — ASK THE USER AND END YOUR RESPONSE

Check for existing custom rules:
```bash
ls "$TECH_ASSESSMENT/custom_rules.json" 2>/dev/null
```

**If `custom_rules.json` exists**, your response MUST end with EXACTLY this text and nothing else after it:

> Setup complete. Found existing custom rules from a previous run.
> Please choose one:
> (a) **Use existing rules** — continue with saved custom rules
> (b) **New rules file** — provide a path to a new rules file (any format)
> (c) **Skip** — use only the 3 default types (Bug, Code_Smell, Cognitive_complexity)

**If `custom_rules.json` does NOT exist**, your response MUST end with EXACTLY this text and nothing else after it:

> Setup complete. The default analysis tracks: **Bug**, **Code_Smell**, **Cognitive_complexity**.
> Do you want to track additional issue types?
> - If **yes**, provide a path to a rules file (any format)
> - If **no**, say **skip**

**This interactive stop applies only when `--non-interactive` is NOT present.** In interactive mode, your message to the user ends here. Do NOT execute Steps 7-9 yet. Do NOT call any more tools. Do NOT delegate to any agents. STOP and send your response.

---

## Step 7: Process User's Custom Rules Reply (ONLY after user responds in interactive mode)

**You only reach this step when the user sends a new message replying to your custom rules question in interactive mode.**

- If a file path is provided: read the file, extract rules, save normalized JSON to `$TECH_ASSESSMENT/custom_rules.json`, set `CUSTOM_RULES_STATUS="loaded"`
- If "use existing" or "a": keep the existing file, set `CUSTOM_RULES_STATUS="loaded"`
- If "skip", "no", or "c": set `CUSTOM_RULES_STATUS="skipped"`

## Step 8: Build PROJECT_CONTEXT Block

Construct the following text block. This EXACT block must be included in EVERY sub-agent delegation prompt:

```
## Project Context (DO NOT re-read metadata.json — use these values)
- WORKSPACE: {value of $WORKSPACE}
- PROJECT_NAME: {value of $PROJECT_NAME}
- PROJECT_ID: {value of $PROJECT_ID}
- TECHNOLOGY: {value of $TECHNOLOGY}
- FRAMEWORK: {value of $FRAMEWORK}
- APP_TYPE: {value of $APP_TYPE}
- ARCHITECTURE: {value of $ARCHITECTURE}
- LEGACY_CODE_PATH: {value of $LEGACY_CODE}
- SCAN_REPORTS_PATH: {value of $SCAN_REPORTS}
- TECH_ASSESSMENT_PATH: {value of $TECH_ASSESSMENT}
- SOURCE_CODE_JSONS_PATH: {value of $SOURCE_CODE_JSONS}
- MCM_JSON_PATH: {value of $MCM_JSON}
- LEGACY_PROJECT_NAME: {value of $LEGACY_PROJECT_NAME}
- LEGACY_FRONTEND: {value of $LEGACY_FRONTEND}
- LEGACY_BACKEND: {value of $LEGACY_BACKEND}
- CUSTOM_RULES_STATUS: {value of $CUSTOM_RULES_STATUS — "loaded" or "skipped"}
```

## Step 9: Delegate to Orchestrator

Delegate the entire assessment to `@tech-assessment-orchestrator` with this prompt:

```
Run the complete Technical Debt Assessment pipeline.

{INSERT PROJECT_CONTEXT BLOCK HERE}

Skip flags: {list any --skip-* flags from user, or "none"}

Custom rules have already been handled by the command. If CUSTOM_RULES_STATUS is "loaded", the file is at {TECH_ASSESSMENT_PATH}/custom_rules.json. Do NOT ask the user about custom rules again.

Execute all phases as defined in your agent instructions:
- Phase 1: File discovery, MCM mapping, per-file analysis
- Phase 2: Sheet generation (sheets 1-4, 7-9 + dependencies)
- Phase 3: Excel report, HTML dashboard, MongoDB ingestion

Update state tracking at .legacyleap/.agent-state/tech-assessment-state.json after each phase.
```

Wait for the orchestrator to complete.

## Step 10: Report Results

After the orchestrator completes, verify outputs and display:

```bash
COMBINED_COUNT=$(find "$SOURCE_CODE_JSONS" -name "*.combined.json" 2>/dev/null | wc -l)
SHEET_COUNT=$(ls "$TECH_ASSESSMENT"/sheet*.json 2>/dev/null | wc -l)
EXCEL_EXISTS=$(test -f "$TECH_ASSESSMENT/technical_assessment_report.xlsx" && echo "Yes" || echo "No")
DASHBOARD_EXISTS=$(test -f "$TECH_ASSESSMENT/technical_assessment_dashboard.html" && echo "Yes" || echo "No")

echo ""
echo "=== ASSESSMENT COMPLETE ==="
echo "Phase 1: $COMBINED_COUNT files analyzed (.combined.json)"
echo "Phase 2: $SHEET_COUNT sheet JSONs generated"
echo "  - sheet1.json: Executive summary"
echo "  - sheet2.json: Modernization decision matrix"
echo "  - sheet3.json: Application-level summary"
echo "  - sheet4.json: Architecture overview"
echo "  - sheet7.json: Code quality & maintainability"
echo "  - sheet8.json: Application inventory"
echo "  - sheet9.json: Issues & suggestions"
echo "Phase 3:"
echo "  - Excel report: $EXCEL_EXISTS"
echo "  - HTML dashboard: $DASHBOARD_EXISTS"
echo "  - MongoDB: check orchestrator output"
echo "==========================="
```
