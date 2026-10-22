Trigger the **frontend-vb-legacy-screen-mapper** agent to analyze the legacy VB.NET/VB6 codebase and generate screen documentation.

Rules:

- Analyze the legacy codebase located in legacy_code/ folder
- Output will be saved to leap-os/screens.md
- Run sequentially with max 1 agent when processing large projects to avoid resource conflicts
