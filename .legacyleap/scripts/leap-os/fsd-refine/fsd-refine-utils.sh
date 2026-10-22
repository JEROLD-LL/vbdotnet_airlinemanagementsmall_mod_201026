#!/usr/bin/env bash
set -euo pipefail

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage:
  fsd-refine-utils.sh latest [--fsd-root <path>]
  fsd-refine-utils.sh create-next [--fsd-root <path>] [--source <version-dir>]
  fsd-refine-utils.sh normalize-report --output-dir <dir> --report <path>
  fsd-refine-utils.sh assert-fresh-evaluation --report <path> --state <path> --started-at <epoch>
  fsd-refine-utils.sh assert-updated-file --file <path> --started-at <epoch> [--allow-unchanged]
  fsd-refine-utils.sh parse-score --report <path> [--state <path>]
  fsd-refine-utils.sh score-ok --score <score> [--threshold <score>]

Purpose:
  Deterministic helper for /fsd-refine. It resolves versioned FSD folders,
  copies the source FSD into the next v_N folder, owns evaluation output paths,
  and parses the final evaluation score.
USAGE
}

abs_path() {
  local path="$1"
  if [ -d "$path" ]; then
    (cd "$path" && pwd -P)
  else
    local dir
    local base
    dir=$(dirname "$path")
    base=$(basename "$path")
    (cd "$dir" 2>/dev/null && printf '%s/%s\n' "$(pwd -P)" "$base")
  fi
}

emit_var() {
  local name="$1"
  local value="$2"
  printf '%s=%q\n' "$name" "$value"
}

resolve_fsd_root() {
  local explicit="${1:-}"
  if [ -n "$explicit" ]; then
    abs_path "$explicit"
    return
  fi

  if [ -f ".legacyleap/metadata.json" ]; then
    python3 - <<'PY'
import json
import os

with open(".legacyleap/metadata.json", "r", encoding="utf-8") as handle:
    metadata = json.load(handle)

comprehend = metadata.get("comprehend") or os.path.join(os.getcwd(), "comprehend")
if not os.path.isabs(comprehend):
    comprehend = os.path.abspath(comprehend)

print(os.path.join(comprehend, "functional_doc"))
PY
  else
    printf '%s/comprehend/functional_doc\n' "$(pwd -P)"
  fi
}

version_number_from_path() {
  local path="$1"
  local base
  base=$(basename "${path%/}")
  if [[ "$base" =~ ^v_([0-9]+)$ ]]; then
    printf '%s\n' "$((10#${BASH_REMATCH[1]}))"
  else
    die "Version folder must be named v_N, got: $base"
  fi
}

