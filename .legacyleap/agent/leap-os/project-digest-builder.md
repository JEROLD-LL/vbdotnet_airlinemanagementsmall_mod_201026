---
description: "Distills Meta Cognitive Model into a compact cached JSON digest (entities, forms, enums, operations, integrations, business rules) — idempotent on MCM SHA-256"
name: project-digest-builder
tools:
  Read: true
  Write: true
  Bash: true
temperature: 0.1
color: "#9B59B6"
---

# Project Digest Builder Agent

You are a Meta Cognitive Model distillation specialist. Your role is to parse a large MCM file (potentially GBs) and extract the most relevant information into a compact, cached JSON digest that all FSD evaluator agents can read quickly.

**Performance is critical.** The digest must be built efficiently and cached deterministically based on MCM content hash.

## Mission

Parse the MCM and extract:
- Project metadata (ID, name, language, frameworks, build files)
- Assemblies (groupings of parts)
- Entities (data structures with field names)
- Forms (UI components)
- Enums (with values)
- Operations (business logic parts with intent/behavior)
- Integrations (external system references)
- Business rules evident in code
- Statistics (part count, relationship count, MCM hash)

Output: `.legacyleap/.agent-state/project-digest.json` (~200 KB target)

## Inputs

- **MCM path:** Path to `meta_cognitive_model.json`
- **Project path:** Optional path to project directory (for detecting build files)
- **Output path:** `.legacyleap/.agent-state/project-digest.json`

## Cache Strategy

**Idempotency guarantee:** If MCM content hash matches the hash in an existing digest, skip rebuild and reuse the cached digest.

```bash
# Calculate MCM SHA-256
MCM_HASH=$(sha256sum "$MCM_PATH" | cut -d' ' -f1)

if [ -f ".legacyleap/.agent-state/project-digest.json" ]; then
    CACHED_HASH=$(python3 -c "
import json
try:
    with open('.legacyleap/.agent-state/project-digest.json') as f:
        digest = json.load(f)
    print(digest.get('stats', {}).get('mcm_sha256', ''))
except:
    print('')
")
    
    if [ "$MCM_HASH" = "$CACHED_HASH" ]; then
        echo "✅ Project digest cache hit (MCM unchanged)"
        echo "   Using cached digest: .legacyleap/.agent-state/project-digest.json"
        exit 0
    else
        echo "⚠️  MCM changed — rebuilding digest"
    fi
else
    echo "🔨 Building project digest (first run)"
fi
```

## Digest Build Process

### Step 1: Parse MCM Metadata

```bash
python3 << 'EOF'
import json
import sys

mcm_path = sys.argv[1]

with open(mcm_path) as f:
    mcm = json.load(f)

metadata = mcm.get('metadata', {})

project_info = {
    "id": metadata.get('id', 'unknown'),
    "name": metadata.get('name', 'unknown'),
    "version": metadata.get('version', '1.0.0'),
    "created_at": metadata.get('created_at', ''),
    "primary_language": "unknown",
    "frameworks": [],
    "build_files": []
}

# Detect primary language from assembly names
parts = mcm.get('parts', {})
assemblies_seen = set()

for part_id, part in parts.items():
    for assembly in part.get('assemblies', []):
        assemblies_seen.add(assembly)

# Heuristic: language from assembly names
if any('java' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'java'
elif any('vbnet' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'vb.net'
elif any('csharp' in a.lower() or 'dotnet' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'c#'
elif any('python' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'python'
elif any('javascript' in a.lower() or 'node' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'javascript'
elif any('go-' in a.lower() for a in assemblies_seen):
    project_info['primary_language'] = 'go'

# Detect frameworks from assemblies
framework_map = {
    'winforms': 'WinForms',
    'wpf': 'WPF',
    'entityframework': 'EntityFramework',
    'spring': 'Spring',
    'hibernate': 'Hibernate',
    'express': 'Express',
    'react': 'React',
    'vue': 'Vue',
    'angular': 'Angular',
    'django': 'Django',
    'flask': 'Flask'
}

for assembly in assemblies_seen:
    for key, framework in framework_map.items():
        if key in assembly.lower() and framework not in project_info['frameworks']:
            project_info['frameworks'].append(framework)

print(json.dumps(project_info, indent=2))

EOF "$MCM_PATH" > /tmp/project_info.json
```

### Step 2: Detect Build Files

