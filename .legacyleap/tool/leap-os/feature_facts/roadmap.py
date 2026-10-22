"""Generate a product roadmap markdown from the MCM feature index.

Each roadmap item is one feature. Under each item the derived REST endpoints
are listed — one line per unique (verb, path), with all contributing legacy
qualified names grouped in parentheses.

Endpoints are resolved generically via ``EndpointStrategyFactory``:
  - Pass 1: SQL / DATABASE ops from ``mcm.screen_operations()``
             → ``DatabaseEndpointStrategy`` (WRITE ops take priority over SELECT)
  - Pass 2: non-DATABASE deps from ``mcm.screen_external_apis()``
             → whichever strategy is registered for that dep_type (API, etc.)

Internal helper methods (noise callbacks: _KeyPress, _Validating, …) and deps
that produce no endpoint (ExternalServiceStrategy, WinForms Show() calls) are
excluded silently.

Deduplication layers
--------------------
1. ``seen`` set in ``endpoint_entries()``  — same QN never appears twice
2. ``_grouped_entries()``                  — same (verb, path) from different QNs
                                             merged into one line

The format:
  N. [ ] **Feature Name** — intent sentence. `EFFORT`
     - [ ] VERB '/path' (qname1, qname2, ...)
     - [ ] VERB '/path' (qname)
     *(no endpoint methods)* — when the feature has no derivable endpoints

Checkbox preservation
---------------------
``build()`` accepts an optional ``existing_text`` parameter (the current file
contents). When supplied it parses every checked ``[x]`` or ``[X]`` line and
carries those ticks forward into the regenerated output so that manually ticked
progress is never erased.

  Feature-level tick: matched by feature number (``N.``) + exact name.
  Endpoint tick: matched by verb+path string (``VERB '/path'``).
  QN-only tick: matched by the backtick QN string.

Usage (called from __main__.py):
    import roadmap
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    text = roadmap.build(mcm, index, existing_text=existing)
    path.write_text(text, encoding="utf-8")
"""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

from endpoint_strategies import EndpointStrategyFactory
from mcm import WRITE_OPS

# ------------------------------------------------------------------ tick parser

_FEATURE_TICK_RE = re.compile(
    r"^\d+\.\s+\[([xX])\]\s+\*\*(.+?)\*\*",
    re.MULTILINE,
)
_ENDPOINT_TICK_RE = re.compile(
    r"^\s+-\s+\[([xX])\]\s+(\w+\s+'[^']*'|`.+?`)",
    re.MULTILINE,
)


def _parse_checked(text: str) -> tuple[set[str], set[str]]:
    """Return (checked_feature_names, checked_endpoint_keys) from existing text.

    checked_feature_names : set of bold feature name strings (e.g. "Authentication")
    checked_endpoint_keys : set of "VERB '/path'" strings or "`qname`" strings
    """
    feature_names: set[str] = set()
    endpoint_keys: set[str] = set()
    for m in _FEATURE_TICK_RE.finditer(text):
        feature_names.add(m.group(2))
    for m in _ENDPOINT_TICK_RE.finditer(text):
        endpoint_keys.add(m.group(2).strip())
    return feature_names, endpoint_keys

# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _method_name(qualified: str) -> str:
    """Return the bare method name from a MCM qualified name.

    MCM format: Namespace.ClassName.ClassName.MethodName.N.ParamType...
    The method name is always at index 3 (0-based).
    """
    parts = qualified.split(".")
    return parts[3] if len(parts) > 3 else parts[-1]


def _is_noise(method_name: str) -> bool:
    """Return True for UI-framework callbacks that never map to a REST endpoint.

    These are field-level input handlers (keystroke validators, focus events)
    that fire on every character/focus change and never initiate a backend
    operation — including them adds noise without value.
    """
    NOISE_SUFFIXES = (
        "_KeyPress",
        "_Validating",
        "_Validated",
        "_TextChanged",
        "_FormClosing",
        "_CheckedChanged",
        "_ValueChanged",
    )
    return any(method_name.endswith(s) for s in NOISE_SUFFIXES)


