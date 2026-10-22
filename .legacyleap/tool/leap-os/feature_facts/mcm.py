"""Load the MCM and normalize it into screens, methods, data operations, libraries and navigation.

Everything here is read from the MCM. Normalization only reshapes MCM values (parse the
external_dependencies string, lowercase table names, pull columns out of SQL / data_contract text);
it never adds information that is not in the MCM.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import OrderedDict, defaultdict

import profiles

QUALIFIED_RE = re.compile(r"^([a-z0-9_]+)\.([a-z0-9_]+)(?![a-z0-9_.(])")
SQL_HEAD_RE = re.compile(
    r"\b(SELECT\s+(?:DISTINCT\s+)?(?:\*|COUNT\s*\([^)]*\)|[\w.`]+(?:\s*,\s*[\w.`]+)*)\s+FROM\s+[\w.`]+"
    r"|INSERT\s+INTO\s+[\w.`]+|UPDATE\s+[\w.`]+\s+SET\s+[\w`]+\s*=|DELETE\s+FROM\s+[\w.`]+)", re.I)
SQL_TABLE_RE = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+`?([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)?)`?", re.I)
SQL_VERB_RE = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", re.I)  # P1: re.I added so flag matches usage
SQL_KEYWORDS = {"select", "from", "where", "and", "or", "on", "as", "insert", "into", "values", "update", "set",
                "delete", "group", "order", "by", "join", "inner", "left", "right", "limit", "distinct", "count",
                "like", "in", "is", "not", "null", "asc", "desc"}
CONTRACT_STOPWORDS = {"string", "strings", "int", "integer", "varchar", "text", "all", "and", "etc", "none"}
WRITE_OPS = ("INSERT", "UPDATE", "DELETE")

# P1: module-level compiled patterns — prevents re-compilation on every hot-path call
_TABLE_WORD_RE = re.compile(r"\btable\b", re.I)
_TABLE_NAME_RE = re.compile(r"^([a-z0-9_]+)\s+table\b", re.I)
_IDENT_FULL_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BARE_OBJ_RE = re.compile(r"[a-z_][a-z0-9_]*")

# P0: sensitive column pattern — marks columns that must not be surfaced in API responses
SENSITIVE_COLUMN_RE = re.compile(r"pass(?:word)?|pwd|secret|token|api[_-]?key|auth", re.I)


def ident(p, k):
    return (p.get("identity") or {}).get(k) or ""


def cog(p, k):
    return (p.get("cognitive") or {}).get(k)


def boundary(p, k):
    return (p.get("boundary") or {}).get(k)


def metric(p, k):
    return ((p.get("structural") or {}).get("metrics") or {}).get(k) or 0


def qn(p):
    return ident(p, "qualified_name")


def semantic(p):
    sp = cog(p, "semantic_profile") or {}
    return {k: list(sp.get(k) or []) for k in ("inputs", "outputs", "key_operations")}


def dedupe(items):
    seen, out = set(), []
    for it in items:
        if it and it.lower() not in seen:
            seen.add(it.lower())
            out.append(it)
    return out


def snippet(text, start, end, pad=80):
    return re.sub(r"\s+", " ", text[max(0, start - pad): end + pad]).strip()


# ---------------------------------------------------------------- SQL / contract text

def is_sql(text):
    return bool(text) and bool(SQL_HEAD_RE.search(str(text)))


def sql_tables(sql):
    return [m.group(1) for m in SQL_TABLE_RE.finditer(sql or "")]


def _ident_token(tok):
    tok = re.split(r"\s+as\s+", tok.strip().strip("`'\"[]"), flags=re.I)[0].strip().split(".")[-1]
    return tok if _IDENT_FULL_RE.fullmatch(tok) and tok.lower() not in SQL_KEYWORDS else None


def sql_columns(sql):
    if not sql:
        return []
    cols = []
    m = re.search(r"INSERT\s+INTO\s+[\w.`]+\s*\(([^)]*)\)", sql, re.I)
    if m:
        cols += [c for c in map(_ident_token, m.group(1).split(",")) if c]
    m = re.search(r"SELECT\s+(?:DISTINCT\s+)?(.+?)\s+FROM\b", sql, re.I | re.S)
    if m and m.group(1).strip() != "*" and "(" not in m.group(1):
        cols += [c for c in map(_ident_token, m.group(1).split(",")) if c]
    m = re.search(r"\bSET\s+(.+?)(?:\bWHERE\b|$)", sql, re.I | re.S)
    if m:
        cols += [c for c in (_ident_token(x.split("=")[0]) for x in m.group(1).split(",")) if c]
    for m in re.finditer(r"\b(?:WHERE|AND|OR|ON)\s+([\w.`]+)\s*(?:=|<>|!=|<=|>=|<|>|\bLIKE\b|\bIN\b)", sql, re.I):
        c = _ident_token(m.group(1))
        if c:
            cols.append(c)
    return dedupe(cols)


def where_columns(sql):
    m = re.search(r"\bWHERE\b(.*)", sql or "", re.I | re.S)
    if not m:
        return []
    clause = re.sub(r"'[^']*'|\"[^\"]*\"", "?", m.group(1))
    return dedupe([c for c in (_ident_token(x) for x in
                               re.findall(r"([\w.`]+)\s*(?:=|<>|!=|<=|>=|<|>|\bLIKE\b)", clause, re.I)) if c])


def contract_columns(text):
    if not text:
        return []
    text = str(text)
    regions = [m.group(1) for m in re.finditer(
        r"(?:columns?|schema|fields?)\s*(?:include|are)?\s*:\s*(.+?)(?:;|\s[—–-]\s|\.\s|$)", text, re.I)]
    if not regions:
        regions = [m.group(1) for m in re.finditer(r"\(([^()]*,[^()]*)\)", text)]
    cols = []
    for region in regions:
        region = re.sub(r"\(([^(),]*)\)", " ", region).replace("(", " ").replace(")", " ")
        for item in (i.strip() for i in region.split(",")):
            if _IDENT_FULL_RE.fullmatch(item) and item.lower() not in CONTRACT_STOPWORDS:
                cols.append(item)
    return dedupe(cols)


# ---------------------------------------------------------------- model

class MCMError(Exception):
    pass


class MCM:
    def __init__(self, path, profile="auto"):
        self.path = path
        raw_bytes = open(path, "rb").read()
        self.sha256 = hashlib.sha256(raw_bytes).hexdigest()
        try:
            raw = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MCMError(f"MCM is not valid UTF-8 JSON: {exc}")
        nodes = raw.get("nodes") if isinstance(raw, dict) else None
        if not isinstance(nodes, dict) or not nodes.get("parts"):
            raise MCMError("MCM has no nodes.parts; a scan must run first")
        self.parts = [p for p in nodes["parts"] if isinstance(p, dict)]
        try:
            self.profile = profiles.select(self.parts, profile)
        except profiles.ProfileError as exc:
            raise MCMError(str(exc)) from exc
        rels = raw.get("relationships")
        if rels is None:
            rels = (raw.get("edges") or {}).get("relationships") or []
        self.metadata = raw.get("metadata") or {}
        self.by_id = {p.get("id"): p for p in self.parts}
        self.order = {p.get("id"): i for i, p in enumerate(self.parts)}
        self.by_qn = {}
        self.children = defaultdict(list)
        for p in self.parts:
            self.by_qn.setdefault(qn(p), p)
            if p.get("kind") == "Method":
                self.children[p.get("parent_id")].append(p)
        self.out_calls, self.in_calls = defaultdict(list), defaultdict(list)
        for r in rels:
            if isinstance(r, dict) and r.get("type") == "CALLS":
                a, b = r.get("from", r.get("source")), r.get("to", r.get("target"))
                if a in self.by_id and b in self.by_id:
                    self.out_calls[a].append(b)
                    self.in_calls[b].append(a)
        self.parse_errors = []
        self._deps = {}
        self.sql_schemas, self.known_objects = self._known_objects()
        self.unresolved_db_refs = []
        self._build_screens()
        self._build_operations()

    # ---- dependencies

    def deps(self, p):
        pid = p.get("id")
        if pid not in self._deps:
            raw = cog(p, "external_dependencies")
            parsed = raw if isinstance(raw, list) else []
            if isinstance(raw, str) and raw.strip():
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError as exc:
                    self.parse_errors.append({"qualified_name": qn(p), "error": str(exc)})
            if isinstance(parsed, dict):
                parsed = [parsed]
            self._deps[pid] = [(i, d) for i, d in enumerate(parsed if isinstance(parsed, list) else [])
                               if isinstance(d, dict)]
        return self._deps[pid]

    def _known_objects(self):
        schemas, objects = set(), set()
        require_schema = self.profile.get("database.require_schema", True)
        for p in self.parts:
            for _, d in self.deps(p):
                for f in ("method_type", "data_contract", "called_entity"):
                    if is_sql(d.get(f)):
                        for t in sql_tables(str(d.get(f))):
                            if "." in t:
                                schemas.add(t.lower().split(".")[0])
                                objects.add(t.lower())
                            elif not require_schema:
                                objects.add(t.lower())
        for p in self.parts:
            for _, d in self.deps(p):
                if str(d.get("dependency_type")).upper() == "DATABASE":
                    for f in ("called_entity", "endpoint_or_identifier"):
                        value = str(d.get(f) or "").strip().lower().strip("`'\"")
                        m = QUALIFIED_RE.match(value)
                        if m and self._plausible(m.group(1), m.group(2), schemas):
                            objects.add(f"{m.group(1)}.{m.group(2)}")
                        elif not require_schema and _BARE_OBJ_RE.fullmatch(value) \
                                and self._plausible("", value, schemas):
                            objects.add(value)
        return schemas, objects

    def _plausible(self, schema, obj, schemas):
        driver = self.profile.regex("database.driver_regex")
        if driver.search(schema) or driver.search(obj):
            return False
        return schema in schemas if schema and schemas else True

    def _bare(self, name):
        hits = sorted(o for o in self.known_objects if o.split(".")[-1] == name.lower())
        return hits[0] if len(hits) == 1 else None

    def _resolve(self, dep, sql):
        require_schema = self.profile.get("database.require_schema", True)
        for f in ("called_entity", "endpoint_or_identifier"):
            value = str(dep.get(f) or "").strip().lower().strip("`'\"")
            m = QUALIFIED_RE.match(value)
            if m and self._plausible(m.group(1), m.group(2), self.sql_schemas):
                return f"{m.group(1)}.{m.group(2)}"
            if not require_schema and value in self.known_objects:
                return value
        for t in sql_tables(sql or ""):
            t = t.lower()
            if t in self.known_objects:
                return t
            if self._bare(t.split(".")[-1]):
                return self._bare(t.split(".")[-1])
        m = _TABLE_NAME_RE.match(str(dep.get("called_entity") or "").strip().lower())
        return self._bare(m.group(1)) if m else None

    def raw_operations(self, p):
        """DATABASE dependencies of one part, resolved to schema.object, with their source index."""
        out = []
        for i, d in self.deps(p):
            if str(d.get("dependency_type")).upper() != "DATABASE":
                continue
            sql = next((str(d[f]) for f in ("method_type", "data_contract", "called_entity") if is_sql(d.get(f))), None)
            obj = self._resolve(d, sql)
            if obj is None:
                if sql or _TABLE_WORD_RE.search(str(d.get("called_entity") or "")):
                    self.unresolved_db_refs.append({"qualified_name": qn(p), "called_entity": d.get("called_entity"),
                                                    "method_type": d.get("method_type"),
                                                    "source": f"mcm:{qn(p)}#external_dependencies[{i}]"})
                continue
            op = None
            for text in (sql, d.get("method_type"), d.get("called_entity"), d.get("purpose")):
                m = SQL_VERB_RE.search(str(text or ""))
                if m:
                    op = m.group(1).upper()
                    break
            cs, cc = sql_columns(sql), contract_columns(d.get("data_contract"))
            all_cols = dedupe(cs + cc)
            # P0: flag columns that must not be exposed in API responses
            sensitive = [c for c in all_cols if SENSITIVE_COLUMN_RE.search(c)]
            out.append({
                "operation": op, "object": obj, "sql": sql, "columns": all_cols,
                "sensitive_columns": sensitive,
                "columns_from_sql": cs, "where_columns": where_columns(sql),
                "method_type": d.get("method_type"), "data_contract": d.get("data_contract"),
                "purpose": d.get("purpose"), "invocation_point": d.get("invocation_point"),
                "called_entity": d.get("called_entity"), "confidence_score": d.get("confidence_score"),
                "confidence_reason": d.get("confidence_reason"),
                "source": f"mcm:{qn(p)}#external_dependencies[{i}]",
            })
        return out

    def external_api_deps(self, p):
        """Non-DATABASE external dependencies of one part, normalised for EndpointStrategyFactory.

        Returns raw dep dicts enriched with ``dep_type`` and ``source`` so that
        ``HttpApiEndpointStrategy`` (and future custom strategies) can consume them
        without knowing MCM internals.

        Intentionally does NOT attempt SQL parsing or table resolution — that is
        DATABASE-specific work handled by ``raw_operations()`` + ``DatabaseEndpointStrategy``.
        """
        out = []
        for i, d in self.deps(p):
            dtype = str(d.get("dependency_type") or "").upper()
            if dtype == "DATABASE":
                continue   # handled by raw_operations()
            out.append({
                "dep_type":               dtype,
                "called_entity":          d.get("called_entity"),
                "endpoint_or_identifier": d.get("endpoint_or_identifier"),
                "method_type":            d.get("method_type"),
                "purpose":                d.get("purpose"),
                "interaction_direction":  d.get("interaction_direction"),
                "probable_external_owner": d.get("probable_external_owner"),
                "confidence_score":       d.get("confidence_score"),
                "confidence_reason":      d.get("confidence_reason"),
                "source":                 f"mcm:{qn(p)}#external_dependencies[{i}]",
            })
        return out

    def screen_external_apis(self, key):
        """All non-DATABASE external deps for every method in one screen.

        Returns a list of dep dicts (same shape as ``external_api_deps``), each
        enriched with ``screen`` and ``method_qn`` for traceability.  Deduplicates
        by ``(dep_type, endpoint_or_identifier)`` so a dep called from multiple
        handlers in the same screen appears once.
        """
        screen = self.screens.get(key)
        if not screen:
            return []
        seen, out = set(), []
        parts = [screen["primary"], *screen["methods"]]
        for p in parts:
            for dep in self.external_api_deps(p):
                dedup_key = (dep["dep_type"], dep.get("endpoint_or_identifier") or dep.get("called_entity") or "")
                if dedup_key in seen:
                    continue
                seen.add(dedup_key)
                out.append(dict(dep, screen=key, method_qn=qn(p)))
        return out

    def libraries(self, p):
        return [{
            "entity": d.get("called_entity"), "type": d.get("dependency_type"),
            "owner": d.get("probable_external_owner"), "purpose": d.get("purpose"),
            "data_contract": d.get("data_contract"), "invocation_point": d.get("invocation_point"),
            "confidence_score": d.get("confidence_score"), "confidence_reason": d.get("confidence_reason"),
            "source": f"mcm:{qn(p)}#external_dependencies[{i}]",
        } for i, d in self.deps(p) if str(d.get("dependency_type")).upper() not in ("DATABASE",)]

    # ---- screens

    def _is_designer(self, p):
        return self.profile.matches("screen.designer_path_regex", os.path.basename(ident(p, "file_path")))

    def _screen_key(self, p):
        fp = ident(p, "file_path")
        if not fp or fp == "None":
            return ident(p, "name")
        stem = re.sub(r"\.[^.]+$", "", os.path.basename(fp))
        for suffix in self.profile.get("screen.strip_suffixes", []):
            stem = re.sub(re.escape(suffix) + r"$", "", stem, flags=re.I)
        return stem

    def _skip_reason(self, p):
        if p.get("kind") not in set(self.profile.get("screen.kinds", [])):
            return f"kind '{p.get('kind')}' is not a screen kind"
        if str(ident(p, "language")).upper() == "EXTERNAL":
            return "EXTERNAL language"
        if qn(p).startswith(tuple(self.profile.get("screen.framework_prefixes", []))):
            return "framework or third-party type"
        if self.profile.matches("screen.generated_path_regex", ident(p, "file_path")):
            return "generated settings/resources/application container"
        if not self.children.get(p.get("id")) and not (cog(p, "intent") or "").strip():
            return "no methods and no cognitive intent"
        return None

    def _build_screens(self):
        self.skipped, groups, self.part_screen = [], OrderedDict(), {}
        for p in self.parts:
            if p.get("kind") == "Method":
                continue
            reason = self._skip_reason(p)
            if reason:
                self.skipped.append({"qualified_name": qn(p), "kind": p.get("kind"), "reason": reason})
            else:
                groups.setdefault(self._screen_key(p), []).append(p)

        def rank(m):
            has = bool((cog(m, "intent") or "").strip() and (cog(m, "behavior") or "").strip())
            return has, len(self.children.get(m.get("id"), [])), metric(m, "loc"), -self.order[m.get("id")]

        # P2: detect when parts from different top-level namespaces share a screen key
        self.screen_collisions = []
        self.screens = OrderedDict()
        for key, members in groups.items():
            namespaces = sorted({qn(m).split(".")[0] for m in members if qn(m) and "." in qn(m)})
            if len(namespaces) > 1:
                self.screen_collisions.append({
                    "key": key,
                    "namespaces": namespaces,
                    "parts": [qn(m) for m in members],
                    "note": "parts from different namespaces share this screen key; "
                            "highest-ranked part selected as primary — review if grouping is incorrect",
                })
            designers = [m for m in members if self._is_designer(m)]
            primary = max([m for m in members if not self._is_designer(m)] or designers, key=rank)
            designer = max(designers, key=rank) if designers and primary not in designers else None
            self.screens[key] = {"key": key, "primary": primary, "designer": designer,
                                 "extras": [m for m in members if m is not primary and m is not designer],
                                 "methods": [], "designer_methods": []}
            for m in members:
                self.part_screen[m.get("id")] = key

        skipped_ids = {self.by_qn[s["qualified_name"]].get("id") for s in self.skipped if s["qualified_name"] in self.by_qn}
        prefixes = sorted(((qn(m), k) for k, s in self.screens.items() for m in self.screen_parts(k)),
                          key=lambda t: -len(t[0]))
        for p in self.parts:
            if p.get("kind") != "Method":
                continue
            parent = self.by_id.get(p.get("parent_id"))
            while parent is not None and parent.get("kind") == "Method":
                parent = self.by_id.get(parent.get("parent_id"))
            key = self.part_screen.get(parent.get("id")) if parent is not None else None
            if key is None and parent is not None and parent.get("id") in skipped_ids:
                self.skipped.append({"qualified_name": qn(p), "kind": "Method", "reason": f"parent part skipped: {qn(parent)}"})
                continue
            if key is None:
                key, parent = next(((k, self.by_qn.get(q)) for q, k in prefixes if qn(p).startswith(q + ".")), (None, None))
            if key is None:
                self.skipped.append({"qualified_name": qn(p), "kind": "Method", "reason": "method could not attach"})
                continue
            self.part_screen[p.get("id")] = key
            s = self.screens[key]
            (s["designer_methods"] if parent is not None and self._is_designer(parent) else s["methods"]).append(p)

    def screen_parts(self, key):
        s = self.screens[key]
        return [m for m in (s["primary"], s["designer"], *s["extras"]) if m is not None]

    def is_ui(self, key):
        strategy = self.profile.get("screen.ui_strategy", "layer_if_any")
        if strategy == "designer_if_any":
            if not any(s["designer"] is not None for s in self.screens.values()):
                return True
            return self.screens[key]["designer"] is not None

        def evidence(s):
            p = s["primary"]
            return p.get("kind") in self.profile.get("screen.entry_kinds", []) or self.profile.matches(
                "screen.ui_layer_regex", boundary(p, "architecture_layer"))

        return evidence(self.screens[key]) if any(evidence(s) for s in self.screens.values()) else True

    # ---- operations attributed to methods

    def _build_operations(self):
        self.operations = OrderedDict()
        for key, s in self.screens.items():
            by_name = {ident(m, "name"): m for m in s["methods"]}
            pairs = [(m, op) for m in s["methods"] for op in self.raw_operations(m)]
            for part in [s["primary"], *s["extras"]]:
                for op in self.raw_operations(part):
                    via = [by_name[n] for n in by_name
                           if re.search(rf"\b{re.escape(n)}\b", str(op["invocation_point"] or ""))]
                    pairs += [(m, op) for m in via] or [(part, op)]
            merged = []
            for m, op in pairs:
                norm = re.sub(r"\s+", "", op["sql"] or "").lower()
                row = next((r for r in merged if r["method"] == qn(m) and r["object"] == op["object"]
                            and r["operation"] == op["operation"]
                            and (not r["sql"] or not norm or re.sub(r"\s+", "", r["sql"]).lower() == norm)), None)
                if row is None:
                    merged.append({**op, "screen": key, "method": qn(m), "sources": [op["source"]]})
                    continue
                if not row["sql"] and op["sql"]:
                    for k in ("sql", "columns_from_sql", "where_columns", "method_type", "data_contract",
                              "confidence_score", "confidence_reason"):
                        row[k] = op[k]
                row["columns"] = dedupe(row["columns"] + op["columns"])
                if op["source"] not in row["sources"]:
                    row["sources"].append(op["source"])
            for row in merged:
                row.pop("source")
                digest = hashlib.sha1(f"{row['method']}|{row['object']}|{row['operation']}|{row['sql']}".encode()).hexdigest()
                row["id"] = f"op-{digest[:10]}"
                self.operations[row["id"]] = row

    def screen_operations(self, key):
        return [o for o in self.operations.values() if o["screen"] == key]

    def owned(self, key):
        return sorted({o["object"] for o in self.screen_operations(key) if o["operation"] in WRITE_OPS})

    def looked_up(self, key):
        return sorted({o["object"] for o in self.screen_operations(key)} - set(self.owned(key)))

    def contract_gap(self, m):
        described = set(SQL_VERB_RE.findall(cog(m, "behavior") or ""))
        captured = {o["operation"] for o in self.operations.values() if o["method"] == qn(m)}
        return sorted(described - captured)

    # ---- navigation and controls

    def _nav_patterns(self, key):
        names = dedupe([key, re.sub(r"(?<=[a-z])(?=[A-Z])", " ", key)])
        alts = "|".join(re.escape(n) for n in names)
        noun = r"(?i:" + "|".join(map(re.escape, self.profile.get("navigation.nouns", []))) + ")"
        verb = r"(?i:" + self.profile.get("navigation.verbs_regex", r"(?!x)x") + r")\w*"
        direct = "|".join(map(re.escape, self.profile.get("navigation.direct_methods", [])))
        return [re.compile(rf"\b(?:{alts})s?\s+{noun}\b"),
                re.compile(rf"\b{verb}\s+(?i:to\s+)?(?i:the\s+|a\s+|new\s+)?(?:{alts})s?\b"),
                re.compile(rf"\b{re.escape(key)}\s*\.\s*(?:{direct})\b")]

    def navigation(self, key):
        if not hasattr(self, "_nav"):
            self._nav = {}
            pats = {k: self._nav_patterns(k) for k in self.screens if self.is_ui(k)}
            for k, s in self.screens.items():
                edges, seen = [], set()
                for m in s["methods"]:
                    for target_id in self.out_calls.get(m.get("id"), []):
                        t = self.part_screen.get(target_id)
                        if t and t != k and t in pats and (qn(m), t) not in seen:
                            seen.add((qn(m), t))
                            edges.append({"to_screen": t, "via": qn(m), "evidence": "CALLS relationship",
                                          "source": f"mcm:{qn(m)}#relationships.CALLS"})
                    text = f"{cog(m, 'intent') or ''}\n{cog(m, 'behavior') or ''}"
                    for t, rxs in pats.items():
                        if t == k or (qn(m), t) in seen:
                            continue
                        hit = next((h for h in (rx.search(text) for rx in rxs) if h), None)
                        if hit:
                            seen.add((qn(m), t))
                            edges.append({"to_screen": t, "via": qn(m), "evidence": "behavior text",
                                          "quote": snippet(text, hit.start(), hit.end()),
                                          "source": f"mcm:{qn(m)}#cognitive.behavior"})
                self._nav[k] = edges
        return self._nav[key]

    def calls_to_platform(self, key):
        out = []
        for m in self.screens[key]["methods"]:
            for target_id in self.out_calls.get(m.get("id"), []):
                t = self.part_screen.get(target_id)
                if t and t != key and not self.is_ui(t):
                    out.append({"method": qn(m), "calls": qn(self.by_id[target_id]), "screen": t})
        return out

    def event_of(self, m):
        name = ident(m, "name")
        if not self.profile.matches("events.qualified_name_regex", qn(m)):
            return None
        hit = self.profile.regex("events.name_regex").match(name)
        if hit:
            return hit.groupdict().get("control") or name, hit.groupdict().get("event") or name
        return None

    def controls(self, key):
        """Controls named by event handlers or by member access (X.Items, X.Text, ...) in method text."""
        out = OrderedDict()
        for m in self.screens[key]["methods"]:
            ev = self.event_of(m)
            if ev and ev[0] != key:
                c = out.setdefault(ev[0], {"name": ev[0], "events": [], "referenced_by": []})
                c["events"].append({"event": ev[1], "handler": qn(m)})
            sp = semantic(m)
            text = " ".join([cog(m, "behavior") or "", *sp["inputs"], *sp["outputs"], *sp["key_operations"]])
            members = self.profile.get("controls.members", [])
            flags = re.I if self.profile.get("controls.case_insensitive", False) else 0
            member_re = re.compile(
                r"\b([A-Za-z_][A-Za-z0-9_]*)\.(" + "|".join(map(re.escape, members)) + r")\b", flags)
            ignored = {n.lower() for n in self.profile.get("controls.ignore_names", [])}
            for name, member in member_re.findall(text):
                if name.lower() in ignored or name == key:
                    continue
                c = out.setdefault(name, {"name": name, "events": [], "referenced_by": []})
                ref = {"method": qn(m), "member": member}
                if ref not in c["referenced_by"]:
                    c["referenced_by"].append(ref)
        return list(out.values())
