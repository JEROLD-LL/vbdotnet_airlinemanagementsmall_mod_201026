"""feature_facts — MCM + UI snapshots -> evidence for one feature spec.

Run from the project root (prefix: python3 -B .legacyleap/tool/leap-os/feature_facts):

  features                 write scan_assessment_reports/features/features.json (pointers only), snapshot-map.json,
                           and features-roadmap.md, and refresh the generated section of scan_assessment_reports/features/README.md.
  screens                  per screen: feature, intents, navigation, mapped images (for mapping snapshots)
  status                   spec status per feature, the next feature to write; refreshes README.md
  evidence --feature ID    write leap-os/specs/features/<ID>/evidence.json (text resolved from the MCM)
  scaffold --feature ID    write the <ID>/<ID>.md skeleton from evidence.json (--force to replace,
                           --sync to refresh only the generated snapshot / API / contract / evidence blocks)
                           Also co-generates <ID>.openapi.json alongside the spec.
  openapi  --feature ID    write <ID>/<ID>.openapi.json (OpenAPI 3.0.3) from evidence.json without
                           touching the spec (safe to run at any time)
  check    --feature ID    mechanical checks of <ID>/<ID>.md against its evidence.json (writes nothing)

Options: --root DIR, --mcm PATH, --profile NAME, --snapshot-folder DIR,
         --features-dir DIR (default scan_assessment_reports/features; index files only),
         --specs-dir DIR (default leap-os/specs/features; evidence/spec/openapi files).
Every command prints one JSON object. Exit codes: 0 ok, 1 check failed or action needed, 2 error.
The MCM and the images are only read. See README.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import board  # noqa: E402
import facts  # noqa: E402
import features  # noqa: E402
import openapi as _openapi  # noqa: E402
import roadmap  # noqa: E402
import scaffold  # noqa: E402
import snapmap  # noqa: E402
import verify  # noqa: E402
from mcm import MCM, MCMError  # noqa: E402

DEFAULT_MCM = "scan_assessment_reports/meta_cognitive_model.json"
DEFAULT_FEATURES_DIR = "scan_assessment_reports/features"
DEFAULT_SPECS_DIR = "leap-os/specs/features"
ROADMAP_NAME = "features-roadmap.md"


def emit(obj, code=0):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")
    sys.exit(code)


def _write_atomic(path: Path, text: str) -> None:
    """Write *text* to *path* atomically: write a sibling .tmp file, then os.replace().

    Guarantees the target is never left in a partially-written state if the
    process is interrupted (Ctrl-C, disk-full, power loss, network share drop).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def write(path: Path, doc):
    _write_atomic(path, json.dumps(doc, ensure_ascii=False, indent=1) + "\n")


def load(args, root):
    path = Path(args.mcm) if Path(args.mcm).is_absolute() else root / args.mcm
    if not path.is_file():
        emit({"ok": False, "error": f"MCM not found: {args.mcm}"}, 2)
    try:
        mcm = MCM(path, args.profile)
    except MCMError as exc:
        emit({"ok": False, "error": str(exc)}, 2)
    feats, broken = features.group(mcm)
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    return mcm, feats, broken, rel


def snaps(args, root, mcm):
    out = root / args.features_dir
    try:
        folder = snapmap.resolve_folder(root, args.snapshot_folder)
        doc = snapmap.build(root, folder, mcm.screens, out / "snapshot-map.json")
    except snapmap.SnapshotError as exc:
        emit({"ok": False, "error": str(exc)}, 2)
    return doc