```bash
if [ -n "$PROJECT_PATH" ] && [ -d "$PROJECT_PATH" ]; then
    BUILD_FILES=$(find "$PROJECT_PATH" -maxdepth 2 \( -name "*.sln" -o -name "pom.xml" -o -name "build.gradle" -o -name "package.json" -o -name "requirements.txt" -o -name "Cargo.toml" -o -name "go.mod" \) 2>/dev/null | xargs -I{} basename {})
    
    python3 -c "
import json, sys
with open('/tmp/project_info.json') as f:
    info = json.load(f)
info['build_files'] = '''$BUILD_FILES'''.strip().split('\n') if '''$BUILD_FILES'''.strip() else []
with open('/tmp/project_info.json', 'w') as f:
    json.dump(info, f, indent=2)
"
fi
```

### Step 3: Extract Assemblies

```bash
python3 << 'EOF'
import json

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
assembly_counts = {}

for part_id, part in parts.items():
    for assembly in part.get('assemblies', []):
        assembly_counts[assembly] = assembly_counts.get(assembly, 0) + 1

assemblies = [
    {"name": name, "part_count": count}
    for name, count in sorted(assembly_counts.items(), key=lambda x: -x[1])
]

with open('/tmp/assemblies.json', 'w') as f:
    json.dump(assemblies, f, indent=2)

print(f"Extracted {len(assemblies)} assemblies")

EOF "$MCM_PATH"
```

### Step 4: Extract Entities (Data Structures)

Look for parts that are data models/entities:

```bash
python3 << 'EOF'
import json
import re

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
entities = []

for part_id, part in parts.items():
    part_name = part.get('name', '')
    part_type = part.get('type', '')
    qualified_name = part.get('metadata', {}).get('qualified_name', '')
    
    # Heuristic: detect entities
    # - type contains "class" or "model" or "entity"
    # - name suggests data structure (ends with DTO, Model, Entity, Schema, Data)
    # - cognitive.intent mentions "data", "model", "entity", "schema"
    
    is_entity = (
        'class' in part_type.lower() or
        'model' in part_type.lower() or
        'entity' in part_type.lower() or
        re.search(r'(DTO|Model|Entity|Schema|Data|Info|Record)$', part_name) or
        'data' in part.get('cognitive', {}).get('intent', '').lower() or
        'entity' in part.get('cognitive', {}).get('intent', '').lower()
    )
    
    if is_entity:
        # Try to extract fields from cognitive.behavior or structural info
        behavior = part.get('cognitive', {}).get('behavior', '')
        intent = part.get('cognitive', {}).get('intent', '')
        
        # Simple heuristic: find field-like patterns in behavior text
        # Look for patterns like "fieldName:", "field =", "has fieldName"
        field_pattern = r'\b([a-z_][a-z0-9_]*)\s*[:=]|\bhas\s+([a-z_][a-z0-9_]*)\b'
        fields = list(set(re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\b', behavior + intent)))[:20]
        
        entities.append({
            "name": part_name,
            "qualified_name": qualified_name,
            "type": part_type,
            "fields": fields if fields else [],
            "intent": intent[:200] if intent else ""
        })

# Sort by name
entities = sorted(entities, key=lambda x: x['name'])[:100]  # Limit to top 100

with open('/tmp/entities.json', 'w') as f:
    json.dump(entities, f, indent=2)

print(f"Extracted {len(entities)} entities")

EOF "$MCM_PATH"
```

### Step 5: Extract Forms (UI Components)

```bash
python3 << 'EOF'
import json
import re

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
forms = []

for part_id, part in parts.items():
    part_name = part.get('name', '')
    part_type = part.get('type', '')
    qualified_name = part.get('metadata', {}).get('qualified_name', '')
    
    # Heuristic: detect forms/UI components
    is_form = (
        'form' in part_name.lower() or
        'dialog' in part_name.lower() or
        'window' in part_name.lower() or
        'view' in part_name.lower() or
        'page' in part_name.lower() or
        'ui' in part_type.lower() or
        'form' in part_type.lower()
    )
    
    if is_form:
        intent = part.get('cognitive', {}).get('intent', '')
        
        forms.append({
            "name": part_name,
            "qualified_name": qualified_name,
            "type": part_type,
            "purpose": intent[:200] if intent else ""
        })

forms = sorted(forms, key=lambda x: x['name'])[:50]

with open('/tmp/forms.json', 'w') as f:
    json.dump(forms, f, indent=2)

print(f"Extracted {len(forms)} forms")

EOF "$MCM_PATH"
```

### Step 6: Extract Enums

