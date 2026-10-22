"""Feature index (pointers only) and per-feature evidence (text resolved from the MCM).

`index` holds ids and qualified names, never MCM text. `evidence` follows those pointers back into
the MCM for one feature. Every value carries a `source` ("mcm:<qualified_name>" or an image path);
nothing here proposes a target design.
"""

from __future__ import annotations

import re

import snapmap
from endpoint_strategies import EndpointStrategyFactory
from mcm import SQL_KEYWORDS, WRITE_OPS, _ident_token, boundary, cog, dedupe, ident, metric, qn, semantic, snippet

SCHEMA_VERSION = "4"
TERM_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)(?:\(\))?`|\(([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)+)\)")
TERM_MAX_PARTS = 8
SECURITY_SIGNALS = {
    "hardcoded_credentials": r"hard-?coded\s+(?:credential|password|connection|user|database|login)"
                             r"|credentials?\s+(?:are\s+)?hard-?coded|embedded\s+(?:credential|password)",
    "plaintext_password": r"plain-?\s?text\s+password|password\w*\s+(?:is\s+|are\s+)?(?:stored|compared|sent|shown)"
                          r"\s+(?:in\s+)?(?:plain|clear)|compar\w+\s+(?:the\s+)?(?:entered\s+|input\s+)?passwords?\b"
                          r"|user\s*name\s+and\s+password[^.]{0,160}\b(?:sql|query)",
    "sql_concatenation": r"concatenat\w*[^.]{0,60}\b(?:sql|query|queries|statement)|(?:sql|query|statement)[^.]{0,60}"
                         r"concatenat\w*|string\s+interpolation|without\s+parameteri[sz]",
    "error_details_exposed": r"exceptions?\b[^.]{0,100}\bmessage\s?box|MsgBox\s*\(\s*ex|\bex\.Message\b",
}
SQL_SIGNALS = {
    "plaintext_password": r"\bpassword\w*\s*=\s*(?:\?|@|:|'|\")",
    "sql_concatenation": r"'\[[\w.]+\]'|\"\s*[&+]\s*\w|\w\s*[&+]\s*\"",
}
TARGET_STACK_GLOBS = ("leap-os/product/tech-stack.md", "leap-os/standards/**/*.md")
SENSITIVE_COLUMN_RE = re.compile(r"pass(?:word)?|pwd|secret|token", re.I)
COUNT_RE = re.compile(r"\bCOUNT\s*\(", re.I)
SELECT_LIST_RE = re.compile(r"SELECT\s+(?:DISTINCT\s+)?(.+?)\s+FROM\b", re.I | re.S)
SET_LIST_RE = re.compile(r"\bSET\s+(.+?)(?:\bWHERE\b|$)", re.I | re.S)
PURPOSE_VERBS = (("SELECT", r"\b(?:retriev|read|fetch|load|get|query|count|select|look\s*up|display|list)"),
                 ("INSERT", r"\b(?:insert|add|sav|creat|register)"),
                 ("UPDATE", r"\b(?:updat|modif|chang|edit)"),
                 ("DELETE", r"\b(?:delet|remov)"))
PURPOSE_FILTER_RE = re.compile(r"\b(?:by|based on|for (?:the )?(?:selected|given))\s+([\w ]{3,40}?)(?:\s+(?:for|to|from|and)\b|[,.;]|$)", re.I)


def _owner_of(features):
    owner = {}
    for f in features:
        for obj in f["owned_objects"]:
            owner.setdefault(obj, []).append(f["id"])
    return owner


def index(mcm, features, broken, snaps, mcm_rel):
    out = []
    for f in features:
        ops = [o for k in f["screens"] for o in mcm.screen_operations(k)]
        out.append({
            "id": f["id"], "name": f["name"], "kind": f["kind"],
            "depends_on": [d["id"] for d in f["depends_on"]],
            "effort": f["effort"]["size"],
            "membership": sorted({m["rule"] for m in f["membership"]}),
            "screens": [{"key": k, "qualified_name": qn(mcm.screens[k]["primary"]),
                         "images": snapmap.images_of(snaps, k)} for k in f["screens"]],
            "owned_objects": f["owned_objects"], "lookup_objects": f["lookup_objects"],
            "operations": [{"id": o["id"], "operation": o["operation"], "object": o["object"], "method": o["method"]}
                           for o in ops],
            "qualified_names": f["qualified_names"],
        })
    for f in out:
        f["used_by"] = [g["id"] for g in out if f["id"] in g["depends_on"]]
    return {
        "schema_version": SCHEMA_VERSION,
        "mcm_path": mcm_rel, "mcm_sha256": mcm.sha256, "profile": mcm.profile.name,
        "snapshot_folder": snaps["snapshot_folder"],
        "counts": {"screens": len(mcm.screens), "data_objects": len({o["object"] for o in mcm.operations.values()}),
                   "data_operations": len(mcm.operations), "features": len(out),
                   "images": len(snaps["images"]), "images_unmatched": len(snapmap.unmatched(snaps))},
        "features": out,
        "broken_dependency_cycles": broken,
    }


def _method(mcm, m, key, role):
    ev = mcm.event_of(m)
    return {
        "name": ident(m, "name"), "screen": key, "role": role,
        "event": {"control": ev[0], "event": ev[1]} if ev else None,
        "intent": cog(m, "intent"), "behavior": cog(m, "behavior"), "semantic_profile": semantic(m),
        "calls": [qn(mcm.by_id[i]) for i in mcm.out_calls.get(m.get("id"), [])],
        "called_by": [qn(mcm.by_id[i]) for i in mcm.in_calls.get(m.get("id"), [])],
        "data_operations": [o["id"] for o in mcm.operations.values() if o["method"] == qn(m)],
        "source": f"mcm:{qn(m)}",
    }


def _screens(mcm, f, snaps):
    screens = []
    for key in f["screens"]:
        s = mcm.screens[key]
        p, d = s["primary"], s["designer"]
        screens.append({
            "key": key, "qualified_name": qn(p), "kind": p.get("kind"),
            "security_zone": boundary(p, "security_zone"),
            "intent": cog(p, "intent"), "behavior": cog(p, "behavior"), "semantic_profile": semantic(p),
            "source": f"mcm:{qn(p)}",
            "designer": None if d is None else {"qualified_name": qn(d), "legacy_controls": mcm.libraries(d),
                                                "source": f"mcm:{qn(d)}"},
            "controls": mcm.controls(key),
            "event_handlers": [{"handler": qn(m), "control": mcm.event_of(m)[0], "event": mcm.event_of(m)[1]}
                               for m in s["methods"] if mcm.event_of(m)],
            "navigation": mcm.navigation(key),
            "images": snapmap.images_of(snaps, key),
        })
    return screens


def _backend(mcm, f, owner_of):
    ops = [o for k in f["screens"] for o in mcm.screen_operations(k)]
    objects = []
    for name in sorted({o["object"] for o in ops}):
        every = [o for o in mcm.operations.values() if o["object"] == name]
        objects.append({
            "object": name, "role": "owned" if name in f["owned_objects"] else "lookup",
            "owner_features": owner_of.get(name, []),
            "columns": dedupe([c for o in every for c in o["columns"]]),
            "written_by_screens": sorted({o["screen"] for o in every if o["operation"] in WRITE_OPS}),
            "read_by_screens": sorted({o["screen"] for o in every if o["operation"] not in WRITE_OPS}),
        })
    methods = [m for k in f["screens"] for m in mcm.screens[k]["methods"]]
    screen_qns = {qn(p) for k in f["screens"] for p in mcm.screen_parts(k)} | {qn(m) for m in methods}
    return {
        "data_objects": objects,
        "operations": ops,
        "external_dependencies": [dict(lib, used_by=qn(part)) for k in f["screens"]
                                  for part in [mcm.screens[k]["primary"], *mcm.screens[k]["methods"]]
                                  for lib in mcm.libraries(part)],
        "multi_write_methods": [{"method": qn(m), "operation_ids": ids} for m in methods
                                for ids in [[o["id"] for o in ops if o["method"] == qn(m) and o["operation"] in WRITE_OPS]]
                                if len(ids) >= 2],
        "open_items": {
            "data_contract_gaps": [{"method": qn(m), "sql_verbs_in_behavior_without_contract": mcm.contract_gap(m)}
                                   for m in methods if mcm.contract_gap(m)],
            "low_confidence_operations": [{"operation_id": o["id"], "confidence_score": o["confidence_score"],
                                           "confidence_reason": o["confidence_reason"]}
                                          for o in ops if isinstance(o["confidence_score"], (int, float))
                                          and o["confidence_score"] < 0.7],
            "unresolved_database_refs": [r for r in mcm.unresolved_db_refs if r["qualified_name"] in screen_qns],
            "objects_without_columns": [o["object"] for o in objects if not o["columns"]],
        },
    }


def _own_parts(mcm, f):
    return [(k, p) for k in f["screens"]
            for p in [*mcm.screen_parts(k), *mcm.screens[k]["methods"], *mcm.screens[k]["designer_methods"]]]


def _member(features):
    return {k: g["id"] for g in features for k in g["screens"]}


def _cross_feature(mcm, f, features):
    """CALLS edges between this feature's parts and other features' parts, grouped by feature."""
    member, mine = _member(features), set(f["screens"])
    groups = {"used_by": {}, "uses": {}}
    for _, p in _own_parts(mcm, f):
        for direction, edges in (("used_by", mcm.in_calls), ("uses", mcm.out_calls)):
            for other in edges.get(p.get("id"), []):
                s = mcm.part_screen.get(other)
                if not s or s in mine or s not in member:
                    continue
                g = groups[direction].setdefault(member[s], {"feature": member[s], "screens": set(), "calls": []})
                g["screens"].add(s)
                a, b = (qn(mcm.by_id[other]), qn(p)) if direction == "used_by" else (qn(p), qn(mcm.by_id[other]))
                g["calls"].append({"caller": a, "callee": b, "source": f"mcm:{a}#relationships.CALLS"})
    return {d: [dict(g, screens=sorted(g["screens"]), call_count=len(g["calls"]))
                for _, g in sorted(groups[d].items())] for d in groups}


def _terms(mcm, f):
    """Names this feature exposes: its screen keys, plus identifiers its behavior text quotes in
    backticks or in parenthesized lists (fields such as stuid), minus its own method names."""
    method_names = {ident(p, "name").lower() for _, p in _own_parts(mcm, f)}
    terms = set(f["screens"])
    for _, p in _own_parts(mcm, f):
        for a, b in TERM_RE.findall(cog(p, "behavior") or ""):
            for t in ([a] if a else [x.strip() for x in b.split(",")]):
                if len(t) >= 4 and t.lower() not in method_names and t.lower() not in SQL_KEYWORDS \
                        and not (t[0].isupper() and t[1:].islower()):
                    terms.add(t)
    return sorted(terms)


def _mentions(mcm, f, features):
    """Behavior or intent text of other features' parts that names one of this feature's terms."""
    member, mine = _member(features), set(f["screens"])
    others = [(p, mcm.part_screen.get(p.get("id"))) for p in mcm.parts]
    others = [(p, s) for p, s in others if s and s not in mine and s in member]
    navigates = {s for s in member if s not in mine and mine & {e["to_screen"] for e in mcm.navigation(s)}}
    out = []
    for term in _terms(mcm, f):
        if term in member and term not in mine:
            continue
        rx = re.compile(rf"\b{re.escape(term)}\b")
        hits = []
        for p, s in others:
            if term in mine and s in navigates:
                continue
            text = f"{cog(p, 'intent') or ''}\n{cog(p, 'behavior') or ''}"
            m = rx.search(text)
            if m:
                hits.append({"term": term, "by": qn(p), "screen": s, "feature": member[s],
                             "quote": snippet(text, m.start(), m.end()), "source": f"mcm:{qn(p)}#cognitive"})
        if len(hits) <= TERM_MAX_PARTS:
            out += hits
    return out


def _security(mcm, f):
    signals = mcm.profile.get("security.signals", SECURITY_SIGNALS)
    out, seen = [], set()
    for k, p in _own_parts(mcm, f):
        sp = semantic(p)
        texts = [cog(p, "intent"), cog(p, "behavior"), *sp["inputs"], *sp["outputs"], *sp["key_operations"]]
        texts += [d.get(x) for _, d in mcm.deps(p) for x in ("purpose", "data_contract", "method_type")]
        text = "\n".join(str(t) for t in texts if t)
        for name, pattern in signals.items():
            m = re.search(pattern, text, re.I)
            if m and (name, qn(p)) not in seen:
                seen.add((name, qn(p)))
                out.append({"signal": name, "screen": k, "qualified_name": qn(p),
                            "quote": snippet(text, m.start(), m.end()), "source": f"mcm:{qn(p)}"})
    sql_signals = mcm.profile.get("security.sql_signals", SQL_SIGNALS)
    for k in f["screens"]:
        for o in mcm.screen_operations(k):
            for name, pattern in sql_signals.items():
                m = re.search(pattern, o["sql"] or "", re.I)
                if m and (name, o["id"]) not in seen:
                    seen.add((name, o["id"]))
                    out.append({"signal": name, "screen": k, "qualified_name": o["method"],
                                "quote": snippet(o["sql"], m.start(), m.end()), "source": o["id"]})
    return out


def _idents(text):
    return [t for t in (_ident_token(x) for x in text.split(",")) if t]


def _triggers(mcm, method_qn):
    """The UI event that runs a method: the method itself when it is an event handler, else the
    event handlers that call it."""
    m = mcm.by_qn.get(method_qn)
    if m is None:
        return []
    ev = mcm.event_of(m)
    if ev:
        return [{"control": ev[0], "event": ev[1], "handler": method_qn}]
    out = []
    for cid in mcm.in_calls.get(m.get("id"), []):
        e = mcm.event_of(mcm.by_id[cid])
        if e:
            out.append({"control": e[0], "event": e[1], "handler": qn(mcm.by_id[cid])})
    return out


def _endpoint(o, columns_of):
    """Thin delegator — REST shape for one DATABASE operation.

    Delegates all logic to ``DatabaseEndpointStrategy`` via the factory so that
    facts.py no longer hard-codes SQL parsing rules.  Return contract is unchanged:
    ``(verb, path, shape, gaps, notes, op_label)``.
    """
    strategy = EndpointStrategyFactory.get("DATABASE")
    return strategy.derive(o, {"columns_of": columns_of})


def _merge_ep(eps, verb, path, shape, gaps, notes, op, legacy_entry):
    """Upsert one endpoint into the ``eps`` accumulator dict.

    Handles both DB-pass and HTTP-API-pass entries with identical merge semantics.
    ``legacy_entry`` is appended to ``eps[(verb,path)]["legacy"]`` if present.
    """
    e = eps.setdefault(
        (verb, path),
        {
            "method": verb, "path": path,
            "object": legacy_entry.get("object", ""),
            "operation": op,
            "purpose": legacy_entry.get("purpose", ""),
            **{key: [] for key in shape},
            "gaps": [], "notes": [], "legacy": [],
        },
    )
    for key, values in shape.items():
        e[key] = dedupe(e[key] + values)
    e["gaps"]  = dedupe(e["gaps"]  + gaps)
    e["notes"] = dedupe(e["notes"] + notes)
    if legacy_entry:
        e["legacy"].append(legacy_entry)


def _apis(mcm, f, objects):
    """Candidate backend endpoints, one per distinct (verb, path), mapped back to legacy screens.

    Pass 1 — DATABASE deps (current behaviour, unchanged):
        ``mcm.screen_operations()`` → ``DatabaseEndpointStrategy`` via ``_endpoint()``.

    Pass 2 — non-DATABASE deps (new, generic):
        ``mcm.screen_external_apis()`` → ``EndpointStrategyFactory.get(dep_type).derive()``.
        For this desktop project every API dep is a WinForms Show() call which
        ``HttpApiEndpointStrategy`` correctly returns None for, so Pass 2 produces
        zero entries and output is identical to pre-refactor.
    """
    columns_of = {o["object"]: o["columns"] for o in objects}
    eps = {}

    # ---- Pass 1: DATABASE -------------------------------------------------------
    for k in f["screens"]:
        for o in mcm.screen_operations(k):
            verb, path, shape, gaps, notes, op = _endpoint(o, columns_of)
            legacy = {
                "screen": k, "method": o["method"],
                "triggers": _triggers(mcm, o["method"]),
                "operation_id": o["id"], "sql": o["sql"],
                "purpose": o["purpose"],
                "source": f"mcm:{o['method']}",
                "object": o["object"],
            }
            _merge_ep(eps, verb, path, shape, gaps, notes, op, legacy)

    # ---- Pass 2: non-DATABASE (API / CLOUD_SERVICE / THIRD_PARTY / …) ----------
    for k in f["screens"]:
        for dep in mcm.screen_external_apis(k):
            strategy = EndpointStrategyFactory.get(dep["dep_type"])
            result = strategy.derive(dep, {"columns_of": columns_of})
            if result is None:
                continue  # e.g. WinForms Show() or out-of-scope external service
            verb, path, shape, gaps, notes, op_label = result
            legacy = {
                "screen": k, "method": dep.get("method_qn", ""),
                "triggers": [],
                "operation_id": dep.get("source", ""),
                "sql": None,
                "purpose": dep.get("purpose", ""),
                "source": dep.get("source", ""),
                "object": dep.get("endpoint_or_identifier") or dep.get("called_entity") or "",
            }
            _merge_ep(eps, verb, path, shape, gaps, notes, op_label, legacy)

    # ---- post-processing (unchanged) -------------------------------------------
    for (verb, path), e in list(eps.items()):
        keyed = [x for (v, p), x in eps.items() if v == verb and p.startswith(path + "/{") and p.count("/") == path.count("/") + 1]
        if verb in ("PUT", "DELETE") and not e["path_params"] and not e["query_params"] and len(keyed) == 1:
            keyed[0]["legacy"] += e["legacy"]
            keyed[0]["request_body"] = dedupe(keyed[0]["request_body"] + e["request_body"])
            keyed[0]["notes"] = dedupe(keyed[0]["notes"] + [f"{len(e['legacy'])} operation(s) without a WHERE column "
                                                            "in the MCM merged here by verb and table"])
            del eps[(verb, path)]
    for (verb, path), e in eps.items():
        keyed = [x for (v, p), x in eps.items() if v == verb and p.startswith(path + "/{")]
        if keyed and any("filter column is unknown" in g for g in e["gaps"]):
            e["gaps"] = [g + f" (the MCM filters this table by {', '.join(x['path_params'][0] for x in keyed)} elsewhere)"
                         if "filter column is unknown" in g else g for g in e["gaps"]]
    out = sorted(eps.values(), key=lambda e: (e["path"], ["GET", "POST", "PUT", "DELETE"].index(e["method"])))
    for i, e in enumerate(out, 1):
        e["id"] = f"api-{i}"
        e["operation_ids"] = dedupe([x["operation_id"] for x in e["legacy"]])
    return out


def _target_stack(root):
    if root is None:
        return []
    return sorted({str(p.relative_to(root)) for g in TARGET_STACK_GLOBS for p in root.glob(g) if p.is_file()})


def evidence(mcm, f, features, snaps, mcm_rel, root=None):
    methods = {qn(m): _method(mcm, m, k, "behavior") for k in f["screens"] for m in mcm.screens[k]["methods"]}
    methods.update({qn(p): _method(mcm, p, k, "behavior") for k in f["screens"] for p in mcm.screens[k]["extras"]
                    if (cog(p, "behavior") or "").strip()})
    methods.update({qn(m): _method(mcm, m, k, "designer") for k in f["screens"]
                    for m in mcm.screens[k]["designer_methods"]})
    by_id = {g["id"]: g for g in features}
    screens = _screens(mcm, f, snaps)
    backend = _backend(mcm, f, _owner_of(features))
    backend["apis"] = _apis(mcm, f, backend["data_objects"])
    images = [img for s in screens for img in s["images"]]
    return {
        "schema_version": SCHEMA_VERSION,
        "feature_id": f["id"], "name": f["name"], "kind": f["kind"], "intent": f["intent"],
        "effort": f["effort"], "membership": f["membership"],
        "mcm_path": mcm_rel, "mcm_sha256": mcm.sha256, "profile": mcm.profile.name,
        "depends_on": [{"id": d["id"], "name": by_id[d["id"]]["name"], "reason": d["reason"]} for d in f["depends_on"]],
        "used_by": [{"id": g["id"], "name": g["name"]} for g in features
                    if f["id"] in [d["id"] for d in g["depends_on"]]],
        "images": images,
        "image_map": {img: snaps["images"][img] for img in images},
        "screens": screens,
        "methods": dict(sorted(methods.items(), key=lambda kv: mcm.order[mcm.by_qn[kv[0]].get("id")])),
        "backend": backend,
        "cross_feature": _cross_feature(mcm, f, features),
        "mentions": _mentions(mcm, f, features),
        "security_signals": _security(mcm, f),
        "target_stack": {"files": _target_stack(root),
                         "use": "target choices for _(derived)_ rows only; cite as stack:<file>"},
        "qualified_names": f["qualified_names"],
    }
