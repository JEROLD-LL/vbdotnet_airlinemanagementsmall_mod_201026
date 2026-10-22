# Interaction Parity

## Purpose

VB.NET modernization in this profile preserves legacy interaction behavior, not just visuals. Keyboard flow, focus movement, and primary action triggers are part of the functional contract and MUST be reproduced unless the specification explicitly documents an approved deviation.

## Mandatory Rules

- Pressing `Enter` in a legacy primary input MUST trigger the same primary action as the legacy screen.
- Default-button behavior from the legacy form MUST be preserved.
- Tab order and focus progression MUST follow the legacy screen unless the spec documents a justified web-specific change.
- `Escape`, function keys, arrow keys, and grid keyboard interactions visible in the legacy flow MUST be documented and implemented.
- Focus MUST remain predictable after validation failures, successful submissions, dialog open/close, and data reloads.
- If an interaction cannot be reproduced exactly on the web, the spec MUST record the deviation and define the replacement behavior.

## Spec Requirements

Every screen specification MUST include:

- an `Interaction Parity Contract`
- a table of keyboard triggers and resulting actions
- focus/Tab order expectations
- documented deviations, if any

## Task Requirements

Task acceptance criteria MUST include the relevant keyboard, focus, and default-action checks for that screen.

## Verification Requirements

- Add component or integration tests for keyboard-triggered actions and focus behavior.
- Add Playwright scenarios for critical keyboard flows.
- A screen is not complete until its interaction parity checks pass.
