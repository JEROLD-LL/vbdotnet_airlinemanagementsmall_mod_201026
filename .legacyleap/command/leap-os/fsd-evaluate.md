---
description: "Read-only FSD evaluation pipeline — scores any Functional Specification Document against project MCM, produces weighted scorecard, gap report, and proposed-additions draft without modifying the FSD"
agent: fsd-evaluation-orchestrator
---

# FSD Evaluation Command

This command evaluates the quality and completeness of a Functional Specification Document (FSD) by cross-referencing it against the project's Meta Cognitive Model (MCM) and producing a comprehensive evaluation report with actionable recommendations.

**This is a read-only evaluation pipeline.** It never modifies the FSD itself — it produces a separate report and a proposed-additions file with draft content for missing or weak sections.

## What It Does

The command runs a single-pass evaluation pipeline that:

- **Prompts for file paths** — Asks user for FSD and MCM paths before attempting auto-discovery
- **Smart auto-discovery** — If user types 'auto', searches standard locations for FSD/MCM files
- **Interactive and flexible** — User can provide explicit paths or let the system search
- **Builds a project digest** — Distills MCM into a compact cached summary (project-digest.json) for fast evaluation
- **Evaluates coverage** — Checks FSD structure against expected sections and MCM-derived inventories (entities, forms, integrations, enums)
- **Verifies correctness** — Spot-checks 20-30 verifiable claims against MCM data (entity fields, role values, integration names)
- **Assesses depth** — Flags placeholder/vague content, empty sections, journeys without steps, rules without conditions
- **Validates domain alignment** — Ensures FSD-style discipline (no TSD leakage), consistent terminology, audience appropriateness
- **Checks diagrams** — Verifies image references resolve and required sections have diagrams
- **Drafts improvements** — Writes proposed Markdown for missing sections into fsd-proposed-additions.md
- **Produces scorecard** — Weighted score across 6 dimensions with detailed justification

## Prerequisites

Before running this command, you will be prompted for:

1. **FSD path** — You'll be asked to provide the path to your Functional Specification Document
   - Provide explicit path (e.g., `Latest_fsd_v3.md`, `comprehend/functional_doc/v_3/Latest_FSD_Document/Latest_fsd.md`)
   - Or type `auto` to search standard locations automatically
   
2. **MCM path** — You'll be asked to provide the path to your Meta Cognitive Model file
   - Provide explicit path (e.g., `meta_cognitive_model.json`, `scan_assessment_reports/meta_cognitive_model.json`)
   - Or type `auto` to search standard locations automatically

Optional:
3. **Project directory structure** — AddInventory-main/ or similar project folder (detected from MCM metadata)
4. **Legacy source code** — If available at legacy_code/, agents will spot-check claims against source; otherwise they rely on MCM cognitive fields

**Note:** You can skip the prompts by providing explicit paths via command line arguments: `/fsd-evaluate --fsd <path> --mcm <path>`

## Usage

### Interactive Mode (Recommended)

```bash
# Run without arguments - you'll be prompted for FSD and MCM paths
/fsd-evaluate
```

**Example interaction:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FSD Path Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please provide the path to your FSD:
  1. Enter the full path (e.g., Latest_fsd_v3.md)
  2. Type 'auto' to search standard locations

> Latest_fsd_v3.md
✅ FSD provided by user: Latest_fsd_v3.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  MCM Path Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please provide the path to your MCM file:
  1. Enter the full path (e.g., meta_cognitive_model.json)
  2. Type 'auto' to search standard locations

> auto
🔍 Running auto-discovery for MCM...
✅ MCM discovered via auto-discovery: meta_cognitive_model.json
```

### Command Line Arguments (Skip Prompts)

```bash
# Provide explicit paths - no prompts
/fsd-evaluate --fsd Latest_fsd_v3.md --mcm meta_cognitive_model.json

# Specify explicit FSD path
/fsd-evaluate --fsd comprehend/functional_doc/v_3/Latest_FSD_Document/Latest_fsd.md

# Provide legacy code path for source-level verification
/fsd-evaluate --fsd Latest_fsd_v3.md --mcm meta_cognitive_model.json --legacy-code AddInventory-main/Add\ Inventory/

