# .NET Dependency Analysis and Migration Suggestion

This command orchestrates a complete dependency analysis workflow for .NET projects, generating comprehensive migration reports and target architecture definitions for .NET modernization to the specified target framework.

## What This Command Does

Analyzes a .NET solution or project and generates:
1. **Compatibility analysis** - Identifies target framework compatibility issues
2. **Migration recommendations** - Suggests Upgrade/Replace/Rewrite actions
3. **Human-readable report** - Markdown report with tables and statistics
4. **Machine-readable architecture** - JSON file for automated task generation

---

## Command Syntax

**Default mode** (uses convention-based directories):
```bash
/dotnet-dependency-suggestion
```

**Explicit mode** (custom paths):
```bash
/dotnet-dependency-suggestion --project_path='path/to/project' --target_tech='path/to/target_tech.json' --output_dir='path/to/output'
```

### Default Directory Convention

If no arguments provided, the command looks for:
- 📁 **Project files**: `legacy_code/` (must contain .sln or .csproj)
- ⚙️ **Configuration**: `DotNet4/configs/target_tech.json`
- 📊 **Output**: `assess_and_recommend/dependency_analysis/`

---

## Multi-Phase Process

Follow these phases **IN SEQUENCE**:

---

## 🚨 CRITICAL FILE GENERATION RULES

**ENFORCEMENT POLICY** - Applied to ALL phases and agents:

1. **ONLY 4 OUTPUT FILES ALLOWED**:
   - ✅ `compatibility-report.json`
   - ✅ `migration-recommendations.json`
   - ✅ `dependency_migration_report.md`
   - ✅ `target_dependencies.json`

2. **STRICTLY FORBIDDEN** (will be auto-deleted if created):
   - ❌ Python scripts (*.py files)
   - ❌ Shell scripts (*.sh, *.bash files)
   - ❌ PowerShell scripts (*.ps1 files)
   - ❌ Additional documentation (README.md, START_HERE.md, SUMMARY.md, KEY_INSIGHTS.md)
   - ❌ Multiple report versions (dependency_migration_report_sonnet.md, etc.)
   - ❌ Temporary files or intermediate outputs
   - ❌ Configuration files (config.yml, settings.json)
   - ❌ Helper utilities or analysis scripts

3. **WORKSPACE BOUNDARY RESTRICTIONS**:
   - ✅ **READ allowed**: User project path (validated), `.legacyleap/config/`, `.legacyleap/tool/`
   - ✅ **WRITE allowed**: `assess_and_recommend/dependency_analysis/[timestamp]/` subdirectories ONLY
   - ❌ **FORBIDDEN**: Parent directory traversal (`../`), absolute paths outside workspace, system directories
   - ❌ **FORBIDDEN**: Modifying `.legacyleap/agent/` or `.legacyleap/command/`
   - 🔒 All paths validated before operations; violations halt execution immediately

4. **ENFORCEMENT MECHANISM**:
   - After each phase, verify ONLY expected files exist in `output/`
   - Validate all file paths are within allowed workspace boundaries
   - If unauthorized files detected, display warning and auto-delete
   - If path violation detected, abort operation and log security error
   - Continue workflow with clean state

5. **AGENT RESPONSIBILITIES**:
   - Each agent generates EXACTLY ONE output (or TWO for report-generator)
   - No helper scripts, no supplementary documentation
   - All file operations confined to designated output directory
   - Focus on producing the specified output only

---

### PHASE 1: Get Project Directory and Target Technology Configuration

**Part A: Locate Project Directory**

**Check for default directory convention first:**

