---
description: Generate Modernization Decision Matrix (Sheet 2) via dynamic Python script
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
mcp:
  neo4j-cypher: true
  neo4j-modeling: true
---

You generate Sheet 2 (Modernization Decision Matrix) by querying Neo4j for MCM data, writing a self-contained Python script, and executing it.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet2.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt. Use directly:

- **WORKSPACE**: Absolute path to workspace root
- **PROJECT_NAME**: Project name
- **PROJECT_ID**: `project_id` from `.legacyleap/metadata.json`. Stored as the `projectId` property on every Neo4j node. **Required** — Neo4j may hold multiple projects, so every query MUST filter on this.
- **TECHNOLOGY**: Technology plugin (dotnet, vb6, delphi, java, python)
- **FRAMEWORK**: Legacy framework
- **TECH_ASSESSMENT_PATH**: Output directory for sheet2.json
- **MCM_JSON_PATH**: Fallback MCM JSON file path

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Query Neo4j via MCP (Scoped by projectId + Paginated)

Every query below is scoped to this project via `p.projectId = $project_id` and paginated with `SKIP`/`LIMIT`. A shared Neo4j may hold many projects and very large graphs; an unfiltered match would pull wrong data and risk OOM.

**Pagination pattern:** start with `skip=0, limit=500`; repeat each query while incrementing `skip` by `limit`; stop when a page returns fewer rows than the limit. Pass parameters via the MCP tool's `params` argument, e.g. `{"project_id": "<PROJECT_ID>", "skip": 0, "limit": 500}`.

**Query 1 — Assemblies:**
```cypher
MATCH (a:Assembly)
WHERE a.projectId = $project_id
RETURN a.id AS id, a.name AS name, a.kind AS kind,
       a.architecture_layer AS architecture_layer,
       a.domain AS domain, a.language AS language
ORDER BY a.id
SKIP $skip LIMIT $limit
```

**Query 2 — Parts with metrics:**
```cypher
MATCH (p:Part)
WHERE p.projectId = $project_id
RETURN p.id AS id, p.name AS name, p.kind AS kind,
       p.ast_type AS ast_type, p.file_path AS file_path,
       p.language AS language, p.loc AS loc,
       p.cyclomatic_complexity AS cyclomatic_complexity,
       p.method_count AS method_count,
       p.qualified_name AS qualified_name
ORDER BY p.id
SKIP $skip LIMIT $limit
```

**Query 3 — Assembly-Part containment:**
```cypher
MATCH (a:Assembly)-[:CONTAINS]->(p:Part)
WHERE a.projectId = $project_id AND p.projectId = $project_id
RETURN a.id AS assembly_id, p.id AS part_id
ORDER BY a.id, p.id
SKIP $skip LIMIT $limit
```

**Query 4 — Part-to-Part CALLS (replaces USES):**
```cypher
MATCH (p1:Part)-[:CALLS]->(p2:Part)
WHERE p1.projectId = $project_id AND p2.projectId = $project_id
RETURN p1.id AS from_id, p2.id AS to_id
ORDER BY p1.id, p2.id
SKIP $skip LIMIT $limit
```

Accumulate each page's rows into a single list per query before moving on.

## Step 2: Save Neo4j Results to Temp

```bash
mkdir -p temp
```

Write the query results as JSON to `temp/neo4j_data.json`:
```json
{
  "assemblies": [results from Query 1],
  "parts": [results from Query 2],
  "contains": [results from Query 3],
  "calls": [results from Query 4]
}
```

If Neo4j returned no assemblies, note this — the script will fall back to MCM JSON.

## Step 3: Write Dynamic Python Script

Write the following Python script to `temp/sheet2_generator.py`. Fill in the actual paths from PROJECT_CONTEXT where marked with `{...}`.

The script MUST implement this EXACT logic:

