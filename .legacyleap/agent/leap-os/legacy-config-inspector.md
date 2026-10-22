---
description: "Returns only the list of legacy application config file extensions to copy during transpile"
name: legacy-config-inspector
mode: subagent
tools:
  Read: true
  Grep: true
  Glob: true
  Bash: true
temperature: 0.1
---

# Legacy Config Inspector

Decide which configuration **file extensions** `take-leap transpile` should copy
for one qualified name. Base the decision on reading candidate files, not on a
fixed keyword pattern.

The orchestrator supplies `TUI_ROOT` (the directory where the TUI is running),
the resolved `legacy_code` directory, and the exact qualified name. Read and
search only paths inside `TUI_ROOT`. If `legacy_code` is outside that
directory, stop and report that. Do not walk parent directories.

## Step 1: Enumerate the extensions that exist

List every distinct file extension present under `legacy_code`, with counts, for
example:

```bash
find <legacy_code> -type f -name '*.*' \
  | sed 's|.*/||; s|^.*\.|.|' \
  | tr '[:upper:]' '[:lower:]' \
  | sort | uniq -c | sort -rn
```

Work only from this discovered list. Do not assume an extension exists and do
not invent extensions that are absent from the tree.

## Step 2: Exclude unwanted paths and file kinds

Ignore files under IDE, build, dependency, and generated locations, including:

- `bin/`, `obj/`, `.vs/`, `.vscode/`, `.idea/`, `Debug/`, `Release/`
- `packages/`, `node_modules/`, `dist/`, `build/`, `TestResults/`
- `.git/`, backup/temp files (`*.bak`, `*.orig`, `*.tmp`, `*~`)
- designer/generated sources (`*.Designer.vb`, `*.g.vb`, `*.g.i.vb`,
  `*.AssemblyInfo.vb`, files marked auto-generated)

Also exclude project/tooling metadata even when its extension looks like
config: `.vbproj`, `.csproj`, `.sln`, `.user`, `.vssettings`, `packages.config`,
`nuget.config`, `.editorconfig`, `.gitignore`, and test-only fixtures.

## Step 3: Shortlist plausible config extensions

From the remaining extensions, shortlist those that plausibly hold runtime
configuration (for example `.config`, `.conf`, `.properties`, `.settings`,
`.ini`, `.xml`, `.json`, `.yml`, `.yaml`). Ignore source, binary, image, and
document extensions.

## Step 4: Confirm by reading the files

Open representative files for each shortlisted extension, and check how the code
for the qualified name loads settings (`ConfigurationManager`, `AppSettings`,
`ConnectionStrings`, `My.Settings`, `GetSection`, `IConfiguration`, or direct
file reads). Keep an extension only when at least one non-excluded file holds
**runtime application configuration** that must keep the same keys after
modernization:

- database / connection strings
- API and integration endpoints
- secrets, tokens, client ids
- other app settings the application reads by key

Drop the extension when its files are only documentation, data, layout,
localization, or build metadata.

## Output contract

Return **only** a JSON array of lowercase extensions with a leading dot, sorted,
deduplicated, and nothing else. No prose, no explanation, no code fences, no
evidence, no key names, no configuration values.

```json
[".config", ".properties"]
```

Return `[]` when no extension qualifies. That is a valid result, not a failure.

Never print configuration values or secrets. Never run git commands.
