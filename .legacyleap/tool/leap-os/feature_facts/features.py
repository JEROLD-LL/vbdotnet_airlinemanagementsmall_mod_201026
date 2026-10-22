"""Group screens into features using MCM evidence only, then derive ids, order, dependencies and effort.

Rules, first match wins, each recorded as membership evidence:
  1. platform        screen has no Designer part (no user surface) while other screens do
  2. authentication  screen key names an authentication surface (login / sign-in / logon / splash / auth)
  3. shell           screen opens >= 3 other screens (navigation evidence) and writes no data object
  4. data            screens that write (INSERT/UPDATE/DELETE) the same data object, transitively
  5. attach          a remaining screen joins the single data feature it opens, else the single data
                     feature it is opened from, else the single feature sharing a >= 4 char name prefix
  6. standalone      anything left gets its own feature
"""

from __future__ import annotations

import re
from collections import OrderedDict, defaultdict

from mcm import WRITE_OPS, cog, metric, qn
EFFORT_LOC = ((100, "XS"), (250, "S"), (700, "M"), (1600, "L"))
EFFORT_METHODS = ((5, "XS"), (15, "S"), (40, "M"), (90, "L"))


def kebab(s):
    s = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "-", str(s))
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def title(s):
    return " ".join(w.capitalize() for w in kebab(s).split("-") if w)


def _effort(loc, methods):
    for limit, size in (EFFORT_LOC if loc > 0 else EFFORT_METHODS):
        if (loc if loc > 0 else methods) < limit:
            return size
    return "XL"


def group(mcm):
    keys = list(mcm.screens)
    nav = {k: sorted({e["to_screen"] for e in mcm.navigation(k)}) for k in keys}
    feats, member = OrderedDict(), {}

    def add(slug, name, kind, entries):
        base, n = slug, 2
        while slug in feats:
            slug, n = f"{base}-{n}", n + 1
        feats[slug] = {"slug": slug, "name": name, "kind": kind, "membership": []}
        for key, reason, evidence in entries:
            feats[slug]["membership"].append({"screen": key, "rule": kind, "reason": reason, "evidence": evidence})
            member[key] = slug
        return slug

    platform = [k for k in keys if not mcm.is_ui(k)]
    if platform:
        reason = mcm.profile.get("features.platform_reason", "not a user-facing entry point")
        add("platform", "Platform", "platform",
            [(k, reason, [qn(mcm.screens[k]["primary"])]) for k in platform])
    auth_re = mcm.profile.regex("features.authentication_key_regex")
    auth = [k for k in keys if k not in member and auth_re.search(k)]
    if auth:
        add("authentication", "Authentication", "authentication",
            [(k, f"screen key '{k}' names an authentication surface", [qn(mcm.screens[k]["primary"])]) for k in auth])
    for k in keys:
        if k not in member and not mcm.owned(k) and len(nav[k]) >= 3:
            add(kebab(k), title(k), "shell",
                [(k, f"opens {len(nav[k])} screens ({', '.join(nav[k])}) and writes no data object",
                  sorted({e["via"] for e in mcm.navigation(k)}))])

    parent, owner = {}, {}

    def find(x):
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for k in keys:
        if k in member or not mcm.owned(k):
            continue
        find(k)
        for obj in mcm.owned(k):
            if obj in owner:
                parent[find(k)] = find(owner[obj])
            else:
                owner[obj] = k
    clusters = OrderedDict()
    for k in keys:
        if k in parent:
            clusters.setdefault(find(k), []).append(k)
    for members in clusters.values():
        writes = defaultdict(int)
        for k in members:
            for o in mcm.screen_operations(k):
                if o["operation"] in WRITE_OPS:
                    writes[o["object"]] += 1
        primary = sorted(writes, key=lambda o: (-writes[o], o))[0]
        table = primary.split(".", 1)[-1]
        entries = []
        for k in members:
            ops = [o for o in mcm.screen_operations(k) if o["operation"] in WRITE_OPS]
            entries.append((k, "writes " + ", ".join(sorted({f"{o['object']} ({o['operation']})" for o in ops})),
                            sorted({o["method"] for o in ops})))
        add(kebab(table), title(table), "data", entries)

    data_slugs = {s for s, f in feats.items() if f["kind"] == "data"}

    def prefix_len(a, b):
        n = 0
        while n < min(len(a), len(b)) and a[n].lower() == b[n].lower():
            n += 1
        return n

    changed = True
    while changed:
        changed = False
        for k in keys:
            if k in member:
                continue
            opens = sorted({member[t] for t in nav[k] if member.get(t) in data_slugs})
            opened_by = sorted({member[s] for s in keys if k in nav[s] and member.get(s) in data_slugs})
            named = sorted({member[t] for t in member if prefix_len(k, t) >= 4 and 2 * prefix_len(k, t) >= min(len(k), len(t))})
            for cands, why in ((opens, "opens"), (opened_by, "is opened from"), (named, "shares a name prefix with")):
                if len(cands) == 1:
                    slug = cands[0]
                    if why == "shares a name prefix with":
                        peers = [t for t in member if member[t] == slug and prefix_len(k, t) >= 4]
                        reason, ev = f"{why} {', '.join(sorted(peers))}", [qn(mcm.screens[k]["primary"])]
                    elif why == "opens":
                        peers = [t for t in nav[k] if member.get(t) == slug]
                        reason = f"{why} {', '.join(peers)}"
                        ev = sorted({e["via"] for e in mcm.navigation(k) if e["to_screen"] in peers})
                    else:
                        peers = [s for s in keys if k in nav[s] and member.get(s) == slug]
                        reason = f"{why} {', '.join(peers)}"
                        ev = sorted({e["via"] for s in peers for e in mcm.navigation(s) if e["to_screen"] == k})
                    feats[slug]["membership"].append({"screen": k, "rule": "attach", "reason": reason, "evidence": ev})
                    member[k] = slug
                    changed = True
                    break
    for k in keys:
        if k not in member:
            add(kebab(k), title(k), "standalone", [(k, "no grouping rule matched", [qn(mcm.screens[k]["primary"])])])
    for f in feats.values():
        f["membership"].sort(key=lambda m: keys.index(m["screen"]))
        f["screens"] = [m["screen"] for m in f["membership"]]
    return _plan(mcm, feats, member)


