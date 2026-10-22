Trigger the **frontend-existing-codebase-verifier** agent to analyze existing React codebase and document reusable components/services for current app integration.

Rules:

- Input: leap-os/screens.md (current app screens) and existing modernized codebase at `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web/`
- Run parallely - 2 agent at a time, one screen per agent.
- Agent discovers folder structure, identifies reusable components/services current app needs
- Output: leap-os/existing-codebase-inventories/[screen-name].md and leap-os/patterns-and-conventions.md