def refresh_readme(args, root, index, doc):
    rows = board.rows(root, args.features_dir, index, specs_dir=args.specs_dir)
    path = root / args.features_dir / "README.md"
    board.write_readme(path, board.render(index, doc, rows))
    return rows, str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def cmd_features(args, root):
    mcm, feats, broken, rel = load(args, root)
    doc = snaps(args, root, mcm)
    out = root / args.features_dir
    write(out / "snapshot-map.json", doc)
    index = facts.index(mcm, feats, broken, doc, rel)
    write(out / "features.json", index)
    # Write features-roadmap.md alongside features.json — endpoint QNs per feature.
    # Preserve any [x] ticks the user has already set.
    roadmap_path = out / ROADMAP_NAME
    existing_roadmap = roadmap_path.read_text(encoding="utf-8") if roadmap_path.is_file() else ""
    _write_atomic(roadmap_path, roadmap.build(mcm, index, existing_text=existing_roadmap))
    _, readme = refresh_readme(args, root, index, doc)
    unmatched, unconfirmed = snapmap.unmatched(doc), snapmap.unconfirmed(doc)
    emit({"ok": True, "features_file": f"{args.features_dir}/features.json",
          "roadmap": f"{args.features_dir}/{ROADMAP_NAME}",
          "snapshot_map": f"{args.features_dir}/snapshot-map.json", "readme": readme,
          "profile": mcm.profile.name, "counts": index["counts"], "snapshots": snapmap.counts(doc),
          "features": [{"id": f["id"], "screens": [s["key"] for s in f["screens"]], "depends_on": f["depends_on"],
                        "grouped_by": [{"screen": m["screen"], "rule": m["rule"], "reason": m["reason"]}
                                       for m in next(g for g in feats if g["id"] == f["id"])["membership"]],
                        "effort": f["effort"], "images": sum(len(s["images"]) for s in f["screens"])}
                       for f in index["features"]],
          "broken_dependency_cycles": broken,
          "screen_collisions": mcm.screen_collisions,  # P2: parts from different namespaces sharing a key
          "unmatched_images": unmatched,
          "unconfirmed_images": [{"image": i, **doc["images"][i]} for i in unconfirmed],
          "next": "open each unmatched and unconfirmed image, set its entry in snapshot-map.json to how=manual, "
                  "then run features again" if unmatched or unconfirmed else "run evidence --feature ID"})


def cmd_screens(args, root):
    mcm, feats, _, _ = load(args, root)
    doc = snaps(args, root, mcm)
    emit({"ok": True, "screens": board.screens(mcm, feats, doc),
          "unmatched_images": snapmap.unmatched(doc),
          "unconfirmed_images": [{"image": i, **doc["images"][i]} for i in snapmap.unconfirmed(doc)]})


def cmd_status(args, root):
    out = root / args.features_dir
    index_path, map_path = out / "features.json", out / "snapshot-map.json"
    if not index_path.is_file() or not map_path.is_file():
        emit({"ok": False, "error": "features.json not found; run `features` (or /feature-identify) first"}, 1)
    mcm_path = Path(args.mcm) if Path(args.mcm).is_absolute() else root / args.mcm
    if not mcm_path.is_file():
        emit({"ok": False, "error": f"MCM not found: {args.mcm}"}, 2)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("mcm_sha256") != hashlib.sha256(mcm_path.read_bytes()).hexdigest():
        emit({"ok": False, "error": "features.json was built from a different MCM; run `features` again"}, 1)
    doc = json.loads(map_path.read_text(encoding="utf-8"))
    rows, readme = refresh_readme(args, root, index, doc)
    emit({"ok": True, "readme": readme, "snapshots": snapmap.counts(doc),
          "unmatched_images": snapmap.unmatched(doc), "unconfirmed_images": snapmap.unconfirmed(doc),
          "features": rows, "next": board.next_feature(rows),
          "to_draft": [r["id"] for r in rows if r["status"] in ("not written", "stale")]})