# Full explicit paths
/fsd-evaluate --fsd comprehend/functional_doc/v_3/Latest_FSD_Document/Latest_fsd.md --mcm scan_assessment_reports/meta_cognitive_model.json --project AddInventory-main
```

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  Phase 0: Input Discovery & Output Setup            │
│  ├─ Prompt user for FSD path (or use --fsd arg)     │
│  │   └─ If 'auto', search standard locations        │
│  ├─ Prompt user for MCM path (or use --mcm arg)     │
│  │   └─ If 'auto', search standard locations        │
│  ├─ Detect project folder from MCM metadata         │
│  ├─ Optional: detect legacy_code/ path              │
│  └─ Resolve versioned output dir (YYYY-MM-DD/v{N})  │
├─────────────────────────────────────────────────────┤
│  Phase 2: Project Digest Build (cached on MCM hash) │
│  ├─ Parse MCM: entities, forms, enums, operations   │
│  ├─ Extract assemblies, integrations, business rules│
│  ├─ Build compact JSON digest (~200 KB)             │
│  └─ Cache at .legacyleap/.agent-state/              │
├─────────────────────────────────────────────────────┤
│  Phase 3: Parallel Evaluation (5 dimensions)        │
│  ├─ [ReAct] Coverage: Reason→Act→Observe            │
│  ├─ [ReAct+Spawn] Correctness: 20-30 claim checks   │
│  │   └─ Spawn subagents for complex sections        │
│  ├─ [ReAct+Spawn] Depth: Flag vague content         │
│  │   └─ Spawn subagents for extensive sections      │
│  ├─ Domain: FSD-style discipline + terminology      │
│  └─ Diagrams: Image references + required diagrams  │
├─────────────────────────────────────────────────────┤
│  Phase 4: Readability Score (Orchestrator)          │
│  └─ Calculate from word count + structure metrics   │
├─────────────────────────────────────────────────────┤
│  Phase 5: Self-Reflection Quality Check             │
│  ├─ Validate scores against evidence                │
│  ├─ Detect score-evidence mismatches                │
│  ├─ Check for hallucinated findings                 │
│  └─ Adjust scores if justified                      │
├─────────────────────────────────────────────────────┤
│  Phase 6: Improvement Recommendations               │
│  ├─ Synthesize findings into ranked recommendations │
│  ├─ Draft Markdown for missing sections             │
│  └─ Write to evaluation-result/fsd-proposed-additions.md │
├─────────────────────────────────────────────────────┤
│  Phase 7: Final Reporting                           │
│  ├─ Calculate weighted score (6 dimensions)         │
│  ├─ Generate evaluation report                      │
│  └─ Consolidate all outputs to versioned folder     │
└─────────────────────────────────────────────────────┘
```

## Scoring Dimensions

The final score is a weighted average out of 10:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Coverage** | 25% | Expected FSD sections present + MCM-derived inventory coverage |
| **Correctness** | 25% | Claims verified against MCM (SUPPORTED vs. FALSE vs. UNSUPPORTED) |
| **Depth** | 15% | Specificity and detail (no vague/placeholder content) |
| **Domain Alignment** | 15% | FSD-style discipline, terminology consistency, audience fit |
| **Diagram Coverage** | 10% | Image references resolve + required sections have diagrams |
| **Clarity & Readability** | 10% | Professional tone, conciseness, logical flow |

**Outcome states:**
- **EXCELLENT** — Overall score ≥ 9.0
- **ACCEPTABLE** — Overall score 7.5–8.9
- **NEEDS_IMPROVEMENT** — Overall score 5.0–7.4
- **INSUFFICIENT** — Overall score < 5.0

## Output Files

All output files are written to a versioned directory structure that preserves evaluation history:

**Path pattern:** `evaluation-result/<YYYY-MM-DD>/fsd-eval-v{N}/`

**Examples:**
- First run on May 7: `evaluation-result/2026-05-07/fsd-eval-v0/`
- Second run on May 7: `evaluation-result/2026-05-07/fsd-eval-v1/`
- First run on May 8: `evaluation-result/2026-05-08/fsd-eval-v0/`

| File | Description |
|------|-------------|
| `fsd-evaluation-report.md` | Comprehensive scorecard, per-dimension justification, top 10 missing items, top 10 weakest sections, claim verification table, glossary coverage |
| `fsd-proposed-additions.md` | Draft Markdown for missing sections (ready to copy/paste, but never auto-applied) |
| `fsd-evaluation-state.json` | Machine-readable findings (claims table, gap list, recommendations, quality check metadata) |
| `project-digest.json` | Cached project digest (copy - original stays in .agent-state for caching) |

**Benefits of versioning:**
- Multiple evaluation runs preserved without overwriting
- Easy comparison between evaluation iterations
- Date-organized history for tracking improvements over time

## Agents Used

