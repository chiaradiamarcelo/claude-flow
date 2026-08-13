# Scorecard — gym-walls (Android/KMP, baseline config, 2026-08-07)

- span **309 min** · agent time 282 min · dispatches 51 · output tokens 1,014,690
- scenarios 13 · **23.7 min/scenario** · 78,053 out-tok/scenario
- test rows 95 · **3.25 min/row** · 10,681 out-tok/row

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 15 | 147.2 | 446,060 | 29,737 | 84,400 | 275,585 | 23% | 151 | 253 | claude-opus-5 | medium |
| test-designer | 13 | 81.7 | 308,871 | 23,759 | 321,479 | 0 | 100% | 0 | 206 | claude-opus-5 | medium |
| architect | 13 | 33.7 | 169,411 | 13,031 | 147,689 | 0 | 100% | 0 | 189 | claude-sonnet-5 | medium |
| android-ui-test-reviewer | 2 | 4.7 | 23,664 | 11,832 | 0 | 0 | — | 0 | 40 | claude-sonnet-5 | medium |
| android-presentation-reviewer | 2 | 4.0 | 18,513 | 9,256 | 0 | 0 | — | 0 | 55 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.2 | 13,604 | 6,802 | 0 | 0 | — | 0 | 47 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 2.8 | 12,924 | 6,462 | 0 | 0 | — | 0 | 35 | claude-sonnet-5 | medium |
| test-reviewer | 1 | 2.7 | 11,964 | 11,964 | 0 | 0 | — | 0 | 29 | claude-sonnet-5 | medium |
| general-purpose | 1 | 2.5 | 9,679 | 9,679 | 0 | 0 | — | 0 | 7 | claude-opus-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 30 | 31.6% |
| early_green | 9 | 9.5% |
| deferred_blind | 21 | 22.1% |
| unplanned | 0 | 0.0% |
| unclassified | 35 | 36.8% |
| open | 0 | 0.0% |

> `unclassified` is free-text Status cells the parser could not classify. Mandating a status vocabulary in the developer prompt drives this to 0 for future runs.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 5 reviewers · span 12.7 min · sum 11.1 min · **ratio 0.88 → SERIAL** |
| reviewer round 2 | 4 reviewers · span 7.4 min · sum 6.3 min · **ratio 0.85 → SERIAL** |
| fix rounds | 2 · 24.4 min · 81,244 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 40 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote evals/scorecard/baseline-gym-walls.json_