def cmd_evidence(args, root):
    mcm, feats, _, rel = load(args, root)
    out = root / args.features_dir
    index_path = out / "features.json"
    if not index_path.is_file():
        emit({"ok": False, "error": "features.json not found; run `features` first"}, 1)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if index.get("mcm_sha256") != mcm.sha256:
        emit({"ok": False, "error": "features.json was built from a different MCM; run `features` again"}, 1)
    doc = snaps(args, root, mcm)
    unmatched = snapmap.unmatched(doc)
    if unmatched:
        emit({"ok": False, "error": "some snapshots are not mapped to a screen; map them in snapshot-map.json "
                                    "(how=manual) and run `features` again", "unmatched_images": unmatched}, 1)
    f = next((x for x in feats if x["id"] == args.feature), None)
    if f is None:
        emit({"ok": False, "error": f"unknown feature '{args.feature}'", "available": [x["id"] for x in feats]}, 2)
    ev = facts.evidence(mcm, f, feats, doc, rel, root)
    path = verify.paths(root, args.specs_dir, f["id"])["evidence"]
    write(path, ev)
    b = ev["backend"]
    emit({"ok": True, "evidence": str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
          "feature_id": f["id"],
          "screens": [s["key"] for s in ev["screens"]], "images": ev["images"],
          "operations": len(b["operations"]), "methods": len(ev["methods"]),
          "open_items": {k: len(v) for k, v in b["open_items"].items()},
          "depends_on": [d["id"] for d in ev["depends_on"]]})


def _write_openapi(p: dict, ev: dict, root: "Path") -> str:
    """Write <ID>.openapi.json alongside the spec; return the relative path string."""
    oa_path = p["openapi"]
    _write_atomic(oa_path, json.dumps(_openapi.build(ev), indent=2) + "\n")
    return str(oa_path.relative_to(root)) if oa_path.is_relative_to(root) else str(oa_path)


def cmd_scaffold(args, root):
    p = verify.paths(root, args.specs_dir, args.feature)
    if not p["evidence"].is_file():
        emit({"ok": False, "error": f"{p['evidence'].name} not found; run `evidence --feature {args.feature}` first"}, 1)
    if p["spec"].is_file() and not (args.force or args.sync):
        emit({"ok": False, "error": f"{p['spec'].name} exists; pass --sync to refresh the generated blocks "
                                    "or --force to replace it with a fresh skeleton"}, 1)
    if args.sync and not p["spec"].is_file():
        emit({"ok": False, "error": f"{p['spec'].name} not found; run scaffold without --sync"}, 1)
    ev = json.loads(p["evidence"].read_text(encoding="utf-8"))
    if ev.get("schema_version") != facts.SCHEMA_VERSION:
        emit({"ok": False, "error": "evidence.json is from an older tool version; run `evidence` again"}, 1)
    spec = str(p["spec"].relative_to(root)) if p["spec"].is_relative_to(root) else str(p["spec"])
    if args.sync:
        text, missing, fixed = scaffold.sync(p["spec"].read_text(encoding="utf-8"), ev)
        _write_atomic(p["spec"], text)
        oa_rel = _write_openapi(p, ev, root)
        result = verify.run(root, args.specs_dir, args.feature)
        emit({"ok": not missing, "spec": spec, "openapi": oa_rel,
              "synced": [n for n in scaffold.GENERATORS if n not in missing],
              "separators_repaired": fixed,
              "missing_headings": {n: scaffold.OWNERS[n] for n in missing},
              "errors_left": len(result["errors"]),
              "next": "run check" if not missing else "add the missing headings (or scaffold --force), then --sync"},
             0 if not missing else 1)
    _write_atomic(p["spec"], scaffold.build(ev, args.specs_dir))
    oa_rel = _write_openapi(p, ev, root)
    result = verify.run(root, args.specs_dir, args.feature)
    emit({"ok": True, "spec": spec, "openapi": oa_rel,
          "todo_left": sum(1 for e in result["errors"] if e["check"] == "todo_left"),
          "next": "replace every TODO, then run check"})


