---
description: Generate Application Inventory Count (Sheet 8) via dynamic Python script
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

You generate Sheet 8 (Application Inventory Count) by querying Neo4j for MCM data, writing a self-contained Python script, and executing it.

## CRITICAL RULES

1. **DO NOT hold large data in context** — write a Python script to process it
2. **DO NOT read `.legacyleap/metadata.json`** — use Project Context values
3. **DO NOT write to `/tmp/`** — use workspace `temp/` directory
4. **DO NOT create extra files** — only `temp/` working files and the final `sheet8.json`

## Project Context (Provided by Orchestrator)

Values received in delegation prompt:
- **TECH_ASSESSMENT_PATH**: Output directory for sheet8.json and where dependencies.json lives
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

**Query 1 — Parts with classification info:**
```cypher
MATCH (p:Part)
WHERE p.projectId = $project_id
RETURN p.id AS id, p.name AS name, p.kind AS kind,
       p.ast_type AS ast_type, p.file_path AS file_path,
       p.qualified_name AS qualified_name
ORDER BY p.id
SKIP $skip LIMIT $limit
```

**Query 2 — Assemblies:**
```cypher
MATCH (a:Assembly)
WHERE a.projectId = $project_id
RETURN a.id AS id, a.name AS name, a.kind AS kind
ORDER BY a.id
SKIP $skip LIMIT $limit
```

Accumulate each page's rows into a single list per query before moving on.

## Step 2: Save Neo4j Results to Temp

```bash
mkdir -p temp
```

Write results to `temp/neo4j_data.json`.

## Step 3: Write Dynamic Python Script

Write to `temp/sheet8_generator.py`, filling in paths from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os
from datetime import datetime

TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"
MCM_JSON_PATH = "{MCM_JSON_PATH}"
NEO4J_DATA_PATH = "temp/neo4j_data.json"
OUTPUT_FILE = os.path.join(TECH_ASSESSMENT_PATH, "sheet8.json")
DEPS_FILE = os.path.join(TECH_ASSESSMENT_PATH, "dependencies.json")

KIND_TO_CATEGORY = {
    "controller": "controllers", "service": "services",
    "repository": "repositories", "repo": "repositories",
    "entity": "entities", "model": "entities",
    "endpoint": "api_endpoints", "action": "api_endpoints", "api": "api_endpoints",
    "method": "methods", "configuration": "configurations",
    "form": "ui_screens", "screen": "ui_screens", "view": "ui_screens", "page": "ui_screens",
    "module": "classes", "class": "classes",
}

def load_from_neo4j():
    if not os.path.exists(NEO4J_DATA_PATH):
        return None
    with open(NEO4J_DATA_PATH) as f:
        data = json.load(f)
    if not data.get("parts"):
        return None
    return data

def load_from_mcm():
    if not os.path.exists(MCM_JSON_PATH):
        return None
    with open(MCM_JSON_PATH) as f:
        mcm = json.load(f)
    parts = []
    for p in mcm.get("nodes", {}).get("parts", []):
        ident = p.get("identity", {})
        struct = p.get("structural", {})
        parts.append({"id": p.get("id",""), "name": ident.get("name", p.get("name","")),
                       "kind": (p.get("kind","") or "").lower(),
                       "ast_type": (struct.get("ast_type","") or "").lower(),
                       "file_path": ident.get("file_path", p.get("file_path","")),
                       "qualified_name": ident.get("qualified_name","")})
    assemblies = []
    for a in mcm.get("nodes", {}).get("assemblies", []):
        ident = a.get("identity", {})
        assemblies.append({"id": a.get("id",""), "name": ident.get("name", a.get("name","")),
                           "kind": (a.get("kind","") or "").lower()})
    return {"parts": parts, "assemblies": assemblies}

def load_dependencies():
    if not os.path.exists(DEPS_FILE):
        return []
    with open(DEPS_FILE) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "dependencies" in data:
            return data["dependencies"]
        if "by_category" in data:
            merged = []
            for cat_list in data["by_category"].values():
                if isinstance(cat_list, list): merged.extend(cat_list)
            return merged
        all_deps = []
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "name" in v[0]:
                all_deps.extend(v)
        if all_deps: return all_deps
    return []

def classify_parts(all_parts):
    result = {"controllers":[],"services":[],"repositories":[],"classes":[],"methods":[],
              "api_endpoints":[],"entities":[],"configurations":[],"ui_screens":[]}
    for part in all_parts:
        kind = (part.get("kind","") or "").lower()
        ast_type = (part.get("ast_type","") or "").lower()
        effective_kind = kind
        if kind in ("class", "") and ast_type in KIND_TO_CATEGORY:
            effective_kind = ast_type
        category = KIND_TO_CATEGORY.get(effective_kind, "classes")
        result[category].append({"name": part.get("name","Unknown"), "path": part.get("file_path",""),
                                  "id": part.get("id",""), "kind": kind})
    return result

def generate():
    data = load_from_neo4j()
    if not data:
        data = load_from_mcm()
    if not data:
        print("No MCM data found")
        return

    all_parts = data["parts"]
    all_assemblies = data.get("assemblies", [])
    classified = classify_parts(all_parts)
    namespaces = [{"name": a.get("name",""), "type": a.get("kind",""), "id": a.get("id","")} for a in all_assemblies]
    dependencies = load_dependencies()

    sheet8 = {
        "sheet_name": "Application Inventory Count", "sheet_number": 8,
        "generated_at": datetime.now().isoformat() + "Z",
        "app_type": "web" if classified["controllers"] or classified["ui_screens"] else "desktop",
        "summary_counts": {
            "api_endpoints": len(classified["api_endpoints"]),
            "ui_screens": len(classified["ui_screens"]),
            "controllers": len(classified["controllers"]),
            "repositories": len(classified["repositories"]),
            "services": len(classified["services"]),
            "methods": len(classified["methods"]),
            "classes": len(classified["classes"]),
            "entities": len(classified["entities"]),
            "configurations": len(classified["configurations"]),
            "modules_packages": len(namespaces),
            "third_party_dependencies": len(dependencies),
        },
        "inventory": {
            "api_endpoints": classified["api_endpoints"],
            "ui_screens": classified["ui_screens"],
            "controllers": classified["controllers"],
            "repositories": classified["repositories"],
            "services": classified["services"],
            "methods": classified["methods"],
            "classes": classified["classes"],
            "entities": classified["entities"],
            "configurations": classified["configurations"],
            "modules_packages": namespaces,
            "third_party_dependencies": dependencies,
        }
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sheet8, f, indent=2)
    print(f"Sheet 8 generated: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()
```

## Step 4: Execute

```bash
python3 temp/sheet8_generator.py
```

## Step 5: Validate

Verify sheet8.json:
1. Has `summary_counts` with exactly 11 keys
2. Has `inventory` with exactly 11 keys
3. summary_counts values match inventory array lengths

## When Complete

Say only: `Done: Sheet 8 generated`
