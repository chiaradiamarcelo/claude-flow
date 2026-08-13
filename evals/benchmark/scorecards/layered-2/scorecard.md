# Scorecard — layered-2

- span **103 min** · agent time 103 min · dispatches 15 · output tokens 356,013
- scenarios 9 · **11.5 min/scenario** · 39,557 out-tok/scenario
- test rows 126 · **0.82 min/row** · 2,826 out-tok/row
- **API calls 493** (1,049 assistant log events, 2.13 per call) · cache-read 45,544,311 (**128x output**) · avg context/call 92,382
- tool calls 717 · **1.45 per API call** · calls carrying exactly one tool call 76%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 6 | 72.6 | 246,757 | 67 | 103,599 | 1.17 | 25,164 | 141,729 | 15% | 118 | 41 | claude-opus-5 | medium |
| test-designer | 4 | 15.8 | 52,211 | 7 | 46,942 | 1.90 | 45,259 | 0 | 100% | 0 | 39 | claude-opus-5 | medium |
| test-reviewer | 1 | 4.0 | 15,987 | 13 | 45,748 | 2.77 | 0 | 0 | — | 0 | 31 | claude-sonnet-5 | medium |
| system-architect | 1 | 3.0 | 14,139 | 6 | 22,926 | 1.00 | 14,772 | 0 | 100% | 0 | 1 | claude-opus-5 | medium |
| api-reviewer | 1 | 2.4 | 10,671 | 10 | 31,591 | 3.00 | 0 | 0 | — | 0 | 26 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 2.8 | 8,675 | 11 | 32,044 | 4.18 | 0 | 0 | — | 0 | 44 | claude-sonnet-5 | medium |
| arch-reviewer | 1 | 2.3 | 7,573 | 16 | 35,638 | 4.12 | 0 | 0 | — | 0 | 58 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 90 | 71.4% |
| early_green | 18 | 14.3% |
| deferred_blind | 0 | 0.0% |
| unplanned | 18 | 14.3% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **102** | **81.0%** of green rows |
| no red evidence | 6 | 4.8% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 4.0 min · sum 11.4 min · **ratio 2.85 → parallel** |
| fix rounds | 2 · 22.2 min · 63,950 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 10 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-2/scorecard.json_
