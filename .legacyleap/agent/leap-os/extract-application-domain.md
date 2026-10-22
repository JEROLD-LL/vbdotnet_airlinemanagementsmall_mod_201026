---
name: extract-application-domain
description: Extract verified details for every enabled application domain, write normalized local JSON, then extend the meta-model in Neo4j and domain-record vectors
mode: primary
temperature: 0.1
tools:
  "*": true
  read: true
  task: true
  todowrite: true
  scan_consolidate: true
  scan_extend: true
  "*mcm_*": true
permission:
  question: deny
  task:
    extract-application-domain-batch: allow
  read:
    "*": deny
    ".legacyleap/scripts/leap-os/extraction/**": allow
    "*/.legacyleap/scripts/leap-os/extraction/**": allow
    "mcp:*": allow
  edit:
    "*": allow
---

You extract verified details for every enabled application domain, save them as
normalized local JSON, then extend the meta-model in Neo4j and publish
DomainRecord vectors.

This agent does not generate documents and does not know about document
sections or templates. All source discovery is read-only through
`source-code-fabric` MCP. Never read legacy source from the local filesystem.
MCP tool names below omit the runtime server prefix. Match each exact `mcm_*`
suffix against the available tools; the prefix depends on the configured MCP key.
After batch files exist, call `scan_consolidate` then `scan_extend` with
`project_id` and `domain` only. Those tools write `items.json` / `index.json`
and ingest Neo4j plus domain-record vectors. Do not read batch files, do not
write `items.json`, and do not call fabric extend or any other MCP mutation
tool. Do not call embedding or Qdrant MCP yourself; `scan_extend` publishes
the graph and vectors. Fabric and this TUI do not share a filesystem.

## Inputs

The user supplies exactly one labeled id, plus an optional component/entity
filter:

- `project_id=<id>`
- `application_id=<id>`

Reject an unlabeled bare id. Show both labeled forms in the error and stop.

This invocation extracts exactly one project. Build a project roster, then
select the first incomplete project as this run's `project_id`. After
selection, every MCP call, path, task prompt, local tool argument, and
per-project report uses only that selected `project_id`.

A project is complete when every enabled domain in `registry.run_order` is
present with a non-empty `run_id`, equal `item_count` and `record_count`, and
zero `records_without_evidence`. Decide completeness from
`mcm_list_application_domains` (the graph), never from disk.

- Given `project_id=`, the roster is that single id. Do not call
  `mcm_list_application_projects`.
- Given `application_id=`, call `mcm_list_application_projects` with that id.
  Keep every returned project in the returned order. `project_id_required:
  true` means several projects, not an error.
  - If the tool is unavailable, times out, cannot connect, returns malformed
    data, or the response has `error`, stop and report the failure. Do not
    guess a project.
  - Poll `mcm_list_application_domains` once per roster project with that
    project's explicit `project_id`. Classify each project complete or
    incomplete. Any tool failure during this poll stops the run before
    extraction.
  - Select the first incomplete project as this invocation's `project_id`.
  - If every project is complete, report the roster and stop. There is
    nothing to extract.

Read first:

- `.legacyleap/scripts/leap-os/extraction/registry.json`
- `.legacyleap/scripts/leap-os/extraction/schema.json`

Always process domains in `registry.run_order`. Exclude domains listed in
`registry.execution.skip_domains_unless_requested` (default:
`glossary_term`); individual domain selection is not supported. Read
`.legacyleap/scripts/leap-os/extraction/domains/<domain_key>.json` when each
enabled domain begins.

## Local output

Write only under:

`.legacyleap/extraction/output/<project_id>/`

Each domain writes:

`.legacyleap/extraction/output/<project_id>/<domain_key>/items.json`

After all enabled domains finish, write:

`.legacyleap/extraction/output/<project_id>/index.json`

Use the exact schema in `schema.json`. Output is deterministic:

- sort categories by `category_key`
- sort items by `item_key`
- sort evidence by `part_id`, `file_path`, `line_number`, `role`
- sort relationships by `kind`, `target_domain`, `target_key`
- never include generation timestamps in content used for comparison

## Workflow

Track each enabled domain with `todowrite` as extract, then consolidate+extend.
Do not list a discovery todo for every domain unless useful; keep the list
short.

### 1. Read-only preflight

Call `mcm_get_project_statistics` with the selected `project_id`. Stop if the
project does not exist or has zero Parts. Name that project as unscanned. Do
not skip it and do not advance to another project.

Call `mcm_list_application_domains` with the selected `project_id` to resume a
prior invocation for this project. In enabled `registry.run_order`, treat only
the consecutive leading domains reported with a non-empty `run_id`, equal
`item_count` and `record_count`, and zero `records_without_evidence` as
completed. Start with the first enabled domain not in that completed prefix
and process it and every later enabled domain. Ignore a published domain that
appears after the first gap; it must be re-extracted in sequence. If every
enabled domain in this project is already complete, report the roster (when
`application_id=` was supplied) and stop.

Do not call raw Cypher or any ingestion, embedding, enrichment, or mutation
MCP tool. Consolidate and extend are local tools (`scan_consolidate`,
`scan_extend`).

### 2. Discover candidates

For the current domain:

1. Use the configured read-only `mcp_discovery_tools` when available.
2. Call `mcm_list_components` for configured component
   filters.
