# Update Specification Process

You are helping me update existing specifications based on gap analysis reports or human feedback reports. This process updates requirements.md with findings from reports, then regenerates spec.md and tasks.md using AgentOS default agents for each available spec.

This process supports two execution modes:
- **Gap based update mode**: Uses gap analysis reports from `gap_reports/` directory
- **Feedback based update mode**: Uses human feedback reports from `feedback_reports/` directory

This process follows 3 main phases:

Process overview:
- PHASE 1: Update requirements.md based on reports (gap or feedback)
- PHASE 2: Regenerate spec.md from requirements.md
- PHASE 3: Regenerate tasks.md from spec.md

Follow each of these phases and their individual workflows IN SEQUENCE:

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

## Multi-Phase Process:

### PHASE 0: Determine Target Specs

**Step 1: Prompt User for Target Path**

**Prompt the user with the following options:**

```
Please specify the target for updating specifications:

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

**Step 2: Process User Response**

**Extract user's response and determine the target:**

1. **If user selected "Option 3" or responded with "default" or "3"**:
   - Set: `SPECS_DIR="$DEFAULT_SPECS_DIR"`
   - Set: `SKIP_DISCOVERY=false`
   - Proceed to Step 3

2. **If user selected "Option 1" or "Option 2", or provided a path directly**:
   - Extract the path from user response: `USER_PATH="[extracted-path]"`
   - Determine if `USER_PATH` is a specific spec folder or a directory:
   ```bash
   # Check if path is a specific spec folder (contains spec.md, tasks.md, and planning/requirements.md)
   if [ -f "$USER_PATH/spec.md" ] && [ -f "$USER_PATH/tasks.md" ] && [ -f "$USER_PATH/planning/requirements.md" ]; then
       # This is a specific spec folder
       SPEC_PATH="$USER_PATH"
       SPEC_FOLDERS=("$SPEC_PATH")
       SKIP_DISCOVERY=true
       # Skip Step 3, proceed directly to Step 4
   else
       # This is a directory - will discover all specs in Step 3
       SPECS_DIR="$USER_PATH"
       SKIP_DISCOVERY=false
       # Proceed to Step 3
   fi
   ```

3. **If user response is unclear or invalid**:
   - OUTPUT to user: "Invalid response. Please provide option 1, 2, or 3, or a valid path."
   - Return to Step 1 and prompt again

**Step 3: Discover Available Specs (SKIP if specific spec provided)**

**ONLY execute this step if `SKIP_DISCOVERY=false`** (i.e., user selected option 2 or 3, or provided a directory path):

Check if `$SPECS_DIR` exists and contains spec folders:

```bash
# Check if specs directory exists
if [ ! -d "$SPECS_DIR" ]; then
    echo "Specs directory not found: $SPECS_DIR"
    # DO NOT ask user for path - only use default or user-provided paths
    # If this is the default path and it doesn't exist, skip processing
    if [ "$SPECS_DIR" = "$DEFAULT_SPECS_DIR" ]; then
        OUTPUT to user: "Default specs directory not found: $SPECS_DIR. No specs to process. Please create specs or provide a path explicitly."
        STOP execution
    else
        # User provided a path that doesn't exist - inform and stop
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
    # DO NOT ask user for a different path - only inform them
    if [ "$SPECS_DIR" = "$DEFAULT_SPECS_DIR" ]; then
        OUTPUT to user: "No valid spec folders found in default directory: $SPECS_DIR. Each spec folder must contain spec.md, tasks.md, and planning/requirements.md. No specs to process."
        STOP execution
    else
        OUTPUT to user: "No valid spec folders found in $SPECS_DIR. Each spec folder must contain spec.md, tasks.md, and planning/requirements.md. Please verify the path or create specs first."
        STOP execution
    fi
fi

echo "Found ${#SPEC_FOLDERS[@]} spec folder(s) to process"
```

**Step 4: Select Execution Mode**

**After determining the target specs, prompt the user to select the execution mode:**

**Prompt the user with the following options:**

```
Please select the execution mode for updating specifications:

1. Gap based update mode - Use gap analysis reports from gap_reports/ directory
   (Reads all .md files from $SPEC_PATH/gap_reports/ and translates gap findings into requirements)

2. Feedback based update mode - Use human feedback reports from feedback_reports/ directory
   (Reads all .md files from $SPEC_PATH/feedback_reports/ and translates feedback into requirements)

