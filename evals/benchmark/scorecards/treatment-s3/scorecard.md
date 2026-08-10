# Scorecard — treatment-s3

- span **75 min** · agent time 103 min · dispatches 39 · output tokens 414,457
- scenarios 9 · **8.4 min/scenario** · 46,051 out-tok/scenario
- test rows 89 · **0.85 min/row** · 4,657 out-tok/row

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 60.5 | 222,671 | 20,242 | 65,097 | 120,899 | 35% | 79 | 136 | claude-opus-5 | medium |
| test-designer | 9 | 15.7 | 62,865 | 6,985 | 29,446 | 0 | 100% | 0 | 64 | claude-opus-5 | medium |
| architect | 9 | 8.0 | 35,453 | 3,939 | 20,033 | 0 | 100% | 0 | 50 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 4.6 | 27,997 | 9,332 | 0 | 0 | — | 0 | 69 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 5.8 | 25,610 | 8,536 | 0 | 0 | — | 0 | 67 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 5.0 | 21,949 | 10,974 | 0 | 0 | — | 0 | 95 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.8 | 17,912 | 8,956 | 0 | 0 | — | 0 | 79 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 57 | 64.0% |
| early_green | 7 | 7.9% |
| deferred_blind | 0 | 0.0% |
| unplanned | 25 | 28.1% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |

> `unclassified` is free-text Status cells the parser could not classify. Mandating a status vocabulary in the developer prompt drives this to 0 for future runs.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.6 min · sum 8.3 min · **ratio 3.18 → parallel** |
| reviewer round 2 | 4 reviewers · span 2.5 min · sum 7.7 min · **ratio 3.08 → parallel** |
| reviewer round 3 | 2 reviewers · span 2.2 min · sum 3.2 min · **ratio 1.46 → SERIAL** |
| fix rounds | 2 · 16.1 min · 68,219 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 8 |
| **plan staleness** (`> Stale plan:`) | **10** — plan-attributed 1, code-attributed 4, unattributed 5 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s3/scorecard.json_
