Trigger the **frontend-gherkin-test-generator** agent to generate BDD test cases from specification files.

Inputs:

- Specification files from leap-os/specs/

Rules:

- For each spec file, invoke the frontend-gherkin-test-generator agent
- Run 1 agent per spec, max 3 agents in parallel
- Output will be saved to leap-os/tests/[spec-name].feature
- Create the leap-os/tests/ folder if it doesn't exist
- Group view and element-visible checks into a single scenario per module/screen instead of creating one scenario per element
- Reduce non-essential negative scenarios. Generate only negative cases that are required for validation, authorization, recoverable API errors, or critical user-facing error handling
- Assign a priority tag to every scenario: `@priority-p0`, `@priority-p1`, or `@priority-p2`
- Add either `@positive` or `@negative` to every scenario
- Database-related scenarios are not in scope. Do not generate tests for database setup, direct database validation, stored procedures, SQL, persistence internals, or seed data
- Group keyboard actions and page focus behavior into one scenario per module/screen where possible to avoid repeated cases
