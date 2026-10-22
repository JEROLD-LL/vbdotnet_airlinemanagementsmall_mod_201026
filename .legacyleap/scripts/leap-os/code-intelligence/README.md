# Code Intelligence Scripts

Predefined bash wrappers for the `take-leap` CLI commands used by the Code Intelligence
Enhancement pipeline. These exist so agents **execute them directly via the `Bash` tool
in the current shell** instead of rewriting the command inline (where it is prone to
being silently "delegated" to a sub-agent or replaced with synthetic data).

**Deploy location (per-project):** `.legacyleap/scripts/leap-os/code-intelligence/`

## Scripts

| Script | Wraps | Purpose |
|--------|-------|---------|
| `check-takeleap-prerequisites.sh` | — | Validates conda env `legacyleap`, `take-leap` CLI, `.legacyleap/metadata.json`, and `python3`. |
| `check-mcm-exists.sh` | — | Exits `0` if a valid MCM (`meta_cognitive_model.json` with ≥1 part) already exists so callers can skip the scan; non-zero when the scan must run. |
| `take-leap-job.sh` | — | Runs a long-running wrapper as a **detached, idempotent** background job so the agent is never blocked for hours. See [Long-running jobs](#long-running-jobs). |
| `run-mcm-scan.sh` | `take-leap scan --latest` | Generates the Meta Cognitive Model (MCM). **Long-running — launch via `take-leap-job.sh`.** |
| `run-meta-layer-visualization.sh` | `take-leap meta-layer-visualization` | Generates the standalone MCM visualization HTML. |
| `run-functional-doc.sh` | `take-leap functional-doc --latest --ingest_vectorstore` | Generates Functional Specification Documentation from MCM. **Long-running (≈2h) — launch via `take-leap-job.sh`.** |
| `run-technical-doc.sh` | `take-leap technical-doc --latest --ingest_vectorstore` | Generates Technical Specification Documentation from MCM. **Long-running — launch via `take-leap-job.sh`.** |

## Common contract

Every `run-*.sh` script:

1. Runs `check-takeleap-prerequisites.sh` first and exits non-zero on failure.
2. Re-activates the `legacyleap` conda env in the current shell (idempotent).
3. Resolves paths from `.legacyleap/metadata.json` (`scan_assessment_reports`, `comprehend`).
4. Streams `take-leap` stdout/stderr **to the terminal AND** to a log file in
   `.legacyleap/.agent-state/logs/` (overridable via the first positional argument).
5. Verifies the expected artifact was produced (MCM JSON, visualization HTML, FSD markdown, or TSD markdown) before
   exiting 0.
6. Runs the `take-leap` invocation **directly in its own shell** — it never delegates the CLI to a sub-agent or
   substitutes synthetic data. (A wrapper may itself be *launched detached* by `take-leap-job.sh`; that runs the whole
   wrapper — with the `take-leap` call still direct — as a background job and captures its exit code. This is different
   from the wrapper forking the CLI internally, which it must not do.)

## Long-running jobs

`take-leap scan` (MCM) and `take-leap functional-doc` (FSD) can run for hours. Running them as a **blocking
foreground call** is the anti-pattern that causes agents to abandon the call on a tool timeout and then re-launch the
same multi-hour job. Use `take-leap-job.sh` instead:

```
# 1. Launch the wrapper detached (idempotent: a repeat launch while active/complete is a no-op)
Bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh launch fsd -- \
     bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh

# 2. Poll to completion — ONE await call per step (never wrap in a shell loop)
Bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh await fsd --max-wait 600   # repeat until STATUS=DONE

# Inspect / recover
Bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh status fsd
Bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh logs   fsd --lines 60
Bash .legacyleap/scripts/leap-os/code-intelligence/take-leap-job.sh launch fsd --force -- bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
```

How it works:

- **Detached** via `setsid` (fallback `nohup`) so the job survives the tool call / shell exit.
- **Completion is authoritative from the captured exit code** (`exit 0` ⇒ `DONE`, and the wrapper already verified the
  artifact). The log tail is used only for **stall/liveness** detection, not for deciding completion.
- **Idempotent `launch`**: already `DONE` or a live PID ⇒ no-op. This is the guard that prevents duplicate multi-hour runs.
- **Bounded `await`**: blocks ≤ `--max-wait` seconds (default 600), returns early on any terminal/actionable status.

Status tokens: `NOT_STARTED | RUNNING | STALLED | DONE | FAILED | DIED`.
Exit codes: `0=DONE 1=FAILED 2=DIED 3=RUNNING 4=STALLED 5=NOT_STARTED` (prefer parsing the `STATUS=<token>` line).
State/log per job: `.legacyleap/.agent-state/jobs/<job>/` (`log`, `pid`, `status`, `exit_code`, …).

| Status | Meaning | What the agent should do |
|--------|---------|--------------------------|
| `RUNNING` | Job alive, log advancing | Call `await` again (do not relaunch) |
| `STALLED` | Alive but log tail unchanged for a long time | Inspect `logs`; relaunch with `--force` only if truly hung |
| `DONE` | Exit 0, artifact verified | Proceed |
| `FAILED` | Exit non-zero | Inspect `logs`, STOP; do not relaunch blindly |
| `DIED` | PID gone, no exit code recorded | Inspect `logs`, relaunch with `--force` |

## Usage from agents

```
Bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh
Bash .legacyleap/scripts/leap-os/code-intelligence/run-meta-layer-visualization.sh
Bash .legacyleap/scripts/leap-os/code-intelligence/run-functional-doc.sh
Bash .legacyleap/scripts/leap-os/code-intelligence/run-technical-doc.sh
```

Optionally pass a custom log file:

```
Bash .legacyleap/scripts/leap-os/code-intelligence/run-mcm-scan.sh "/tmp/mcm_scan.log"
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0`  | Command completed AND the expected artifact was produced. |
| `1`  | Prerequisites missing, `take-leap` failed, or expected artifact is missing. |
