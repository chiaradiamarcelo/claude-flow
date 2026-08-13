# Scorecard — turn-economy

- span **95 min** · agent time 98 min · dispatches 39 · output tokens 439,306
- scenarios 9 · **10.5 min/scenario** · 48,812 out-tok/scenario
- test rows 100 · **0.95 min/row** · 4,393 out-tok/row
- **API calls 476** (1,548 assistant log events, 3.25 per call) · cache-read 23,151,968 (**53x output**) · avg context/call 48,639
- tool calls 1,099 · **2.31 per API call** · calls carrying exactly one tool call 43%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 53.5 | 246,986 | 20 | 68,606 | 2.41 | 49,016 | 122,905 | 29% | 69 | 165 | claude-opus-5 | medium |
| test-designer | 9 | 15.2 | 61,560 | 6 | 33,820 | 1.61 | 34,468 | 0 | 100% | 0 | 52 | claude-opus-5 | medium |
| architect | 9 | 11.0 | 48,874 | 7 | 25,805 | 2.22 | 24,650 | 0 | 100% | 0 | 95 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 6.2 | 31,471 | 10 | 38,191 | 2.45 | 0 | 0 | — | 0 | 66 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 5.1 | 23,396 | 10 | 23,528 | 2.25 | 0 | 0 | — | 0 | 59 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.5 | 15,232 | 16 | 29,779 | 2.56 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 3.1 | 11,787 | 13 | 29,399 | 2.85 | 0 | 0 | — | 0 | 71 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 77 | 77.0% |
| early_green | 7 | 7.0% |
| deferred_blind | 0 | 0.0% |
| unplanned | 16 | 16.0% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **86** | **86.0%** of green rows |
| no red evidence | 7 | 7.0% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.7 min · sum 8.0 min · **ratio 2.94 → parallel** |
| reviewer round 2 | 4 reviewers · span 1.7 min · sum 5.6 min · **ratio 3.31 → parallel** |
| reviewer round 3 | 2 reviewers · span 2.2 min · sum 4.3 min · **ratio 1.95 → parallel** |
| fix rounds | 2 · 11.9 min · 58,668 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 10 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/turn-economy/scorecard.json_
