# Pipeline cost programme — working state

**Read this first after a compaction.** Written 2026-08-12, revised same day after the
re-derivation. Live working notes, not a finding. Findings 15 and 16 are the durable
record; this file is what is *in flight*.

Immediate next action: **decide PR #17.** The extractor is fixed, all eight arms are
re-derived, and findings 15 and 16 carry dated corrections.

---

## 1. Two measurement bugs, both now fixed

**Bug A — usage summed per log event, not per API request.** Claude Code logs one API
response as several assistant events (a thinking block, then one per `tool_use`), each
repeating the same `usage` block. Verified on s1s2: 1,590 events vs 669 `requestId`s.
Fixed by keying usage on `ev["requestId"]`; API calls are `len(set(requestId))`.

| quantity | per-event | per-request (truth) | inflation |
|---|---|---|---|
| `output_tokens`, s1s2 | 440,250 | 429,198 | 1.03× |
| `output_tokens`, baseline | 633,728 | **564,943** | **1.12× — NOT uniform** |
| `cache_read_input_tokens`, s1s2 | 73,849,792 | **36,651,982** | 1.76× |
| "turns" | 1,590 | **669 API calls** | 2.38× — wrong concept |

The inflation was **not** uniform across arms (1.03× to 1.12×), so ratios moved too. This
is why finding 15's headline is now **−24%** output tokens, not −30.5%. The earlier note
in this file saying output tokens were "valid within 3%" was itself wrong — it
generalised from the one arm I happened to check.

**Bug B — `red_then_green` was exclusive with `unplanned`.** The classifier's elif-chain
tested `unplanned` first, so an unplanned row that *had* gone red→green was counted only
as unplanned and silently subtracted from test strength. Provenance and red-arrival are
orthogonal and are now scored on separate axes; **`red_arrival`** (evidence of a real
failure, across all green rows) is the metric to compare. This mattered: it made
turn-economy look like a 9-point regression when the true figure is −3.1pp.

**Untouched by either bug, and still valid as first reported:** span, mutation survivors,
CRAP, DRY, catches, staleness. Both findings' *conclusions* stand; several of their
*numbers* did not, and now carry dated corrections in place.

---

## 2. Corrected result for PR #17 (`turn-economy`, closes #13/#14)

The only prompt delta between these two arms is the developer's `## Turn economy`
section — clean single-variable comparison. (`spec-gap-reviewer` does not run in a
`/run-pipeline` arm; verified zero dispatches.)

| | s1s2 (adopted) | turn-economy | |
|---|---|---|---|
| **API calls** | 669 | **476** | **−29%** |
| developer API calls/dispatch | **36** | **20** | **−44%** |
| **tool calls per API call** | 1.66 | **2.31** | **+39%** |
| — developer alone | **1.25** | **2.41** | **+93%** |
| API calls carrying 1 tool call | 60% | 43% | |
| **cache-read** | **36.7M** | **23.2M** | **−37%** |
| context per API call | 54,786 | 48,639 | −11% |
| Bash bytes total | 231,059 | 108,456 | −53% |
| output tokens | 429,198 | 439,306 | +2.4% |
| span | 104 min | 95 min | **not claimable, 3-arm rule** |
| **red arrival** | **89.1%** | 86.0% | −3.1pp |
| rows with no red evidence | **0** | 7 | ⚠️ |
| catches (`> Note to architect:`) | **18** | 10 | ⚠️ unexplained |
| **mutation candidate-real** | **0** | **3** | ⚠️ |
| CRAP over threshold | 0 (mean 1.23) | 0 (mean 1.26) | flat |
| rows | 101 | 100 | flat |
| **Rule 1 uniqueness guard** | **ABSENT** | **present** | ⚠️ see below |

**The cost win is mechanistic, not an aggregate.** `tool/api` is 1.45–1.69 in all seven
other arms; turn-economy is the only one at 2.31, far outside the spread. The
distribution has calls carrying 4, 5, 6 and a tail of 14, 18, 20 tool calls.

**The correctness win is the bigger one.** s1s2's `OpenAccountUseCase.run` builds a fresh
empty `Account` and calls JPA `save` unconditionally: re-opening an existing account
replaces the row and **destroys its entire movement history**. No guard anywhere in the
arm. turn-economy adds `AccountNumberAlreadyTakenException`, the use-case check, the 409
mapping and two tests — reached through unplanned rows whose Status cells record real red
states. Guard presence across all eight arms: absent in `baseline` and `treatment-s1s2`,
present in the other six.

