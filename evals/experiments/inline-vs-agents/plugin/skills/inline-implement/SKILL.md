---
name: inline-implement
description: "[experiment arm B] Implementation phase run inline — executes one scenario's Ordered Test List red→green, batched per class, with scoped Gradle runs. Spawns nothing."
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

You are implementing **one scenario** of a planned feature, inline. Prerequisite skills are
already loaded once for this run — **do not re-invoke**: `clean-architecture`, `testing`,
`comments`, plus `api-conventions` / `cqrs` where the plan touches HTTP or a new port.

## Phase gate (no hook — you enforce it)

Before the **first** write under any `src/` path for this scenario, `Grep` the scenario
file for `## Ordered Test List`. If absent, stop and report that planning has not run.

## The Iron Law

**No production code without a failing test first.** There must be a run where the new
tests fail before their production code exists. A test that is green on its first run is
vacuous — fix it before writing production code. Code written before its tests went red
must be deleted and reimplemented from the tests.

## Test runs are scoped

Never run the workspace-wide suite inside the red/green loop. Run only the test classes
this scenario owns:

```bash
./gradlew test --tests '<FQN or pattern from the plan table headings>'
```

A compile error during a red run counts as red and is expected while dependencies are
being introduced. The full `./gradlew build` runs **once**, at the end of the scenario.

## Turn economy

**Batch independent tool calls into one message** — all of a class's test files, several
call-site edits after a rename. Only serialise when a later call genuinely depends on an
earlier one's result.

**A class's tests and its production code are NOT independent** — batch-red sits between
them. Never put a test file and the production file it drives in the same message: that
skips the only step that proves the test can fail.

## Implementation mode

1. Read `specification.md` (context only — **do not modify** except the progress checkbox
   in step 6) and `SCENARIO-XX.md`. `## Structure & Contracts` is reference material;
   `## Ordered Test List` is your execution order; the `Status` column is the single
   progress tracker and the resume point after a compaction (first `☐` row).

2. Walk the table **grouped by class**, taking the classes in the order their rows first
   appear (all of a class's rows form one batch). For each class, run one batched TDD
   cycle:

   - **Write all of that class's tests at once (RED)** — each named by its row's FLFI
     label and seeded to create its Contradiction, in row order.
   - **Verify batch-red (non-negotiable).** Run the scoped command **once**; every new
     test must fail for the reason its row states. A test *green* on this first run is
     vacuous — fix it so it genuinely exercises the behaviour **before writing any
     production code**.
   - **Write the class's production code (GREEN)** — the smallest code that forces each
     row's TPP transformation and makes all of the class's tests pass. Run once, confirm
     green.
   - Refactor if useful; everything stays green.
   - Flip each row's Status as its test passes, using the vocabulary below.

3. **Plan↔code fidelity.** A test the plan did not foresee but the implementation forced
   (constructor guard, value-object query, mapper) is appended to the appropriate table as
   a new row (`✅ UNPLANNED — <what it supports>`). When the scenario is done, the Ordered
   Test List is a **complete inventory**: every test maps to a row and every row to a test.

4. If a row turns out already-green or genuinely redundant when you reach it, mark it
   `✅ EARLY-GREEN` rather than forcing a false red — or drop it only if truly vacuous.
   Never silently skip it.

5. When every row is `✅`, run `./gradlew build` and confirm green.

6. Check `- [x] SCENARIO-XX` in `specification.md` — **one line**: what was built and any
   defect found. Nothing else.

7. Optionally write `SCENARIO-XX.record.md` for a human reader — a defect witnessed red, a
   deviation from the plan, a mutant applied. **Never** into the plan or the specification;
   those are re-read every scenario.

### Status vocabulary (mandatory, machine-read)

A Status cell MUST begin with exactly one of these tokens, followed by ` — ` and prose.

| Token | Means |
|---|---|
| `☐` | not yet reached |
| `✅ RED→GREEN` | failed first for its Contradiction's reason, then passed |
| `✅ EARLY-GREEN` | green on its batch-red run — say why kept and name the mutant that shows it is not vacuous |
| `✅ UNPLANNED` | TDD forced it — say what it supports |
| `✅ DEFERRED` | written, executes elsewhere — say where |
| `❌ BLOCKED` | could not pass — say why, then stop and report |

Example: `✅ RED→GREEN — red with expected:<50> but was:<0> before the deposit was applied`

## Failure rule

If a row cannot go green after reasonable effort, mark it `❌ BLOCKED`, stop, and report.
Do not bypass tests, weaken assertions, or mark incomplete work done.
