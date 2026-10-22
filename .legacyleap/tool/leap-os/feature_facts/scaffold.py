"""Spec skeleton for one feature, built from its evidence.json, and the tool-owned blocks inside it.

`build` writes every heading and table of the spec template. Everything that needs judgement is a
TODO row, and `check` fails while any TODO is left. Three parts are generated from the MCM and the
snapshot map only, between `<!-- generated:NAME:start -->` / `<!-- generated:NAME:end -->` markers:

  snapshots   embedded screenshots per screen with mapping rationale   (## Visual References)
  apis        endpoint table derived from MCM data operations          (### Endpoints)
  contracts   request/response bodies per endpoint from SQL columns    (### Contracts)

`check` fails when a block is missing or differs from a fresh render; `sync` rewrites them in place.

Output format: GitHub Spec Kit
  Sections: Summary · User Scenarios · Functional Requirements · Success Criteria ·
            Non-Functional Requirements · API Contracts · Data Model ·
            Visual References · Out of Scope · Open Questions · Approval
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

TODO = "TODO"
SIGNAL_TEXT = {
    "hardcoded_credentials": "Hard-coded database credentials",
    "plaintext_password": "Password compared or stored in plain text",
    "sql_concatenation": "SQL built from UI values without parameters",
    "error_details_exposed": "Exception details shown to the user",
}
HOW_TEXT = {"name": "matched by file name", "words": "matched by file-name words", "manual": "mapped after looking"}
OWNERS = {"snapshots": r"^##\s+Visual References\b.*$", "apis": r"^###\s+Endpoints\b.*$",
          "contracts": r"^###\s+Contracts\b.*$"}


SEPARATOR_RE = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")


def cells(row):
    """Cells of a markdown table row; an escaped \\| stays inside its cell."""
    s = row.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def repair_separators(text):
    """Rewrite each table's separator row to the header's column count; returns (text, rows repaired)."""
    lines, fenced, fixed = text.split("\n"), False, 0
    for i in range(1, len(lines)):
        if lines[i - 1].lstrip().startswith("```"):
            fenced = not fenced
        if fenced or not SEPARATOR_RE.match(lines[i]) or not lines[i - 1].lstrip().startswith("|") \
                or SEPARATOR_RE.match(lines[i - 1]):
            continue
        want = "|" + "---|" * len(cells(lines[i - 1]))
        if len(cells(lines[i])) != len(cells(lines[i - 1])):
            lines[i], fixed = want, fixed + 1
    return "\n".join(lines), fixed


def _cell(v):
    return str(v).replace("|", "\\|").replace("\n", " ")


def _row(*cells):
    return "| " + " | ".join(_cell(c) for c in cells) + " |"


def _table(headers, rows=None):
    out = [_row(*headers), "|" + "---|" * len(headers)]
    out += [_row(*r) for r in (rows or [[TODO] * len(headers)])]
    return out


def _ids(items):
    return ", ".join(f"`{i}`" for i in items) or "none"


def _link(img):
    target = f"../../../{img}"
    return f"<{target}>" if " " in target else target


def _trigger_text(legacy):
    seen, out = set(), []
    for x in legacy:
        for t in x["triggers"] or [None]:
            label = f"{x['screen']} · `{t['control']}.{t['event']}`" if t else f"{x['screen']} · no UI event in the MCM"
            if label not in seen:
                seen.add(label)
                out.append(label)
    return "<br>".join(out)


# ---------------------------------------------------------------- generated blocks

def gen_snapshots(ev):
    out = []
    for s in ev["screens"]:
        out += [f"#### {s['key']}", ""]
        if not s["images"]:
            out += [f"No snapshot of this screen (`mcm:{s['qualified_name']}`).", ""]
        for img in s["images"]:
            m = (ev.get("image_map") or {}).get(img) or {}
            how = HOW_TEXT.get(m.get("how"), m.get("how") or "mapped")
            note = f" ({m['note']})" if m.get("note") else ""
            out += [f"![{s['key']}: {PurePosixPath(img).name}]({_link(img)})", "",
                    f"`snapshot:{img}` · screen `{s['key']}` (`mcm:{s['qualified_name']}`) · {how}{note}", ""]
    return out


def gen_apis(ev):
    apis = ev["backend"].get("apis", [])
    head = ["API", "Method", "Path", "Purpose (MCM)", "Legacy screen · trigger", "Legacy method (qualified name)",
            "Replaces operation(s)"]
    if not apis:
        return _table(head, [["none", "", "", "no data operations in the MCM", "", "",
                              f"mcm:{ev['screens'][0]['qualified_name']}" if ev["screens"] else ""]]) + [""]
    rows = [[a["id"], a["method"], f"`{a['path']}`", a["purpose"] or "", _trigger_text(a["legacy"]),
             "<br>".join(dict.fromkeys(f"`mcm:{x['method']}`" for x in a["legacy"])),
             ", ".join(a["operation_ids"])] for a in apis]
    return _table(head, rows) + ["", "_(derived)_ One endpoint per distinct verb and path over the MCM data operations: "
                                     "the table name gives the resource, the SQL verb the HTTP method, a single WHERE "
                                     "column the path parameter, the column lists the fields.", ""]


def _json(obj):
    return ["```json", json.dumps(obj, indent=2), "```"]


def gen_contracts(ev):
    """Render the Contracts generated block as markdown lines.

    All derivation logic lives in api_contract.py — this function only formats.
    """
    import api_contract as _ac  # noqa: PLC0415 — deferred so module loads fast
    cs = _ac.contracts(ev)
    if not cs:
        return ["No endpoints: this feature has no data operations in the MCM.", ""]
    out = []
    for c in cs:
        legacy_md = ", ".join(f"`mcm:{m}`" for m in c["legacy_methods"])
        out += [f"#### {c['id']} · `{c['method']} {c['path']}`", "",
                f"Replaces {', '.join(c['operation_ids']) or 'none'} · legacy {legacy_md or 'none'}", ""]
        params = ([f"path `{p}`" for p in c["path_params"]]
                  + [f"query `{q}`" for q in c["query_params"]])
        out += [f"Parameters: {', '.join(params) or 'none'}", ""]
        if c["has_body"]:
            out += ["Request body:"] + _json({k: f"<{k}>" for k in c["body_props"]}) + [""]
        rk = c["resp_kind"]
        if rk == _ac.RESP_COUNT:
            out += ["Response `200`:"] + _json({"count": "<integer>"}) + [""]
        elif rk == _ac.RESP_OBJECT and c["resp_props"]:
            out += ["Response `200`:"] + _json({k: f"<{k}>" for k in c["resp_props"]}) + [""]
        elif rk == _ac.RESP_LIST and c["resp_props"]:
            out += ["Response `200`:"] + _json([{k: f"<{k}>" for k in c["resp_props"][0]}]) + [""]
        elif rk == _ac.RESP_AUTH:
            out += ["Response: `200` when a row matches the submitted values (the legacy query selects the "
                    "matching row), `401` otherwise; the MCM names no other returned field.", ""]
        elif rk == _ac.RESP_CREATED:
            out += ["Response: `201`, no body in the MCM.", ""]
        else:  # RESP_NO_CONTENT or unknown
            out += ["Response: `204`, no body in the MCM.", ""]
        out += [f"Note: {n}." for n in c["notes"]] + [f"Gap: {g}; see Open questions." for g in c["gaps"]]
        out += [""] if c["notes"] or c["gaps"] else []
    return out


def gen_evidence(ev):
    out = ["### 9.1 Screen behavior (verbatim)", ""]
    for s in ev["screens"]:
        out += [f"**{s['key']}** (`mcm:{s['qualified_name']}`)", "", s["behavior"] or "No behavior text in the MCM.", ""]
    out += ["### 9.2 Method behavior (verbatim)", ""]
    for q, m in ev["methods"].items():
        if m["role"] == "behavior" and m["behavior"]:
            out += [f"**{m['name']}** (`mcm:{q}`)", "", m["behavior"], ""]
    out += ["### 9.3 Data operations (verbatim SQL)", ""]
    for o in ev["backend"]["operations"]:
        sensitive = o.get("sensitive_columns", [])
        sensitive_note = f" · ⚠ sensitive column(s): {', '.join(sensitive)}" if sensitive else ""
        out += [f"**{o['id']}** · {o['operation'] or '?'} `{o['object']}` · columns: {', '.join(o['columns']) or 'none'}"
                f"{sensitive_note} · method `mcm:{o['method']}`", ""]
        out += ["```sql", o["sql"], "```", ""] if o["sql"] else ["No SQL in the MCM.", ""]
    if not ev["backend"]["operations"]:
        out += ["No data operations for this feature.", ""]
    return out


GENERATORS = {"snapshots": gen_snapshots, "apis": gen_apis, "contracts": gen_contracts}

# P1: process-lifetime cache — block() is called 4× per check run with the same evidence;
# keyed by (name, mcm_sha256, feature_id) so it is safe across multiple features in one run.
_block_cache: dict = {}


def start(name):
    return f"<!-- generated:{name}:start (tool output from the MCM and snapshots; refresh with scaffold --sync, do not edit) -->"


def end(name):
    return f"<!-- generated:{name}:end -->"


def block(name, ev):
    cache_key = (name, ev.get("mcm_sha256", ""), ev.get("feature_id", ""))
    if cache_key not in _block_cache:
        _block_cache[cache_key] = "\n".join([start(name), ""] + GENERATORS[name](ev) + [end(name)])
    return _block_cache[cache_key]


def extract(text, name):
    m = re.search(re.escape(start(name)) + r"(.*?)" + re.escape(end(name)), text, re.S)
    return m.group(0) if m else None


def sync(text, ev):
    """Replace the body of each tool-owned heading with a fresh block and repair table separator rows;
    returns (text, missing headings, separator rows repaired)."""
    missing = []
    text, fixed = repair_separators(text)
    for name, heading in OWNERS.items():
        m = re.search(heading, text, re.M)
        if not m:
            missing.append(name)
            continue
        level = m.group(0).split()[0]
        nxt = re.compile(r"^#{1,%d}\s" % len(level), re.M).search(text, m.end())
        stop = nxt.start() if nxt else len(text)
        text = text[:m.end()] + "\n" + block(name, ev) + "\n\n" + text[stop:].lstrip("\n")
    return text, missing, fixed


# ---------------------------------------------------------------- skeleton

def build(ev, specs_dir="leap-os/specs/features"):
    """Build a GitHub Spec Kit skeleton from evidence.

    Section order:
    Summary · User Scenarios · Functional Requirements · Success Criteria ·
    Non-Functional Requirements · UI Modernization · Backend Modernization ·
    API Contracts · Data Model · Visual References · E2E Test Coverage ·
    Out of Scope · Open Questions · Approval.

    Generated blocks (apis, contracts, snapshots) are embedded inside the
    relevant sections so `scaffold --sync` can refresh them in place.
    Every narrative cell is a TODO; `check` fails while any TODO remains.

    Anti-hallucination guarantees — ALL pre-seeded content traces to evidence.json only:
    - FR rows: one per API endpoint (backend.apis) + one per unique security signal.
    - SC rows: 1:1 with FR count.
    - UI Modernization sub-sections: one per MCM screen; input fields from
      controls[] where events==[]; actions from controls[] where events!=[].
    - Backend Modernization: security signals → remediation stubs;
      APIs → modern response shape stubs.
    - E2E Test Coverage rows: one per MCM event handler control; API-backed
      triggers auto-marked @priority-p0, others @priority-p1 or @priority-p2.
    - Data Model rows: from backend.data_objects only.
    - No requirement is invented that is not traceable to the MCM or snapshots.
    """
    fid = ev["feature_id"]
    L: list[str] = []
    add = L.extend
    apis = ev["backend"].get("apis", [])
    screens_list = ev["screens"]
    sigs = ev.get("security_signals", [])
    objs = ev["backend"]["data_objects"]
    items = ev["backend"]["open_items"]
    cross = ev.get("cross_feature") or {"used_by": [], "uses": []}

    # Pre-compute unique security signals (MCM can repeat same screen+signal)
    _sig_seen: set[tuple] = set()
    unique_sigs: list[dict] = []
    for sig in sigs:
        key = (sig["screen"], sig["signal"])
        if key not in _sig_seen:
            _sig_seen.add(key)
            unique_sigs.append(sig)

    # Pre-compute the set of (screen, control, event) that directly trigger an API.
    # Used to assign @priority-p0 to E2E scenarios for those event handlers.
    api_triggers: set[tuple] = set()
    for api in apis:
        for x in api.get("legacy", []):
            for t in (x.get("triggers") or []):
                if t and t.get("control"):
                    api_triggers.add((x["screen"], t["control"], t["event"]))

    # ---- header (feature_id must appear in the title line so `check` can verify it)
    add([f"# Feature Specification: {ev['name']} ({fid})", "",
         f"> **Format:** GitHub Spec Kit · "
         f"**Feature ID:** `{fid}` · **Kind:** {ev['kind']} · **Effort:** `{ev['effort']['size']}`",
         f"> **Depends on:** {_ids(d['id'] for d in ev['depends_on'])} · "
         f"**Used by:** {_ids(u['id'] for u in ev['used_by'])}",
         f"> **Evidence:** `{specs_dir}/{fid}/evidence.json` · "
         f"MCM sha256 `{ev['mcm_sha256'][:12]}` · "
         f"{len(ev['images'])} snapshot(s) · {len(apis)} API(s)",
         "", "---", ""])

    # ---- Summary
    add(["## Summary", ""])
    if ev.get("intent"):
        add([ev["intent"], ""])
    add([f"{TODO}: Add any additional context about this feature's purpose and business value.", ""])
    # Actors from MCM screen keys
    actors = list(dict.fromkeys(
        s.get("actor") or s["key"]
        for s in screens_list
        if s.get("actor") or s.get("key")
    ))
    if actors:
        add(["**Actors:**"])
        for actor in actors:
            add([f"- **{actor}** — {TODO}: describe the actor's role and goal"])
        add([""])

    # ---- User Scenarios
    # One Gherkin stub per MCM screen so every flow surface is represented;
    # the agent replaces each TODO with real Given/When/Then from the event handlers.
    add(["## User Scenarios", ""])
    for i, s in enumerate(screens_list, 1):
        us_id = f"US-{i:02d}"
        add([f"### {us_id}: {TODO}: scenario title for {s['key']}", "",
             "```gherkin",
             f"Given {TODO}: precondition on {s['key']}",
             f"When  {TODO}: user action",
             f"Then  {TODO}: expected outcome",
             "```", ""])

    # ---- Functional Requirements
    # Seeded from MCM evidence only — one row per API endpoint,
    # then one per unique (screen, signal) security pair.
    # The agent may add more rows, but must not invent endpoints.
    add(["## Functional Requirements", ""])
    fr_rows: list[list[str]] = []
    fr_num = 1

    for api in apis:
        screen_names = ", ".join(dict.fromkeys(x["screen"] for x in api["legacy"]))
        fr_rows.append([f"FR-{fr_num:03d}",
                        f"{TODO}: describe the requirement for `{api['method']} {api['path']}`",
                        "Must Have",
                        screen_names or TODO])
        fr_num += 1

    # Security signal FR rows (pre-computed unique_sigs, MCM-derived only)
    import api_contract as _ac  # noqa: PLC0415 — deferred so module loads fast
    _oa_cfg = _ac.profile_openapi_cfg(ev)
    _pw_hash = _oa_cfg.get("recommendations", {}).get("password_hash",
                           "a secure one-way hash (e.g. bcrypt cost ≥ 12 or Argon2id)")
    for sig in unique_sigs:
        label = SIGNAL_TEXT.get(sig["signal"], sig["signal"])
        fr_rows.append([f"FR-{fr_num:03d}",
                        f"{label} in `{sig['screen']}` MUST be remediated — "
                        f"{TODO}: describe the specific fix (e.g. hash with "
                        f"parameterised queries, {_pw_hash})",
                        "Must Have",
                        sig["screen"]])
        fr_num += 1

    # Fallback: if no APIs and no signals, seed one stub per screen
    if fr_num == 1:
        for s in screens_list:
            fr_rows.append([f"FR-{fr_num:03d}",
                            f"{TODO}: main functional requirement for {s['key']}",
                            "Must Have",
                            s["key"]])
            fr_num += 1

    add(_table(["ID", "Requirement", "Priority", "Screen(s)"], fr_rows))
    add([""])

    # ---- Success Criteria
    # One SC row per pre-seeded FR so each requirement has a measurable test.
    add(["## Success Criteria", ""])
    sc_rows = [[f"SC-{i:03d}",
                f"{TODO}: criterion covering FR-{i:03d}",
                f"{TODO}: measurable acceptance test"]
               for i in range(1, fr_num)]
    add(_table(["ID", "Criterion", "Measurement / Acceptance Test"], sc_rows))
    add([""])

    # ---- Non-Functional Requirements
    add(["## Non-Functional Requirements", ""])
    nfr_rows = [[f"NFR-001", f"{TODO}: performance, security, or reliability requirement",
                 f"{TODO}: target metric"]]
    if unique_sigs:
        nfr_rows.append([f"NFR-002",
                         f"All passwords MUST be stored using {_pw_hash} — "
                         f"{TODO}: confirm algorithm with tech lead",
                         "Zero plain-text passwords in DB"])
    add(_table(["ID", "Requirement", "Target"], nfr_rows))
    add([""])

    # ---- UI Modernization
    # One sub-section per MCM screen.
    # Input fields = controls with no events but referenced by handlers (MCM-derived).
    # Action controls = controls that have events (MCM-derived).
    # Agent must set labels from the snapshot; must not invent controls not in the MCM.
    add(["## UI Modernization", ""])
    add(["> _Map each legacy screen to its modern component. "
         "Use only control names from the MCM and label text visible in the snapshots. "
         "Do not invent field names or actions not present in the MCM controls list._", ""])
    for s in screens_list:
        comp = f"<{s['key']}Page />"
        add([f"### {s['key']} → `{comp}`", ""])
        add([f"- **Route:** `{TODO}: e.g. /feature/{s['key'].lower()}`",
             f"- **Component file:** `{TODO}: src/pages/.../{s['key']}Page.tsx`"])

        # Input fields: controls with no events but referenced by event handlers
        input_ctrls = [c for c in s.get("controls", [])
                       if not c.get("events") and c.get("referenced_by")]
        if input_ctrls:
            add(["- **Input fields** (MCM control names — set label text from snapshot):"])
            for c in input_ctrls:
                add([f"  - `{c['name']}` — {TODO}: label text from snapshot · input type"])

        # Action controls: controls that have events
        action_ctrls = [c for c in s.get("controls", []) if c.get("events")]
        if action_ctrls:
            add(["- **Actions** (MCM event handlers):"])
            for c in action_ctrls:
                ev_labels = ", ".join(f"`{e['event']}`" for e in c["events"])
                add([f"  - `{c['name']}` ({ev_labels}) — {TODO}: modern handler description"])

        # States from semantic_profile outputs (MCM-derived)
        outputs = (s.get("semantic_profile") or {}).get("outputs", [])
        if outputs:
            add(["- **UI States:**"])
            for o in outputs[:5]:
                add([f"  - {TODO}: {o[:90].rstrip()}"])

        add([""])

    # ---- Backend Modernization
    # Pre-seeded from MCM APIs and security signals only.
    # Agent fills in the modern implementation details; must not invent endpoints.
    add(["## Backend Modernization", ""])
    add(["> _Implementation notes beyond the generated API Contracts. "
         "Source of truth: MCM security signals and data operations. "
         "Follow `leap-os/standards/backend/api.md` and `leap-os/standards/global/tech-stack.md`._", ""])

    if unique_sigs:
        add(["### Security Remediation", ""])
        add(["> _Each item below maps to a security signal in the MCM. "
             "Agent must describe the concrete fix without inventing additional signals._", ""])
        for sig in unique_sigs:
            label = SIGNAL_TEXT.get(sig["signal"], sig["signal"])
            add([f"- **{label}** (`{sig['screen']}`): {TODO}: migration plan — e.g. add "
                 f"`password_hash` column (VARCHAR 60), hash on first login, drop `password` "
                 f"column after full migration."])
        add([""])

    if apis:
        _auth_example = _oa_cfg.get("recommendations", {}).get("auth_response_example", "token, role, error body")
        add(["### Modern API Response Shape", ""])
        add([f"> _The generated contracts show legacy request/response shapes. "
             f"Define the full modern response ({_auth_example}) here._", ""])
        for api in apis:
            screen_names = ", ".join(dict.fromkeys(x["screen"] for x in api["legacy"]))
            add([f"- `{api['method']} {api['path']}` (from `{screen_names}`): "
                 f"{TODO}: modern response body — e.g. `{{ \"token\": \"<jwt>\", \"role\": \"<role>\" }}`"])
        add([""])

    if objs and unique_sigs:
        add(["### Data Migration", ""])
        add(["> _One migration note per data object that has a related security signal. "
             "Follow `leap-os/standards/backend/migrations.md` for file naming._", ""])
        for o in objs:
            add([f"- `{o['object']}`: {TODO}: column changes required — "
                 f"e.g. rename `password` → `password_hash`, update type to VARCHAR(60)."])
        add([""])

    # Fallback: feature has no security signals, APIs or data objects that need migration.
    # Always emit at least one stub so the section is non-empty and todo_left fires.
    if not unique_sigs and not apis and not objs:
        add([f"- {TODO}: Describe any backend implementation notes for this feature "
             "(e.g. platform configuration, connection settings, environment variables)."])
        add([""])

    # ---- API Contracts  (generated blocks — do not edit inside markers)
    add(["## API Contracts", ""])
    fid = ev["feature_id"]
    add([f"> Machine-readable: [{fid}.openapi.json](./{fid}.openapi.json)", ""])
    add(["### Endpoints", ""])
    add([block("apis", ev), ""])
    add(["### Contracts", ""])
    add([block("contracts", ev), ""])

    # ---- Data Model  (pre-populated from MCM; agent adds column notes)
    add(["## Data Model", ""])
    if objs:
        dm_rows = []
        for o in objs:
            # Show first 6 columns; truncate with … if more
            col_list = o["columns"] or []
            cols_str = ", ".join(col_list[:6]) + ("…" if len(col_list) > 6 else "")
            dm_rows.append([f"`{o['object']}`", o["role"], f"`{cols_str}`" if cols_str else TODO])
        add(_table(["Table", "Role", "Key Columns Used"], dm_rows))
    else:
        add(_table(["Table", "Role", "Key Columns Used"],
                   [[TODO, TODO, TODO]]))
    add([""])

    # ---- Visual References  (generated block — always present even for no-image features)
    add(["## Visual References", ""])
    add([block("snapshots", ev), ""])
    if ev["images"]:
        add([f"{TODO}: For each snapshot above describe the UI elements to reproduce in the "
             "modern UI: window title, field labels, button text, layout, and any visible state "
             "(loading indicator, masked password, error message).", ""])

    # ---- E2E Test Coverage
    # Rows are seeded one-per-MCM-event-handler so every testable trigger is listed.
    # API-backed triggers → @priority-p0; toggle/state handlers → @priority-p2;
    # everything else → @priority-p1. Agent sets scenario titles and adjusts priority.
    # The .feature file is generated by /frontend-gherkin-test-generator from this spec.
    add(["## E2E Test Coverage", ""])
    feature_file = f"{specs_dir}/{fid}/{fid}.feature"
    add([f"**Feature file:** `{feature_file}`",
         "_Generate with `/frontend-gherkin-test-generator` from this spec; "
         "execute with `/frontend-playwright-gherkin-tester`._", ""])

    e2e_rows: list[list[str]] = []
    e2e_num = 1
    # State-change events (toggles, checked, selection) get p2; all others p1 by default
    STATE_EVENTS = {"checkedchanged", "selectedindexchanged", "valuechanged", "toggled"}
    for s in screens_list:
        for c in s.get("controls", []):
            for evt in c.get("events", []):
                event_name = evt.get("event", "")
                is_api = (s["key"], c["name"], event_name) in api_triggers
                if is_api:
                    # API trigger: add success path (p0) + invalid input path (p0)
                    e2e_rows.append([f"E2E-{e2e_num:03d}", s["key"],
                                     f"`{c['name']}.{event_name}` — success path",
                                     "@priority-p0 @positive",
                                     f"{TODO}: scenario title"])
                    e2e_num += 1
                    e2e_rows.append([f"E2E-{e2e_num:03d}", s["key"],
                                     f"`{c['name']}.{event_name}` — invalid / empty input",
                                     "@priority-p0 @negative",
                                     f"{TODO}: scenario title"])
                    e2e_num += 1
                elif event_name.lower() in STATE_EVENTS:
                    # Toggle / state handler
                    e2e_rows.append([f"E2E-{e2e_num:03d}", s["key"],
                                     f"`{c['name']}.{event_name}`",
                                     "@priority-p2 @positive",
                                     f"{TODO}: scenario title"])
                    e2e_num += 1
                else:
                    # Other click / navigation handlers
                    e2e_rows.append([f"E2E-{e2e_num:03d}", s["key"],
                                     f"`{c['name']}.{event_name}`",
                                     "@priority-p1 @positive",
                                     f"{TODO}: scenario title"])
                    e2e_num += 1

    if not e2e_rows:
        e2e_rows = [[f"E2E-001", TODO, f"{TODO}: trigger", "@priority-p0 @positive",
                     f"{TODO}: scenario title"]]
    add(_table(["ID", "Screen", "MCM Trigger", "Tags", "Scenario Title"], e2e_rows))
    add([""])

    # ---- Out of Scope
    add(["## Out of Scope", ""])
    oos_items: list[str] = []
    for o in items.get("low_confidence_operations", []):
        oos_items.append(f"`{o['operation_id']}` — low confidence "
                         f"({o['confidence_reason'] or 'see evidence'}); "
                         "confirm or exclude before implementing.")
    for r in items.get("unresolved_database_refs", []):
        oos_items.append(f"`{r['called_entity']}` database reference is unresolved — "
                         "clarify which table it targets before implementing.")
    for obj in items.get("objects_without_columns", []):
        oos_items.append(f"`{obj}` — column list unknown; confirm schema before implementing.")
    if oos_items:
        for item in oos_items:
            add([f"- {item}"])
    else:
        add([f"- {TODO}: List features, edge cases, or behaviours explicitly excluded from this spec."])
    add([""])

    # ---- Open Questions
    add(["## Open Questions", ""])
    add(_table(["#", "Question", "Owner", "Status"],
               [["OQ-01", f"{TODO}: key open question about this feature", TODO, "Open"]]))
    add([""])

    # ---- Approval
    add(["## Approval"] + _table(["Field", "Value"], [["Status", "scaffolded"]]))
    return "\n".join(L) + "\n"
