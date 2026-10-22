Trigger the **frontend-playwright-gherkin-tester** agent to execute functional tests against the web application.

Inputs:

- Gherkin feature files from leap-os/tests/
- Base URL of the running application

Rules:

- If base URL is not provided, ask the user for it before proceeding
- For each feature file, invoke the frontend-playwright-gherkin-tester agent
- Run sequentially - 1 agent at a time, no parallel execution
- Output test reports to leap-os/test-results/[feature-name]-[timestamp].md
- Create the leap-os/test-results/ folder if it doesn't exist
- Failing scenarios are blocking. A failed Playwright run means the feature is not verified and related tasks MUST NOT be marked complete.