latest_version_record() {
  local root="$1"
  [ -d "$root" ] || die "FSD root does not exist: $root"

  local latest_number=-1
  local latest_path=""
  local candidate
  local base
  local number

  shopt -s nullglob
  for candidate in "$root"/v_*; do
    [ -d "$candidate" ] || continue
    base=$(basename "$candidate")
    if [[ "$base" =~ ^v_([0-9]+)$ ]]; then
      number=$((10#${BASH_REMATCH[1]}))
      if [ "$number" -gt "$latest_number" ]; then
        latest_number="$number"
        latest_path="$candidate"
      fi
    fi
  done
  shopt -u nullglob

  [ "$latest_number" -ge 0 ] || die "No version folders named v_N found in: $root"
  printf '%s\t%s\n' "$latest_number" "$(abs_path "$latest_path")"
}

find_fsd_markdown() {
  local version_path="$1"
  local preferred="$version_path/Latest_FSD_Document/Latest_fsd.md"
  local found=""

  if [ -f "$preferred" ]; then
    abs_path "$preferred"
    return
  fi

  found=$(
    find "$version_path" -maxdepth 4 -type f \
      \( -iname 'Latest_fsd.md' \
        -o -iname 'Latest_FSD*.md' \
        -o -iname '*functional*spec*.md' \
        -o -iname '*functional*document*.md' \
        -o -iname '*fsd*.md' \) \
      ! -iname '*proposed*' \
      ! -iname '*addition*' \
      ! -iname '*evaluation*' \
      ! -iname '*report*' \
      ! -iname '*quality*' \
      ! -iname '*state*' \
      ! -path '*/evaluations/*' 2>/dev/null |
      sort |
      head -n 1 || true
  )

  [ -n "$found" ] || die "No FSD markdown file found under: $version_path"
  abs_path "$found"
}

cmd_latest() {
  local fsd_root_arg=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --fsd-root)
        fsd_root_arg="${2:-}"
        [ -n "$fsd_root_arg" ] || die "--fsd-root requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for latest: $1"
        ;;
    esac
  done

  local fsd_root
  local latest_record
  local latest_number
  local latest_path
  local latest_markdown
  local latest_evaluation_dir

  fsd_root=$(resolve_fsd_root "$fsd_root_arg")
  latest_record=$(latest_version_record "$fsd_root")
  latest_number=${latest_record%%$'\t'*}
  latest_path=${latest_record#*$'\t'}
  latest_markdown=$(find_fsd_markdown "$latest_path")
  latest_evaluation_dir="$fsd_root/evaluations/v_$latest_number"
  mkdir -p "$latest_evaluation_dir"
  latest_evaluation_dir=$(abs_path "$latest_evaluation_dir")

  emit_var "FSD_ROOT" "$fsd_root"
  emit_var "LATEST_VERSION_NUMBER" "$latest_number"
  emit_var "LATEST_VERSION" "v_$latest_number"
  emit_var "LATEST_VERSION_PATH" "$latest_path"
  emit_var "LATEST_FSD_MARKDOWN" "$latest_markdown"
  emit_var "LATEST_EVALUATION_DIR" "$latest_evaluation_dir"
  emit_var "LATEST_EVALUATION_REPORT_PATH" "$latest_evaluation_dir/evaluation-report.md"
  emit_var "LATEST_EVALUATION_STATE_PATH" "$latest_evaluation_dir/fsd-evaluation-state.json"
}

cmd_create_next() {
  local fsd_root_arg=""
  local source_arg=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --fsd-root)
        fsd_root_arg="${2:-}"
        [ -n "$fsd_root_arg" ] || die "--fsd-root requires a value"
        shift 2
        ;;
      --source)
        source_arg="${2:-}"
        [ -n "$source_arg" ] || die "--source requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for create-next: $1"
        ;;
    esac
  done

  local fsd_root
  fsd_root=$(resolve_fsd_root "$fsd_root_arg")
  [ -d "$fsd_root" ] || die "FSD root does not exist: $fsd_root"

  local latest_record
  local latest_number
  latest_record=$(latest_version_record "$fsd_root")
  latest_number=${latest_record%%$'\t'*}

  local source_path
  if [ -n "$source_arg" ]; then
    [ -d "$source_arg" ] || die "Source version folder does not exist: $source_arg"
    source_path=$(abs_path "$source_arg")
  else
    source_path=${latest_record#*$'\t'}
  fi

  local source_parent
  source_parent=$(abs_path "$(dirname "$source_path")")
  [ "$source_parent" = "$fsd_root" ] || die "Source version must be a direct child of FSD root: $fsd_root"

  local source_number
  source_number=$(version_number_from_path "$source_path")

  local next_number
  local next_path
  next_number=$((latest_number + 1))
  next_path="$fsd_root/v_$next_number"
  [ ! -e "$next_path" ] || die "Next version path already exists: $next_path"

  cleanup_incomplete_next_version() {
    local status=$?
    trap - ERR
    if [ -n "${next_path:-}" ] && [[ "$next_path" == "$fsd_root"/v_[0-9]* ]] && [ -d "$next_path" ]; then
      rm -rf -- "$next_path"
    fi
    exit "$status"
  }

  trap cleanup_incomplete_next_version ERR
  mkdir -p "$next_path"
  cp -a "$source_path"/. "$next_path"/

  local next_markdown
  local evaluation_dir
  local evaluation_report
  local evaluation_state
  next_path=$(abs_path "$next_path")
  next_markdown=$(find_fsd_markdown "$next_path")
  evaluation_dir="$fsd_root/evaluations/v_$next_number"
  mkdir -p "$evaluation_dir"
  trap - ERR

  evaluation_dir=$(abs_path "$evaluation_dir")
  evaluation_report="$evaluation_dir/evaluation-report.md"
  evaluation_state="$evaluation_dir/fsd-evaluation-state.json"

  emit_var "FSD_ROOT" "$fsd_root"
  emit_var "SOURCE_VERSION_NUMBER" "$source_number"
  emit_var "SOURCE_VERSION" "v_$source_number"
  emit_var "SOURCE_VERSION_PATH" "$source_path"
  emit_var "NEXT_VERSION_NUMBER" "$next_number"
  emit_var "NEXT_VERSION" "v_$next_number"
  emit_var "NEXT_VERSION_PATH" "$next_path"
  emit_var "NEXT_FSD_MARKDOWN" "$next_markdown"
  emit_var "EVALUATION_DIR" "$evaluation_dir"
  emit_var "EVALUATION_REPORT_PATH" "$evaluation_report"
  emit_var "EVALUATION_STATE_PATH" "$evaluation_state"
}

cmd_normalize_report() {
  local output_dir=""
  local report_path=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --output-dir)
        output_dir="${2:-}"
        [ -n "$output_dir" ] || die "--output-dir requires a value"
        shift 2
        ;;
      --report)
        report_path="${2:-}"
        [ -n "$report_path" ] || die "--report requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for normalize-report: $1"
        ;;
    esac
  done

  [ -n "$output_dir" ] || die "normalize-report requires --output-dir"
  [ -n "$report_path" ] || die "normalize-report requires --report"
  mkdir -p "$(dirname "$report_path")"

  if [ -f "$report_path" ]; then
    abs_path "$report_path"
    return
  fi

  local default_report="$output_dir/fsd-evaluation-report.md"
  if [ -f "$default_report" ]; then
    cp "$default_report" "$report_path"
    abs_path "$report_path"
    return
  fi

  die "Evaluation report not found at $report_path or $default_report"
}

