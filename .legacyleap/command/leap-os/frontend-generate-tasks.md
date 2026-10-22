Trigger the **frontend-spec-task-generator** agent to convert specification documents into actionable task lists.

Inputs:

- Specification files from leap-os/specs/frontend/

Rules:

- For each spec file, invoke the frontend-spec-task-generator agent
- Run 1 agent per spec, max 3 agents in parallel
- Output will be saved to leap-os/tasks/[spec-name].md
- Create the leap-os/tasks/ folder if it doesn't exist
- Every task list MUST convert the enforcement sections from the spec into explicit, testable acceptance criteria and verification steps.
- Agent should batch the writes to the task file, max 2 tasks per write
