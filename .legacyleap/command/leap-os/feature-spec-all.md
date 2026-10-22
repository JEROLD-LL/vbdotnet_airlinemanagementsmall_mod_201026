---
description: "Draft the specs of all features (or the ones you name) in dependency order, without stopping; approve them afterwards one by one"
agent: feature-spec-batch
---

# `/feature-spec-all [FEATURE_ID ...]`

Drafts `leap-os/specs/features/<ID>/<ID>.md` for every feature that has no spec yet (or whose spec is stale because the MCM changed), in dependency order. Give feature ids to draft only those.

Each draft is written, mechanically checked and reviewed exactly as `/feature-spec` does, but nothing is asked while drafting: what the evidence cannot settle becomes an open question in the spec. Every spec is left as `draft`.

## What happens

1. If features are not identified yet, or some snapshots are not placed, **feature-identifier** does that first (you are asked only about images it cannot place).
2. You confirm the list of features to draft.
3. **feature-spec-writer** drafts each spec in turn: evidence, spec, `check`, one review by **feature-spec-reviewer**.
4. You get a table of drafts with their check results and open questions, and the order to approve them in.

## Then approve

Run `/feature-spec <ID>` for each draft, dependencies first. The writer sees the existing draft, skips rewriting, and takes you straight to its open questions and Approve / Request changes / Stop.
