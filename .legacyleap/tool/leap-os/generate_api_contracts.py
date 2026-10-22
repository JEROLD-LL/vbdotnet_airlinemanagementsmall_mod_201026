#!/usr/bin/env python3
"""
Blocking runner for `take-leap generate-api-contracts` via conda env `legacyleap`.

- Runs synchronously (waits for subprocess to finish).
- Writes exactly one JSON object to stdout — parse this for success/failure and logs.
- Exits 0 iff generation succeeded and fragment check passed (unless SKIP_FRAGMENT_CHECK=1).

Installed paths (after project-install, same file copied to both):
  .legacyleap/tool/leap-os/generate_api_contracts.py   (Bash / agents)
  .opencode/tools/generate_api_contracts.py            (OpenCode; beside the .ts wrapper)

Invoke from the agent with Bash, e.g.:
  python3 .legacyleap/tool/leap-os/generate_api_contracts.py .

OpenCode: after project-install, call the **`generate-api-contracts`** tool; it runs
`.opencode/tools/generate_api_contracts.py` via `python3` (see
https://opencode.ai/docs/custom-tools/#examples).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import shutil
import subprocess
from pathlib import Path

MAX_STREAM_CHARS = 120_000

# Run in login bash so conda activate works (not `conda run`).
CONDA_ENV = "legacyleap"
SHELL_SCRIPT = (
    "set -e; "
    'eval "$(conda shell.bash hook 2>/dev/null)" || { echo "conda shell.bash hook failed" >&2; exit 127; }; '
    f"conda activate {CONDA_ENV}; "
    "take-leap generate-api-contracts"
)
CMD = ["bash", "-lc", SHELL_SCRIPT]


def _truncate(s: str) -> tuple[str, bool]:
    if len(s) <= MAX_STREAM_CHARS:
        return s, False
    return s[:MAX_STREAM_CHARS], True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run take-leap generate-api-contracts and report JSON result.",
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (where modernize/ lives). Default: current directory.",
    )
    args = parser.parse_args()
    root = Path(args.project_root).resolve()

    result: dict = {
        "ok": False,
        "project_root": str(root),
        "command": SHELL_SCRIPT,
        "command_argv": CMD,
        "conda_on_path": shutil.which("conda") is not None,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "stdout_truncated": False,
        "stderr_truncated": False,
        "fragment_count": 0,
        "fragment_paths": [],
        "error": None,
    }

    if not root.is_dir():
        result["error"] = f"project_root is not a directory: {root}"
        print(json.dumps(result, indent=2))
        return 1

    if not shutil.which("conda"):
        result["error"] = "conda not found in PATH"
        print(json.dumps(result, indent=2))
        return 127

    proc = subprocess.run(
        CMD,
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=None,
    )

    stdout, st = _truncate(proc.stdout or "")
    stderr, st2 = _truncate(proc.stderr or "")
    result["stdout"] = stdout
    result["stderr"] = stderr
    result["stdout_truncated"] = st
    result["stderr_truncated"] = st2
    result["exit_code"] = proc.returncode

    if proc.returncode != 0:
        result["error"] = f"take-leap exited with code {proc.returncode}"
        print(json.dumps(result, indent=2))
        return 1

    frag_dir = root / "modernize" / "target" / "endpoints"
    pattern = str(frag_dir / "*.json")
    paths = sorted(glob.glob(pattern))
    rel_paths = []
    for p in paths:
        rp = Path(p)
        try:
            rel_paths.append(str(rp.relative_to(root)))
        except ValueError:
            rel_paths.append(str(rp))
    result["fragment_paths"] = rel_paths
    result["fragment_count"] = len(paths)

    skip_check = os.environ.get("SKIP_FRAGMENT_CHECK", "") == "1"
    if skip_check:
        result["ok"] = True
        result["error"] = None
        print(json.dumps(result, indent=2))
        return 0

    if result["fragment_count"] == 0:
        result["error"] = (
            "CLI exited 0 but no *.json under modernize/target/endpoints/ (set SKIP_FRAGMENT_CHECK=1 to override)"
        )
        print(json.dumps(result, indent=2))
        return 2

    result["ok"] = True
    result["error"] = None
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        err = {"ok": False, "error": f"unexpected: {e!s}"}
        print(json.dumps(err, indent=2))
        raise SystemExit(1)
