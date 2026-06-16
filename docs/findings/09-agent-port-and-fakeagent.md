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

## Slice 2 (next, not yet built)

Lift one orchestration path out of bash into an injectable function and drive it
with `FakeAgent`:
- **fix-loop control flow** — script "2 violations then 0" → assert it loops once
  and accepts; "always 2" → assert it stops at `maxFixRounds` and fails. (Today
  this costs real opus rounds to exercise.)
- eventually the **CLAUDE.md choreography** test (real orchestrator + fake
  workers) — the untested gap above.

## Honest limits

FakeAgent tests scaffolding, never intelligence. "Is the agent good?" stays the
paid, real-CLI, `pass@k` evals. And the graders are already pure functions — the
port's unique value is testing the *seam* (dispatch → capture → parse → loop →
route), the part that currently requires a real dispatch.
