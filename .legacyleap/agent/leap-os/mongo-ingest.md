---
description: Ingest technical assessment sheet data into MongoDB
mode: all
temperature: 0.1
tools:
  read_file: true
  write: true
  bash: true
---

You ingest all technical assessment sheet JSON files into MongoDB collections.

## CRITICAL RULES

1. Do NOT create markdown files, text reports, completion reports, or summary documents
2. Do NOT modify any files besides the temporary Python script
3. **NEVER use `/tmp/`** — use workspace `temp/` directory only
4. Only ingest technical assessment data — NOT MCM data

## Project Context (Provided by Orchestrator)

When invoked by the orchestrator, you receive these values in the delegation prompt.
Use these directly. Do NOT read `.legacyleap/metadata.json` yourself.

- **WORKSPACE**: Absolute path to workspace root
- **PROJECT_NAME**: Project name
- **PROJECT_ID**: Unique project identifier (UUID)
- **TECHNOLOGY**: Technology plugin
- **FRAMEWORK**: Legacy framework
- **TECH_ASSESSMENT_PATH**: Absolute path to tech_assessment/ directory

If these values are missing, fall back to reading `.legacyleap/metadata.json`.

## CRITICAL: Temporary File Handling

- NEVER use `/tmp/` for any purpose
- Create `temp/` in workspace root: `mkdir -p temp`
- Write all temporary files there
- DO NOT delete `temp/` — the orchestrator handles cleanup after all agents complete

## Step 1: Write Ingestion Script

```bash
mkdir -p temp
```

Write `temp/mongo_ingest.py` with the following logic, filling in actual values from PROJECT_CONTEXT:

```python
#!/usr/bin/env python3
import json, os, re
from datetime import datetime, timezone

PROJECT_NAME = "{PROJECT_NAME}"
PROJECT_ID = "{PROJECT_ID}"
TECHNOLOGY = "{TECHNOLOGY}"
FRAMEWORK = "{FRAMEWORK}"
TECH_ASSESSMENT_PATH = "{TECH_ASSESSMENT_PATH}"

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.environ.get("MONGODB_DATABASE", "")

SHEET_COLLECTION_MAP = {
    "sheet1.json": "executive_summary",
    "sheet2.json": "modernization_matrix",
    "sheet3.json": "app_summary",
    "sheet4.json": "architecture_overview",
    "sheet7.json": "code_quality",
    "sheet8.json": "inventory",
    "sheet9.json": None,
}

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')

def get_db_name():
    if MONGODB_DATABASE:
        return MONGODB_DATABASE
    return f"{slugify(PROJECT_NAME)}_assessment"

def enrich(doc):
    doc["_project_id"] = PROJECT_ID
    doc["_project_name"] = PROJECT_NAME
    doc["_technology"] = TECHNOLOGY
    doc["_framework"] = FRAMEWORK
    doc["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    return doc

def ingest():
    try:
        from pymongo import MongoClient, ASCENDING
        from pymongo.errors import ConnectionFailure
    except ImportError:
        print("pymongo not installed. Run: pip install pymongo")
        return

    db_name = get_db_name()
    print(f"Connecting to {MONGODB_URI}, database: {db_name}")

    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        return

    db = client[db_name]
    total_docs = 0

    for sheet_file, collection_name in SHEET_COLLECTION_MAP.items():
        path = os.path.join(TECH_ASSESSMENT_PATH, sheet_file)
        if not os.path.exists(path):
            print(f"  Skipping {sheet_file}: not found")
            continue
        with open(path) as f:
            sheet = json.load(f)

        if sheet_file == "sheet9.json":
            for cname, key in [("issues", "issues"), ("suggestions", "suggestions")]:
                items = sheet.get(key, [])
                if items:
                    col = db[cname]
                    col.delete_many({"_project_id": PROJECT_ID})
                    docs = [enrich(dict(item)) for item in items]
                    for i in range(0, len(docs), 500):
                        col.insert_many(docs[i:i+500])
                    col.create_index([("_project_id", ASCENDING)])
                    total_docs += len(docs)
                    print(f"  {cname}: {len(docs)} docs")
            continue

        if sheet_file == "sheet8.json":
            col = db[collection_name]
            col.delete_many({"_project_id": PROJECT_ID})
            inventory = sheet.get("inventory", {})
            docs = []
            for category, items in inventory.items():
                if isinstance(items, list):
                    for item in items:
                        doc = dict(item) if isinstance(item, dict) else {"name": str(item)}
                        doc["_category"] = category
                        docs.append(enrich(doc))
            if docs:
                for i in range(0, len(docs), 500):
                    col.insert_many(docs[i:i+500])
            col.create_index([("_project_id", ASCENDING)])
            counts_doc = enrich({"_type": "summary_counts", **sheet.get("summary_counts", {})})
            col.insert_one(counts_doc)
            total_docs += len(docs) + 1
            print(f"  {collection_name}: {len(docs)+1} docs")
            continue

        data = sheet.get("data", [])
        col = db[collection_name]
        col.delete_many({"_project_id": PROJECT_ID})
        if data:
            docs = [enrich(dict(row)) for row in data]
            for i in range(0, len(docs), 500):
                col.insert_many(docs[i:i+500])
            total_docs += len(docs)
        col.create_index([("_project_id", ASCENDING)])
        print(f"  {collection_name}: {len(data)} docs")

    meta_col = db["assessment_metadata"]
    meta_col.delete_many({"_project_id": PROJECT_ID})
    meta_doc = enrich({
        "_type": "assessment_run",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_documents": total_docs,
        "sheets_ingested": [f for f in SHEET_COLLECTION_MAP if os.path.exists(os.path.join(TECH_ASSESSMENT_PATH, f))],
    })
    meta_col.insert_one(meta_doc)
    total_docs += 1

    print(f"\nIngestion complete: {db_name}, {total_docs} total documents")
    client.close()

if __name__ == "__main__":
    ingest()
```

## Step 2: Execute

```bash
pip install pymongo >/dev/null 2>&1 || true
export MONGODB_URI="${MONGODB_URI:-mongodb://localhost:27017}"
python3 temp/mongo_ingest.py
```

## When Complete

Say only: `Done: MongoDB ingestion complete`