```bash
# Initialize variables
PROJECT_PATH=""
TARGET_TECH_PATH=""
OUTPUT_BASE_DIR=""

# Parse command-line arguments if provided
while [[ $# -gt 0 ]]; do
    case $1 in
        --project_path=*)
            PROJECT_PATH="${1#*=}"
            shift
            ;;
        --target_tech=*)
            TARGET_TECH_PATH="${1#*=}"
            shift
            ;;
        --output_dir=*)
            OUTPUT_BASE_DIR="${1#*=}"
            shift
            ;;
        *)
            echo "Unknown argument: $1"
            shift
            ;;
    esac
done

# Check for default directories if arguments not provided
if [[ -z "$PROJECT_PATH" ]] && [[ -d "legacy_code" ]]; then
    echo "✓ Found default project directory: legacy_code/"
    PROJECT_PATH="legacy_code"
fi

if [[ -z "$TARGET_TECH_PATH" ]] && [[ -f "DotNet4/configs/target_tech.json" ]]; then
    echo "✓ Found default config: DotNet4/configs/target_tech.json"
    TARGET_TECH_PATH="DotNet4/configs/target_tech.json"
fi

if [[ -z "$OUTPUT_BASE_DIR" ]] && [[ -d "assess_and_recommend" ]] || mkdir -p "assess_and_recommend" 2>/dev/null; then
    echo "✓ Using default output directory: assess_and_recommend/"
    OUTPUT_BASE_DIR="assess_and_recommend/dependency_analysis"
    mkdir -p "$OUTPUT_BASE_DIR"
fi

# Validate we have all required paths
MISSING_DEFAULTS=()

if [[ -z "$PROJECT_PATH" ]]; then
    MISSING_DEFAULTS+=("project_path")
fi

if [[ -z "$TARGET_TECH_PATH" ]]; then
    MISSING_DEFAULTS+=("target_tech")
fi

if [[ -z "$OUTPUT_BASE_DIR" ]]; then
    MISSING_DEFAULTS+=("output_dir")
fi

# If any defaults are missing, show usage and exit
if [[ ${#MISSING_DEFAULTS[@]} -gt 0 ]]; then
    echo ""
    echo "❌ Error: Required directories/files not found in default locations"
    echo ""
    echo "Missing defaults:"
    for item in "${MISSING_DEFAULTS[@]}"; do
        case $item in
            project_path)
                echo "  • Project directory: legacy_code/ (must contain .sln or .csproj files)"
                ;;
            target_tech)
                echo "  • Configuration file: DotNet4/configs/target_tech.json"
                ;;
            output_dir)
                echo "  • Output directory: assess_and_recommend/"
                ;;
        esac
    done
    echo ""
    echo "📋 Solution: Either create the default directories or use explicit paths:"
    echo ""
    echo "Usage:"
    echo "  /dotnet-dependency-suggestion \\"
    echo "    --project_path='path/to/your/dotnet/project' \\"
    echo "    --target_tech='path/to/target_tech.json' \\"
    echo "    --output_dir='path/to/output/directory'"
    echo ""
    echo "Example:"
    echo "  /dotnet-dependency-suggestion \\"
    echo "    --project_path='/home/user/projects/MvcMusicStore' \\"
    echo "    --target_tech='/home/user/configs/target_tech.json' \\"
    echo "    --output_dir='/home/user/analysis/results'"
    echo ""
    exit 1
fi

echo ""
echo "📁 Directory Configuration:"
echo "  Project:  $PROJECT_PATH"
echo "  Config:   $TARGET_TECH_PATH"
echo "  Output:   $OUTPUT_BASE_DIR"
echo ""
```

**Validate project directory contains .NET files:**

```bash
# Look for .sln or .csproj files
SOLUTION_FILE=$(find "$PROJECT_PATH" -maxdepth 2 -name "*.sln" -type f | head -n 1)
PROJECT_FILE=$(find "$PROJECT_PATH" -maxdepth 2 -name "*.csproj" -type f | head -n 1)

if [[ -z "$SOLUTION_FILE" ]] && [[ -z "$PROJECT_FILE" ]]; then
    echo "❌ Error: No .NET project files found in $PROJECT_PATH"
    echo ""
    echo "The directory must contain:"
    echo "  • A .sln file (solution), OR"
    echo "  • A .csproj file (project)"
    echo ""
    echo "Please verify the project path and try again."
    exit 1
fi

if [[ -n "$SOLUTION_FILE" ]]; then
    echo "✓ Found solution: $(basename "$SOLUTION_FILE")"
else
    echo "✓ Found project: $(basename "$PROJECT_FILE")"
fi

echo ""
```

