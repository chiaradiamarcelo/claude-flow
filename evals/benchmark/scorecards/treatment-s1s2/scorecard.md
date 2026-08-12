# Scorecard — treatment-s1s2

- span **104 min** · agent time 111 min · dispatches 41 · output tokens 429,198
- scenarios 9 · **11.6 min/scenario** · 47,689 out-tok/scenario
- test rows 101 · **1.03 min/row** · 4,249 out-tok/row
- **API calls 669** (1,590 assistant log events, 2.38 per call) · cache-read 36,651,982 (**85x output**) · avg context/call 54,786
- tool calls 1,108 · **1.66 per API call** · calls carrying exactly one tool call 60%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 58.4 | 215,342 | 36 | 69,994 | 1.25 | 44,796 | 105,527 | 30% | 92 | 81 | claude-opus-5 | medium |
| test-designer | 9 | 18.4 | 72,781 | 8 | 39,417 | 1.68 | 36,624 | 0 | 100% | 0 | 79 | claude-opus-5 | medium |
| architect | 9 | 9.8 | 43,739 | 5 | 24,936 | 2.13 | 26,097 | 0 | 100% | 0 | 70 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 7.1 | 31,770 | 12 | 27,982 | 2.47 | 0 | 0 | — | 0 | 64 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 7.0 | 29,750 | 10 | 44,605 | 2.53 | 0 | 0 | — | 0 | 66 | claude-sonnet-5 | medium |
| arch-reviewer | 3 | 5.3 | 20,178 | 13 | 24,864 | 2.76 | 0 | 0 | — | 0 | 95 | claude-sonnet-5 | medium |
| refactor-advisor | 3 | 5.0 | 15,638 | 12 | 29,024 | 2.58 | 0 | 0 | — | 0 | 86 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 87 | 86.1% |
| early_green | 11 | 10.9% |
| deferred_blind | 0 | 0.0% |
| unplanned | 3 | 3.0% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **90** | **89.1%** of green rows |
| no red evidence | 0 | 0.0% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.3 min · sum 8.0 min · **ratio 3.42 → parallel** |
| reviewer round 2 | 4 reviewers · span 3.2 min · sum 9.0 min · **ratio 2.80 → parallel** |
| reviewer round 3 | 4 reviewers · span 3.0 min · sum 7.4 min · **ratio 2.44 → parallel** |
| fix rounds | 2 · 14.1 min · 46,589 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 18 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s1s2/scorecard.json_