def _best_endpoint(qname: str, all_ops: list, columns_of: dict):
    """Return (verb, path) for a DATABASE-backed qname, or None.

    When a method has both a WRITE op (INSERT/UPDATE/DELETE) and a SELECT op
    in the MCM, the WRITE op wins — e.g. SaveButton2_Click returns POST, not GET.
    """
    strategy = EndpointStrategyFactory.get("DATABASE")
    ops = [op for op in all_ops if op.get("method") == qname]
    write_ops = [op for op in ops if op.get("operation") in WRITE_OPS]
    for op in (write_ops or ops):
        result = strategy.derive(op, {"columns_of": columns_of})
        if result:
            return result[0], result[1]
    return None


def _best_api_endpoint(dep: dict):
    """Return (verb, path) for a non-DATABASE dep via the registered strategy, or None.

    For WinForms Show() calls, HttpApiEndpointStrategy returns None (no HTTP verb
    pattern) and the dep is silently skipped.  For a web app with real HTTP deps,
    the verb+path are taken verbatim from endpoint_or_identifier.
    """
    strategy = EndpointStrategyFactory.get(dep.get("dep_type", ""))
    result = strategy.derive(dep, {})
    return (result[0], result[1]) if result else None


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def endpoint_entries(mcm, feature) -> list[tuple[str, str | None, str | None]]:
    """Return [(qname, verb, path), ...] for all endpoint methods in a feature.

    Pass 1 — DATABASE ops via ``mcm.screen_operations()``.
    Pass 2 — non-DATABASE deps via ``mcm.screen_external_apis()``.

    A shared ``seen`` set guarantees each QN appears at most once across both
    passes.  QNs whose strategy returns None are still included with
    verb=None, path=None so callers can decide what to do with them.

    ``feature`` may be a dict (from features.json) or any object with a
    ``screens`` attribute/key that is a list of screen keys (strings) or
    screen dicts with a "key" field.
    """
    # Build columns_of for DatabaseEndpointStrategy
    columns_of: dict[str, set] = {}
    for op in mcm.operations.values():
        for c in op.get("columns", []):
            columns_of.setdefault(op.get("object", ""), set()).add(c)
    all_ops = list(mcm.operations.values())

    raw_screens = feature["screens"] if isinstance(feature, dict) else feature.screens
    screen_keys = [s["key"] if isinstance(s, dict) else s for s in raw_screens]

    seen: set[str] = set()
    out: list[tuple[str, str | None, str | None]] = []

    for key in screen_keys:
        # Pass 1: DATABASE ops
        for op in mcm.screen_operations(key):
            qname = op.get("method", "")
            if not qname or qname in seen or _is_noise(_method_name(qname)):
                continue
            seen.add(qname)
            ep = _best_endpoint(qname, all_ops, columns_of)
            out.append((qname, ep[0] if ep else None, ep[1] if ep else None))

        # Pass 2: non-DATABASE deps (API, CLOUD_SERVICE, etc.)
        for dep in mcm.screen_external_apis(key):
            qname = dep.get("method_qn", "") or dep.get("called_entity", "")
            if not qname or qname in seen:
                continue
            ep = _best_api_endpoint(dep)
            if ep:   # None → ExternalServiceStrategy / no HTTP verb → skip
                seen.add(qname)
                out.append((qname, ep[0], ep[1]))

    return out


def endpoint_qns(mcm, feature) -> list[str]:
    """Backward-compatible wrapper: return just the qualified names.

    Still used by ``__main__.py`` for the ``total_endpoint_qns`` count.
    """
    return [q for q, _, _ in endpoint_entries(mcm, feature)]


