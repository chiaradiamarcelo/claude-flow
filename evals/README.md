# Eval corpus

Fixtures and their expected gradings for the pipeline's agents (reviewers,
architect, …). This is the **unit-test layer** of "using the tool to build the
tool": each fixture pins one agent's behavior on one frozen input, so a prompt
edit that regresses the agent is caught cheaply.

Inspired by `bdfinst/agentic-dev-team`'s eval corpus: a **deterministic,
model-free grader** (`eval_grade.py`) checks *coarse, non-determinism-tolerant*
properties of a lightly-structured agent output — not exact wording.

## Testing strategy

The pipeline is "tested" the same way it asks you to test production code — but
the unit under test is a **prompt**, not a function. The core reframe:

> An agent is a (non-deterministic) function. A fixture is its test:
> a frozen `input` → an `expected.json` describing the behavior we specified.

Because the agent is non-deterministic, we **never compare its prose**. We
extract a structured verdict from it and assert only **stable facts** —
pass/fail status, an issue-count *range*, and *must-mention* substrings. That
looseness is what keeps a grader of a non-deterministic agent deterministic and
flake-free. For a genuinely flaky pair, run it `k` times and track a pass *rate*
(`pass@k`) rather than a single boolean; quarantine pairs too flaky to gate on.

### The confidence pyramid

Fixture evals are necessary but **not sufficient**. Confidence is layered, the
same shape as a normal test pyramid, cheap → expensive:

1. **Unit — fixture evals (this corpus).** One agent, one frozen input, graded
   on coarse facts. Cheap, fast, runs on every prompt edit. Job: **regression
   safety** — catch a prompt change that silently makes an agent worse. Narrow:
   it only checks that the agent does what *its own* `expected.json` says.

2. **Integration — pipeline-composition / golden-repo runs.** Run the *chain*
   (`architect → developer → reviewers`) on a known feature spec in a reference
   repo, and assert **objective outcomes**: code compiles, generated tests pass,
   `/run-reviewers` reaches PASS. Tests the **handoffs** between agents, which no
   per-agent fixture can.

3. **Acceptance — real codebases + outcome metrics.** Run the pipeline on real
   features and *measure*: did all generated tests pass? did reviewers reach
   PASS? how many fix-mode round-trips? did a human accept the diff with no
   rework? These are the only signals that tell you the tool actually *works*.

### Two questions, two layers (verification vs. validation)

- **"Does each agent behave as I specified?"** — verification. Fixture evals
  answer this. But you wrote both the agent *and* its `expected.json`, so a green
  fixture only proves internal consistency.
- **"Is my specified behavior actually good at producing software?"** —
  validation. Only the integration + acceptance layers answer this.

### Cross-artifact drift

Per-agent fixture evals **do not** catch drift between artifacts (e.g. the
architect proposes one convention, a reviewer enforces another). Each agent's
`expected.json` is itself hand-authored and drifts in lockstep — green board,
inconsistent pipeline. Two defenses:

- **Preventive (cheap, model-free): single source of truth.** Rules live in one
  place (a skill); agents `@`-reference them rather than restating. A structural
  lint can enforce "reviewers reference their skill, don't paraphrase it." Kills
  the most common drift class (stale copies) at the root.
- **Detective (the integration layer): the reviewers are the consistency
  oracle.** Run producers (architect/developer) then checkers (reviewers) on one
  shared fixture; if the checkers reject what the producers built, that *is* the
  drift alarm. Assert on the **objective outcome**, never a hand-authored
  expected artifact — else the expected drifts too and the problem returns.

### Failure-driven fixtures

The strongest "use the tool to build the tool" loop: run the pipeline on real
work, and when it misbehaves, **capture that input as a regression fixture
before fixing the prompt** — the same "reproduce with a failing test first" rule
applied to the agents. Real codebases are the test *source*; the corpus is the
distilled set of regressions you never want to reintroduce.