def cmd_openapi(args, root):
    """Regenerate <ID>.openapi.json from evidence.json without touching the spec."""
    p = verify.paths(root, args.specs_dir, args.feature)
    if not p["evidence"].is_file():
        emit({"ok": False, "error": f"{p['evidence'].name} not found; run `evidence --feature {args.feature}` first"}, 1)
    ev = json.loads(p["evidence"].read_text(encoding="utf-8"))
    if ev.get("schema_version") != facts.SCHEMA_VERSION:
        emit({"ok": False, "error": "evidence.json is from an older tool version; run `evidence` again"}, 1)
    oa_rel = _write_openapi(p, ev, root)
    apis = ev["backend"].get("apis", [])
    emit({"ok": True, "openapi": oa_rel,
          "feature_id": ev["feature_id"], "endpoints": len(apis),
          "paths": [f"{a['method']} {a['path']}" for a in apis],
          "next": f"open {oa_rel} in Swagger UI or import into Postman"})


def cmd_check(args, root):
    result = verify.run(root, args.specs_dir, args.feature)
    emit(result, 0 if result["ok"] else 1)


def cmd_roadmap(args, root):
    """(Re-)generate features-roadmap.md from the current features.json + MCM."""
    out = root / args.features_dir
    index_path = out / "features.json"
    if not index_path.is_file():
        emit({"ok": False, "error": "features.json not found; run `features` first"}, 1)
    mcm_path = Path(args.mcm) if Path(args.mcm).is_absolute() else root / args.mcm
    if not mcm_path.is_file():
        emit({"ok": False, "error": f"MCM not found: {args.mcm}"}, 2)
    index = json.loads(index_path.read_text(encoding="utf-8"))
    import hashlib
    if index.get("mcm_sha256") != hashlib.sha256(mcm_path.read_bytes()).hexdigest():
        emit({"ok": False, "error": "features.json was built from a different MCM; run `features` again"}, 1)
    try:
        mcm = MCM(mcm_path, args.profile)
    except MCMError as exc:
        emit({"ok": False, "error": str(exc)}, 2)
    roadmap_path = out / ROADMAP_NAME
    existing_roadmap = roadmap_path.read_text(encoding="utf-8") if roadmap_path.is_file() else ""
    _write_atomic(roadmap_path, roadmap.build(mcm, index, existing_text=existing_roadmap))
    rel = str(roadmap_path.relative_to(root)) if roadmap_path.is_relative_to(root) else str(roadmap_path)
    # Count total endpoint QNs across all features
    total_qns = sum(
        len(roadmap.endpoint_qns(mcm, f))
        for f in index.get("features", [])
    )
    emit({"ok": True, "roadmap": rel,
          "features": len(index.get("features", [])),
          "total_endpoint_qns": total_qns,
          "next": f"tick a checkbox in {ROADMAP_NAME} once the corresponding API endpoint is implemented"})


def main():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".")
    common.add_argument("--mcm", default=DEFAULT_MCM)
    common.add_argument("--profile", default="auto", help="stack profile (default: auto)")
    common.add_argument("--snapshot-folder", default=None, help="default: the only **/snapshots/ folder")
    common.add_argument("--features-dir", default=DEFAULT_FEATURES_DIR)
    common.add_argument("--specs-dir", default=DEFAULT_SPECS_DIR)
    ap = argparse.ArgumentParser(prog="feature_facts", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("features", "screens", "status", "roadmap"):
        sub.add_parser(name, parents=[common])
    for name in ("evidence", "check", "scaffold", "openapi"):
        sub.add_parser(name, parents=[common]).add_argument("--feature", required=True)
    mode = sub.choices["scaffold"].add_mutually_exclusive_group()
    mode.add_argument("--force", action="store_true", help="replace an existing spec")
    mode.add_argument("--sync", action="store_true", help="refresh only the generated blocks of an existing spec")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    {"features": cmd_features, "screens": cmd_screens, "status": cmd_status, "evidence": cmd_evidence,
     "scaffold": cmd_scaffold, "check": cmd_check, "roadmap": cmd_roadmap,
     "openapi": cmd_openapi}[args.command](args, root)


if __name__ == "__main__":
    main()
