# Finding 09 — The Agent port + FakeAgent (testing the harness, not the model)

**Date:** 2026-06 · **Area:** `evals/harness/`, `evals/tests/`
**Status:** slice 1 built and green (the seam + first self-tests); orchestration
tests are slice 2 (pending)

Prompted by Antony Marcano's "test-driven agentic behaviours" (pluggable
agent-under-test + Auditor/Critic inspectors). The exercise mostly held a mirror
to our own harness.

## The reframe that matters: two different questions

Testing "an agent eval" conflates two things that need opposite tools:

| Question | Examples | Needs real model? | FakeAgent helps? |
|---|---|---|---|
| **Is the agent good?** (validation) | reviewer fixtures, architect plan quality, developer build-passes | **yes** | **no — tautology** |
| **Is the harness correct?** (verification of *our* glue) | routing-output parsing, the fix-loop, pipeline chaining, JUnit parsing | **no** | **yes** |

Faking a reviewer's verdict to test the reviewer proves nothing (your canned
output vs your canned expectation). So **FakeAgent is NOT for the reviewer/
architect/developer fixture evals** — those keep the real `claude -p` dispatch.
It is for the *orchestration glue*, which today has zero test coverage.

## Where it pays off — and the full-pipeline insight

The richer the orchestration, the more FakeAgent earns its keep. The reviewer
eval has ~none (one dispatch). The **full pipeline** has the most, and a subtle
point fell out:

- "Test the full pipeline" splits into **(a) does it produce good software?**
  (real workers, expensive) and **(b) does the CLAUDE.md *choreography* happen
  correctly?** — one scenario at a time, reviewers run once, **fix-pass on FAIL**,
  re-review, terminate, auto-continue.
- (b) is testable cheaply by running the **real orchestrator** (a session
  following CLAUDE.md) with **fake workers** (architect/developer/reviewers
  stubbed to return canned artifacts). You then assert the *dance*, not the
  content — and crucially you can **force** the interesting paths (make the fake
  reviewers return FAIL to verify the fix-pass triggers), which real agents won't
  do on demand.
- **Gap found:** our current acceptance test (`run_all.sh` Phase 1d) *bakes the
  orchestration into bash*. So it tests the workers + our glue — it does **not**
  test the CLAUDE.md choreography itself. That orchestration is currently
  untested.

## The enabling move: injectability

None of this works unless the orchestration **takes the agent as a parameter**.
Inline `claude -p` in bash has no seam to substitute. Extracting the **Agent
port** is what gives orchestration a knob: inject `ClaudeCliAgent` for a real,
paid eval; inject `FakeAgent` for a free, deterministic logic test.

```
Agent (port)
  ClaudeCliAgent   → `claude -p` (real model; agent-quality evals)
  FakeAgent        → scripted stdout + file-effects + call recording (harness tests)
```

## Slice 1 (this commit)

- `evals/harness/agent.py` — the `Agent` port, `RunResult`/`Call`, `ClaudeCliAgent`,
  `FakeAgent` (scripted replay + workspace file-effects + ordered call log).
- `evals/tests/` (stdlib `unittest`, no new dependency):
  - `test_check_routing.py` — pins the **finding-01** parser bug (empty `fires:`
    line must yield nobody, not the `skips:` line) + parse cases. The exact
    "looks like model flakiness but it's our parser" class, now caught for $0.
  - `test_agent_port.py` — the port **contract test** (every port with a fake
    needs one): FakeAgent honors the `RunResult` shape, applies file-effects,
    records calls, fails loudly on an exhausted script.
- `evals/run_tests.sh` — model-free runner (`python3 -m unittest discover`).
  `run_all.sh` left untouched.

10 tests, ~3ms, $0.

## Slice 2a (built) — pipeline orchestration is now injectable + tested

The Phase 1d chain (optional intent → architect → developer → build → reviewers →
**fix-loop**) was lifted out of `run_all.sh` bash into `evals/harness/pipeline.py`
(`run_pipeline(agent, workspace, cfg, build)`), driven by the Agent port and an
injected `build` callable. `evals/harness/run_pipeline.py` injects the real
`ClaudeCliAgent` + `./gradlew`; **`run_all.sh` Phase 1d now calls it** — single
source of truth, no bash/python duplicate. (This is the one place `run_all.sh`
did change from slice 1, on purpose — slice 2 *is* the orchestration work.)

`evals/tests/test_pipeline.py` drives that SAME `run_pipeline` with a `FakeAgent`
+ a fake builder and asserts the control flow, for $0:
- clean first pass → **0** fix rounds;
- FAIL→PASS → **exactly 1** round, and the fix dispatch carried the `## Review
  Findings` block;
- never-converging → **stops at `maxFixRounds`** and the grader rejects on the
  surviving VIOLATIONs (catches infinite-loop / off-by-one);
- full chain → architect dispatched **before** developer **before** reviewers.

This tests **our orchestrator's** control flow (logic that otherwise costs real
opus rounds). It is *not* the CLAUDE.md-choreography test.

## Slice 2b (built and green) — the CLAUDE.md choreography test

Closes the gap that slices 1/2a test *our* orchestrator, not the choreography
CLAUDE.md actually drives. A **real orchestrator** session runs the pipeline over
**fake worker agent definitions** — `evals/orchestration/fixtures/
withdraw-money-choreography/input/.claude/agents/` holds fake architect /
developer / test-reviewer / arch-reviewer / refactor-advisor that **self-log**
their invocation to `pipeline-calls.log` (a Bash `echo >>`) and return canned
artifacts. Project-local `.claude/agents` override the globals, so a `claude -p`
run in the scratch dir dispatches the fakes. The fake test-reviewer **forces a
FAIL on its first call** (via a `grep -c` self-count), PASS after — so the fix
pass is exercised *on demand* (real reviewers won't FAIL when you need them to).

`evals/check_choreography.py` grades the call log as a tolerant **ordered
subsequence** (extra interleaved reviewers are fine): plan → implement → review →
fix → re-review, ending after a passing review (`endsAfterReview`), one architect
(`maxArchitects`). `run_all.sh` **Phase 1f** (opt-in: `run_all.sh orchestration`)
runs it; `evals/tests/test_check_choreography.py` covers the grader for $0.

**Two layers of fake — don't conflate:** slice 1/2a's `FakeAgent` is a *python*
test double for *our* orchestrator (free, deterministic). Slice 2b's fakes are
*real agent definitions* the *real* orchestrator dispatches — this run is **paid
+ pass@k** (the orchestrator is a model), just cheap (fake haiku workers).

**Result:** with a *minimal* prompt that leans on CLAUDE.md (not spelled-out
steps), the orchestrator produced the full dance —
`architect → developer:impl → test-reviewer (FAIL) → … → developer:fix →
test-reviewer (PASS) → stop`. So CLAUDE.md's orchestration rules reliably drive
the choreography headless. (pass@1; run k times to harden.)

## Honest limits

FakeAgent tests scaffolding, never intelligence. "Is the agent good?" stays the
paid, real-CLI, `pass@k` evals. And the graders are already pure functions — the
port's unique value is testing the *seam* (dispatch → capture → parse → loop →
route), the part that currently requires a real dispatch.
