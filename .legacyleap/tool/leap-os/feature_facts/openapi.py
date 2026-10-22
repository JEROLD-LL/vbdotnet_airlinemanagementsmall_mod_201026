"""Convert evidence.json → OpenAPI 3.0.3 document for one feature.

Source of truth: ev["backend"]["apis"], consumed via api_contract.contracts(ev).
All response-kind classification, status-code rules, and type inference live in
api_contract.py — this module is responsible only for OpenAPI JSON formatting.

Nothing here invents endpoints, schemas, or status codes not present in the
evidence or derivable from it by deterministic rules.
"""

from __future__ import annotations

import re
from typing import Any

import api_contract as _ac


# ---------------------------------------------------------------- schema helpers

def _props_to_schema(props: dict[str, str]) -> dict:
    """Convert {col: json_schema_type} → a JSON Schema 'object' node."""
    if not props:
        return {"type": "object"}
    return {
        "type": "object",
        "properties": {col: {"type": t} for col, t in props.items()},
    }


def _response_content_schema(c: dict) -> dict | None:
    """JSON Schema node for the success response body, or None when there is no body."""
    rk = c["resp_kind"]
    if rk == _ac.RESP_COUNT:
        return {"type": "object", "properties": {"count": {"type": "integer"}}}
    if rk == _ac.RESP_OBJECT:
        rp = c["resp_props"]
        return _props_to_schema(rp) if rp else None
    if rk == _ac.RESP_LIST:
        rp = c["resp_props"]
        if not rp:
            return None
        return {"type": "array", "items": _props_to_schema(rp[0])}
    return None   # auth / created / no_content — no body schema


# ---------------------------------------------------------------- operation builder

def _build_responses(c: dict) -> dict[str, Any]:
    """Build the OpenAPI 'responses' map from the canonical contract dict."""
    rk     = c["resp_kind"]
    method = c["method"]
    schema = _response_content_schema(c)

    def _body(desc: str) -> dict:
        if schema:
            return {"description": desc, "content": {"application/json": {"schema": schema}}}
        return {"description": desc}

    if rk == _ac.RESP_AUTH:
        return {
            "200": {"description": "Credentials matched."},
            "401": {"description": "Credentials did not match or user not found."},
            "422": {"description": "Missing or malformed request fields."},
        }
    if method == "GET":
        return {
            "200": _body("Success."),
            "404": {"description": "Resource not found."},
        }
    if method == "POST":
        return {
            "201": _body("Resource created."),
            "422": {"description": "Validation error."},
        }
    if method in ("PUT", "PATCH"):
        return {
            "200": _body("Resource updated."),
            "404": {"description": "Resource not found."},
            "422": {"description": "Validation error."},
        }
    if method == "DELETE":
        return {
            "204": {"description": "Resource deleted."},
            "404": {"description": "Resource not found."},
        }
    return {"200": {"description": "Success."}}


def _operation_id(c: dict) -> str:
    """Build operationId as camelCaseSummary[QualifiedName].

    Format matches the MCM convention:
      camelCaseSummary[Namespace.Form.Form.Method.N.ArgType.ArgType]
    Falls back to c["id"] when no legacy method is captured.
    """
    qname = next(iter(c.get("legacy_methods") or []), None)
    if not qname:
        return c["id"]
    summary = c.get("purpose") or f"{c['method']} {c['path']}"
    words = re.sub(r"[^a-zA-Z0-9]+", " ", summary).split()
    if not words:
        return f"{c['id']}[{qname}]"
    camel = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    return f"{camel}[{qname}]"


def _build_operation(c: dict, needs_security: bool, sec_cfg: dict | None = None) -> dict[str, Any]:
    """Build one OpenAPI operation object from a canonical contract dict.

    sec_cfg: the profile's openapi.security section (from api_contract.profile_openapi_cfg).
             Used to name the security scheme; defaults to BearerAuth when absent.
    """
    op: dict[str, Any] = {
        "operationId": _operation_id(c),
        "summary":     c["purpose"] or f"{c['method']} {c['path']}",
    }

    if c["screens"]:
        op["tags"] = c["screens"]

    # parameters (path then query)
    params: list[dict] = []
    for p in c["path_params"]:
        params.append({
            "name":         p,
            "in":           "path",
            "required":     True,
            "schema":       {"type": "string"},
            "x-mcm-source": "path parameter derived from MCM WHERE clause",
        })
    for q in c["query_params"]:
        params.append({
            "name":     q,
            "in":       "query",
            "required": False,
            "schema":   {"type": "string"},
        })
    if params:
        op["parameters"] = params

    # request body
    if c["has_body"]:
        op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {"schema": _props_to_schema(c["body_props"])}
            },
        }

    op["responses"] = _build_responses(c)

    # security — auth endpoints are the grant surface; they don't require a token
    if needs_security and not c["is_auth"]:
        scheme_name = (sec_cfg or {}).get("scheme_name", "BearerAuth")
        op["security"] = [{scheme_name: []}]

    # MCM traceability extensions (verbatim from evidence, never invented)
    if c["operation_ids"]:
        op["x-replaces-operations"] = c["operation_ids"]
    if c["notes"]:
        op["x-mcm-notes"] = c["notes"]
    if c["gaps"]:
        op["x-mcm-gaps"] = c["gaps"]
    if c["legacy_refs"]:
        op["x-mcm-legacy-sources"] = c["legacy_refs"]

    return op


