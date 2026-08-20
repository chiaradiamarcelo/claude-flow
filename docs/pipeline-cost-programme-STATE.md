# Pipeline cost programme — working state

**Read this first after a compaction.** Written 2026-08-17. Live working notes, not a
finding. Findings 15, 16 and 17 are the durable record; this file is what is *in flight*.

**Nothing is running. No arm is in progress.** The Android validation run is **done** and
analysed — see §2, which replaces the "next action" this file used to carry.

---

## 1. Where the programme stands

**Merged to `main`:** plan-file caps, mandated Status vocabulary, severity-ordered 2-round
fix loop with `## Follow-ups`, reviewer gate on VIOLATIONs only, developer tool-call
batching, the rule-coverage check in `/intent-and-goal` Phase 2, the measurement rig,
findings 15 and 16, **the `comments` skill (#33)**, and **reviewer skill wiring (#36)**.

**Also merged since:** **#37**, dropping the per-scenario commit rule (closed #30 — the rule had
never fired in any run on record).

**Open PRs:**

| PR | What | Why it matters |
|---|---|---|
| **#25** (this branch) | finding 17, both #14 arms' scorecards, `run-arm.sh` identity fix, 9 restored mutation XMLs, this file | **Closes the work-email leak at source.** Until it lands, a new arm's git commands take the machine's global identity |
| **#38** | `/mutation-audit` on Maven + Stryker (closes #12) | Also fixes a glob bug that made the command's own documented filter invocation read nothing on a real PIT run |
| **#42** → #38 | `classify-survivors` status buckets + generated-Kotlin rules (#28, partly) | The oracle was unusable on coroutine Kotlin. Does **not** fix suspend-entry filtering — unvalidatable without a report, see the PR |
| **#39** | refactor-advisor reviews its whole scope; `mustFlagFiles` / `mustScope` | It had a closed reading list, so `presentation/` was never read. **13/13 paid, verified** |
| **#41** → #39 | triggers for any layout, `cqrs` unconditional, cross-file comment rule | `**/src/main/**` matched nothing in KMP/TS/Go, so two reviewers silently never fired. **25/25 paid, verified** |

**Open issues, in the order I would take them:**

1. **#28 — `classify-survivors.py` on Kotlin coroutines.** #42 fixes the status buckets and the
   generated-Kotlin rules; what remains is the suspend-entry filter, which needs a coroutine PIT
   report to validate against. boulder-friend's is gone, so this now waits on the next such run
   rather than blocking one.
2. **#40 — the eval harness grades the live `~/.claude` checkout, not the tree it runs in.**
   Do this before the next eval run from a worktree; it is the third instance of a green suite
   compatible with the thing under test being absent.
3. **#27 — `red_arrival` scores mutant-proven early-green rows as the weakest category.**
   No red-arrival figure should be quoted for a future run until this lands.
4. **#29** reviewer parallelism ratio mislabels parallel rounds · **#31** no cheap exit for an
   untestable scenario · **#32** markdown is the largest remaining output · **#24** shell
   file-inspection · **#21** a 529 burns an arm · **#16** Stage 6 deliberation budget ·
   **#15** split the testing skill.

