# Finding 06 — Testing a generative agent (the architect)

**Date:** 2026-06 · **Area:** `evals/architect/`, `evals/check_plan.py`, `run_all.sh`
**Status:** built and green (3 fixtures, unit layer of the confidence pyramid)

## The change

The reviewers are pure functions — code in, JSON verdict out — so `eval_grade.py`
grades their stdout. The **architect is generative**: it reads
`specification.md` and *writes an artifact* (`SCENARIO-XX.md`, a checklist plan).
There is no JSON verdict to grade. So testing it needed a different shape:

- **Grade the artifact, not stdout.** New grader `evals/check_plan.py` diffs the
  scratch run dir against the frozen `input/` (new files = scratch − input) and
  asserts coarse, non-determinism-tolerant facts about the plan the architect
  wrote: `planMustExist`, `writesNoCode`, `minSteps`, `mustMention`,
  `orderedBefore` (first line matching regex A precedes B).
- **A scratch-dir dispatch.** New `run_all.sh` **Phase 1b** copies `input/` to a
  temp dir, runs `claude -p --agent architect` there **with Write/Edit/Skill
  granted** (a generative agent needs to write — unlike the read-only reviewers),
  then grades the file it produced. The architect is excluded from the Phase 1
  reviewer loop (it would fail the JSON-verdict schema check).

Fixtures: `withdraw-money` (write-side command), `list-accounts` (read-side
query), `open-account` (HTTP create).

## What it revealed

- **`writesNoCode` is the key control.** It pins the architect's contract — *plan,
  don't implement*. A green here proves it produced only the `.md`, no `.kt`.
- **The plan embeds API design despite the Agent.md saying "no API design."**
  The withdraw plan's controller step spelled out `POST /accounts/{id}/withdrawals`,
  `204`, and the full validation matrix (`400/404/500`); the create plan used
  **`201` + `Location`**. So the `api-conventions` integration *at planning time*
  works — and the architect correctly distinguished a create (`201`+`Location`)
  from a state-change (`204`, no `Location`). The "no API design" line is
  interpreted as "no method signatures / assertions," not "no HTTP semantics."
- **CQRS routing is correct.** The read-side `list-accounts` scenario produced a
  `Query`-named port + a contract test for its fake — not a write-side
  `Repository` + use case. The architect applied the read-side path from the
  `clean-architecture` / `cqrs` skills.

## Why (mechanism)

Grading a generative agent reduces to the same trick as the reviewers — **assert
coarse facts, never prose** — but the facts live in a *file the agent wrote*, so
the grader's first job is "what did it create?" (set diff), and the second is
"does that artifact have the right shape?" (`mustMention` / ordering / step
count). `orderedBefore` is the one architect-specific check: inside-out ordering
(use-case test before the controller step) is a structural property of a good
plan that a substring can't capture.

## Limitations / next

- **No fingerprint cache for Phase 1b.** `check_plan.py` doesn't hash inputs, so
  every full run re-dispatches all 3 architect fixtures (~3 sonnet dispatches).
  Cheap for now; add caching if the corpus grows.
- **This is still the unit layer.** A green plan proves the architect plans *as
  specified*; it does not prove the plan *builds into working software*. That's
  the developer-integration + full-pipeline layers (need a buildable golden
  repo), still unbuilt — the toolchain here is JDK-only (no Gradle/Kotlin on
  PATH; Node present), so that's a deliberate next investment.

## Verdict

The architect is now regression-covered at the unit layer with the same
deterministic, model-free discipline as the reviewers — generalized from
"grade the JSON" to "grade the artifact."