def _plan(mcm, feats, member):
    owners = defaultdict(set)
    for f in feats.values():
        f["behavior_loc"] = sum(metric(mcm.screens[k]["primary"], "loc")
                                + sum(metric(x, "loc") for x in mcm.screens[k]["extras"]) for k in f["screens"])
        f["designer_loc"] = sum(metric(mcm.screens[k]["designer"], "loc") if mcm.screens[k]["designer"] else 0
                                for k in f["screens"])
        f["method_count"] = sum(len(mcm.screens[k]["methods"]) for k in f["screens"])
        f["owned_objects"] = sorted({o for k in f["screens"] for o in mcm.owned(k)})
        f["lookup_objects"] = sorted({o for k in f["screens"] for o in mcm.looked_up(k)} - set(f["owned_objects"]))
        for obj in f["owned_objects"]:
            owners[obj].add(f["slug"])

    platform = sorted(s for s, f in feats.items() if f["kind"] == "platform")
    auth = sorted(s for s, f in feats.items() if f["kind"] == "authentication")
    deps = {s: {} for s in feats}
    for s, f in feats.items():
        if f["kind"] == "authentication":
            deps[s].update({p: "platform" for p in platform})
        elif f["kind"] != "platform":
            deps[s].update({a: "authentication" for a in auth})
            for k in f["screens"]:
                for c in mcm.calls_to_platform(k):
                    p = member.get(c["screen"])
                    if p and p != s:
                        deps[s].setdefault(p, f"calls {c['screen']}")
            if f["owned_objects"]:
                for obj in f["lookup_objects"]:
                    for o in sorted(owners.get(obj, ())):
                        if o == s:
                            continue
                        prev = deps[s].get(o)
                        if prev is None:
                            deps[s][o] = f"reads {obj}"
                        elif prev.startswith("reads "):
                            deps[s][o] = f"{prev}, {obj}"

    broken = []
    while True:
        cycle = _cycle({s: set(d) for s, d in deps.items()})
        if not cycle:
            break
        edges = [(cycle[i], cycle[i + 1]) for i in range(len(cycle) - 1)]

        def weight(e):
            reads = deps[e[0]][e[1]].replace("reads ", "").split(", ")
            return sum(1 for o in mcm.operations.values() if o["object"] in reads and o["operation"] in WRITE_OPS
                       and member.get(o["screen"]) == e[1])

        victim = min(edges, key=lambda e: (not deps[e[0]][e[1]].startswith("reads "), weight(e), e))
        broken.append({"cycle": cycle, "removed": {"from": victim[0], "to": victim[1]}, "owner_writes": weight(victim)})
        del deps[victim[0]][victim[1]]

    depth = {}

    def d(s):
        if s not in depth:
            depth[s] = 1 + max((d(x) for x in deps[s]), default=-1)
        return depth[s]

    order = sorted(feats, key=lambda s: (d(s), -(feats[s]["behavior_loc"] + feats[s]["designer_loc"]), s))
    width = max(2, len(str(len(order))))
    ids = {s: f"F{i + 1:0{width}d}-{s}" for i, s in enumerate(order)}
    out = []
    for s in order:
        f = feats[s]
        loc = f["behavior_loc"] + f["designer_loc"]
        screen_parts = sorted((p for k in f["screens"] for p in mcm.screen_parts(k)), key=lambda p: mcm.order[p.get("id")])
        methods = sorted((m for k in f["screens"] for m in mcm.screens[k]["methods"] + mcm.screens[k]["designer_methods"]),
                         key=lambda p: mcm.order[p.get("id")])
        out.append({
            "id": ids[s], "slug": s, "name": f["name"], "kind": f["kind"],
            "intent": cog(mcm.screens[f["screens"][0]]["primary"], "intent"),
            "screens": f["screens"], "membership": f["membership"],
            "depends_on": [{"id": ids[x], "reason": deps[s][x]} for x in sorted(deps[s], key=lambda x: ids[x])],
            "dependency_depth": depth[s],
            "effort": {"size": _effort(loc, f["method_count"]), "basis": "loc" if loc > 0 else "method_count",
                       "behavior_loc": f["behavior_loc"], "designer_loc": f["designer_loc"],
                       "method_count": f["method_count"]},
            "owned_objects": f["owned_objects"], "lookup_objects": f["lookup_objects"],
            "qualified_names": [qn(p) for p in screen_parts] + [qn(m) for m in methods],
        })
    return out, broken


def _cycle(graph):
    color, stack = {}, []

    def visit(n):
        color[n] = 1
        stack.append(n)
        for m in sorted(graph[n]):
            if color.get(m) == 1:
                return stack[stack.index(m):] + [m]
            if m not in color:
                c = visit(m)
                if c:
                    return c
        stack.pop()
        color[n] = 2
        return None

    for n in sorted(graph):
        if n not in color:
            c = visit(n)
            if c:
                return c
    return None
