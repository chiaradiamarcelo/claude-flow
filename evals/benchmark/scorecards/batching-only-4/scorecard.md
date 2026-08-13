# Scorecard — batching-only-4

- span **103 min** · agent time 109 min · dispatches 37 · output tokens 451,859
- scenarios 9 · **11.4 min/scenario** · 50,207 out-tok/scenario
- test rows 89 · **1.15 min/row** · 5,077 out-tok/row
- **API calls 555** (1,507 assistant log events, 2.72 per call) · cache-read 32,607,867 (**72x output**) · avg context/call 58,753
- tool calls 1,069 · **1.93 per API call** · calls carrying exactly one tool call 50%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 54.8 | 226,561 | 27 | 75,651 | 1.57 | 35,866 | 121,533 | 23% | 75 | 90 | claude-opus-5 | medium |
| test-designer | 9 | 18.1 | 71,496 | 7 | 36,929 | 1.79 | 33,587 | 0 | 100% | 0 | 73 | claude-opus-5 | medium |
| architect | 9 | 12.3 | 55,445 | 6 | 26,107 | 2.17 | 22,960 | 0 | 100% | 0 | 74 | claude-sonnet-5 | medium |
| test-reviewer | 2 | 9.1 | 40,478 | 22 | 71,122 | 1.98 | 0 | 0 | — | 0 | 72 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 5.3 | 24,645 | 12 | 25,981 | 3.80 | 0 | 0 | — | 0 | 84 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 5.1 | 20,901 | 17 | 33,469 | 2.85 | 0 | 0 | — | 0 | 90 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 4.6 | 12,333 | 9 | 23,990 | 3.16 | 0 | 0 | — | 0 | 47 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 70 | 78.7% |
| early_green | 5 | 5.6% |
| deferred_blind | 0 | 0.0% |
| unplanned | 14 | 15.7% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **70** | **78.7%** of green rows |
| no red evidence | 14 | 15.7% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.3 min · sum 9.6 min · **ratio 2.86 → parallel** |
| reviewer round 2 | 4 reviewers · span 6.2 min · sum 14.6 min · **ratio 2.37 → partial** |
| fix rounds | 2 · 18.7 min · 73,013 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 10 |
| **plan staleness** (`> Stale plan:`) | **0** — plan-attributed 0, code-attributed 0, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/batching-only-4/scorecard.json_
