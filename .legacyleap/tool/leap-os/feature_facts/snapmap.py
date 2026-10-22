"""Snapshot map: which screen each UI snapshot image shows.

Images are matched to MCM screen keys by file name: the normalized name ("name"), else the words of
the name ("words", e.g. AdminLogin -> Login when "Admin" names no other screen). Entries marked
"manual" (set by an agent or a person after looking at the image) are kept as they are on every
rebuild. The images themselves are never interpreted here; agents open them directly.
"""

from __future__ import annotations

import difflib
import json
import os
import re
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
PRUNE = {".git", "node_modules", ".venv", "venv", "__pycache__", "bin", "obj", "dist", "build"}
FUZZY = 0.85


class SnapshotError(Exception):
    pass


def discover(root: Path):
    found = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in PRUNE and not d.startswith("."))
        if os.path.basename(dirpath).lower() == "snapshots":
            found.append(Path(dirpath))
            dirnames[:] = []
    return found


def resolve_folder(root: Path, folder: str | None):
    if folder:
        path = Path(folder) if Path(folder).is_absolute() else root / folder
        if not path.is_dir():
            raise SnapshotError(f"snapshot folder not found: {folder}")
        return path
    found = discover(root)
    if len(found) > 1:
        raise SnapshotError("several snapshot folders found; pass --snapshot-folder: "
                            + ", ".join(str(f.relative_to(root)) for f in found))
    return found[0] if found else None


def _norm(name):
    return re.sub(r"\d+$", "", re.sub(r"[^a-z0-9]", "", name.lower()))


def words(name):
    name = re.sub(r"\d+", " ", str(name))
    return [w.lower() for w in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+", name)]


def match(stem, screens):
    """Screen key for an image file stem: exact normalized name first, then a close spelling."""
    target = _norm(stem)
    by_norm = {_norm(k): k for k in screens}
    if target in by_norm:
        return by_norm[target]
    close = difflib.get_close_matches(target, list(by_norm), n=1, cutoff=FUZZY)
    return by_norm[close[0]] if close else None


def match_words(stem, screens):
    """(screen key, note) when the file name's words point at exactly one screen, else None.

    Either the name contains one screen's words and its other words name no other screen
    (AdminLogin -> Login), or the name's words appear in exactly one screen key (Email -> EmailWeb).
    """
    have = set(words(stem))
    if not have:
        return None
    keys = {k: set(words(k)) for k in screens}
    inside = [k for k, w in keys.items() if w and w <= have]
    if inside:
        best = max(len(keys[k]) for k in inside)
        top = [k for k in inside if len(keys[k]) == best]
        rest = have - keys[top[0]]
        if len(top) == 1 and not any(rest & w for k, w in keys.items() if k != top[0]):
            extra = f"; '{' '.join(sorted(rest))}' names no other screen" if rest else ""
            return top[0], f"file name words contain screen '{top[0]}'{extra}"
        return None
    around = [k for k, w in keys.items() if have < w]
    if len(around) == 1:
        return around[0], f"file name words appear only in screen '{around[0]}'"
    return None


def build(root: Path, folder: Path | None, screens, map_path: Path):
    old = {}
    if map_path.is_file():
        try:
            old = json.loads(map_path.read_text(encoding="utf-8")).get("images", {})
        except json.JSONDecodeError as exc:
            raise SnapshotError(f"{map_path.name} is not valid JSON: {exc}")
    images = {}
    if folder is not None:
        for p in sorted(folder.rglob("*")):
            if not (p.is_file() and p.suffix.lower() in IMAGE_EXTS):
                continue
            rel = str(p.relative_to(root))
            prev = old.get(rel) or {}
            if prev.get("how") == "manual":
                if prev.get("screen") is not None and prev["screen"] not in screens:
                    raise SnapshotError(f"{map_path.name}: '{rel}' names unknown screen '{prev['screen']}'")
                images[rel] = prev
                continue
            key = match(p.stem, screens)
            if key:
                images[rel] = {"screen": key, "how": "name"}
                continue
            hit = match_words(p.stem, screens)
            images[rel] = ({"screen": hit[0], "how": "words", "note": hit[1]} if hit
                           else {"screen": None, "how": "unmatched"})
    return {
        "schema_version": "1",
        "snapshot_folder": str(folder.relative_to(root)) if folder else None,
        "how_to_edit": "After looking at an image set {\"screen\": \"<screen key or null>\", \"how\": \"manual\", "
                       "\"note\": \"<what identifies it>\"}. Manual entries are kept on rebuild.",
        "screens": sorted(screens),
        "images": images,
    }


def unmatched(doc):
    return sorted(img for img, e in doc["images"].items() if e.get("how") == "unmatched")


def unconfirmed(doc):
    """Images matched by file-name words only; an agent confirms them by looking."""
    return sorted(img for img, e in doc["images"].items() if e.get("how") == "words")


def counts(doc):
    out = {"name": 0, "words": 0, "manual": 0, "unmatched": 0}
    for e in doc["images"].values():
        out[e.get("how", "unmatched")] = out.get(e.get("how", "unmatched"), 0) + 1
    return out


def images_of(doc, key):
    return sorted(img for img, e in doc["images"].items() if e.get("screen") == key)
