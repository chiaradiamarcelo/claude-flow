# Pipeline cost programme — working state

**Read this first after a compaction.** Written 2026-08-16. Live working notes, not a
finding. Findings 15, 16 and 17 are the durable record; this file is what is *in flight*.

**Immediate next action: nothing is running.** The user has a **12-scenario Android feature
run** going in another session and will hand over its **worktree path** when it finishes.
That is the next piece of work — see §5.

---

## 1. Where the programme stands

Merged to `main`: the plan-file caps, the mandated Status vocabulary, the severity-ordered
2-round fix loop with `## Follow-ups`, the reviewer gate on VIOLATIONs only, tool-call
batching in the developer, the rule-coverage check inside `/intent-and-goal` Phase 2, the
measurement rig, and findings 15 and 16.

**Open PR #25** (`fix-arm-identity`) — finding 17, both #14 arms' scorecards, the
`run-arm.sh` identity fix, and the nine restored mutation XMLs. **Merge this**: until it
lands, a new arm's per-scenario commits still take the machine's global git identity.

**Open issues:** #24 (shell file-inspection — the real Bash lever), #21 (a 529 destroys an
arm), #16 (Stage 6 deliberation budget), #15 (split the testing skill), #12 (unrelated).

**Closed this round:** #13 batching, shipped and measured. #14 Bash quieting, **rejected**.

## 2. Arms on record

All eleven live in `evals/benchmark/scorecards/`. The table with *what each arm tested*
lives in `evals/benchmark/README.md` — read that column before citing any row.

| arm | what it tested | span | out-tok | api | tool/api | mut-real | red arr |
|---|---|---|---|---|---|---|---|
| `baseline` | pre-programme control | 127 | 564,943 | 787 | 1.69 | 2 | 80.5% |
| `treatment-s1s2` | plan caps + reviewer gate | 104 | 429,198 | 669 | 1.66 | 0 | 89.1% |
| `treatment-s3` | plan 2 ahead — rejected | 75 | 390,762 | 680 | 1.66 | 1 | 64.0% |
| `treatment-s3-1deep` | plan 1 ahead — rejected | 106 | 450,950 | 716 | 1.55 | 1 | 67.7% |
| `layered-seq` | layer as unit — rejected | 74 | 280,012 | 324 | 1.47 | 1 | 83.6% |
| `layered-2` | layered confirmation | 103 | 356,013 | 493 | 1.45 | 4 | 81.0% |
| `layered-3` | layered confirmation | 103 | 401,981 | 510 | 1.45 | 2 | 93.6% |
| `turn-economy` | #13+#14 together — unattributable | 95 | 439,306 | 476 | 2.31 | 3 | 86.0% |
| `batching-only-4` | #13 alone — shipped | 103 | 451,859 | 555 | 1.93 | 0 | 78.7% |
| **`main-control`** | **current `main` — the control for all future arms** | 102 | 473,784 | 618 | 1.75 | 3 | 84.1% |
| `quiet-bash-2` | #14 — rejected | 97 | 472,770 | 621 | 1.84 | 0 | 83.0% |

**`main-control` is the baseline for everything from here.** `batching-only-4` measured a
prompt set that no longer exists.

## 3. Standing rules, earned the hard way

1. **No wall-clock claim from fewer than three arms.** Span has ranged 74–127 min.
2. **No claim — cost *or mechanism* — from an interim or partial reading.** Four inversions
   now. The worst: #14 read −46% Bash bytes at 2 of 11 dispatches and **+31%** complete.
   Its predecessor arm died at 7/9, so a false mechanism story was one crash from being
   published.
3. **A metric parsed out of agent prose measures the prose.** Three cases: usage summed per
   log event; `red_then_green` made exclusive with `unplanned` by an elif-chain; and
   `red_arrival` moving because Status cells got 42% shorter while suite runs stayed at
   103 vs 110. Cross-check a behavioural counter before believing any of them.
4. **Filtered mutation candidate-real has ranged 0–4 across eleven arms with no treatment
   explaining the spread.** A gate of "must not increase" is a floor against gross failure,
   not a precision instrument. Single-arm moves inside that band are noise. This applies
   retroactively to every gate set here — the Stage 3 and layered rejections survive because
   they rest on red-arrival collapses too, not on mutation alone.
5. **Read the produced source, not only the oracles.** The most decision-relevant defect
   found in this programme — a use case destroying an account's movement history on re-open
   — is invisible to mutation, CRAP, DRY and every row metric.
