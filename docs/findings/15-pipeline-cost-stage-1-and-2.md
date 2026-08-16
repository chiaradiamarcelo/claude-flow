# Finding 15 — Pipeline cost: where 5 hours went, and the first 18% back

**Date:** 2026-08 · **Area:** `evals/scorecard/`, `evals/benchmark/`, `agents/{architect,test-designer,developer}`, `commands/{run-pipeline,run-reviewers}`
**Status:** adopted on two A/B arms. Stage 3 (planning lookahead) is next and untested.
Supersedes nothing; builds on [finding 13](13-batch-vs-strict-tdd.md) (experimental
method) and [finding 14](14-mutation-gate-spike.md) (the survivor filter).

---

## What this is

Measurement infrastructure for the pipeline, plus the first two optimisation stages —
adopted on the strength of two full A/B arms rather than argument.

**Headline: 18% faster, 24% fewer output tokens, quality equal or better on every oracle.**

The trigger was a real run: `gym-walls` on the Android project took **5h09** for 13
scenarios. The code was good. Nobody could say where the time went.

## Where the time actually went

Mined from that run's transcripts, not recalled:

| | |
|---|---|
| Gradle, all 151 invocations | **18 min — 5.8%** |
| `architect` + `test-designer`, which run **zero** builds | **115 min — 41%** |
| Output tokens | 1,014,690, at ~60 tok/s sustained |

It was never the build. Time is output tokens, and the pipeline was spending them
writing prose *about* the code: **6,461 lines of plan markdown against 4,547 lines of
Kotlin.** `SCENARIO-07.md` alone was 844 lines — a 275-line "declarative skeleton"
against a prompt whose own example is ten bullets, and 149 lines of essay before the
first test table.

## The measurement rig

Runs are compared **across features**, never by repeating one, so every metric is a
rate rather than a total.

- **`evals/scorecard/extract_run.py`** — per-role cost, row-level quality, and Stage 1
  metrics from session transcripts.
- **`evals/scorecard/baseline-gym-walls.md`** — the Android datapoint of record
  (23.7 min/scenario · 3.25 min/row · 10,681 tok/row). Extracted while the transcripts
  still existed; it is not recoverable later.
- **`evals/benchmark/`** — a frozen 9-scenario bank spec, a Boot 3.5 fixture, and
  `run-arm.sh` to materialise and score an arm.
- **Oracle** — PIT + JaCoCo + jscpd via an **init script**, never the fixture's build
  file, so the agents cannot see that the run is being scored.
- **`tools/mutation/dry.py`** — new. **`classify-survivors.py`** — precision fix for
  Kotlin synthetic accessors.

Validated against a probe with a deliberately-uncovered branch: the filter surfaced
exactly that mutant and binned all the `equals`/`hashCode`/`toString` noise, as
[finding 14](docs/findings/14-mutation-gate-spike.md) predicts.

## Stage 1 — the fix budget

