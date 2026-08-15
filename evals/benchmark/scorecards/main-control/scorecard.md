# Scorecard — main-control

- span **102 min** · agent time 106 min · dispatches 37 · output tokens 473,784
- scenarios 9 · **11.4 min/scenario** · 52,643 out-tok/scenario
- test rows 82 · **1.25 min/row** · 5,778 out-tok/row
- **API calls 618** (1,583 assistant log events, 2.56 per call) · cache-read 35,985,926 (**76x output**) · avg context/call 58,230
- tool calls 1,080 · **1.75 per API call** · calls carrying exactly one tool call 57%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 63.6 | 270,633 | 35 | 73,114 | 1.46 | 54,604 | 110,087 | 33% | 110 | 122 | claude-opus-5 | medium |
| test-designer | 9 | 15.3 | 67,304 | 6 | 33,265 | 1.56 | 32,252 | 0 | 100% | 0 | 52 | claude-opus-5 | medium |
| architect | 9 | 10.5 | 53,001 | 6 | 26,032 | 2.00 | 26,427 | 0 | 100% | 0 | 78 | claude-sonnet-5 | medium |
| test-reviewer | 2 | 7.0 | 36,104 | 19 | 56,592 | 1.95 | 0 | 0 | — | 0 | 61 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 3.0 | 16,649 | 7 | 19,939 | 3.47 | 0 | 0 | — | 0 | 43 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 3.3 | 15,580 | 12 | 27,023 | 3.12 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.2 | 14,513 | 14 | 27,711 | 3.21 | 0 | 0 | — | 0 | 80 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 63 | 76.8% |
| early_green | 10 | 12.2% |
| deferred_blind | 0 | 0.0% |
| unplanned | 9 | 11.0% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **69** | **84.1%** of green rows |
| no red evidence | 3 | 3.7% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.2 min · sum 7.7 min · **ratio 2.37 → partial** |
| reviewer round 2 | 4 reviewers · span 4.0 min · sum 8.7 min · **ratio 2.16 → partial** |
| fix rounds | 2 · 17.6 min · 70,085 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 4 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/main-control/scorecard.json_
