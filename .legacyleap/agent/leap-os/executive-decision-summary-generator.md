---
description: Generate Executive Decision Summary (Sheet 1) via dynamic Python script
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
---

You generate Sheet 1 (Executive Decision Summary) by writing a self-contained Python script that reads previously generated sheet JSONs.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet1.json`
5. **Sheet 1 runs LAST** — after sheets 2, 3, 4, 7, 8 are generated

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **PROJECT_NAME**: Project name
- **TECHNOLOGY**: Technology plugin
- **FRAMEWORK**: Legacy framework
- **TECH_ASSESSMENT_PATH**: Where sheet JSONs live and where to write sheet1.json

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Write Dynamic Python Script

Write to `temp/sheet1_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os
from datetime import datetime

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
PROJECT_NAME = "{PROJECT_NAME}"
TECHNOLOGY = "{TECHNOLOGY}"
FRAMEWORK = "{FRAMEWORK}"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet1.json")

def safe_load(filename):
    path = os.path.join(TECH_ASSESSMENT_PATH, filename)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def safe_num(val, default=0):
    if isinstance(val, (int, float)):
        return val
    return default

def generate():
    s2 = safe_load("sheet2.json")
    s3 = safe_load("sheet3.json")
    s4 = safe_load("sheet4.json")
    s7 = safe_load("sheet7.json")
    s8 = safe_load("sheet8.json")

    # --- technical_health_score (0-100, higher = healthier) ---
    health = 100.0
    s7_summary = s7.get("summary", {})
    high_risk = safe_num(s7_summary.get("high_risk_files", 0))
    med_risk = safe_num(s7_summary.get("medium_risk_files", 0))
    low_risk = safe_num(s7_summary.get("low_risk_files", 0))
    total_files = high_risk + med_risk + low_risk
    if total_files > 0:
        health -= (high_risk / total_files) * 40
    total_vulns = safe_num(s7_summary.get("total_vulnerabilities", 0))
    total_bugs = safe_num(s7_summary.get("total_bugs", 0))
    tf = max(total_files, 1)
    health -= min(total_vulns / tf * 3, 15)
    health -= min(total_bugs / tf * 4, 15)
    avg_cx = safe_num(s7_summary.get("avg_cognitive_complexity", 0))
    if avg_cx > 30:
        health -= 10
    elif avg_cx > 20:
        health -= 5
    s4_summary = s4.get("summary", {})
    cyclic_deps = s4_summary.get("cyclic_dependencies", 0)
    if isinstance(cyclic_deps, (int, float)):
        health -= min(cyclic_deps * 5, 10)
    health = round(max(0, min(100, health)), 1)

    # --- modernization_readiness_score ---
    s2_summary = s2.get("summary", {})
    total_mods = safe_num(s2_summary.get("total_modules", 0))
    if total_mods > 0:
        rehost_f = safe_num(s2_summary.get("rehost_feasible", 0))
        replace_c = safe_num(s2_summary.get("replacement_candidates", 0))
        rearch_n = safe_num(s2_summary.get("rearchitect_needed", 0))
        mod_readiness = (rehost_f / total_mods * 100 * 0.4
                         + (total_mods - replace_c) / total_mods * 100 * 0.3
                         + (total_mods - rearch_n) / total_mods * 100 * 0.3)
        mod_readiness = round(max(0, min(100, mod_readiness)), 1)
    else:
        mod_readiness = 50.0

    # --- business_criticality ---
    s8_counts = s8.get("summary_counts", {})
    components = (safe_num(s8_counts.get("controllers", 0))
                  + safe_num(s8_counts.get("services", 0))
                  + safe_num(s8_counts.get("repositories", 0))
                  + safe_num(s8_counts.get("api_endpoints", 0))
                  + safe_num(s8_counts.get("ui_screens", 0)))
    deps = safe_num(s8_counts.get("third_party_dependencies", 0))
    if components > 20 or deps > 30:
        biz_crit = "Critical"
    elif components > 10 or deps > 15:
        biz_crit = "High"
    elif components > 3 or deps > 5:
        biz_crit = "Medium"
    else:
        biz_crit = "Low"

    # --- risk_level ---
    s4_high = safe_num(s4_summary.get("high_risk", 0))
    high_risk_pct = (high_risk / max(total_files, 1)) * 100
    cyclic_num = safe_num(cyclic_deps) if isinstance(cyclic_deps, (int, float)) else 0
    if s4_high > 2 or high_risk_pct > 40 or cyclic_num > 2:
        risk_level = "High"
    elif s4_high > 0 or high_risk_pct > 15 or cyclic_num > 0:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # --- recommended_action ---
    action_counts = {"Replace": 0, "Re-architect": 0, "Refactor": 0, "Re-host": 0}
    for row in s2.get("data", []):
        if row.get("replacement_indicator") == "Yes":
            action_counts["Replace"] += 1
        if row.get("rearchitect_need") == "Yes":
            action_counts["Re-architect"] += 1
        if row.get("refactor_feasibility") in ("Yes", "Partial"):
            action_counts["Refactor"] += 1
        if row.get("rehost_feasibility") in ("Yes", "Partial"):
            action_counts["Re-host"] += 1
    recommended = max(action_counts, key=action_counts.get) if any(action_counts.values()) else "Refactor"

    # --- confidence_score ---
    confidence = "N/A"

    # --- key_blocking_risks ---
    risks = []
    if isinstance(cyclic_deps, (int, float)) and cyclic_deps > 0:
        risks.append(f"{int(cyclic_deps)} cyclic dependencies detected")
    replace_c_val = safe_num(s2_summary.get("replacement_candidates", 0))
    if replace_c_val > 0:
        risks.append(f"{int(replace_c_val)} modules flagged for replacement")
    rearch_val = safe_num(s2_summary.get("rearchitect_needed", 0))
    if rearch_val > 0:
        risks.append(f"{int(rearch_val)} modules need re-architecture")
    if total_vulns > 50:
        risks.append(f"High vulnerability count ({int(total_vulns)})")
    if high_risk > 5:
        risks.append(f"{int(high_risk)} high-risk files identified")
    s3_data = s3.get("data", [{}])
    cloud_score = safe_num(s3_data[0].get("cloud_readiness_score", 100) if s3_data else 100)
    if cloud_score < 40:
        risks.append(f"Low cloud readiness ({cloud_score}%)")
    blocking = "; ".join(risks) if risks else "No major blocking risks identified"

    row = {
        "application_name": PROJECT_NAME,
        "current_version": TECHNOLOGY,
        "business_criticality": biz_crit,
        "technical_health_score": health,
        "modernization_readiness_score": mod_readiness,
        "risk_level": risk_level,
        "recommended_action": recommended,
        "confidence_score": confidence,
        "key_blocking_risks": blocking,
    }

    sheet1 = {
        "sheet_name": "Executive Decision Summary", "sheet_number": 1,
        "generated_at": datetime.now().isoformat() + "Z",
        "technology": TECHNOLOGY, "framework": FRAMEWORK,
        "columns": ["application_name","current_version","business_criticality",
                     "technical_health_score","modernization_readiness_score","risk_level",
                     "recommended_action","confidence_score","key_blocking_risks"],
        "data": [row]
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet1, f, indent=2)
    print(f"Sheet 1 generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()
```

## Step 2: Execute

```bash
mkdir -p temp
python3 temp/sheet1_generator.py
```

## Step 3: Validate

Verify sheet1.json:
1. Has `columns` with exactly 9 entries
2. `data` has exactly 1 row
3. Row keys match column names
4. `confidence_score` is "N/A"
5. `technical_health_score` is 0-100
6. `modernization_readiness_score` is 0-100

## When Complete

Say only: `Done: Sheet 1 generated`
