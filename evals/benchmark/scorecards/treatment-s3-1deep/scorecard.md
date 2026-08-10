# Scorecard — treatment-s3-1deep

- span **106 min** · agent time 123 min · dispatches 37 · output tokens 465,913
- scenarios 9 · **11.8 min/scenario** · 51,768 out-tok/scenario
- test rows 127 · **0.84 min/row** · 3,669 out-tok/row

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 73.5 | 288,473 | 26,224 | 60,779 | 139,159 | 30% | 104 | 126 | claude-opus-5 | medium |
| test-designer | 9 | 19.7 | 71,817 | 7,979 | 36,438 | 0 | 100% | 0 | 111 | claude-opus-5 | medium |
| architect | 9 | 11.4 | 33,725 | 3,747 | 23,211 | 0 | 100% | 0 | 64 | claude-sonnet-5 | medium |
| test-reviewer | 2 | 5.3 | 23,442 | 11,721 | 0 | 0 | — | 0 | 39 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 6.0 | 21,221 | 10,610 | 0 | 0 | — | 0 | 80 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 3.2 | 15,102 | 7,551 | 0 | 0 | — | 0 | 32 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.3 | 12,133 | 6,066 | 0 | 0 | — | 0 | 59 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 78 | 61.4% |
| early_green | 18 | 14.2% |
| deferred_blind | 0 | 0.0% |
| unplanned | 31 | 24.4% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |

> `unclassified` is free-text Status cells the parser could not classify. Mandating a status vocabulary in the developer prompt drives this to 0 for future runs.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.2 min · sum 8.9 min · **ratio 2.82 → parallel** |
| reviewer round 2 | 4 reviewers · span 3.2 min · sum 8.9 min · **ratio 2.77 → parallel** |
| fix rounds | 2 · 21.0 min · 79,585 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 21 |
| **plan staleness** (`> Stale plan:`) | **13** — plan-attributed 5, code-attributed 8, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s3-1deep/scorecard.json_
