Trigger the **frontend-react-dev** agent to implement tasks from task files.

Inputs:

- Task files from leap-os/tasks/
- Codebase at `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web`

Rules:

- For each task file, read and parse all tasks and execute with frontend-react-dev agent, 1 agent per task file.
- Run sequentially - 1 agent at a time, no parallel execution
- Implement directly in `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web` (existing mock codebase)
- Agent must write unit tests for the implemented code
- Agent must validate with Playwright after implementation
- Agent must run the project verification commands before considering a task complete:
  - `pnpm verify`
  - `pnpm verify:full` when e2e prerequisites are available
- Mark tasks as completed in the task file only after the required verification commands pass
