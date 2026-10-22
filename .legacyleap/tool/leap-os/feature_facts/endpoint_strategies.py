"""Factory + Strategy pattern for deriving REST endpoint shapes from MCM dependency records.

Each strategy converts one MCM external_dependency entry into a canonical
``(verb, path, shape, gaps, notes, op_label)`` tuple — the same contract that
``_apis()`` in facts.py assembles into the ``evidence.json`` apis[] list.

Selecting the right strategy for a ``dependency_type`` is done by
``EndpointStrategyFactory``.

Public API
----------
EndpointStrategy            — abstract base (one subclass per MCM dependency_type)
DatabaseEndpointStrategy    — SQL SELECT/INSERT/UPDATE/DELETE → REST endpoint
HttpApiEndpointStrategy     — existing HTTP path used verbatim (web apps)
ExternalServiceStrategy     — CLOUD_SERVICE / THIRD_PARTY → skip (out-of-scope)
EndpointStrategyFactory     — dict-based registry; register() + get()

Return contract of derive()
---------------------------
Returns a 6-tuple  (verb, path, shape, gaps, notes, op_label)  or  None.
  verb     : str   HTTP verb  e.g. "GET"
  path     : str   URL path   e.g. "/api/users/{id}"
  shape    : dict  {"path_params": [], "query_params": [], "request_body": [], "response": []}
  gaps     : list  data-quality warnings to surface in the spec
  notes    : list  informational notes about derivation decisions
  op_label : str   short label describing the source operation (e.g. "SELECT")
Returns None to signal "skip this dependency — it is not a REST endpoint".
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

# ---- re-use the same compiled patterns that facts.py / mcm.py use ----------
# Imported lazily inside methods to avoid circular-import issues at module load.
_COUNT_RE        = re.compile(r"\bCOUNT\s*\(", re.I)
_SELECT_LIST_RE  = re.compile(r"SELECT\s+(?:DISTINCT\s+)?(.+?)\s+FROM\b", re.I | re.S)
_SET_LIST_RE     = re.compile(r"\bSET\s+(.+?)(?:\bWHERE\b|$)", re.I | re.S)
_SENSITIVE_RE    = re.compile(r"pass(?:word)?|pwd|secret|token|api[_-]?key|auth", re.I)
_IDENT_RE        = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PURPOSE_VERBS   = (
    ("SELECT", r"\b(?:retriev|read|fetch|load|get|query|count|select|look\s*up|display|list)"),
    ("INSERT", r"\b(?:insert|add|sav|creat|register)"),
    ("UPDATE", r"\b(?:updat|modif|chang|edit)"),
    ("DELETE", r"\b(?:delet|remov)"),
)
_PURPOSE_FILTER_RE = re.compile(
    r"\b(?:by|based on|for (?:the )?(?:selected|given))\s+([\w ]{3,40}?)"
    r"(?:\s+(?:for|to|from|and)\b|[,.;]|$)", re.I
)
_HTTP_VERB_PATH_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE|HEAD)\s+(/\S*)", re.I)


# ---- helpers ----------------------------------------------------------------

def _empty_shape() -> dict:
    return {"path_params": [], "query_params": [], "request_body": [], "response": []}


def _idents(text: str) -> list[str]:
    """Extract SQL column identifiers from a comma-separated column list."""
    out = []
    for token in text.split(","):
        m = _IDENT_RE.search(token.strip())
        if m:
            out.append(m.group())
    return out


def _dedupe(seq: list) -> list:
    """Order-preserving deduplication."""
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ---- abstract base ----------------------------------------------------------

class EndpointStrategy(ABC):
    """Abstract base: one concrete strategy per MCM dependency_type.

    Subclasses must be stateless (shared instances) — derive() must not mutate
    ``operation`` or ``context``.
    """

    #: Short label written to evidence.json for traceability
    source_kind: str

    @abstractmethod
    def derive(
        self,
        operation: dict,
        context: dict,
    ) -> tuple | None:
        """Convert one MCM dependency/operation record to a REST endpoint shape.

        Parameters
        ----------
        operation
            For DATABASE: the dict produced by ``MCM.raw_operations()`` — contains
            ``operation``, ``object``, ``sql``, ``columns``, ``where_columns``, etc.
            For API: the raw external_dependency dict — contains
            ``dep_type``, ``called_entity``, ``endpoint_or_identifier``, etc.
        context
            Execution context:
            ``columns_of``  {table_name: [column_names]}  (empty for non-DB strategies)
            ``profile``     the active Profile object (optional, may be absent)

        Returns
        -------
        (verb, path, shape, gaps, notes, op_label) tuple, or None to skip.
        """


# ---- DatabaseEndpointStrategy -----------------------------------------------

class DatabaseEndpointStrategy(EndpointStrategy):
    """Derive a REST endpoint from an MCM SQL/DATABASE dependency.

    This is the verbatim logic that lived in ``facts.py::_endpoint()`` before
    the strategy refactoring.  No behaviour change — only reorganisation.
    """

    source_kind = "database"

    def derive(self, operation: dict, context: dict) -> tuple | None:
        o          = operation
        columns_of = context.get("columns_of") or {}

        res = re.sub(r"[^a-z0-9]+", "-", o["object"].split(".")[-1].lower()).strip("-")
        # HTTP routers treat leading-digit segments as IDs; prefix purely numeric names
        if res and res[0].isdigit():
            res = "x-" + res

        base  = f"/api/{res}"
        where = o.get("where_columns") or []
        sql   = o.get("sql") or ""
        gaps: list[str]  = []
        notes: list[str] = []
        shape = _empty_shape()
        op    = o.get("operation")

        if op is None:
            purpose = str(o.get("purpose") or "")
            hits = sorted(
                (m.start(), verb)
                for verb, rx in _PURPOSE_VERBS
                for m in [re.search(rx, purpose, re.I)]
                if m
            )
            if hits:
                op = hits[0][1]
                notes.append(f"no SQL in the MCM; {op} inferred from the purpose text")
            f_match = _PURPOSE_FILTER_RE.search(purpose)
            if op == "SELECT" and f_match and not where:
                gaps.append(
                    f"the purpose says 'by {f_match.group(1).strip()}' but the MCM has "
                    f"no SQL, so the filter column is unknown"
                )

        def keyed(verb):
            if len(where) == 1:
                shape["path_params"] = list(where)
                return verb, f"{base}/{{{where[0]}}}"
            if where:
                shape["query_params"] = list(where)
            elif verb != "GET":
                gaps.append("the MCM SQL has no WHERE column, so the record key is unknown")
            return verb, base

        if op == "SELECT":
            m = _SELECT_LIST_RE.search(sql)
            listed = m.group(1).strip() if m else ""
            cols = (
                columns_of.get(o["object"], [])
                if listed == "*"
                else ([] if "(" in listed else _idents(listed))
            )
            counting = _COUNT_RE.search(listed) or (
                not sql
                and re.search(
                    r"\b(?:count|number of|total number)\b",
                    str(o.get("purpose") or ""),
                    re.I,
                )
            )
            if counting:
                verb, path = "GET", f"{base}/count"
                shape["query_params"] = list(where)
                shape["response"]     = ["count"]
            elif any(_SENSITIVE_RE.search(c) for c in where):
                verb, path            = "POST", f"{base}/authenticate"
                shape["request_body"] = list(where)
                shape["response"]     = [
                    c for c in cols
                    if c not in where and not _SENSITIVE_RE.search(c)
                ]
            else:
                verb, path     = keyed("GET")
                shape["response"] = cols
            if not m and not shape["response"]:
                shape["response"] = columns_of.get(o["object"], [])
                notes.append(
                    "no SELECT list in the MCM; response lists every known column of the table"
                )

        elif op == "INSERT":
            verb, path            = "POST", base
            shape["request_body"] = [c for c in o.get("columns", []) if c not in where]

        elif op == "UPDATE":
            verb, path = keyed("PUT")
            m = _SET_LIST_RE.search(sql)
            shape["request_body"] = (
                [
                    c
                    for c in (
                        _idents(part.split("=")[0])
                        for part in m.group(1).split(",")
                    )
                    if c
                ]
                if m
                else [c for c in o.get("columns", []) if c not in where]
            )

        elif op == "DELETE":
            verb, path = keyed("DELETE")

        else:
            verb, path = "POST", base
            gaps.append("the MCM does not say which SQL verb this operation uses")

        if op in ("INSERT", "UPDATE") and not shape["request_body"]:
            gaps.append(
                "the MCM names no columns for this write, so the request fields are unknown"
            )

        withheld = [c for c in shape["response"] if _SENSITIVE_RE.search(c)]
        if withheld:
            shape["response"] = [c for c in shape["response"] if c not in withheld]
            notes.append(f"{', '.join(withheld)} withheld from the response (sensitive column)")

        return verb, path, shape, gaps, notes, op


# ---- HttpApiEndpointStrategy ------------------------------------------------

class HttpApiEndpointStrategy(EndpointStrategy):
    """Use an existing HTTP path verbatim from the MCM API dependency record.

    Designed for web apps where the legacy code already calls REST endpoints.
    The MCM captures these as ``dependency_type == "API"`` records whose
    ``endpoint_or_identifier`` field contains the HTTP verb and path,
    e.g. ``"GET /api/users/{id}"``.

    WinForms ``Show()`` / ``ShowDialog()`` calls also carry ``dependency_type == "API"``
    in this project but have no HTTP verb in their identifier — those return None
    (skip), so no spurious endpoints are generated.
    """

    source_kind = "http_api"

    def derive(self, operation: dict, context: dict) -> tuple | None:
        ident = (
            operation.get("endpoint_or_identifier")
            or operation.get("called_entity")
            or ""
        ).strip()

        m = _HTTP_VERB_PATH_RE.match(ident)
        if not m:
            # Not an HTTP endpoint (e.g. WinForms Show() call) — skip silently
            return None

        verb  = m.group(1).upper()
        path  = m.group(2)
        shape = _empty_shape()

        # Extract path params from {param} patterns already in the path
        shape["path_params"] = re.findall(r"\{(\w+)\}", path)

        notes = ["path taken verbatim from MCM endpoint_or_identifier"]
        gaps: list[str] = []

        purpose = operation.get("purpose") or operation.get("method_type") or ""
        return verb, path, shape, gaps, notes, purpose or "HTTP_CALL"


# ---- ExternalServiceStrategy ------------------------------------------------

class ExternalServiceStrategy(EndpointStrategy):
    """CLOUD_SERVICE and THIRD_PARTY dependencies are not REST endpoints.

    These are calls to external systems (S3, SendGrid, Stripe, …) that are
    out-of-scope for the REST API the modernised system exposes.  Return None
    so ``_apis()`` silently skips them.
    """

    source_kind = "external_service"

    def derive(self, operation: dict, context: dict) -> tuple | None:
        return None


# ---- FallbackStrategy -------------------------------------------------------

class _FallbackStrategy(EndpointStrategy):
    """Returned by the factory for unknown dependency_types.

    Emits a gap note so the spec author is aware of the unhandled dep, then
    returns None to skip (no spurious endpoint generated).
    """

    source_kind = "unknown"

    def derive(self, operation: dict, context: dict) -> tuple | None:
        # Callers check for None; gaps recorded by _apis() if needed
        return None


# ---- EndpointStrategyFactory ------------------------------------------------

class EndpointStrategyFactory:
    """Registry mapping MCM ``dependency_type`` strings to ``EndpointStrategy`` instances.

    Usage
    -----
    # Look up the strategy for a dep type (case-insensitive):
    strategy = EndpointStrategyFactory.get("DATABASE")
    result   = strategy.derive(operation, context)

    # Register a custom strategy (e.g. from a profile plugin):
    EndpointStrategyFactory.register("GRAPHQL", MyGraphQLStrategy())
    """

    _registry: dict[str, EndpointStrategy] = {}
    _fallback: EndpointStrategy             = _FallbackStrategy()

    @classmethod
    def register(cls, dep_type: str, strategy: EndpointStrategy) -> None:
        """Register a strategy for a dependency_type (case-insensitive key)."""
        cls._registry[dep_type.upper()] = strategy

    @classmethod
    def get(cls, dep_type: str) -> EndpointStrategy:
        """Return the registered strategy, or the fallback for unknown types."""
        return cls._registry.get((dep_type or "").upper(), cls._fallback)

    @classmethod
    def registered_types(cls) -> list[str]:
        """Return the list of currently registered dep_type strings."""
        return sorted(cls._registry.keys())


# ---- built-in registrations -------------------------------------------------

EndpointStrategyFactory.register("DATABASE",      DatabaseEndpointStrategy())
EndpointStrategyFactory.register("API",           HttpApiEndpointStrategy())
EndpointStrategyFactory.register("CLOUD_SERVICE", ExternalServiceStrategy())
EndpointStrategyFactory.register("THIRD_PARTY",   ExternalServiceStrategy())
# LIBRARY and EVENT deps are not endpoints — factory fallback returns None
