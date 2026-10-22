#!/bin/bash
set -uo pipefail
# Take-Leap Job Manager
# Purpose: Run a LONG-RUNNING command (e.g. run-mcm-scan.sh / run-functional-doc.sh,
#          which can take hours) as a DETACHED background job so the agent's tool call
#          is never blocked for the full duration. The job survives shell/session exit
#          (setsid/nohup), its exit code is captured authoritatively, and (re)launch is
#          IDEMPOTENT — a second `launch` while a run is active or already complete is a
#          no-op. This is the fix for agents that abandon a blocked foreground call and
#          then relaunch the same multi-hour job.
#
# Completion is decided by the CAPTURED EXIT CODE of the job body (exit 0 => DONE),
# NOT by grepping the log. The log tail is used only for liveness/stall detection so a
# hung CLI does not cause an indefinite wait.
#
# Subcommands:
#   launch <job> [--log <path>] [--force] -- <cmd> [args...]
#       Start <cmd> detached under job name <job>. Idempotent:
#         - already DONE            -> prints STATUS=DONE, no-op (unless --force)
#         - already RUNNING/STALLED -> prints STATUS=RUNNING|STALLED, no-op (unless --force)
#         - otherwise               -> starts the job, prints STATUS=RUNNING
#   status <job> [--stall-after <sec>] [--quiet]
#       Print the current status once and exit. Non-blocking.
#   await  <job> [--max-wait <sec>] [--poll <sec>] [--stall-after <sec>] [--quiet]
#       Block up to --max-wait seconds (default 600 = 10 min), polling every --poll
#       seconds (default 30). Returns EARLY on any terminal/actionable status
#       (DONE|FAILED|DIED|STALLED). Call this REPEATEDLY as separate steps until the
#       status is terminal — never wrap it in a shell loop (that re-creates the block).
#   logs   <job> [--lines <n>]
#       Print the tail of the job log.
#   clean  <job>
#       Remove the job's state directory (use before a deliberate re-run).
#
# Status tokens: NOT_STARTED | RUNNING | STALLED | DONE | FAILED | DIED
# Exit codes:    0=DONE  1=FAILED  2=DIED  3=RUNNING  4=STALLED  5=NOT_STARTED  64=usage
#   (Prefer parsing the `STATUS=<token>` line; exit codes mirror it for convenience.)
#
# Examples:
#   take-leap-job.sh launch fsd -- bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
#   take-leap-job.sh await  fsd --max-wait 600        # repeat until STATUS=DONE
#   take-leap-job.sh status fsd
#   take-leap-job.sh logs   fsd --lines 40

JOBS_ROOT="$(pwd)/.legacyleap/.agent-state/jobs"
DEFAULT_MAX_WAIT=600
DEFAULT_POLL=30
DEFAULT_STALL_AFTER=1800   # 30 min with no new log output while alive => STALLED

usage() {
    sed -n '2,45p' "$0" | sed 's/^# \{0,1\}//'
    exit 64
}

fail_usage() {
    echo "ERROR: $1" >&2
    echo "Run '$0' with no valid subcommand for help." >&2
    exit 64
}

# ---- state helpers -----------------------------------------------------------

job_dir()      { echo "$JOBS_ROOT/$1"; }
now()          { date +%s; }
read_file()    { cat "$1" 2>/dev/null || echo ""; }

# Recompute the log signature (byte count + checksum of the last lines). If it changed
# since last check, stamp logsig_at with the current time. Used for stall detection.
update_logsig() {
    local d="$1" log sig prev
    log="$d/log"
    sig="$(wc -c <"$log" 2>/dev/null | tr -d ' ')-$(tail -n 5 "$log" 2>/dev/null | cksum 2>/dev/null | awk '{print $1}')"
    prev="$(read_file "$d/logsig")"
    if [ "$sig" != "$prev" ]; then
        printf '%s' "$sig" > "$d/logsig"
        now > "$d/logsig_at"
    fi
    [ -f "$d/logsig_at" ] || now > "$d/logsig_at"
}

# Echo the current status token for a job dir.
compute_status() {
    local d="$1" stall_after="$2" pid code last_change
    if [ ! -d "$d" ]; then echo "NOT_STARTED"; return; fi

    if [ -f "$d/exit_code" ]; then
        code="$(read_file "$d/exit_code")"
        if [ "$code" = "0" ]; then echo "DONE"; else echo "FAILED"; fi
        return
    fi

    pid="$(read_file "$d/pid")"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        update_logsig "$d"
        last_change="$(read_file "$d/logsig_at")"
        if [ -n "$last_change" ] && [ "$(( $(now) - last_change ))" -ge "$stall_after" ]; then
            echo "STALLED"
        else
            echo "RUNNING"
        fi
        return
    fi

    if [ -n "$pid" ]; then
        # PID was recorded but the process is gone and no exit code landed => killed/crashed.
        echo "DIED"
        return
    fi

    echo "NOT_STARTED"
}

