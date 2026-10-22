# Canonical Types

## Purpose

The same business object MUST NOT be redefined across screens. This profile requires a single canonical definition per business concept, with explicit mapping layers where API or form shapes differ.

## Mandatory Rules

- Each business object MUST have one canonical shared definition in the domain/type layer.
- Screen-local redefinitions of canonical business objects are forbidden.
- API request and response types MAY differ from canonical domain types, but conversion MUST happen through explicit mappers.
- View-model or form-model types MAY exist only when they serve a distinct UI concern and are clearly named as such.
- Types MUST be imported from shared modules instead of copied into pages, components, or hooks.
- `any` is forbidden for business objects.

## Preferred Structure

- Canonical business types: `src/domain/` or `src/types/domain/`
- API transport models: `src/services/`, `src/api/`, or feature-local `*.api.ts`
- Mapping functions: `*.mapper.ts`
- Form models: feature-local files only when necessary

## Spec Requirements

Every screen specification MUST include:

- the canonical business objects it depends on
- where those canonical types live
- any transport-to-domain or domain-to-view mappings required

## Task Requirements

Task acceptance criteria MUST verify that shared business types are reused instead of redefined.

## Verification Requirements

- The generated app MUST include a type-ownership verification script.
- For existing codebases, type-ownership verification MAY inspect the current working tree scope: staged files, unstaged tracked files, and untracked files.
- For existing codebases, blocking verification MUST NOT fail solely on domain-type ownership until the project has an explicit type inventory and reuse/create decision workflow.
- When a stable inventory workflow exists, verification MUST fail when changed files redefine canonical business types outside the approved shared location.
