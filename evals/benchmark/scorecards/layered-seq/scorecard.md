# Scorecard — layered-seq

- span **74 min** · agent time 73 min · dispatches 13 · output tokens 280,012
- scenarios 9 · **8.2 min/scenario** · 31,112 out-tok/scenario
- test rows 116 · **0.63 min/row** · 2,414 out-tok/row
- **API calls 324** (702 assistant log events, 2.17 per call) · cache-read 25,626,056 (**92x output**) · avg context/call 79,093
- tool calls 477 · **1.47 per API call** · calls carrying exactly one tool call 73%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 4 | 44.6 | 156,590 | 57 | 95,370 | 1.10 | 29,877 | 125,753 | 19% | 63 | 20 | claude-opus-5 | medium |
| test-designer | 4 | 17.4 | 74,626 | 8 | 49,261 | 1.74 | 46,733 | 0 | 100% | 0 | 38 | claude-opus-5 | medium |
| arch-reviewer | 1 | 2.9 | 12,540 | 17 | 30,816 | 3.12 | 0 | 0 | — | 0 | 46 | claude-sonnet-5 | medium |
| system-architect | 1 | 2.2 | 10,488 | 7 | 24,971 | 1.00 | 13,696 | 0 | 100% | 0 | 1 | claude-opus-5 | medium |
| test-reviewer | 1 | 2.1 | 10,259 | 14 | 53,053 | 2.57 | 0 | 0 | — | 0 | 31 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 2.3 | 9,931 | 15 | 33,269 | 2.93 | 0 | 0 | — | 0 | 42 | claude-sonnet-5 | medium |
| api-reviewer | 1 | 1.4 | 5,578 | 9 | 29,579 | 3.11 | 0 | 0 | — | 0 | 25 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 97 | 83.6% |
| early_green | 18 | 15.5% |
| deferred_blind | 0 | 0.0% |
| unplanned | 1 | 0.9% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **97** | **83.6%** of green rows |
| no red evidence | 1 | 0.9% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.9 min · sum 8.7 min · **ratio 2.98 → parallel** |
| fix rounds | 0 · 0.0 min · 0 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 11 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-seq/scorecard.json_
