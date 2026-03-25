---
name: tdd
description: Use when writing any new code or feature to enforce the TDD red-green-refactor cycle.
argument-hint: <what-to-implement>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

Implement using strict TDD: **$ARGUMENTS**

## Rules

- NEVER write production code without a failing test first.
- **Mandatory Standards**: Follow the `testing` skill for all test structure (GWT with blank lines), naming (snake_case), and fakes usage.
- **Mandatory Review**: After writing tests for a layer (RED phase) and after any refactor (REFACTOR phase), you MUST invoke the `test-reviewer` agent to validate the test quality.

## Approach: Outside-In, Layer-by-Layer

Work in cohesive layer slices from the outside in. The RED-GREEN-REFACTOR cycle applies at the **layer level**, not line by line.

### 0. UNDERSTAND & PLAN

- Read the SoT file (`docs/specifications/<feature-slug>.md`) and any relevant existing source files.
- Identify which layers are needed for this scenario.
- **Write the implementation plan in the SoT file before writing any code.** Fill in the ordered Implementation Plan checklist for the scenario being implemented. The plan drives the work — do not start coding until it is written.
- **Prepare the seam before changing signatures.** When the plan requires adding a parameter to a constructor, method, or data class that is already called in multiple places (especially tests), scan the call sites first. If 3+ sites use identical construction, extract a shared helper/fixture *before* changing the signature. This keeps the actual feature change surgical — one edit in the helper, not shotgun surgery across dozens of files. "Make the change easy (this might be hard), then make the easy change." — Kent Beck
- Do not re-read files during implementation.

### 1. RED - Write all failing tests for the current layer

- Write all tests for the current layer in one pass.
- Use project naming style:
  - Unit/domain: clear behavior in snake_case.
  - API: `returns_<status>_when_<condition>`.
- Run tests and confirm they fail.
- Show failing output.

### 2. GREEN - Implement the full layer

- Write **all** production code for this layer in one pass to make its tests pass.
- Design the interface from the test's perspective: write tests and production code for the same layer together — you already know the contract.
- Do not generalize prematurely, but do not artificially limit scope to one method at a time.
- Run tests and confirm the layer's tests pass.
- Show passing output.

### 3. REFACTOR - Improve design

- Remove duplication and improve naming.
- Keep domain rules in domain/application, not controller glue.
- Keep domain framework-free.
- Run tests again to confirm still green.

### 4. NEXT LAYER

Repeat RED → GREEN → REFACTOR for each subsequent layer as defined in the implementation plan.
Tick off the SoT checklist item as each layer is completed.

## Guidelines

- One behavior per test; one layer per cycle.
- Use the minimum input data that still reproduces the target behavior. Two items prove "multiple" as well as three; one field proves "missing required field" as well as five; `1` proves an amount as well as `50`, and `add(1, 1)` proves addition as well as `add(50, 100)`.
- Each file is read once and written once — avoid re-reading the same file multiple times.
- Start with the simplest happy path per layer, then add error/edge cases for that layer before moving inward.
- Prefer unit tests for fast feedback on inner layers.
- For API endpoints, use framework-provided slice/unit test utilities.
- In API tests, keep Given/When/Then blocks separated by blank lines.
- For create/update endpoints, cover tests in this order:
  1. success (`201`/`204`)
  2. malformed input and parse errors (`400`)
  3. missing/invalid required domain values (`400`)
  4. non-existing resource (`404`) when applicable
  5. unexpected runtime failure (`500`) when behavior exists