**The three mutation survivors:** `AccountNumber.constructor-impl` ×2 (NegateConditionals,
EmptyObjectReturnVals) — recurring benchmark artifacts, also survived in layered-2 and
layered-3, a format guard the frozen spec never constrains; plus **`Account.creditMovement`
NegateConditionals, genuine and new** — the transfer-*in* movement's counterparty is not
pinned on the destination account, while the symmetric `debitMovement` is. A transfer
would record a plain deposit with no counterparty and no test would notice. Real, moderate,
one finding.

**Mechanism to watch, if a confirmation arm runs:** developer build calls dropped 92 → 69
(−25%). That is the Bash-quieting half (#14), not the batching half (#13), and fewer suite
runs is the plausible route to 7 rows with no red evidence. Worth splitting the two halves
if the next arm reproduces it.

**Prompt defect found during this review and fixed on the branch:** the Turn-economy
section's own example told the developer that "a class's test file and its production
file" are independent and belong in one message — flatly incompatible with batch-red,
which the same file mandates two sections earlier. The arm never acted on it (0 of 240
write-messages combined the two), so it did not contaminate the result, but it licensed
breaking the pipeline's core discipline. Now says the opposite, explicitly.

---

## 3. Standing position

**Adopted** (PR #18, `pipeline-scorecard-baseline`): Stage 1 + Stage 2 — **−18% span,
−24% output tokens**, mutation candidate-real **0**, red arrival 89.1%, catches 18. Plus
`spec-gap-reviewer` at `/intent-and-goal` Phase 2b. **PR #17 is a strict superset of #18**
(`git merge-base --is-ancestor pipeline-scorecard-baseline turn-economy` passes), so
merging #17 subsumes it — close #18 rather than merging both.

**Rejected with evidence:**
- Stage 3 planning lookahead, 2-deep and 1-deep (finding 15). Red arrival collapses:
  89.1% → 64.0%/67.7%, with 25 and 23 rows showing no failure evidence at all against 0.
  This is the cleanest negative result in the programme, and the fixed classifier
  *strengthens* it.
- Stage 4 scenario DAG — cut before building; measured value would mostly reflect a
  benchmark property we chose.
- Layered pipeline, 4 arms (finding 16). Spans 74/103/103, mutation 1/4/2 vs 0.
  `agents/_rejected-system-architect/`, `commands/_rejected-run-pipeline-layered.md`.
  Note after the fix: mutation now carries this rejection almost alone, since the
  red-arrival spread narrowed. It is the weaker version of the argument; the conclusion
  holds but is worth revisiting if the layered fork is ever proposed again.

**Open:**
- **#13** batching — **WRONGLY CLOSED, must reopen.** It works: −37% cache-read,
  tool/api 1.66 → 2.31.
- **#14** Bash quieting — in PR #17. Real but small (Bash was 40.7% of a minority share;
  `Read` results are 49.8% of context bytes).
- **#15** skill split — `skills/testing/SKILL.md` is 545 lines, loaded whole by both
  test-designer and developer. Honest effect ~2%; do it for maintainability. Method: move
  whole sections verbatim by line range, never rewrite, so no rule is silently dropped.
- **#16** Stage 6, deliberation budget — `effort` is uniform `medium` on every dispatch;
  file content is only 20–26% of output tokens. Requires **3 arms per configuration**.

---

## 4. Standing rules earned the hard way

1. **No wall-clock claim from fewer than three arms.** Span misled twice: the 1-deep arm's
   speed claim was confounded by row count (89–127 across arms, span tracks it), and
   layered-1's 74 min looked like −42% until two confirmation arms landed at 103 both.
2. **No claim from an interim reading.** The "−17% ctx/turn at 6 dispatches" became −4% on
   the full arm.
3. **Quality metrics are better behaved than cost metrics** — mutation and red→green have
   moved consistently and in the predicted direction every time. Two arms of quality signal
   beat two arms of speed signal.
4. **Verify a metric's *definition* before building on it**, not just its value. All three
   of the worst errors here (turns, cache-read, red→green) were definition bugs that
   produced confident, wrong, and *internally consistent* stories.
5. **Metrics must be orthogonal, or one will silently eat another.** `red_then_green` and
   `unplanned` were mutually exclusive by accident of an elif-chain, so an arm was
   penalised on test strength for adding tests. Any classifier with a fall-through chain
   needs asking: what does a row lose by matching an earlier branch?
6. **When a bug's blast radius is unknown, check every arm, not one.** I sampled s1s2,
   found output tokens inflated 1.03×, and wrote down that tokens were safe. Baseline was
   inflated 1.12×, which moved finding 15's headline by 6 points. A single-arm spot check
   is not a bound.
7. **Read the produced source, not just the oracles.** The most decision-relevant fact in
   this whole review — that the adopted config destroys movement history on re-open — is
   invisible to mutation, CRAP, DRY and every row-level metric, because no test and no
   mutant covers behaviour nobody wrote. Three `grep`s found what eight scored arms
   could not.
8. `gh` on this repo: use `GH_TOKEN=$(cat ~/.claude-flow-gh-token)` — the default login is
   `marceloprerender`, pull-only, so `gh pr create` fails while `gh issue create` works.

---

## 5. The rig — paths and commands

```
~/.claude/evals/benchmark/
  bank-accounts/specification.md   FROZEN 9-scenario spec. Every arm runs it verbatim.
  fixture/                         Boot 3.5 / JUnit 5 / Java-21 bytecode from JDK 25
  fixture/.claude/CLAUDE.md        arm hygiene: work in place, no worktree, no /intent-and-goal
  oracle/oracle.init.gradle.kts    PIT + JaCoCo, applied OUT OF BAND so agents stay blind
  run-arm.sh <arm>                 materialise; --score runs oracle + scorecard
  run-confirmation-arms.sh a b     sequential; never run arms concurrently (CPU contention
                                   corrupts span, the metric being confirmed)
  rescore-cost.sh                  re-derive EVERY arm's cost side from stored transcripts,
                                   without re-running the oracle. Use after any change to
                                   extract_run.py; that is what it was written for.
  runs/                            gitignored arm workspaces
  scorecards/<arm>/                committed results
~/.claude/evals/scorecard/extract_run.py       both §1 bugs fixed 2026-08-12
~/.claude/evals/scorecard/baseline-gym-walls.md  Android datapoint of record
~/.claude/tools/mutation/{classify-survivors,crap,dry}.py
```

Launch an arm (headless, unattended — no human corrections, consistent across arms):
```bash
cd ~/.claude/evals/benchmark && ./run-arm.sh <arm>
cd runs/<arm> && nohup claude -p "/run-pipeline bank-accounts" --dangerously-skip-permissions > ../../<arm>-run.log 2>&1 &
# then: ./run-arm.sh <arm> --score
```

**PIT toolchain traps** (all encoded in the init script, all cost real time to find):
`gradle-pitest-plugin` 1.19.0 is on the **Gradle Plugin Portal**, not Maven Central (whose
latest 1.15.0 dies on Gradle 9's removed `ReportingExtension.baseDir`); init-script plugins
apply by class (`apply<T>()`), not id; `JavaToolchainService` must be resolved at project
scope, not inside `configureEach`; `addJUnitPlatformLauncher.set(false)` or the injected
launcher misaligns with Boot's engine; **pitest ≥ 1.20.4** — 1.19.1's bundled ASM dies on
Java 25 with `Unsupported class file major version 69`.

## 6. Arms on record

All figures below are post-fix (per-`requestId` tokens, orthogonal red-arrival).
Regenerate any time with `evals/benchmark/rescore-cost.sh` — it re-derives the cost side
of every arm from the stored transcripts without re-running the oracle.

| arm | span | out-tok | api | tool/api | cache-read | mut-real | red arr | Rule 1 | note |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 127 | 564,943 | 787 | 1.69 | 48.0M | 2 | 80.5% | ✗ | pre-Stage-1/2 control |
| **treatment-s1s2** | **104** | **429,198** | 669 | 1.66 | 36.7M | **0** | **89.1%** | **✗** | **adopted config** |
| treatment-s3 (2-deep) | 75 | 390,762 | 680 | 1.66 | 40.4M | 1 | 64.0% | ✓ | rejected |
| treatment-s3-1deep | 106 | 450,950 | 716 | 1.55 | 47.1M | 1 | 67.7% | ✓ | rejected |
| layered-seq | 74 | 280,012 | 324 | 1.47 | 25.6M | 1 | 83.6% | ✓ | rejected (outlier span) |
| layered-2 | 103 | 356,013 | 493 | 1.45 | 45.5M | 4 | 81.0% | ✓ | rejected |
| layered-3 | 103 | 401,981 | 510 | 1.45 | 42.5M | 2 | 93.6% | ✓ | rejected |
| turn-economy | 95 | 439,306 | **476** | **2.31** | **23.2M** | 3 | 86.0% | ✓ | **decision pending** |

Two columns are worth reading down rather than across. **`tool/api`** sits in 1.45–1.69
for seven arms and 2.31 for one — the batching change is the only thing that has ever
moved it. **`Rule 1`** is the uniqueness guard whose absence destroys movement history:
the two arms missing it are the baseline and the config we adopted.

Android reference (never re-run, different stack/feature): gym-walls, 5h09, 13 scenarios,
23.7 min/scenario, 3.25 min/row, 10,681 out-tok/row.
