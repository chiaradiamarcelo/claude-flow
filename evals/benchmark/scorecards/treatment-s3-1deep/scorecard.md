# Scorecard — treatment-s3-1deep

- span **106 min** · agent time 123 min · dispatches 37 · output tokens 450,950
- scenarios 9 · **11.8 min/scenario** · 50,106 out-tok/scenario
- test rows 127 · **0.84 min/row** · 3,551 out-tok/row
- **API calls 716** (1,600 assistant log events, 2.23 per call) · cache-read 47,086,090 (**104x output**) · avg context/call 65,763
- tool calls 1,113 · **1.55 per API call** · calls carrying exactly one tool call 67%

## Cost by role

| role | disp | min | out tok | api/disp | ctx/call | tool/call | md chars | code chars | md share | builds | reads | model | effort |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| developer | 11 | 73.5 | 285,079 | 43 | 80,723 | 1.23 | 60,779 | 139,159 | 30% | 104 | 126 | claude-opus-5 | medium |
| test-designer | 9 | 19.7 | 65,819 | 8 | 39,321 | 1.95 | 36,438 | 0 | 100% | 0 | 111 | claude-opus-5 | medium |
| architect | 9 | 11.4 | 32,144 | 5 | 26,508 | 2.00 | 23,211 | 0 | 100% | 0 | 64 | claude-sonnet-5 | medium |
| test-reviewer | 2 | 5.3 | 21,223 | 13 | 48,311 | 1.96 | 0 | 0 | — | 0 | 39 | claude-sonnet-5 | medium |
| refactor-advisor | 2 | 6.0 | 20,144 | 17 | 39,036 | 2.71 | 0 | 0 | — | 0 | 80 | claude-sonnet-5 | medium |
| api-reviewer | 2 | 3.2 | 14,678 | 8 | 18,789 | 3.00 | 0 | 0 | — | 0 | 32 | claude-sonnet-5 | medium |
| arch-reviewer | 2 | 3.3 | 11,863 | 12 | 27,171 | 2.64 | 0 | 0 | — | 0 | 59 | claude-sonnet-5 | medium |

## Row-level quality (normalised)

| metric | count | rate |
|---|---|---|
| red_then_green | 78 | 61.4% |
| early_green | 18 | 14.2% |
| deferred_blind | 0 | 0.0% |
| unplanned | 31 | 24.4% |
| unclassified | 0 | 0.0% |
| open | 0 | 0.0% |
| **red arrival** (all ✅, incl. unplanned) | **86** | **67.7%** of green rows |
| no red evidence | 23 | 18.1% of green rows |

> The first block is **provenance**; `red arrival` is the **independent** test-strength axis and is the one to compare across arms. `red_then_green` excludes unplanned rows by construction, so an arm that adds many unplanned rows scores low on it while being stronger. `unclassified` is Status cells outside the mandated vocabulary.

## Stage 1 metrics (reviewer gate · batching · commits)

| metric | value |
|---|---|
| reviewer round 1 | 4 reviewers · span 3.2 min · sum 8.9 min · **ratio 2.82 → parallel** |
| reviewer round 2 | 4 reviewers · span 3.2 min · sum 8.9 min · **ratio 2.77 → parallel** |
| fix rounds | 2 · 21.0 min · 79,050 out tok |
| git commits during run | 0 |
| catches (`> Note to architect:`) | 21 |
| **plan staleness** (`> Stale plan:`) | **13** — plan-attributed 5, code-attributed 8, unattributed 0 |

> ratio = sum(durations)/span. 1.0 means the reviewers ran one after another; n means all n went out in a single message, as `/run-reviewers` requires.

_wrote /Users/mchiaradia/.claude/evals/benchmark/scorecards/treatment-s3-1deep/scorecard.json_
