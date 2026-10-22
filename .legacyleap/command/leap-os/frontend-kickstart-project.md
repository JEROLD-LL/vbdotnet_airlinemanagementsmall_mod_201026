# Step 0: Kickstart Project

Before proceeding, collect the following input from user:

1. **CSS Framework**: CSS framework to use (e.g., Tailwind, Material-UI, Ant Design, Chakra UI, Bootstrap)

Once input is collected, use the **frontend-react-kickstart** agent to scaffold the project as `{{metadata.modernize}}/{{metadata.legacy_project_name}}-web/`.
Rules:

- Follow `leap-os/instructions/tech-stack.md`, before starting the kick start which gives the core dependencies required to install
- Create AGENTS.md based on the tech-stack.md file and include verification commands, architectural boundaries, interaction parity expectations, canonical type ownership, and error-handling rules
- Should not create any new component other than index and main
- The generated codebase MUST expose `files:changed`, `lint:changed`, `typecheck`, `test`, `test:e2e`, `check:domain-types`, `check:arch`, `verify:changed`, `verify`, and `verify:full` scripts in `package.json`
- The generated codebase MUST include config and support files for ESLint, Vitest, Playwright, and custom Node verification scripts
- The generated custom verification scripts MUST operate on the combined staged, unstaged, and untracked file set by default
- For existing codebases, `verify:changed` MUST use changed-file linting and architectural checks as the default blocking path. `check:domain-types` may be scaffolded, but it MUST NOT be part of the default blocking path until a stable type-inventory workflow exists
