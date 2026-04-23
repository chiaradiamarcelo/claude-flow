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

## Approach: Outside-In, Layer-by-Layer

Work in cohesive layer slices from the outside in. The RED-GREEN-REFACTOR cycle applies at the **layer level**, not line by line.

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

Repeat RED → GREEN → REFACTOR for each subsequent layer.

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
