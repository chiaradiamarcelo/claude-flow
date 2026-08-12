# Pipeline cost programme — working state

**Read this first after a compaction.** Written 2026-08-12. Live working notes, not a
finding. Findings 15 and 16 are the durable record; this file is what is *in flight*.

Immediate next action: **fix `extract_run.py` to key on `requestId`, re-derive every arm,
then decide whether to merge PR #17.**

---

## 1. The measurement bug just found — read before trusting any number

`evals/scorecard/extract_run.py` sums `message.usage` **per assistant event**. Claude Code
logs **one API response as several assistant events** (a thinking block, then one per
tool_use), and several of them repeat the same `usage` block.

Verified on the s1s2 arm: **1,590 assistant events vs 669 distinct `requestId`s** (2.38
events per API call; developer alone 751 events / 401 calls = 1.87).

| quantity | per-event (what was quoted) | per-request (truth) | inflation |
|---|---|---|---|
| `output_tokens` | 440,250 | 429,198 | **1.03× — harmless** |
| `cache_read_input_tokens` | 73,849,792 | **36,651,982** | **1.76× — wrong** |
| "turns" | 1,590 | **669 API calls** | **2.38× — wrong concept** |

**Fix:** dedupe usage by `ev["requestId"]` (take one value per request, not a sum), and
count API calls as `len(set(requestId))`. Events with no `requestId` were 0 in the arms
checked, but guard anyway.

### What this invalidated, and what it did not

**Invalid — do not cite:** every `turns`, `cache-read`, `ctx/turn` figure; the claim that
subagents cannot batch tool calls; "2 multi-tool turns in 36,895"; "1.00 tool calls per
acting turn"; the interim "−17% ctx/turn" and the "68 → 72 turns went up" reading.

**Still valid:** output tokens (within 3%), span, mutation survivors, CRAP, DRY, row-level
quality (red→green, early-green, unplanned, catches, staleness). So **findings 15 and 16
stand** — none of their conclusions rest on turns or cache-read.

---

## 2. Corrected result for PR #17 (`turn-economy`, closes #13/#14)

Recomputed per `requestId`:

| | s1s2 (adopted) | turn-economy | |
|---|---|---|---|
| **API calls** | 669 | **476** | **−29%** |
| developer API calls/dispatch | **36** | **20** | **−44%** |
| **tool calls per API call** | **1.25** | **2.41** | **+93%** |
| API calls carrying 1 tool call | 81% | 52% | |
| **cache-read** | **36.7M** | **23.2M** | **−37%** |
| context per API call | 54,786 | 48,638 | −11% |
| Bash bytes total | 231,059 | 108,456 | −53% |
| **output tokens** | 440,250 | **460,631** | **+5% — worse** |
| span | 104 min | 95 min | **not claimable, 3-arm rule** |
| **mutation candidate-real** | **0** | **3** | ⚠️ the open question |
| CRAP over threshold | 0 (mean 1.23) | 0 (mean 1.26) | flat |
| rows | 101 | 100 | flat |

The batching distribution is decisive: the after-arm has API calls carrying 4, 5, 6 and a
tail of 14, 18 and 20 tool calls. Before, 81% carried exactly one.

**Trade to decide:** −37% cache-read and −29% API calls, against +5% output tokens and one
new mutation survivor. Cache-read ≈ 3× output in dollar terms (≈10% of input price × 36.7M
vs ≈5× input price × 440k), so it is a clear net win on spend.

**The three mutation survivors:** `AccountNumber.constructor-impl` ×2 (NegateConditionals,
EmptyObjectReturnVals) — **also survived in layered-2 and layered-3**, a guard on
account-number format that the frozen spec never constrains and that `spec-gap-reviewer`
flagged as an unspecified ambiguity; plus `Account.creditMovement` NegateConditionals,
genuine business logic and new. So ≈1 new survivor + 2 recurring benchmark artifacts.

**Recommended before merging:** one confirmation arm, now worth the ~100 min because the
prize is 37% rather than the 4% I mistakenly reported.

---

## 3. Standing position

**Adopted and merged into the pipeline** (PR #18 open on `pipeline-scorecard-baseline`):
Stage 1 + Stage 2 — **−18% span, −30% output tokens**, mutation candidate-real **0**,
red→green 86.1%, catches 18. Plus `spec-gap-reviewer` at `/intent-and-goal` Phase 2b.

**Rejected with evidence:**
- Stage 3 planning lookahead, 2-deep and 1-deep (finding 15). Red-arrival is incompatible
  with planning ahead: red→green 86% → 64%/61%.
- Stage 4 scenario DAG — cut before building; measured value would mostly reflect a
  benchmark property we chose.
- Layered pipeline, 4 arms (finding 16). Spans 74/103/103, mutation 1/4/2 vs 0.
  `agents/_rejected-system-architect/`, `commands/_rejected-run-pipeline-layered.md`.

**Open:**
- **#13** batching — **WRONGLY CLOSED, must reopen.** It works: −37% cache-read.
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
4. **Verify a metric's *definition* before building on it**, not just its value. Both of the
   worst errors here (turns, cache-read) were definition bugs that produced confident,
   wrong, and *internally consistent* stories.
5. `gh` on this repo: use `GH_TOKEN=$(cat ~/.claude-flow-gh-token)` — the default login is
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
  runs/                            gitignored arm workspaces
  scorecards/<arm>/                committed results
~/.claude/evals/scorecard/extract_run.py       <-- HAS THE BUG IN §1
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

| arm | span | out-tok | mut-real | red→green | note |
|---|---|---|---|---|---|
| baseline | 127 | 633,728 | 2 | 78.8% | pre-Stage-1/2 control |
| **treatment-s1s2** | **104** | **440,250** | **0** | **86.1%** | **adopted config** |
| treatment-s3 (2-deep) | 75 | 414,457 | 1 | 64.0% | rejected |
| treatment-s3-1deep | 106 | 465,913 | 1 | 61.4% | rejected |
| layered-seq | 74 | 284,149 | 1 | 83.6% | rejected (outlier span) |
| layered-2 | 103 | 364,545 | 4 | 71.4% | rejected |
| layered-3 | 103 | 412,250 | 2 | 91.7% | rejected |
| turn-economy | 95 | 460,631 | 3 | — | **decision pending** |

Android reference (never re-run, different stack/feature): gym-walls, 5h09, 13 scenarios,
23.7 min/scenario, 3.25 min/row, 10,681 out-tok/row.
