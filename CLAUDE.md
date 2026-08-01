@RTK.md

# Clean Architecture & TDD Playbook

## Workflow rules

- **Step 0 — fresh worktree (MANDATORY, before any feature work):** Every
  `/intent-and-goal` pipeline must start from a clean, up-to-date default branch
  in an isolated worktree — never on the shared checkout's current branch.
  1. If the session is **already in a worktree**, skip this step.
  2. Otherwise call the **`EnterWorktree`** tool with `name` set to a short slug
     of the feature. With `worktree.baseRef: fresh` (set in `settings.json`) this
     branches off `origin/<default-branch>` after fetching, so the worktree starts
     from current master on its own branch — regardless of which branch the main
     checkout is on. All pipeline artifacts live inside it.
  3. **Do not warm dependencies yourself.** A `PostToolUse` hook on `EnterWorktree`
     runs the repo's `.claude/warm-deps.sh` detached and silently if present.
     A global default (`~/.claude/warm-deps.sh`) auto-detects the ecosystem
     (pnpm/npm/yarn → install; Kotlin/Java/Gradle/Maven/Go/Rust → no-op), and any
     repo can override it with its own `.claude/warm-deps.sh`. If you later need to
     confirm deps are ready, read the one-line `.claude/warm-deps.status` (`ok` =
     ready), never `.claude/warm-deps.log`. Convention:
     `~/.claude/hooks/worktree-warming.md`.
- **New features/use cases**: after Step 0, run
  `/intent-and-goal <feature description>`. It scopes the feature and, once you
  approve the scenarios, drives the rest of the pipeline to completion. Never
  implement a feature any other way.

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

## Inner-loop granularity in the agent pipeline: batch red-green per class

The Red-Green cycle above is stated per test — the human discipline. In the
`/intent-and-goal` pipeline the `developer` agent instead batches it **per class**: write
ALL of a class's planned tests, run once and verify **every one is red for the reason its
row states** (batch-red-verified — a test green on the first run is vacuous and is fixed
before any production code), then write the class's production code to green. "Test precedes
code, seen to fail" still holds; only the granularity moves from per-row to per-class. The
Ordered Test List's row sequence stays the design order (simplest transformation first). The
**outer loop is unchanged: one scenario at a time.**

Rationale — measured, not assumed. An eval-harness A/B
(`evals/experiments/batch-vs-strict-withdraw-money/`, n=3 structurally different scenarios +
a 4-runs-per-arm variance study) found batch-per-class ran the test suite ~⅓ as often
(noise-free) and was ~30–50% cheaper with no quality regression (mutation / CRAP / duplication /
reviewer-finding parity), because this pipeline front-loads design into the architect +
test-designer phases — so the developer *executes* a plan rather than discovering one, which is
exactly where strict row-by-row-red earns least. This applies **only** to the plan-executing
pipeline developer; hand-written TDD outside the pipeline stays per-test.

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

## Code quality conventions

The `refactor-advisor` agent enforces patterns from the catalog at
`~/.claude/knowledge/refactor-catalog/` (start at `index.md`) —
*Comment as a missing name*, *Compose method*, *Feature envy → Move method*, and others.


