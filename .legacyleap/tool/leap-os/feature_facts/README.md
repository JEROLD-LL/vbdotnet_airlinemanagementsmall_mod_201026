# feature_facts

Turns the MCM and the UI snapshot folder into evidence for one feature spec, and checks the spec mechanically. Used by the `feature-spec-writer` agent (`/feature-spec`); see `scan_assessment_reports/features/README.md` for the flow.

```bash
python3 -B .legacyleap/tool/leap-os/feature_facts <command> [options]
```

Every command prints one JSON object. Exit codes: `0` ok, `1` check failed or action needed (see `error`), `2` error.

## Commands

| Command | Reads | Writes | Notes |
|---|---|---|---|
| `features` | MCM, snapshot folder, existing `snapshot-map.json` | `scan_assessment_reports/features/features.json`, `scan_assessment_reports/features/snapshot-map.json`, `scan_assessment_reports/features/features-roadmap.md`, generated section of `scan_assessment_reports/features/README.md` | Groups screens into features. Pointers only (qualified names, `op-` ids, image paths). Lists each screen's grouping reason, `unmatched_images` and `unconfirmed_images`. |
| `screens` | MCM, `snapshot-map.json` | nothing | Per screen: feature, intent, Designer intent, `opens` / `opened_by`, mapped images. Used to decide which screen an image shows. |
| `status` | `features.json`, `snapshot-map.json`, every `<ID>/<ID>.md` | generated section of `scan_assessment_reports/features/README.md` | Spec status per feature (`not written`, `draft`, `approved`, `stale`), `waiting_on`, `next`, `to_draft`. |
| `evidence --feature ID` | MCM, `features.json`, `snapshot-map.json`, target stack files | `leap-os/specs/features/<ID>/evidence.json` | Pulls that feature's text from the MCM (below). Refuses if `features.json` is from another MCM or any image is unmatched. |
| `scaffold --feature ID [--force \| --sync]` | `<ID>/evidence.json` | `leap-os/specs/features/<ID>/<ID>.md` | Spec skeleton: every heading and table, mechanical content filled in, `TODO` where judgement is needed, plus the generated blocks (below). Refuses to overwrite without `--force`. `--sync` rewrites only the generated blocks of an existing spec, repairs table separator rows whose column count differs from their header (`separators_repaired`), and reports `missing_headings` when the spec lacks 3.5, 4.1, 4.2 or 9. |
| `check --feature ID` | `<ID>/evidence.json`, `<ID>/<ID>.md` | nothing | Mechanical checks (below). |

Options: `--root` (default `.`), `--mcm` (default `scan_assessment_reports/meta_cognitive_model.json`), `--profile` (default `auto`; profiles in `profiles/`), `--snapshot-folder` (default: the only `**/snapshots/` folder), `--features-dir` (default `scan_assessment_reports/features`).

## Snapshot matching

An image is matched to a screen (`how: "name"`) when its file name, lowercased with punctuation and trailing digits removed, equals the screen key (`SUBJECT1.png` goes to `Subject`), or is a close spelling (`Cources.png` goes to `Courses`).

Otherwise the words of the file name are compared with the words of the screen keys (`how: "words"`, with a `note`). The image goes to a screen when the name contains that screen's words and its other words name no other screen (`AdminLogin.png` goes to `Login`), or when its words appear in exactly one screen key (`Email.png` goes to `EmailWeb`). `EditMarks.png` stays unmatched because "Edit" also names `EditStudent` and `EditFaculty`. Words matches count as matched but are listed as `unconfirmed_images` until an agent looks at them.

Anything else is `unmatched` until someone looks at it and writes:

```json
"legacy_code/.../snapshots/AdminLogin.png": {"screen": "Login", "how": "manual", "note": "window title 'Admin Login'"}
```

Use `"screen": null` for an image that shows no screen. Manual entries are kept on every `features` run.

## What `evidence` contains

Per feature: screens (intent, behavior, controls, event handlers, navigation, images), methods and other parts with behavior (constructors included), data objects and operations with SQL, external libraries, methods that write more than once, open items, and:

| Key | What it is |
|---|---|
| `cross_feature.used_by` / `uses` | CALLS edges to and from other features, grouped by feature, with every caller and callee |
| `mentions` | Other features' behavior or intent text naming this feature's screen keys or the identifiers its behavior quotes (e.g. static fields `stuid`, `stuname`); terms named by more than 8 parts are dropped as too generic |
| `security_signals` | Hard-coded credentials, plain-text passwords (text, or `password=` in a WHERE clause), SQL built from UI values, exception details shown in message boxes; each with a quote and its `mcm:` or `op-` source. Patterns can be overridden per profile (`security.signals`, `security.sql_signals`) |
| `target_stack.files` | `leap-os/product/tech-stack.md` and `leap-os/standards/**/*.md`, cited in specs as `stack:<file>` |
| `image_map` | Per image of this feature: its screen, `how` it was matched and the `note` |
| `backend.apis` | Backend endpoints derived from the data operations (below) |

