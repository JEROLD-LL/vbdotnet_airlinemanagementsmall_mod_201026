"""Canonical API contract model — single source of truth for both
scaffold.py (markdown contracts) and openapi.py (OpenAPI 3.0.3 JSON).

Every function here is a pure function of evidence.json.
No LLM, no invention: same input → same output, every time.

Public API
----------
contracts(ev)            → list[dict]   one contract dict per api in evidence
sql_column_types(ev)     → dict         {col_name: json_schema_type}
classify_response(api)   → str          one of the RESP_* constants
contract(api, col_types) → dict         canonical contract for one api entry

Response kind constants (RESP_*)
---------------------------------
RESP_AUTH        /authenticate path  → 200 + 401 + 422
RESP_COUNT       response==["count"] → {count: integer}
RESP_OBJECT      known columns, single-item result
RESP_LIST        known columns, parameter-free GET (collection)
RESP_CREATED     POST with no MCM response columns → 201 no body
RESP_NO_CONTENT  DELETE or unknown method → 204 no body
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ---------------------------------------------------------------- response kind constants

RESP_AUTH        = "auth"
RESP_COUNT       = "count"
RESP_OBJECT      = "object"
RESP_LIST        = "list"
RESP_CREATED     = "created"
RESP_NO_CONTENT  = "no_content"

# ---------------------------------------------------------------- SQL type inference

# Columns produced by aggregate functions are numeric.
_AGG_RE = re.compile(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', re.IGNORECASE)


def sql_column_types(ev: dict) -> dict[str, str]:
    """Return {column_name: json_schema_type} derived from MCM SQL statements.

    Rules (deterministic, MCM-only):
    - Column returned by an aggregate query (COUNT/SUM/AVG/MIN/MAX) → "integer"
    - All others → "string"  (safest default when the MCM does not state the type)
    - First-seen wins when a column appears in both aggregate and non-aggregate ops.

    Edge cases handled:
    - op["sql"] is None or "" → skipped
    - op["columns"] is None or [] → skipped
    - Empty column name strings → skipped
    """
    types: dict[str, str] = {}
    for op in (ev.get("backend") or {}).get("operations") or []:
        sql  = op.get("sql") or ""
        cols = [c for c in (op.get("columns") or []) if c]  # drop empty names
        if not cols:
            continue
        t = "integer" if _AGG_RE.search(sql) else "string"
        for c in cols:
            if c not in types:      # first-seen wins
                types[c] = t
    return types


# ---------------------------------------------------------------- response classification

def classify_response(api: dict) -> str:
    """Return the RESP_* constant that best describes this api's response shape.

    Logic is purely rule-based over MCM fields — no inference or invention.
    """
    if (api.get("path") or "").endswith("/authenticate"):
        return RESP_AUTH

    resp = api.get("response") or []
    if resp == ["count"]:
        return RESP_COUNT

    if resp:
        is_list = (
            api.get("method") == "GET"
            and not (api.get("path_params") or [])
            and not (api.get("query_params") or [])
        )
        return RESP_LIST if is_list else RESP_OBJECT

    # No response columns in the MCM
    return RESP_CREATED if api.get("method") == "POST" else RESP_NO_CONTENT


# ---------------------------------------------------------------- canonical contract

def contract(api: dict, col_types: dict[str, str] | None = None) -> dict:
    """Canonical contract for one api entry. Pure function, no side-effects.

    Parameters
    ----------
    api       : one entry from ev["backend"]["apis"]
    col_types : optional {col: json_schema_type} from sql_column_types();
                defaults to all-"string" when absent or a column is not listed.

    Returns a flat dict consumed by both scaffold.py and openapi.py.
    No formatting or serialisation decisions are made here.
    """
    ct     = col_types or {}
    method = api.get("method") or "GET"
    resp   = api.get("response") or []

    def _t(col: str) -> str:
        """Resolve column type, defaulting to string."""
        return ct.get(col, "string")

    resp_kind = classify_response(api)

    # ---- request body (only meaningful for mutating methods)
    body_cols = api.get("request_body") or []
    has_body  = bool(body_cols and method in ("POST", "PUT", "PATCH"))
    body_props: dict[str, str] = {c: _t(c) for c in body_cols if c} if has_body else {}

    # ---- response shape
    if resp_kind == RESP_COUNT:
        resp_props: dict | list | None = {"count": "integer"}
    elif resp_kind == RESP_OBJECT:
        inner = {c: _t(c) for c in resp if c}
        resp_props = inner if inner else None
    elif resp_kind == RESP_LIST:
        inner = {c: _t(c) for c in resp if c}
        # list marker: a one-element list-of-dict so callers know it's a collection
        resp_props = [inner] if inner else None
    else:
        resp_props = None   # auth / created / no_content — no schema

    # ---- HTTP status codes (deterministic rule table, never invented)
    if resp_kind == RESP_AUTH:
        status_codes = ["200", "401", "422"]
    elif method == "GET":
        status_codes = ["200", "404"]
    elif method == "POST":
        status_codes = ["201", "422"]
    elif method in ("PUT", "PATCH"):
        status_codes = ["200", "404", "422"]
    elif method == "DELETE":
        status_codes = ["204", "404"]
    else:
        status_codes = ["200"]

    # ---- traceability (verbatim MCM values, never invented)
    legacy = api.get("legacy") or []
    legacy_refs    = list(dict.fromkeys(x["source"]  for x in legacy if x.get("source")))
    legacy_methods = list(dict.fromkeys(x["method"]  for x in legacy if x.get("method")))
    screens        = list(dict.fromkeys(x["screen"]  for x in legacy if x.get("screen")))
    # screen → purpose mapping (for OpenAPI tags)
    screen_tags: dict[str, str] = {}
    for x in legacy:
        scr = x.get("screen") or ""
        if scr and scr not in screen_tags:
            screen_tags[scr] = x.get("purpose") or scr

    return {
        # ---- identity
        "id":      api.get("id") or "",
        "method":  method,
        "path":    api.get("path") or "",
        "purpose": api.get("purpose") or "",
        # ---- parameters
        "path_params":  api.get("path_params") or [],
        "query_params": api.get("query_params") or [],
        # ---- request body
        "has_body":   has_body,
        "body_props": body_props,       # {col: json_type} or {} if no body
        # ---- response
        "resp_kind":    resp_kind,      # one of the RESP_* constants
        "resp_props":   resp_props,     # None | {col:type} | [{col:type}]
        "status_codes": status_codes,
        "is_auth":      resp_kind == RESP_AUTH,
        # ---- traceability (all verbatim from MCM, never invented)
        "operation_ids":  api.get("operation_ids") or [],
        "notes":          api.get("notes") or [],
        "gaps":           api.get("gaps") or [],
        "legacy_refs":    legacy_refs,      # ["mcm:..."] source strings
        "legacy_methods": legacy_methods,   # MCM qualified names
        "screens":        screens,          # screen names (for tags)
        "screen_tags":    screen_tags,      # {screen: purpose} for OpenAPI tags
    }


def contracts(ev: dict) -> list[dict]:
    """Canonical contract list for every api in evidence.json.

    Always call this rather than calling contract() directly so that
    sql_column_types() is computed once and shared across all endpoints.

    Returns [] (not raises) when evidence has no apis — callers guard with `if not cs`.
    """
    col_types = sql_column_types(ev)
    return [
        contract(a, col_types)
        for a in (ev.get("backend") or {}).get("apis") or []
    ]


# ---------------------------------------------------------------- profile-driven OpenAPI config

_PROFILES_DIR = Path(__file__).parent / "profiles"

# Hard-coded defaults used when the profile has no openapi section.
# These are the generic REST API conventions that apply to any modern project.
_OPENAPI_DEFAULTS: dict = {
    "server": {
        "default_url": "http://localhost:8000",
        "description": "Replace {baseUrl} with the deployed service root URL.",
        "url_template": "{baseUrl}/api",
        "base_url_variable_description": "Service base URL (scheme + host + optional port).",
    },
    "security": {
        "scheme_name": "BearerAuth",
        "type": "http",
        "scheme": "bearer",
        "format": "JWT",
        "description": (
            "Token obtained from the authentication endpoint. "
            "Required on all non-authentication endpoints."
        ),
    },
    "recommendations": {
        "password_hash": "a secure one-way hash (e.g. bcrypt cost \u2265 12 or Argon2id)",
        "auth_response_example": "token, role, error body",
    },
}


def profile_openapi_cfg(ev: dict) -> dict:
    """Return the openapi config section for the profile that generated this evidence.

    Resolution order:
    1. Profile named in ev["profile"]  (e.g. "dotnet-winforms")
    2. "generic-mcm"  (always-present fallback)
    3. _OPENAPI_DEFAULTS  (in-code hard-coded last resort)

    The returned dict is deep-merged: profile values override defaults key-by-key
    within each nested section, so a profile only needs to specify what differs
    from the generic defaults.  Callers use nested .get() — never assume a key exists.
    """
    profile_name = ev.get("profile") or "generic-mcm"
    raw: dict = {}

    for name in dict.fromkeys([profile_name, "generic-mcm"]):  # unique, order-preserving
        p = _PROFILES_DIR / f"{name}.json"
        if p.is_file():
            try:
                raw = json.loads(p.read_text(encoding="utf-8")).get("openapi") or {}
                if raw:
                    break
            except (OSError, json.JSONDecodeError, ValueError):
                continue

    # Deep-merge: default wins only where profile is silent
    merged: dict = {}
    for section, defaults in _OPENAPI_DEFAULTS.items():
        profile_section = raw.get(section) or {}
        merged[section] = {**defaults, **profile_section}  # profile overrides default

    return merged