**#34** (deterministic orphaned-doc-block check) is **closed as confounded**: the five reviewers
that missed the orphans were running with no `comments` skill and no skill content at all (#33 /
#36 both postdate that run), so no model was ever asked. Reopen only if a post-#33/#36 run still
emits one *and* `refactor-advisor` misses it.

A TypeScript port of everything above exists in the `prerender/monostack` repo (PR #4405).
Out of scope here; noted only so it is not rediscovered.

## 2. The Android validation run — done, and it delivered

`boulder-friend` PR #19, `filter-by-grade`: **14 scenarios, 167 min, unattended**, on the
merged `main` config. This was the external validation the whole programme was for.

Against **gym-walls** (13 scenarios, pre-programme config, the only other real-Android
datapoint):

| | gym-walls | filter-by-grade | |
|---|---|---|---|
| wall clock / scenario | 23.7 min | **11.9 min** | **−50%** |
| output tokens / scenario | 78,053 | **38,265** | **−51%** |
| architect tok/dispatch | 13,031 | 5,114 | −61% |
| test-designer tok/dispatch | 23,759 | 8,728 | **−63%** |
| test-designer markdown chars | 321,479 | 51,975 | **−84%** |
| reviewer round-1 span | 12.7 min (serial) | 3.4 min (parallel) | −73% |
| fix rounds | 2 (24.4 min) | 1 (6.7 min) | |
| unclassified / deferred-blind rows | 36.8% / 22.1% | **0% / 0%** | |

Two features, n=1 each — the weakest kind of comparison. It carries weight only because the
direction agrees with the controlled arms and the two biggest movers are exactly where the
caps were aimed.

**Quality, verified by me rather than claimed:** 365 JVM tests, 0 failures, 0 skipped.
CRAP **0 methods over threshold** in domain / application / infrastructure (means 1.17–1.33);
the 86 over-threshold methods are all `@Composable`s at 0% *JVM* coverage, covered by the 133
instrumented tests JaCoCo cannot see from that task. DRY 1.85%, and every clone is an import
block. **`CatalogFilter` — the class the feature turns on — 14 mutants, 14 killed.**

**Also true and worth remembering:** the run was never blocked. Largest gap between dispatches
3.3 min, largest stall inside one 2.2 min. A recollection of it waiting on input was not borne
out by the transcripts.

## 3. What the run taught, beyond the numbers

- **PIT is unusable on this codebase, and the filter hid it.** 424 mutants on the non-UI
  layers; `classify-survivors.py` reported **175 candidate-real (96%)**. The true figure is
  **0**. ~103 are coroutine machinery (`invokeSuspend`, `$inlined$map`, `$$serializer`), most
  of the rest are `VoidMethodCall`/`NullReturnVals` on suspend-function entry lines or on an
  `internal inline fun` PIT sees as uncovered, and `TIMED_OUT` was counted as surviving when
  PIT counts it killed. **Exactly one survivor was reproducible as a source edit** — I applied
  it in a clean worktree and 4 tests failed. That is #28.
- **Every early-green row was mutant-proven.** 24 of 46 rows are `EARLY-GREEN`, and all 24
  name a mutant that was applied and confirmed to redden that row. Zero unproven. `red_arrival`
  scored the run 60.5% and calls this the *weakest* category. That is #27.
- **The reviewers were running without their skills.** A bare `@skills/…/SKILL.md` line in an
  agent definition is **not expanded** — it reaches the agent as literal text. All six
  reviewers relied on one. They compensated by reading the path *sometimes*: `test-reviewer`
  did in round 1 and not in round 2 of the same run. Fixed in #33/#36.
- **Comments are 39.2% of production lines added** (369 / 573), 32.1% in tests (745 / 1577),
  and the run wrote **more markdown (2,064 lines) than Kotlin (1,581)**. One comment was
  disproved by SCENARIO-14 *in the same run* and never updated. Three KDoc blocks in one file
  attach to nothing. #33 is the doctrine; #32 and #34 are what remain.

## 4. Standing rules, earned the hard way

1. **No wall-clock claim from fewer than three arms.** Span has ranged 74–167 min.
2. **No claim — cost *or mechanism* — from an interim or partial reading.** Four inversions.
   The worst: #14 read −46% Bash bytes at 2 of 11 dispatches and **+31%** complete.
3. **A metric parsed out of agent prose measures the prose.** Now five cases: usage summed per
   log event; `red_then_green` made exclusive with `unplanned`; `red_arrival` moving because
   Status cells got shorter; `mustMention` passing whether or not a skill loaded; and
   `classify-survivors` on coroutines. Cross-check a behavioural counter before believing any.
4. **Filtered mutation candidate-real has ranged 0–3 across eleven arms with no treatment
   explaining the spread.** A "must not increase" gate is a floor against gross failure, not a
   precision instrument. Was 0–4 until #42 corrected the status buckets: four of the seventeen
   historical candidate-reals were `NO_COVERAGE` mutants, which are a coverage gap, not a weak
   assertion. `main-control` is unchanged at 3, so nothing compared against it moved.
5. **Read the produced source, not only the oracles.** The most decision-relevant defects in
   this programme — a use case destroying an account's history, a comment that lies — are
   invisible to every oracle.
6. **Verify a metric's *definition* before building on it.** Every serious error here was a
   definition bug producing a confident, internally consistent, wrong story.
7. **Normalise by scenario, not by row, within one frozen spec.** Row count is an *output*.
8. **Verify wiring, not just output.** A green eval suite was fully compatible with zero skill
   content loaded. `mustInvokeSkills` grades tool calls; Phase 0 rejects inert `@` includes.
9. **Diff the merged PRs before porting anything.** Working from the files I happened to read
   missed three whole changes in the monostack port.

## 5. Rig operation

```
evals/benchmark/README.md      how to run an arm, what is scored, the traps
run-arm.sh <arm>               materialise; --score runs oracles + scorecard
rescore-cost.sh                re-derive every arm's cost side from stored transcripts
evals/scorecard/extract_run.py transcript -> scorecard, keyed on requestId
evals/run_all.sh <corpus>      reviewer evals (fingerprint-cached, $0 when unchanged)
evals/run_tests.sh             72 harness self-tests, free
```

```bash
cd runs/<arm> && nohup caffeinate -i -s -m \
  claude -p "/run-pipeline bank-accounts" --dangerously-skip-permissions \
  > ../../<arm>-run.log 2>&1 < /dev/null &
pmset -g assertions | grep PreventUserIdleSystemSleep   # must be 1
```

- **`caffeinate` is not optional** — an arm died 11 minutes in to an idle sleep.
- **Never switch branches in `~/.claude` while an arm runs.** The checkout *is* the live config
  the arm reads on every dispatch. Use `git worktree` to edit another branch.
- **An arm a human helped is not an arm.** Discard it however complete it looks.
- **A 529 destroys an arm** (#21) — four instant retries, no backoff, then it proceeds as
  though the scenario were skipped.
- **Spend limits kill arms mid-run.** One died at 7/9. Ask before starting a paid run.
- `gh` on this repo: `export GH_TOKEN=$(cat ~/.claude-flow-gh-token)` in the **same** command.
  The ambient login is the work account — never author anything as it.

**Reviewer evals:** 84 fixtures across six corpora, all passing, each asserting both its
findings *and* `mustInvokeSkills`. A skill edit re-runs exactly the fixtures that depend on it.
What they still cannot do is notice a skill's *content* degrading — `mustMention` is one
substring, and each Agent.md restates enough to satisfy it. That is the next real
strengthening, and it is the same weakness as #27.

## 6. Arms on record

All eleven live in `evals/benchmark/scorecards/`. The *what each arm tested* column is in
`evals/benchmark/README.md` — read it before citing any row. **`main-control` is the baseline
for everything from here**; `batching-only-4` measured a prompt set that no longer exists.

| arm | what it tested | span | out-tok | api | tool/api | mut-real | red arr |
|---|---|---|---|---|---|---|---|
| `baseline` | pre-programme control | 127 | 564,943 | 787 | 1.69 | 2 | 80.5% |
| `treatment-s1s2` | plan caps + reviewer gate | 104 | 429,198 | 669 | 1.66 | 0 | 89.1% |
| `treatment-s3` | plan 2 ahead — rejected | 75 | 390,762 | 680 | 1.66 | 0 | 64.0% |
| `treatment-s3-1deep` | plan 1 ahead — rejected | 106 | 450,950 | 716 | 1.55 | 0 | 67.7% |
| `layered-seq` | layer as unit — rejected | 74 | 280,012 | 324 | 1.47 | 0 | 83.6% |
| `layered-2` | layered confirmation | 103 | 356,013 | 493 | 1.45 | 3 | 81.0% |
| `layered-3` | layered confirmation | 103 | 401,981 | 510 | 1.45 | 2 | 93.6% |
| `turn-economy` | #13+#14 together — unattributable | 95 | 439,306 | 476 | 2.31 | 3 | 86.0% |
| `batching-only-4` | #13 alone — shipped | 103 | 451,859 | 555 | 1.93 | 0 | 78.7% |
| **`main-control`** | **the control for all future arms** | 102 | 473,784 | 618 | 1.75 | 3 | 84.1% |
| `quiet-bash-2` | #14 — rejected | 97 | 472,770 | 621 | 1.84 | 0 | 83.0% |

Real-feature datapoints, not arms: **gym-walls** 13 scenarios / 309 min (pre-programme) and
**filter-by-grade** 14 scenarios / 167 min (current `main`) — §2.

## 7. If you are picking this up cold

Land **#25** and **#38**, then take **#28** — it is the only open item blocking work rather
than improving measurement. After that #27, because until it lands the pipeline's best
behaviour (mutant-proving a pinning row) is scored as its worst.
