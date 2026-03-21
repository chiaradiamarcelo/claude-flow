@RTK.md

# Clean Architecture & TDD Playbook

## Workflow rules

- **New features/use cases**: when starting a new task, run `/intent-and-goal`.
- **Scenarios first**: follow the `/intent-and-goal` flow to refine the intent, then propose Gherkin scenarios, and create a Source of Truth (SoT) specification file before any code is written.
- **MANDATORY: Use the `architect` + `developer` + `review-gate` to implement scenarios**: when the user asks to proceed with a scenario (e.g. "proceed with SCENARIO-01"), follow this pipeline:
  1. **`architect`** → writes the implementation plan into the SoT file.
  2. **`developer`** → implements the plan with TDD.
  3. **`review-gate`** → discovers all `type: reviewer` agents (global + project), filters by changed files against each reviewer's `triggers`, launches relevant ones in parallel, and returns a consolidated report.
  4. If the review-gate verdict is **FAIL** (violations exist): spawn `developer` in fix mode with the consolidated report. Then re-run `review-gate`.
  5. If the review-gate verdict is **PASS**: scenario is done.
  - Never implement a scenario manually without going through this pipeline.

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
- **No Faking Use Cases in Acceptance Tests**: Behavioral verifications (AT/Scenario tests) MUST use the real Use Case implementation. Only fake external dependencies (repositories, external APIs).
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

