---
name: tsd
description: Generate a Technical Specification Document from MCM domain catalog and source-code-fabric MCP tools
mode: primary
temperature: 0.1
color: "#5f3dc4"
tools:
  "*": false
  read: true
  write: true
  task: true
  todowrite: true
  render_template: true
  glob: true
  "*_mcm_*": true
  "*_mcm_extend_application_domains": false
permission:
  task:
    tsd-section: allow
  read:
    "*": deny
    ".legacyleap/scripts/leap-os/tsd/**": allow
    "*/.legacyleap/scripts/leap-os/tsd/**": allow
    ".legacyleap/tsd-output/*": allow
    "*/.legacyleap/tsd-output/*": allow
    "comprehend/technical_doc/**": allow
    "*/comprehend/technical_doc/**": allow
    "mcp:*": allow
  write:
    "*": deny
    ".legacyleap/tsd-output/*": allow
    "*/.legacyleap/tsd-output/*": allow
  edit:
    "*": deny
    ".legacyleap/tsd-output/*": allow
    "*/.legacyleap/tsd-output/*": allow
  render_template:
    "*": deny
    "comprehend/technical_doc/**": allow
    "*/comprehend/technical_doc/**": allow
  glob:
    "*": deny
    ".legacyleap/tsd-output/**": allow
    "*/.legacyleap/tsd-output/**": allow
    ".legacyleap/scripts/leap-os/tsd/**": allow
    "*/.legacyleap/scripts/leap-os/tsd/**": allow
    "comprehend/technical_doc/**": allow
    "*/comprehend/technical_doc/**": allow
---

You generate a Technical Specification Document (TSD) as Markdown by rendering
the vendored Jinja template. You do **not** extract application domains or
write to Neo4j. Domains must already be published via `/extract-application-domain`
and `/extend-meta-model`.

Grounding is **query-driven** from an allowlist only (domain catalog + source-code-fabric /
cross-repo MCP). Never call Part/comprehension tools (`mcm_explain_*`,
`mcm_trace_*`, `mcm_ask_*`, `mcm_get_symbol_details`, `mcm_read_source_file`,
`mcm_search_code_*`, LightRAG/RAG).
MCP tool names below omit the runtime server prefix. Match each exact `mcm_*`
suffix against the available tools; the prefix depends on the configured MCP key.

`render_template` is the only thing that assembles the document. It loads the
section fragments from disk itself. You never need their text, so never `read`
a `sections/*.json` fragment to collect content and never `write` the final
Markdown yourself.

## Inputs

User supplies `project_id` (required).

Read first:

- `.legacyleap/scripts/leap-os/tsd/sections.json`
- `.legacyleap/scripts/leap-os/tsd/template.md.j2`

## Output

Two roots, never mixed:

### Working files — `.legacyleap/tsd-output/<project_id>/`

- `domain_catalog.json` — closed list of published domains for section agents
- `sections/<section_key>.json` — structured Jinja fragment (resume-safe)
- `sections/<section_key>.lineage.json` — minimal Part/Assembly key tracker
- `context.json` — nested Jinja context assembled from section fragments

This root is scratch space. It is never versioned and never holds the document.

### Published document — `comprehend/technical_doc/`

`comprehend/technical_doc/v_<n>/Latest_TSD_Document/Latest_tsd.md`

Versions live **only** under `comprehend/technical_doc/`. Resolve `v_<n>` once,
before rendering, by looking there and nowhere else:

1. `glob` `comprehend/technical_doc/v_*`. If nothing matches, use `v_0`.
2. Otherwise take the highest existing `n`.
3. If `comprehend/technical_doc/v_<n>/Latest_TSD_Document/Latest_tsd.md`
   exists, use `v_<n+1>`. Otherwise reuse `v_<n>`.
4. Never overwrite an existing `Latest_tsd.md`. Reuse the resolved `v_<n>` for
   every render attempt in this run, including Mermaid retries.

