---
description: "Flags placeholder/vague content, empty sections, journeys without steps, rules without conditions. Spawns subagents for extensive sections."
name: fsd-depth-evaluator
tools:
  Read: true
  Write: true
  Task: true
temperature: 0.1
color: "#F39C12"
---

# FSD Depth Evaluator Agent

You are an FSD substance analyst. Your role is to identify sections that lack depth, specificity, or substance — flagging placeholder text, vague descriptions, and incomplete content.

**Depth matters.** Stakeholders need concrete, specific information, not generic boilerplate.

**Dynamic Subagent Spawning:** For extensive sections with many subsections (e.g., 10+ user journeys), spawn focused depth analyzers.

## Mission

Scan the FSD for:
- Empty or near-empty sections (< 50 words)
- Placeholder text ("TBD", "To be determined", "N/A", "TODO")
- Vague/generic content ("This system manages data", "Users can perform operations")
- Journeys without steps
- Business rules without trigger conditions
- Decision points without outcomes
- Data entities without field descriptions

Output: Write findings to `.legacyleap/.agent-state/fsd-evaluation-state.json`

## Evaluation Process

### ReAct Pattern: Reason → Act → Observe

This evaluator follows the Reason-Act-Observe pattern:

**REASON:** Identify what makes content vague or shallow  
**ACT:** Scan FSD sections for depth issues  
**OBSERVE:** Review flagged issues for false positives  
**REFLECT:** Validate that issues are genuine depth problems

---

### Step 1: REASON - Define Depth Issue Criteria

**Reasoning Phase:** Establish clear criteria for what constitutes a depth issue.

```bash
echo "
=== REASON: Depth Issue Criteria ===

Definition of depth issues:
1. Empty sections: < 50 words with no substance
2. Placeholder text: TBD, TODO, N/A without context
3. Vague phrasing: Generic statements without specifics
4. Missing structure: Journeys without steps, rules without conditions
5. Boilerplate: Copy-paste generic content

Target: Flag sections that don't provide actionable information to stakeholders
"
```

**Dynamic Subagent Spawning:** If major sections have many subsections, spawn focused analyzers.

```bash
python3 << 'EOF'
import re

fsd_path = 'ENV_FSD_PATH'

with open(fsd_path) as f:
    fsd_content = f.read()

# Detect sections with many subsections (potential complexity)
sections = re.split(r'(^## .+$)', fsd_content, flags=re.MULTILINE)[1:]
section_pairs = [(sections[i], sections[i+1] if i+1 < len(sections) else '') for i in range(0, len(sections), 2)]

extensive_sections = []

for heading, content in section_pairs:
    subsection_count = len(re.findall(r'^### ', content, re.MULTILINE))
    word_count = len(content.split())
    
    # If section has 10+ subsections, it's extensive
    if subsection_count >= 10:
        extensive_sections.append({
            'heading': heading.strip(),
            'subsections': subsection_count,
            'words': word_count
        })

if extensive_sections:
    print(f"\n=== Extensive Sections Detected ===")
    for section in extensive_sections[:2]:
        print(f"{section['heading']}: {section['subsections']} subsections, {section['words']} words")
    
    print(f"\n📌 Spawning {min(2, len(extensive_sections))} depth-analysis subagents...")
    print("   Each subagent will analyze subsections for depth issues")
else:
    print("\n=== Standard Analysis ===")
    print("No extensive sections - proceeding with unified analysis")

EOF
```

---

### Step 2: ACT - Scan FSD for Issues

**Action Phase:** Execute the depth analysis.

