---
description: "Builds .NET solution and generates build status report"
name: dotnet-build-check
mode: primary
tools:
  Bash: true
  Read: true
  Write: true
  Task: false
temperature: 0.1
---

# 🔐 CRITICAL: Self-Contained Agent

**NEVER use Task tool. ONLY use Bash tool.**
- ❌ Forbidden: dotnet-build-analyzer, dotnet-auto-fix, dotnet-error-fixer, dotnet-version-setup
- ✅ Allowed: Bash tool for scripts, Read/Write for files only

---

# .NET Build Check Agent

Simple agent that builds a .NET solution and generates a detailed build status report.

## Outputs

Returns simple status message and generates a build report document:

1. **Simple Status** (stdout):
   - Success: `✅ Build Check Completed Successfully`
   - Failure: `❌ Build Check Failed`
   - Includes summary: solution, configuration, status, error/warning counts, build time

2. **Build Report Document** (`.legacyleap/reports/execution-summary.md`):
   - Formatted Markdown document with build details, errors, warnings, and metadata
   - Consolidated report with all execution information

## Scripts Called

This agent calls the following read-only scripts:

1. **`build-check-safe.sh`** (dotnet-build-check directory) - Builds .NET solution WITHOUT modifying source
   - Args: `$1 = solution_path` (optional), `$2 = configuration` (optional, default: Debug), `$3 = output_file` (optional), `$4 = timeout` (optional, default: 600)
   - Output: Build output to stdout and optionally to temporary file (auto-deleted after parsing)
   - Safety: Uses -p:BaseOutputPath to redirect artifacts to `.legacyleap/.agent-state/.tmp/build-artifacts/`
   - Safety: NEVER creates global.json or modifies source directory
   - Example: `./build-check-safe.sh "MusicStore.sln" "Debug" ".legacyleap/.agent-state/.tmp/build-output.txt" "600"`

2. **`parse-build-output-native.sh`** (dotnet-build-check directory) - Parses native dotnet CLI output for deterministic error/warning counts
   - Args: `$1 = build_output_file` (or '-' for stdin)
   - Output: Native format error/warning counts in JSON format to stdout
   - Method: Extracts counts from native dotnet summary: "Restore/Build failed with X error(s) and Y warning(s)"
   - Determinism: 100% - counts match exactly what native `dotnet build` reports
   - Example: `./parse-build-output-native.sh ".legacyleap/.agent-state/.tmp/build-output.txt"`
   - Example Output:
     ```json
     {
       "error_count": 1,
       "warning_count": 7,
       "build_status": "failed",
       "summary_line": "Restore failed with 1 error(s) and 7 warning(s) in 0.5s"
     }
     ```

3. **`verify-sdk-version.sh`** (shared) - Verifies SDK version matches detected version
    - Args: `$1 = required_version` (X.Y.Z format), `$2 = project_root` (optional, default: current directory)
    - Output: "match", "mismatch:VERSION", or "error:MESSAGE" to stdout
    - Example: `./verify-sdk-version.sh "8.0.0" "."`

## Prerequisites

Before executing: Verify `execution_model: "direct"` in command file (NOT "delegated")

---

## Execution Steps

