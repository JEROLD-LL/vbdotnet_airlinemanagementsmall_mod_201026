Trigger the **frontend-vb6-functional-analyzer** agent to extract functional requirements from the legacy VB.NET/VB6 screens.

Rules:

- Read the screen list from leap-os/screens.md
- For each screen, invoke the frontend-vb6-functional-analyzer agent with the screen name and its mapped file path
- Run 1 agent per screen, max 3 agents in parallel
- Output will be saved to leap-os/requirements/[screen-name].md
- Create the leap-os/requirements/ folder if it doesn't exist
