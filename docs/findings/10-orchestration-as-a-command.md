# Finding 10 — Orchestration belongs in a command, not a test-only Python harness

**Date:** 2026-06 · **Area:** `commands/`, `CLAUDE.md`, `evals/`
**Status:** built and green — Phase 1f, driving the **real `/run-pipeline`
command** over fake workers, produced the full dance:
`architect → developer:impl → … → test-reviewer (FAIL) → developer:fix → … →
test-reviewer (PASS) → stop` (pass@1). The forced-FAIL fix pass fires against the
real command, confirming the choreography lives in `run-pipeline.md`.

This reverses the part of [finding 09](09-agent-port-and-fakeagent.md) that built
an injectable **Python** orchestrator (`run_pipeline()`) plus an **Agent port** +
`FakeAgent` to test it. The reversal was driven by one observation:

> `run_pipeline.py` is artificial. No user ever invokes it. Passing its tests
> proves nothing about what actually runs in prod.

The choreography existed in **two** places — CLAUDE.md prose (what real sessions
follow) **and** `run_pipeline.py` (what the acceptance test drove). Two
implementations of one thing can drift: the Python copy could stay green while
CLAUDE.md said something subtly different.

## The move: extract orchestration into a real `/run-pipeline` command

The pipeline now lives where a user actually triggers it — a slash command:

- **`commands/run-pipeline.md`** — the execution orchestrator: precondition
  (an approved spec must exist, else refuse and write no code) → per-scenario
  `architect` → `developer` → `/run-reviewers` → fix-loop. The single source of
  truth for the choreography.
- **`commands/intent-and-goal.md`** — scoping (refine intent, Gherkin, write the
  SoT spec), then hands off to `/run-pipeline`. The dependency points one way:
  intent → pipeline, never back (`/run-pipeline` knows nothing of intent).
- **`CLAUDE.md`** — shrinks to a thin pointer: *Step 0 worktree → `/intent-and-goal`*.
  No choreography prose. (The agentic-dev-team plugin's CLAUDE.md uses the same
  discipline: philosophy + a command index, with the "how" deferred to the skill
  files — map and why in CLAUDE.md, how in the command.)

Each thing is described **once**, where it lives.

## What this did to the harness

| Before (finding 09) | After (this finding) |
|---|---|
| `run_pipeline.py` orchestrates (Python) | the real `/run-pipeline` command orchestrates |
| Agent port + `FakeAgent` inject real/fake workers | project-local `.claude/agents` overrides inject fake workers (unchanged mechanism) |
| Phase 1d drives `run_pipeline.py` | Phase 1d drives `claude -p "/run-pipeline …"` then **independently** builds + reviews + grades (`verify_acceptance.py`) |
| Phase 1f drives a prose prompt "leaning on CLAUDE.md" | Phase 1f drives the **real `/run-pipeline` command** over fake workers |

**Deleted:** `harness/run_pipeline.py`, `harness/pipeline.py`, `harness/agent.py`
(the port + `FakeAgent`), `tests/test_pipeline.py`, `tests/test_agent_port.py`,
and the orphaned `_review_findings.py`.
**Added:** `verify_acceptance.py` — the harness's *independent* verifier (it runs
`./gradlew test` + a fresh reviewer pass and grades; it never trusts the
command's self-report). That's verification, not orchestration, so it
legitimately stays in the harness.

## The honest trade

- **Won:** no drift (one choreography), the tests exercise the **real prod
  artifact**, a clean named seam (`claude -p "/run-pipeline …"` is one line), and
  a new cheap behavior to test (refuse-if-no-spec). Two acceptance fixtures now
  split cleanly: `withdraw-money-core` (`/run-pipeline` over a frozen spec) and
  `withdraw-money-e2e` (`/intent-and-goal` → handoff → `/run-pipeline`, the full
  CLAUDE.md chain).
- **Lost:** the `$0` deterministic fix-loop control-flow tests. That logic now
  lives in the model's reading of a prompt, not in Python — so "exactly 1 round /
  stops at 3" can no longer be asserted for free. Its replacement is the Phase 1f
  choreography test, which forces a FAIL against the **real** command: higher
  fidelity, but paid + pass@k, and it asserts the *ordered dance*, not exact
  counts.

Net, by the finding-09 two-questions rule: orchestration is "is the harness
correct?" — but the *correct harness to test* is the production command, not a
Python stand-in. Leanness of the command itself is orthogonal to testability;
the extraction into a named command is what helped.

## Unit-test count

`evals/tests/` drops from 20 to **11** ($0): `test_check_routing.py` (5,
finding-01 regression) + `test_check_choreography.py` (6). The 9 removed tests
(port contract + Python fix-loop) tested code that no longer exists.