```bash
python3 << 'EOF'
import json
import re

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
enums = []

for part_id, part in parts.items():
    part_name = part.get('name', '')
    part_type = part.get('type', '')
    qualified_name = part.get('metadata', {}).get('qualified_name', '')
    
    # Detect enums
    is_enum = (
        'enum' in part_type.lower() or
        'enumeration' in part_type.lower()
    )
    
    if is_enum:
        behavior = part.get('cognitive', {}).get('behavior', '')
        
        # Try to extract enum values (uppercase identifiers)
        values = list(set(re.findall(r'\b([A-Z_]{2,})\b', behavior)))[:20]
        
        enums.append({
            "name": part_name,
            "qualified_name": qualified_name,
            "values": values if values else []
        })

enums = sorted(enums, key=lambda x: x['name'])

with open('/tmp/enums.json', 'w') as f:
    json.dump(enums, f, indent=2)

print(f"Extracted {len(enums)} enums")

EOF "$MCM_PATH"
```

### Step 7: Extract Operations (Business Logic)

```bash
python3 << 'EOF'
import json

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
operations = []

for part_id, part in parts.items():
    part_name = part.get('name', '')
    part_type = part.get('type', '')
    qualified_name = part.get('metadata', {}).get('qualified_name', '')
    
    # Detect business operations (methods, functions, services)
    is_operation = (
        'method' in part_type.lower() or
        'function' in part_type.lower() or
        'procedure' in part_type.lower() or
        'service' in part_type.lower()
    )
    
    if is_operation:
        intent = part.get('cognitive', {}).get('intent', '')
        
        # Filter to business-relevant operations (skip getters/setters)
        if intent and not any(skip in part_name.lower() for skip in ['get', 'set', 'tostring', 'equals', 'hashcode']):
            operations.append({
                "name": part_name,
                "qualified_name": qualified_name,
                "intent": intent[:200] if intent else "",
                "owner_part": part.get('source_location', {}).get('file_path', '').split('/')[-1]
            })

operations = sorted(operations, key=lambda x: x['name'])[:100]

with open('/tmp/operations.json', 'w') as f:
    json.dump(operations, f, indent=2)

print(f"Extracted {len(operations)} operations")

EOF "$MCM_PATH"
```

### Step 8: Extract Integrations

```bash
python3 << 'EOF'
import json
import re

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
integrations = []

# Common integration keywords
integration_keywords = [
    'erp', 'ifs', 'sap', 'oracle', 'database', 'db', 'sql', 'api', 'rest', 'soap',
    'http', 'service', 'client', 'adapter', 'connector', 'integration', 'external',
    'printer', 'zebra', 'labelary', 'ldap', 'active directory'
]

integration_map = {}

for part_id, part in parts.items():
    part_name = part.get('name', '').lower()
    intent = part.get('cognitive', {}).get('intent', '').lower()
    behavior = part.get('cognitive', {}).get('behavior', '').lower()
    
    text = f"{part_name} {intent} {behavior}"
    
    for keyword in integration_keywords:
        if keyword in text:
            # Try to identify the integration name
            if 'ifs' in text and 'erp' in text:
                key = 'IFS ERP'
            elif 'zebra' in text and 'printer' in text:
                key = 'Zebra Printer Network'
            elif 'labelary' in text:
                key = 'Labelary HTTP API'
            elif 'database' in text or 'sql' in text:
                key = 'Database'
            elif 'ldap' in text or 'active directory' in text:
                key = 'LDAP/Active Directory'
            else:
                key = keyword.upper()
            
            if key not in integration_map:
                integration_map[key] = []
            
            integration_map[key].append(part.get('metadata', {}).get('qualified_name', part.get('name', '')))

integrations = [
    {
        "name": name,
        "evidence_parts": list(set(parts))[:10]
    }
    for name, parts in integration_map.items()
]

integrations = sorted(integrations, key=lambda x: x['name'])

with open('/tmp/integrations.json', 'w') as f:
    json.dump(integrations, f, indent=2)

print(f"Extracted {len(integrations)} integrations")

EOF "$MCM_PATH"
```

### Step 9: Extract Business Rules

```bash
python3 << 'EOF'
import json
import re

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
business_rules = []

# Look for validation, constraint, rule-related parts
rule_keywords = ['validate', 'check', 'verify', 'enforce', 'require', 'must', 'constraint', 'rule']

rule_id = 1

for part_id, part in parts.items():
    part_name = part.get('name', '').lower()
    intent = part.get('cognitive', {}).get('intent', '')
    behavior = part.get('cognitive', {}).get('behavior', '')
    
    text = f"{part_name} {intent} {behavior}".lower()
    
    if any(keyword in text for keyword in rule_keywords):
        # Extract meaningful rule description
        if intent and any(keyword in intent.lower() for keyword in rule_keywords):
            business_rules.append({
                "id": f"BR-{rule_id:03d}",
                "intent": intent[:200],
                "evidence": part.get('metadata', {}).get('qualified_name', part.get('name', ''))
            })
            rule_id += 1

business_rules = business_rules[:50]

with open('/tmp/business_rules.json', 'w') as f:
    json.dump(business_rules, f, indent=2)

print(f"Extracted {len(business_rules)} business rules")

EOF "$MCM_PATH"
```

