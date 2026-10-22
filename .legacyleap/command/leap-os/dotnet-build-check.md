---
description: "Builds .NET solution and reports build status with detailed report"
agent: dotnet-build-check
execution_model: "direct"
forbidden_agents:
  - dotnet-build-analyzer
  - dotnet-auto-fix
  - dotnet-error-fixer
  - dotnet-version-setup
---

# Build Check Command

This command builds your .NET solution and provides a simple status report with a detailed build report document.

## Configuration (Optional)

The command can optionally read the target code path from an existing `metadata.json` file. It searches for this file in the following locations (in order):

1. Same level as `.legacyleap` folder (parent directory)
2. Up to 2 directory levels above (../../)
3. If not found anywhere: Defaults to `../../../modernize/target/` relative to command location (backward compatible)

### metadata.json Format

If `metadata.json` exists, it should contain:

```json
{
  "modernize": "../../../modernize/target/"
}
```

- **`modernize`**: Path to the target directory containing the code to be built
  - Can be relative (e.g., `"../../../modernize/target/"`) or absolute (e.g., `"/path/to/modernize/target/"`)
  - Relative paths are resolved from the directory containing `metadata.json`

### Important Notes

- **READ-ONLY OPERATION:** The command NEVER creates or modifies `metadata.json` file
- **Search Scope:** The command searches for existing `metadata.json` in specific directories only
- **Default Path:** When `metadata.json` is not found, defaults to `../../../modernize/target/` relative to command location
- **Backward Compatible:** If `metadata.json` doesn't exist, the command still works using the default path
- **No Initialization:** Configuration file must be created separately before running this command

## What It Does

The command runs a streamlined build workflow that:

- **Finds and reads** target path from existing `metadata.json` (if available) and changes working directory
- **Builds** the solution with specified configuration
- **Generates** a formatted build report document
- **Returns** simple success/failure status with key metrics

The command provides a lightweight alternative to the full auto-fix workflow when you only need to check build status without modifying source code.

## When to Use

Use this command when you want to:

- Verify your code compiles successfully
- Get a quick build status check
- Generate a detailed build report document
- Check build health without fixing errors
- Validate build before committing changes

The command provides a lightweight alternative to the full auto-fix workflow when you only need to check build status.
