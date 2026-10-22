Trigger the **frontend-vbnet-modernization-spec-writer** agent to create implementation specifications for modernizing VB.NET legacy screens.

Inputs:

- Screen list from leap-os/screens.md
- Functional requirements from leap-os/requirements/[screen-name].md
- API documentation from leap-os/api/final/[screen-name].md
- Mock implementation from `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web`

Rules:

- For each screen, invoke the frontend-vbnet-modernization-spec-writer agent with the screen name, API docs, and mock implementation path
- Run 1 agent per screen, max 3 agents in parallel
- Output will be saved to leap-os/specs/frontend/[screen-name].md
- Create the leap-os/specs/frontend/ folder if it doesn't exist
- If `leap-os/existing-codebase-inventories/` exists: refer the components and services from here for maximum re-usability, Mention what components we are going to re-use and how we integrate.
- Every generated spec MUST include explicit sections for `Interaction Parity Contract`, `Canonical Types & Data Ownership`, `Error Handling & Recovery`, `React Architecture Constraints`, and `Verification Gates`
- **Mandatory batched write protocol (MUST be included verbatim in every sub-agent prompt under a `## Write Protocol` heading):**
  - Do NOT write the entire spec in a single Write call. Writing a full spec in one call produces a huge tool input that inflates context and risks truncation.
  - Create the file with `Write` containing ONLY the first 2 sections (e.g., `Interaction Parity Contract` + `Canonical Types & Data Ownership`).
  - Append each subsequent pair of sections using `Edit` (append to end of file), max **2 sections per Edit call**.
  - After the final Edit, re-read the file to verify all 5 mandatory sections are present and ordered correctly.
  - Never bundle more than 2 sections in a single `Write`/`Edit` call, regardless of section size.
- The orchestrator MUST copy the `Write Protocol` block above into every sub-agent prompt it spawns. A sub-agent prompt that omits this block is considered malformed — do not spawn it.