Dependencies include direct calls into platform features ("calls DTconnection") besides authentication and data reads.

## Backend API derivation

`backend.apis` uses only the MCM data operations. One endpoint per distinct method and path; each keeps every legacy operation it replaces (`legacy[]`: screen, method qualified name, UI triggers, `op-` id, SQL, purpose).

| MCM operation | Endpoint |
|---|---|
| resource | `/api/{table}` from the table name (`cmsdbx.courses` becomes `/api/courses`) |
| `SELECT COUNT(...)`, or no SQL and the purpose says count | `GET /api/{table}/count` |
| `SELECT` with a WHERE on a password-like column | `POST /api/{table}/authenticate`, WHERE columns as body |
| `SELECT` | `GET`, one WHERE column as path parameter (`/{col}`), several as query parameters |
| `INSERT` | `POST`, inserted columns as body |
| `UPDATE` | `PUT`, SET columns as body, keyed like SELECT |
| `DELETE` | `DELETE`, keyed like SELECT |
| no SQL verb | verb inferred from the purpose text ("Retrieve …" is a SELECT), noted |

Fields come from the SQL column lists; `SELECT *` or a missing list uses every known column of the table (noted). Password-like columns are never in a response. Quoted literals and `'<placeholder>'` values are ignored when reading WHERE columns. A keyless `PUT` / `DELETE` is merged into its only keyed sibling. What cannot be derived (no key, no columns, a filter the purpose names but no SQL shows) is a `gap`, which the scaffold writes as an open question.

`triggers` are the UI events behind each operation: the method itself when it is an event handler (`SaveButton_Click` gives `SaveButton.Click`), otherwise the event handlers that call it (`load_Data` gives `Courses.Load` and `RefreshButton.Click`).

## Generated blocks

The scaffold writes three blocks between `<!-- generated:NAME:start … -->` and `<!-- generated:NAME:end -->`. They come from `evidence.json` only; the writer never edits them.

| Block | Section | Content |
|---|---|---|
| `snapshots` | Visual References | Per screen, every image embedded (`![…](../../../<path>)`), its `snapshot:` token, the screen's `mcm:` qualified name and why it maps there |
| `apis` | Endpoints | API id, method, path, MCM purpose, legacy screen and trigger, legacy method as `mcm:<qualified_name>`, replaced `op-` ids |
| `contracts` | Contracts | Per API: parameters, request body and response JSON, derivation notes, gaps |

## What `check` verifies

- The title contains the feature id; all sections are present (Summary, Workflow, Business rules, UI, Backend, Data, Errors and edge cases, Test scenarios, Modernization, Evidence, Open questions, Approval) and Approval comes last.
- Every template subsection is present (3.1–3.6, 4.1–4.5, 5.1–5.2, 7.1, 8.1–8.6, 9.1–9.3), and every table subsection, Workflow, Business rules and Errors has at least one row. No `TODO` is left.
- Every table renders (`table_shape`): a header has a `|---|` separator row under it, and the separator and every row have the header's cell count (`\|` counts as text).
- The three generated blocks are present (`generated_missing`) and equal a fresh render from `evidence.json` (`generated_changed`); `scaffold --sync` fixes both.
- Test scenarios has a Gherkin block with at least one scenario per click handler.
- Every screen is named. Screen and method behavior and every SQL statement are copied verbatim.
- Every `op-`, `mcm:`, `snapshot:` and `stack:` token resolves, and every operation and every image is cited. 8.1 Target mapping cites the target stack.
- Every cross-feature group appears in 8.2 and every security signal in 4.4.
- Every table row in Workflow through Modernization, and every Gherkin scenario, carries a legacy token.
- No unknown qualified names or `schema.object` names, no broken links, no "see mcm" / "see legacy" / "refer to source".
- Every open item from the evidence appears under Open questions; question statuses start with `open`, `resolved` or `accepted`.
- Approval has `| Status | draft |` or `approved`. An approved spec needs Reviewer, Date and an MCM sha256 that matches `evidence.json`, and no open questions.

## Modules

| File | Role |
|---|---|
| `mcm.py` | Reads the MCM: screens, methods, data operations (`op-` ids), navigation, controls |
| `features.py` | Groups screens into features and orders them by dependency |
| `profiles.py`, `profiles/` | Stack recognition (`dotnet-winforms`, `generic-mcm`) |
| `snapmap.py` | Image-to-screen map |
| `facts.py` | `features.json` index and per-feature `evidence.json` |
| `board.py` | Spec status, next feature, generated README section, screen digest |
| `scaffold.py` | Spec skeleton and generated blocks from `evidence.json`; `--sync` |
| `verify.py` | `check` |
