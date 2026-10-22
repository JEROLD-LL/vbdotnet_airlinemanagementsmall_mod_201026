---
description: Generate a Technical Specification Document from MCM domain catalog + source-code-fabric MCP
agent: tsd
---

Generate the full TSD for this project using `.legacyleap/scripts/leap-os/tsd/sections.json`.
Ground every section from ApplicationDomain catalogs and source-code-fabric MCP
tools only (no Part/comprehension tools). Assemble `Latest_tsd.md` under
`comprehend/technical_doc/v_<n>/Latest_TSD_Document/`, using `v_0` on the first
run and the next `v_<n>` when a `Latest_tsd.md` already exists. Keep section JSON
under `.legacyleap/tsd-output/<project_id>/`.

Project: $ARGUMENTS