Please respond with:
- Option 1 or 2, OR
- "gap" or "feedback" (short form)
```

**Wait for user response.**

**Process user response and set mode variables:**

```bash
# Process user response
if [[ "$USER_RESPONSE" =~ ^1$ ]] || [[ "$USER_RESPONSE" =~ ^[Gg]ap$ ]] || [[ "$USER_RESPONSE" =~ ^[Gg]ap[[:space:]]*based$ ]]; then
    # Gap based update mode (Option 1)
    UPDATE_MODE="gap"
    REPORTS_DIR_NAME="gap_reports"
    MODE_DESCRIPTION="gap analysis"
elif [[ "$USER_RESPONSE" =~ ^2$ ]] || [[ "$USER_RESPONSE" =~ ^[Ff]eedback$ ]] || [[ "$USER_RESPONSE" =~ ^[Ff]eedback[[:space:]]*based$ ]]; then
    # Feedback based update mode (Option 2)
    UPDATE_MODE="feedback"
    REPORTS_DIR_NAME="feedback_reports"
    MODE_DESCRIPTION="human feedback"
else
    # Invalid response
    OUTPUT to user: "Invalid response. Please provide option 1 or 2, or 'gap'/'feedback'."
    # Return to prompt and ask again
    # (Repeat Step 4)
fi
```

**Set the reports directory variable:**
```bash
# For each spec, the reports directory will be: $SPEC_PATH/$REPORTS_DIR_NAME/
# This variable will be used throughout the process
```

**After mode selection, proceed to Step 5.**

**Step 5: Process Spec(s)**

**If specific spec was provided in Step 1** (`SKIP_DISCOVERY=true`):
- Process only the single spec in `SPEC_FOLDERS` (which contains just one entry)
- Proceed directly to PHASE 1 for that spec

**If directory was provided or default used** (`SKIP_DISCOVERY=false`):
- Process each spec folder found in `SPEC_FOLDERS` sequentially:

```bash
for SPEC_PATH in "${SPEC_FOLDERS[@]}"; do
    echo "Processing spec: $SPEC_PATH"
    echo "Using $UPDATE_MODE based update mode ($MODE_DESCRIPTION reports)"
    # Continue to PHASE 1 for this spec
done
```

### PHASE 1: Update Requirements Based on Reports

**For each spec in SPEC_FOLDERS (or single spec if provided), execute the following:**

**Step 1: Verify Required Files Exist**

For the current `$SPEC_PATH`, verify that the required files exist:

```bash
# Check for required spec files
if [ -f "$SPEC_PATH/spec.md" ] && [ -f "$SPEC_PATH/tasks.md" ]; then
    echo "Required spec files found for $SPEC_PATH"
else
    echo "Missing required spec files in $SPEC_PATH"
    # Skip this spec and continue to next
    continue
fi

# Check for requirements.md
if [ -f "$SPEC_PATH/planning/requirements.md" ]; then
    echo "requirements.md found"
else
    echo "requirements.md not found in $SPEC_PATH"
    # Skip this spec and continue to next
    continue
fi

