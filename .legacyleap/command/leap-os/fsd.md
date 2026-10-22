---
description: Generate a Functional Specification Document from MCM domain catalog + source-code-fabric MCP
agent: fsd
---

Generate the stakeholder FSD using `.legacyleap/scripts/leap-os/fsd/sections.json`
and `.legacyleap/scripts/leap-os/fsd/template.md.j2`.
An architecture analyst then a system analyst write shared briefs first.
Section agents research from those briefs, ApplicationDomain catalogs, and any
other `source-code-fabric` MCP tool their section needs, then write fragments.
Assemble `Latest_fsd.md` only via `render_template`.

Arguments must be labeled. Pass exactly one of:

- `project_id=<id>`
- `application_id=<id>`

An unlabeled bare id is rejected. Show both labeled forms in the error.

When `project_id=` is given, keep section JSON under
`.legacyleap/fsd-output/<project_id>/` and publish under
`comprehend/functional_doc/v_<n>/Latest_FSD_Document/`.

When `application_id=` is given, the agent lists every project in that
application, requires published domains on each, and builds one FSD covering
all of them. Scratch lives under `.legacyleap/fsd-output/app_<application_id>/`.
Publish under
`comprehend/functional_doc/application/<application_id>/v_<n>/Latest_FSD_Document/`.
Use `v_0` on the first run and the next `v_<n>` when a `Latest_fsd.md` already
exists in that folder.

$ARGUMENTS
