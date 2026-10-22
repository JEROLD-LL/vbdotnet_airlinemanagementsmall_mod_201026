Trigger the **frontend-api-finaliser** agent to reconcile tentative per-screen API documentation with the actual OpenAPI specification and produce finalized API documentation.

Inputs:

- Per-screen tentative API markdown files from leap-os/api/\*.md
- OpenAPI specification from leap-os/api/openapi.json

Rules:

- For each .md file in leap-os/api/, invoke the frontend-api-finaliser agent with:
  - The per-screen tentative API markdown file
  - The OpenAPI spec at leap-os/api/openapi.json
- Run 1 agent per screen file, max 3 agents in parallel
- Output will be saved to leap-os/api/final/[screen-name].md
- Create the leap-os/api/final/ folder if it doesn't exist
- Each agent should read the full openapi.json to find the actual matching endpoints
- Each API should be verified with CURL, if any authorisation header required please get it from user. If user didn't provided, lets skip verifying the API
- The finalized documentation should follow the same format as the input tentative API markdown file
- Agent should write max 5 APIs per write
