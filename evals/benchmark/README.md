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

## Arms on record

Each `scorecards/<arm>/` is committed so the numbers quoted in findings 15 and 16 can be
checked. **Only `batching-only-4` measures the configuration that shipped** — the rest are
history, and several measure configurations that were rejected. Read the *what it tested*
column before citing any row.

| arm | what it tested | span | out-tok | API calls | tool/call | cache-read | **mut-real** | red arrival |
|---|---|---|---|---|---|---|---|---|
| `baseline` | pre-programme control | 127 | 564,943 | 787 | 1.69 | 48.0M | **2** | 80.5% |
| `treatment-s1s2` | plan-file caps + reviewer gate (Stage 1+2) | 104 | 429,198 | 669 | 1.66 | 36.7M | **0** | 89.1% |
| `treatment-s3` | + planning 2 scenarios ahead — **rejected** | 75 | 390,762 | 680 | 1.66 | 40.4M | **1** | 64.0% |
| `treatment-s3-1deep` | + planning 1 ahead — **rejected** | 106 | 450,950 | 716 | 1.55 | 47.1M | **1** | 67.7% |
| `layered-seq` | layer as unit of work — **rejected** | 74 | 280,012 | 324 | 1.47 | 25.6M | **1** | 83.6% |
| `layered-2` | layered, confirmation — **rejected** | 103 | 356,013 | 493 | 1.45 | 45.5M | **4** | 81.0% |
| `layered-3` | layered, confirmation — **rejected** | 103 | 401,981 | 510 | 1.45 | 42.5M | **2** | 93.6% |
| `turn-economy` | batching **and** Bash quieting together — unattributable | 95 | 439,306 | 476 | 2.31 | 23.2M | **3** | 86.0% |
| `batching-only-4` | batching alone — shipped (finding 15) | 103 | 451,859 | 555 | 1.93 | 32.6M | **0** | 78.7% |
| **`main-control`** | **current `main` — the control for everything after** | 102 | 473,784 | 618 | 1.75 | 36.0M | **3** | 84.1% |
| `quiet-bash-2` | + quieten Bash output — **rejected** (finding 17) | 97 | 472,770 | 621 | 1.84 | 36.4M | **0** | 83.0% |

Two rows deserve a warning.

**`turn-economy` changed two things at once** — tool-call batching and quieting Bash output
— so none of its numbers belong to either. Splitting them halved the saving credited to
batching (API calls −29% → −17%, cache-read −37% → −11%) and showed its 3 mutation
survivors were not batching's doing. Quieting Bash output is still unshipped and unmeasured
for exactly this reason. It is the cautionary row: an arm that moves two levers measures
neither.

**`batching-only-4`'s red arrival of 78.7% is not comparable** to the rows above it. All 14
of its no-evidence rows were added during *fix* rounds, where batch-red is not required, and
the metric cannot currently tell those from a row that skipped verification. Its mutation
score — the gate — is 0.

**Read `main-control` and `quiet-bash-2` as a pair, and read the mutation column with
suspicion.** They differ only by the rejected Bash rule, yet score 3 and 0 candidate-real.
Across all eleven arms the figure has ranged 0–4 with no treatment explaining the spread, so
a single-arm move inside that band is noise (finding 17). The column catches gross failure —
the layered fork's 4 — not small regressions.

**Artifact convention:** an arm's directory holds everything the scoring step produces except
the `jscpd` JSON, which `dry.txt` already summarises in 15 lines instead of 800. Arms scored
before that convention settled keep only `scorecard.md`, `mutation.txt` and the mutation XML;
their CRAP and DRY figures live in findings 15 and 16 rather than in the repo.

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
