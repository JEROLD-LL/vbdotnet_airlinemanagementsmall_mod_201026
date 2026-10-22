# Spec Implementation Process

Now that we have a spec and tasks list ready for implementation, we will proceed with implementation of this spec by following this multi-phase process:

PHASE 1: Determine which task group(s) from tasks.md should be implemented
PHASE 2: Delegate implementation to the implementer subagent
PHASE 3: After ALL task groups have been implemented, delegate to implementation-verifier to produce the final verification report.

Follow each of these phases and their individual workflows IN SEQUENCE:

## Multi-Phase Process

### PHASE 1: Determine which task group(s) to implement

First, check if the user has already provided instructions about which task group(s) to implement.

**If the user HAS provided instructions:** Proceed to PHASE 2 to delegate implementation of those specified task group(s) to the **implementer** subagent.

**If the user has NOT provided instructions:**

Read `leap-os/specs/[this-spec]/tasks.md` to review the available task groups, then output the following message to the user and WAIT for their response:

```
Should we proceed with implementation of all task groups in tasks.md?

If not, then please specify which task(s) to implement.
```

### PHASE 2: Delegate implementation to the implementer subagent

Before delegating, read `.legacyleap/metadata.json` to check `is_schema_file_provided`, `is_backend_rule_provided`, and `is_api_contract_provided`. Extract **`legacyleap_plugin`** and **`migration_config`** from that file (project-specific values — do not assume a particular plugin or config name) so you can construct the paths below.

Delegate to the **implementer** subagent to implement the specified task group(s):

Provide to the subagent:
- The specific task group(s) from `leap-os/specs/[this-spec]/tasks.md` including the parent task, all sub-tasks, and any sub-bullet points
- The path to this spec's documentation: `leap-os/specs/[this-spec]/spec.md`
- The path to this spec's requirements: `leap-os/specs/[this-spec]/planning/requirements.md`
- The path to this spec's visuals (if any): `leap-os/specs/[this-spec]/planning/visuals`
- If `is_schema_file_provided` is `true`: the DB schema at `{legacyleap_plugin}/configs/{migration_config}/schema.sql` — instruct the subagent to treat this as the authoritative database definition and never create tables or columns that conflict with it
- If `is_backend_rule_provided` is `true`: the backend rules at `{legacyleap_plugin}/configs/{migration_config}/backend_rules.txt` — instruct the subagent to follow these rules strictly when implementing backend code
- If `is_api_contract_provided` is `true`: the legacy API contract at `{legacyleap_plugin}/configs/{migration_config}/legacy_api_contract.json` — instruct the subagent to implement **only** `id`s in `tasks.md` **§ A. In contract** or **§ B. Proposed** rows with **Approved** checked; use **Modern route** from § A for `[Route]`, `MapGet`, and route templates — **never** Legacy route or legacy_code URL shapes; **do not** add controllers/actions for `id`s not in the contract unless approved in **B** or chat
- The path to `leap-os/specs/[this-spec]/tasks.md` — the subagent must read **## API scope** before implementing any API/controller task

Instruct the subagent to:
1. Analyze the provided spec.md, requirements.md, and visuals (if any)
2. Analyze patterns in the codebase according to its built-in workflow
3. Implement the assigned task group according to requirements and standards
4. Update `leap-os/specs/[this-spec]/tasks.md` to mark completed tasks with `- [x]`

### PHASE 3: Produce the final verification report

IF ALL task groups in tasks.md are marked complete with `- [x]`, then proceed with this step.  Otherwise, return to PHASE 1.

Assuming all tasks are marked complete, then delegate to the **implementation-verifier** subagent to do its implementation verification and produce its final verification report.

Provide to the subagent the following:
- The path to this spec: `leap-os/specs/[this-spec]`
Instruct the subagent to do the following:
  1. Run all of its final verifications according to its built-in workflow
  2. Produce the final verification report in `leap-os/specs/[this-spec]/verifications/final-verification.md`.
