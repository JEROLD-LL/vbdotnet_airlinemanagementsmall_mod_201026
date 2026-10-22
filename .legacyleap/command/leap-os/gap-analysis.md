You are orchestrating a comprehensive **GAP Analysis** for a legacy-to-modern code transformation project. This multi-phase process will analyze the modernized codebase against multiple baselines to identify gaps, missing features, and architectural violations.

## Overview

The GAP Analysis consists of three parallel sub-agent analyses that generate three specific outputs:

**PHASE 0 (NEW):** Spec Parity Gap Analysis (via spec-parity-gap-agent) → per-spec `gap_report.md` in `leap-os/specs/*/gap_reports/gap_report.md`
**PHASE 1:** Code Inventory Gap Analysis (via code-inventory-gap-agent) → `code_base_inventory.md`
**PHASE 2:** Functional Gap Analysis (via functional-gap-agent) → `functional_gaps.md`
**PHASE 3:** Architecture Gap Analysis (via architecture-gap-agent) → `architectural_violations.md`

**FINAL OUTPUT:** Generate only `GAP_report.md` (no additional summaries or executive documents)

Carefully read and execute the instructions in the following files IN SEQUENCE, following their numbered file names. Only proceed to the next numbered instruction file once the previous numbered instruction has been executed.

## PRE-FLIGHT: Load DB Schema, Backend Rules, API Contract, and Target Tech Context

**Before starting any phase**, load context files that anchor gap analysis to the same **CLI migration config** as modernization: database shape, coding rules, **legacy API contract**, and **target stack** (including **backend addons** from `target_tech.json`).

### Step 1: Read project metadata

Read `.legacyleap/metadata.json` and extract the following fields (use the **actual** values from the file — do not assume a stack):
- `legacyleap_plugin` — plugin folder under the project 
- `migration_config` — config subfolder under that plugin 
- `migration_complexity` — stack tier key in `target_tech.json` (e.g. `standard`, `minimal`, `enterprise`); default to `enterprise` if missing
- `is_schema_file_provided` (boolean)
- `is_backend_rule_provided` (boolean)
- `is_api_contract_provided` (boolean)

### Step 2: Load DB Schema (if available)

If `is_schema_file_provided` is `true`:
- Read the file at: `{legacyleap_plugin}/configs/{migration_config}/schema.sql`
- Store this as **DB Schema Context** to pass to all sub-agents.
- This schema is the **authoritative definition of the existing database**. Gaps that would require creating tables or columns already present in this schema are **not gaps** — they are correct. Gaps that use **different column names, types, or table structures** from this schema **are** gaps that must be flagged.

If `is_schema_file_provided` is `false` or the file does not exist, skip silently.

### Step 3: Load Backend Rules (if available)

If `is_backend_rule_provided` is `true`:
- Read the file at: `{legacyleap_plugin}/configs/{migration_config}/backend_rules.txt`
- Store this as **Backend Rules Context** to pass to all sub-agents.
- These rules define project-specific coding conventions and architectural constraints. Any modernized code that violates these rules is a gap.

If `is_backend_rule_provided` is `false` or the file does not exist, skip silently.

### Step 4: Load Legacy API Contract (if available)

If `is_api_contract_provided` is `true`:
- Read the file at: `{legacyleap_plugin}/configs/{migration_config}/legacy_api_contract.json`
- Store this as **API Contract Context** to pass to all sub-agents.
- This contract is the **authoritative allowed API surface** for the project by **`id`**. **`path` = modern route**; **`legacyPath`** is reference only (see `profiles/default/docs/legacy-api-contract.md` for backward-compat when `path` contains legacy-only URLs). Endpoints whose **`id` is not** in `endpoints[]` are **Proposed / HITL** (default: do not implement), not automatic gaps. Do not treat modern code using `/api/v1/...` instead of legacy paths as out-of-contract.

**API precedence:** contract > legacy evidence > rules/schema/target_tech > spec/FSD.

