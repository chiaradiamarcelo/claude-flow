@RTK.md

# Clean Architecture & TDD Playbook

## Workflow rules

- **New features/use cases**: when starting a new task, run `/intent-and-goal`.
- **Scenarios first**: follow the `/intent-and-goal` flow to refine the intent, then propose Gherkin scenarios, and create a Source of Truth (SoT) specification file before any code is written.
- **Sequential pipeline.**
  After scenarios are defined, run them one at a time:

  **For each scenario in order (top-to-bottom in `## BDD Acceptance Progress`):**
  1. Run **`architect`** to plan it (produces `SCENARIO-XX.md`).
  2. Run **`developer`** to implement it.
  3. Move to the next unchecked scenario.

  **After all scenarios are implemented:**
  4. Run **`/run-reviewers`** (once, no arguments) on all changed files.
  5. If **FAIL**: run **`developer`** in fix mode with the consolidated findings (all violations, warnings, suggestions in one pass).
  6. Run **`/run-reviewers`** again. Fix any remaining findings the same way.

  **Rules:**
  - One scenario at a time. Never run multiple architects or developers in parallel.
  - Never batch multiple scenarios in one architect or developer call.
  - Never skip `/run-reviewers` after all scenarios are implemented.
  - Auto-continue — do not ask for permission between steps.

## Methodology: TDD (Red-Green-Refactor)

1. **Red**: write a failing test first.
2. **Green**: write the smallest code to pass.
3. **Refactor**: clean while keeping tests green.
4. Test file naming:
   - Domain/unit tests: `<ClassName>Test`
   - API controller slice tests: `<ControllerName>IT`
5. Use descriptive test names that read as specifications (snake_case like `returns_400_when_creating_with_invalid_amount`).

## VERY IMPORTANT: TDD applies to every production change

- Every production change must be preceded by a failing test.
- Bug fix: reproduce with a test first, then fix.
- Refactor: no behavior change, keep tests green.

## VERY IMPORTANT: Test design rules

- Tests are declarative. Avoid control flow (`if`, `for`, `while`, `switch`) in test bodies.
- One scenario per test.
- Use explicit fixtures/fakes for deterministic setup.
- Keep Given-When-Then separated by blank lines (no `// Given` comments).

## API test conventions

- For controller behavior, prefer framework-provided slice/unit test utilities.
- Mock controller dependencies.
- Assert status code first, then payload/headers.
- Cover validation categories explicitly:
  - malformed input / parse errors -> `400`
  - missing/invalid required domain values -> `400`
  - non-existing resource on update/delete/get -> `404`
  - unexpected runtime failures where defined -> `500`

When writing or modifying tests, invoke the `testing` skill for full conventions. Enforced by the `test-reviewer` agent.


