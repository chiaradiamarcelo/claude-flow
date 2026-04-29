---
name: tdd
description: Use when writing any new code or feature to enforce the TDD red-green-refactor cycle.
argument-hint: <what-to-implement>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

Implement using strict TDD: **$ARGUMENTS**

## Iron Law

**No production code without a failing test first.** If you didn't watch the test fail, you don't know if it tests the right thing. Code written before a test must be deleted and reimplemented from the test — no exceptions.

## The cycle (one behavior at a time)

Each behavior is one tracer bullet: RED → GREEN → REFACTOR. Then move to the next behavior. Do not batch tests across behaviors.

### 1. RED — Write one failing test

- Write the smallest test that describes the next behavior.
- Run the test suite. The new test must fail.
- **Hard gate: paste the failing output before proceeding.** No output, no GREEN.
- Verify the failure is for the expected reason (missing feature — not a typo, not a missing import).
- If the test passes without new code, the behavior already exists — pick a different test.

### 2. GREEN — Make it pass

- Write the minimum production code to make the failing test pass.
- Run the test suite. All tests must pass.
- **Hard gate: paste the passing output before proceeding.** No output, no REFACTOR.
- Do not add behavior beyond what the current test requires.
- Do not refactor yet.

### 3. REFACTOR — Improve design

- Remove duplication, improve naming, separate concerns.
- Keep tests green throughout. If they break, the change was too aggressive — undo and try smaller.
- Keep domain rules in domain/application; keep domain framework-free.

Then return to RED for the next behavior.

## Anti-pattern: writing tests in bulk

**Do not write all of a layer's tests first, then all of the production code.** Tests written in bulk validate imagined behavior, not actual behavior — they commit to a contract guess that no running code has confirmed. Each cycle should learn from the previous one.

A plan from an architect tells you *which* tests and *what order*. It does not tell you the test's setup, assertions, or fake API — those are design decisions made during the cycle, one test at a time.

## Rationalization prevention

LLMs generate plausible excuses for skipping or deferring TDD. Common ones and why they fail:

| Excuse | Reality |
|---|---|
| "I'll add tests after the implementation" | You won't, or you'll write tests that pass by definition — they validate what you wrote, not what should work. |
| "This is too simple to test" | Simple code breaks too. The test takes 30 seconds. |
| "I need to see the implementation shape first" | That's a spike. Spike, throw it away, then TDD. |
| "I'm just refactoring, not adding behavior" | Existing tests must pass throughout. If there are no tests, write characterization tests first. |
| "Writing the test first would be slower" | TDD is faster than debugging. It catches errors at the cheapest moment. |
| "The test is hard to write — I'll come back to it" | Hard-to-test code is hard-to-use code. The test is design feedback. Listen to it. |

If you catch yourself composing an excuse not on this list, it is still an excuse.

## Red flags — stop and restart from RED

- Writing implementation before a test.
- A test passing immediately without new code.
- Inability to explain why a test failed.
- Any reasoning beginning with "just this once."
- Manual testing claims replacing automated verification.

**Response**: delete code written without a test. Restart from RED.

## Project conventions

- Follow the `testing` skill for test structure (GWT with blank lines), fakes, and assertions.
- Test names: snake_case behavior style (e.g., `withdrawing_more_than_balance_fails`).
- API tests: `returns_<status>_when_<condition>`.
- One behavior per test.
- Use the minimum input data that proves the behavior. `add(1, 1)` proves addition; two items prove "multiple"; one missing field proves "missing required field."
- Each file is read once and written once.
- Prefer unit tests for fast feedback on inner layers; use framework slice utilities for API endpoints.
- For create/update endpoints, cover in this order:
  1. success (`201`/`204`)
  2. malformed input / parse errors (`400`)
  3. missing/invalid required domain values (`400`)
  4. non-existing resource (`404`) when applicable
  5. unexpected runtime failure (`500`) when behavior exists