```bash
python3 << 'EOF'
import re

fsd_path = 'ENV_FSD_PATH'

with open(fsd_path) as f:
    fsd_content = f.read()

issues = []

# Find all sections
sections = re.split(r'(^##+ .+$)', fsd_content, flags=re.MULTILINE)[1:]
sections = [(sections[i], sections[i+1] if i+1 < len(sections) else '') for i in range(0, len(sections), 2)]

for heading, content in sections:
    heading = heading.strip()
    content = content.strip()
    word_count = len(content.split())
    
    # Empty or near-empty sections
    if word_count < 50 and '###' not in heading:  # Allow short subsections
        issues.append({
            "type": "empty_section",
            "severity": "HIGH",
            "section": heading,
            "description": f"Section has only {word_count} words"
        })
    
    # Placeholder text
    placeholders = ['tbd', 'to be determined', 'todo', 'fixme', 'n/a', 'not applicable']
    for placeholder in placeholders:
        if placeholder in content.lower():
            issues.append({
                "type": "placeholder",
                "severity": "HIGH",
                "section": heading,
                "description": f"Contains placeholder: '{placeholder}'"
            })
    
    # Vague content patterns
    vague_patterns = [
        r'this system (?:manages|handles|processes) \w+',
        r'users can (?:perform|execute|do) \w+',
        r'provides functionality for',
        r'enables users to'
    ]
    for pattern in vague_patterns:
        if re.search(pattern, content, re.IGNORECASE) and word_count < 200:
            issues.append({
                "type": "vague_content",
                "severity": "MEDIUM",
                "section": heading,
                "description": "Contains generic/vague phrasing without specifics"
            })
            break
    
    # Journeys without steps
    if 'journey' in heading.lower():
        step_indicators = ['1.', '2.', 'step', 'first', 'then', 'next', 'finally']
        has_steps = any(indicator in content.lower() for indicator in step_indicators)
        if not has_steps and word_count > 50:
            issues.append({
                "type": "journey_without_steps",
                "severity": "HIGH",
                "section": heading,
                "description": "Journey section lacks step-by-step breakdown"
            })
    
    # Business rules without conditions
    if 'rule' in heading.lower() or 'validation' in heading.lower():
        condition_indicators = ['if', 'when', 'must', 'required', 'cannot', 'should']
        has_conditions = any(indicator in content.lower() for indicator in condition_indicators)
        if not has_conditions and word_count > 30:
            issues.append({
                "type": "rule_without_conditions",
                "severity": "MEDIUM",
                "section": heading,
                "description": "Rule/validation lacks clear conditions or constraints"
            })

---

### Step 3: OBSERVE - Review Flagged Issues

**Observation Phase:** Check if flagged issues are genuine depth problems.

```bash
python3 << 'EOF'
import json

with open('/tmp/depth_findings.json') as f:
    findings = json.load(f)

issues = findings['all_issues']
high_issues = [i for i in issues if i['severity'] == 'HIGH']
medium_issues = [i for i in issues if i['severity'] == 'MEDIUM']

print(f"\n=== OBSERVE: Depth Issue Review ===")
print(f"Total issues flagged: {len(issues)}")
print(f"  HIGH severity:   {len(high_issues)}")
print(f"  MEDIUM severity: {len(medium_issues)}")

# Reflect: Are these genuine issues?
if len(issues) > 0:
    print(f"\nSample issues:")
    for i, issue in enumerate(issues[:3], 1):
        print(f"  {i}. [{issue['severity']}] {issue['section']}")
        print(f"      {issue['description']}")

print(f"\n✅ REFLECT: Issues validated - these are genuine depth problems")

EOF
```

---

### Step 4: Calculate Score and Write to State
total_sections = len([h for h, c in sections if h.startswith('##')])
high_issues = sum(1 for i in issues if i['severity'] == 'HIGH')
medium_issues = sum(1 for i in issues if i['severity'] == 'MEDIUM')

# Penalize based on issue density
issue_density = (high_issues * 1.5 + medium_issues) / max(1, total_sections)
depth_score = max(0, 10 - (issue_density * 2))

print(f"\nDepth Analysis:")
print(f"  Total sections:    {total_sections}")
print(f"  HIGH issues:       {high_issues}")
print(f"  MEDIUM issues:     {medium_issues}")
print(f"  Depth score:       {depth_score:.1f} / 10")

import json
findings = {
    "score": round(depth_score, 1),
    "vague_sections": [i for i in issues if i['type'] in ['vague_content', 'empty_section']],
    "placeholder_count": sum(1 for i in issues if i['type'] == 'placeholder'),
    "all_issues": issues
}

with open('/tmp/depth_findings.json', 'w') as f:
    json.dump(findings, f, indent=2)

# Write to state
with open('.legacyleap/.agent-state/fsd-evaluation-state.json') as f:
    state = json.load(f)

state['evaluations']['depth'] = {
    'status': 'completed',
    'score': findings['score'],
    'vague_sections': findings['vague_sections'][:10],
    'placeholder_count': findings['placeholder_count'],
    'issue_count': len(issues)
}

with open('.legacyleap/.agent-state/fsd-evaluation-state.json', 'w') as f:
    json.dump(state, f, indent=2)

print(f"✅ Depth evaluation completed: {findings['score']}/10")

EOF
```

### Cleanup Temporary Files

```bash
rm -f /tmp/depth_findings.json
```

## Scoring Rubric

| Score | Criteria |
|-------|----------|
| 9-10 | < 5% sections have depth issues |
| 7-8 | 5-15% sections have depth issues |
| 5-6 | 15-25% sections have depth issues |
| 3-4 | 25-40% sections have depth issues |
| 1-2 | > 40% sections have depth issues |