`/run-reviewers` failed on **any** severity. In the baseline arm that spent all three
fix rounds on warnings and suggestions, then **ran out before reaching a defect that
silently destroyed stored data** (`POST /accounts` on an existing number wiped the
account's history). Not a slow gate — a misallocating one.

- FAIL on **VIOLATION only**; warnings and suggestions reported, not gating
- `/run-pipeline` triages by severity, caps at 2 rounds, records every deferral, and
  **headlines any unfixed violation**
- commit after each green scenario *(since removed — see the note below)*

## Stage 2 — cap what gets written, not how hard agents think

- **architect**: `Structure & Contracts` ≤ 40 lines
- **test-designer**: the tables *are* the deliverable — no prose before the first
  table, `Contradiction` ≤ 120 chars, deleted candidates one line each
- **developer**: the narrative record moves to `<scenario>.record.md`, which no agent
  reads; status cells use a mandated vocabulary so the run is machine-scorable

## Results — baseline vs treatment, same frozen spec

| | baseline | treatment | Δ |
|---|---|---|---|
| Span | 127 min | **104 min** | **−18%** |
| Output tokens | 564,943 | **429,198** | **−24.0%** |
| Plan-file bytes | 217,274 | **75,437** | **−65%** |
| architect tokens | 77,607 | 43,739 | −44% |
| test-designer tokens | 121,620 | 72,781 | −40% |
| Fix rounds | 3 (the cap) | 2 | −29% time |

> **Per-scenario commits removed 2026-08-16.** They were part of this measured bundle, so
> the −18%/−24% headline was produced by a configuration that included them. Removing one
> element of a bundle that was never measured element-by-element leaves the remaining
> figures unverified for the current configuration; nothing here was re-run. The rule also
> had a side effect worth recording: because an arm is its own git repo, those commits took
> whatever identity the machine's global git config held.

> **Token figures corrected 2026-08-12.** They were first reported as −30.5%
> (633,728 → 440,250) by an extractor that summed `usage` per assistant *log event*
> rather than per API *request*; Claude Code emits several events per response, each
> repeating the same usage block. The inflation was not uniform — 10.9% on the
> baseline against 2.5% on the treatment — so the *ratio* moved too. Direction and
> significance are unchanged. Every other number in this finding was independent of
> the bug.

| quality | baseline | treatment |
|---|---|---|
| **Mutation, candidate-real survivors** | 2 | **0** |
| CRAP over threshold | 0 (mean 1.23) | 0 (mean 1.23) |
| DRY | 4.95% | 6.46% |
| red→green | 78.8% | **86.1%** |
| **catches (`> Note to architect:`)** | 9 | **18** |

The last row is the one that decided it. The risk of capping output was cutting the
*deliberation* that catches architect errors — five of them in the Android run. Instead
the structural-gap notes **doubled**. The caps removed narration, not thinking.

DRY's rise is a denominator effect: 139 vs 141 duplicated lines over 22% less code.

## What I got wrong along the way, on the record

- Claimed the reviewers were dispatched serially in the baseline and that
  `/run-reviewers` was at fault. **Wrong** — an artifact of my own round-grouping
  heuristic collapsing four rounds into one. Rounds are now delimited by developer
  dispatches. The headless orchestrator batched correctly; that also means **batching
  cannot be measured in headless arms** and Stage 1's saving is the fix rounds alone.
- Claimed `mutation-audit.md`'s "gradle-pitest-plugin ≥ 1.19" was stale. **Wrong** — it
  publishes to the Gradle Plugin Portal, not Maven Central. Cost four failed builds.
- Predicted ~60–65 test rows. Actual **113**. Low by 74%.
- The `commits` metric reads 0 for both arms: it counts subagent Bash calls, but the
  orchestrator does the committing. Real counts are 2 and 15. **Still broken.**

## Known limitations

- **n=1 per arm.** Directional, not settled — [finding 13](docs/findings/13-batch-vs-strict-tdd.md)
  needed four runs per arm for its call.
- **Plain-Kotlin surrogate.** It ranks levers; it does not size them for Android.
  Per-unit cost there is 2–3× higher.
- **Headless arms have no human corrections.** The Android baseline had two, both
  catching rule violations.
- **The frozen spec states Rule 1 (unique account numbers) and gives it no scenario.**
  My error. Left as-is because it is identical across arms — and it is now a standing
  test of whether the pipeline catches an undriven invariant. Neither arm did.
- The last commit (fix-mode inventory + triage deference) is **unmeasured**. It restores
  invariants the pipeline already claimed, so shipping it is lower risk than shipping
  the config exactly as measured.

## Next

**Stage 3 — plan one scenario ahead of implementation.** `architect` + `test-designer`
write no code, so their 41% of agent time can overlap the developer's. It is now the
largest remaining lever, and its load-bearing assumption — that plan-breaking
dependencies are long-distance rather than adjacent — is still untested.

Stage 4 (a scenario DAG) was **cut**: its measured value would mostly reflect a
benchmark property we chose, and real dependency graphs look near-linear.
