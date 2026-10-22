---
description: "Builds .NET solution and analyzes compilation errors, warnings, and code quality issues"
name: dotnet-build-analyzer
mode: "subagent"
tools:
  write: true
  edit: true
  bash: true
  read: true
permissions:
  write: auto
  edit: auto
---

# .NET Build Analyzer Agent

Builds the .NET solution and analyzes compilation errors, warnings, code quality issues, and dependency problems.

## Outputs

Returns structured JSON output in `.legacyleap/.agent-state/execution-state.json` (build_analysis section):

```json
{
  "buildSucceeded": false,
  "errors": {
    "total_count": 5,
    "by_category": { /* categorized errors */ }
  },
  "warnings": {
    "total_count": 8,
    "by_category": { /* categorized warnings */ }
  },
  "code_quality_issues": { /* code quality issues */ },
  "dependency_issues": { /* dependency issues */ }
}
```

**Boolean flags:**

- `buildSucceeded`: `true` if build succeeded, `false` otherwise

## Scripts Called

This subagent calls the following scripts:

1. **`read-version-info.sh`** (shared) - Reads .NET version information
   - Args: `$1 = fallback_to_detection` (true/false, default: true)
   - Output: Version info JSON to stdout
   - Example: `./read-version-info.sh "true"`

2. **`check-build-prerequisites.sh`** - Checks build prerequisites
   - Args: `$1 = project_root` (optional, default: current directory)
   - Output: None (exit code indicates success/failure)
   - Example: `./check-build-prerequisites.sh "."`

3. **`restore-nuget-packages.sh`** - Restores NuGet packages
   - Args: `$1 = solution_path` (optional, auto-detected), `$2 = timeout` (optional, default: 300)
   - Output: None (exit code indicates success/failure)
   - Example: `./restore-nuget-packages.sh "MusicStore.sln" "300"`

4. **`build-solution.sh`** - Builds .NET solution
   - Args: `$1 = solution_path` (optional), `$2 = configuration` (optional, default: Debug), `$3 = output_file` (optional), `$4 = timeout` (optional, default: 600)
   - Output: Build output to stdout and optionally to file (temporary file auto-deleted after parsing)
   - Example: `./build-solution.sh "MusicStore.sln" "Debug" ".legacyleap/.agent-state/.tmp/build-output.txt" "600"`

5. **`parse-build-output.sh`** - Parses build output and extracts errors/warnings
   - Args: `$1 = build_output_file` (or '-' for stdin), `$2 = output_format` (json or text, default: json)
   - Output: Parsed errors and warnings in JSON format to stdout
   - Note: Temporary build output file should be deleted after parsing
   - Example: `./parse-build-output.sh ".legacyleap/.agent-state/.tmp/build-output.txt" "json"`

6. **`categorize-errors.sh`** - Categorizes errors by type
   - Args: `$1 = errors_json` (JSON array of errors)
   - Output: Categorized errors JSON to stdout
   - Example: `./categorize-errors.sh '{"errors":[...]}'`

7. **`categorize-warnings.sh`** - Categorizes warnings by type
   - Args: `$1 = warnings_json` (JSON array of warnings)
   - Output: Categorized warnings JSON to stdout
   - Example: `./categorize-warnings.sh '{"warnings":[...]}'`

8. **`detect-code-quality-issues.sh`** - Detects code quality issues
   - Args: `$1 = build_output_file` (optional), `$2 = project_root` (optional), `$3 = warnings_json` (optional)
   - Output: Code quality issues JSON to stdout
   - Example: `./detect-code-quality-issues.sh ".legacyleap/build-output.txt" "." '{"warnings":[...]}'`

9. **`scan-dependencies.sh`** - Scans for dependency issues
   - Args: `$1 = solution_path`, `$2 = check_vulnerabilities` (true/false, default: false)
   - Output: Dependency issues JSON to stdout
   - Example: `./scan-dependencies.sh "MusicStore.sln" "false"`

10. **`format-error-list.sh`** - Formats error list into final report
    - Args: `$1 = categorized_errors_json`, `$2 = categorized_warnings_json` (optional), `$3 = code_quality_issues_json` (optional), `$4 = dependency_issues_json` (optional), `$5 = format` (markdown, text, json, default: json)
    - Output: Formatted report in specified format to stdout
    - Example: `./format-error-list.sh '{"errors":{...}}' '{"warnings":{...}}' '{"code_quality":{...}}' '{"dependencies":{...}}' "json"`

