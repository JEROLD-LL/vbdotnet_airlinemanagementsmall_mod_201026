---
description: "End-to-end .NET error fixing: automatically detects/installs .NET version, analyzes build errors, and fixes them iteratively"
agent: dotnet-auto-fix
---

# Auto-Fix Command

This command automatically fixes .NET compilation errors in your project by orchestrating a complete workflow from version detection to error resolution.

## Configuration (Optional)

The command can optionally read the target code path from a `metadata.json` file located at the same level as the `.legacyleap` folder.

### metadata.json Format

Create `metadata.json` at the same level as `.legacyleap`:

```json
{
  "modernize": "../../../modernize/target/"
}
```

- **`modernize`**: Path to the target directory containing the code to be fixed
  - Can be relative (e.g., `"../../../modernize/target/"`) or absolute (e.g., `"/path/to/modernize/target/"`)
  - Relative paths are resolved from the directory containing `metadata.json`
  - If `metadata.json` doesn't exist or `modernize` key is missing, the command works in the current directory (backward compatible)

## What It Does

The command runs a fully automated pipeline that:

- **Reads target path** from `metadata.json` (if available) and changes working directory
- **Detects and verifies** the required .NET SDK version from your project files
- **Ensures** a compatible SDK is installed on your system
- **Builds** the solution and scans for compilation errors, warnings, and code quality issues
- **Auto-fixes** errors iteratively until the project builds cleanly or iteration limits are reached

## When to Use

Use this command when you want to:

- Fix all compilation errors in your .NET project automatically
- Ensure your project builds successfully without manual intervention
- Get a comprehensive analysis of build issues and their resolutions

The command handles the entire process end-to-end, from checking .NET version requirements to applying fixes and verifying the final build status.