cmd_assert_fresh_evaluation() {
  local report_path=""
  local state_path=""
  local started_at=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --report)
        report_path="${2:-}"
        [ -n "$report_path" ] || die "--report requires a value"
        shift 2
        ;;
      --state)
        state_path="${2:-}"
        [ -n "$state_path" ] || die "--state requires a value"
        shift 2
        ;;
      --started-at)
        started_at="${2:-}"
        [ -n "$started_at" ] || die "--started-at requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for assert-fresh-evaluation: $1"
        ;;
    esac
  done

  [ -n "$report_path" ] || die "assert-fresh-evaluation requires --report"
  [ -n "$state_path" ] || die "assert-fresh-evaluation requires --state"
  [ -n "$started_at" ] || die "assert-fresh-evaluation requires --started-at"

  python3 - "$report_path" "$state_path" "$started_at" <<'PY'
import json
import os
import sys

report_path, state_path, started_raw = sys.argv[1], sys.argv[2], sys.argv[3]

try:
    started_at = float(started_raw)
except ValueError:
    print(f"ERROR: invalid --started-at value: {started_raw}", file=sys.stderr)
    sys.exit(1)

for label, path in (("report", report_path), ("state", state_path)):
    if not os.path.isfile(path):
        print(f"ERROR: evaluation {label} not found: {path}", file=sys.stderr)
        sys.exit(1)
    if os.path.getsize(path) == 0:
        print(f"ERROR: evaluation {label} is empty: {path}", file=sys.stderr)
        sys.exit(1)

report_mtime = os.path.getmtime(report_path)
state_mtime = os.path.getmtime(state_path)

if report_mtime < started_at:
    print(
        "ERROR: evaluation report is stale; it was not updated "
        f"after run start ({started_raw}): {report_path}",
        file=sys.stderr,
    )
    sys.exit(1)

if state_mtime < started_at:
    print(
        "ERROR: evaluation state is stale; it was not updated "
        f"after run start ({started_raw}): {state_path}",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    with open(state_path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
except Exception as exc:
    print(f"ERROR: could not parse evaluation state JSON: {exc}", file=sys.stderr)
    sys.exit(1)

score = state.get("overall_score")
if score is None:
    print("ERROR: evaluation state missing overall_score", file=sys.stderr)
    sys.exit(1)

try:
    score = float(score)
except (TypeError, ValueError):
    print(f"ERROR: evaluation state overall_score is not numeric: {score}", file=sys.stderr)
    sys.exit(1)

if not 0 <= score <= 10:
    print(f"ERROR: evaluation state overall_score out of range: {score}", file=sys.stderr)
    sys.exit(1)

print("fresh")
PY
}

cmd_assert_updated_file() {
  local file_path=""
  local started_at=""
  local allow_unchanged=false

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --file)
        file_path="${2:-}"
        [ -n "$file_path" ] || die "--file requires a value"
        shift 2
        ;;
      --started-at)
        started_at="${2:-}"
        [ -n "$started_at" ] || die "--started-at requires a value"
        shift 2
        ;;
      --allow-unchanged)
        allow_unchanged=true
        shift
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for assert-updated-file: $1"
        ;;
    esac
  done

  [ -n "$file_path" ] || die "assert-updated-file requires --file"
  [ -n "$started_at" ] || die "assert-updated-file requires --started-at"

  python3 - "$file_path" "$started_at" "$allow_unchanged" <<'PY'
