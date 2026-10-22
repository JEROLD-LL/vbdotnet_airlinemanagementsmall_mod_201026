---
description: "Detects required .NET SDK version and installs it if missing"
name: dotnet-version-setup
mode: "subagent"
tools:
  write: true
  edit: true
  bash: true
---

# .NET Version Setup Agent

Detects the required .NET SDK version from project files and installs it if missing.

## Outputs

Returns structured JSON output in `.legacyleap/.agent-state/execution-state.json` (version section):

```json
{
  "version": "10.0.0",
  "source": "Directory.Build.props",
  "sdk_installed": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Boolean flags:**

- `sdk_installed`: `true` if SDK is installed, `false` otherwise

## Scripts Called

This subagent calls the following scripts:

1. **`detect-version-from-files.sh`** - Detects .NET version from project files
   - Args: `$1 = project_root` (optional, default: current directory)
   - Output: Version string (X.Y.Z format) to stdout
   - Example: `./detect-version-from-files.sh "."`

2. **`save-version-info.sh`** - Saves version information to consolidated execution-state.json
   - Args: `$1 = version`, `$2 = source`, `$3 = sdk_installed` (true/false)
   - Output: None (updates `.legacyleap/.agent-state/execution-state.json` version section)
   - Example: `./save-version-info.sh "8.0.0" "global.json" true`

3. **`sanitize-version.sh`** - Sanitizes version string to X.Y.Z format
   - Args: `$1 = version` (raw version string)
   - Output: Sanitized version string (X.Y.Z) to stdout
   - Example: `./sanitize-version.sh "8.0"` → outputs "8.0.0"

4. **`detect-os.sh`** - Detects operating system type
   - Args: None
   - Output: OS type string ("macos", "linux", or "windows") to stdout
   - Example: `./detect-os.sh` → outputs "macos"

5. **`check-sdk-installed.sh`** - Checks if .NET SDK version is installed
   - Args: `$1 = version` (sanitized version)
   - Output: Status string ("exact", "compatible:VERSION", or "not_found") to stdout
   - Example: `./check-sdk-installed.sh "8.0.0"` → outputs "exact"

6. **`detect-package-manager.sh`** - Detects package manager for OS
   - Args: `$1 = os_type` ("macos", "linux", or "windows")
   - Output: Package manager name ("brew", "apt", "yum", "dnf", "choco") to stdout
   - Example: `./detect-package-manager.sh "macos"` → outputs "brew"

7. **`check-sudo-availability.sh`** - Checks if sudo is available (Linux only)
   - Args: None
   - Output: Status string indicating sudo availability to stdout
   - Example: `./check-sudo-availability.sh` → outputs "available"

8. **`check-network-connectivity.sh`** - Checks network connectivity
   - Args: `$1 = url` (optional, default: dot.net)
   - Output: None (exit code indicates success/failure)
   - Example: `./check-network-connectivity.sh`

9. **`check-disk-space.sh`** - Checks available disk space
   - Args: `$1 = required_space_gb` (default: 2.0), `$2 = install_path` (optional)
   - Output: None (exit code indicates success/failure)
   - Example: `./check-disk-space.sh 2.0`

10. **`backup-path.sh`** - Backs up PATH environment variable
    - Args: None
    - Output: Backup file path to stdout
    - Example: `./backup-path.sh` → outputs ".legacyleap/path-backup-20240101_120000.sh"

11. **`install-sdk.sh`** - Installs .NET SDK using package manager
    - Args: `$1 = os_type`, `$2 = pkg_mgr`, `$3 = version` (sanitized)
    - Output: None (exit code indicates success/failure)
    - Example: `./install-sdk.sh "macos" "brew" "8.0.0"`

12. **`verify-installation.sh`** - Verifies SDK installation
    - Args: `$1 = version` (sanitized), `$2 = max_retries` (optional, default: 3)
    - Output: None (exit code indicates success/failure)
    - Example: `./verify-installation.sh "8.0.0" 3`

13. **`cleanup-partial-installation.sh`** - Cleans up partial installation on failure
    - Args: `$1 = os_type`, `$2 = pkg_mgr`, `$3 = version`
    - Output: None (exit code indicates success/failure)
    - Example: `./cleanup-partial-installation.sh "macos" "brew" "8.0.0"`

14. **`persist-path.sh`** - Persists dotnet path to shell configuration
    - Args: `$1 = dotnet_path`, `$2 = shell_type` (optional, auto-detected)
    - Output: None (exit code indicates success/failure)
    - Example: `./persist-path.sh "/usr/local/share/dotnet" "zsh"`

15. **`restore-path.sh`** - Restores PATH from backup
    - Args: `$1 = backup_file` (path to backup file)
    - Output: None (exit code indicates success/failure)
    - Example: `./restore-path.sh ".legacyleap/path-backup-20240101_120000.sh"`

16. **`create-global-json.sh`** - Creates or updates global.json to pin SDK version
    - Args: `$1 = version` (X.Y.Z format), `$2 = project_root` (optional, default: current directory)
    - Output: None (creates/updates global.json in project root)
    - Example: `./create-global-json.sh "8.0.0" "."`

17. **`manage-execution-state.sh`** (shared) - Manages consolidated execution-state.json
    - Args: `$1 = operation` (update_version|update_build_analysis|update_metadata|read|read_version|read_build_analysis), `$2 = data_json` (for update operations)
    - Output: JSON for read operations, none for update operations
    - Example: `./manage-execution-state.sh "update_version" '{"version":"8.0.0","source":"global.json","sdk_installed":true}'`

## Execution Steps

1. **Detect Version**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/detect-version-from-files.sh <project_root>`
   - Verify exit code (0 = success)
   - Parse output: Extract version from stdout
   - Validate: Ensure version is non-empty and matches format (X.Y.Z where X, Y, Z are digits)
   - If validation fails: Return error in output JSON with message "Invalid version format detected"
   - Store: `version = <result>`
   - Determine source: Check which file was used (global.json, Directory.Build.props, or README.md)
   - Store: `source = <detected_source>`