---

**Part B: Load Target Technology Configuration**

**Validate target_tech.json exists:**

```bash
# Validate target_tech.json exists
if [[ ! -f "$TARGET_TECH_PATH" ]]; then
    echo "❌ Error: Configuration file not found: $TARGET_TECH_PATH"
    exit 1
fi

echo "✓ Configuration file: $TARGET_TECH_PATH"
```

**Load and parse target_tech.json:**
- Read the JSON configuration file
- Validate structure contains: `target_technology`, `stacks`
- Extract available stacks: `standard`, `minimal`, `enterprise`

**Validate configuration structure**:
```json
{
  "source_technology": "string",
  "target_technology": "string",
  "target_backend_technology": "string",
  "complexity": "string",
  "stacks": {
    "standard": { "backend": {}, "frontend": {} },
    "minimal": { "backend": {}, "frontend": {} },
    "enterprise": { "backend": {}, "frontend": {} }
  }
}
```

**Ask user to select target stack** if not specified:
```
Which technology stack would you like to use for migration?

Available stacks:
1. standard   - Standard stack for typical migrations
2. minimal    - Minimal stack for simpler migrations  
3. enterprise - Enterprise-grade stack with advanced patterns

Enter selection (1-3) or stack name:
```

**Extract target framework version**:
- Parse `target_backend_technology` field (e.g., "Dot Net 10 C#")
- Convert to framework moniker: "Dot Net 10" → "net10.0"
- If version not parseable or not provided, default to "net8.0" (fallback)
- Store as `TARGET_FRAMEWORK` variable

**Extract selected stack configuration**:
- Read `stacks[selected_stack]` object
- Extract `backend` and `frontend` configurations
- Store for use in subsequent phases

**Copy target_tech.json to output directory**:
- Create `[output-dir]/input/` directory if not exists
- Copy `target_tech.json` to `[output-dir]/input/target_tech.json`
- This ensures agents have access to the configuration

**Display configuration summary**:
```
✓ Configuration Loaded
  Target Framework: net10.0
  Selected Stack: standard
  Backend Framework: ASP.NET Core Web API with Clean Architecture
  Backend ORM: Entity Framework Core 9.0.5 and Dapper 2.1.66
  Frontend: React 19 with TypeScript 5.8
```

---

### PHASE 2: Parse Dependencies Using Tool

**Create timestamped output directory:**

```bash
# Create timestamped output directory
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT_DIR="$OUTPUT_BASE_DIR/$TIMESTAMP"
mkdir -p "$OUTPUT_DIR"/{input,output,logs}

echo "📂 Created output directory: $OUTPUT_DIR"
```

**Use the dotnet_dependency_parser.py tool** to extract dependencies:

```bash
python3 .legacyleap/tool/dotnet_dependency_parser.py \
  "$PROJECT_PATH" \
  --output "$OUTPUT_DIR/input/dependencies-raw.json"
```

**Output directory structure**:
All generated files organized in timestamped directory:

```
assess_and_recommend/
└── dependency_analysis/
    └── [YYYYMMDD_HHMMSS]/
        ├── input/
        │   └── dependencies-raw.json
        ├── output/
        │   ├── compatibility-report.json
        │   ├── migration-recommendations.json
        │   ├── dependency_migration_report.md
        │   └── target_dependencies.json
        └── logs/
            └── analysis.log
```

