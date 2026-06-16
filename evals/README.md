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
equation, but `f` is an **agent** (non-deterministic) instead of a function. So
we can't compare outputs directly. The mechanism splits that equation into
**four files and one rule**: *don't compare the agent's wording — compare coarse
facts extracted from its machine-first JSON verdict.*

```
  input artifact ──►  [ agent f ]  ──►  JSON verdict  ──►  actuals.json  ──►  [ grader ]  ◄──  expected.json
       (1)               (3)               (3)               (4)              (5)              (2)
   frozen .kt        fresh process      { status,        assembled by     deterministic    tolerant facts:
   test file        (claude -p)          issues }        the orchestrator   model-free     status/range/mention
                                                                                │
                                                                          PASS / FAIL
```

Read the numbers `(1)…(5)` as the five moving parts below: the input (1) and the
expectation (2) are the two ends of the `assert`; the agent + its verdict
contract (3) and the orchestrator (4) produce `actuals.json`; the grader (5)
compares the two ends.

### The five moving parts

**1. The fixture input** — `evals/<agent>/fixtures/<stem>/input/*`
A frozen artifact. For `test-reviewer`, each fixture isolates one class of
finding the reviewer must flag: a `for`-loop + camelCase test (→ VIOLATION), a
happy-path-only test (→ WARNING, missing coverage), and a test with repeated
magic literals (→ SUGGESTION). This is the `input` to `f`.

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

**3. The agent's verdict contract** — `<agent>/Agent.md`
The agent is **machine-first**: its *entire* output is a single JSON object — no
prose, no markers. The human-readable report is *derived* from it by the consumer
(`/run-reviewers`); the agent produces only the data.

```
{ "status": "FAIL",
  "issues": [{ "severity": "VIOLATION", "file": "", "line": 0, "message": "" }],
  "summary": "" }
```

`severity` is `VIOLATION` / `WARNING` / `SUGGESTION` (the same words the developer
uses in fix mode — all mandatory to fix). `status` is a strict two-state gate:
`FAIL` if there are any issues, else `PASS` — the severity carries the detail.
Because the whole output is JSON,
there is no prose lane for the agent to wander into — parsing is trivial, and an
agent that *does* emit prose fails the schema check (which is exactly how a
not-yet-migrated agent is caught).

**4. The orchestrator** — `commands/run-evals.md`
Four mechanical steps: glob the fixtures; **dispatch** the agent on each `input/`
in a **fresh process** (`claude -p --agent <agent>` — *never* the in-session
`Agent` tool, which caches a stale definition); **parse** each output as JSON;
**assemble** them into one `actuals.json` keyed by fixture stem:

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

### Cost control: opt-in, diff-scoping, caching

A live run dispatches the agent once per fixture (~15k tokens each — almost all
input, dominated by the `@`-referenced skill the agent loads). Three mechanisms
keep that cheap:

- **Opt-in** — *whether* the paid gate runs. `/run-evals` is the only trigger;
  nothing wires it into a hook. The free structural gate (`--check-corpus`) and
  the free plan (`--plan`) can run as often as you like.
- **Diff-scoping** — *which* agents run. `eval_grade.py --changed-agents` reads
  the git diff and prints the agents whose `Agent.md`, referenced skill, or
  fixtures changed. Run evals only for those.
- **Caching** — *which fixtures* run. Each fixture is fingerprinted over
  `(agent Agent.md + @-referenced skills + input + expected.json)`. `--plan`
  marks a fixture `CACHED` when its fingerprint matches a prior pass, so only
  changed fixtures dispatch; `--write-cache` records fingerprints after grading.
  An untouched agent's whole suite replays at **zero tokens**. The cache lives in
  `evals/<agent>/.eval-cache.json` (git-ignored — it's regenerable, per-machine
  state). Fingerprints are content-based, so a no-op `touch` does not invalidate.

The flow a `/run-evals` performs: `--check-corpus` → `--plan` → dispatch only the
`RUN` fixtures in a **fresh process** (never the in-session `Agent` tool, which
caches a stale definition) → `--actuals … --write-cache`.

## Two kinds of test, one runner

The corpus holds two distinct kinds of test:

- **Agent fixture evals** (`evals/<agent>/fixtures/`) — does the agent's
  *judgement* match the spec? Each fixture isolates one finding the agent must
  flag. Run = `claude -p --agent`; assert = `eval_grade.py` (status + severity
  ranges + must-mention). Fingerprint-cached.
- **Command routing tests** (`evals/run-reviewers/fixtures/`) — does the
  *command* route to the right reviewers for a given changeset? Each fixture
  declares `changed_files` + `fires` / `does_not_fire`. Run = a lean scratch
  repo (`git init`, empty files at the declared paths, left untracked) +
  `claude -p "/run-reviewers --dry-run"`; assert = `check_routing.py` on the
  `fires:` line. The `--dry-run` stops after routing, so no reviewers dispatch.

Both **run the thing in a fresh `claude -p` process** (the in-session `Agent`
tool caches a stale definition) under **least-privilege, read-only** tool
allowlists; both **assert deterministically** (no model in the grader).

### Quarantine (the flaky-pair escape hatch)

For a genuinely flaky pair, a fixture can set `"quarantine": true` (+ a
`quarantineReason`): it still runs and prints its **real** result — labelled
`QUAR` instead of `PASS`/`FAIL` — but never fails the gate. Use it sparingly,
for pairs that are flaky *because the agent is*, not because the grader is.

> **War story — be sure it's the agent, not the grader.** The
> `no-match-skips-all` routing fixture (a docs-only changeset → nobody should
> fire) looked ~50% flaky and got quarantined on the theory that the model was
> "routing by topic." Wrong. The command produced an empty `fires:` line all
> along; the bug was in the grader: `check_routing.py`'s `fires:` regex used
> `\s*` after the colon, and `\s` matches `\n`, so on an **empty** `fires:` line
> it swallowed the newline and captured the next (`skips:`) line — reporting the
> *skipped* reviewers as *fired*. It only ever bit the universal-negative.
> Fixed by matching `[ \t]*`. Lesson: a deterministic grader can have
> non-obvious bugs that masquerade as agent flakiness; reproduce the raw output
> and parse it by hand before blaming the model or reaching for quarantine.

### Running the suite

```bash
./evals/run_all.sh            # everything
./evals/run_all.sh --agents   # only agent fixture evals
./evals/run_all.sh --commands # only command routing tests (cheap)
```

Phases: **0** structural (free) → **1** agent fixture evals (cached) → **2**
command routing tests. Exits non-zero on any failure.

## Findings / lab notebook

Measured discoveries from running this harness live in [`docs/`](../docs/README.md):
a grader bug that masqueraded as model flakiness, an `@`-include vs on-demand
skill-loading cost experiment (~1.8×), the eval cost model (~$0.06/dispatch), and
the conventions for writing robust agent evals.