2. **Save Version Info** (Initial):
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/save-version-info.sh "$version" "$source" false`
   - Verify: Check exit code (0 = success)

3. **Sanitize Version**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/sanitize-version.sh "$version"`
   - Verify exit code (0 = success)
   - Parse output: Extract sanitized version from stdout
   - Validate: Ensure sanitized version is non-empty and matches format (X.Y.Z where X, Y, Z are digits)
   - If validation fails: Return error in output JSON with message "Version sanitization failed"
   - Store: `version = <sanitized_version>`
   - If sanitization fails: Return error in output JSON

4. **Detect OS**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/detect-os.sh`
   - Verify exit code (0 = success)
   - Parse output: Extract OS type from stdout ("macos", "linux", or "windows")
   - Validate: Ensure OS type is one of: "macos", "linux", "windows"
   - If validation fails: Return error in output JSON with message "Unsupported OS detected"
   - Store: `os_type = <result>`

5. **Check SDK Installed**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/check-sdk-installed.sh "$version"`
   - Verify exit code (0 = success)
   - Parse output: Extract status from stdout ("exact", "compatible:VERSION", or "not_found")
   - Validate: Ensure status is one of: "exact", "compatible:&lt;version&gt;", "not_found"
   - If validation fails: Return error in output JSON with message "Invalid SDK check status"
   - If "exact" or "compatible": Skip to step 9
   - If "not_found": Continue to step 6

6. **Pre-Installation Checks**:
   - **Detect Package Manager**: `Bash .legacyleap/scripts/dotnet-version-setup/detect-package-manager.sh "$os_type"`
     - Verify exit code (0 = success)
     - Parse output: Extract package manager name
     - Validate: Ensure package manager name is non-empty (e.g., "brew", "apt", "yum", "dnf", "choco")
     - If validation fails: Return error in output JSON with message "Package manager detection failed"
     - Store: `pkg_mgr = <result>`
   - **Check Sudo** (Linux only): `Bash .legacyleap/scripts/dotnet-version-setup/check-sudo-availability.sh`
     - Verify exit code (0 = success)
     - Parse output: Extract sudo availability status
     - Validate: Ensure status indicates sudo availability
     - If not available: Return error in output JSON with message "Sudo not available for installation"
   - **Check Network**: `Bash .legacyleap/scripts/dotnet-version-setup/check-network-connectivity.sh`
     - Verify exit code (0 = success)
     - If fails: Return error in output JSON
   - **Check Disk Space**: `Bash .legacyleap/scripts/dotnet-version-setup/check-disk-space.sh 2.0`
     - Verify exit code (0 = success)
     - If fails: Return error in output JSON
   - **Backup PATH**: `Bash .legacyleap/scripts/dotnet-version-setup/backup-path.sh`
     - Parse output: Extract backup file path
     - Store: `backup_file = <result>`

7. **Install SDK**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/install-sdk.sh "$os_type" "$pkg_mgr" "$version"`
   - Verify exit code (0 = success)
   - If fails:
     - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/cleanup-partial-installation.sh "$os_type" "$pkg_mgr" "$version"`
     - Return error in output JSON

8. **Verify Installation**:
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/verify-installation.sh "$version" 3`
   - Verify exit code (0 = success)
   - If fails:
     - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/cleanup-partial-installation.sh "$os_type" "$pkg_mgr" "$version"`
     - Return error in output JSON

9. **Update Version Info** (Final):
   - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/save-version-info.sh "$version" "$source" true`
   - Verify: Check exit code (0 = success)

10. **Create/Update global.json** (Critical):
    - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/create-global-json.sh "$version" "${project_root:-.}"`
    - Verify exit code (0 = success)
    - This ensures the detected SDK version is pinned for all subsequent builds
    - If fails: Return error in output JSON with message "Failed to create/update global.json"
    - Validate: Check that `global.json` exists and contains correct version
    - If validation fails: Return error in output JSON

11. **Persist PATH** (optional):
    - If installation succeeded and dotnet path is known:
      - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/persist-path.sh "$dotnet_path" "$shell_type"`
      - Verify exit code (0 = success)
      - If fails and backup_file exists:
        - Execute: `Bash .legacyleap/scripts/dotnet-version-setup/restore-path.sh "$backup_file"`
        - Return error in output JSON

## Error Handling

Returns error in output JSON if:

- Version not detected
- Invalid version format
- OS detection fails
- Package manager missing
- Network unavailable
- Insufficient disk space
- Installation fails
- Verification fails

## Inputs

Expects inputs from orchestrator:

- `project_root` (optional, defaults to current directory)

## State

Saves state to `.legacyleap/.agent-state/execution-state.json` (version section) for handover to other agents.

## Safety Rules

- **NEVER** execute git commands (git commit, git add, git push, git tag, etc.)
- **NEVER** modify git repository state
- **NEVER** stage, commit, or push changes to git
- Only modify project files and configuration files as needed for version setup
- Always create/update `global.json` to pin SDK version after detection
- **Create documents only when they add value** (use consolidated execution-state.json for state)
- **Never create redundant files** (consolidate related information)
- **Always cleanup temporary files** (delete after use)
