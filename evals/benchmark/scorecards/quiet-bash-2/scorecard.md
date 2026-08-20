# Scorecard — quiet-bash-2

- span **97 min** · agent time 101 min · dispatches 39 · output tokens 472,770
- scenarios 9 · **10.8 min/scenario** · 52,530 out-tok/scenario
- test rows 100 · **0.97 min/row** · 4,728 out-tok/row
- **API calls 621** (1,620 assistant log events, 2.61 per call) · cache-read 36,399,562 (**77x output**) · avg context/call 58,614
- tool calls 1,145 · **1.84 per API call** · calls carrying exactly one tool call 57%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 59.9 | 264,687 | 35 | 76,681 | 1.51 | 50,571 | 119,313 | 30% | 103 | 117 | claude-opus-5 | medium |
| test-designer | 9 | 15.5 | 70,419 | 7 | 35,025 | 1.67 | 35,081 | 0 | 100% | 0 | 65 | claude-opus-5 | medium |
| architect | 9 | 10.5 | 55,351 | 5 | 23,222 | 2.34 | 27,373 | 0 | 100% | 0 | 78 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 4.6 | 24,625 | 11 | 21,162 | 2.59 | 0 | 0 | — | 0 | 66 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 3.9 | 20,323 | 14 | 30,857 | 3.29 | 0 | 0 | — | 0 | 87 | claude-sonnet-5 | medium |
| arch-reviewer | 3 | 3.9 | 20,197 | 10 | 22,378 | 3.00 | 0 | 0 | — | 0 | 87 | claude-sonnet-5 | medium |
| test-reviewer | 2 | 3.3 | 17,168 | 10 | 36,330 | 2.48 | 0 | 0 | — | 0 | 43 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 79 | 79.0% |
| early_green | 5 | 5.0% |
| deferred_blind | 0 | 0.0% |
| unplanned | 16 | 16.0% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **83** | **83.0%** of green rows |
| no red evidence | 12 | 12.0% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 1.9 min · sum 6.2 min · **ratio 3.28 → parallel** |
| reviewer round 2 | 4 reviewers · span 2.1 min · sum 7.3 min · **ratio 3.48 → parallel** |
| reviewer round 3 | 2 reviewers · span 1.5 min · sum 2.0 min · **ratio 1.34 → SERIAL** |
| fix rounds | 2 · 14.8 min · 65,102 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 6 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/quiet-bash-2/scorecard.json_
