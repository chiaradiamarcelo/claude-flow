# Results — subagent pipeline vs inline pipeline

**n = 1 run per arm per round, 3 rounds.** All six arms finished green.
Total spend: **$25.11** on the arms, $7.31 on the post-hoc reviewer pass, ~$0.60 on
instrument spikes.

## Headline

Across the three rounds combined, the inline arm cost **−21%**, finished **−28%** faster,
and delivered **+28% more tests**. Normalised for the scope difference, it cost **−38% per
test delivered**.

**But the effect is not uniform, and the design does not support a general claim.** It is
large on the first write-side round, halves on the second, and all but vanishes on the
read-side round — where the inline arm was actually *worse* on suite runs. See *What this
does not establish*.

## Cost and effort

| Round | Arm | Cost | Wall | Gradle runs | Plan rows | Tests | $/test |
|---|---|---|---|---|---|---|---|
| withdraw-money (write) | agents | $5.13 | 731s | 14 | 12 | 12 | $0.427 |
| withdraw-money | **inline** | **$3.52** | **407s** | **10** | 22 | 21 | **$0.168** |
| deposit-money (write) | agents | $5.26 | 639s | 14 | 16 | 17 | $0.309 |
| deposit-money | **inline** | **$4.15** | **512s** | **11** | 21 | 20 | **$0.208** |
| account-overview (read) | agents | $3.62 | 444s | **9** | 9 | 10 | **$0.362** |
| account-overview | **inline** | **$3.43** | **389s** | 12 | 8 | 9 | $0.381 |
| **combined** | agents | $14.01 | 1814s | 37 | 37 | 39 | $0.359 |
| **combined** | **inline** | **$11.10** | **1308s** | **33** | 51 | 50 | **$0.222** |

Per-round deltas (inline vs agents):

| Round | cost | wall | gradle runs | tests |
|---|---|---|---|---|
| R1 withdraw (write) | **−31%** | **−44%** | −29% | +75% |
| R2 deposit (write) | **−21%** | −20% | −21% | +18% |
| R3 account-overview (read) | −5% | −12% | **+33%** | −10% |

The gradient is the most informative thing here: the advantage tracks how much
**authoring** the round demands, and collapses on the round that demands least.

## Quality

| Round | Arm | Mutation | CRAP mean | CRAP >30 | Duplication | Build |
|---|---|---|---|---|---|---|
| withdraw-money | agents | 5/8 (62%) | 1.16 | 0 | 0 | green |
| withdraw-money | **inline** | **14/16 (88%)** | 1.29 | 0 | 0 | green |
| deposit-money | agents | 8/11 (73%) | 1.23 | 0 | 0 | green |
| deposit-money | **inline** | 9/12 (75%) | 1.21 | 0 | 0 | green |
| account-overview | agents | 3/3 (100%) | 1.24 | 0 | 0 | green |
| account-overview | **inline** | 5/5 (100%) | 1.30 | 0 | 0 | green |
| combined | agents | 16/22 (73%) | — | 0 | 0 | 3/3 green |
| combined | **inline** | **28/33 (85%)** | — | 0 | 0 | 3/3 green |

- **CRAP and DRY are at parity** — every method under the threshold in both arms, zero
  duplicated blocks anywhere. Neither topology produced risk-shaped code.
- **Mutation favours inline**, and it is not purely a volume effect: the inline arm both
  raised the mutant count (more production logic reachable by the framework-free sidecar)
  and killed a higher *fraction* of it. Its extra tests were carrying discriminating power,
  not padding.
- **But the denominators are tiny** (3–16 mutants per arm). R1's 62% vs 88% is 5/8 against
  14/16. Kotlin's synthetic bytecode makes absolute scores noisy; the delta cancels
  systematic noise, but it cannot carry much weight at this n.

## Scope was not held equal

The arms were given identical specifications and produced **materially different amounts of
work** — most starkly in R1, where inline planned 22 rows to agents' 12. So "inline is
cheaper" and "inline does more" are entangled, and the raw cost delta understates the
efficiency gap while overstating the like-for-like saving. **$/test is the fairer axis**;
it is also the one most vulnerable to a test-granularity difference, so treat it as
indicative.

Plan↔code fidelity held in both arms (agents 12 rows / 12 tests; inline 22 rows / 21 tests,
one row short).

## Reviewer axis: partial, not comparable

**2 of 6 reviewer runs did not produce a verdict** — `deposit-money/inline` and
`account-overview/agents` both ended with the orchestrator saying reviewers were still
running in the background when the `-p` session terminated. The four that completed found
issues of similar character in both arms (boundary status-code mapping, fixture defaults
hiding a Given, a derived field in a read model).

With two holes and a known flip-direction noise floor from the prior experiment, **this
axis is reported as inconclusive** rather than scored.

## Instrument note — the measurement was nearly rigged

A $0.21 spike before any paid run established that `result.usage` counts the **main loop
only**, while `result.total_cost_usd` rolls subagents up. Scoring this experiment with the
prior experiment's `metrics.py` would have hidden most of the subagent arm's spend — the
topology under test would have measured as nearly free, and the inline arm would have
looked *worse*. `oracle/metrics2.py` sums per-origin via `parent_tool_use_id` and takes
cost from the result event. Per-event `output_tokens` is under-reported (streaming
partials), so token counts are used for **attribution only**, never as spend.

## What this does not establish

1. **n = 1 per cell.** The prior experiment's variance study (4 runs/arm) found that
   cost and turns separated only at n=4, while tokens and wall-clock **overlapped** between
   arms. A −21% combined cost delta from single runs is suggestive, not established.
2. **The read-side round is near-parity**, and its Gradle runs went the *wrong* way
   (+33%). Any claim should be scoped to authoring-heavy work.
3. **Scope differed**, so the cost comparison is not like-for-like (above).
4. **Review was excluded from the measured run** by design, and the post-hoc pass is
   incomplete. If subagent review is where the topology earns its keep, this experiment
   cannot see it.
5. **Only the topology variable was tested.** The three other differences bundled into the
   `rafa-*` variant were deliberately pinned out and remain untested.

## Recommendation

**Do not promote inline into the standing pipeline on this evidence.** The direction is
consistent and quality never regressed, which is enough to justify the next step — not
enough to move `main`.

Next, in order:

1. **Variance study** on `withdraw-money` (the round with the largest effect), 4 runs per
   arm, mirroring the prior experiment's R4. That is what turns this into a claim.
2. **Fix the reviewer harness** so the `-p` session waits for dispatched reviewers before
   terminating — that bug will bite any future experiment that scores review.
3. **Then the other three variables**, one experiment each: all-scenarios-in-one-pass
   planning, `one-shot` granularity, and the deterministic inventory script. The inventory
   script in particular is cheap, deterministic and independently attractive.

One incidental finding worth fixing regardless: the subagent arm named a Kotlin file
`AccountJpaAdapter.integration.spec.kt`, leaking a `.spec.ts` convention into a Kotlin
repo. The inline arm named it `AccountJpaAdapterIT.kt` correctly.