**CRITICAL FILE GENERATION RESTRICTIONS**:
- ✅ **ONLY 4 files** allowed in `output/` directory (listed above)
- ❌ **NEVER allow agents to create**: Helper scripts (Python, Bash, PowerShell)
- ❌ **NEVER allow agents to create**: Additional documentation (README, SUMMARY, START_HERE)
- ❌ **NEVER allow agents to create**: Multiple report versions (no _sonnet, _haiku, _v2 suffixes)
- ❌ **NEVER allow agents to create**: Temporary files or intermediate outputs
- ❌ **NEVER allow agents to create**: Configuration files or supplementary data files
- Monitor and reject any attempts to create files beyond the 4 specified outputs

**Handle tool execution errors**:
- If parser fails, output error message
- Check if dependencies-raw.json was created
- Validate JSON structure
- If empty or invalid, inform user and stop

**Transform parsed output** to compatibility checker input format:
- Extract solution and project information
- Format package references with `id`, `requestedVersion`, `isTransitive`
- Format assembly references with `name`, `requestedVersion`, `isTransitive`
- Create `compatibility-input.json` in output directory

**Example transformation**:
```json
{
  "solution": {
    "name": "MvcMusicStore",
    "path": "/path/to/solution.sln"
  },
  "projects": [
    {
      "name": "MvcMusicStore",
      "path": "MvcMusicStore/MvcMusicStore.csproj",
      "targetFramework": "v4.8",
      "nugetPackages": [
        {
          "id": "EntityFramework",
          "requestedVersion": "6.0.0",
          "isTransitive": false
        }
      ],
      "assemblyReferences": [
        {
          "name": "System.Web",
          "requestedVersion": null,
          "isTransitive": false
        }
      ]
    }
  ]
}
```

---

### PHASE 3: Run Compatibility Analysis

**Invoke the dependency-compatibility-checker agent**:

Provide the agent with:
- Input file: `[output-dir]/input/compatibility-input.json`
- Target technology configuration: `[output-dir]/input/target_tech.json`
- Target framework: `{TARGET_FRAMEWORK}` (extracted from target_tech.json)

**Agent instruction**:
```
@dotnet-dependency-compatibility-checker

Analyze the dependencies in @[output-dir]/input/compatibility-input.json 
and check for {TARGET_FRAMEWORK} compatibility.

Target Technology Configuration: @[output-dir]/input/target_tech.json
Target Framework: {TARGET_FRAMEWORK}

Use the target framework version from the configuration for all compatibility checks.

Write the compatibility report to: [output-dir]/output/compatibility-report.json
```

**Verify agent output**:
- Check that `compatibility-report.json` was created
- Validate JSON structure
- Verify it contains: `analysisMetadata`, `summary`, `projects[]`
- Check for any errors in the `errors[]` array
- If critical errors, inform user and ask whether to continue

**Verify ONLY specified file was created** (ENFORCE FILE RESTRICTIONS):

1. **List all files** in `[output-dir]/output/` directory
2. **Expected files at this stage:** ONLY `compatibility-report.json`
3. **Identify unauthorized files:**
   - Any file that is NOT `compatibility-report.json`
   - Examples: `*.py`, `*.sh`, `README.md`, `SUMMARY.md`, `*.txt`
4. **If unauthorized files found:**
   - Display warning:
     ```
     ⚠️ WARNING: Agent created {count} unauthorized file(s). Enforcing file restrictions...
     
     Unauthorized files:
       - {filename1}
       - {filename2}
       ...
     
     Removing unauthorized files...
     ```
   - **DELETE each unauthorized file** using `rm` command
   - Verify deletion successful
   - Display: `✓ Cleanup complete. Continuing with valid output only.`
5. **If only expected file exists:**
   - Display: `✓ File restrictions: PASSED (1/1 expected files)`

**Display progress**:
```
✓ Phase 3 Complete: Compatibility Analysis
  Total Dependencies: [count]
  Compatible: [count]
  Incompatible: [count]
  Errors: [count]
```