6. **Verify a metric's *definition* before building on it.** Every serious error here was a
   definition bug producing a confident, internally consistent, wrong story.
7. **Normalise by scenario, not by row, within one frozen spec.** Row count is an *output*
   of a run; dividing by it rewards an arm for writing more tests. Per-row is for comparing
   across different features.

## 4. Rig operation

```
evals/benchmark/README.md      how to run an arm, what is scored, the traps
run-arm.sh <arm>               materialise; --score runs oracles + scorecard
rescore-cost.sh                re-derive every arm's cost side from stored transcripts
evals/scorecard/extract_run.py transcript -> scorecard, keyed on requestId
```

```bash
cd runs/<arm> && nohup caffeinate -i -s -m \
  claude -p "/run-pipeline bank-accounts" --dangerously-skip-permissions \
  > ../../<arm>-run.log 2>&1 < /dev/null &
pmset -g assertions | grep PreventUserIdleSystemSleep   # must be 1
```

- **`caffeinate` is not optional** — an arm died 11 minutes in to an idle sleep.
- **Never switch branches in `~/.claude` while an arm runs.** The checkout *is* the live
  config the arm reads on every dispatch. Use `git worktree` to edit another branch.
- **An arm a human helped is not an arm.** Discard it however complete it looks.
- **A 529 destroys an arm** (#21) — four instant retries, no backoff, then it proceeds as
  though the scenario were skipped.
- **Spend limits kill arms mid-run.** One died at 7/9. There is no way to check headroom
  from inside the session; ask before starting a paid run.
- `gh` on this repo: `export GH_TOKEN=$(cat ~/.claude-flow-gh-token)` in the **same**
  command. The ambient login is the user's work account — never author anything as it.

## 5. NEXT: the 12-scenario Android run

The user is running a real 12-scenario feature on the merged `main` config in another
session. **This is the external validation the whole programme was for** — the user said at
the outset they would judge it on a real Android feature rather than re-running gym-walls.

**They will hand over the worktree path.** From that alone everything is extractable: the
Claude Code project slug is the path with `/` and `.` replaced by `-`, giving
`~/.claude/projects/<slug>/<session>/subagents/`. The worktree gives the plan files and the
source.

Per-scenario breakdown is already verified working — architect / test-designer / developer
API calls and wall-clock minutes per scenario, by parsing `SCENARIO-NN` out of each
dispatch's `description` in its `.meta.json`.

**Two things that would break the analysis:**

- **A session restart mid-run** creates a second session directory, and the extractor takes
  only the most recent — silently dropping every earlier dispatch. gym-walls ran 5h09, so a
  12-scenario run is well inside the range where this happens. Ask whether they restarted,
  and merge the directories if so.
- **The oracles will not run** on Android — the init script targets a Boot/JVM Gradle
  fixture. This does **not** matter: mutation/CRAP/DRY were never part of `/run-pipeline`
  (finding 14 rejected a gate), and everything worth extracting comes from transcripts and
  plan files, which are stack-agnostic. I raised this once as a limitation and was correctly
  told it was noise — do not repeat that.

**Asked the user to note, since transcripts cannot show it:** any pause (span is wall-clock
and a lunch break is undetectable afterwards), every intervention *and why*, anything that
felt wrong, and whether they would have shipped the code unchanged. This is the first
**attended** run of the programme; unlabelled interventions make it incomparable.

Compare per unit against gym-walls: **23.7 min/scenario, 3.25 min/row, 10,681 out-tok/row**.

## 6. Still open, in the order I would take them

1. **#24 shell file-inspection.** The real Bash lever — 64.6% of the developer's Bash bytes
   against gradle's 35.2%. Harder than it looks: those bytes rose 41% in the #14 arm with no
   rule aimed at them, so the number moves for reasons not yet understood.
2. **Arm B — one suite run per class instead of two.** Design written and rationale recorded
   in the scratchpad note from 2026-08-12: after writing a class's production code, do not
   run the suite; the next class's batch-red run confirms both. Runs per scenario go 2N →
   N+1 while every class keeps a real behavioural red. Rejected alternatives are in that
   note: per-scenario batch-red (compile-cascade destroys the red evidence) and test+prod in
   one message (≤16% of developer API calls, and removes the property finding 14 relied on).
3. **#21** 529 handling, **#15** skill split, **#16** Stage 6 deliberation budget (needs 3
   arms per configuration).