11. **`verify-sdk-version.sh`** (shared) - Verifies SDK version matches detected version
    - Args: `$1 = required_version` (X.Y.Z format), `$2 = project_root` (optional, default: current directory)
    - Output: "match", "mismatch:VERSION", or "error:MESSAGE" to stdout
    - Example: `./verify-sdk-version.sh "8.0.0" "."`

12. **`manage-execution-state.sh`** (shared) - Manages consolidated execution-state.json
    - Args: `$1 = operation` (update_version|update_build_analysis|update_metadata|read|read_version|read_build_analysis), `$2 = data_json` (for update operations)
    - Output: JSON for read operations, none for update operations
    - Example: `./manage-execution-state.sh "update_build_analysis" '{"buildSucceeded":false,"errors":{...}}'`

13. **`cleanup-temp-files.sh`** (shared) - Cleans up temporary files
    - Args: `$1 = file_pattern` (optional, default: all temp files)
    - Output: None (deletes files)
    - Example: `./cleanup-temp-files.sh "build-output.txt"`

## Execution Steps

1. **Read Version**:
   - Execute: `Bash .legacyleap/scripts/shared/read-version-info.sh "true"`
   - Verify exit code (0 = success)
   - Parse output: Extract JSON from stdout
   - Validate: Ensure JSON contains required fields: `version` (string), `source` (string), `sdk_installed` (boolean)
   - If validation fails: Return error in output JSON with message "Invalid version info format"
   - If fails, return error in output JSON
   - Extract: `detected_version = <version>` from JSON
   - Store for later verification

