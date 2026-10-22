---
description: Extract verified application-domain details into local JSON, then extend the meta-model in Neo4j and domain-record vectors
agent: extract-application-domain
---

Extract verified details for every enabled application domain using only
read-only `source-code-fabric` MCP access for discovery. Verify every record
against source-backed Parts. Batch subagents write files under
`.legacyleap/extraction/output/<project_id>/<domain>/batches/`.

After each domain's batches exist, call `scan_consolidate` then `scan_extend`
with `project_id` and that domain key. Do not read batches or write `items.json`.

Arguments must be labeled. Pass exactly one of:

- `project_id=<id>`
- `application_id=<id>`

An unlabeled bare id is rejected. Show both labeled forms in the error.

An optional entity or component filter may follow the labeled id.

When `application_id=` is given, the agent lists the application's projects,
selects the first incomplete one, and extracts that project only. Re-run the
same command to continue until the application reports complete.

$ARGUMENTS

Always process enabled domains in registry order. If an earlier invocation
stopped, skip its consecutively completed domains and restart the first
incomplete domain from its beginning. Do not retry automatically within the
same invocation.

Do not generate documents. Do not call embedding or Qdrant MCP yourself.
