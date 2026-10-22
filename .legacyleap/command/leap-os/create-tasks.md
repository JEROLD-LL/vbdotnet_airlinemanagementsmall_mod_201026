# Task List Creation Process

You are creating a tasks breakdown from a given spec and requirements for a new feature.

## PRE-FLIGHT: Load DB Schema, Backend Rules, and Legacy API Contract

Before creating any tasks, load optional context files that anchor the task list to the project's authoritative database schema, coding rules, and **allowed API surface**.

1. Read `.legacyleap/metadata.json` and extract (use **actual** values from the file — do not assume a stack):
   - `legacyleap_plugin` — plugin folder
   - `migration_config` — config subfolder
   - `is_schema_file_provided` (boolean)
   - `is_backend_rule_provided` (boolean)
   - `is_api_contract_provided` (boolean)

2. If `is_schema_file_provided` is `true`: read `{legacyleap_plugin}/configs/{migration_config}/schema.sql` and store as **DB Schema Context**.
3. If `is_backend_rule_provided` is `true`: read `{legacyleap_plugin}/configs/{migration_config}/backend_rules.txt` and store as **Backend Rules Context**.
4. If `is_api_contract_provided` is `true`: read `{legacyleap_plugin}/configs/{migration_config}/legacy_api_contract.json` and store as **API Contract Context**.

If any flag is `false` or the file does not exist, skip that item silently.

**API precedence (when contract loaded):** contract > legacy evidence > rules/schema/target_tech > spec/FSD. Endpoints in spec/FSD that are **not** in the contract must go in **tasks.md § B Proposed (HITL, default skip)** — do not generate controller/route implementation tasks for them unless the user explicitly approves in chat.

**Modern vs legacy routes (when contract loaded):** The contract lists **which APIs may exist** (`id` only for gating). **`path` = modern route** to implement; **`legacyPath`** (or a legacy-only value in `path` per backward-compat — see `profiles/default/docs/legacy-api-contract.md`) is evidence only. **Never** implement legacy URL shapes in modern controllers (`[Route]`, `MapGet`, etc.). Derive modern paths from existing modernized controllers, `target_tech.json` `backend_api_style`, and `backend_rules.txt` when the file only contains legacy URLs in `path`.

Pass all loaded context to the **tasks-list-creator** subagent in PHASE 2.

## PHASE 1: Get and read the spec.md and/or requirements document(s)

You will need ONE OR BOTH of these files to inform your tasks breakdown:
- `leap-os/specs/[this-spec]/spec.md`
- `leap-os/specs/[this-spec]/planning/requirements.md`

IF you don't have ONE OR BOTH of those files in your current conversation context, then ask user to provide direction on where to you can find them by outputting the following request then wait for user's response:

```
I'll need a spec.md or requirements.md (or both) in order to build a tasks list.

Please direct me to where I can find those.  If you haven't created them yet, you can run /shape-spec or /write-spec.
```

## PHASE 2: Create tasks.md

Once you have `spec.md` AND/OR `requirements.md`, use the **tasks-list-creator** subagent to break down the spec and requirements into an actionable tasks list with strategic grouping and ordering.

Provide the tasks-list-creator:
- `leap-os/specs/[this-spec]/spec.md` (if present)
- `leap-os/specs/[this-spec]/planning/requirements.md` (if present)
- `leap-os/specs/[this-spec]/planning/visuals/` and its' contents (if present)
- **DB Schema Context** (if loaded in PRE-FLIGHT): instruct the subagent that this is the authoritative database schema — (a) do not generate migration tasks for tables already in it, (b) only include scaffold entities whose source table exists in the schema, (c) do not create new stored procedures if an existing SP already covers the same operation
- **Backend Rules Context** (if loaded in PRE-FLIGHT): instruct the subagent that these rules are hard constraints that override any conflicting value in the spec, including target framework/runtime version, package versions, and architectural patterns
- **API Contract Context** (if loaded in PRE-FLIGHT): instruct the subagent that only endpoints whose `id` appears in `legacy_api_contract.json` may have API/controller implementation tasks in section **A**; match by **`id` only**, not legacy path strings; § A must use **Modern route** / **Legacy route** columns; implement **Modern route** only; spec/FSD-only routes go in **§ B Proposed (HITL)** with default skip; require **## API scope** (A/B/C) at the top of `tasks.md` when the feature has backend/API work

The tasks-list-creator will create `tasks.md` inside the spec folder.

## PHASE 3: Inform user

Once the tasks-list-creator has created `tasks.md` output the following to inform the user:

```
Your tasks list ready!

✅ Tasks list created: `leap-os/specs/[this-spec]/tasks.md`

NEXT STEP 👉 Run `/implement-tasks` (simple, effective) or `/orchestrate-tasks` (advanced, powerful) to start building!
```
