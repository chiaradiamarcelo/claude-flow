# Scorecard — treatment-s3

- span **75 min** · agent time 103 min · dispatches 39 · output tokens 390,762
- scenarios 9 · **8.4 min/scenario** · 43,418 out-tok/scenario
- test rows 89 · **0.85 min/row** · 4,391 out-tok/row
- **API calls 680** (1,614 assistant log events, 2.37 per call) · cache-read 40,378,714 (**103x output**) · avg context/call 59,380
- tool calls 1,132 · **1.66 per API call** · calls carrying exactly one tool call 60%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 60.5 | 218,521 | 38 | 75,267 | 1.35 | 65,097 | 120,899 | 35% | 79 | 136 | claude-opus-5 | medium |
| test-designer | 9 | 15.7 | 56,419 | 7 | 37,437 | 1.59 | 29,446 | 0 | 100% | 0 | 64 | claude-opus-5 | medium |
| architect | 9 | 8.0 | 34,215 | 5 | 24,588 | 1.76 | 20,033 | 0 | 100% | 0 | 50 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 5.8 | 24,524 | 12 | 42,064 | 2.11 | 0 | 0 | — | 0 | 67 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 4.6 | 21,896 | 11 | 23,645 | 2.76 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 5.0 | 19,181 | 18 | 36,085 | 2.73 | 0 | 0 | — | 0 | 95 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.8 | 16,006 | 14 | 29,192 | 3.18 | 0 | 0 | — | 0 | 79 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 57 | 64.0% |
| early_green | 7 | 7.9% |
| deferred_blind | 0 | 0.0% |
| unplanned | 25 | 28.1% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **57** | **64.0%** of green rows |
| no red evidence | 25 | 28.1% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.6 min · sum 8.3 min · **ratio 3.18 → parallel** |
| reviewer round 2 | 4 reviewers · span 2.5 min · sum 7.7 min · **ratio 3.08 → parallel** |
| reviewer round 3 | 2 reviewers · span 2.2 min · sum 3.2 min · **ratio 1.46 → SERIAL** |
| fix rounds | 2 · 16.1 min · 66,001 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 8 |
| **plan staleness** (`> Stale plan:`) | **10** — plan-attributed 0, code-attributed 0, unattributed 10 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s3/scorecard.json_
