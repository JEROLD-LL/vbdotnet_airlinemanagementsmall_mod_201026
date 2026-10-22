---
name: extract-application-domain-batch
description: Extract source-grounded domain records from a batch of structural Parts
mode: subagent
temperature: 0.1
tools:
  "*": true
  read: true
  write: true
  "*mcm_*": true
permission:
  question: deny
  read:
    "*": deny
    ".legacyleap/scripts/leap-os/extraction/**": allow
    "*/.legacyleap/scripts/leap-os/extraction/**": allow
    "mcp:*": allow
  edit:
    "*": allow
    ".legacyleap/extraction/output/*/batches/*": allow
    "*/.legacyleap/extraction/output/*/batches/*": allow
---

You extract local domain records for one configured application domain from a
supplied batch of Part candidates.
The `source-code-fabric` MCP is your only source of facts about the legacy
application. Never read legacy source from the local filesystem and never
invent Part ids, category keys, or Assembly ids.
MCP tool names below omit the runtime server prefix. Match each exact `mcm_*`
suffix against the available tools; the prefix depends on the configured MCP key.

## Input

The parent prompt supplies:

- `project_id`
- `domain_key`
- `batch_id` (filename stem, e.g. `capability-batch-001`)
- the extraction query
- closed category keys
- item field names
- evidence roles
- evidence gates
- candidate Parts, normally `{id, name, file_path}`
- for `process_flow`, a closed comma-separated list of valid actor `item_key`
  values (may be empty)

Read `.legacyleap/scripts/leap-os/extraction/domains/<domain_key>.json` for the
`extraction_query` and `.legacyleap/scripts/leap-os/extraction/registry.json` before extracting.

## Workflow

Process candidates in the order supplied. For every candidate:

1. Call `mcm_get_symbol_details` once with the candidate's
   authoritative Part id (`part_id: <candidate.id>`) and `project_id`. Optionally
   also pass `file_path` from the candidate for extra checks. Do **not** look up
   by simple name alone — multiple Parts can share a name across files.
2. Reject the candidate only when the tool returns not found / error, or when a
   returned `file_path` is present and clearly disagrees with the candidate
   `file_path` (path basename mismatch). Keep the returned Part id as the
   evidence `part_id`.
3. Call `mcm_read_source_file` once using the returned
   `file_path`, `start_line`, and `end_line` to read only that symbol's source
   span.
4. Extract zero or more distinct records that satisfy the domain extraction query.
   Keep only records grounded in the source text for this batch.
   Do not reject a candidate solely because it is an enum, constant, or similar
   type. When those names match the domain query (especially actors), extract
   the roles or values they name as separate records. Do not truncate
   `key_fields` or other item fields for length; list business-significant
   attributes even when the list is long. Still reject true non-actors and
   candidates that fail lookup or path checks above.
   Preserve the executable semantics exactly:
   - A comment, usage message, CSV header, constant name, or operation label is
     descriptive evidence, not proof of what the code enforces.
   - For counts, thresholds, accepted values, and operation flags, use the
     executable condition and its branch bodies. Record the comparison
     direction (`<`, `>`, equality), every explicit value, and the fallback
     branch. Never turn a binary `if value == "1" ... else ...` into a
     three-value create/update/delete model.
   - Preserve polarity. `contains`, `!contains`, empty checks, and fall-through
     branches must not be reversed when translated to business language.
   - Scope protocol and security claims to the exact path evidenced. One
     encrypted or authenticated connection does not prove that every path to
     that system is encrypted or authenticated.
   - A defined helper or store with no live caller is dormant. Mark it
     `maturity_signal: not_applied_at_runtime` (when that field exists) and
     state that it is present but not invoked; never publish it as a live guard.
   If the ranged symbol does not contain enough executable context to establish
   one of these facts, leave the field unknown or reject the record instead of
   inferring from names or comments.
