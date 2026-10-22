# React Architecture

## Purpose

This profile modernizes legacy VB.NET screens into maintainable React applications. Visual fidelity does not excuse weak React structure.

## Mandatory Rules

- Presentational components MUST NOT perform direct API calls.
- Async data access MUST live in services, feature APIs, hooks, or equivalent orchestration layers.
- Business logic MUST NOT be buried inline in JSX.
- Canonical business types MUST be shared and imported from the approved domain/type layer.
- Screen-level logic SHOULD be extracted into feature modules, hooks, or services when it exceeds trivial event wiring.
- Derived state MUST NOT be copied into local state unless there is a clear reason.
- Forms MUST use the project’s selected form and validation pattern consistently.
- Reuse existing components and services before introducing new ones.
- New routes MUST integrate into the existing application router; do not create a second app shell or nested `BrowserRouter`.

## New Project Requirements

Every newly scaffolded frontend codebase for this profile MUST include:

- lint rules enforcing error handling and React hooks discipline
- unit/integration test setup
- Playwright e2e setup
- architecture verification scripts
- a `verify` command and a full verification command that includes e2e tests

## Verification Requirements

- Lint MUST fail on forbidden architectural patterns the project can detect statically.
- Custom verification scripts MUST fail on forbidden imports or duplicate domain-type ownership.
- Tasks MUST NOT be marked complete until the project verification command passes.