---

### PHASE 4: Generate Migration Recommendations

**Invoke the dependency-suggestor agent**:

Provide the agent with:
- Input file: `[output-dir]/output/compatibility-report.json`
- Target technology configuration: `[output-dir]/input/target_tech.json`
- Selected stack: `{SELECTED_STACK}` (from Phase 1)
- Target framework: `{TARGET_FRAMEWORK}` (from Phase 1)
- Static mapping configuration: `.legacyleap/config/dotnet-legacy-to-modern-mappings.yml`

**Agent instruction**:
```
@dotnet-dependency-suggestor

Generate migration recommendations from @[output-dir]/output/compatibility-report.json
using the target technology configuration at @[output-dir]/input/target_tech.json

Configuration Details:
- Selected Stack: {SELECTED_STACK}
- Target Framework: {TARGET_FRAMEWORK}
- Static Mappings: @config/dotnet-legacy-to-modern-mappings.yml (as fallback)

CRITICAL: Generate dynamic mappings from target_tech.json based on selected stack:
- Use backend specifications to determine ORM, authentication, framework choices
- Use frontend specifications to determine UI library, state management choices
- Static mappings serve as fallback for unmapped dependencies

Write recommendations to: [output-dir]/output/migration-recommendations.json

CRITICAL: Follow the EXACT JSON schema specified in the agent definition:
- Use "name" field (not "dependencyId")
- Use "dependencyType" field ("nuget" or "assembly")
- Format "migrationNotes" as ARRAY of strings
- Format "breakingChanges" as ARRAY of strings
- Include "codeChangesRequired" boolean field
- Use proper case for action, priority, and effort fields
- Include target framework in metadata: "targetFramework": "{TARGET_FRAMEWORK}"
```

**Verify agent output** (STRICT VALIDATION):
- Check that `migration-recommendations.json` was created
- Validate JSON structure matches agent schema
- Verify required fields: `recommendationMetadata`, `summary`, `projects[]`
- Verify each recommendation has ALL mandatory fields:
  - `dependencyType` (string: "nuget" or "assembly")
  - `name` (string)
  - `currentVersion` (string or null)
  - `action` (string: "Upgrade", "Replace", or "Rewrite")
  - `priority` (string: "critical", "high", "medium", or "low")
  - `targetPackage` (string or null)
  - `targetVersion` (string or null)
  - `estimatedEffort` (string: "Low", "Medium", "High", or "Very High")
  - `migrationNotes` (array of strings)
  - `breakingChanges` (array of strings)
  - `codeChangesRequired` (boolean)
  - `alternativeApproach` (string or null)
- Check recommendation counts match summary
- If validation fails, request agent re-run with corrections

**Verify Recommendation Completeness** (CRITICAL):
- Read `[output-dir]/output/compatibility-report.json`
- Count total dependencies in compatibility report:
  - Count nugetPackages from all projects
  - Count assemblyReferences from all projects
  - Total INPUT dependencies = nugetPackages + assemblyReferences
- Read `[output-dir]/output/migration-recommendations.json`
- Count total recommendations:
  - Count recommendations from all projects
  - Total OUTPUT recommendations
- **Compare counts - MUST be equal**:
  - If OUTPUT == INPUT: ✅ PASS - All dependencies processed
  - If OUTPUT < INPUT: ❌ FAIL - Missing dependencies
    - Calculate: missing_count = INPUT - OUTPUT
    - Display ERROR:
      ```
      ⚠️ ERROR: Dependency count mismatch detected!
      
      Input (Compatibility Report):  {INPUT} dependencies
      Output (Recommendations):      {OUTPUT} recommendations
      Missing:                       {missing_count} dependencies
      
      Some dependencies were not processed by the suggestor agent.
      Requesting agent re-run with explicit ALL-DEPENDENCIES instruction...
      ```
    - List missing dependencies (compare names from input vs output)
    - Re-invoke dependency-suggestor with additional instruction:
      ```
      CRITICAL: Process ALL dependencies from input.
      Missing dependencies detected: [list]
      Ensure every dependency gets a recommendation (Upgrade/Replace/Rewrite).
      ```
    - Re-verify after re-run
  - If OUTPUT > INPUT: ⚠️ WARNING - Possible duplicates
    - Log warning but continue (duplicates will be visible in report)