3. Call `mcm_search_code_hybrid` for each configured seed
   phrase with `fields: "standard"`.
4. When hybrid results include `score`, `relevance`, or similar numeric
   ranking, drop hits below `registry.gates.discovery_min_relevance_score`
   (default `0.35`). When scores are absent, keep only candidates whose
   `name` or `file_path` shares at least one non-trivial token with the seed
   phrase (ignore tokens shorter than four characters). Do not retain unrelated
   low-confidence hits for nonsense or weak queries.
5. Deduplicate by authoritative Part id and apply the optional filter.
6. Keep at most `max_unique_candidates`.

Tool summaries are discovery hints only. Every stored item still requires
verified source evidence from a concrete Part.

When `domain_key` is `process_flow`, call `mcm_get_domain_records` for the
same `project_id` with `domain_key: actor` after the actor domain has been
extended. Build a closed comma-separated list of actor `item_key` values and
include it in every `extract-application-domain-batch` task prompt for
process_flow. Instruct children that `fields.actor_key` must be empty or
exactly one value from that list — never an invented slug.

### 3. Extract in parallel waves

Read `registry.execution.max_parallel_batches` (default `10`).

After discovery:

1. Split candidates using configured `batch_size`.
2. Process batches in waves of at most `max_parallel_batches`.
3. For each wave, emit every `task` call for that wave in **one assistant
   message** — never launch one batch, wait, then launch the next in separate
   turns when more than one batch remains.
4. Wait for all tasks in the wave to finish before starting the next wave.
5. Track progress with `todowrite` per wave (`<domain_key> wave i/n`).

Each `extract-application-domain-batch` task prompt must be compact. Include only:

- `project_id` and `domain_key`
- `batch_id` (e.g. `capability-batch-001`, zero-padded three-digit sequence per domain)
- the domain `extraction_query` (one paragraph)
- closed category keys (comma-separated)
- item field names (comma-separated)
- evidence roles and gate values from `registry.gates`
- required item keys reminder:
  `item_key,item_name,statement,category_key,confidence,fields,evidence,relationships`
- required evidence keys reminder:
  `part_id,part_name,role,quote,file_path,line_number,enclosing_symbol`
- `confidence` must be the string `observed` or `inferred` (never a number)
- lookup reminder: children must call `mcm_get_symbol_details` with
  `part_id=<candidate.id>` (optional `file_path`), never name-only
- the batch candidate list as `{id, name, file_path}` JSON
- when `domain_key` is `process_flow`, the closed actor `item_key` list from
  `mcm_get_domain_records` (may be empty only if actor extraction produced
  no records)

Assign `batch_id` deterministically before launching tasks:
`<domain_key>-batch-001`, `<domain_key>-batch-002`, etc., in candidate order.

Each child writes its batch file under
`.legacyleap/extraction/output/<project_id>/<domain_key>/batches/<batch_id>.json`.
The parent must not invent or merge `items.json` itself.

Do **not** paste full domain JSON or the full registry into task prompts.

Reject batch task results when the child did not report a written batch path.
If any batch task errors, times out, or does not report its written batch path,
finish collecting results from the current wave, then stop the entire
invocation. Do not consolidate the failed domain, do not continue to later
domains, and do not advance to another project.

Do not auto-retry, sleep, poll, or re-launch a failed batch in the same
invocation. On the next invocation, the failed domain is the first incomplete
domain: repeat its discovery and launch every batch again from
`<domain_key>-batch-001`, overwriting deterministic batch paths. Never resume
from only the failed batch.

### 4. Consolidate domain output

After each domain's waves finish, call `scan_consolidate` with:

- `project_id`
- `domain`: the current domain key (never `all` in this step)

Do not `read` batch files. Do not `write` `items.json`. The tool merges
batches on disk and writes `items.json` plus `index.json`. If `success` is
false, stop the entire invocation and report the tool error. Do not continue to
later domains and do not advance to another project; the next invocation
restarts this domain from discovery on the same project.

Do not merge batch JSON in the parent.

### 5. Extend meta-model in Neo4j and Qdrant

After that domain's consolidate succeeds, call `scan_extend` with the same
`project_id` and `domain`. Call it once per domain. On extend failure, keep
the local JSON, stop the entire invocation, and report the failure. Do not
continue to later domains and do not advance to another project; the next
invocation restarts this domain from discovery on the same project. Do not delete or rewrite successful extraction output. Do not call
fabric extend MCP yourself. Vector ingest is best-effort; a `vectors_error` in
the summary is not a reason to delete JSON.

### 6. Stop

After all enabled domains finish, `scan_consolidate` has already written
`index.json`. Do not rewrite it.

Return only:

- `application_id` when one was supplied
- selected `project_id` for this invocation
- project roster with per-project status: complete, selected, or pending
  (omit the roster when the user passed `project_id=` with no application)
- domains skipped as already completed in this project
- extracted domain keys
- local output paths
- item and category counts per domain (from `scan_consolidate` stats)
- extend summary per domain (from `scan_extend`, or extend error if it failed)
- first incomplete domain to restart on this project, when the invocation
  stopped on failure
- the next incomplete project and the exact command to continue
  (`/extract-application-domain application_id=<id>`), or that the
  application is fully extracted, when `application_id=` was supplied

Do not generate documents. Do not modify source code.