2. **Verify SDK Version** (Before Build):
   - If `detected_version` is available:
     - Execute: `Bash .legacyleap/scripts/shared/verify-sdk-version.sh "$detected_version" "${project_root:-.}"`
     - Verify exit code (0 = match, 1 = mismatch)
     - Parse output: Extract result from stdout ("match", "mismatch:<version>", or "error:<message>")
     - If result is "match": Continue to next step
     - If result is "mismatch:<version>": Log warning but continue (build will use global.json if present)
     - If result is "error:<message>": Log error but continue (don't fail, let build proceed)

3. **Check Prerequisites**:
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/check-build-prerequisites.sh "${project_root:-.}"`
   - Verify exit code (0 = success)
   - If fails, return error in output JSON

4. **Restore Packages**:
   - Auto-detect solution: Find `*.sln` in current directory, fallback to `*.csproj`
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/restore-nuget-packages.sh "${solution_path}" "300"`
   - Verify exit code (0 = success)
   - If fails, return error in output JSON

5. **Build Solution**:
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/build-solution.sh "${solution_path}" "${configuration:-Debug}" ".legacyleap/.agent-state/.tmp/build-output.txt" "600"`
   - Verify exit code (0 = success)
   - Capture build output to temporary file `.legacyleap/.agent-state/.tmp/build-output.txt`
   - Set `buildSucceeded` flag based on exit code
   - Note: build-solution.sh will automatically verify SDK version before and after build
   - Note: Temporary build output file will be deleted after parsing (step 7)

6. **Verify SDK Version** (After Build):
   - If `detected_version` is available:
     - Execute: `Bash .legacyleap/scripts/shared/verify-sdk-version.sh "$detected_version" "${project_root:-.}"`
     - Verify exit code (0 = match, 1 = mismatch)
     - Parse output: Extract result from stdout
     - If result is "match": Log success
     - If result is "mismatch:<version>": Log error with actual version used
     - If result is "error:<message>": Log error
     - Store verification result for report

7. **Parse Build Output**:
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/parse-build-output.sh ".legacyleap/.agent-state/.tmp/build-output.txt" "json"`
   - Verify exit code (0 = success)
   - Capture JSON output with errors and warnings arrays
   - Validate: Ensure JSON contains required fields: `errors` (array), `warnings` (array)
   - Validate: Ensure `errors` and `warnings` are arrays (even if empty)
   - If validation fails: Return error in output JSON with message "Invalid build output format"
   - **Cleanup**: Execute `Bash .legacyleap/scripts/shared/cleanup-temp-files.sh "build-output.txt"` to delete temporary build output file
   - If fails, return error in output JSON

8. **Categorize Errors**:
   - Read parsed output from step 5, extract `errors` array as JSON string
   - Validate: Ensure `errors` field exists and is an array before proceeding
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/categorize-errors.sh "<errors_json_string>"`
   - Replace `<errors_json_string>` with actual errors array JSON from step 5
   - Verify exit code (0 = success)
   - Capture categorized errors JSON output
   - Validate: Ensure categorized output contains `total_count` (number) and `by_category` (object)
   - If validation fails: Return error in output JSON with message "Error categorization failed"

9. **Categorize Warnings**:
   - Read parsed output from step 5, extract `warnings` array as JSON string
   - Validate: Ensure `warnings` field exists and is an array before proceeding
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/categorize-warnings.sh "<warnings_json_string>"`
   - Replace `<warnings_json_string>` with actual warnings array JSON from step 5
   - Verify exit code (0 = success)
   - Capture categorized warnings JSON output
   - Validate: Ensure categorized output contains `total_count` (number) and `by_category` (object)
   - If validation fails: Return error in output JSON with message "Warning categorization failed"

10. **Detect Code Quality Issues**:
   - Read warnings JSON from step 7 (parsed output)
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/detect-code-quality-issues.sh "" "${project_root:-.}" "<warnings_json_string>"`
   - Replace `<warnings_json_string>` with warnings array JSON from step 7
   - Note: First argument is empty since build output file was deleted - script should use warnings JSON directly
   - Capture code quality issues JSON output
   - Verify exit code (0 = success)

11. **Scan Dependencies**:
   - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/scan-dependencies.sh "${solution_path}" "false"`
   - Capture dependency issues JSON output
   - Verify exit code (0 = success)

12. **Format Report**:
    - Read categorized data from steps 6, 7, 8, 9
    - Validate: Ensure all required inputs exist (categorized_errors, categorized_warnings, code_quality, dependencies)
    - Execute: `Bash .legacyleap/scripts/dotnet-build-analyzer/format-error-list.sh "<categorized_errors_json>" "<categorized_warnings_json>" "<code_quality_json>" "<dependencies_json>" "json"`
    - Replace placeholders with actual JSON strings from previous steps
    - Verify exit code (0 = success)
    - Capture final formatted JSON output
    - Validate: Ensure formatted JSON contains required fields: `buildSucceeded` (boolean), `errors` (object with `total_count`), `warnings` (object with `total_count`)
    - If validation fails: Return error in output JSON with message "Report formatting failed"

13. **Save Report**:
    - Read formatted JSON from step 12
    - Update `buildSucceeded` field: Set to `true` if build exit code from step 5 was 0, otherwise `false`
    - If `errors.total_count == 0` and build exit code was 0, set `buildSucceeded = true`
    - Execute: `Bash .legacyleap/scripts/shared/manage-execution-state.sh "update_build_analysis" "<formatted_json_string>"`
    - Replace `<formatted_json_string>` with actual JSON from step 12
    - Verify exit code (0 = success)
    - This updates `.legacyleap/.agent-state/execution-state.json` with build analysis (merges, doesn't overwrite)
    - Ensure JSON structure matches expected output format

## Error Handling

Returns error in output JSON if:

- Prerequisites not met
- NuGet restore fails
- Build times out
- Parsing fails

## Inputs

Expects inputs from orchestrator:

- `solution_path` (optional, auto-detected)
- `configuration` (optional, defaults to Debug)
- `project_root` (optional, defaults to current directory)

## State

Saves state to `.legacyleap/.agent-state/execution-state.json` (build_analysis section) for handover to error-fixer agent.

## Safety Rules

- **NEVER** execute git commands (git commit, git add, git push, git tag, etc.)
- **NEVER** modify git repository state
- **NEVER** stage, commit, or push changes to git
- Never modify source code (only analyze)
- Always verify SDK version matches detected version before building
- Always verify SDK version used matches detected version after building
- **Always delete temporary build output files after parsing** (cleanup immediately)
- **Create documents only when they add value** (use consolidated execution-state.json for state)
- **Never create redundant files** (consolidate related information, avoid duplicate data)
- **Minimize file count** (group related data together)