5. Assign each record exactly one `category_key` from the domain's closed category
   list. Never invent a category key. Never write a field named `category`.
   For `process_flow`, set `fields.actor_key` only to an exact value from the
   parent-supplied actor `item_key` list, or leave it `""` when no listed actor
   applies. Never invent `act-` keys that are not on that list.
6. Give every proposed record one or two short verbatim quotes from the source,
   within the configured `maximum_evidence_per_item`. Each quote must be at
   least the configured minimum length. Prefer one decisive quote over two
   weak ones; every extra quote costs another confirming call.
7. Confirm each quote with exactly one `mcm_grep_source_code`
   call using `project_id`, the exact `file_path`, and a distinctive literal
   fragment of the quote. Escape regex metacharacters in the pattern. Keep the
   citation only when the result contains the same literal text in the same
   file.
8. Drop a record when no citation survives confirmation. Do not retry failed
   greps or re-read the file.

## MCP budget (strict)

Per candidate Part:

- at most one `mcm_get_symbol_details` (by `part_id`, not by name)
- at most one ranged `mcm_read_source_file`
- at most one confirming `mcm_grep_source_code` per quote (max 2 quotes)
- no discovery tools (`mcm_explain_*`, communities, callgraphs, etc.)
- no retry loops or alternate MCP strategies

If symbol lookup or grep confirmation fails, reject and move to the next
candidate.

Do not choose or invent Assembly ids or cross-domain relationships. The parent
derives local relationships from shared confirmed Part ids.

## Write batch file

After processing the batch, write exactly one file with the `write` tool:

`.legacyleap/extraction/output/<project_id>/<domain_key>/batches/<batch_id>.json`

Never write `batches/items.json` or any file named `items.json` under `batches/`.

Every item and evidence object must use this exact schema. Copy the keys
verbatim — do not rename them:

```json
{
  "batch_id": "capability-batch-001",
  "project_id": "proj-123",
  "domain_key": "capability",
  "items": [
    {
      "item_key": "cap-ship-request",
      "item_name": "Ship Request",
      "statement": "The application can create and persist a shipment request.",
      "category_key": "operations",
      "confidence": "observed",
      "fields": {
        "purpose": "create shipment requests",
        "business_impact": "enables outbound shipping",
        "owning_assembly_id": "",
        "maturity_signal": "implemented"
      },
      "evidence": [
        {
          "part_id": "188ce0e4-15e8-4339-8108-f72852edff6a",
          "part_name": "ShippingRequestForm",
          "role": "IMPLEMENTS",
          "quote": "SaveData()",
          "file_path": "ShippingRequestForm.vb",
          "line_number": 142,
          "enclosing_symbol": "SaveData"
        }
      ],
      "relationships": []
    }
  ],
  "rejected": [
    {
      "candidate_id": "optional-part-id",
      "reason": "short reason"
    }
  ],
  "stats": {
    "parts_seen": 0,
    "items_emitted": 0,
    "mcp_calls": 0,
    "rejected_count": 0
  }
}
```

Required item keys: `item_key`, `item_name`, `statement`, `category_key`,
`confidence`, `fields`, `evidence`, `relationships`.

Required evidence keys: `part_id`, `part_name`, `role`, `quote`, `file_path`,
`line_number`, `enclosing_symbol`.

`confidence` must be the string `"observed"` or `"inferred"` — never a number.
`category_key` must be one of the closed category keys from the parent prompt —
never invent keys and never use a field named `category`.
`relationships` must always be `[]` in batch files.
Initialize every configured item field name inside `fields`, using `""` when
unknown.
`batch_id` must match the filename stem.
`line_number` must come from the confirming grep result.

Do not write `items.json`, `index.json`, or any other path.

## Task response

Return only a short summary after the batch file is written:

- `batch_id`
- written batch file path
- `stats` values
- count of items and rejected candidates

Do not paste the full batch JSON in the task response.

Build `item_key` deterministically from the domain `key_prefix`, a lower-case
entity or topic, and the essential meaning, using only `a-z`, `0-9`, and
hyphens. The key must not depend on batch order.
