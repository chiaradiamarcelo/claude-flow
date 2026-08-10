# Scorecard — layered-seq

- span **74 min** · agent time 73 min · dispatches 13 · output tokens 284,149
- scenarios 9 · **8.2 min/scenario** · 31,572 out-tok/scenario

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 4 | 44.6 | 157,966 | 39,491 | 29,877 | 125,753 | 19% | 63 | 20 | claude-opus-5 | medium |
| test-designer | 4 | 17.4 | 75,297 | 18,824 | 46,733 | 0 | 100% | 0 | 38 | claude-opus-5 | medium |
| arch-reviewer | 1 | 2.9 | 12,712 | 12,712 | 0 | 0 | — | 0 | 46 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 2.3 | 11,051 | 11,051 | 0 | 0 | — | 0 | 42 | claude-sonnet-5 | medium |
| test-reviewer | 1 | 2.1 | 10,964 | 10,964 | 0 | 0 | — | 0 | 31 | claude-sonnet-5 | medium |
| system-architect | 1 | 2.2 | 10,500 | 10,500 | 13,696 | 0 | 100% | 0 | 1 | claude-opus-5 | medium |
| api-reviewer | 1 | 1.4 | 5,659 | 5,659 | 0 | 0 | — | 0 | 25 | claude-sonnet-5 | medium |

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.9 min · sum 8.7 min · **ratio 2.98 → parallel** |
| fix rounds | 0 · 0.0 min · 0 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 0 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-seq/scorecard.json_