# ---------------------------------------------------------------- public API

def build(ev: dict) -> dict:
    """Build an OpenAPI 3.0.3 document from evidence.json.

    All endpoint derivation is delegated to api_contract.contracts(ev).
    Project-specific defaults (server URL, auth scheme) are read from the
    profile that was used to generate evidence via api_contract.profile_openapi_cfg(ev).

    No endpoint, schema, or status code is invented beyond what the MCM
    captured and api_contract.py derives deterministically from it.
    """
    fid          = ev.get("feature_id") or ""
    cs           = _ac.contracts(ev)
    has_security = bool(ev.get("security_signals"))
    cfg          = _ac.profile_openapi_cfg(ev)     # project-specific config from profile

    srv_cfg  = cfg.get("server") or {}
    sec_cfg  = cfg.get("security") or {}

    # ---- info block
    doc: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title":       f"{ev.get('name') or fid} ({fid})",
            "version":     "0.0.1-mcm",
            "description": (
                f"API contracts for feature `{fid}` derived from the Meta Cognitive Model (MCM). "
                f"All endpoints and schemas are sourced from MCM data operations; "
                f"this file is a machine-readable companion to `{fid}.md`."
            ),
            "x-feature-id":   fid,
            "x-mcm-sha256":   ev.get("mcm_sha256") or "",
            "x-mcm-path":     ev.get("mcm_path") or "",
            "x-generated-by": "feature_facts openapi",
        },
        "servers": [
            {
                "url":         srv_cfg.get("url_template", "{baseUrl}/api"),
                "description": srv_cfg.get("description", "Replace {baseUrl} with the deployed service root URL."),
                "variables": {
                    "baseUrl": {
                        "default":     srv_cfg.get("default_url", "http://localhost:8000"),
                        "description": srv_cfg.get("base_url_variable_description",
                                                   "Service base URL (scheme + host + optional port)."),
                    }
                },
            }
        ],
    }

    # ---- paths
    paths: dict[str, Any] = {}
    for c in cs:
        paths.setdefault(c["path"], {})
        paths[c["path"]][c["method"].lower()] = _build_operation(c, has_security, sec_cfg)

    if not cs:
        # Feature has no data operations — emit a placeholder so the file is valid OpenAPI
        paths["/"] = {
            "get": {
                "operationId": "no-ops",
                "summary":     "No data operations captured in the MCM for this feature.",
                "responses":   {"200": {"description": "No operations."}},
                "x-mcm-note":  (
                    "This feature has no backend data operations in the MCM. "
                    "Add endpoints manually after analysing the source code."
                ),
            }
        }
    doc["paths"] = paths

    # ---- components
    components: dict[str, Any] = {}

    if has_security:
        scheme_name = sec_cfg.get("scheme_name", "BearerAuth")
        components["securitySchemes"] = {
            scheme_name: {
                "type":         sec_cfg.get("type", "http"),
                "scheme":       sec_cfg.get("scheme", "bearer"),
                "bearerFormat": sec_cfg.get("format", "JWT"),
                "description":  sec_cfg.get(
                    "description",
                    "Token obtained from the authentication endpoint. "
                    "Required on all non-authentication endpoints.",
                ),
            }
        }

    # Inline schemas for data objects — types from sql_column_types() (not invented)
    data_objects = (ev.get("backend") or {}).get("data_objects") or []
    if data_objects:
        col_types = _ac.sql_column_types(ev)
        schemas: dict[str, Any] = {}
        for obj in data_objects:
            raw  = obj.get("object") or "Unknown"
            name = raw.split(".")[-1].capitalize()
            cols = [c for c in (obj.get("columns") or []) if c]
            schemas[name] = {
                "type":        "object",
                "description": (
                    f"Schema for `{raw}` ({obj.get('role') or 'table'}). "
                    "Column types derived from MCM SQL; "
                    "\"string\" is a conservative stub where the type is not stated."
                ),
                "properties":  {c: {"type": col_types.get(c, "string")} for c in cols},
                "x-mcm-table": raw,
                "x-mcm-role":  obj.get("role") or "",
            }
        if schemas:
            components["schemas"] = schemas

    if components:
        doc["components"] = components

    # ---- tags  (one per screen, description = screen-level MCM purpose)
    seen: dict[str, str] = {}
    for c in cs:
        for scr, purpose in c["screen_tags"].items():
            if scr not in seen:
                seen[scr] = purpose
    if seen:
        doc["tags"] = [{"name": k, "description": v} for k, v in seen.items()]

    return doc
