---
description: "Version-safe FSD refinement loop that evaluates and improves an FSD iteratively until the evaluation score reaches at least 9.5/10, inlining the full /fsd-evaluate and /doc-quality-improve pipelines"
agent: fsd-refinement-orchestrator
---

# FSD Refinement Command

This command coordinates a safe, repeatable Functional Specification Documentation refinement loop. It evaluates the latest existing FSD first, then creates versioned copies only when refinement is required.

This command is **self-contained**. It calls the individual subagents from the `/fsd-evaluate` and `/doc-quality-improve` pipelines directly, without delegating to their orchestrators. The existing `/fsd-evaluate` and `/doc-quality-improve` commands and their agents are not modified.

## Pipeline Overview

```
Phase 0: Resolve Paths & Initialize State
    ├─ Resolve FSD root and latest v_N
    ├─ Resolve MCM, legacy code, project paths
    ├─ Resolve deterministic evaluation paths
    └─ Initialize .legacyleap/.agent-state/fsd-refine-state.json
    ↓
Phase 1: Baseline FSD Evaluation (inlined /fsd-evaluate pipeline)
    ├─ Initialize fsd-evaluation-state.json
    ├─ Build project digest (project-digest-builder)
    ├─ Run 5 evaluator subagents in parallel
    │   ├─ fsd-coverage-evaluator
    │   ├─ fsd-correctness-evaluator
    │   ├─ fsd-depth-evaluator
    │   ├─ fsd-domain-evaluator
    │   └─ fsd-diagram-evaluator
    ├─ Compute readability score
    ├─ Compute weighted overall score
    ├─ Run fsd-improvement-recommender
    ├─ Run fsd-evaluation-quality-checker
    ├─ Run fsd-evaluation-reporter
    ├─ Normalize report to orchestrator-owned path
    └─ Parse score and reject stale reports
    ↓
Phase 2: Decision Gate
    ├─ If baseline score >= 9.5/10: stop CLIENT_READY
    └─ If score < 9.5/10: create v_N+1 copy
    ↓
Phase 3: Create Refinement Copy
    └─ fsd-refine-utils.sh create-next
    ↓
Phase 4: Document Quality Improvement (inlined /doc-quality-improve pipeline)
    ├─ Initialize doc-quality-state.json for the copied version
    ├─ Step 1: Correctness analysis (doc-correctness-analyzer)
    ├─ Step 2: Structure optimization (doc-structure-optimizer)
    ├─ Step 3: Diagram rendering (doc-diagram-renderer)
    ├─ Step 4: Quality verification (doc-quality-verifier)
    ├─ Step 5: Document splitting if needed (doc-splitter)
    ├─ Step 6: .docx generation via pandoc
    └─ Validate no unexpected v_N folder was created
    ↓
Phase 5: Refined Evaluation (inlined /fsd-evaluate pipeline again)
    ├─ Re-initialize fsd-evaluation-state.json for the refined version
    ├─ Build or reuse project digest
    ├─ Run 5 evaluator subagents in parallel
    ├─ Compute readability + weighted score
    ├─ Run recommender, quality-checker, reporter
    ├─ Normalize report and parse score
    └─ Reject stale reports before parsing score
    ↓
Phase 6: Loop or Finish
    ├─ If score >= 9.5/10: stop CLIENT_READY
    ├─ If max refinement iterations reached: stop BEST_EFFORT
    └─ Otherwise use refined version + report as next source and repeat
```

## Agents Used

| Agent | Role | Pipeline Origin | Called By |
|-------|------|-----------------|-----------|
| `fsd-refinement-orchestrator` | Owns versioning, loop control, deterministic paths, freshness checks, final reporting | `/fsd-refine` | `/fsd-refine` |
| `project-digest-builder` | Distills MCM into compact cached digest | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-coverage-evaluator` | Checks FSD structural coverage against expected sections and MCM inventory | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-correctness-evaluator` | Spot-checks FSD claims against MCM data and optionally legacy code | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-depth-evaluator` | Flags placeholder and vague content | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-domain-evaluator` | Validates FSD-style discipline and terminology | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-diagram-evaluator` | Verifies diagram references and coverage | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-evaluation-quality-checker` | Self-reflection on evaluation scores | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-improvement-recommender` | Synthesizes findings and drafts proposed additions | `/fsd-evaluate` | Phases 1, 5 |
| `fsd-evaluation-reporter` | Produces final evaluation report | `/fsd-evaluate` | Phases 1, 5 |
| `doc-correctness-analyzer` | Verifies document accuracy against source code, MCM, domain | `/doc-quality-improve` | Phase 4 |
| `doc-structure-optimizer` | Reduces to 20-25 pages, fixes issues, client-presentable | `/doc-quality-improve` | Phase 4 |
| `doc-diagram-renderer` | Beautiful professional diagrams via Mermaid service | `/doc-quality-improve` | Phase 4 |
| `doc-quality-verifier` | Scores quality across 5 dimensions | `/doc-quality-improve` | Phase 4 |
| `doc-splitter` | Splits large documents into navigable sub-documents | `/doc-quality-improve` | Phase 4 |

`/fsd-refine` calls these subagents directly. It does **not** delegate to `fsd-evaluation-orchestrator` or `doc-quality-orchestrator`.

## Usage

```bash
/fsd-refine