import os
import sys

file_path, started_raw, allow_raw = sys.argv[1], sys.argv[2], sys.argv[3]
allow_unchanged = allow_raw.lower() == "true"

try:
    started_at = float(started_raw)
except ValueError:
    print(f"ERROR: invalid --started-at value: {started_raw}", file=sys.stderr)
    sys.exit(1)

if not os.path.isfile(file_path):
    print(f"ERROR: file not found: {file_path}", file=sys.stderr)
    sys.exit(1)

if os.path.getsize(file_path) == 0:
    print(f"ERROR: file is empty: {file_path}", file=sys.stderr)
    sys.exit(1)

if not allow_unchanged and os.path.getmtime(file_path) < started_at:
    print(f"ERROR: file was not updated after run start: {file_path}", file=sys.stderr)
    sys.exit(1)

print("updated" if os.path.getmtime(file_path) >= started_at else "unchanged-allowed")
PY
}

cmd_parse_score() {
  local report_path=""
  local state_path=""

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --report)
        report_path="${2:-}"
        [ -n "$report_path" ] || die "--report requires a value"
        shift 2
        ;;
      --state)
        state_path="${2:-}"
        [ -n "$state_path" ] || die "--state requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for parse-score: $1"
        ;;
    esac
  done

  [ -n "$report_path" ] || die "parse-score requires --report"

  python3 - "$report_path" "$state_path" <<'PY'
import json
import os
import re
import sys

report_path = sys.argv[1]
state_path = sys.argv[2] if len(sys.argv) > 2 else ""

def emit(value):
    try:
        score = float(value)
    except (TypeError, ValueError):
        return False
    if 0 <= score <= 10:
        print(f"{score:g}")
        return True
    return False

if state_path and os.path.isfile(state_path):
    with open(state_path, "r", encoding="utf-8") as handle:
        state = json.load(handle)
    for key in ("overall_score", "final_score", "score"):
        if key in state and emit(state[key]):
            sys.exit(0)

if os.path.isfile(report_path):
    with open(report_path, "r", encoding="utf-8", errors="replace") as handle:
        report = handle.read()
else:
    print(f"ERROR: report not found: {report_path}", file=sys.stderr)
    sys.exit(1)

patterns = [
    r"Overall\s+Score\s*:?\s*\*{0,2}\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10",
    r"Final\s+evaluation\s+score\s*:?\s*\*{0,2}\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10",
    r"\|\s*\*{0,2}Overall\*{0,2}\s*\|\s*\*{0,2}([0-9]+(?:\.[0-9]+)?)\*{0,2}\s*\|",
    r'"overall_score"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
]

for pattern in patterns:
    match = re.search(pattern, report, flags=re.IGNORECASE)
    if match and emit(match.group(1)):
        sys.exit(0)

print(f"ERROR: could not parse an overall score from {report_path}", file=sys.stderr)
sys.exit(1)
PY
}

cmd_score_ok() {
  local score=""
  local threshold="9"

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --score)
        score="${2:-}"
        [ -n "$score" ] || die "--score requires a value"
        shift 2
        ;;
      --threshold)
        threshold="${2:-}"
        [ -n "$threshold" ] || die "--threshold requires a value"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        die "Unknown argument for score-ok: $1"
        ;;
    esac
  done

  [ -n "$score" ] || die "score-ok requires --score"

  python3 - "$score" "$threshold" <<'PY'
import re
import sys

def to_score(raw):
    match = re.search(r"[0-9]+(?:\.[0-9]+)?", raw)
    if not match:
        raise ValueError(raw)
    return float(match.group(0))

score = to_score(sys.argv[1])
threshold = to_score(sys.argv[2])
sys.exit(0 if score >= threshold else 1)
PY
}

main() {
  local command="${1:-}"
  [ -n "$command" ] || {
    usage
    exit 1
  }
  shift || true

  case "$command" in
    latest)
      cmd_latest "$@"
      ;;
    create-next)
      cmd_create_next "$@"
      ;;
    normalize-report)
      cmd_normalize_report "$@"
      ;;
    assert-fresh-evaluation)
      cmd_assert_fresh_evaluation "$@"
      ;;
    assert-updated-file)
      cmd_assert_updated_file "$@"
      ;;
    parse-score)
      cmd_parse_score "$@"
      ;;
    score-ok)
      cmd_score_ok "$@"
      ;;
    --help|-h|help)
      usage
      ;;
    *)
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"
