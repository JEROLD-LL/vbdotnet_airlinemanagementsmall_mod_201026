#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

print_prerequisite_help() {
  local reason="$1"

  cat >&2 <<EOF
ERROR: $reason

Recommended fresh-machine setup:

  conda create -n legacyleap-video python=3.11 -y
  conda activate legacyleap-video
  conda install -c conda-forge ffmpeg pillow -y

Then rerun:

  .legacyleap/scripts/leap-os/video-screenshot-extractor/run.sh

Notes:
- ffmpeg and ffprobe are provided by the conda-forge ffmpeg package.
- Pillow is the Python image dependency used for crop previews and dedupe.
- If you already have a preferred Python interpreter, set LEGACYLEAP_SCREENSHOT_PYTHON=/path/to/python.
EOF
}

PYTHON_BIN="${LEGACYLEAP_SCREENSHOT_PYTHON:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    print_prerequisite_help "Python was not found on PATH."
    exit 1
  fi
elif [ ! -x "$PYTHON_BIN" ]; then
  print_prerequisite_help "LEGACYLEAP_SCREENSHOT_PYTHON is set but is not executable: $PYTHON_BIN"
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  print_prerequisite_help "ffmpeg was not found on PATH."
  exit 1
fi

if ! command -v ffprobe >/dev/null 2>&1; then
  print_prerequisite_help "ffprobe was not found on PATH."
  exit 1
fi

if ! "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
from PIL import Image
PY
then
  print_prerequisite_help "Python package Pillow was not found for interpreter: $PYTHON_BIN"
  exit 1
fi

cd "$REPO_ROOT"
exec "$PYTHON_BIN" "$SCRIPT_DIR/extract_unique_screenshots.py" "$@"
