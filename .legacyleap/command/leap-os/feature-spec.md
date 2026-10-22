---
description: "Write one evidence-backed modernization spec for one feature from the MCM and its UI snapshots, review it once, and get your approval"
agent: feature-spec-writer
---

# `/feature-spec [FEATURE_ID]`

Writes `leap-os/specs/features/<ID>/<ID>.md`: one spec covering workflow, business rules, UI, backend, data, errors and test scenarios. Every claim cites the MCM (`op-…`, `mcm:…`) or a UI snapshot (`snapshot:…`).

Run it once per feature, dependencies first. Without an ID, the agent lists the features with their spec status and suggests the next one. To draft every spec in one go, use `/feature-spec-all`, then run `/feature-spec <ID>` on each draft to approve it.

## What happens

1. The agent reads each feature's spec status (`status`). If features are not identified yet or some snapshots are not placed, **feature-identifier** does that first (`/feature-identify`).
2. The tool collects this feature's evidence from the MCM (`evidence`) and the agent opens the feature's snapshots.
3. The agent writes the spec, fixes mechanical check errors (`check`), and applies one review by **feature-spec-reviewer**. An existing draft is not rewritten: the agent goes straight to step 4.
4. You answer open questions and approve. The spec's Approval table records your name, the date and the MCM version.

## Files

| File | Purpose |
|---|---|
| `scan_assessment_reports/features/features.json` | Feature list (pointers into the MCM, no copied text) |
| `scan_assessment_reports/features/snapshot-map.json` | Which screen each snapshot shows |
| `leap-os/specs/features/<ID>/evidence.json` | This feature's evidence, pulled from the MCM |
| `leap-os/specs/features/<ID>/<ID>.md` | **The spec** |
