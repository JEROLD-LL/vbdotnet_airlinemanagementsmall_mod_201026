# Spec Verification Command

You are verifying an existing specification and tasks list using the spec-verifier agent.

## Process Overview

This command is a simple wrapper that uses the **spec-verifier** subagent to verify specifications and tasks.

## Configuration

**Default Specs Directory (Single Point of Truth):**

```bash
# Set default path - this is the ONLY place where the default path is defined
DEFAULT_SPECS_DIR="leap-os/specs"
```

**All other references use this variable or accept user input.**

**CRITICAL RULE - Path Selection:**
- The command will prompt the user to specify the target path after execution
- User can choose: specific feature spec, directory with specs, or default path
- Keep the prompt simple and clear

## Step 1: Prompt User for Target Path

**Prompt the user with the following options:**

```
Please specify the target for verifying specifications:

1. Specific feature spec - Provide the path to a specific feature spec folder
   (e.g., "leap-os/specs/2025-12-02-feature-name")

2. Directory with specs - Provide the path to a directory containing multiple spec folders
   (e.g., "leap-os/specs" or "custom/path/to/specs")

3. Default path - Use the default path: $DEFAULT_SPECS_DIR

Please respond with:
- Option 1, 2, or 3, OR
- A path directly (will be treated as option 1 or 2 based on what the path points to)
```

**Wait for user response.**

## Step 2: Process User Response

**Extract user's response and determine the target:**

1. **If user selected "Option 3" or responded with "default" or "3"**:
   - Set: `SPECS_DIR="$DEFAULT_SPECS_DIR"`
   - Set: `SKIP_DISCOVERY=false`
   - Proceed to Step 3

2. **If user selected "Option 1" or "Option 2", or provided a path directly**:
   - Extract the path from user response: `USER_PATH="[extracted-path]"`
   - Determine if `USER_PATH` is a specific spec folder or a parent directory:
   ```bash
   # Check if path is a specific spec folder (contains spec.md, tasks.md, and planning/requirements.md)
   if [ -f "$USER_PATH/spec.md" ] && [ -f "$USER_PATH/tasks.md" ] && [ -f "$USER_PATH/planning/requirements.md" ]; then
       # This is a specific spec folder
       SPEC_PATH="$USER_PATH"
       SPEC_FOLDERS=("$SPEC_PATH")
       SKIP_DISCOVERY=true
       # Skip Step 3, proceed directly to Step 4
   else
       # This is a parent directory - will discover all specs in Step 3
       SPECS_DIR="$USER_PATH"
       SKIP_DISCOVERY=false
       # Proceed to Step 3
   fi
   ```

3. **If user response is unclear or invalid**:
   - OUTPUT to user: "Invalid response. Please provide option 1, 2, or 3, or a valid path."
   - Return to Step 1 and prompt again

## Step 3: Discover Available Specs (SKIP if specific spec provided)

**ONLY execute this step if `SKIP_DISCOVERY=false`** (i.e., user selected option 2 or 3, or provided a directory path):

Check if `$SPECS_DIR` exists and discover all valid spec folders:

```bash
# Check if specs directory exists
if [ ! -d "$SPECS_DIR" ]; then
    echo "Specs directory not found: $SPECS_DIR"
    if [ "$SPECS_DIR" = "$DEFAULT_SPECS_DIR" ]; then
        OUTPUT to user: "Default specs directory not found: $SPECS_DIR. No specs to verify. Please create specs or provide a path explicitly."
        STOP execution
    else
        OUTPUT to user: "Specs directory not found: $SPECS_DIR. Please verify the path and try again."
        STOP execution
    fi
fi

# Find all spec folders (directories that contain spec.md, tasks.md, and planning/requirements.md)
SPEC_FOLDERS=()
for dir in "$SPECS_DIR"/*; do
    if [ -d "$dir" ] && [ -f "$dir/spec.md" ] && [ -f "$dir/tasks.md" ] && [ -f "$dir/planning/requirements.md" ]; then
        SPEC_FOLDERS+=("$dir")
    fi
done

# Check if any specs found
if [ ${#SPEC_FOLDERS[@]} -eq 0 ]; then
    if [ "$SPECS_DIR" = "$DEFAULT_SPECS_DIR" ]; then
        OUTPUT to user: "No valid spec folders found in default directory: $SPECS_DIR. Each spec folder must contain spec.md, tasks.md, and planning/requirements.md. No specs to verify."
        STOP execution
    else
        OUTPUT to user: "No valid spec folders found in $SPECS_DIR. Each spec folder must contain spec.md, tasks.md, and planning/requirements.md. Please verify the path or create specs first."
        STOP execution
    fi
fi

echo "Found ${#SPEC_FOLDERS[@]} spec folder(s) to verify"
```