**Verify ONLY specified files were created** (ENFORCE FILE RESTRICTIONS):

1. **List all files** in `[output-dir]/output/` directory
2. **Expected files at this stage:** `compatibility-report.json`, `migration-recommendations.json` (exactly 2 files)
3. **Identify unauthorized files:**
   - Any file that is NOT in the expected list
   - Examples: `*.py`, `*.sh`, `README.md`, `SUMMARY.md`, `INSIGHTS.md`, `*.txt`
4. **If unauthorized files found:**
   - Display warning:
     ```
     ⚠️ WARNING: Agent created {count} unauthorized file(s). Enforcing file restrictions...
     
     Unauthorized files:
       - {filename1}
       - {filename2}
       ...
     
     Removing unauthorized files...
     ```
   - **DELETE each unauthorized file** using `rm` command
   - Verify deletion successful
   - Display: `✓ Cleanup complete. Continuing with valid outputs only.`
5. **If only expected files exist:**
   - Display: `✓ File restrictions: PASSED (2/2 expected files)`

**Display progress**:
```
✓ Phase 4 Complete: Migration Recommendations
  Total Recommendations: [count]
  Upgrade: [count]
  Replace: [count]
  Rewrite: [count]
  Critical Priority: [count]
  ✅ JSON Schema Validation: PASSED
```

---

### PHASE 5: Generate Reports

**Invoke the dependency-report-generator agent**:

Provide the agent with:
- Input file: `[output-dir]/output/migration-recommendations.json`
- Target technology configuration: `[output-dir]/input/target_tech.json`
- Selected stack: `{SELECTED_STACK}`
- Target framework: `{TARGET_FRAMEWORK}`

**Agent instruction**:
```
@dotnet-dependency-report-generator

Generate migration report and target dependencies from:
- Migration recommendations: @[output-dir]/output/migration-recommendations.json
- Target technology configuration: @[output-dir]/input/target_tech.json

Configuration:
- Selected Stack: {SELECTED_STACK}
- Target Framework: {TARGET_FRAMEWORK}

Use the target_tech.json configuration to populate framework decisions in the report.

Write outputs to:
1. [output-dir]/output/dependency_migration_report.md
2. [output-dir]/output/target_dependencies.json

CRITICAL: Follow the EXACT report structure specified in the agent definition:

MARKDOWN REPORT MUST INCLUDE (in order):
1. Title: "# .NET {TargetVersion} Migration Report: [SolutionName]"
   (Use target framework version from target_tech.json, e.g., "# .NET 10 Migration Report: MvcMusicStore")
2. Executive Summary with tables
3. Key Milestones section (SIMPLE numbered list, NO sub-bullets, NO phases, NO timelines)
4. Recommendations by Action (Upgrade/Replace/Rewrite tables)
5. Recommendations by Priority (Critical/High/Medium/Low tables)
6. Detailed Recommendations (numbered, one per dependency)
7. Next Steps section (with "### Immediate Actions" subsection, NO time estimates)
8. Resources section
9. Footer

CRITICAL FORMATTING:

**Key Milestones MUST be simple:**
- Plain numbered list (1. 2. 3.)
- Single line per milestone
- NO bold, NO sub-bullets, NO phase names, NO timelines
- Example: "1. Migrate from ASP.NET MVC to ASP.NET Core"
- NOT: "1. **Phase 1: Planning** (Week 1-2)\n   - Setup project"

**Next Steps MUST have "Immediate Actions":**
- Must include "### Immediate Actions" subsection
- Brief numbered list of high-level actions
- NO time estimates (no weeks, months, days)
- NO detailed implementation steps
- Example: "1. **Review Critical Priority Items** - Address these first"
- NOT: "1. **Week 1-2: Review** - Analyze all dependencies in detail"

JSON FILE MUST INCLUDE:
- metadata (with generatedDate, solutionName, solutionPath, targetFramework)
- frameworkDecisions (with decision/package/version/reason objects)
- targetPackages array
- migrationSummary (with migrationType, complexity, actionBreakdown, priorityBreakdown, keyMilestones)
- projectDetails array with full recommendations
```

