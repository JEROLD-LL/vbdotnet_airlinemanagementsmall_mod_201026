---
name: frontend-generate-agents-md
description: Generate AGENTS.md from tech-stack.md to define coding standards and conventions for all agents
agent: frontend-agents-md-generator
---

Trigger the **frontend-agents-md-generator** agent to create an AGENTS.md file that all subsequent agents must follow.

Rules:
- Input is leap-os/instructions/tech-stack.md
- If codebase exists at `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web`, scan it to reflect actual conventions
- Output will be saved to `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web/AGENTS.md`
- AGENTS.md should cover the
    tech stack with versions
    Primary dependency manager & package json scripts exposed
    Linting and formatting scripts
    Folder structures and Naming conventions
    Routing pattern
    Form handling
    How State management is been handled, expecting pattern
    Unit testing flows
    API integration flows
    ENV variables,
    Interaction parity expectations
    Canonical business type ownership
    Error handling rules
    Architecture boundaries and verification commands
    Agent should not make any assumptions, if not clear get input from user