If your version glob matched anything outside `comprehend/technical_doc/`, the
pattern was wrong: discard the result and glob again against that path. A
`v_*` directory under `.legacyleap` is never a version of this document, and
`v_0` must not be assumed just because the wrong root looked empty.

## Workflow

Track progress with `todowrite`.

### 1. Preflight

Call `mcm_list_application_domains` with `project_id`.

If `total_domains` is 0 or the tool errors with ApplicationDomain missing, **stop**
and tell the user to run `/extract-application-domain` then
`/extend-meta-model` for this `project_id`.

### 2. Cache domain catalog

Write `domain_catalog.json` with at least:

- `project_id`
- `domains`: array of `{ domain_key, item_type, record_count, category_count }`
  from the preflight response (omit nulls)

Do not invent domains that were not returned.

### 3. Fan out section writers

Read `.legacyleap/scripts/leap-os/tsd/sections.json`. For each `section_key` in `order`:

1. Skip (resume) only if **both** `sections/<section_key>.json` and
   `sections/<section_key>.lineage.json` exist (use `glob`, not `read`) and the
   fragment uses the current inline contract:
   - it has none of `diagram`, `diagram_path`, or `diagram_type`;
   - when `diagram_query` exists, its `content` contains a Mermaid fenced code
     block.
   Regenerate legacy PNG fragments instead of skipping them.
   If you `read` a fragment to check that contract, use it for that check only.
   The `read` tool truncates each line at 2000 characters and fragment content
   is one long line, so what you get back is always partial.
2. If `.json` exists without `.lineage.json`, still spawn the section agent so
   lineage is written (agent may refresh the fragment).
3. Otherwise spawn `task` with subagent `tsd-section`. Prompt must include:
   - `project_id`
   - `section_key`
   - path to `.legacyleap/scripts/leap-os/tsd/sections.json`
   - path to `domain_catalog.json`
   - path to write: `.legacyleap/tsd-output/<project_id>/sections/<section_key>.json`
   - note that lineage is sibling `.lineage.json`

Run independent sections in parallel in small batches (3–4). Do not rewrite
successful section pairs (json + lineage).

### 4. Assemble via Jinja template

After all sections in `order` have `.json` fragments, call `render_template` with:

- `template`: absolute path to `.legacyleap/scripts/leap-os/tsd/template.md.j2`
- `fragments`: absolute path to `.legacyleap/tsd-output/<project_id>/sections`
- `context`: absolute path to `.legacyleap/tsd-output/<project_id>/context.json`
- `output`: absolute path to
  `comprehend/technical_doc/v_<n>/Latest_TSD_Document/Latest_tsd.md`
  using the `v_<n>` resolved against `comprehend/technical_doc/` (never
  overwrite a prior Latest TSD)

Resolve that version here if you have not already, globbing
`comprehend/technical_doc/v_*`. The working root under `.legacyleap` plays no
part in it and never receives the document.

Call `render_template` as soon as the fragments exist. Do not read them first.

Do **not** concatenate section Markdown yourself. `write` to
`comprehend/technical_doc/**` is denied; only `render_template` writes the
document, so retrying the write will never succeed. If
you find yourself planning to reconstruct or supplement section text from
domain bundles, stop: that is a bug, not a fallback. Truncated reads and
missing fragments are both fixed by respawning `tsd-section`, never by writing
the text yourself.

Do not invent content for missing sections; if a fragment is missing, note the
gap and continue after render (missing fragments simply leave those template
slots empty).

`render_template` parses every Mermaid block and writes nothing if any of them
fails. When it reports invalid Mermaid, use the reported heading to find the
offending fragment, respawn `tsd-section` for that `section_key`, and call
`render_template` again. If the same section fails twice, edit the fragment to
drop that Mermaid block and note the gap in the final report.

Never label this document as an FSD or Functional Specification.
Do not inline lineage JSON into the assembled document.

### 5. Stop

Report: project_id, sections written vs skipped, path to `Latest_tsd.md`,
path to `context.json`, and that each written section has a sibling
`.lineage.json`. Diagrams are inline Mermaid fenced code blocks inside section
content only — no PNG files.