```python
#!/usr/bin/env python3
import json, sys, os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import bisect

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
MCM_JSON_PATH = "{MCM_JSON_PATH}"
NEO4J_DATA_PATH = "temp/neo4j_data.json"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet2.json")
TECHNOLOGY = "{TECHNOLOGY}".lower()
FRAMEWORK = "{FRAMEWORK}".lower()

OBSOLETE_TECHNOLOGIES = {"vb6","vb","visual basic 6.0","visual basic","cobol","fortran","delphi","pascal"}
OBSOLETE_FRAMEWORKS = {"visual basic 6.0","vb6","classic asp","asp 3.0","com+","dcom","delphi vcl","delphi 7"}

def load_from_neo4j():
    if not os.path.exists(NEO4J_DATA_PATH):
        return None
    with open(NEO4J_DATA_PATH) as f:
        data = json.load(f)
    if not data.get("assemblies"):
        return None
    return data

def load_from_mcm():
    if not os.path.exists(MCM_JSON_PATH):
        return None
    with open(MCM_JSON_PATH) as f:
        mcm = json.load(f)
    assemblies = []
    for a in mcm.get("nodes", {}).get("assemblies", []):
        ident = a.get("identity", {})
        bnd = a.get("boundary", {})
        assemblies.append({"id": a.get("id",""), "name": ident.get("name", a.get("name","")),
                           "kind": ident.get("kind", a.get("kind","")),
                           "architecture_layer": bnd.get("architecture_layer", a.get("architecture_layer","")),
                           "domain": bnd.get("domain", ident.get("domain",""))})
    parts = []
    for p in mcm.get("nodes", {}).get("parts", []):
        ident = p.get("identity", {})
        struct = p.get("structural", {})
        metrics = struct.get("metrics", {})
        parts.append({"id": p.get("id",""), "name": ident.get("name", p.get("name","")),
                       "kind": ident.get("kind", p.get("kind","")),
                       "language": ident.get("language",""),
                       "loc": metrics.get("loc", 0),
                       "cyclomatic_complexity": metrics.get("cyclomatic_complexity", 0),
                       "method_count": metrics.get("method_count", 0)})
    rels = mcm.get("relationships", mcm.get("edges", {}).get("relationships", []))
    contains = [{"assembly_id": r["from"], "part_id": r["to"]} for r in rels if r.get("type","").upper() == "CONTAINS"]
    calls = [{"from_id": r["from"], "to_id": r["to"]} for r in rels if r.get("type","").upper() in ("USES","CALLS")]
    return {"assemblies": assemblies, "parts": parts, "contains": contains, "calls": calls}

def generate():
    data = load_from_neo4j()
    source = "Neo4j"
    if not data:
        data = load_from_mcm()
        source = "MCM JSON"
    if not data or not data["assemblies"]:
        print("No assembly data found. Writing empty sheet2.json")
        empty = {"sheet_name":"Modernization Decision Matrix","sheet_number":2,
                 "generated_at":datetime.now().isoformat()+"Z","technology":TECHNOLOGY,
                 "framework":FRAMEWORK,"columns":["module","rehost_feasibility","refactor_feasibility",
                 "rearchitect_need","replacement_indicator","estimated_effort","primary_drivers"],
                 "summary":{"total_modules":0,"rehost_feasible":0,"rearchitect_needed":0,"replacement_candidates":0},"data":[]}
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE,'w') as f: json.dump(empty, f, indent=2)
        return

    print(f"Loading data from {source}: {len(data['assemblies'])} assemblies, {len(data['parts'])} parts")

    asm_lookup = {a["id"]: a for a in data["assemblies"]}
    part_lookup = {p["id"]: p for p in data["parts"]}
    assembly_parts = defaultdict(list)
    part_assembly = {}
    for c in data["contains"]:
        assembly_parts[c["assembly_id"]].append(c["part_id"])
        if c["part_id"] not in part_assembly:
            part_assembly[c["part_id"]] = c["assembly_id"]

    efferent = defaultdict(set)
    afferent = defaultdict(set)
    for call in data["calls"]:
        from_asm = part_assembly.get(call["from_id"])
        to_asm = part_assembly.get(call["to_id"])
        if from_asm and to_asm and from_asm != to_asm:
            efferent[from_asm].add(to_asm)
            afferent[to_asm].add(from_asm)

    total_assemblies = len(data["assemblies"])
    cyclic_assemblies = set()
    for a in data["assemblies"]:
        aid = a["id"]
        for dep in efferent.get(aid, set()):
            if aid in efferent.get(dep, set()):
                cyclic_assemblies.add(aid)
                break

    is_obsolete_tech = TECHNOLOGY in OBSOLETE_TECHNOLOGIES or FRAMEWORK in OBSOLETE_FRAMEWORKS
    max_conn = 2 * max(total_assemblies - 1, 1)

    LOC_T = [200, 1000, 5000]; LOC_S = [0, 1, 2, 3]
    COUP_T = [10, 30, 60]; COUP_S = [0, 1, 2, 3]
    PART_T = [5, 20]; PART_S = [0, 1, 2]
    EFF_T = [3, 5, 8]; EFF_L = ["S", "M", "L", "XL"]

    results = []
    for asm in data["assemblies"]:
        aid = asm["id"]
        pids = assembly_parts.get(aid, [])
        parts = [part_lookup[pid] for pid in pids if pid in part_lookup]
        part_count = len(parts)
        total_loc = sum(p.get("loc", 0) or 0 for p in parts)
        complexities = [p.get("cyclomatic_complexity", 0) or 0 for p in parts if (p.get("cyclomatic_complexity", 0) or 0) > 0]
        avg_cx = round(sum(complexities) / len(complexities), 1) if complexities else 0
        langs = set((p.get("language","") or "").lower() for p in parts if p.get("language"))
        has_obsolete_lang = bool(langs & OBSOLETE_TECHNOLOGIES)
        eff = len(efferent.get(aid, set()))
        aff = len(afferent.get(aid, set()))
        coupling = min(round((eff + aff) / max_conn * 100, 1), 100.0)
        has_cycle = aid in cyclic_assemblies
        is_obs = is_obsolete_tech or has_obsolete_lang

        # Decision rules
        rehost = "Yes" if not has_cycle and coupling < 30 else ("Partial" if not has_cycle and coupling < 60 else "No")
        refactor = "Yes" if coupling < 40 and avg_cx < 15 and not has_cycle else ("Partial" if coupling < 70 and avg_cx < 25 else "No")
        rearchitect = "Yes" if (has_cycle and coupling >= 40) or coupling >= 70 else ("Partial" if has_cycle or coupling >= 40 else "No")
        replacement = "Yes" if is_obs and rearchitect == "Yes" else ("Partial" if is_obs or (rearchitect == "Yes" and refactor == "No") else "No")
        effort_score = (LOC_S[bisect.bisect_right(LOC_T, total_loc)] + COUP_S[bisect.bisect_right(COUP_T, coupling)]
                        + PART_S[bisect.bisect_right(PART_T, part_count)] + (1 if has_cycle else 0))
        effort = EFF_L[bisect.bisect_right(EFF_T, effort_score)]
        drivers = []
        if is_obs: drivers.append("Obsolescence")
        if has_cycle: drivers.append("Architecture")
        if avg_cx > 10 or coupling > 30: drivers.append("Tech Debt")
        if not drivers: drivers = ["Minimal"]

        layer = asm.get("architecture_layer", "")
        label = f"{asm['name']} ({layer})" if layer else asm["name"]
        results.append({"module": label, "rehost_feasibility": rehost, "refactor_feasibility": refactor,
                         "rearchitect_need": rearchitect, "replacement_indicator": replacement,
                         "estimated_effort": effort, "primary_drivers": ", ".join(drivers)})

    effort_order = {"XL":0,"L":1,"M":2,"S":3}
    replacement_order = {"Yes":0,"Partial":1,"No":2}
    results.sort(key=lambda r: (replacement_order.get(r["replacement_indicator"],3), effort_order.get(r["estimated_effort"],4)))

    replace_yes = sum(1 for r in results if r["replacement_indicator"] == "Yes")
    rearch_yes = sum(1 for r in results if r["rearchitect_need"] == "Yes")
    rehost_yes = sum(1 for r in results if r["rehost_feasibility"] == "Yes")

    sheet2 = {
        "sheet_name": "Modernization Decision Matrix", "sheet_number": 2,
        "generated_at": datetime.now().isoformat() + "Z",
        "technology": TECHNOLOGY, "framework": FRAMEWORK,
        "columns": ["module","rehost_feasibility","refactor_feasibility","rearchitect_need",
                     "replacement_indicator","estimated_effort","primary_drivers"],
        "summary": {"total_modules": len(results), "rehost_feasible": rehost_yes,
                     "rearchitect_needed": rearch_yes, "replacement_candidates": replace_yes},
        "data": results
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet2, f, indent=2)
    print(f"Sheet 2 generated: {OUTPUT_FILE} ({len(results)} modules)")

if __name__ == "__main__":
    generate()
```

## Step 4: Execute the Script

```bash
python3 temp/sheet2_generator.py
```

## Step 5: Validate Output

Read the generated `sheet2.json` and verify:
1. File exists at `{TECH_ASSESSMENT_PATH}/sheet2.json`
2. Has `sheet_name`, `sheet_number`, `columns`, `data` keys
3. `columns` has exactly 7 entries
4. Each row in `data` has exactly 7 matching keys

If validation fails, report the error.

## When Complete

Say only: `Done: Sheet 2 generated with X modules`
