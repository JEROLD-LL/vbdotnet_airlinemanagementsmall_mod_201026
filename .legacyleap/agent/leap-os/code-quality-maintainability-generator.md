---
description: Generate Code Quality & Maintainability (Sheet 7) via dynamic Python script
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
---

You generate Sheet 7 (Code Quality & Maintainability) by writing a self-contained Python script that reads `.combined.json` files.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet7.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **TECH_ASSESSMENT_PATH**: Output directory for sheet7.json
- **SOURCE_CODE_JSONS_PATH**: Where .combined.json files live

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Write Dynamic Python Script

Write to `temp/sheet7_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os, glob
from datetime import datetime

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
SOURCE_CODE_JSONS_PATH = "{SOURCE_CODE_JSONS_PATH}"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet7.json")
FILES_TO_ANALYZE = os.path.join(TECH_ASSESSMENT_PATH, "files_to_analyze.json")

COLUMNS = [
    "filename", "class_name", "path", "vulnerabilities", "bugs", "code_smells",
    "coverage", "cognitive_complexity", "functions", "duplicate_lines_density",
    "lines", "security_risk_rating", "tech_debt_time", "architecture_complexity",
    "nfr_security_rating", "nfr_maintainability_rating", "nfr_reliability_rating",
    "nfr_testability_rating", "cloud_compatibiliy_rating", "coupling_score",
    "cloud_compatibiliy_assessment", "nfr_extensibility_rating", "nfr_reusability_rating",
    "nfr_scalability_rating", "risk_category", "mcm_node_id"
]

def classify_risk(complexity, maintainability, lines):
    if complexity > 50 or maintainability >= 5 or lines > 1500:
        return "High"
    if complexity > 25 or maintainability == 3 or lines > 1000:
        return "Medium"
    return "Low"

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
        empty = {"sheet_name":"Code Quality & Maintainability","sheet_number":7,
                 "generated_at":datetime.now().isoformat()+"Z","total_files_analyzed":0,
                 "summary":{},"columns":COLUMNS,"data":[]}
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE,'w') as f: json.dump(empty, f, indent=2)
        return

    authorized = load_authorized_files()
    files = filter_combined_jsons(files, authorized)

    rows = []
    totals = {"vulnerabilities":0,"bugs":0,"code_smells":0,"functions":0,"lines":0,"tech_debt_time":0}
    risk_counts = {"High":0,"Medium":0,"Low":0}
    complexity_sum = 0.0
    coverage_sum = 0.0
    coupling_sum = 0.0

    for fpath in files:
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        s = data.get("summary", {})
        path_val = data.get("path", "")
        filename = os.path.basename(path_val) if path_val else os.path.basename(fpath).replace(".combined.json","")
        class_name = data.get("class_name", filename.rsplit(".", 1)[0])
        mcm_id = data.get("mcm_node_ids", "")

        vulns = s.get("vulnerabilities", 0) or 0
        bugs = s.get("bugs", 0) or 0
        smells = s.get("code_smells", 0) or 0
        cov = s.get("coverage", 0) or 0
        cog_cx = s.get("cognitive_complexity", 0) or 0
        funcs = s.get("functions", 0) or 0
        dup = s.get("duplicate_lines_density", 0) or 0
        lines = s.get("lines", 0) or 0
        sec_rating = s.get("security_risk_rating", 3)
        debt = s.get("tech_debt_time", 0) or 0
        arch_cx = s.get("architecture_complexity", 0) or 0
        nfr_sec = s.get("nfr_security_rating", 3)
        nfr_maint = s.get("nfr_maintainability_rating", 3)
        nfr_rel = s.get("nfr_reliability_rating", 3)
        nfr_test = s.get("nfr_testability_rating", 0)
        cloud_rat = s.get("cloud_compatibiliy_rating", 3)
        coupling = s.get("coupling_score", 0) or 0
        cloud_ass = s.get("cloud_compatibiliy_assessment", 0)
        nfr_ext = s.get("nfr_extensibility_rating", 3)
        nfr_reu = s.get("nfr_reusability_rating", 3)
        nfr_sca = s.get("nfr_scalability_rating", 3)

        risk = classify_risk(cog_cx, nfr_maint, lines)

        row = {
            "filename": filename, "class_name": class_name, "path": path_val,
            "vulnerabilities": vulns, "bugs": bugs, "code_smells": smells,
            "coverage": cov, "cognitive_complexity": cog_cx, "functions": funcs,
            "duplicate_lines_density": dup, "lines": lines,
            "security_risk_rating": sec_rating, "tech_debt_time": debt,
            "architecture_complexity": arch_cx, "nfr_security_rating": nfr_sec,
            "nfr_maintainability_rating": nfr_maint, "nfr_reliability_rating": nfr_rel,
            "nfr_testability_rating": nfr_test, "cloud_compatibiliy_rating": cloud_rat,
            "coupling_score": coupling, "cloud_compatibiliy_assessment": cloud_ass,
            "nfr_extensibility_rating": nfr_ext, "nfr_reusability_rating": nfr_reu,
            "nfr_scalability_rating": nfr_sca, "risk_category": risk,
            "mcm_node_id": mcm_id,
        }
        rows.append(row)

        totals["vulnerabilities"] += vulns
        totals["bugs"] += bugs
        totals["code_smells"] += smells
        totals["functions"] += funcs
        totals["lines"] += lines
        totals["tech_debt_time"] += debt
        risk_counts[risk] += 1
        complexity_sum += cog_cx
        coverage_sum += cov
        coupling_sum += coupling

    n = len(rows)
    summary = {
        "high_risk_files": risk_counts["High"],
        "medium_risk_files": risk_counts["Medium"],
        "low_risk_files": risk_counts["Low"],
        "total_vulnerabilities": totals["vulnerabilities"],
        "total_bugs": totals["bugs"],
        "total_code_smells": totals["code_smells"],
        "total_functions": totals["functions"],
        "total_lines": totals["lines"],
        "total_tech_debt_minutes": totals["tech_debt_time"],
        "avg_cognitive_complexity": round(complexity_sum / max(n, 1), 1),
        "avg_coverage": round(coverage_sum / max(n, 1), 1),
        "avg_coupling_score": round(coupling_sum / max(n, 1), 1),
    }

    sheet7 = {
        "sheet_name": "Code Quality & Maintainability", "sheet_number": 7,
        "generated_at": datetime.now().isoformat() + "Z",
        "total_files_analyzed": n,
        "summary": summary,
        "columns": COLUMNS,
        "data": rows
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet7, f, indent=2)
    print(f"Sheet 7 generated: {OUTPUT_FILE} ({n} files)")

if __name__ == "__main__":
    generate()
```

## Step 2: Execute

```bash
mkdir -p temp
python3 temp/sheet7_generator.py
```

## Step 3: Validate

Verify sheet7.json:
1. Has `columns` with exactly 26 entries
2. Each row in `data` has exactly 26 keys matching column names
3. Has `summary` with risk counts and totals
4. Note: `cloud_compatibiliy_rating` typo is INTENTIONAL — keep it

## When Complete

Say only: `Done: Sheet 7 generated with X files`
