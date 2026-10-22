Use the **frontend-orchestrator** subagent to run the vbdotnet_to_dot_net_9 UI modernization journey.

Input required:

- Legacy application in `legacy_code/`.
- Screenshots in `leap-os/screenshots/`.
- `leap-os/instructions/tech-stack.md`.
- Fresh or existing application selection. Ask at startup when it was not supplied with the command.

Rules:

- Inspect the configured `modernize` folder for valid React applications, show the detected paths, and recommend fresh or existing.
- Do not silently select a flow from directory existence. Ask the person to confirm the recommendation.
- For the existing flow, require a selected React app under the configured `modernize` folder and validate its `package.json`, React dependency, and `src/` directory.
- For the fresh flow, require the target path to be absent or empty before scaffolding.
- Run discovery, requirements, mocks, API exploration, specs, tasks, implementation, and tests without asking the person to start each command.
- Stop for the CSS framework on a fresh app, for `leap-os/api/openapi.json`, for API contract approval, and for the test base URL.
- Use `leap-os/screens.md` as the screen inventory. When `scan_assessment_reports/meta_cognitive_model.json` contains a complete screen inventory, use that file instead.
- Do not read or edit application source in the orchestrator.

Output:

```text
leap-os/orchestration.md
```