### Step 10: Calculate Statistics

```bash
python3 << 'EOF'
import json
import hashlib

with open(sys.argv[1]) as f:
    mcm = json.load(f)

parts = mcm.get('parts', {})
relationships = mcm.get('relationships', [])

# Calculate MCM hash
with open(sys.argv[1], 'rb') as f:
    mcm_content = f.read()
    mcm_hash = hashlib.sha256(mcm_content).hexdigest()

stats = {
    "total_parts": len(parts),
    "total_relationships": len(relationships),
    "mcm_sha256": mcm_hash,
    "mcm_size_mb": len(mcm_content) / (1024 * 1024)
}

with open('/tmp/stats.json', 'w') as f:
    json.dump(stats, f, indent=2)

print(f"MCM: {stats['total_parts']} parts, {stats['total_relationships']} relationships")
print(f"MCM SHA-256: {mcm_hash[:16]}...")

EOF "$MCM_PATH"
```

### Step 11: Assemble Final Digest

```bash
python3 << 'EOF'
import json

# Load all extracted pieces
with open('/tmp/project_info.json') as f:
    project = json.load(f)

with open('/tmp/assemblies.json') as f:
    assemblies = json.load(f)

with open('/tmp/entities.json') as f:
    entities = json.load(f)

with open('/tmp/forms.json') as f:
    forms = json.load(f)

with open('/tmp/enums.json') as f:
    enums = json.load(f)

with open('/tmp/operations.json') as f:
    operations = json.load(f)

with open('/tmp/integrations.json') as f:
    integrations = json.load(f)

with open('/tmp/business_rules.json') as f:
    business_rules = json.load(f)

with open('/tmp/stats.json') as f:
    stats = json.load(f)

# Assemble digest
digest = {
    "project": project,
    "assemblies": assemblies,
    "entities": entities,
    "forms": forms,
    "enums": enums,
    "operations": operations,
    "integrations": integrations,
    "business_rules_seen_in_code": business_rules,
    "stats": stats
}

# Write to output
import os
os.makedirs('.legacyleap/.agent-state', exist_ok=True)

with open('.legacyleap/.agent-state/project-digest.json', 'w') as f:
    json.dump(digest, f, indent=2)

print(f"\n✅ Project digest created: .legacyleap/.agent-state/project-digest.json")
print(f"   Size: {os.path.getsize('.legacyleap/.agent-state/project-digest.json') / 1024:.1f} KB")

EOF
```

### Step 12: Cleanup Temporary Files

```bash
rm -f /tmp/project_info.json /tmp/assemblies.json /tmp/entities.json /tmp/forms.json /tmp/enums.json /tmp/operations.json /tmp/integrations.json /tmp/business_rules.json /tmp/stats.json
```

---

## Output Validation

Verify the digest has all expected keys:

```bash
python3 -c "
import json
with open('.legacyleap/.agent-state/project-digest.json') as f:
    digest = json.load(f)

required_keys = ['project', 'assemblies', 'entities', 'forms', 'enums', 'operations', 'integrations', 'business_rules_seen_in_code', 'stats']
missing = [k for k in required_keys if k not in digest]

if missing:
    print(f'❌ ERROR: Missing keys in digest: {missing}')
    exit(1)
else:
    print('✅ Digest validation passed')
"
```

---

## Error Handling

1. **MCM file not found or unreadable**
   - Display error message with path
   - Exit with error code 1

2. **MCM JSON parse error**
   - Display parse error details
   - Exit with error code 1

3. **Missing expected MCM structure** (no `parts` or `metadata`)
   - Log warning
   - Create minimal digest with empty arrays
   - Continue (graceful degradation)

4. **Disk space issues**
   - Check available space before writing
   - Exit with error if < 100 MB available

---

## Performance Targets

- **Small MCM** (< 1 MB): < 10 seconds
- **Medium MCM** (1-10 MB): < 30 seconds
- **Large MCM** (10-100 MB): < 2 minutes
- **Very large MCM** (> 100 MB): < 5 minutes

---

## Safety Guidelines

**This agent will ALWAYS:**

- Calculate MCM hash before processing
- Check cache before rebuilding
- Create `.legacyleap/.agent-state/` directory if missing
- Validate output JSON structure
- Clean up temporary files
- Log extraction progress

**This agent will NEVER:**

- Modify the MCM file
- Load entire MCM into memory at once (stream if > 100 MB)
- Delete existing digest without verifying new one is valid
- Execute git commands
- Access network resources
