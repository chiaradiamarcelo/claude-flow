# Eval corpus

Fixtures and their expected gradings for the pipeline's agents and commands
(reviewers, architect, developer, `/intent-and-goal`, `/run-pipeline`,
`/run-reviewers`). This is the **test layer** of "using the tool to build the
tool": each fixture pins one behavior on one frozen input, so a prompt edit that
regresses an agent — or a choreography change that breaks a command — is caught.

Inspired by `bdfinst/agentic-dev-team`'s eval corpus: a **deterministic,
model-free grader** checks *coarse, non-determinism-tolerant* properties of a
lightly-structured agent output — not exact wording.

## Two layers, two questions

This corpus answers **"did this prompt edit break an agent?"** — one behaviour, one frozen
input, a model-free grader. It is fast, cheap and per-agent.

It cannot answer **"what did this change cost, and did quality hold?"** Cost lives in the
interaction between agents: a plan file is re-read by every later agent on every dispatch,
and a developer's turn count multiplies its context by every turn after it. For that there
is a second layer — [`benchmark/`](benchmark/README.md) — which runs the *whole*
`/run-pipeline` on a frozen 9-scenario spec and scores the finished run against mutation,
CRAP and DRY oracles applied out of band. One such run is an **arm**; arms are unattended,
never re-run in place, and cost ~100 minutes each.

Use this corpus while editing a prompt. Use the benchmark before claiming a change made
the pipeline cheaper or better.

## Every fixture is a test.json (given / when / then)

A fixture is **data**. One manifest, `test.json`, expresses the whole test:

```json
{
  "given": { "files": "input/" },
  "when":  { "do": "agent", "agent": "api-reviewer" },
  "then":  { "grader": "verdict", "expectedStatus": "FAIL",
             "severities": { "VIOLATION": { "min": 1 } }, "mustMention": ["logic"] }
}
```

- **given** — the inputs (`input/`) and the workspace to set up (`golden-repo`,
  `git-scratch`, or none).
- **when** — the action. `do` is a **closed enum**: `agent` (dispatch a reviewer
  or an artifact-writing agent), `command` (run a slash command), `build` (run an
  agent then `./gradlew test`). Closed, not free-text steps — so there is **no
  glue layer to rot** (the Cucumber failure mode). A new kind is one handler.
- **then** — `grader` names the grader; the rest is its tolerant spec.

One engine runs them: **`./evals/evals`** (`run_fixture.py`). `when.do` → a
handler; `then.grader` → one of the pure `grade_*` functions
(verdict / plan / build / spec / acceptance / choreography / refusal / routing).

```bash
./evals/evals --test <fixture>      # run ONE fixture, always; red/green + diff  (the TDD loop)
./evals/evals --test <f> --agent X  # disambiguate a name across corpora
./evals/evals --list                # every fixture with its when/then
```

## Testing strategy

The pipeline is "tested" the same way it asks you to test production code — but
the unit under test is a **prompt / choreography**, not a function.

> An agent is a (non-deterministic) function. A fixture is its test:
> a frozen `given` → a `then` describing the behavior we specified.

Because the agent is non-deterministic, we **never compare its prose**. We
extract a structured result and assert only **stable facts** — pass/fail status,
an issue-count *range*, *must-mention* substrings, an ordered call-log
subsequence. That looseness is what keeps a grader of a non-deterministic agent
deterministic and flake-free. For a genuinely flaky pair, run it `k` times and
track a pass *rate* (`pass@k`); quarantine pairs too flaky to gate on.

### The confidence pyramid

Fixture evals are necessary but **not sufficient**. Confidence is layered,
cheap → expensive:

1. **Unit — fixture evals.** One agent, one frozen input, graded on coarse facts.
   Cheap, cached, runs on every prompt edit. Job: **regression safety**. Narrow:
   it only checks the agent does what *its own* `then` says.
2. **Integration — golden-repo runs.** Run an agent (developer) on a known spec
   in a buildable repo and assert **objective outcomes**: code compiles, tests
   pass. Tests the agent against a real toolchain.
3. **Acceptance + choreography — the whole pipeline.** Run the real
   `/run-pipeline` (and `/intent-and-goal` → handoff): with real workers
   (does it produce building, clean software?) and with fake workers (does the
   CLAUDE.md choreography happen — plan→implement→review→fix→stop?).

### Two questions, two layers (verification vs. validation)

- **"Does each agent behave as I specified?"** — verification. Fixture evals
  answer this. But you wrote both the agent *and* its `then`, so a green fixture
  only proves internal consistency.
- **"Is my specified behavior actually good at producing software?"** —
  validation. Only the integration + acceptance layers answer this.

### Cross-artifact drift

Per-agent fixture evals **do not** catch drift between artifacts (the architect
proposes one convention, a reviewer enforces another); each `then` is itself
hand-authored and drifts in lockstep. Two defenses:

- **Preventive (cheap): single source of truth.** Rules live in one place (a
  skill); agents `@`-reference them. A structural lint enforces "reviewers
  reference their skill, don't paraphrase it."
- **Detective (the acceptance layer): the reviewers are the consistency oracle.**
  Run producers then checkers on one shared fixture; if the checkers reject what
  the producers built, that *is* the drift alarm. Assert the **objective
  outcome**, never a hand-authored expected artifact.

### Failure-driven fixtures

