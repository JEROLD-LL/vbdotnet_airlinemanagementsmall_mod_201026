"""Feature board: spec status per feature, the next feature to write, the generated README section,
and a per-screen digest that agents use to tell snapshot images apart.

Status comes from each <ID>/<ID>.md Approval table and Open questions table. A spec is "stale" when it
was approved, or its evidence was pulled, from an MCM other than the one features.json was built from,
or when a draft rests on evidence from an older tool version.
"""

from __future__ import annotations

import json
import re

import facts
import snapmap
import verify
from mcm import cog, qn

START = "<!-- features:start -->"
END = "<!-- features:end -->"
HEADING = "## Features in this project"


def spec_status(root, features_dir, fid, mcm_sha, specs_dir=None):
    p = verify.paths(root, specs_dir if specs_dir is not None else features_dir, fid)
    if not p["spec"].is_file():
        return {"status": "not written", "open_questions": 0, "reviewer": None}
    by_name, _ = verify.sections(p["spec"].read_text(encoding="utf-8"))
    appr = verify.approval(by_name.get("approval", ""))
    # AgentOS format uses Out of Scope bullets instead of a numbered Open questions table;
    # open_questions count is always 0 in this format.
    status = appr.get("status", "").lower()
    status = status if status in ("draft", "approved", "scaffolded") else "scaffolded"
    ev = json.loads(p["evidence"].read_text(encoding="utf-8")) if p["evidence"].is_file() else {}
    old_tool = bool(ev) and ev.get("schema_version") != facts.SCHEMA_VERSION
    if (status == "approved" and appr.get("mcm sha256") != mcm_sha) or (ev and ev.get("mcm_sha256") != mcm_sha) \
            or (old_tool and status != "approved"):
        status = "stale"
    return {"status": status, "open_questions": 0, "reviewer": appr.get("reviewer")}


def rows(root, features_dir, index, specs_dir=None):
    out, state = [], {}
    for f in index["features"]:
        s = spec_status(root, features_dir, f["id"], index["mcm_sha256"], specs_dir=specs_dir)
        state[f["id"]] = s["status"]
        out.append({"id": f["id"], "name": f["name"], "kind": f["kind"],
                    "screens": [x["key"] for x in f["screens"]], "depends_on": f["depends_on"],
                    "grouped_by": f["membership"], "effort": f["effort"],
                    "images": sum(len(x["images"]) for x in f["screens"]), **s})
    for r in out:
        r["waiting_on"] = [d for d in r["depends_on"] if state[d] != "approved"]
    return out


def next_feature(board):
    return next((r["id"] for r in board if r["status"] != "approved" and not r["waiting_on"]), None)


def _short(fid):
    return fid.split("-", 1)[0]


def _spec_cell(r):
    if r["status"] == "approved":
        return f"approved ({r['reviewer']})" if r["reviewer"] else "approved"
    if r["status"] == "draft" and r["open_questions"]:
        return f"draft, {r['open_questions']} open question(s)"
    return r["status"]


def render(index, snaps, board):
    c = snapmap.counts(snaps)
    nxt = next_feature(board)
    lines = [START,
             "_Generated from `features.json` by `feature_facts features` / `status`. "
             "Change the MCM or `snapshot-map.json`, not this table._", "",
             "| Feature | Screens | Depends on | Grouped by | Effort | Images | Spec |",
             "|---|---|---|---|---|---|---|"]
    for r in board:
        deps = ", ".join(_short(d) for d in r["depends_on"]) or "none"
        lines.append(f"| {r['id']} | {', '.join(r['screens'])} | {deps} | {', '.join(r['grouped_by'])} "
                     f"| {r['effort']} | {r['images']} | {_spec_cell(r)} |")
    lines += ["", "**Order:** " + ", ".join(_short(r["id"]) for r in board)
              + " (every feature comes after the features it depends on). "
              + (f"**Next:** `/feature-spec {nxt}`." if nxt else "**All specs approved.**")]
    lines += ["", f"**Snapshots:** {len(snaps['images'])} images: {c['name']} matched by file name, "
                  f"{c['words']} by file-name words (not yet confirmed), {c['manual']} mapped after looking, "
                  f"{c['unmatched']} unmatched."
              + (" Run `/feature-identify` to map and confirm them." if c["unmatched"] or c["words"] else "")]
    for b in index.get("broken_dependency_cycles") or []:
        lines += ["", f"Dependency cycle {' -> '.join(b['cycle'])} broken by dropping "
                      f"{b['removed']['from']} -> {b['removed']['to']}."]
    lines.append(END)
    return "\n".join(lines)


def write_readme(path, block):
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Feature specs\n"
    # P2: guard against duplicate markers — direct .index() would splice at wrong position
    start_count, end_count = text.count(START), text.count(END)
    if start_count > 1 or end_count > 1:
        raise ValueError(
            f"{path.name} contains {start_count} '{START}' marker(s) and {end_count} '{END}' "
            f"marker(s); expected exactly one of each. Remove the duplicates manually."
        )
    if START in text and END in text:
        text = text[:text.index(START)] + block + text[text.index(END) + len(END):]
    elif HEADING in text:
        head, tail = text.split(HEADING, 1)
        m = re.search(r"^## ", tail, re.M)
        text = head + HEADING + "\n\n" + block + "\n\n" + (tail[m.start():] if m else "")
    else:
        text = text.rstrip("\n") + "\n\n" + HEADING + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def screens(mcm, feats, snaps):
    """Per screen: feature, intents (code and Designer part), navigation and mapped images."""
    member = {k: f["id"] for f in feats for k in f["screens"]}
    opened_by = {k: sorted({s for s in mcm.screens if k in {e["to_screen"] for e in mcm.navigation(s)}})
                 for k in mcm.screens}
    out = []
    for k, s in mcm.screens.items():
        out.append({
            "key": k, "feature": member.get(k), "user_facing": mcm.is_ui(k),
            "intent": cog(s["primary"], "intent"),
            "designer_intent": cog(s["designer"], "intent") if s["designer"] else None,
            "opens": sorted({e["to_screen"] for e in mcm.navigation(k)}), "opened_by": opened_by[k],
            "images": snapmap.images_of(snaps, k), "source": f"mcm:{qn(s['primary'])}",
        })
    return out
