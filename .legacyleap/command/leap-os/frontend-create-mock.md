Trigger the **frontend-vbnet-to-leap-os-mock** agent to create a modernised implementation from a VB.NET screenshot.

Rules:

- Input screenshots are located in leap-os/screenshots/ folder
- If `leap-os/existing-codebase-inventories/` exists, identify the best matching inventory file for the screenshot and provide it to the agent as reuse guidance
- If `leap-os/patterns-and-conventions.md` exists, provide it to the agent before implementation
- Output will be placed under `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web/` following tech-stack.md conventions
- Run sequentially with 1 screenshot per agent to ensure consistent tech stack implementation
- For mock creation, stay UI-first.
- Avoid introducing new backend, query, or service layers unless explicitly
  required.
- Reuse existing shared UI building blocks and patterns before creating new
  feature-local abstractions.
