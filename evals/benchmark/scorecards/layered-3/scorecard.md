# Scorecard — layered-3

- span **103 min** · agent time 166 min · dispatches 17 · output tokens 412,250
- scenarios 9 · **11.5 min/scenario** · 45,806 out-tok/scenario

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 6 | 57.9 | 231,511 | 38,585 | 18,571 | 132,879 | 12% | 103 | 67 | claude-opus-5 | medium |
| test-designer | 4 | 26.8 | 96,719 | 24,179 | 67,064 | 0 | 100% | 0 | 42 | claude-opus-5 | medium |
| system-architect | 1 | 70.0 | 33,153 | 33,153 | 33,335 | 0 | 100% | 0 | 15 | claude-opus-5 | medium |
| test-reviewer | 2 | 4.8 | 19,257 | 9,628 | 0 | 0 | — | 0 | 48 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.5 | 17,351 | 8,675 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| api-reviewer | 1 | 1.9 | 8,269 | 8,269 | 0 | 0 | — | 0 | 28 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 1.4 | 5,990 | 5,990 | 0 | 0 | — | 0 | 42 | claude-sonnet-5 | medium |

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.0 min · sum 7.8 min · **ratio 2.57 → parallel** |
| reviewer round 2 | 2 reviewers · span 2.1 min · sum 3.8 min · **ratio 1.80 → parallel** |
| fix rounds | 2 · 11.9 min · 37,795 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 0 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-3/scorecard.json_
