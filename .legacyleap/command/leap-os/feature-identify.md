---
description: "Identify the features from the MCM, map every UI snapshot to its screen, and refresh the feature table"
agent: feature-identifier
---

# `/feature-identify`

Builds the feature list from the MCM and places every snapshot image on a screen, so `/feature-spec` and `/feature-spec-all` can run without stopping. Run it once before writing specs, and again when the MCM or the snapshot folder changes.

## What happens

1. The `feature_facts` tool groups the MCM screens into features and matches images to screens by file name (`features`).
2. The agent opens every image the tool could not place, and every image placed by file-name words only, and maps it by what it shows: the content area, heading, fields and title bar.
3. It asks you only about images it is not sure of.
4. The tool regenerates the feature table in `scan_assessment_reports/features/README.md` (`status`).
5. You get the feature list with the reason each screen was grouped, the snapshot decisions, and the next command to run.

## Files

| File | Purpose |
|---|---|
| `scan_assessment_reports/features/features.json` | Feature list (pointers into the MCM, no copied text) |
| `scan_assessment_reports/features/snapshot-map.json` | Which screen each snapshot shows (`manual` entries are kept on every rebuild) |
| `scan_assessment_reports/features/README.md` | Generated feature table, order and spec status |
| `scan_assessment_reports/features/features-roadmap.md` | Checklist of endpoint-owning methods per feature; tick a checkbox once the corresponding API is implemented |
