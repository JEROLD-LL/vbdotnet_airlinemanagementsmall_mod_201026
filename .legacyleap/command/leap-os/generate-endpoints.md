---
description: "Run generate_api_contracts.py, then merge fragments into modernize/endpoints-open-api.json on the fly (mechanical bundle; no fragment edits)"
---

# `/generate-endpoints`

Workflow: **(1)** run the blocking generator so fragments exist under **`modernize/target/endpoints/`**; **(2)** mechanically merge those fragments **on the fly** into **`modernize/endpoints-open-api.json`**. Treat fragments as **read-only** inputs—never edit or add files under the input folder; only write the single bundled output file (create parents if missing).

---

## Paths (fixed unless the user overrides in this conversation)

| Role | Path |
|------|------|
| Generator script | After `project-install`: `.legacyleap/tool/leap-os/generate_api_contracts.py`; in-repo profile: `profiles/default/tools/generate_api_contracts.py` |
| **Input** | `modernize/target/endpoints/` — non-recursive `*.json` only |
| **Output** | `modernize/endpoints-open-api.json` |

---

## Phase 1 — Generate fragments

From the **project root** (directory that contains `modernize/`):

```bash
python3 .legacyleap/tool/leap-os/generate_api_contracts.py .
```

(or the equivalent absolute path into `profiles/default/tools/` when invoking from **`leap-os`** against another project.)

Parse **`stdout`** as JSON: **`ok`** and fragment paths / exit code must indicate success before merging. Do not merge if generation failed. If fragments already exist and the user skips generation, state that assumption explicitly.

---

## Phase 2 — Merge on the fly (no auxiliary merge script)

You are acting as an experienced REST / OpenAPI engineer. Your **only job** is to assemble many per-endpoint JSON OpenAPI fragments into **one** valid OpenAPI document at **`modernize/endpoints-open-api.json`**—without “improving” content, refactoring names, or changing business meaning. **Structural merge only.**

### Discovery

1. List every `*.json` file **directly** under `modernize/target/endpoints/` (no subdirectories unless the user says otherwise).

### Merge rules (apply in order; if a rule blocks without user instruction, stop and report)

1. **`openapi`** — Every fragment MUST declare the **same** `openapi` string (full version). If any differ: **report mismatch and stop** (do not invent a compromise).
2. **`info`** — Prefer a single **`info`** block:
   - If all fragment `info` objects are identical, reuse once.
   - Otherwise use the **`info` from the first lexicographically sorted input filename** as the baseline.
   - For each other fragment’s `info`, add **only missing keys**, copying values **verbatim**. If another fragment tries to introduce a conflicting value for a key already on the baseline, **stop and report**.
3. **`paths`** — Deep-merge by **path template** and **HTTP method**.
   - Each `(path_template, http_method)` should appear once in the merged **`paths`**.
   - Duplicate `(path, method)` where the **operation bodies are not identical** (JSON-equal): **do not drop** the endpoint—assign the conflicting operation under a **renamed path template**: `original___2`, `original___3`, … (increment until the slot is unique and no collisions remain). Rename **only** the path key; preserve the operation payload as emitted in the fragment.
   - Duplicate `(path, method)` with **identical** bodies: collapse to one logical entry while merging path-item fields compatibly as below.
   - **`parameters`**, **`servers`**, summary/description at path/item level: merge structurally—if the same `(name, in)` differs between sources, **stop and report**.
4. **`components`** — Merge map sections (`schemas`, `parameters`, `requestBodies`, `responses`, `headers`, `securitySchemes`, …) **by key**:
   - Same key **and** identical definition → include once.
   - Same key **but** differing definitions → **stop and report** (no renaming to force compatibility).
5. **`tags`, `servers`, `security`** — Union arrays. Remove **exact** duplicate entries after JSON-normalized comparison only. Never rewrite strings to unify “similar” values. Where duplicate tag **`name`** has inconsistent other fields and you cannot union without rewriting, either keep both verbatim or **report**—do not silently pick a winner unless the user resolves it in-chat.
6. **Ordering** — Process input files in **lexicographically sorted** order by path. Preserve **first-seen** order for paths and methods as you ingest that list (unless the user asks for alphabetical paths).
7. **Other top-level keys** — Carry over only where every fragment agrees or merging is additive; conflicting unknown top-level keys → **report and stop**.

### Hard boundaries

- **Do** read fragments only from `modernize/target/endpoints/` for this merge (plus any path the user adds in-chat).
- **Do** write **exactly one** output: `modernize/endpoints-open-api.json`.
- Invalid JSON / invalid root in a fragment: **cite the file and stop** (default: no silent fixes).
- **Do not** modify or create files under `modernize/target/endpoints/`.

### Lightweight self-check before you finish

- Output exists and is valid JSON.
- Exactly one **`openapi`** version; **`paths`** and **`components`** (if any) parse structurally under OpenAPI 3.x expectations.
- Count merged **`(path, method)`** operations and compare to declarations across fragments (identical repeats collapse; conflicting duplicates yield extra **`___n`** path keys)—briefly explain your count.

---

## Reply to the user (short, concrete)

1. Which fragment files were merged (or skipped, with reason).
2. Confirm output path **`modernize/endpoints-open-api.json`**.
3. Conflicts resolved (especially **path template** disambiguations: `original` → `original___2`), and any assumptions.

If anything in this command conflicts with a **specific** instruction the user gave in the **same conversation**, follow the user’s instruction for that point only—still keep **merge-only** discipline.

Note:
Do not pass the timeout to bash tool use the default timeout.
