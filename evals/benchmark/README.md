# Cost/quality benchmark — measuring a pipeline change end to end

The `evals/` corpus answers *"did this prompt edit break an agent?"* on frozen inputs.
This rig answers a different question: **"what did this change cost, and did quality
hold?"** — by running the *whole* `/run-pipeline` on one frozen specification and scoring
the run against oracles the agents cannot see.

One run of the pipeline is an **arm**. An arm is a measurement: it runs unattended, in its
own workspace, in its own session, and is never re-run in place.

## Why the whole pipeline, and not a fixture

Cost lives in the interaction, not in any single agent. The plan file an architect writes
is re-read by two later agents on every dispatch; a developer's turn count multiplies its
context by every turn after it. No per-agent fixture can see that. Findings 15 and 16 both
turn on cross-agent effects that only appear at full-run scale.

## The pieces

| Path | Purpose |
|---|---|
| `bank-accounts/specification.md` | **The frozen spec.** 9 scenarios. Every arm runs it verbatim — an arm that regenerates it is incomparable to every other. Two deliberate **red-arrival chains** (02→03, 04→05): the later scenario is red *only* because the earlier one shipped without a guard. That is what makes planning ahead unsafe, and it is the property Stage 3 was rejected for breaking. |
| `fixture/` | Buildable Spring Boot 3.5 / JUnit 5 skeleton, Java-21 bytecode from a JDK 25 toolchain. Copied fresh per arm. |
| `fixture/.claude/CLAUDE.md` | Arm hygiene: work in place, no worktree, do not run `/intent-and-goal`. |
| `oracle/oracle.init.gradle.kts` | PIT + JaCoCo applied **out of band** via a Gradle init script, so the agents never see a coverage or mutation plugin in the build they read. Blind scoring. |
| `run-arm.sh <arm>` | Materialise an arm; `--score` runs the oracles and the scorecard. **Refuses to overwrite an existing workspace** — re-running an arm in place destroys its record. |
| `run-confirmation-arms.sh a b` | Runs arms **sequentially**. Never run two concurrently: they contend for CPU and corrupt span, the metric a confirmation exists to pin down. |
| `rescore-cost.sh` | Re-derives every arm's cost side from stored transcripts, without re-running the oracles. Use after any change to `extract_run.py`. |
| `scorecards/<arm>/` | Committed results: `scorecard.md` (the normalised report) and `mutation.txt` (filtered survivors). |
| `../scorecard/extract_run.py` | Transcript → normalised scorecard. |
| `../scorecard/baseline-gym-walls.md` | The Android datapoint of record — a real 13-scenario feature, 5h09. Never re-run. |
| `../../tools/mutation/` | `classify-survivors.py` (junk-vs-real filter), `crap.py`, `dry.py`. |

## Running an arm

```bash
cd ~/.claude/evals/benchmark
./run-arm.sh my-change                       # materialise runs/my-change/

cd runs/my-change && nohup caffeinate -i -s -m \
  claude -p "/run-pipeline bank-accounts" --dangerously-skip-permissions \
  > ../../my-change-run.log 2>&1 < /dev/null &

pmset -g assertions | grep PreventUserIdleSystemSleep   # must be 1

cd ~/.claude/evals/benchmark && ./run-arm.sh my-change --score
```

**`caffeinate` is not optional.** A ~100-minute unattended run outlasts the idle timer,
and a machine sleep kills the agent mid-dispatch. One arm died 11 minutes in this way.

**An arm that a human helped is not an arm.** If the orchestrator repairs a killed agent's
work or you answer a question it asked, discard it however complete it looks — the
measurement is of an unattended pipeline.

An arm must run in a **fresh session** from its own workspace. It cannot run from the
session designing the experiment: the scorecard reads
`~/.claude/projects/<workspace-slug>/<session>/subagents/`, and an orchestrator carrying
the experiment's own conversation is not the orchestrator whose cost is being measured.

## What gets scored

**Cost — deterministic counts, trustworthy at n=1.** API calls (keyed on `requestId`, not
log events — one API response is logged as several), tool calls per API call, output
tokens, cache-read, context per call, and generated characters bucketed by destination
(plan vs spec vs production vs test).

**Quality — the oracles.**

- **Filtered mutation** is the gate. Raw PIT survivors on clean Kotlin output are ~100%
  junk (finding 14), so `classify-survivors.py` splits junk from candidate-real, and only
  candidate-real counts.
- **CRAP** from JaCoCo XML; **DRY** via jscpd.
- **Red arrival** — the share of green rows whose Status cell evidences a real failure.
  This is the test-strength metric. Note it cannot currently distinguish a row added in
  *fix mode* (where batch-red is not required) from one that skipped batch-red, so read it
  with that caveat.
- **Plan↔code fidelity** — every planned row maps to a test method and every test method
  to a row. Verify it against the source, not against the developer's own `✅` marks.

Metrics are **per unit** (per scenario, per row) because arms are compared across
features, where totals are meaningless and rates are not.

## Rules earned the hard way

1. **No wall-clock claim from fewer than three arms.** Span has ranged 74–127 minutes.
   It misled twice: once confounded by row count, once when a 74-minute arm looked like
   −42% until two confirmations landed at 103 both.
2. **No claim from an interim reading.** Developer tool-calls-per-call measured 1.86–1.90
   at 4–7 dispatches and settled at 1.57 over the full arm. Three separate interim
   readings have now been wrong.
3. **Quality metrics behave better than cost metrics.** Mutation and red arrival have
   moved in the predicted direction every time; two arms of quality signal beat two arms
   of speed signal.
4. **Verify a metric's *definition*, not just its value.** Every serious error here was a
   definition bug producing a confident, internally consistent, wrong story.
5. **Metrics must be orthogonal.** An elif-chain once made `red_then_green` exclusive with
   `unplanned`, penalising an arm for adding tests that had genuinely gone red.
6. **Read the produced source, not only the oracles.** The most decision-relevant defect
   found in this programme — a use case that destroyed an account's history on re-open —
   is invisible to mutation, CRAP, DRY and every row metric, because nothing covers
   behaviour nobody wrote. Three greps found what eight scored arms could not.
7. **Never switch branches in `~/.claude` while an arm runs.** The checkout *is* the live
   config the arm reads on every dispatch. Use `git worktree` to edit another branch.

## Toolchain traps (all encoded in the init script)

- `gradle-pitest-plugin` 1.19.0 is on the **Gradle Plugin Portal**, not Maven Central
  (whose latest, 1.15.0, dies on Gradle 9's removed `ReportingExtension.baseDir`).
- Init-script plugins apply by **class** (`apply<T>()`), not by id.
- `JavaToolchainService` must be resolved at **project** scope, not inside `configureEach`.
- `addJUnitPlatformLauncher.set(false)`, or the injected launcher misaligns with Boot's
  engine.
- **pitest ≥ 1.20.4** — 1.19.1's bundled ASM dies on Java 25 with
  `Unsupported class file major version 69`.