status_exit_code() {
    case "$1" in
        DONE) echo 0 ;;
        FAILED) echo 1 ;;
        DIED) echo 2 ;;
        RUNNING) echo 3 ;;
        STALLED) echo 4 ;;
        *) echo 5 ;;
    esac
}

print_status() {
    local d="$1" s="$2" quiet="$3" pid start elapsed last
    if [ "$quiet" = "1" ]; then
        echo "STATUS=$s"
        return
    fi
    pid="$(read_file "$d/pid")"
    start="$(read_file "$d/started_at")"
    elapsed=""
    if [ -n "$start" ]; then elapsed="$(( $(now) - start ))s"; fi
    last="$(tail -n 1 "$d/log" 2>/dev/null || echo "")"
    echo "STATUS=$s"
    echo "  job:     $(basename "$d")"
    echo "  pid:     ${pid:-<none>}"
    echo "  elapsed: ${elapsed:-<n/a>}"
    echo "  log:     $d/log"
    [ -n "$last" ] && echo "  last:    $last"
    case "$s" in
        DONE)    echo "  => Completed successfully (exit 0, artifact verified by the job body)." ;;
        FAILED)  echo "  => Job body exited non-zero ($(read_file "$d/exit_code")). Inspect the log; do NOT relaunch blindly." ;;
        DIED)    echo "  => Process vanished without an exit code (killed/crashed). Inspect the log, then relaunch with --force." ;;
        STALLED) echo "  => Alive but no new log output for a while. Likely hung — inspect the log instead of waiting." ;;
        RUNNING) echo "  => Still running. Call 'await' again (each call blocks up to --max-wait); do NOT relaunch." ;;
        NOT_STARTED) echo "  => No job recorded. Use 'launch'." ;;
    esac
}

# ---- subcommands -------------------------------------------------------------

cmd_launch() {
    local job="" log_override="" force=0
    local -a JOB_CMD=()
    while [ $# -gt 0 ]; do
        case "$1" in
            --log) log_override="$2"; shift 2 ;;
            --force) force=1; shift ;;
            --) shift; JOB_CMD=("$@"); break ;;
            -*) fail_usage "unknown launch option: $1" ;;
            *) if [ -z "$job" ]; then job="$1"; shift; else fail_usage "unexpected argument: $1 (did you forget '--' before the command?)"; fi ;;
        esac
    done
    [ -n "$job" ] || fail_usage "launch requires a <job> name"
    [ "${#JOB_CMD[@]}" -gt 0 ] || fail_usage "launch requires '-- <cmd> [args...]'"

    local d; d="$(job_dir "$job")"
    local s; s="$(compute_status "$d" "$DEFAULT_STALL_AFTER")"

    if [ "$force" != "1" ]; then
        case "$s" in
            DONE)
                echo "INFO: job '$job' already completed — not relaunching (use --force to override)."
                print_status "$d" DONE 0
                exit "$(status_exit_code DONE)"
                ;;
            RUNNING|STALLED)
                echo "INFO: job '$job' is already active ($s) — not relaunching (use --force to override)."
                print_status "$d" "$s" 0
                exit "$(status_exit_code "$s")"
                ;;
        esac
    fi

    # Fresh (or forced) start: reset state. If forcing over a live process, stop it first.
    local old_pid; old_pid="$(read_file "$d/pid")"
    if [ "$force" = "1" ] && [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
        echo "INFO: --force: terminating existing job pid $old_pid"
        kill "$old_pid" 2>/dev/null || true
        sleep 1
    fi

    mkdir -p "$d"
    rm -f "$d/pid" "$d/exit_code" "$d/started_at" "$d/finished_at" "$d/logsig" "$d/logsig_at" "$d/status"
    : > "$d/log"
    [ -n "$log_override" ] && ln -sf "$log_override" "$d/log_override" 2>/dev/null || true
    printf '%q ' "${JOB_CMD[@]}" > "$d/cmd"; echo >> "$d/cmd"

    # Per-job runner records its own PID (reliable across setsid's fork), runs the body,
    # then records the captured exit code + terminal status.
    cat > "$d/runner.sh" <<RUNNER
#!/bin/bash
echo \$\$ > "$d/pid"
date +%s > "$d/started_at"
echo RUNNING > "$d/status"
"\$@"
code=\$?
echo "\$code" > "$d/exit_code"
date +%s > "$d/finished_at"
if [ "\$code" -eq 0 ]; then echo DONE > "$d/status"; else echo FAILED > "$d/status"; fi
RUNNER
    chmod +x "$d/runner.sh"

    # Detach so the job outlives this tool call / shell. setsid gives a fresh session;
    # fall back to nohup where setsid is unavailable.
    if command -v setsid >/dev/null 2>&1; then
        setsid bash "$d/runner.sh" "${JOB_CMD[@]}" >>"$d/log" 2>&1 < /dev/null &
    else
        nohup bash "$d/runner.sh" "${JOB_CMD[@]}" >>"$d/log" 2>&1 < /dev/null &
    fi
    disown 2>/dev/null || true

    # Give the runner a moment to record its PID, then report.
    local i=0
    while [ ! -s "$d/pid" ] && [ "$i" -lt 20 ]; do sleep 0.1; i=$((i+1)); done

    echo "INFO: launched job '$job' (detached)."
    echo "INFO: command: $(read_file "$d/cmd")"
    print_status "$d" "$(compute_status "$d" "$DEFAULT_STALL_AFTER")" 0
    exit 0
}

