---
description: Generate File-Level Detailed Findings (Sheet 9) via dynamic Python script
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
---

You generate Sheet 9 (File-Level Detailed Findings) by writing a self-contained Python script that reads `.combined.json` files.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet9.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **TECH_ASSESSMENT_PATH**: Output directory for sheet9.json
- **SOURCE_CODE_JSONS_PATH**: Where .combined.json files live

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Write Dynamic Python Script

Write to `temp/sheet9_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os, glob
from collections import defaultdict
from datetime import datetime

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
SOURCE_CODE_JSONS_PATH = "{SOURCE_CODE_JSONS_PATH}"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet9.json")
FILES_TO_ANALYZE = os.path.join(TECH_ASSESSMENT_PATH, "files_to_analyze.json")

ISSUES_COLUMNS = ["filename","class_name","path","issue_location","type","category","description","confidence","mcm_node_id"]
SUGGESTIONS_COLUMNS = ["filename","class_name","path","suggestion","mcm_node_id"]

def load_authorized_files():
    """Load the authoritative file list and return as a set of normalized paths."""
    if not os.path.exists(FILES_TO_ANALYZE):
        return None
    with open(FILES_TO_ANALYZE) as f:
        data = json.load(f)
    files = data if isinstance(data, list) else data.get("files", [])
    authorized = set()
    for entry in files:
        path = entry.get("path", entry) if isinstance(entry, dict) else entry
        authorized.add(path.strip().rstrip("/"))
    return authorized

def filter_combined_jsons(all_files, authorized):
    """Deduplicate .combined.json files: keep only those whose 'path' field
    matches files_to_analyze.json. When multiple files map to the same source
    path, prefer the one at the correct mirrored directory structure."""
    if authorized is None:
        return all_files

    by_source_path = {}
    for fpath in all_files:
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue
        source_path = data.get("path", "").strip().rstrip("/")
        if source_path not in authorized:
            print(f"  SKIP (not in files_to_analyze): {os.path.basename(fpath)} -> {source_path}")
            continue
        if source_path in by_source_path:
            existing = by_source_path[source_path]
            if os.sep in os.path.relpath(fpath, SOURCE_CODE_JSONS_PATH).rsplit(".combined.json", 1)[0]:
                print(f"  DEDUP: keeping mirrored {os.path.basename(fpath)}, dropping {os.path.basename(existing)}")
                by_source_path[source_path] = fpath
            else:
                print(f"  DEDUP: keeping mirrored {os.path.basename(existing)}, dropping {os.path.basename(fpath)}")
        else:
            by_source_path[source_path] = fpath

    result = list(by_source_path.values())
    print(f"  Filtered: {len(all_files)} total -> {len(result)} matched ({len(all_files) - len(result)} orphans skipped)")
    return result

def generate():
    pattern = os.path.join(SOURCE_CODE_JSONS_PATH, "**", "*.combined.json")
    files = glob.glob(pattern, recursive=True)
    if not files:
        print(f"No .combined.json files found in {SOURCE_CODE_JSONS_PATH}")
        empty = {"sheet_name":"File-Level Detailed Findings","sheet_number":9,
                 "generated_at":datetime.now().isoformat()+"Z",
                 "summary":{"total_files":0,"total_issues":0,"total_suggestions":0,"issues_by_type":{},"issues_by_category":{}},
                 "issues_columns":ISSUES_COLUMNS,"suggestions_columns":SUGGESTIONS_COLUMNS,
                 "issues":[],"suggestions":[]}
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE,'w') as f: json.dump(empty, f, indent=2)
        return

    authorized = load_authorized_files()
    files = filter_combined_jsons(files, authorized)

    all_issues = []
    all_suggestions = []
    issues_by_type = defaultdict(int)
    issues_by_category = defaultdict(int)
    total_files = 0

    for fpath in files:
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        total_files += 1
        path_val = data.get("path", "")
        filename = os.path.basename(path_val) if path_val else os.path.basename(fpath).replace(".combined.json","")
        class_name = data.get("class_name", filename.rsplit(".", 1)[0])
        mcm_id = data.get("mcm_node_ids", "")

        for issue in data.get("issues", []):
            itype = issue.get("type", "Unknown")
            cat = issue.get("category", "General")
            desc = issue.get("message", issue.get("description", ""))
            loc = issue.get("issue_location", "")
            conf = issue.get("confidence", 0.0)

            all_issues.append({
                "filename": filename, "class_name": class_name, "path": path_val,
                "issue_location": str(loc), "type": itype, "category": cat,
                "description": desc, "confidence": conf, "mcm_node_id": mcm_id,
            })
            issues_by_type[itype] += 1
            issues_by_category[cat] += 1

        for sugg in data.get("suggestions", []):
            text = sugg.get("code_suggestion", sugg.get("message", ""))
            if text and str(text).strip().upper() != "NA":
                all_suggestions.append({
                    "filename": filename, "class_name": class_name, "path": path_val,
                    "suggestion": text, "mcm_node_id": mcm_id,
                })

    all_issues.sort(key=lambda r: (r["filename"], r["class_name"], r["path"], r["issue_location"]))
    all_suggestions.sort(key=lambda r: (r["filename"], r["class_name"], r["path"]))

    sheet9 = {
        "sheet_name": "File-Level Detailed Findings", "sheet_number": 9,
        "generated_at": datetime.now().isoformat() + "Z",
        "summary": {
            "total_files": total_files,
            "total_issues": len(all_issues),
            "total_suggestions": len(all_suggestions),
            "issues_by_type": dict(issues_by_type),
            "issues_by_category": dict(issues_by_category),
        },
        "issues_columns": ISSUES_COLUMNS,
        "suggestions_columns": SUGGESTIONS_COLUMNS,
        "issues": all_issues,
        "suggestions": all_suggestions,
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet9, f, indent=2)
    print(f"Sheet 9 generated: {OUTPUT_FILE} ({len(all_issues)} issues, {len(all_suggestions)} suggestions)")

if __name__ == "__main__":
    generate()
```

## Step 2: Execute

```bash
mkdir -p temp
python3 temp/sheet9_generator.py
```

## Step 3: Validate

Verify sheet9.json:
1. Has `issues_columns` with exactly 9 entries
2. Has `suggestions_columns` with exactly 5 entries
3. Each issue has exactly 9 keys matching issues_columns
4. Each suggestion has exactly 5 keys matching suggestions_columns
5. Issues are sorted by (filename, class_name, path, issue_location)

## When Complete

Say only: `Done: Sheet 9 generated with X issues and Y suggestions`
