# Scorecard — layered-3

- span **103 min** · agent time 166 min · dispatches 17 · output tokens 401,981
- scenarios 9 · **11.5 min/scenario** · 44,665 out-tok/scenario
- test rows 157 · **0.66 min/row** · 2,560 out-tok/row
- **API calls 510** (1,079 assistant log events, 2.12 per call) · cache-read 42,489,985 (**106x output**) · avg context/call 83,314
- tool calls 739 · **1.45 per API call** · calls carrying exactly one tool call 74%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 6 | 57.9 | 225,709 | 54 | 102,281 | 1.19 | 18,571 | 132,879 | 12% | 103 | 67 | claude-opus-5 | medium |
| test-designer | 4 | 26.8 | 95,332 | 13 | 56,841 | 1.47 | 67,064 | 0 | 100% | 0 | 42 | claude-opus-5 | medium |
| system-architect | 1 | 70.0 | 33,084 | 52 | 61,851 | 0.92 | 33,335 | 0 | 100% | 0 | 15 | claude-opus-5 | medium |
| test-reviewer | 2 | 4.8 | 18,277 | 14 | 44,564 | 2.24 | 0 | 0 | — | 0 | 48 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.5 | 16,253 | 12 | 30,185 | 3.16 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| api-reviewer | 1 | 1.9 | 7,773 | 11 | 27,769 | 3.00 | 0 | 0 | — | 0 | 28 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 1.4 | 5,553 | 12 | 30,035 | 3.75 | 0 | 0 | — | 0 | 42 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 144 | 91.7% |
| early_green | 4 | 2.5% |
| deferred_blind | 0 | 0.0% |
| unplanned | 9 | 5.7% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **147** | **93.6%** of green rows |
| no red evidence | 6 | 3.8% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.0 min · sum 7.8 min · **ratio 2.57 → parallel** |
| reviewer round 2 | 2 reviewers · span 2.1 min · sum 3.8 min · **ratio 1.80 → parallel** |
| fix rounds | 2 · 11.9 min · 37,096 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 6 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-3/scorecard.json_