def _grouped_entries(mcm, feature) -> list[dict]:
    """Return endpoint groups for one feature, deduped by (verb, path).

    Each group dict has one of two shapes:
      {"verb": str,  "path": str,  "qnames": [str, ...]}  — resolved endpoint
      {"verb": None, "path": None, "qnames": [str]}        — no endpoint derived

    Multiple QNs that map to the same (verb, path) are merged into one group so
    the same endpoint line never appears twice in the roadmap.  Ordering is the
    insertion order of the first QN that produced each endpoint.
    """
    entries = endpoint_entries(mcm, feature)
    grouped: OrderedDict[tuple, list[str]] = OrderedDict()
    fallback: list[str] = []

    for qname, verb, path in entries:
        if verb and path:
            grouped.setdefault((verb, path), []).append(qname)
        else:
            fallback.append(qname)

    out = [{"verb": v, "path": p, "qnames": qs} for (v, p), qs in grouped.items()]
    out += [{"verb": None, "path": None, "qnames": [q]} for q in fallback]
    return out


# ------------------------------------------------------------------
# Markdown builder
# ------------------------------------------------------------------

def build(mcm, index: dict, existing_text: str = "") -> str:
    """Return the full roadmap markdown text.

    Parameters
    ----------
    mcm:
        Loaded MCM object (provides screen_operations and screen_external_apis).
    index:
        The features index dict as returned by facts.index() and written
        to features.json.  Uses: id, name, effort, screens, depends_on.
    existing_text:
        Current contents of features-roadmap.md (if any). Checked items
        (``[x]`` / ``[X]``) are carried forward into the rebuilt output so
        that manually ticked progress is never erased.
    """
    checked_features, checked_endpoints = _parse_checked(existing_text)

    lines: list[str] = [
        "# Product Roadmap",
        "",
        "> **Auto-generated** — do not edit the endpoint lines by hand.",
        "> Re-run `features` to refresh this file.",
        "> Tick a checkbox once the corresponding API endpoint is implemented.",
        "",
    ]

    # Build a lookup: feature-id → intent (first sentence from primary screen).
    def _intent(f_index_entry: dict) -> str:
        screens = f_index_entry.get("screens", [])
        if not screens:
            return ""
        key = screens[0]["key"] if isinstance(screens[0], dict) else screens[0]
        part = mcm.screens.get(key, {}).get("primary")
        if part is None:
            return ""
        raw = (part.get("cognitive") or {}).get("intent") or ""
        sentence = raw.split(".")[0].strip()
        return sentence + "." if sentence and not sentence.endswith(".") else sentence

    feats = index.get("features", [])

    for i, f in enumerate(feats, start=1):
        name   = f["name"]
        effort = f["effort"]
        intent = _intent(f)
        intent_part = f" — {intent}" if intent else ""
        depends = f.get("depends_on", [])
        dep_note = (
            f" *(depends on {', '.join(d['id'] if isinstance(d, dict) else d for d in depends)})*"
            if depends else ""
        )

        feat_tick = "x" if name in checked_features else " "
        lines.append(f"{i}. [{feat_tick}] **{name}**{intent_part} `{effort}`{dep_note}")

        groups = _grouped_entries(mcm, f)
        if groups:
            for g in groups:
                if g["verb"]:
                    ep_key = f"{g['verb']} '{g['path']}'"
                    ep_tick = "x" if ep_key in checked_endpoints else " "
                    # Show only the primary (first) QN per endpoint — no comma lists.
                    lines.append(f"   - [{ep_tick}] {ep_key} ({g['qnames'][0]})")
                else:
                    qn_key = f"`{g['qnames'][0]}`"
                    qn_tick = "x" if qn_key in checked_endpoints else " "
                    # No endpoint derived — fallback to backtick QN
                    lines.append(f"   - [{qn_tick}] {qn_key}")
        else:
            lines.append("   *(no endpoint methods — platform / UI-only feature)*")

        lines.append("")

    return "\n".join(lines)
