---
description: Generate Application-Level Summary (Sheet 3) via dynamic Python script
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
---

You generate Sheet 3 (Application-Level Summary) by writing a self-contained Python script that reads `.combined.json` files.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet3.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **PROJECT_NAME**: Project name
- **TECH_ASSESSMENT_PATH**: Output directory for sheet3.json
- **SOURCE_CODE_JSONS_PATH**: Where .combined.json files live

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Write Dynamic Python Script

Write to `temp/sheet3_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os, glob
from datetime import datetime

PROJECT_NAME = "{PROJECT_NAME}"
TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
SOURCE_CODE_JSONS_PATH = "{SOURCE_CODE_JSONS_PATH}"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet3.json")

def generate():
    pattern = os.path.join(SOURCE_CODE_JSONS_PATH, "**", "*.combined.json")
    files = glob.glob(pattern, recursive=True)
    if not files:
        print(f"No .combined.json files found in {SOURCE_CODE_JSONS_PATH}")
        empty = {"sheet_name":"Application-Level Summary","sheet_number":3,
                 "generated_at":datetime.now().isoformat()+"Z",
                 "total_files_all_projects":0,"total_projects_detected":1,
                 "columns":["repo_name","total_files","legacy_files_pct","high_risk_files_count",
                            "architectural_violations","security_issues","test_coverage_indicator",
                            "cloud_readiness_score"],
                 "summary":{"total_files":0},"data":[]}
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE,'w') as f: json.dump(empty, f, indent=2)
        return

    total_files = 0
    high_risk = 0
    arch_violations = 0
    security_issues = 0
    coverage_sum = 0.0
    cloud_sum = 0.0

    VIOLATION_KEYWORDS = {"violation", "solid", "boundary", "architecture"}

    for fpath in files:
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        total_files += 1
        summary = data.get("summary", {})
        arch_cx = summary.get("architecture_complexity", 0) or 0
        maint = summary.get("nfr_maintainability_rating", 0) or 0
        lines = summary.get("lines", 0) or 0
        vulns = summary.get("vulnerabilities", 0) or 0

        if arch_cx > 30 or maint >= 4 or lines > 500:
            high_risk += 1

        for issue in data.get("issues", []):
            cat = (issue.get("category", "") or "").lower()
            if any(kw in cat for kw in VIOLATION_KEYWORDS):
                arch_violations += 1

        security_issues += vulns
        coverage_sum += summary.get("coverage", 0) or 0
        cloud_sum += summary.get("cloud_compatibiliy_rating", 3) or 3

    avg_coverage = coverage_sum / max(total_files, 1)
    if avg_coverage == 0:
        test_indicator = "None"
    elif avg_coverage < 30:
        test_indicator = "Low"
    elif avg_coverage < 70:
        test_indicator = "Medium"
    else:
        test_indicator = "High"

    cloud_readiness = round(cloud_sum / max(total_files, 1) / 5.0 * 100, 1)

    row = {
        "repo_name": PROJECT_NAME,
        "total_files": total_files,
        "legacy_files_pct": 100.0,
        "high_risk_files_count": high_risk,
        "architectural_violations": arch_violations,
        "security_issues": security_issues,
        "test_coverage_indicator": test_indicator,
        "cloud_readiness_score": cloud_readiness,
    }

    sheet3 = {
        "sheet_name": "Application-Level Summary", "sheet_number": 3,
        "generated_at": datetime.now().isoformat() + "Z",
        "total_files_all_projects": total_files,
        "total_projects_detected": 1,
        "columns": ["repo_name","total_files","legacy_files_pct","high_risk_files_count",
                     "architectural_violations","security_issues","test_coverage_indicator",
                     "cloud_readiness_score"],
        "summary": {"total_files": total_files, "high_risk_files": high_risk,
                     "architectural_violations": arch_violations, "security_issues": security_issues},
        "data": [row]
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet3, f, indent=2)
    print(f"Sheet 3 generated: {OUTPUT_FILE} ({total_files} files analyzed)")

if __name__ == "__main__":
    generate()
```

## Step 2: Execute

```bash
mkdir -p temp
python3 temp/sheet3_generator.py
```

## Step 3: Validate

Verify sheet3.json:
1. Has `columns` with exactly 8 entries
2. `data` has exactly 1 row
3. Row keys match column names

## When Complete

Say only: `Done: Sheet 3 generated with X files analyzed`
