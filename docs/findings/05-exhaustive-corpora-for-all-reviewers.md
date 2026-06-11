# Finding 05 — Exhaustive corpora for the other four reviewers

**Date:** 2026-06 · **Area:** `evals/{api,arch,refactor-advisor,ui-test}-reviewer/`
**Status:** built and green (50 fixtures added; 79 across all five reviewers)

## The change

Replicated the 29-fixture `test-reviewer` corpus method (finding 04) for the
remaining four reviewers — one focused fixture per rule, otherwise clean, plus a
deliberate clean *control* per reviewer:

| Reviewer | Fixtures | Rule source | Clean control |
|---|---|---|---|
| `api-reviewer` | 13 | `api-conventions` skill | PASS |
| `arch-reviewer` | 11 | `clean-architecture` skill | PASS |
| `refactor-advisor` | 12 | `clean-architecture` + `refactor-catalog` | **FAIL (only SUGGESTIONs)** |
| `ui-test-reviewer` | 14 | `ui-testing` skill | PASS (after a fix) |

Also added an **agent-name filter to `run_all.sh`** (`./evals/run_all.sh
api-reviewer`) so one corpus runs without re-dispatching the others — notably the
stale-cache `test-reviewer` 29-fixture re-run (~$1.7, finding 03 gotcha).

## What it caused / what it revealed

The interesting signal came from the **clean controls** — fixtures of idiomatic
code asserting `PASS` (no issues). They split the reviewers into two kinds:

### 1. Structural reviewers do not over-trigger

`api-reviewer` and `arch-reviewer` returned **PASS with zero issues** on a clean
controller and a clean aggregate. A reviewer whose rules are *structural*
(layer boundaries, REST shape, file placement) has a finite, checkable rule set —
clean code genuinely satisfies all of them. The strict "any issue ⇒ FAIL" gate
is well-behaved for these.

### 2. The advisory reviewer can never return PASS

`refactor-advisor`, given a minimal already-refactored use case (orchestrate-only,
`Money` value object, get-less accessors, no comments), **still found a defensible
`SUGGESTION`** — `accountId: String` → an `AccountId` value object. There is
always one more value object to extract, one more method to compose. This is the
**empirical evidence for the strict-gate / advisory-SUGGESTION question (the
deferred decision in `PROGRESS.md`):** an improvement-oriented reviewer is a
*permanent FAIL* under "any issue ⇒ FAIL."

The stable, measurable fact is the **severity** of what it finds: on clean code
it surfaces **only SUGGESTIONs — zero VIOLATION/WARNING**. So we did not force the
control green; we converted it into the regression test
`refactor-advisor/fixtures/clean-code-only-suggestions` that pins exactly that
(`expectedStatus FAIL`, `VIOLATION max 0`, `SUGGESTION min 1`). The finding is now
encoded as a test, not a memory.

### 3. A reviewer caught a rule the fixture author missed

The `ui-test-reviewer` clean control *failed* first time — not over-triggering,
but a **correct** catch: it flagged `userEvent.click()` (static) where the
`ui-testing` skill (line 164) requires the `const user = userEvent.setup(); await
user.click(...)` instance pattern. The "clean" fixture wasn't clean. Fixing the
fixture (and the four other `userEvent`-using fixtures, so each isolates exactly
one smell) made it PASS. **A green control is also a check on your own idea of
"idiomatic."**

## Why (mechanism)

- **Structural rules are closed-world; quality rules are open-world.** "No verb
  in the URL" is satisfiable; "could this be cleaner?" never is. The gate
  semantics that fit a closed-world reviewer (any issue ⇒ FAIL) mis-fit an
  open-world one.
- **Thorough reviewers add incidental findings.** Several focused FAIL fixtures
  (e.g. the naming ones) *also* drew an extra `userEvent.setup()` finding. They
  still passed because we assert `mustMention` for the *target* rule, not an exact
  issue count (finding 04 §3, §5). Confirmed the method holds at scale.

## Gotchas hit (all finding-04 traps, re-confirmed)

- **`mustMention` wording miss.** `should-prefixed-name` asserted `"naming"`; the
  reviewer wrote *"Test name pattern … rename to …"* — no substring `"naming"`.
  Fixed to the root `"name"`. Pick a root the reviewer actually emits.
- **Severity over-constraint avoided.** The `primitive-obsession` fixture dropped
  its `SUGGESTION min 1` floor (a thorough reviewer might rank it WARNING); the
  clean-code probe caps `VIOLATION` but not `WARNING`, for the same reason.

## Verdict

All four corpora green; 79 fixtures now form the reviewer regression net. The
strict-gate decision is no longer a hunch — fixture `clean-code-only-suggestions`
demonstrates and *guards* the fact that `refactor-advisor` cannot pass a strict
gate, which is the input the decision needs.