**Verify agent outputs** (STRICT VALIDATION):

**For dependency_migration_report.md**:
- Check file exists and is valid markdown
- Verify contains Executive Summary section
- Verify contains all three action tables (Upgrade, Replace, Rewrite)
- Verify contains all four priority tables (Critical, High, Medium, Low)
- Verify contains Detailed Recommendations section (numbered entries)
- Verify contains Next Steps section
- Verify contains Resources section
- Verify footer present
- If validation fails, request agent re-run

**For target_dependencies.json**:
- Check file exists and is valid JSON
- Verify has metadata object with all required fields
- Verify has frameworkDecisions with proper structure
- Verify has targetPackages array
- Verify has migrationSummary with all required fields
- Verify has projectDetails array with recommendations
- Each recommendation must have: dependencyType, name, currentVersion, action, priority, targetPackage, targetVersion, estimatedEffort, migrationNotes (array), breakingChanges (array), codeChangesRequired, alternativeApproach
- If validation fails, request agent re-run

**Verify ONLY specified files were created** (ENFORCE FILE RESTRICTIONS):

1. **List all files** in `[output-dir]/output/` directory
2. **Expected files at this stage:** 
   - `compatibility-report.json`
   - `migration-recommendations.json`
   - `dependency_migration_report.md`
   - `target_dependencies.json`
   - Total: exactly 4 files
3. **Identify unauthorized files:**
   - Any file that is NOT in the expected list above
   - Common violations:
     - Python scripts: `*.py`, `generate_*.py`, `transform_*.py`, `run_*.py`
     - Shell scripts: `*.sh`, `*.bash`
     - Documentation: `README.md`, `START_HERE.md`, `SUMMARY.md`, `KEY_INSIGHTS.md`, `EXECUTIVE_SUMMARY.txt`, `ANALYSIS_SUMMARY.md`, `PACKAGE_REPLACEMENT_GUIDE.md`
     - Index files: `INDEX.txt`, `MANIFEST.txt`, `DELIVERY_MANIFEST.txt`
     - Report variants: `dependency_migration_report_sonnet.md`, `*_v2.md`, `*_final.json`
4. **If unauthorized files found:**
   - Display warning:
     ```
     ⚠️ WARNING: Agent created {count} unauthorized file(s). Enforcing file restrictions...
     
     Expected files (4):
       ✅ compatibility-report.json
       ✅ migration-recommendations.json
       ✅ dependency_migration_report.md
       ✅ target_dependencies.json
     
     Unauthorized files detected:
       ❌ {filename1}
       ❌ {filename2}
       ❌ {filename3}
       ...
     
     Removing unauthorized files...
     ```
   - **DELETE each unauthorized file** using `rm` command
   - Verify deletion successful
   - Display: `✓ Cleanup complete. Only 4 authorized files remain.`
5. **If only expected files exist:**
   - Display: `✓ File restrictions: PASSED (4/4 expected files)`
6. **Final verification:**
   - List remaining files to confirm
   - If count != 4, display error and halt

**Display progress**:
```
✓ Phase 5 Complete: Report Generation
  Markdown Report: [path]
    ✅ Structure Validation: PASSED
    ✅ Sections: 9/9 present
  Target Dependencies: [path]
    ✅ JSON Schema Validation: PASSED
    ✅ Framework Decisions: present
  Migration Type: [type]
  Complexity: [level]
```

