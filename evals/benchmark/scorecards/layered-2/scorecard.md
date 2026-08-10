# Scorecard — layered-2

- span **103 min** · agent time 103 min · dispatches 15 · output tokens 364,545
- scenarios 9 · **11.5 min/scenario** · 40,505 out-tok/scenario

## Cost by role

| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 6 | 72.6 | 252,539 | 42,089 | 25,164 | 141,729 | 15% | 118 | 41 | claude-opus-5 | medium |
| test-designer | 4 | 15.8 | 53,550 | 13,387 | 45,259 | 0 | 100% | 0 | 39 | claude-opus-5 | medium |
| test-reviewer | 1 | 4.0 | 16,224 | 16,224 | 0 | 0 | — | 0 | 31 | claude-sonnet-5 | medium |
| system-architect | 1 | 3.0 | 14,161 | 14,161 | 14,772 | 0 | 100% | 0 | 1 | claude-opus-5 | medium |
| api-reviewer | 1 | 2.4 | 11,051 | 11,051 | 0 | 0 | — | 0 | 26 | claude-sonnet-5 | medium |
| refactor-advisor | 1 | 2.8 | 8,805 | 8,805 | 0 | 0 | — | 0 | 44 | claude-sonnet-5 | medium |
| arch-reviewer | 1 | 2.3 | 8,215 | 8,215 | 0 | 0 | — | 0 | 58 | claude-sonnet-5 | medium |

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 4.0 min · sum 11.4 min · **ratio 2.85 → parallel** |
| fix rounds | 2 · 22.2 min · 67,601 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 0 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/layered-2/scorecard.json_