# Check for reports in the selected mode's reports folder
REPORTS_DIR="$SPEC_PATH/$REPORTS_DIR_NAME"
if [ -d "$REPORTS_DIR" ]; then
    # Count all available .md files in reports directory (at least 1 required)
    REPORT_COUNT=0
    for report_file in "$REPORTS_DIR"/*.md; do
        if [ -f "$report_file" ]; then
            REPORT_COUNT=$((REPORT_COUNT + 1))
        fi
    done
    
    if [ $REPORT_COUNT -ge 1 ]; then
        echo "Found $REPORT_COUNT $MODE_DESCRIPTION report(s) in $SPEC_PATH/$REPORTS_DIR_NAME"
    else
        echo "No $MODE_DESCRIPTION reports (.md files) found in $SPEC_PATH/$REPORTS_DIR_NAME"
        # Skip this spec and continue to next
        continue
    fi
else
    echo "$REPORTS_DIR_NAME directory not found: $REPORTS_DIR"
    # Skip this spec and continue to next
    continue
fi
```

**Verification Rules:**
- **REQUIRED**: `$SPEC_PATH/spec.md` must exist
- **REQUIRED**: `$SPEC_PATH/tasks.md` must exist
- **REQUIRED**: `$SPEC_PATH/planning/requirements.md` must exist
- **REQUIRED**: At least 1 report (any `.md` file) must exist in `$SPEC_PATH/$REPORTS_DIR_NAME/` directory
  - For Gap based mode: `$SPEC_PATH/gap_reports/`
  - For Feedback based mode: `$SPEC_PATH/feedback_reports/`

**IF any required files are missing for a spec:**
- Skip that spec and continue to the next spec
- Log which spec was skipped and why

**IF all required files are present, CONTINUE automatically to Step 2.**

**Step 2: Use Requirements-Updater Agent**

Once all required files are verified for the current spec, use the **requirements-updater** subagent to analyze reports (gap or feedback) and update requirements.md.

**CRITICAL: Pass execution mode to the agent**

Provide the requirements-updater with:
- **Spec path**: `$SPEC_PATH` (pass this variable to the agent)
- Target requirements: `$SPEC_PATH/planning/requirements.md`
- **Reports directory**: `$SPEC_PATH/$REPORTS_DIR_NAME/` (the agent will discover and read all `.md` files in this directory)
  - The agent should read ALL `.md` files found in `$SPEC_PATH/$REPORTS_DIR_NAME/` regardless of their names
  - At least 1 report file must be present (already verified in Step 1)
- **Execution mode**: `UPDATE_MODE` (pass this variable to the agent - value is either "gap" or "feedback")
  - This variable tells the agent which type of reports it's processing
  - The agent will use this to determine how to parse and understand the reports
  - **MANDATORY**: Always pass `UPDATE_MODE` variable to the requirements-updater agent

**When calling the requirements-updater agent, explicitly pass:**
```
UPDATE_MODE="$UPDATE_MODE"
SPEC_PATH="$SPEC_PATH"
REPORTS_DIR="$SPEC_PATH/$REPORTS_DIR_NAME"
TARGET_REQUIREMENTS="$SPEC_PATH/planning/requirements.md"
```

The requirements-updater will:
1. Receive and use the `UPDATE_MODE` variable to determine report type
2. Discover and read all available report files (any `.md` files) from `$SPEC_PATH/$REPORTS_DIR_NAME/` directory
3. Read and understand existing requirements.md structure
4. Parse reports based on mode:
   - If `UPDATE_MODE="gap"`: Parse gap analysis reports (architectural violations, code inventory, functional gaps)
   - If `UPDATE_MODE="feedback"`: Parse human feedback reports (user feedback, improvement suggestions, feature requests)
5. Translate findings from all reports into proper requirements
6. Update requirements.md with new requirements (minimal changes only)

**Hard constraint (no extra outputs):**
- Do **NOT** create any new `.md` files (no change logs, no reports, no summaries, no "final report").
- Do **NOT** create any scripts (Python or otherwise).
- Only modify the existing requirements file: `$SPEC_PATH/planning/requirements.md`.

**Step 3: Verify Phase 1 Completion for Current Spec**

After requirements-updater completes for the current spec, verify:
- requirements.md has been updated with findings from reports (gap analysis or feedback) translated to requirements
- Existing requirements are preserved
- Only minimal changes were made

**Then proceed to PHASE 2 for this spec.**

### PHASE 2: Regenerate Specification from Requirements

**For the current spec being processed:**

**Step 1: Use Spec-Writer Agent**

After requirements-updater has updated requirements.md for the current spec, use the **spec-writer** subagent to update spec.md from the updated requirements.md.

**CRITICAL INSTRUCTIONS TO PASS TO SPEC-WRITER**:

When calling the spec-writer agent, provide these explicit instructions:

```
MANDATORY INSTRUCTIONS FOR UPDATING SPEC.MD:

1. READ FIRST: Read the complete existing spec.md at $SPEC_PATH/spec.md and understand ALL existing content before making any changes.

2. UPDATE STRATEGY:
   - PRIMARY ACTION: Add new requirements from $SPEC_PATH/planning/requirements.md to appropriate sections
   - PRESERVE: Keep ALL existing content unless there's a clear conflict
   - THINK BEFORE REMOVING: Ask "Why remove this? Can I add instead?"
   - THINK BEFORE MODIFYING: Ask "Why modify this? Is it necessary?"
   - WHEN IN DOUBT: Add new content, don't remove or modify existing

3. VERIFY: After updating, ensure all original content is still present.

4. NO GIT ACTIONS: Do NOT perform any git operations (commit, push, pull, add, status, diff, etc.). Never run git commands or perform any git-related actions.
```

Provide the spec-writer with:
- The spec folder path: `$SPEC_PATH` (use the variable)
- The existing spec.md: `$SPEC_PATH/spec.md` (MUST be provided)
- The updated requirements from `$SPEC_PATH/planning/requirements.md`
- Any visual assets in `$SPEC_PATH/planning/visuals/` (if present)

**Hard constraint (no extra outputs):**
- The spec-writer must **only** update `$SPEC_PATH/spec.md`.
- Do **NOT** create additional `.md` planning docs, reports, summaries, or "final report" files.
- Do **NOT** generate scripts.

**Step 2: Verify Phase 2 Completion for Current Spec**

After spec-writer completes for the current spec, verify:
- spec.md has been updated with new requirements from updated requirements.md
- **CRITICAL CHECK**: Read the updated spec.md and verify:
  - Key existing sections are still present (Goal, User Stories, Specific Requirements, etc.)
  - Major existing content is preserved
  - New content has been added appropriately
- Specification is comprehensive and properly formatted

**If significant existing content appears to be missing**:
- Log the issue: "Content may have been removed from $SPEC_PATH/spec.md"
- Continue to PHASE 3 (agent will handle this in final summary)

**Then proceed to PHASE 3 for this spec.**

### PHASE 3: Regenerate Tasks from Specification

**For the current spec being processed:**

**Step 1: Use Tasks-List-Creator Agent**

After spec-writer has regenerated spec.md for the current spec, use the **tasks-list-creator** subagent to regenerate tasks.md from the updated spec.md.

**CRITICAL INSTRUCTIONS TO PASS TO TASKS-LIST-CREATOR**:

When calling the tasks-list-creator agent, provide these explicit instructions:

```
MANDATORY INSTRUCTIONS FOR UPDATING TASKS.MD:

1. READ FIRST: Read the complete existing tasks.md at $SPEC_PATH/tasks.md and understand ALL existing tasks before making any changes.

2. UPDATE STRATEGY:
   - PRIMARY ACTION: Add new tasks from $SPEC_PATH/spec.md for requirements that don't have corresponding tasks
   - PRESERVE: Keep ALL existing tasks unless there's a clear conflict
   - WHEN IN DOUBT: Add new tasks, don't remove or modify existing tasks

3. VERIFY: After updating, ensure all original tasks are still present.

4. NO GIT ACTIONS: Do NOT perform any git operations (commit, push, pull, add, status, diff, etc.). Never run git commands or perform any git-related actions.
```

Provide the tasks-list-creator with:
- The updated spec: `$SPEC_PATH/spec.md` (use the variable)
- The existing tasks.md: `$SPEC_PATH/tasks.md` (MUST be provided)
- The requirements from `$SPEC_PATH/planning/requirements.md`
- Any visual assets in `$SPEC_PATH/planning/visuals/` (if present)

The tasks-list-creator will:
1. Read the existing tasks.md completely to understand structure and preserve all existing tasks
2. Read the updated spec.md and requirements.md to identify new requirements needing tasks
3. Update tasks.md by adding new tasks while preserving ALL existing tasks
4. Ensure proper formatting and structure following AgentOS format

**Hard constraint (no extra outputs):**
- The tasks-list-creator must **only** update `$SPEC_PATH/tasks.md`.
- Do **NOT** create additional `.md` files, reports, summaries, or "final report" files.
- Do **NOT** generate scripts.

**Step 2: Verify Phase 3 Completion for Current Spec**

After tasks-list-creator completes for the current spec, verify:
- tasks.md has been regenerated from updated spec.md
- Existing tasks are preserved
- Tasks follow proper formatting and structure

**Step 3: Verify All Files Were Updated for Current Spec**

**CRITICAL**: After completing all 3 phases for the current spec, verify that ALL 3 required files were actually updated. If any file is not updated, automatically update it.

**For the current spec at `$SPEC_PATH`, verify and fix each file:**

1. **Verify requirements.md was updated**:
   - Check that `$SPEC_PATH/planning/requirements.md` exists
   - Verify the file contains new requirements from reports (gap analysis or feedback)
   - **If NOT updated**: Re-run PHASE 1 (requirements-updater agent) to update requirements.md
   - Verify again after re-running

2. **Verify spec.md was updated**:
   - Check that `$SPEC_PATH/spec.md` exists
   - Verify the file contains new content from updated requirements.md
   - **If NOT updated**: Re-run PHASE 2 (spec-writer agent) to update spec.md
   - Verify again after re-running

3. **Verify tasks.md was updated**:
   - Check that `$SPEC_PATH/tasks.md` exists
   - Verify the file contains new tasks for updated requirements
   - **If NOT updated**: Re-run PHASE 3 (tasks-list-creator agent) to update tasks.md
   - Verify again after re-running

**Verification and Auto-Fix Logic**:
- **If ALL 3 files exist and were updated**: Mark this spec as SUCCESS and proceed to next spec
- **If ANY file is missing or not updated**:
  - Identify which file(s) were not updated
  - Automatically re-run the corresponding phase(s) to update the missing file(s):
    - requirements.md not updated → Re-run PHASE 1
    - spec.md not updated → Re-run PHASE 2
    - tasks.md not updated → Re-run PHASE 3
  - After re-running, verify again that the file(s) are now updated
  - Repeat until all 3 files are verified as updated

**Before moving to next spec**:
- Ensure ALL 3 files are verified as updated (✓)
- Only proceed to next spec after all 3 files are confirmed updated

**After completing all 3 phases and verification (with auto-fix if needed) for the current spec, move to the next spec in SPEC_FOLDERS and repeat the process.**

## PHASE 4: Inform the user

After all specs have been processed, inform the user:

```
Specification update complete!

Processed ${#SPEC_FOLDERS[@]} spec(s) from $SPECS_DIR
Execution Mode: $UPDATE_MODE based update mode ($MODE_DESCRIPTION reports)

✅ Phase 1: Requirements updated with $MODE_DESCRIPTION findings
✅ Phase 2: Specification regenerated from updated requirements
✅ Phase 3: Tasks regenerated from updated specification

File Update Status for Each Spec:
[For each SPEC_PATH processed, list:]
- $SPEC_PATH:
  ✓ requirements.md updated
  ✓ spec.md updated
  ✓ tasks.md updated

[Note: All files are verified and auto-updated if needed before moving to next spec]

[If any specs were skipped, list them and reason]

Review the updated specifications and task lists to see the $MODE_DESCRIPTION findings incorporated.
```

## Important Notes

- **Default Path Configuration**: The default specs directory is defined at a single point of truth in the Configuration section. All path references use variables derived from this default or user input.
- **Path Selection**: The command will prompt the user to select the target path (specific spec, directory, or default) after execution. This keeps the implementation simple and clear.
- **Execution Mode Selection**: After determining target specs, the command prompts the user to select the execution mode (Gap based or Feedback based). The selected mode determines which reports directory is used.
- **Multiple Specs Support**: The command processes all available specs in the directory sequentially, one-by-one, completing all 3 phases for each spec before moving to the next.
- **Path Variables**: All paths use variables (`$SPECS_DIR`, `$SPEC_PATH`, `$REPORTS_DIR`, `$REPORTS_DIR_NAME`) - no hardcoded paths except the default configuration.
- **Mode Variables**: 
  - `$UPDATE_MODE`: Set to "gap" or "feedback" based on user selection
  - `$REPORTS_DIR_NAME`: Set to "gap_reports" or "feedback_reports" based on selected mode
  - `$MODE_DESCRIPTION`: Set to "gap analysis" or "human feedback" for user-facing messages
- All agents preserve existing content - only add/update relevant sections
- **Minimal Changes Only**: Always make minimal changes to existing content. Only make the required changes - add new requirements. Do NOT make formatting differences, restructuring, or unnecessary modifications. Simply follow the existing structure and add new content.
- Required files must exist for each spec before processing:
  - `$SPEC_PATH/spec.md` (required)
  - `$SPEC_PATH/tasks.md` (required)
  - `$SPEC_PATH/planning/requirements.md` (required)
  - At least 1 report (any `.md` file) in the selected mode's reports directory (required):
    - Gap based mode: `$SPEC_PATH/gap_reports/` directory
    - Feedback based mode: `$SPEC_PATH/feedback_reports/` directory
- Reports location: Uses variable `$SPEC_PATH/$REPORTS_DIR_NAME/` (not hardcoded)
- **No extra artifacts**: do not generate any new reports/summaries/final documents or scripts; only update `requirements.md`, `spec.md`, and `tasks.md`.
- **NO GIT ACTIONS**: Do **NOT** perform any git operations (commit, push, pull, add, etc.). Never run git commands or perform any git-related actions.
