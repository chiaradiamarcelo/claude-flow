# Experiment: subagent pipeline vs inline pipeline

**Question.** The pipeline delegates authoring to `architect` → `test-designer` →
`developer` subagents. Does that topology pay for itself, against running the same
procedure inline in one session?

Prompted by a co-worker's `rafa-*` variant, whose stated intent was *"copy the workflow
and make the flow inline except for adversarials (reviews, etc)"*.

## The variant was not one change — it was four

Diffing `rafa-*` against the live pipeline:

| | live pipeline | `rafa-*` variant | in this experiment |
|---|---|---|---|
| **Topology** | architect / test-designer / developer subagents | inline | **the treatment** |
| Convention skills | `clean-architecture`, `testing`, `comments`, `cqrs`, `api-conventions` | **byte-identical** copies | shared, not a confound |
| Planning scope | per scenario | all scenarios in one pass | **neutral by construction** — every round's spec has exactly 1 scenario |
| Inner-loop granularity | always batch-per-class | plan declares `one-shot` \| `per-batch` | **pinned** to batch-per-class in both arms |
| Plan↔code fidelity | developer self-reports | deterministic `rafa-plan-inventory.sh` | **pinned out** — self-report in both arms |

Only the topology row was intended by the author; the other three arrived as drift when
Claude did the copy. Leaving them in would have been actively misleading: the prior
experiment (`docs/findings/13-batch-vs-strict-tdd.md`) already established that loosening
inner-loop granularity alone buys **−46% cost** and **−61% suite runs**, and `one-shot`
loosens that same lever further. A bundled run would have shown a large cost win that
looked like evidence for "inline" while mostly measuring granularity.

The other three differences are worth testing — **separately, one experiment each**.

## Arms

Both arms are frozen in one plugin (`plugin/`), loaded with `--plugin-dir`, so neither
depends on nor pollutes the live `~/.claude` config:

- **arm-agents** — `/exptopology:arm-agents <slug>`. The orchestrator dispatches and never
  authors.
- **arm-inline** — `/exptopology:arm-inline <slug>`. The session plans and implements, and
  spawns nothing.

The convention skills are shared byte-identical copies. `inline-plan` is a faithful merge
of the `architect` + `test-designer` agent bodies; `inline-implement` is the `developer`
agent body. Same rules, same budgets, same output format — **only the delivery differs.**

**Review is excluded from the measured run.** Both arms spawn the same reviewers by
construction, so including them adds the noisiest, most expensive component to both sides
without discriminating between them. Reviewer findings are instead collected once per arm
*after* the run, as a quality oracle rather than part of the treatment.

## Rounds

Three structurally different scenarios, one run per arm, mirroring the prior experiment's
R1–R3 so the numbers stay comparable:

1. `withdraw-money` — write side
2. `deposit-money` — write side, second shape
3. `account-overview` — read side (CQRS query)

Each arm starts from a byte-identical copy of `evals/golden-repo-spring` plus that round's
`specification.md`, in a neutral scratch dir (**not** under `~/.claude`, which the harness
protects — that asymmetry confounded the first run of the prior experiment).

## Instrument

### The rig that was nearly rigged

A $0.21 spike dispatching three `echo`s through a subagent established:

- `result.usage` counts the **main loop only**. Main-loop-only cost was **$0.11** against a
  reported total of **$0.21** — scoring the subagent arm with the prior experiment's
  `metrics.py` would have hidden roughly half its spend and made the topology under test
  look free.
- `result.total_cost_usd` **does** roll subagents up. Valid as-is.
- Every subagent assistant event carries `parent_tool_use_id`, so tool calls can be counted
  *and attributed*. All 3 dispatched echoes were present and correctly attributed.
- Per-event `output_tokens` is **under-reported** (main loop summed to 18 against the result
  event's 204 — streaming events carry partial usage).

`oracle/metrics2.py` encodes this:

| axis | source | status |
|---|---|---|
| **cost** | `result.total_cost_usd` | complete, rolls up |
| **suite runs** | `gradlew` Bash blocks, split by origin | complete |
| **tool calls** | `tool_use` blocks, split by origin | complete |
| **wall clock** | wrapper timing | complete |
| token counts | summed per-event usage | **attribution only** — never read as spend |

### Quality oracle (all $0, reused from `experiment/batch-vs-strict-tdd`)

- **Mutation** — PIT in a pure-Kotlin sidecar (Spring Boot 4 forces JUnit 6, which
  `pitest-junit5` cannot drive), over domain + application.
- **CRAP** — JaCoCo XML → `comp²·(1−cov)³+comp` per method (`oracle/crap.py`).
- **DRY** — PMD CPD.
- **Coverage** — JaCoCo.
- **Reviewer findings** — one post-hoc `/run-reviewers` pass per arm.

Kotlin's synthetic bytecode makes *absolute* mutation scores noisy, but for an A/B on the
same production shape the noise is systematic and cancels in the delta.

## Reproducing

```bash
./setup-arm.sh <round-slug> <agents|inline>   # pristine repo + spec
./run-arm.sh   <round-slug> <agents|inline>   # dispatch + metrics.json
```

## Status

See `RESULTS.md`.