/fsd-refine --fsd-root comprehend/functional_doc --mcm scan_assessment_reports/meta_cognitive_model.json

/fsd-refine --threshold 9.5 --doc-quality-iterations 1 --doc-quality-threshold 10 --max-refinement-iterations 5 --legacy-code legacy_code
```

## Inputs

| Argument | Description |
|----------|-------------|
| `--fsd-root <path>` | Root containing FSD versions named `v_N`. Defaults to metadata `comprehend/functional_doc` or `comprehend/functional_doc`. |
| `--mcm <path>` | MCM path. Defaults to metadata `scan_assessment_reports/meta_cognitive_model.json` or `scan_assessment_reports/meta_cognitive_model.json`. |
| `--project <path>` | Optional project path passed to evaluator subagents. |
| `--legacy-code <path>` | Optional legacy source path passed to downstream subagents. |
| `--threshold <score>` | Target FSD evaluation score. Default: `9.5`. |
| `--doc-quality-iterations <n>` | Max iterations for the doc-quality improvement cycle within each refinement attempt. Default: `1`. |
| `--doc-quality-threshold <score>` | Quality threshold passed to `doc-quality-verifier`. Default: `10` (forces full iteration budget). |
| `--max-refinement-iterations <n>` | Max copied-version refinement attempts. Default: `5`. |

## Required Invariants

- Evaluate the latest existing FSD version before creating any refinement copy.
- Never modify an existing source FSD version in place.
- Every refinement attempt operates on a newly copied `v_N` folder.
- Version creation belongs only to `fsd-refinement-orchestrator`.
- `doc-structure-optimizer` and other doc-quality subagents must improve the provided copied folder in place only.
- Evaluation reports must be stored in deterministic paths controlled by `/fsd-refine`.
- Stale evaluation reports must be rejected before score parsing.
- Preserve all previous FSD versions and evaluation reports.

## Deterministic Helper

Use:

```bash
.legacyleap/scripts/leap-os/fsd-refine/fsd-refine-utils.sh
```

When testing from this profile repository before deployment, use:

```bash
profiles/default/scripts/fsd-refine/fsd-refine-utils.sh
```

The helper owns deterministic shell-only behavior:

| Helper command | Purpose |
|----------------|---------|
| `latest` | Resolve latest FSD version and deterministic baseline evaluation paths. |
| `create-next` | Copy a source FSD version into the next `v_N` folder. |
| `normalize-report` | Normalize evaluator output to the orchestrator-owned report path. |
| `assert-fresh-evaluation` | Fail if report/state are missing, empty, stale, or missing `overall_score`. |
| `assert-updated-file` | Verify expected FSD output exists and is not empty. |
| `parse-score` | Parse score from fresh state/report. |
| `score-ok` | Return success when score meets threshold. |

## State Files

| State File | Owner | Purpose |
|------------|-------|---------|
| `.legacyleap/.agent-state/fsd-refine-state.json` | `fsd-refinement-orchestrator` | Outer loop state: versioning, iterations, scores |
| `.legacyleap/.agent-state/fsd-evaluation-state.json` | `fsd-refinement-orchestrator` (initialized), evaluation subagents (updated) | Per-evaluation pass: dimension scores, findings |
| `.legacyleap/.agent-state/doc-quality-state.json` | `fsd-refinement-orchestrator` (initialized), doc-quality subagents (updated) | Per-improvement pass: correctness issues, quality scores |

## Completion Output

When the command completes, report:

```text
Completion status: <CLIENT_READY|BEST_EFFORT>
Final FSD version: <path-to-final-v_N>
Final evaluation score: <score>/10
Refinement iterations performed: <count>
Final evaluation report: <path-to-final-evaluation-report>
```

`Refinement iterations performed` counts only copied-version improvement attempts. If the existing latest FSD already meets the threshold during baseline evaluation, this value is `0`.
