# Scorecard — baseline

- span **127 min** · agent time 134 min · dispatches 41 · output tokens 564,943
- scenarios 9 · **14.1 min/scenario** · 62,771 out-tok/scenario
- test rows 113 · **1.12 min/row** · 4,999 out-tok/row
- **API calls 787** (1,907 assistant log events, 2.42 per call) · cache-read 47,971,608 (**85x output**) · avg context/call 60,955
- tool calls 1,332 · **1.69 per API call** · calls carrying exactly one tool call 62%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 12 | 67.6 | 260,259 | 40 | 73,697 | 1.23 | 41,105 | 136,752 | 23% | 114 | 96 | claude-opus-5 | medium |
| test-designer | 9 | 27.9 | 121,620 | 7 | 41,611 | 1.61 | 106,081 | 0 | 100% | 0 | 66 | claude-opus-5 | medium |
| architect | 9 | 15.0 | 77,607 | 7 | 30,887 | 2.22 | 47,568 | 0 | 100% | 0 | 95 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 7.4 | 34,834 | 16 | 54,787 | 2.45 | 0 | 0 | — | 0 | 103 | claude-sonnet-5 | medium |
| refactor-advisor | 4 | 8.4 | 34,093 | 17 | 42,385 | 3.00 | 0 | 0 | — | 0 | 190 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.9 | 19,286 | 12 | 32,286 | 3.71 | 0 | 0 | — | 0 | 82 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 3.6 | 17,244 | 11 | 30,502 | 2.70 | 0 | 0 | — | 0 | 50 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 89 | 78.8% |
| early_green | 9 | 8.0% |
| deferred_blind | 0 | 0.0% |
| unplanned | 15 | 13.3% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **91** | **80.5%** of green rows |
| no red evidence | 13 | 11.5% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.2 min · sum 7.0 min · **ratio 3.22 → parallel** |
| reviewer round 2 | 4 reviewers · span 2.6 min · sum 8.8 min · **ratio 3.42 → parallel** |
| reviewer round 3 | 2 reviewers · span 3.0 min · sum 5.4 min · **ratio 1.81 → parallel** |
| reviewer round 4 | 1 reviewers · span 2.1 min · sum 2.1 min · **ratio 1.00 → SERIAL** |
| fix rounds | 3 · 19.9 min · 71,093 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 9 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/baseline/scorecard.json_