0. **Set Target Directory (Optional)**:

   **Purpose**: Read target path from metadata.json if available, otherwise continue normally in current directory.

   **Configuration File**:
   - File: `metadata.json` (at same level as `.legacyleap` folder)
   - Key: `modernize` (contains path to code that needs to be built)

   **Steps**:

   1. **Get target path**:
      - Execute: `Bash .legacyleap/scripts/shared/get-target-path.sh`
      - Capture output: `TARGET_DIR = <stdout>`
      - Capture exit code: `exit_code = <exit_code>`

   2. **Process result**:
      
      **Case A: Path found (exit code 0, TARGET_DIR != ".")**:
      - Path found in metadata.json
      - Change directory: `cd "$TARGET_DIR"`
      - Verify: Check that `$(pwd)` equals `TARGET_DIR`
      - If change fails: Log warning but continue (don't stop execution)
      - Log: `Bash .legacyleap/scripts/shared/log-audit-event.sh "info" "Using target path from metadata.json" '{"target_dir":"<TARGET_DIR>"}' "info"`
      - Display: "📁 Working in configured directory: `<TARGET_DIR>`"
      
      **Case B: No config found (exit code 0, TARGET_DIR == ".")**:
      - No metadata.json found OR "modernize" key is missing/empty
      - Skip directory change (continue in current directory)
      - Log: `Bash .legacyleap/scripts/shared/log-audit-event.sh "info" "No metadata.json found, using current directory" '{}' "info"`
      - Display: "ℹ️ Using current directory (no metadata.json configuration)"
      - Continue normally (original behavior)
      
      **Case C: Error reading config (exit code 1)**:
      - Error reading metadata.json (invalid JSON, path doesn't exist, etc.)
      - Log warning: `Bash .legacyleap/scripts/shared/log-audit-event.sh "warning" "Error reading metadata.json, using current directory" '{"error":"<error_message>"}' "warning"`
      - Display: "⚠️ Warning: Error reading metadata.json, continuing in current directory"
      - Continue in current directory (don't stop execution - maintain backward compatibility)

   **Note**: This step is optional and non-blocking. Execution continues in current directory if config is missing or invalid, maintaining full backward compatibility.

   **Log**: `Bash .legacyleap/scripts/shared/log-audit-event.sh "phase_start" "Step 0: Target Directory Configuration" '{}' "info"`

---

1. **Initialize**:
   - Set defaults: `configuration = Debug`, `timeout = 600`, `project_root = .`
   - Auto-detect solution file: Find `*.sln` in current directory, fallback to `*.csproj`
   - Store: `solution_path = <detected_solution>`
   - Record start time: `start_time = $(date +%s)`

2. **Read Version** (for verification):
   - Execute: `Bash .legacyleap/scripts/shared/read-version-info.sh "false"`
   - If exit code == 0: Extract `version` from JSON output
   - Store: `detected_version = <version>` or empty if not found
   - If version found: Validate JSON contains `version` field

3. **Verify SDK Version** (Before Build, if version available):
   - If `detected_version` is available:
     - Execute: `Bash .legacyleap/scripts/shared/verify-sdk-version.sh "$detected_version" "${project_root:-.}"`
     - Verify exit code (0 = match, 1 = mismatch)
     - Parse output: Extract result from stdout
     - If result is "match": Log success, continue
     - If result is "mismatch:VERSION": Log warning but continue
     - If result is "error:MESSAGE": Log error but continue (don't fail)

4. **Build Solution** (required, read-only):
   - Execute: `Bash .legacyleap/scripts/dotnet-build-check/build-check-safe.sh "${solution_path}" "${configuration:-Debug}" ".legacyleap/.agent-state/.tmp/build-output.txt" "${timeout:-600}"`
   - Verify exit code (0 = success, 1 = failure)
   - Record end time: `end_time = $(date +%s)`
   - Calculate: `build_time = end_time - start_time`
   - Store: `build_exit_code = <exit_code>`
   - Store: `build_succeeded = <true|false>`
   - **SAFETY GUARANTEE:** Uses -p:BaseOutputPath to redirect all artifacts to `.legacyleap/.agent-state/.tmp/build-artifacts/`
   - **SAFETY GUARANTEE:** NEVER creates global.json
   - **SAFETY GUARANTEE:** NEVER modifies source directory (@modernize stays completely clean)
    - If fails, continue to parse errors

    **FAST-PATH OPTIMIZATION (NEW):**
    - Check if build output file exists AND has content:
      ```bash
      if [ -f ".legacyleap/.agent-state/.tmp/build-output.txt" ] && [ -s ".legacyleap/.agent-state/.tmp/build-output.txt" ]
      ```
    - Store: `build_output_exists = <true|false>`
    - Log: If true: "✓ Build completed, output verified" | If false: "⚠ Build output missing or empty"

4B. **Check Build Logs for Immediate Status (FAST-FAIL)** (Fix #7):
    - **Purpose:** Detect build failures immediately WITHOUT waiting for file creation
    - **NEW:** Check live build log for immediate status patterns (instead of waiting for file)
    - Execute: Check if live build log exists and contains status patterns:
      ```bash
      if [ -f ".legacyleap/.agent-state/.tmp/build-live.log" ] && [ -s ".legacyleap/.agent-state/.tmp/build-live.log" ]; then
        IMMEDIATE_STATUS=$(Bash .legacyleap/scripts/dotnet-build-check/check-build-status-immediate.sh ".legacyleap/.agent-state/.tmp/build-live.log")
      fi
      ```
    - Parse JSON output: Extract `status`, `method`, `error_count`, `warning_count`, `summary_line`
    
    - **If status detected from logs (method != "none" and method != "log_not_found"):**
      - Log: `Bash .legacyleap/scripts/shared/log-audit-event.sh "info" "Build status detected from execution logs (immediate, no wait)" '{"method":"'$method'","status":"'$status'","errors":'$error_count',"warnings":'$warning_count'}' "info"`
      - Display: "✓ Build status confirmed from execution logs (immediate detection)"
      - Store: `skip_file_wait = true`
      - Store: `build_status_immediate = $status`
      - Store: `error_count = $error_count`
      - Store: `warning_count = $warning_count`
      - **SKIP to Step 6** (parse already complete, don't wait for file)
      - Continue immediately to Step 7 (Generate report)
    
    - **If status unclear from logs (method == "none" or log not available):**
      - Log: "Build status unclear from logs, proceeding with file verification"
      - Store: `skip_file_wait = false`
      - Store: `build_status_immediate = "unknown"`
      - Continue to Step 4C (verify file, fallback to file-based parsing)

    **BENEFIT:** Early failure detection (seconds instead of minutes)

4C. **Verify Build Output File** (Only if status unclear from logs):
    - **NEW:** Only verify file if immediate status check was inconclusive
    - If `skip_file_wait == true`: 
      - SKIP this entire step
      - Log: "⏭ Skipping file verification (status confirmed from logs)"
      - Continue to Step 6
    
    - Otherwise:
      - Check if output file exists and has content:
        ```bash
        if [ -f ".legacyleap/.agent-state/.tmp/build-output.txt" ] && [ -s ".legacyleap/.agent-state/.tmp/build-output.txt" ]; then
          echo "✓ Build output file verified"
        else
          echo "⚠️  Build output file not found or empty"
        fi
        ```
      - Store: `build_output_exists = <true|false>`
      - If file exists: Log success, continue to Step 6
      - If file missing/empty: Log warning, attempt diagnostic (SDK version check), continue to Step 6

5. **Verify SDK Version** (After Build, CONDITIONAL - only if output missing):
   - **FAST-PATH:** If `build_output_exists == true` (build produced output):
     - SKIP this verification step (build success validates environment)
     - Log: "⏭ SDK verification skipped (build output validates environment)"
     - Continue directly to Step 6 (Parse Build Output)
     - **Performance gain:** Saves 200-400ms
   
   - **DIAGNOSTIC PATH:** If `build_output_exists == false` (build output missing/empty):
     - Run full SDK verification (something may be wrong, need diagnostics)
     - If `detected_version` is available:
       - Execute: `Bash .legacyleap/scripts/shared/verify-sdk-version.sh "$detected_version" "${project_root:-.}"`
       - Verify exit code (0 = match, 1 = mismatch)
       - Parse output: Extract result from stdout
       - If result is "match": Log success
       - If result is "mismatch:VERSION": Log warning but continue
       - If result is "error:MESSAGE": Log error but continue
       - Store: `version_verification = match|mismatch|error`

6. **Parse Build Output Using Native Dotnet Format** (DETERMINISTIC):
    - **NEW:** Conditional parsing based on source (immediate logs vs file)
    - **If build_status_immediate != "unknown"** (status already detected from logs):
      - SKIP parsing step (already have data from immediate check)
      - Log: "⏭ Skipping file parsing (status already confirmed from execution logs)"
      - Use stored values: `error_count`, `warning_count`, `build_status_immediate`
      - **Performance gain:** Saves 500-1000ms file parsing time
    
    - **Otherwise, parse from file:**
      - **Purpose:** Extract error and warning counts directly from native dotnet CLI summary
      - Execute: `Bash .legacyleap/scripts/dotnet-build-check/parse-build-output-native.sh ".legacyleap/.agent-state/.tmp/build-output.txt"`
      - Verify exit code (0 = success)
      - Capture JSON output with native dotnet summary information
      - Validate: Ensure JSON contains required fields: `error_count` (number), `warning_count` (number), `build_status` (string), `summary_line` (string)
      - Extract: 
        - `error_count = <count>` (directly from native dotnet summary: "Restore/Build failed with X error(s)...")
        - `warning_count = <count>` (directly from native dotnet summary: "...and Y warning(s)")
        - `build_status = <succeeded|failed>` (from native output)
        - `summary_line = <native_summary>` (the authoritative source)
      - **DETERMINISM GUARANTEE:** Error/warning counts come directly from native dotnet CLI output summary, NOT from regex parsing
      - **ACCURACY GUARANTEE:** Counts match exactly what native `dotnet build` reports (1 NU1605 error = 1, 7 warnings = 7)
      - **Cleanup**: Execute `Bash .legacyleap/scripts/shared/cleanup-temp-files.sh "build-output.txt"` to delete temporary build output file
      - If validation fails: Set `error_count = 0`, `warning_count = 0`, `build_status = "unknown"`

7. **Get .NET Version** (for report):
   - If `detected_version` is already available from step 2: Use it
   - Otherwise: Execute `Bash .legacyleap/scripts/shared/read-version-info.sh "false"`
   - If exit code == 0: Extract `version` from JSON output
   - Store: `dotnet_version = <version>` or `"unknown"`

8. **Generate Build Report Document**:

   - Create Markdown document with:

     ```markdown
     # Build Check Report
     
     **Timestamp:** ISO8601_TIMESTAMP
     **Solution:** SOLUTION_PATH
     **Configuration:** CONFIGURATION
     **Status:** SUCCESS_OR_FAILED
     **Build Time:** BUILD_TIME seconds
     **.NET Version:** VERSION
     
     ## Summary
     
     - **Build Succeeded:** TRUE_OR_FALSE
     - **Total Errors:** ERROR_COUNT
     - **Total Warnings:** WARNING_COUNT
     - **Prerequisites Check:** SUCCESS_OR_WARNING
     - **Packages Restored:** SUCCESS_OR_WARNING
     
     ## Errors
     
     If errors exist, list each error with file, line, code, and message.
     If no errors: "No errors found."
     
     ## Warnings
     
     If warnings exist, list each warning with file, line, code, and message.
     If no warnings: "No warnings found."
     
     ## Build Output
     
     Full build output saved to: `.legacyleap/build-output.txt`
     ```

   - Write to: `.legacyleap/reports/execution-summary.md`
   - Ensure directory exists: `mkdir -p .legacyleap/reports`

11. **Return Simple Status**:

   - Format human-readable summary:

     ```text
     ✅ Build Check Completed Successfully
     
     Summary:
     - Solution: SOLUTION_PATH
     - Configuration: CONFIGURATION
     - Status: SUCCESS
     - Errors: ERROR_COUNT
     - Warnings: WARNING_COUNT
     - Build Time: BUILD_TIME seconds
     
     Report saved to: .legacyleap/reports/execution-summary.md
     ```

     OR

     ```text
     ❌ Build Check Failed
     
     Summary:
     - Solution: SOLUTION_PATH
     - Configuration: CONFIGURATION
     - Status: FAILED
     - Errors: ERROR_COUNT
     - Warnings: WARNING_COUNT
     - Build Time: BUILD_TIME seconds
     
     Report saved to: .legacyleap/reports/execution-summary.md
     ```

   - Output to stdout

## Error Handling

Returns error in output if:

- Solution file not found
- Build script execution fails
- Report generation fails

## Inputs

Accepts optional inputs:

- `solution_path` (optional, auto-detected)
- `configuration` (optional, defaults to Debug)
- `timeout` (optional, defaults to 600 seconds)
- `project_root` (optional, defaults to current directory)

## State

Generates state files (all in `.legacyleap/` - source directory stays clean):

- `.legacyleap/.agent-state/.tmp/build-artifacts/` - Build artifacts directory (isolated, temporary)
- `.legacyleap/.agent-state/.tmp/build-output.txt` - Temporary build output (auto-deleted after parsing)
- `.legacyleap/reports/execution-summary.md` - Formatted build report (Markdown, user-facing)

**IMPORTANT:** Source directory (@modernize) remains completely unmodified. All artifacts and temporary files are stored in `.legacyleap/` directory tree.

## Safety Rules

**CRITICAL CONSTRAINTS - MUST NEVER:**

- **NEVER** execute git commands (git commit, git add, git push, git tag, etc.)
- **NEVER** modify git repository state
- **NEVER** stage, commit, or push changes to git
- **NEVER** modify source code files in @modernize directory
- **NEVER** create global.json file
- **NEVER** create build artifacts (bin/, obj/) in source directory
- **NEVER** modify any files in the @modernize target directory

**OPERATIONAL RULES:**

- Always use read-only build script (`build-check-safe.sh`) that redirects artifacts
- Continue execution even if SDK version verification fails (log warning)
- Always generate report document, even on failure
- Format errors and warnings in readable Markdown format
- **Always delete temporary files after use** (build output files after parsing)
- **Create documents only when they add value** (user-facing reports only)
- **Consolidate related information** (avoid redundant files)
- **Minimize file count** (group related data)

**PERFORMANCE OPTIMIZATION RULES:**

- **Fast-Path Execution:** Skip post-build SDK verification if build output exists and has content (build success validates environment)
- **Deterministic Output:** Output file existence is the validation mechanism - if file exists, build ran successfully
- **Conditional Diagnostics:** Only run full SDK verification when build output is missing/empty (error diagnosis path)
- **Time Savings:** Fast path saves ~200-400ms per execution (typical case: 2-3s total vs 5-6s without optimization)

**DETERMINISTIC PARSING RULES (🔒 Guarantees):**

- **Native Source of Truth:** Error/warning counts extracted ONLY from native dotnet CLI output summary format
  - Format: `Restore/Build [succeeded|failed] with X error(s) and Y warning(s)`
  - Example: `Restore failed with 1 error(s) and 7 warning(s) in 0.5s`
- **No Regex Parsing:** Do NOT use regex patterns to count errors (prone to miscounting multi-line messages)
- **Exact Match Guarantee:** Counts ALWAYS match exactly what native `dotnet build` command reports
  - If native shows "1 error" → Report shows 1 error (not 6)
  - If native shows "7 warnings" → Report shows 7 warnings (not 14)
- **Consistent Across Runs:** Same project + Same configuration = IDENTICAL counts, every execution
- **100% Deterministic:** No timing variations, no machine dependencies, no edge cases