The strongest loop: run the pipeline on real work, and when it misbehaves,
**capture that input as a regression fixture before fixing the prompt** — the
"reproduce with a failing test first" rule applied to the agents.

## The mechanism — a unit test where `f` is an agent

A normal unit test is `assert(f(input) == expected)`. Here `f` is an **agent**
(non-deterministic), so we don't compare outputs — we compare coarse facts
extracted from a structured result. The engine runs each fixture as
given → when → then:

```
 given (input/, workspace)  ──►  when (claude -p, FRESH process)  ──►  result  ──►  then (grader)
   frozen .kt / spec /            agent | command | build            JSON verdict,    deterministic,
   golden-repo / git-scratch                                          scratch, log    model-free → PASS/FAIL
```

- **GIVEN** — `evals/<corpus>/fixtures/<stem>/input/*` plus `given.workspace`. A
  frozen artifact (a reviewer's `.kt`, an architect's `specification.md`) and, for
  the heavy kinds, a scratch (`golden-repo` copy, or a `git-scratch` with the
  declared `changedFiles`).
- **WHEN** — dispatched in a **fresh `claude -p` process**, *never* the in-session
  `Agent` tool (it caches a stale definition — see the war story). The handler is
  chosen by `when.do`; least-privilege tools per kind.
- **THEN** — `then.grader` selects a pure grader. For reviewers that's
  `grade_agent`: machine-first verdict `{status, issues:[{severity,…}], summary}`,
  `status` a strict FAIL-if-any-issue gate; checks are `status` ==, `len(issues)`
  in range, each `mustMention` substring present, each `mustFlagFiles` path
  reported in some issue's `file`, each `mustInvokeSkills` skill actually invoked.
  **No model in the grader** — pure Python, flake-free.

  The last two exist because the first two read the reviewer's *prose*, and prose
  is the easiest thing for a reviewer to get right while covering the wrong ground.
  `mustInvokeSkills` grades tool calls, so a reviewer cannot pass with its rules
  unloaded; `mustFlagFiles` grades the `file` field, so it cannot pass by reviewing
  a familiar layer and generalising about the rest. Both were added after a green
  suite turned out to be compatible with exactly that. `/run-reviewers` fixtures
  have the sibling assertion, `mustScope`: the file list each reviewer is
  dispatched with must contain the files that matched its triggers.

### The two-tier gate

- **Structural (free)** — `eval_grade.py --evals-dir evals/<agent> --check-corpus`
  (or it runs in `run_all.sh` Phase 0). Asserts every `test.json` is well-formed.
  A `$0` unit test (`evals/tests/`) additionally asserts every `when.do` /
  `then.grader` in the corpus maps to a registered handler/grader.
- **Live** — `./evals/evals --test <fixture>` (one) or `run_all.sh` (the suite).
  Costs tokens, so it's on demand.

### Cost control: cached reviewers, opt-in heavy kinds

- **Caching (reviewers).** Each reviewer fixture is fingerprinted over
  `(agent Agent.md + @-referenced skills + input + test.json)`. `run_all.sh`'s
  Phase 1 replays a fixture at **zero tokens** when its fingerprint matches a
  prior pass (`evals/<agent>/.eval-cache.json`, git-ignored). Content-based, so a
  no-op `touch` does not invalidate. (Decision in `docs/findings/11`: the cache
  is preserved on the reviewer path; the engine handles the rest.)
- **Opt-in heavy kinds.** `developer`, `pipeline`, `orchestration` are paid +
  slow; they run **only when named** (`run_all.sh developer`), never in the
  default suite.
- **The TDD loop is cheap by construction** — `evals --test <one fixture>`.

### Running the suite

```bash
./evals/evals --test <fixture>   # one fixture (red/green) — the dev loop
./evals/evals --list             # list every fixture + its when/then
./evals/run_tests.sh             # $0 model-free harness self-tests
./evals/run_all.sh               # default: structural + reviewers (cached) + architect + intent + routing
./evals/run_all.sh <corpus>      # one corpus (incl. opt-in: developer | pipeline | orchestration)
```

`run_all.sh` exits non-zero on any failure.

### Quarantine (the flaky-pair escape hatch)

A routing fixture can set `"quarantine": true`: it still runs and prints its
**real** result (labelled `QUAR`) but never fails the gate. Use sparingly, for
pairs flaky *because the agent is*, not because the grader is.

> **War story — be sure it's the agent, not the grader.** The `no-match-skips-all`
> routing fixture (docs-only changeset → nobody fires) looked ~50% flaky and got
> quarantined on the theory the model "routed by topic." Wrong: the command
> produced an empty `fires:` line all along; the bug was in the grader —
> `check_routing.py`'s regex used `\s*` after the colon, and `\s` matches `\n`, so
> on an empty `fires:` line it swallowed the newline and captured the next
> (`skips:`) line. Fixed by matching `[ \t]*`. Lesson: a deterministic grader can
> have bugs that masquerade as agent flakiness — reproduce the raw output before
> blaming the model.

## Findings / lab notebook

Measured discoveries from running this harness live in [`docs/`](../docs/README.md):
a grader bug that masqueraded as model flakiness, an `@`-include vs on-demand
skill-loading cost experiment (~1.8×), the eval cost model (~$0.06/dispatch),
orchestration as a real command (finding 10), and the test.json migration +
cache decision (finding 11).
