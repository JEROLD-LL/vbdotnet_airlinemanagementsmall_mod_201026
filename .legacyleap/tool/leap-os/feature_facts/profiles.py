"""Load stack profiles used to interpret language-neutral MCM records.

Profiles contain recognition rules only. They do not add project facts. `auto` selects the
highest-scoring profile from MCM language/path/name evidence and falls back to `generic-mcm`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


class ProfileError(Exception):
    pass


class Profile:
    def __init__(self, data, path):
        self.data, self.path = data, path
        self.name = data["name"]
        self._regex_cache: dict = {}  # P1: cache compiled regexes — same patterns reused hundreds of times per MCM load

    def get(self, key, default=None):
        value = self.data
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def regex(self, key, default=r"(?!x)x"):
        pattern = self.get(key, default)
        if pattern not in self._regex_cache:
            self._regex_cache[pattern] = re.compile(pattern, re.I)
        return self._regex_cache[pattern]

    def matches(self, key, text):
        return bool(self.regex(key).search(str(text or "")))


def _folder():
    return Path(__file__).resolve().parent / "profiles"


def available():
    out = {}
    for path in sorted(_folder().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProfileError(f"profile is not valid UTF-8 JSON ({path}): {exc}")
        if not isinstance(data, dict) or not data.get("name"):
            raise ProfileError(f"profile needs a non-empty 'name': {path}")
        if data["name"] in out:
            raise ProfileError(f"duplicate profile name '{data['name']}'")
        out[data["name"]] = Profile(data, path)
    if "generic-mcm" not in out:
        raise ProfileError("required fallback profile 'generic-mcm' is missing")
    return out


def _score(profile, parts):
    detectors = profile.get("detect", {})
    required = detectors.get("required_any", [])
    evidence = "\n".join(str((p.get("identity") or {}).get(field) or "")
                         for p in parts for field in ("language", "file_path", "qualified_name"))
    if required and not any(re.search(pattern, evidence, re.I | re.M) for pattern in required):
        return 0
    score = 0
    for p in parts:
        identity = p.get("identity") or {}
        values = {
            "language": identity.get("language"),
            "file_path": identity.get("file_path"),
            "qualified_name": identity.get("qualified_name"),
        }
        for field, patterns in detectors.items():
            if field == "required_any":
                continue
            value = str(values.get(field) or "")
            if any(re.search(pattern, value, re.I) for pattern in patterns):
                score += 1
    return score


def select(parts, requested="auto"):
    profiles = available()
    if requested != "auto":
        if requested not in profiles:
            raise ProfileError(f"unknown profile '{requested}'; choose from: {', '.join(sorted(profiles))}")
        return profiles[requested]
    ranked = sorted(
        ((-_score(p, parts), -int(p.get("priority", 0)), name, p)
         for name, p in profiles.items() if name != "generic-mcm")
    )
    return ranked[0][3] if ranked and ranked[0][0] < 0 else profiles["generic-mcm"]


def summary():
    return [{"name": p.name, "description": p.get("description", ""),
             "path": str(p.path.relative_to(Path(__file__).resolve().parent))}
            for p in available().values()]