| Agent | Role |
|-------|------|
| `fsd-evaluation-orchestrator` | Discovers inputs, delegates to sub-agents, aggregates results, calculates final score |
| `project-digest-builder` | Distills MCM into compact cached JSON digest |
| `fsd-coverage-evaluator` | Checks FSD structural completeness vs. expected taxonomy and MCM inventories (uses ReAct pattern) |
| `fsd-correctness-evaluator` | Spot-checks 20-30 verifiable claims against MCM data (uses ReAct + spawns subagents for complex sections) |
| `fsd-depth-evaluator` | Flags placeholder/vague content, empty sections (uses ReAct + spawns subagents for extensive sections) |
| `fsd-domain-evaluator` | Validates FSD-style discipline and terminology consistency |
| `fsd-diagram-evaluator` | Verifies image references and diagram requirements |
| `fsd-evaluation-quality-checker` | **Self-reflection agent** — Reviews scores for consistency, detects hallucination, adjusts scores if needed |
| `fsd-improvement-recommender` | Synthesizes findings and drafts proposed Markdown additions |
| `fsd-evaluation-reporter` | Produces final report and state files |

## When to Use

Use this command to:

- **Quality-check an FSD before client delivery** — Identify gaps and weaknesses proactively
- **Compare FSD coverage against actual codebase** — Ensure documentation matches reality
- **Generate improvement recommendations** — Get actionable, prioritized suggestions
- **Draft missing content** — Receive proposed Markdown for gaps (fsd-proposed-additions.md)
- **Establish baseline quality metrics** — Track FSD quality over time

## Relationship to /doc-quality-improve

- **`/fsd-evaluate`** — Read-only evaluator (this command). Produces reports and recommendations. Never modifies FSD.
- **`/doc-quality-improve`** — Mutating fixer. Iterates on FSD/TSD, edits them in place, renders diagrams, targets 95% quality threshold.

Use `/fsd-evaluate` first to understand what's missing, then optionally run `/doc-quality-improve` to apply fixes.

## Safety Features

- **Read-only evaluation** — FSD is never modified
- **User-first prompting** — Asks for file paths before attempting auto-discovery
- **Flexible input** — Explicit paths or 'auto' for smart search
- **Versioned output** — Each run gets its own dated/versioned folder, preserving evaluation history
- **MCM digest caching** — Fast re-runs when MCM unchanged
- **Smart auto-discovery** — Works with various project layouts when user requests it
- **Graceful degradation** — Works without legacy_code/ (relies on MCM cognitive fields)
- **No git operations**
- **No external API calls** (except local Mermaid service if configured)

## Example Output Structure

```markdown
# FSD Evaluation Report

**Evaluation ID:** 2026-05-07/fsd-eval-v0
**FSD:** Latest_fsd_v3.md (4,842 lines)
**MCM:** meta_cognitive_model.json (112,879 lines, 3.5 MB)
**Project:** AddInventory-main (VB.NET, WinForms)
**Evaluation Date:** 2026-05-07

## Overall Score: 7.8 / 10 (ACCEPTABLE)

| Dimension | Score | Weight | Weighted | Status |
|-----------|-------|--------|----------|--------|
| Coverage | 8.5 | 25% | 2.13 | ✅ Strong |
| Correctness | 7.2 | 25% | 1.80 | ⚠️ Needs attention |
| Depth | 7.0 | 15% | 1.05 | ⚠️ Some vague sections |
| Domain Alignment | 8.8 | 15% | 1.32 | ✅ Strong |
| Diagram Coverage | 6.5 | 10% | 0.65 | ⚠️ Missing diagrams |
| Clarity & Readability | 8.5 | 10% | 0.85 | ✅ Strong |

## Top 10 Recommendations (Priority Order)

1. [CRITICAL] Add 12 missing entity field definitions (inpartsub missing IPAddress, MacAddress descriptions)
2. [HIGH] Fix 3 incorrect claim about PO validation logic (line 2511: states "BuyQtyDue >= received", actual code checks "<=")
3. [HIGH] Add 8 missing decision points (MAC address validation, IP auto-assignment triggers)
...

## Claim Verification Summary

- **SUPPORTED:** 22 claims (73%)
- **UNSUPPORTED:** 6 claims (20%)
- **FALSE:** 2 claims (7%)

## Missing Sections

- Decision Point: IP Address Auto-Assignment (mentioned in code, not in FSD)
- Business Rule: Zebra Printer Enablement by Owner
- Data Entity: BarcodeTemplate (fields not documented)
...
```
