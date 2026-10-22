# Error Handling

## Purpose

Legacy modernization work often hides defects when failures are swallowed. This profile requires explicit, visible, and testable error handling.

## Mandatory Rules

- Empty `catch` blocks are forbidden.
- `catch` blocks MUST either recover intentionally, add context and rethrow, or translate the failure into a user-visible error state.
- Loading, success, empty, and error states MUST be handled explicitly for async flows.
- User-facing failures MUST produce a visible response such as inline validation, alert text, toast, dialog, or error panel.
- Silent failure is forbidden unless the specification explicitly documents a safe fire-and-forget case.
- Unexpected failures SHOULD be logged or surfaced through the project’s chosen diagnostics path.

## Spec Requirements

Every screen specification MUST include:

- expected user-visible error states
- retry or recovery behavior where applicable
- known backend/API failure scenarios

## Task Requirements

Task acceptance criteria MUST include the expected error behavior and verification requirements.

## Verification Requirements

- ESLint MUST fail on empty catches and similar swallowed-error patterns.
- Unit or integration tests MUST cover relevant error states.
- Playwright scenarios MUST cover critical failure paths for user-visible flows.
