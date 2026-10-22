#!/usr/bin/env python3
"""Blocking wrapper for ``take-leap transpile`` in the legacyleap conda env.

Config extensions are supplied by the ``legacy-config-inspector`` agent.
This tool does not inspect or auto-detect configuration files.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

CONDA_ENV = "legacyleap"
MAX_STREAM_CHARS = 120_000
SHELL_SCRIPT = (
    "set -e; "
    'eval "$(conda shell.bash hook 2>/dev/null)" || '
    '{ echo "conda shell.bash hook failed" >&2; exit 127; }; '
    f"conda activate {CONDA_ENV}; "
    'exec take-leap transpile "$@"'
)


def _truncate(value: str) -> tuple[str, bool]:
    if len(value) <= MAX_STREAM_CHARS:
        return value, False
    return value[:MAX_STREAM_CHARS], True


def _metadata(root: Path) -> dict:
    for path in (root / ".legacyleap" / "metadata.json", root / "metadata.json"):
        if path.is_file():
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                return value if isinstance(value, dict) else {}
            except (OSError, json.JSONDecodeError):
                return {}
    return {}


def _legacy_root(root: Path) -> Path:
    configured = _metadata(root).get("legacy_code")
    if isinstance(configured, str) and configured.strip():
        path = Path(configured).expanduser()
        return path.resolve() if path.is_absolute() else (root / path).resolve()
    return (root / "legacy_code").resolve()


def normalize_extensions(values: list[str]) -> list[str]:
    normalized: set[str] = set()
    for value in values:
        for item in value.split(","):
            extension = item.strip().lower()
            if not extension:
                continue
            if not extension.startswith("."):
                extension = f".{extension}"
            if not re.fullmatch(r"\.[a-z0-9][a-z0-9._-]*", extension):
                raise ValueError(f"invalid config extension: {item!r}")
            normalized.add(extension)
    return sorted(normalized)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run take-leap transpile for one qualified name.",
    )
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument(
        "--qualified-name-pattern",
        "--qualified-name",
        dest="qualified_name",
        required=True,
        help="Exact qualified name to pass to take-leap.",
    )
    parser.add_argument(
        "--legacy-config-files",
        action="append",
        default=[],
        metavar="EXTENSIONS",
        help="Comma-separated config extensions from legacy-config-inspector. Repeatable.",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result = {
        "ok": False,
        "project_root": str(root),
        "qualified_name": args.qualified_name,
        "legacy_root": None,
        "legacy_config_extensions": [],
        "config_evidence_files": [],
        "command_argv": [],
        "conda_on_path": shutil.which("conda") is not None,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "stdout_truncated": False,
        "stderr_truncated": False,
        "error": None,
    }

    if not root.is_dir():
        result["error"] = f"project_root is not a directory: {root}"
        print(json.dumps(result, indent=2))
        return 1
    if not args.qualified_name.strip():
        result["error"] = "qualified name must not be empty"
        print(json.dumps(result, indent=2))
        return 1
    if not shutil.which("conda"):
        result["error"] = "conda not found in PATH"
        print(json.dumps(result, indent=2))
        return 127

    legacy_root = _legacy_root(root)
    result["legacy_root"] = str(legacy_root)
    try:
        extensions = normalize_extensions(args.legacy_config_files)
    except ValueError as exc:
        result["error"] = str(exc)
        print(json.dumps(result, indent=2))
        return 1

    result["legacy_config_extensions"] = extensions
    result["config_evidence_files"] = []

    take_leap_args = [
        "--qualified-name-pattern",
        args.qualified_name.strip(),
    ]
    if extensions:
        take_leap_args.extend(["--legacy-config-files", ",".join(extensions)])

    command = ["bash", "-lc", SHELL_SCRIPT, "take-leap", *take_leap_args]
    result["command_argv"] = command
    proc = subprocess.run(
        command,
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=None,
        env=os.environ.copy(),
    )
    stdout, stdout_truncated = _truncate(proc.stdout or "")
    stderr, stderr_truncated = _truncate(proc.stderr or "")
    result.update(
        {
            "exit_code": proc.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_truncated": stdout_truncated,
            "stderr_truncated": stderr_truncated,
        }
    )
    if proc.returncode != 0:
        result["error"] = f"take-leap exited with code {proc.returncode}"
        print(json.dumps(result, indent=2))
        return 1

    result["ok"] = True
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"unexpected: {exc!s}"}, indent=2))
        raise SystemExit(1)
