---
description: Generate Architecture Overview (Sheet 4) via dynamic Python script
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

You generate Sheet 4 (Architecture Overview) by querying Neo4j for MCM data, writing a self-contained Python script, and executing it.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet4.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **TECH_ASSESSMENT_PATH**: Output directory for sheet4.json
- **MCM_JSON_PATH**: Fallback MCM JSON file path
- **PROJECT_ID**: `project_id` from `.legacyleap/metadata.json` (stored as `projectId` on every Neo4j node). **Required** — always scope queries with this.

If missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Query Neo4j via MCP (Scoped by projectId + Paginated)

Every query is scoped to this project via `projectId = $project_id` and paginated with `SKIP`/`LIMIT`. Use batches of 500, increment `$skip` by `$limit` per iteration, and stop when a page returns fewer rows than the limit. Pass parameters via the MCP tool's `params` argument, e.g. `{"project_id": "<PROJECT_ID>", "skip": 0, "limit": 500}`.

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

**Query 2 — Parts:**
```cypher
MATCH (p:Part)
WHERE p.projectId = $project_id
RETURN p.id AS id, p.name AS name, p.kind AS kind
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

**Query 4 — Part-to-Part CALLS:**
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

Write results as JSON to `temp/neo4j_data.json`.

## Step 3: Write Dynamic Python Script

Write to `temp/sheet4_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os
from collections import defaultdict
from datetime import datetime

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
MCM_JSON_PATH = "{MCM_JSON_PATH}"
NEO4J_DATA_PATH = "temp/neo4j_data.json"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet4.json")

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
                           "architecture_layer": bnd.get("architecture_layer", a.get("architecture_layer",""))})
    parts = [{"id": p.get("id","")} for p in mcm.get("nodes", {}).get("parts", [])]
    rels = mcm.get("relationships", mcm.get("edges", {}).get("relationships", []))
    contains = [{"assembly_id": r["from"], "part_id": r["to"]} for r in rels if r.get("type","").upper() == "CONTAINS"]
    calls = [{"from_id": r["from"], "to_id": r["to"]} for r in rels if r.get("type","").upper() in ("USES","CALLS")]
    return {"assemblies": assemblies, "parts": parts, "contains": contains, "calls": calls}

def generate():
    data = load_from_neo4j()
    if not data:
        data = load_from_mcm()
    if not data or not data["assemblies"]:
        empty = {"sheet_name":"Architecture Overview","sheet_number":4,
                 "generated_at":datetime.now().isoformat()+"Z",
                 "columns":["module_layer","dependency_count","cyclic_dependency","cross_repo_dependency",
                            "boundary_violation","coupling_score","architectural_risk","change_impact"],
                 "summary":{"total_modules":0,"high_risk":0,"medium_risk":0,"low_risk":0,
                            "cyclic_dependencies":0,"cross_repo_dependency":"N/A","boundary_violations":"N/A"},
                 "data":[]}
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE,'w') as f: json.dump(empty, f, indent=2)
        return

    assembly_parts = defaultdict(list)
    part_assembly = {}
    for c in data["contains"]:
        assembly_parts[c["assembly_id"]].append(c["part_id"])
        if c["part_id"] not in part_assembly:
            part_assembly[c["part_id"]] = c["assembly_id"]

    total_assemblies = len(data["assemblies"])
    efferent = defaultdict(set)
    afferent = defaultdict(set)
    for call in data["calls"]:
        from_asm = part_assembly.get(call["from_id"])
        to_asm = part_assembly.get(call["to_id"])
        if from_asm and to_asm and from_asm != to_asm:
            efferent[from_asm].add(to_asm)
            afferent[to_asm].add(from_asm)

    cyclic_assemblies = set()
    for a in data["assemblies"]:
        aid = a["id"]
        for dep in efferent.get(aid, set()):
            if aid in efferent.get(dep, set()):
                cyclic_assemblies.add(aid)
                break

    max_conn = 2 * max(total_assemblies - 1, 1)
    results = []

    for asm in data["assemblies"]:
        aid = asm["id"]
        eff = len(efferent.get(aid, set()))
        aff = len(afferent.get(aid, set()))
        has_cycle = aid in cyclic_assemblies
        coupling = min(round((eff + aff) / max_conn * 100, 1), 100.0)

        risk_score = 0
        if has_cycle: risk_score += 2
        if coupling >= 70: risk_score += 2
        elif coupling >= 40: risk_score += 1
        arch_risk = "High" if risk_score >= 4 else ("Medium" if risk_score >= 2 else "Low")
        impact = "High" if aff >= 3 else ("Medium" if aff >= 1 else "Low")

        layer = asm.get("architecture_layer", "")
        label = f"{asm['name']} ({layer})" if layer else asm["name"]

        results.append({
            "module_layer": label, "dependency_count": eff,
            "cyclic_dependency": "Yes" if has_cycle else "No",
            "cross_repo_dependency": "N/A", "boundary_violation": "N/A",
            "coupling_score": coupling, "architectural_risk": arch_risk, "change_impact": impact
        })

    risk_order = {"High":0,"Medium":1,"Low":2}
    results.sort(key=lambda r: (risk_order.get(r["architectural_risk"],3), -r["coupling_score"]))

    high = sum(1 for r in results if r["architectural_risk"] == "High")
    med = sum(1 for r in results if r["architectural_risk"] == "Medium")
    low = sum(1 for r in results if r["architectural_risk"] == "Low")
    cyc = sum(1 for r in results if r["cyclic_dependency"] == "Yes")

    sheet4 = {
        "sheet_name": "Architecture Overview", "sheet_number": 4,
        "generated_at": datetime.now().isoformat() + "Z",
        "columns": ["module_layer","dependency_count","cyclic_dependency","cross_repo_dependency",
                     "boundary_violation","coupling_score","architectural_risk","change_impact"],
        "summary": {"total_modules": len(results), "high_risk": high, "medium_risk": med,
                     "low_risk": low, "cyclic_dependencies": cyc,
                     "cross_repo_dependency": "N/A", "boundary_violations": "N/A"},
        "data": results
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet4, f, indent=2)
    print(f"Sheet 4 generated: {OUTPUT_FILE} ({len(results)} modules)")

if __name__ == "__main__":
    generate()
```

## Step 4: Execute

```bash
python3 temp/sheet4_generator.py
```

## Step 5: Validate

Verify sheet4.json:
1. Has `columns` with exactly 8 entries
2. `cross_repo_dependency` and `boundary_violation` are "N/A" for all rows
3. `summary` has required keys

## When Complete

Say only: `Done: Sheet 4 generated with X modules`