cmd_status() {
    local job="" quiet=0 stall_after="$DEFAULT_STALL_AFTER"
    while [ $# -gt 0 ]; do
        case "$1" in
            --quiet) quiet=1; shift ;;
            --stall-after) stall_after="$2"; shift 2 ;;
            -*) fail_usage "unknown status option: $1" ;;
            *) job="$1"; shift ;;
        esac
    done
    [ -n "$job" ] || fail_usage "status requires a <job> name"
    local d; d="$(job_dir "$job")"
    local s; s="$(compute_status "$d" "$stall_after")"
    print_status "$d" "$s" "$quiet"
    exit "$(status_exit_code "$s")"
}

cmd_await() {
    local job="" quiet=0 max_wait="$DEFAULT_MAX_WAIT" poll="$DEFAULT_POLL" stall_after="$DEFAULT_STALL_AFTER"
    while [ $# -gt 0 ]; do
        case "$1" in
            --quiet) quiet=1; shift ;;
            --max-wait) max_wait="$2"; shift 2 ;;
            --poll) poll="$2"; shift 2 ;;
            --stall-after) stall_after="$2"; shift 2 ;;
            -*) fail_usage "unknown await option: $1" ;;
            *) job="$1"; shift ;;
        esac
    done
    [ -n "$job" ] || fail_usage "await requires a <job> name"
    local d; d="$(job_dir "$job")"

    local deadline s; deadline="$(( $(now) + max_wait ))"
    while true; do
        s="$(compute_status "$d" "$stall_after")"
        case "$s" in
            DONE|FAILED|DIED|STALLED|NOT_STARTED) break ;;
        esac
        if [ "$(now)" -ge "$deadline" ]; then break; fi
        sleep "$poll"
    done

    print_status "$d" "$s" "$quiet"
    exit "$(status_exit_code "$s")"
}

cmd_logs() {
    local job="" lines=40
    while [ $# -gt 0 ]; do
        case "$1" in
            --lines) lines="$2"; shift 2 ;;
            -*) fail_usage "unknown logs option: $1" ;;
            *) job="$1"; shift ;;
        esac
    done
    [ -n "$job" ] || fail_usage "logs requires a <job> name"
    local d; d="$(job_dir "$job")"
    [ -f "$d/log" ] || { echo "No log for job '$job' at $d/log" >&2; exit 1; }
    tail -n "$lines" "$d/log"
    exit 0
}

cmd_clean() {
    local job="${1:-}"
    [ -n "$job" ] || fail_usage "clean requires a <job> name"
    local d; d="$(job_dir "$job")"
    local pid; pid="$(read_file "$d/pid")"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "ERROR: job '$job' is still running (pid $pid). Stop it first or use launch --force." >&2
        exit 1
    fi
    rm -rf "$d"
    echo "INFO: cleaned job '$job'."
    exit 0
}

# ---- dispatch ----------------------------------------------------------------

[ $# -ge 1 ] || usage
SUB="$1"; shift
case "$SUB" in
    launch) cmd_launch "$@" ;;
    status) cmd_status "$@" ;;
    await)  cmd_await "$@" ;;
    logs)   cmd_logs "$@" ;;
    clean)  cmd_clean "$@" ;;
    -h|--help|help) usage ;;
    *) fail_usage "unknown subcommand: $SUB" ;;
esac