---

### PHASE 6: Display Summary and Next Steps

**Output final summary** to user:

```
🎉 Dependency Analysis Complete!

📊 Analysis Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Solution: [solution-name]
Target Framework: {TARGET_FRAMEWORK}
Total Dependencies: [count]

Migration Breakdown:
  ✅ Upgrade:  [count] ([percentage]%)
  🔄 Replace:  [count] ([percentage]%)
  ⚠️  Rewrite:  [count] ([percentage]%)

Priority Distribution:
  🔴 Critical: [count]
  🟠 High:     [count]
  🟡 Medium:   [count]
  🟢 Low:      [count]

Migration Assessment:
  Type:       [Full Framework Migration | Partial Migration | Package Modernization]
  Complexity: [High | Medium | Low]

📁 Generated Files
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reports are in: [output-directory]

📄 Human-Readable:
  └─ dependency_migration_report.md

🤖 Machine-Readable:
  └─ target_dependencies.json

📊 Analysis Data:
  ├─ compatibility-report.json
  ├─ migration-recommendations.json
  └─ dependencies-raw.json

🎯 Key Milestones
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[List key milestones from migrationSummary]

📋 Next Steps
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review the migration report: [path to .md file]

2. Examine framework decisions in target_dependencies.json:
   - Web Framework: [decision]
   - Data Access: [decision]
   - Authentication: [decision]

3. Create LeapOS tasks from the report tables

4. Begin implementation:
   - Start with Upgrade actions (lowest risk)
   - Address Replace actions next (clear migration path)
   - Plan Rewrite actions carefully (architectural changes)

5. Track progress using target_dependencies.json as reference

Would you like me to create LeapOS tasks from the migration report?
```



## Error Handling

**If dependency parser fails**:
- Display error message from tool
- Check if project path is valid
- Verify .NET project files exist
- Offer to retry with different path

**If compatibility checker fails**:
- Check network connectivity (NuGet API access)
- Verify input JSON structure
- Continue with partial results if possible
- Log errors to analysis.log

**If suggestor fails**:
- Verify mapping configuration exists
- Check compatibility report structure
- Attempt to continue without mappings
- Log warnings

**If report generator fails**:
- Verify recommendations JSON structure
- Generate partial report if possible
- At minimum, output raw JSON files

**Graceful degradation**:
- Always save intermediate results
- Allow manual inspection of any phase
- Provide clear error messages
- Enable resume from any phase

---

## Output Files Reference

**Input Files**:
- `dependencies-raw.json` - Raw output from dotnet_dependency_parser.py
- `compatibility-input.json` - Transformed input for compatibility checker

**Analysis Files**:
- `compatibility-report.json` - Compatibility facts per dependency
- `migration-recommendations.json` - Structured recommendations

**Report Files** (Main outputs):
- `dependency_migration_report.md` - Human-readable migration guide
- `target_dependencies.json` - Machine-readable target architecture

**Log Files**:
- `analysis.log` - Execution log with timestamps and errors

---



## Command Output Structure

```
assess_and_recommend/dependency_analysis/[YYYYMMDD_HHMMSS]/
├── input/
│   ├── dependencies-raw.json          (Phase 2 output)
│   └── compatibility-input.json       (Phase 2 transformed)
├── output/
│   ├── compatibility-report.json      (Phase 3 output)
│   ├── migration-recommendations.json (Phase 4 output)
│   ├── dependency_migration_report.md (Phase 5 output - HUMAN)
│   └── target_dependencies.json       (Phase 5 output - MACHINE)
└── logs/
    └── analysis.log                    (Execution log)
```

All files are organized and timestamped for easy reference and comparison across multiple runs.

**Note**: If using custom output directory via `--output_dir`, the structure will be created at the specified location instead.