If `is_api_contract_provided` is `false` or the file does not exist, skip silently.

### Step 5: Load Target Tech — backend stack only (if available)

Read the file at: `{legacyleap_plugin}/configs/{migration_config}/target_tech.json`

If the file exists:
1. Parse JSON and select the stack using **`migration_complexity`** from Step 1: `stacks[<migration_complexity>].backend` (fallback: `stacks.standard.backend`, then top-level `target_backend_technology` only).
2. Store as **Target Tech Context (backend only)** with these fields explicitly listed for sub-agents:
   - `backend_core`, `backend_framework`, `backend_orm`, `backend_api_style`, `backend_auth`, `backend_validation`, `backend_config`
   - **`backend_addons`** — required third-party / infrastructure addons (SQL client, Swagger/OpenAPI, logging, Docker, etc.)
3. **Do not** pass `frontend_*` keys or `stacks.*.frontend` into gap analysis — backend scope only.

If the file does not exist, skip silently and note in the final `GAP_report.md` summary: `Target Tech Context: not loaded`.

**Purpose:** Gap analysis must verify the modernized backend uses the **same target packages and platform choices** the CLI modernization config declared — not only what the FSD or a generic blueprint says.

### Step 6: Pass context to sub-agents

When invoking each sub-agent (PHASES 0–3), include **DB Schema Context**, **Backend Rules Context**, **API Contract Context**, and **Target Tech Context (backend only)** (each if loaded) as additional inputs alongside the standard inputs for that phase.

**Architecture gap (PHASE 3)** must perform an explicit **Backend Addons Compliance** check (see architecture-gap-agent). **Code inventory (PHASE 1)** must list missing required packages when Target Tech Context was provided.

---

Instructions to follow in sequence:

# PHASE 0 (NEW): Spec Parity Gap Analysis (per spec)

This optional phase produces a per-spec `gap_report.md` for each spec under `leap-os/specs/`, by scanning the entire **Modernized Code Directory** for evidence that the spec is implemented.\n\nEach per-spec report is written under the spec’s `gap_reports/` folder.

## Step 1: Verify Required Inputs

Before starting analysis, verify that you have access to:

1. **Modernized Code Directory** - The transformed codebase (scan the entire codebase)
2. **Specs Root Directory** - Defaults to `workspace/leap-os/specs` unless the user specifies otherwise

If any required input is missing, prompt the user:

```
To perform Spec Parity GAP analysis, I need the following information:

1. Path to Modernized Code Directory: [user to provide]
2. Path to Specs Root Directory (optional): [user to provide or default workspace/leap-os/specs]
```

WAIT for the user to provide required paths before proceeding.

## Step 2: Delegate to Spec Parity Gap Agent

Invoke the **spec-parity-gap-agent** by following these instructions:

You are now acting as the **spec-parity-gap-agent**.

Read the agent instructions from:
`workspace/.legacyleap/agent/leap-os/spec-parity-gap-agent.md`

Execute the spec parity analysis as specified in that agent definition, using:
- Modernized Code Directory
- Specs Root Directory
- **API Contract Context** (if loaded in PRE-FLIGHT) — classify by contract `id`; verify modernized code against **modern `path`**, not legacy URLs

### Output Guardrails (IMPORTANT)
- Only generate a report for spec folders that contain a `spec.md`.
- If required inputs are missing/invalid (e.g., Modernized Code Directory not provided or not accessible), **STOP** and prompt the user. Do not create any folders/files.
- **Do not pre-create** `gap_reports/` for every spec. Create `gap_reports/` **only at the moment you are actually writing** `gap_report.md`.
- If a spec is skipped (e.g., missing `spec.md`), log: `SKIPPED: <spec-folder> (reason)` and do not create `gap_reports/`.

Generate output reports: for each eligible spec folder, create `gap_report.md` at `workspace/leap-os/specs/<spec-folder>/gap_reports/gap_report.md`.

## Step 3: Confirm Completion

Once per-spec reports have been created, display:

```
✅ PHASE 0 COMPLETE: Spec Parity Gap Analysis

Reports generated: `workspace/leap-os/specs/*/gap_reports/gap_report.md`

NEXT STEP 👉 Proceed to PHASE 1: Code Inventory Gap Analysis (optional)
```

# PHASE 1: Code Inventory Gap Analysis

The FIRST STEP is to perform code inventory analysis to identify coverage and untransformed components.

## Step 1: Verify Required Inputs

Before starting analysis, verify that you have access to:

1. **Legacy Code Directory** - The original codebase
2. **Modernized Code Directory** - The transformed codebase
3. **MCM (Meta Cognitive Model)** - JSON representation of legacy code
4. **Tech Stack Blueprint** - Architecture diagram or tech stack documentation

If any of these inputs are missing, prompt the user:

```
To perform GAP analysis, I need the following information:

1. Path to Legacy Code Directory: [user to provide]
2. Path to Modernized Code Directory: [user to provide]
3. Path to MCM JSON file: [user to provide]
4. Path to Tech Stack Blueprint/Documentation: [user to provide]
5. Path to FSD (Functional Specification Document): [user to provide]

Please provide the paths to these required files and directories.
```

WAIT for the user to provide all required paths before proceeding.

## Step 2: Delegate to Code Inventory Gap Agent

Once you have all required inputs, invoke the **code-inventory-gap-agent** by following these instructions:

You are now acting as the **code-inventory-gap-agent**.

Read the agent instructions from:
`workspace/.legacyleap/agent/leap-os/code-inventory-gap-agent.md`

Execute the code inventory analysis as specified in that agent definition, using the provided:
- Legacy Code Directory
- Modernized Code Directory
- MCM JSON file
- Tech Stack Blueprint

Generate the output report: `code_base_inventory.md` in the location specified by the user or default to `workspace/gap-analysis/code_base_inventory.md`.

## Step 3: Confirm Completion

Once code_base_inventory.md has been created, display:

```
✅ PHASE 1 COMPLETE: Code Inventory Gap Analysis

Report generated: [path to code_base_inventory.md]

Summary:
- Total Legacy Components: [count]
- Fully Transformed: [count] ([X]%)
- Partially Transformed: [count] ([X]%)
- Missing: [count] ([X]%)

NEXT STEP 👉 Proceed to PHASE 2: Functional Gap Analysis
```

# PHASE 2: Functional Gap Analysis

Now that we have the code inventory analysis, we need to perform functional gap analysis to identify missing features and functional mismatches.

## Step 1: Verify FSD Document

Confirm that the Functional Specification Document (FSD) path was provided in PHASE 1.

If not provided, prompt:
```
Please provide the path to the Functional Specification Document (FSD).
```

WAIT for the user to provide the path.

## Step 2: Delegate to Functional Gap Agent

Invoke the **functional-gap-agent** by following these instructions:

You are now acting as the **functional-gap-agent**.

Read the agent instructions from:
`workspace/.legacyleap/agent/leap-os/functional-gap-agent.md`

Execute the functional gap analysis as specified in that agent definition, using the provided:
- Modernized Code Directory
- FSD Document
- Tech Stack Blueprint
- **Legacy Code Directory** (same path used in PHASE 1) — required to cross-check every identified gap against the actual legacy implementation
- **API Contract Context** (if loaded in PRE-FLIGHT) — match by `id`; report missing `id`s as **Proposed / HITL**; compare modern code to **modern routes**; flag legacy-path-only implementations as route modernization gaps; keep **FSD Artifacts** for no legacy evidence

Generate the output report: `functional_gaps.md` in the same directory as code_base_inventory.md (default: `workspace/gap-analysis/functional_gaps.md`).

## Step 3: Confirm Completion

Once functional_gaps.md has been created, display:

```
✅ PHASE 2 COMPLETE: Functional Gap Analysis

Report generated: [path to functional_gaps.md]

Summary:
- Total Functional Requirements: [count]
- Fully Implemented: [count] ([X]%)
- Partially Implemented (CLI created something, needs completion): [count] ([X]%)
- Not Implemented (CLI created nothing, needs full implementation): [count] ([X]%)
- FSD Artifacts (not traceable to legacy code — DO NOT implement): [count]
- API Contract violations / Proposed (HITL) (in spec or code but not in contract): [count]
- Critical Gaps: [count]

NEXT STEP 👉 Proceed to PHASE 3: Architecture Gap Analysis
```

# PHASE 3: Architecture Gap Analysis

Now we need to perform architecture gap analysis to identify architectural violations and deviations from the tech stack blueprint.

## Step 1: Delegate to Architecture Gap Agent

Invoke the **architecture-gap-agent** by following these instructions:

You are now acting as the **architecture-gap-agent**.

Read the agent instructions from:
`workspace/.legacyleap/agent/leap-os/architecture-gap-agent.md`

Execute the architecture gap analysis as specified in that agent definition, using the provided:
- Modernized Code Directory
- Tech Stack Blueprint
- MCM JSON file

Generate the output report: `architectural_violations.md` in the same directory as the other reports (default: `workspace/gap-analysis/architectural_violations.md`).

## Step 2: Confirm Completion

Once architectural_violations.md has been created, display:

```
✅ PHASE 3 COMPLETE: Architecture Gap Analysis

Report generated: [path to architectural_violations.md]

Summary:
- Overall Compliance: [X]%
- Major Violations: [count]
- Minor Deviations: [count]
- Critical Issues: [count]

NEXT STEP 👉 Proceed to PHASE 4: Synthesize GAP Report
```

# PHASE 4: Synthesize Comprehensive GAP Report

Now that all three sub-analyses are complete, synthesize them into one comprehensive GAP report.

## Step 1: Read All Sub-Reports

Read the following reports in their entirety:
1. `code_base_inventory.md`
2. `functional_gaps.md`
3. `architectural_violations.md`

## Step 2: Synthesize Comprehensive Report

Create a comprehensive `GAP_report.md` that consolidates findings from all three sub-reports.

### CRITICAL: Report Quality Requirements

Before generating the report, apply these mandatory quality standards:

#### Anti-Duplication Rules (MANDATORY)

| Rule | Description | Example Violation to Avoid |
|------|-------------|---------------------------|
| **Single Metric Location** | Each statistic appears ONCE | Don't repeat "33% health score" in multiple sections |
| **No Repeated Timelines** | Timeline appears in Section 8 only | Don't mention "10-12 weeks" in Executive Summary AND Roadmap |
| **Consolidated Budgets** | Budget details in Section 9 only | Don't list costs in Recommendations AND Resources |
| **Consolidated Recommendations** | Recommendations in Conclusion only | Don't scatter recommendations throughout |
| **Cross-Reference, Don't Copy** | Use "See Section X" for related info | Don't restate domain health scores in Conclusion |

#### Section Ownership (Who Owns What)

| Information Type | Authoritative Section | Other Sections |
|-----------------|----------------------|----------------|
| Health Score & Metrics | Executive Summary | Reference only |
| Critical Issues List | Section 5 (Risks) | Reference only |
| Timeline Details | Section 8 (Roadmap) | Reference only |
| Budget & Resources | Section 9 | Reference only |
| Recommendations | Conclusion | Reference only |
| Domain-by-Domain Status | Section 6 | Summary table elsewhere |

#### Table-First Formatting Rules

**MANDATORY Table Format For:**
- All metric summaries (coverage %, compliance %, etc.)
- Priority matrices and action lists
- Risk assessments
- Resource requirements
- Timeline/roadmap phases
- Domain health summaries

**Narrative Allowed Only For:**
- Executive Summary context (max 3 short paragraphs)
- Conclusion (max 2 paragraphs)
- Complex cross-cutting issue explanations

#### Length Constraints

| Section | Maximum Length |
|---------|---------------|
| Executive Summary | 200 words + metrics table |
| Each Domain Summary | 50 words + status table row |
| Each Risk Description | 75 words |
| Conclusion | 150 words |
| **Total Report** | Aim for 50% reduction vs verbose approach |

### Report Structure

```markdown
# Comprehensive GAP Analysis Report

**Project:** [Project Name] | **Date:** [Current Date] | **Analyst:** GAP Analysis Command

| Aspect | Legacy | Modern |
|--------|--------|--------|
| System | [Legacy tech] | [Modern tech] |

---

## Executive Summary

[Maximum 3 short paragraphs: (1) Project context, (2) Key findings, (3) Recommendation. No statistics here—they go in the table below.]

### Modernization Health Metrics

| Metric | Score | Weight | Weighted |
|--------|-------|--------|----------|
| Code Inventory Coverage | [X]% | 40% | [X] pts |
| Functional Implementation | [X]% | 40% | [X] pts |
| Architectural Compliance | [X]% | 20% | [X] pts |
| **Health Score** | **[X]%** | - | - |

### Critical Issues Count

| Category | Critical | High | Medium | Total |
|----------|----------|------|--------|-------|
| Code Gaps | [n] | [n] | [n] | [n] |
| Functional Gaps | [n] | [n] | [n] | [n] |
| Arch Violations | [n] | [n] | [n] | [n] |
| **Total** | **[n]** | **[n]** | **[n]** | **[n]** |

---

## 1. Code Inventory Analysis Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Legacy Components | [n] | 100% |
| Fully Transformed | [n] | [X]% |
| Partially Transformed | [n] | [X]% |
| Missing | [n] | [X]% |

### Top Code Gaps

| Component | Impact | Priority | Effort |
|-----------|--------|----------|--------|
| [Component 1] | [Brief impact] | Critical | [hours] |
| [Component 2] | [Brief impact] | High | [hours] |
| [Component 3] | [Brief impact] | Medium | [hours] |

**Detailed Report:** `code_base_inventory.md`

---

## 2. Functional Gap Analysis Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Requirements | [n] | 100% |
| Fully Implemented | [n] | [X]% |
| Partially Implemented | [n] | [X]% |
| Not Implemented | [n] | [X]% |

### Critical Functional Gaps

| Feature | Business Impact | Severity | Blocking? |
|---------|-----------------|----------|-----------|
| [Feature 1] | [Impact] | Critical | Yes/No |
| [Feature 2] | [Impact] | High | Yes/No |
| [Feature 3] | [Impact] | Medium | Yes/No |

**Detailed Report:** `functional_gaps.md`

---

## 3. Architectural Compliance Summary

| Metric | Count |
|--------|-------|
| Overall Compliance | [X]% |
| Major Violations | [n] |
| Minor Deviations | [n] |
| Critical Issues | [n] |

### Critical Architectural Issues

| Violation | Category | Impact | Fix Effort |
|-----------|----------|--------|------------|
| [Violation 1] | [Type] | [Impact] | [Effort] |
| [Violation 2] | [Type] | [Impact] | [Effort] |
| [Violation 3] | [Type] | [Impact] | [Effort] |

**Detailed Report:** `architectural_violations.md`

---

## 4. Cross-Cutting Concerns

| Issue | Found In | Combined Impact | Recommendation |
|-------|----------|-----------------|----------------|
| [Issue 1] | Code, Functional | [Impact] | [Action] |
| [Issue 2] | Functional, Arch | [Impact] | [Action] |
| [Issue 3] | All three | [Impact] | [Action] |

*Note: Issues appearing in multiple analyses often have compounding effects. Address these first.*

---

## 5. Risk Assessment

### Risk Matrix

| Risk | Category | Likelihood | Impact | Mitigation | Timeline |
|------|----------|------------|--------|------------|----------|
| [Risk 1] | Code Gap | High | Critical | [Action] | Week 1-2 |
| [Risk 2] | Functional | Medium | High | [Action] | Week 2-4 |
| [Risk 3] | Arch | Low | Medium | [Action] | Month 2 |

*Note: Risks ordered by severity (Likelihood × Impact). See Section 8 for detailed remediation.*

---

## 6. Domain Health Summary

| Domain | Code % | Functional % | Arch % | Health | Status | Key Issue |
|--------|--------|--------------|--------|--------|--------|-----------|
| [Domain 1] | [X]% | [X]% | [X]% | [X]% | ✅/⚠️/❌ | [Issue] |
| [Domain 2] | [X]% | [X]% | [X]% | [X]% | ✅/⚠️/❌ | [Issue] |
| [Domain 3] | [X]% | [X]% | [X]% | [X]% | ✅/⚠️/❌ | [Issue] |

*Note: Domain health = weighted average of three metrics. ✅ ≥90%, ⚠️ 50-89%, ❌ <50%*

---

## 7. Priority Matrix

| Priority | Timeframe | Issue | Source | Impact | Owner |
|----------|-----------|-------|--------|--------|-------|
| **CRITICAL** | 0-2 weeks | [Issue 1] | Code | [Impact] | [TBD] |
| **CRITICAL** | 0-2 weeks | [Issue 2] | Arch | [Impact] | [TBD] |
| **HIGH** | 2-4 weeks | [Issue 3] | Func | [Impact] | [TBD] |
| **HIGH** | 2-4 weeks | [Issue 4] | Code | [Impact] | [TBD] |
| **MEDIUM** | 1-2 months | [Issue 5] | Arch | [Impact] | [TBD] |
| **LOW/DEFER** | Future | [Issue 6] | - | [Rationale] | - |

---

## 8. Remediation Roadmap

| Phase | Timeline | Goal | Key Tasks | Outcome |
|-------|----------|------|-----------|---------|
| **1: Critical** | Weeks 1-2 | Fix blockers | [Task 1], [Task 2], [Task 3] | Unblocked |
| **2: High** | Weeks 3-4 | Core features | [Task 4], [Task 5] | MVP ready |
| **3: Medium** | Months 2-3 | Complete gaps | [Task 6], [Task 7] | Feature complete |
| **4: Polish** | Month 4+ | Optimization | [Task 8], [Task 9] | Production ready |

*Note: Detailed task breakdowns available in sub-reports. Timeline assumes [X] FTE.*

---

## 9. Testing & Verification

### Testing Matrix

| Area | Unit | Integration | E2E | Security | Status |
|------|------|-------------|-----|----------|--------|
| [Component 1] | Required | Required | Optional | Required | ⬜ |
| [Component 2] | Required | Optional | Required | Optional | ⬜ |

### Verification Checklist

| Category | Requirement | Status |
|----------|-------------|--------|
| Code | All critical gaps addressed | ⬜ |
| Functional | All critical features implemented | ⬜ |
| Arch | All critical violations fixed | ⬜ |
| Testing | Integration testing complete | ⬜ |
| Testing | UAT complete | ⬜ |
| Testing | Performance testing complete | ⬜ |
| Testing | Security testing complete | ⬜ |

---

## 10. Documentation Updates

| Doc Type | Document | Action | Priority |
|----------|----------|--------|----------|
| Code | API documentation | Update | High |
| Code | Architecture diagrams | Update | High |
| Functional | FSD | Update | Medium |
| Functional | User manuals | Update | Low |
| Technical | Deployment guides | Update | High |
| Technical | ADRs | Update | Medium |

---

## 11. Success Criteria

| Metric | Minimum | Target | Current |
|--------|---------|--------|---------|
| Code Coverage | ≥95% | 100% | [X]% |
| Functional Implementation | ≥95% | 100% | [X]% |
| Architectural Compliance | ≥90% | 95% | [X]% |
| Critical Issues | 0 | 0 | [n] |
| High-Risk Items | 0 | 0 | [n] |
| Test Pass Rate | 100% | 100% | [X]% |

---

## 12. Stakeholder Summary

**For Leadership (1 paragraph):** [Concise non-technical summary of status, timeline, and confidence level.]

| Aspect | Status |
|--------|--------|
| Current State | [Brief assessment] |
| What's Working | [Key positives] |
| What Needs Work | [Key gaps] |
| Timeline | [X] weeks |
| Confidence | High/Medium/Low |

---

## 13. Conclusion

[Maximum 2 paragraphs: (1) State of modernization and confidence assessment. (2) Final recommendation and next steps. Do NOT repeat statistics—reference Executive Summary.]

**Final Assessment:** ✅ On Track | ⚠️ Needs Attention | ❌ Critical Issues

---

## Appendices

### A: Report References

| Report | File | Purpose |
|--------|------|---------|
| Code Inventory | `code_base_inventory.md` | Component coverage |
| Functional Gaps | `functional_gaps.md` | Feature completeness |
| Arch Violations | `architectural_violations.md` | Blueprint compliance |

### B: Methodology
[1-2 sentences on analysis approach. Do not elaborate.]

### C: Glossary
[Table format for terms. Maximum 10 most important terms.]

### D: Contacts

| Role | Name | Date |
|------|------|------|
| Project Lead | [Name] | - |
| Technical Architect | [Name] | - |
| Analysis Date | - | [Date] |
```

## Step 3: Display Final Confirmation

Once GAP_report.md has been created, display:

```
✅ GAP ANALYSIS COMPLETE

Reports generated:
1. Code Inventory: [path to code_base_inventory.md]
2. Functional Gaps: [path to functional_gaps.md]  
3. GAP Report: [path to GAP_report.md]

---

## Modernization Health Score: [X]%

**Summary:**
- Code Coverage: [X]%
- Functional Implementation: [X]%
- Architectural Compliance: [X]%

**Critical Issues:** [count]
**High Priority Issues:** [count]
**Estimated Remediation Time:** [X] weeks

---

**Next Steps:**
1. Review the three GAP analysis reports
2. Prioritize remediation based on the priority matrix
3. Schedule kickoff for remediation Phase 1

The GAP analysis provides a complete picture of the modernization status and a clear roadmap for completion.
```

---

## Important Notes

- All three sub-agent analyses (PHASES 1-3) can potentially run in parallel if you have access to all required inputs
- Ensure all file paths are clearly communicated to the user
- If any sub-agent analysis fails or cannot be completed, note this in the final report with explanations
- The synthesis phase should not introduce new analysis—only consolidate and contextualize existing findings
- All reports should be stored in a consistent directory (suggest: `workspace/gap-analysis/`)
- Maintain consistent date format and metadata across all reports

---

## MANDATORY: Pre-Submission Quality Checklist

Before finalizing the GAP report, verify compliance with these QA requirements:

### Deduplication Verification

| Check | Verification Action |
|-------|---------------------|
| ✅ Statistics appear once | Search for percentages—each should appear in ONE section only |
| ✅ Timeline not repeated | Timeline details only in Section 8 (Roadmap) |
| ✅ Budget not repeated | Cost details only in Section 9 (Resources) |
| ✅ Recommendations consolidated | All recommendations only in Conclusion |
| ✅ No repeated critical issues | Issues listed once by severity, cross-referenced elsewhere |

### Table Format Verification

| Check | Verification Action |
|-------|---------------------|
| ✅ Metrics in tables | No metrics buried in paragraphs |
| ✅ Priorities in tables | No priority lists as bullet points |
| ✅ Domain summaries in tables | Single consolidated domain health table |
| ✅ Resources in tables | Team, timeline, budget all in tables |

### Length Verification

| Section | Maximum | Actual |
|---------|---------|--------|
| Executive Summary | 200 words | [ ] |
| Conclusion | 150 words | [ ] |
| Each domain summary | 50 words | [ ] |
| Total narrative (non-table) | 30% of report | [ ] |

**If any check fails, revise before submission.**