**If specific spec was provided in Step 2** (`SKIP_DISCOVERY=true`):
- Proceed directly to Step 4 (no folder checks needed)

## Step 4: Use Spec-Verifier Agent

**For the current spec being processed:**

Use the **spec-verifier** subagent to verify the specification and tasks list.

**CRITICAL INSTRUCTIONS TO PASS TO SPEC-VERIFIER**:

When calling the spec-verifier agent, provide these explicit instructions:

```
MANDATORY INSTRUCTIONS FOR VERIFICATION:

1. FOCUS: Verify the mapping between spec.md and tasks.md - ensure all requirements in spec.md have corresponding tasks in tasks.md.

2. VERIFICATION TASKS:
   - Verify requirements accuracy against user Q&A
   - Check structural integrity of all files
   - Analyze visual alignment (if visuals exist)
   - Validate reusability opportunities
   - Verify limited testing approach (2-8 tests per task group)
   - Create verification report at $SPEC_PATH/verification/spec-verification.md

3. NO GIT ACTIONS: Do NOT perform any git operations (commit, push, pull, add, status, diff, etc.). Never run git commands or perform any git-related actions.
```

Provide the spec-verifier with:

- The spec folder path: `$SPEC_PATH` (use the variable)
- The requirements from `$SPEC_PATH/planning/requirements.md` (if it exists)
- The spec document: `$SPEC_PATH/spec.md`
- The tasks list: `$SPEC_PATH/tasks.md`
- Any visual assets in `$SPEC_PATH/planning/visuals/` (if present)
- Any Q&A data or user responses that were used during requirements gathering (if available)

The spec-verifier will:

1. Verify requirements accuracy against user Q&A
2. Check structural integrity of all files
3. Analyze visual alignment (if visuals exist)
4. Validate reusability opportunities
5. Verify limited testing approach (2-8 tests per task group)
6. Create a verification report at `$SPEC_PATH/verification/spec-verification.md`

**Hard constraint (no extra outputs):**

- The spec-verifier will create the verification report at `$SPEC_PATH/verification/spec-verification.md`
- Do **NOT** create additional `.md` files, reports, or summaries beyond the verification report
- Do **NOT** create any combined summary report that aggregates multiple spec verification reports
- Do **NOT** generate scripts

**If processing multiple specs:**

- After completing verification for the current spec, move to the next spec in `SPEC_FOLDERS` and repeat Step 4
- Each spec will have its own individual verification report at `$SPEC_PATH/verification/spec-verification.md`

## Step 5: Inform the User

After spec-verifier completes for the current spec (or all specs if processing multiple), display the summary output from the agent.

**For each verified spec:**

The verification report has been created at:

- `$SPEC_PATH/verification/spec-verification.md`

**If multiple specs were processed:**

- List each spec that was verified
- Each spec has its own verification report (no combined summary report is created)

Review the individual verification reports for any issues or recommendations.

## Important Notes

- **Path Selection**: The command will prompt the user to select the target path (specific spec, directory, or default) after execution. This keeps the implementation simple and clear.
- **Spec Requirements**: Only specs with required files (spec.md, tasks.md, and planning/requirements.md) will be verified. Specs missing any of these files will be skipped.
- **Multiple Specs Support**: If a directory path is provided, the command processes all valid specs sequentially, one at a time.
- **Individual Reports Only**: Each spec gets its own verification report. Do **NOT** create any combined summary report that aggregates multiple spec verification reports.
- The spec-verifier agent performs comprehensive verification including:

  - Requirements accuracy check
  - Structural integrity validation
  - Visual design alignment (if visuals exist)
  - Reusability validation
  - Test writing limits verification (2-8 tests per task group)
  - Over-engineering detection

- The verification report will contain detailed findings, critical issues, minor issues, and recommendations
- **NO GIT ACTIONS**: Do **NOT** perform any git operations (commit, push, pull, add, etc.). Never run git commands or perform any git-related actions
