# Scorecard — treatment-s1s2

- span **104 min** · agent time 111 min · dispatches 41 · output tokens 440,250
- scenarios 9 · **11.6 min/scenario** · 48,917 out-tok/scenario
- test rows 101 · **1.03 min/row** · 4,359 out-tok/row

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 58.4 | 218,709 | 19,882 | 44,796 | 105,527 | 30% | 92 | 81 | claude-opus-5 | medium |
| test-designer | 9 | 18.4 | 74,846 | 8,316 | 36,624 | 0 | 100% | 0 | 79 | claude-opus-5 | medium |
| architect | 9 | 9.8 | 45,377 | 5,041 | 26,097 | 0 | 100% | 0 | 70 | claude-sonnet-5 | medium |
| api-reviewer | 3 | 7.1 | 32,505 | 10,835 | 0 | 0 | — | 0 | 64 | claude-sonnet-5 | medium |
| test-reviewer | 3 | 7.0 | 30,789 | 10,263 | 0 | 0 | — | 0 | 66 | claude-sonnet-5 | medium |
| arch-reviewer | 3 | 5.3 | 21,160 | 7,053 | 0 | 0 | — | 0 | 95 | claude-sonnet-5 | medium |
| refactor-advisor | 3 | 5.0 | 16,864 | 5,621 | 0 | 0 | — | 0 | 86 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 87 | 86.1% |
| early_green | 11 | 10.9% |
| deferred_blind | 0 | 0.0% |
| unplanned | 3 | 3.0% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |

> `unclassified` is free-text Status cells the parser could not classify. Mandating a status vocabulary in the developer prompt drives this to 0 for future runs.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 2.3 min · sum 8.0 min · **ratio 3.42 → parallel** |
| reviewer round 2 | 4 reviewers · span 3.2 min · sum 9.0 min · **ratio 2.80 → parallel** |
| reviewer round 3 | 4 reviewers · span 3.0 min · sum 7.4 min · **ratio 2.44 → parallel** |
| fix rounds | 2 · 14.1 min · 46,932 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 18 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s1s2/scorecard.json_