## How it works — the parallel with a unit test

A normal unit test is `assert(f(input) == expected)`. Our "test" is the same
equation, but `f` is an **agent** (non-deterministic, prose output) instead of a
function. So we can't compare outputs directly. The mechanism splits that
equation into **four files and one rule**: *don't compare the prose — compare
coarse facts extracted from it.*

```
  input artifact ──►  [ agent f ]  ──► prose + verdict block ──►  actuals.json  ──►  [ grader ]  ◄──  expected.json
       (1)                (3)                  (3)                     (4)              (5)               (2)
   frozen .kt        dispatched by      <!-- EVAL-VERDICT -->     assembled by      deterministic    tolerant facts:
   test file        the orchestrator     { status, issues }      the orchestrator    model-free      status/range/mention
                                                                                          │
                                                                                    PASS / FAIL
```

Read the numbers `(1)…(5)` as the five moving parts below: the input (1) and the
expectation (2) are the two ends of the `assert`; the agent + its verdict
contract (3) and the orchestrator (4) produce `actuals.json`; the grader (5)
compares the two ends.

### The five moving parts

**1. The fixture input** — `evals/<agent>/fixtures/<stem>/input/*`
A frozen artifact. For `test-reviewer`, two Kotlin test files: one deliberately
dirty (`for` loop, camelCase), one meant to be clean. This is the `input` to `f`.

**2. The expected spec** — `evals/<agent>/fixtures/<stem>/expected.json`
The *assertion*, written as **tolerant facts**, not exact text:

```json
{
  "fixture": "dirty-loop-and-camelcase",
  "applicableAgents": ["test-reviewer"],
  "agents": {
    "test-reviewer": { "expectedStatus": "fail", "issueCount": { "min": 1 }, "mustMention": ["loop"] }
  }
}
```

It never says "the output must equal this string." It says: the verdict must be
`fail`, must carry ≥1 issue, and *somewhere* in the issues the substring `"loop"`
must appear. That looseness is the whole trick for grading a non-deterministic
agent deterministically.

**3. The agent's verdict contract** — a block in `<agent>/Agent.md`
The agent writes its usual human prose, then appends one machine-readable verdict:

```
<!-- EVAL-VERDICT -->
{ "status": "fail", "issues": [{ "severity": "error", "message": "..." }] }
```

This is the **adapter** that turns free prose into something parseable.
`status = fail` iff there's ≥1 VIOLATION; `issues` = the violations only.

**4. The orchestrator** — `commands/run-evals.md`
Four mechanical steps: glob the fixtures; **dispatch** the agent on each `input/`
(`Agent(subagent_type="<agent>", …)`); **extract** the verdict block from each
returned text; **assemble** them into one `actuals.json` keyed by fixture stem:

```json
{ "dirty-loop-and-camelcase": { "agents": { "test-reviewer": { "status": "fail", "issues": ["…6…"] } } } }
```

This is the **only** step that touches the model and costs tokens.

**5. The grader** — `evals/eval_grade.py` (deterministic, model-free)
For each fixture it loads `expected.json` + the matching slice of `actuals.json`
and runs three checks in `grade_agent()`:

- `status` equals `expectedStatus`?
- `len(issues)` inside the `issueCount` range (`_in_range`)?
- each `mustMention` substring present in the concatenated issue text (`_mentions`)?

Any failing check → that `fixture::agent` pair fails → exit 1. **No model is
involved here** — pure Python string/number comparison, so it's flake-free and
free to run in CI.

### The two-tier gate (why there are two entry points)

- **Structural gate** — `eval_grade.py --evals-dir evals/<agent> --check-corpus`.
  No agent, no actuals. Asserts every `expected.json` is well-formed and pairs
  with a non-empty `input/`. Free, always-on.
- **Live gate** — `/run-evals <agent>`. The full dispatch → extract → grade path
  (`eval_grade.py --actuals actuals.json`). Costs tokens, so it's on-demand.
