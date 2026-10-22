Trigger the **frontend-vbnet-api-explorer** agent to analyze VB.NET screen components and extract API endpoint documentation.

Rules:

- Input is a screen name and its component file path, referenced from leap-os/screens.md
- Should not have any additional information on the API documentation (business rules, validation, suggestion, data model etc)
- Output will be saved to leap-os/api/[screen-name].md
- Run 1 agent per screen, do it sequentially
- each agent should write max 5 APIs at single write to the file, so it can handle larger files/screens.
