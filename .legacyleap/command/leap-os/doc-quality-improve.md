---
description: "End-to-end Technical Specification Documentation and Functional Specification Documentation quality improvement — correctness verification, verbosity reduction, beautiful diagram rendering, quality scoring to 90%, and optional document splitting for client delivery"
agent: doc-quality-orchestrator
---

# Document Quality Improvement Command

This command automatically improves the quality of your Technical Specification Documentation and/or Functional Specification Documentation through an iterative multi-agent pipeline. It ensures documents are correct, concise (20–25 pages), visually stunning, and ready for client presentation with a **90% quality threshold**.

**Customer delight is the ultimate goal.** The final documents should make clients feel confident about the modernization journey — not worried about complexity or effort.

## What It Does

The command runs a fully automated quality improvement pipeline that:

- **Verifies correctness** — Cross-references every claim against actual source code, MCM data, and domain conventions
- **Analyzes domain accuracy** — Validates business terminology, rules, and workflows against the application domain
- **Checks diagrams** — Verifies all image references, validates Mermaid syntax, identifies sections needing diagrams
- **Removes noise** — Eliminates verbose filler text, redundant sections, internal notes, and generic boilerplate
- **Ensures client-readiness** — Removes alarming language, internal artifacts, sensitive info, draft markers
- **Renders beautiful diagrams** — Generates Mermaid code with professional color palette, renders via project Mermaid service (from `leap.properties`)
- **Protects images** — Ensures existing valid images are never broken during edits
- **Scores quality** — Produces a quality scorecard across correctness, completeness, readability, visual quality, and presentation
- **Iterates until 95%** — Repeats the improvement cycle until documents score ≥ 9.5/10 or max iterations reached
- **Enforces 20–25 pages** — Reduces document to ~10,000 words using tables, diagrams, and concise prose
- **Splits if needed** — Breaks oversized documents into navigable sub-documents with references
- **Outputs .md and .docx** — Both formats for maximum delivery flexibility
- **Applies LegacyLeap branding** — Logo header and "Powered by LegacyLeap" footer on all documents
- **Enterprise-scale ready** — Processes FSD and TSD in parallel, chunks large documents by section, accesses MCM via Neo4j with pagination when configured
- **Tech-agnostic** — Works with Java, C#, Python, Go, COBOL, Node.js, Ruby, PHP, Kotlin, Scala, or any stack

## Prerequisites

Before running this command, ensure:

1. **Technical Specification Documentation and/or Functional Specification Documentation are generated**:
   ```bash
   bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
   bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh
   ```

2. **Source code is available** in the project's `legacy_code/` directory

3. **MCM scan results exist** (from `bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh`)

4. **`.legacyleap/leap.properties`** exists with service configuration (MERMAID_URL, CHROMA settings)

## Usage

```bash
# Improve both Technical Specification Documentation and Functional Specification Documentation
/doc-quality-improve

# The command will prompt you for:
# - Document type (tsd, fsd, or both)
# - Max iterations (default: 3)
# - Quality threshold (default: 9.5 / 10 — 95%)
```

## How It Works

### Iteration 1..N (until quality ≥ 90%):

```
┌─────────────────────────────────────────────────────┐
│  Step 1: Correctness Analysis                       │
│  ├─ Cross-reference doc vs source code + MCM        │
│  ├─ Verify domain terminology and business rules    │
│  ├─ Check all diagrams (exist? correct? styled?)    │
│  ├─ Flag client-readiness issues                    │
│  └─ Produce correctness report                      │
├─────────────────────────────────────────────────────┤
│  Step 2: Structure Optimization                     │
│  ├─ Fix all correctness issues                      │
│  ├─ Reduce to 20-25 pages (tables + diagrams)       │
│  ├─ Remove internal artifacts and alarming language  │
│  ├─ Ensure consistent full-form terminology          │
│  └─ Produce optimized document                      │
├─────────────────────────────────────────────────────┤
│  Step 3: Diagram Rendering                          │
│  ├─ Detect missing/broken diagrams                  │
│  ├─ Generate Mermaid with professional colors       │
│  ├─ Validate syntax (zero tolerance for errors)     │
│  ├─ Render via MERMAID_URL from leap.properties     │
│  └─ Ensure every section has a diagram              │
├─────────────────────────────────────────────────────┤
│  Step 4: Quality Verification                       │
│  ├─ Score: Correctness (25%)                        │
│  ├─ Score: Completeness (20%)                       │
│  ├─ Score: Readability (25%) — 20-25 page target    │
│  ├─ Score: Visual Quality (15%) — professional look │
│  ├─ Score: Presentation (15%) — customer delight    │
│  └─ Overall ≥ 9.5? → Done or iterate               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Step 5: Document Splitting (if still >25 pages)    │
│  ├─ Split into logical sub-documents                │
│  ├─ Create overview with references                 │
│  └─ Each sub-document is self-contained             │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  Step 6: Final Report & .docx Generation            │
│  ├─ .legacyleap/reports/doc-quality-report.md       │
│  └─ Generate .docx versions via pandoc              │
└─────────────────────────────────────────────────────┘
```

## Agents Used

| Agent | Role |
|-------|------|
| `doc-quality-orchestrator` | Controls the full pipeline, manages iterations and state |
| `doc-correctness-analyzer` | Verifies accuracy against source code, MCM, domain, and diagrams |
| `doc-structure-optimizer` | Reduces to 20–25 pages, fixes issues, ensures client-presentable |
| `doc-diagram-renderer` | Beautiful professional diagrams via project Mermaid service |
| `doc-quality-verifier` | Scores quality against 90% threshold |
| `doc-splitter` | Splits large documents into navigable sub-documents |

## Output Files

| File | Description |
|------|-------------|
| Improved Technical Specification Documentation (.md + .docx) | In-place improvement of existing document |
| Improved Functional Specification Documentation (.md + .docx) | In-place improvement of existing document |
| `.legacyleap/reports/doc-quality-report.md` | Comprehensive quality improvement report |
| `.legacyleap/.agent-state/doc-quality-state.json` | Full audit trail with all scores |
| `sections/` subfolder (if split) | Sub-documents with navigation |

## Quality Scoring

The final quality score is a weighted average:

```
Overall = Correctness (25%) + Completeness (20%) + Readability (25%)
        + Visual Quality (15%) + Presentation (15%)
```

**Threshold:** 9.5 / 10 (95%)

**Outcome states:**
- **CLIENT_READY** — Overall score ≥ 9.5
- **BEST_EFFORT** — Max iterations (3) reached, best achievable quality
- **PLATEAU** — No further improvement possible (scores stopped increasing)

## Safety Features

- Backups created before each iteration (recoverable)
- Existing valid images are protected from accidental removal
- Source code is never modified
- No git operations are performed
- Max iteration limit (3) prevents infinite loops
- Document corruption detection with automatic rollback
- No internal notes or change descriptions written to client documents
- Sensitive information (emails, passwords, URLs) automatically redacted

## When to Use

Use this command after generating Technical Specification Documentation / Functional Specification Documentation to ensure they are:
- Technically/functionally accurate (no hallucinated or incorrect content)
- Domain-correct (proper terminology and business rules)
- Concise and professional (20–25 pages, tables over prose)
- Visually stunning (beautiful colored diagrams in every section)
- Client-presentation ready (no internal artifacts, reassuring tone)
- Properly sized (split if too large)
- Available in both .md and .docx formats
