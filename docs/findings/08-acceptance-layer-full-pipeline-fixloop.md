# Finding 08 — Acceptance layer: full pipeline + self-correcting fix-loop

**Date:** 2026-06 · **Area:** `evals/pipeline/`, `evals/intent-and-goal/`,
`check_acceptance.py`, `check_spec.py`, `_review_findings.py`, `run_all.sh`
Phases 1d/1e
**Status:** built and green — the top of the confidence pyramid

## The change

The acceptance layer runs the **producer→checker chain on real artifacts** and
grades the only signals the strategy doc calls "the tool actually works": the
code builds and passes, and the reviewers (the consistency oracle) find no
must-fix defect in it. Two fixtures:

- **`withdraw-money-core`** (frozen spec): architect → developer → reviewers.
- **`withdraw-money-e2e`** (true end-to-end): `/intent-and-goal` → architect →
  developer → reviewers → **Phase 5 fix-loop**, from a one-line feature
  description, single scenario, framework-free.

Supporting pieces: `check_acceptance.py` (build-green + zero reviewer
VIOLATIONs), `check_spec.py` + the `intent-and-goal` unit fixture (grade the
`specification.md` the command writes), and `_review_findings.py` (counts
VIOLATIONs and formats the fix-mode findings block).

## What it revealed (the headline)

**The pipeline produces working code, then self-corrects its quality defects.**
On the e2e run the chain reached a green build, but `test-reviewer` flagged real
GWT/setup VIOLATIONs in the developer's *contract test* (the *When* buried inside
the assertion; SUT built in the test body, not `@BeforeTest`) — even though the
developer's *use-case* test in the same run was clean. The Phase 5 fix-loop fed
those specific findings back to the developer in fix-mode, and it drove
VIOLATIONs to **0 in one round**. The full "intent → reviewed code" promise holds
end-to-end, self-correction included.

This is the **consistency oracle working as designed**: the pipeline's own
producer (developer) emitted code its own checker (test-reviewer) rejected, the
harness caught it objectively, and the fix loop closed it.

## Why these design choices

- **Gate on VIOLATIONs, not "all clean."** `refactor-advisor` always emits a
  SUGGESTION and `test-reviewer` routinely emits WARNINGs (coverage, etc.), so a
  strict "any issue → FAIL" acceptance bar would *never* pass on sound code. The
  meaningful floor is **zero must-fix VIOLATIONs**, with WARNING/SUGGESTION
  reported but non-gating. This is concrete, measured evidence for the deferred
  strict-gate decision: a strict gate is unusable at the pipeline level.
- **Fix-loop feeds VIOLATION+WARNING, gates on VIOLATION.** Feeding SUGGESTIONs
  back would never converge (the advisory reviewer always finds one). The loop
  is bounded by `maxFixRounds`; if it can't reach 0 VIOLATIONs in K rounds, the
  final grade fails.
- **Independent verdict.** As in the integration layer, the harness runs the
  build itself and dispatches the reviewers itself — the agents never grade
  their own work.

## Non-interactive `/intent-and-goal` (and its honest limit)

`/intent-and-goal` is an interactive command (asks clarifying questions, waits
for approval). It runs headless by instructing it to **assume reasonable answers
and proceed** rather than ask/wait. The unit fixture proves this writes a valid,
well-structured, multi-scenario spec headless — which de-risks using it as step
[0] of the e2e.

**Caveat, stated plainly:** non-interactive mode *auto-assumes the human
clarification and approval gates*. So the e2e tests the **agent chain**
end-to-end, not the interactive human dialogue (which fundamentally cannot run
headless). It is "the whole pipeline minus the human decisions."

## Other fidelity caveats

- The acceptance test runs the reviewer **agents** directly, routed by a
  hardcoded glob map — not the literal `/run-reviewers` command. The command's
  routing is covered separately by the Phase 2 routing tests.
- Non-determinism: the developer's initial output quality varies run to run
  (observed 5 VIOLATIONs one run, 1 the next). The fix-loop absorbed both. If a
  run ever fails to converge, switch to `pass@k`.

## Cost / cadence

The most expensive eval by far: `/intent-and-goal` (sonnet) + architect (sonnet)
+ developer (opus, full TDD loop) + 3 reviewers (sonnet) + a real build, times
each fix round. Strictly opt-in: `./evals/run_all.sh pipeline`, with a
single-fixture filter (`run_all.sh pipeline withdraw-money-e2e`). Not cached.

## Verdict — the pyramid is complete

| Layer | Covers | Status |
|---|---|---|
| Unit | reviewers (79) · architect (3) · `/intent-and-goal` (1) | green |
| Integration | developer → `./gradlew test` | green |
| Acceptance | full pipeline + Phase 5 fix-loop | green |

Every rung of the confidence pyramid from `evals/README.md` is now built and
green, end to end, on the framework-free core. Remaining future work: the
Spring/JPA vertical slice (a heavier golden repo), and more scenarios.
