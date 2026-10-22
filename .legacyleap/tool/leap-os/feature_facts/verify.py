"""Mechanical checks for one feature spec (GitHub Spec Kit format) against its evidence.json.

Fails when the spec misses its feature id or a required section, leaves TODO placeholders,
has malformed tables, has an incomplete Approval block, has generated blocks that are
missing or differ from a fresh render, or is missing Gherkin scenarios / FR rows.
Semantic review belongs to the reviewer agent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import scaffold

# Required top-level sections (case-insensitive match against ## headings)
# GitHub Spec Kit mandatory sections for this project:
SECTIONS = (
    "Summary",
    "User Scenarios",
    "Functional Requirements",
    "Success Criteria",
    "UI Modernization",
    "Backend Modernization",
    "API Contracts",
    "Visual References",
    "E2E Test Coverage",
    "Out of Scope",
    "Approval",
)

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
TODO_RE = re.compile(r"\bTODO\b")
SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")

# GitHub Spec Kit ID patterns
FR_RE = re.compile(r"^\|\s*FR-\d{3,}", re.M)
SC_RE = re.compile(r"^\|\s*SC-\d{3,}", re.M)
US_HEADING_RE = re.compile(r"^###\s+US-\d+", re.M)
GHERKIN_RE = re.compile(r"```gherkin", re.M)
E2E_RE = re.compile(r"^\|\s*E2E-\d{3,}", re.M)
UI_MOD_HEADING_RE = re.compile(r"^###\s+\S+", re.M)  # at least one ### sub-section


def _norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def paths(root: Path, specs_dir: str, feature_id: str):
    d = root / specs_dir / feature_id
    return {
        "dir": d,
        "evidence": d / "evidence.json",
        "spec": d / f"{feature_id}.md",
        "openapi": d / f"{feature_id}.openapi.json",
    }


def sections(text):
    marks = [(m.start(), m.group(1).strip()) for m in HEADING_RE.finditer(text)]
    by_name = {}
    for i, (pos, name) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        by_name[name.lower()] = text[pos:stop]   # last occurrence wins; duplicates reported by run()
    return by_name, [name for _, name in marks]


def _unfenced(text):
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        yield fenced, line


def _cells(row):
    return scaffold.cells(row)


def table_shapes(text):
    """Problems per table: a header without a separator row, or rows whose cell count differs from the header."""
    problems, lines = [], list(enumerate(_unfenced(text), 1))
    i = 0
    while i < len(lines):
        n, (fenced, line) = lines[i]
        if fenced or not line.lstrip().startswith("|"):
            i += 1
            continue
        blk = []
        while i < len(lines) and not lines[i][1][0] and lines[i][1][1].lstrip().startswith("|"):
            blk.append((lines[i][0], lines[i][1][1]))
            i += 1
        head = len(_cells(blk[0][1]))
        if len(blk) < 2 or not SEPARATOR_RE.match(blk[1][1].strip()):
            problems.append(f"line {blk[0][0]}: table header has no |---| separator row under it")
            continue
        for ln, row in blk[1:]:
            if len(_cells(row)) != head:
                kind = "separator" if SEPARATOR_RE.match(row.strip()) else "row"
                problems.append(f"line {ln}: {kind} has {len(_cells(row))} cells, "
                                 f"header '{blk[0][1][:50]}' has {head}")
    return problems


def tables(text):
    """(header cells, data rows) for every top-level markdown table."""
    lines = [line for fenced, line in _unfenced(text) if not fenced]
    out, header = [], None
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            header = None
            continue
        if SEPARATOR_RE.match(line):
            continue
        if i + 1 < len(lines) and SEPARATOR_RE.match(lines[i + 1]):
            header = [c.lower() for c in _cells(line)]
            out.append((header, []))
            continue
        if out and header is not None:
            out[-1][1].append(line)
    return out


def approval(section):
    fields = {}
    for header, rows in tables(section):
        for row in rows:
            cs = _cells(row)
            if len(cs) >= 2:
                fields[cs[0].lower()] = cs[1].strip("` ")
    return fields


def run(root: Path, specs_dir: str, feature_id: str):
    """Validate a GitHub Spec Kit spec against its evidence.json.

    Checks performed (in order):
    - evidence.json and spec file exist
    - Title line contains feature id
    - No duplicate ## headings
    - All required sections present:
        Summary, User Scenarios, Functional Requirements, Success Criteria,
        UI Modernization, Backend Modernization, API Contracts, Visual References,
        E2E Test Coverage, Out of Scope, Approval
    - Approval is the last section
    - No TODO placeholders left
    - All markdown tables are well-formed (table_shape)
    - All 3 generated blocks (apis, contracts, snapshots) are present and match evidence
    - ## Summary has at least one non-empty, non-TODO line
    - ## User Scenarios has at least one ### US-NN heading and one ```gherkin block
    - ## Functional Requirements has at least one FR-NNN row
    - ## Success Criteria has at least one SC-NNN row
    - ## UI Modernization has at least one ### sub-section (per MCM screen)
    - ## Backend Modernization has at least one filled-in line
    - ## E2E Test Coverage has at least one E2E-NNN row
    - Approval status is 'scaffolded', 'draft', or 'approved'; approved needs reviewer/date/sha256
    - No broken relative links
    """
    p = paths(root, specs_dir, feature_id)
    errors = []

    def err(check, detail):
        errors.append({"check": check, "detail": detail})

    def rel(path):
        return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)

    if not p["evidence"].is_file():
        return {"ok": False, "feature_id": feature_id,
                "errors": [{"check": "evidence_exists",
                             "detail": f"{rel(p['evidence'])} not found; run `evidence` first"}]}
    ev = json.loads(p["evidence"].read_text(encoding="utf-8"))
    if not p["spec"].is_file():
        return {"ok": False, "feature_id": feature_id, "spec": rel(p["spec"]),
                "errors": [{"check": "spec_exists", "detail": f"{p['spec'].name} not found"}]}

    text = p["spec"].read_text(encoding="utf-8")
    by_name, order = sections(text)

    # ---- feature id in title
    title = next((line for line in text.splitlines() if line.startswith("# ")), "")
    if feature_id not in title:
        err("feature_id", f"title line must contain {feature_id!r}")

    # ---- duplicate headings
    _seen: set = set()
    for name in order:
        key = name.lower()
        if key in _seen:
            err("duplicate_section", f"'## {name}' appears more than once; remove the duplicate heading")
        _seen.add(key)

    # ---- required sections present
    for name in SECTIONS:
        if name.lower() not in by_name:
            err("section_missing", name)

    # ---- Approval is last
    if order and order[-1].lower() != "approval":
        err("approval_last", "## Approval must be the last section")

    # ---- no TODO placeholders
    for m in TODO_RE.finditer(text):
        err("todo_left", _norm(text[max(0, m.start() - 60): m.end() + 60]))

    # ---- table shape
    for problem in table_shapes(text):
        err("table_shape",
            problem + "; separator rows are repaired by `scaffold --sync`, "
            "other rows need the header's column count (escape a literal | as \\|)")

    # ---- generated blocks present and up to date (apis, contracts, snapshots)
    for name in scaffold.GENERATORS:
        found = scaffold.extract(text, name)
        if found is None:
            err("generated_missing", f"{name} block is missing; run `scaffold --sync`")
        elif _norm(found) != _norm(scaffold.block(name, ev)):
            err("generated_changed",
                f"{name} block differs from the MCM and snapshots; "
                "run `scaffold --sync` and put additions outside the markers")

    # ---- Summary has substance (at least one non-empty, non-TODO line)
    summary_body = by_name.get("summary", "")
    summary_lines = [l.strip() for l in summary_body.splitlines()
                     if l.strip() and not l.startswith("#") and "TODO" not in l
                     and not l.startswith(">") and not l.startswith("**Actors")]
    if not summary_lines:
        err("summary_empty",
            "## Summary must contain at least one non-TODO sentence describing the feature")

    # ---- User Scenarios: must have at least one ### US-NN heading and one ```gherkin block
    scenarios_body = by_name.get("user scenarios", "")
    if not US_HEADING_RE.search(scenarios_body):
        err("scenario_missing",
            "## User Scenarios must contain at least one '### US-NN: …' heading")
    if not GHERKIN_RE.search(scenarios_body):
        err("gherkin_missing",
            "## User Scenarios must contain at least one ```gherkin code block "
            "with Given/When/Then steps")

    # ---- Functional Requirements: at least one FR-NNN row
    fr_body = by_name.get("functional requirements", "")
    if not FR_RE.search(fr_body):
        err("fr_empty",
            "## Functional Requirements must have at least one row with ID 'FR-NNN'")

    # ---- Success Criteria: at least one SC-NNN row
    sc_body = by_name.get("success criteria", "")
    if not SC_RE.search(sc_body):
        err("sc_empty",
            "## Success Criteria must have at least one row with ID 'SC-NNN'")

    # ---- UI Modernization: at least one ### sub-section (one per screen)
    ui_body = by_name.get("ui modernization", "")
    if not UI_MOD_HEADING_RE.search(ui_body):
        err("ui_modernization_empty",
            "## UI Modernization must have at least one '### ScreenKey → <Component />' sub-section")

    # ---- Backend Modernization: section must have at least one non-heading, non-blockquote line
    # (bullets with TODOs are acceptable at scaffold stage; todo_left catches unfilled content)
    be_body = by_name.get("backend modernization", "")
    be_lines = [l.strip() for l in be_body.splitlines()
                if l.strip() and not l.startswith("#") and not l.startswith(">")]
    if not be_lines:
        err("backend_modernization_empty",
            "## Backend Modernization must contain at least one line of content "
            "(security remediation bullet, API response note, or data migration note)")

    # ---- E2E Test Coverage: at least one E2E-NNN row
    e2e_body = by_name.get("e2e test coverage", "")
    if not E2E_RE.search(e2e_body):
        err("e2e_empty",
            "## E2E Test Coverage must have at least one row with ID 'E2E-NNN'")

    # ---- Approval status
    appr = approval(by_name.get("approval", ""))
    status = appr.get("status", "").lower()
    if status not in ("draft", "approved", "scaffolded"):
        err("approval", "Approval table needs a Status row of 'scaffolded', 'draft', or 'approved'")
    if status == "approved":
        for field in ("reviewer", "date", "mcm sha256"):
            if not appr.get(field):
                err("approval", f"approved spec needs a '{field}' row")
        if appr.get("mcm sha256") and appr["mcm sha256"] != ev["mcm_sha256"]:
            err("approval",
                "MCM sha256 in Approval does not match evidence.json "
                "(the MCM changed; re-run evidence and update the spec)")

    # ---- broken relative links
    for link in LINK_RE.findall(text):
        if re.match(r"^[a-z]+:", link) or link.startswith("#"):
            continue
        if not (p["spec"].parent / link.split("#")[0]).resolve().exists():
            err("broken_link", link)

    images = set(ev["images"])
    ops = {o["id"]: o for o in ev["backend"]["operations"]}

    # ---- soft warnings (do not affect ok / exit code)
    warnings = []
    if not p["openapi"].is_file():
        warnings.append({
            "check": "openapi_missing",
            "detail": (
                f"{p['openapi'].name} not found. "
                "Run `scaffold --force` or `openapi --feature` to generate it."
            ),
        })

    return {
        "ok": not errors,
        "feature_id": feature_id,
        "spec": rel(p["spec"]),
        "status": status or None,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "operations": len(ops),
            "images": len(images),
            "sections": len(order),
        },
    }
