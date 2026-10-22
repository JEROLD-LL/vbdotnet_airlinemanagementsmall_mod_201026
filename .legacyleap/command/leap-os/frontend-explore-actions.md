Trigger the **frontend-vbnet-ui-action-explorer** agent to analyze VB.NET screen components and extract screen-level UI action documentation.

Rules:

- Input is a screen name and its component file path, referenced from `leap-os/screens.md`
- Analyze the legacy VB.NET codebase under `legacy_code/`
- Trace only user-triggered UI actions at screen level
- Do not infer, invent, or document REST API endpoints
- Do not convert database calls, service calls, or stored procedures into assumed APIs
- Do not include modernization suggestions, React implementation guidance, API contracts, data models, or business-rule rewrites
- Output will be saved to `leap-os/actions/[screen-name].md`
- Run 1 agent per screen, sequentially
- Each agent should write max 10 actions at a single write to the file, so it can handle larger files/screens
