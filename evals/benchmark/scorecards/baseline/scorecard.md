# Scorecard — baseline

- span **127 min** · agent time 134 min · dispatches 41 · output tokens 633,728
- scenarios 9 · **14.1 min/scenario** · 70,414 out-tok/scenario
- test rows 113 · **1.12 min/row** · 5,608 out-tok/row

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 12 | 67.6 | 266,732 | 22,227 | 41,105 | 136,752 | 23% | 114 | 96 | claude-opus-5 | medium |
| test-designer | 9 | 27.9 | 151,833 | 16,870 | 106,081 | 0 | 100% | 0 | 66 | claude-opus-5 | medium |
| architect | 9 | 15.0 | 98,949 | 10,994 | 47,568 | 0 | 100% | 0 | 95 | claude-sonnet-5 | medium |
| refactor-advisor | 4 | 8.4 | 39,085 | 9,771 | 0 | 0 | — | 0 | 190 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 7.4 | 36,612 | 12,204 | 0 | 0 | — | 0 | 103 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.9 | 21,567 | 10,783 | 0 | 0 | — | 0 | 82 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 3.6 | 18,950 | 9,475 | 0 | 0 | — | 0 | 50 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 89 | 78.8% |
| early_green | 9 | 8.0% |
| deferred_blind | 0 | 0.0% |
| unplanned | 15 | 13.3% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |

> `unclassified` is free-text Status cells the parser could not classify. Mandating a status vocabulary in the developer prompt drives this to 0 for future runs.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 11 reviewers · span 31.1 min · sum 23.3 min · **ratio 0.75 → SERIAL** |
| fix rounds | 3 · 19.9 min · 72,932 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 9 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote scorecards/baseline/scorecard.json_
