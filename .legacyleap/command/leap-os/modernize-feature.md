---
description: "Interactively modernize or resume one scanned feature using stack-specific build-fix and unit-test agents from metadata"
agent: modernization-orchestrator
---

# Modernize Feature

Start the resumable feature modernization workflow.

Work only inside the directory where the TUI is running. Do not read or write
files outside that directory, including parent folders and absolute paths that
resolve elsewhere.

The orchestrator reads `.legacyleap/metadata.json` (and `target_tech.json` when
configured) to resolve the **target** tech stack, then selects the matching
build-fix and unit-test agents. It reads `features-roadmap.md` from the
scan-assessment folder (fallback `features/feature-API-roadmap.md`). Checkboxes
are the progress record. Each feature lists API endpoints as **METHOD and path**
lines; legacy qualified names live in parentheses on those lines for transpile
only and are not shown in the feature picker. It lists unchecked features and
asks which one to modernize. It does not choose a feature, and it does not
change checkboxes until the user names one. If that feature has no endpoint
lines, it marks only that feature `[x]`, tells the user, and asks for the next
feature. Otherwise it starts at the first unchecked endpoint and handles each
remaining unchecked endpoint sequentially:

1. inspect legacy code to choose application config extensions, then transpile
   the qualified name from that endpoint's roadmap line (parentheses or
   backtick fallback);
2. run the metadata-selected build-fix agent to repair the generated build;
3. run the metadata-selected unit-test agent for files git reports as added or
   updated under `modernize/target/<projectName>` (or
   `.modernize/target/<projectName>`), returning the created/updated file list
   and test execution result;
4. run the build-fix agent again to confirm build status and produce the
   summary; and
5. tick that endpoint's checkbox in the roadmap. When every endpoint under
   the feature is checked, tick the feature checkbox too.

Run this command again after an interruption or failure. Checked endpoints and
checked features are skipped. Each run asks which feature to modernize before
updating the roadmap. A feature with no endpoints is marked completed only
after the user names it, then the user is asked for the next feature.

Do not assume a language; always take the target stack from metadata. A
feature named in the request is used without asking again.
