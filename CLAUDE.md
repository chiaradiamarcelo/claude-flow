@RTK.md

# Clean Architecture & TDD Playbook

## Workflow rules

- **New features/use cases**: when starting a new task, run `/intent-and-goal`.
- **Scenarios first**: follow the `/intent-and-goal` flow to refine the intent, then propose Gherkin scenarios, and create a Source of Truth (SoT) specification file before any code is written.
- **Plan all, then implement.**
  After scenarios are defined, the pipeline has two phases:

  **Phase 1 — Plan all scenarios upfront:**
  Run **`architect`** for all scenarios in parallel before any implementation begins. One scenario per architect, never batch.

  **Dependency map** (added to the SoT specification file after all plans are complete):
  Compare planned files across all scenarios. Scenarios with no shared files can run in parallel. Scenarios that share files must run sequentially. Use the dependency map to form parallel cycles for Phase 2.

  **Phase 2 — Implement in parallel cycles:**
  1. Follow the dependency map to determine which scenarios run in each cycle.
  2. Run scenarios in the current cycle in parallel — one **`developer`** per scenario, using worktree isolation.
  3. After each cycle, run **`/run-reviewers`** (once, no arguments) on all changed files.
  4. If **FAIL**: fix findings in parallel (one developer per scenario with findings). All findings (violations, warnings, suggestions) in one pass.
  5. Continue with the next cycle until all scenarios are done.
  6. After the last cycle, run **`/run-reviewers`** on all changed files (full final review). Fix all findings.

  **Rules:**
  - Never skip `/run-reviewers` after a cycle.
  - Never batch multiple scenarios in one developer.
  - Auto-continue between cycles — do not ask for permission.

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


