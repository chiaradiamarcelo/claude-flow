# Round 4 — repeated-run variance study

**Question the n=3 result left open:** is the batch advantage larger than run-to-run noise, or
could an unlucky run erase it? To find out, the same scenario (`account-overview`, the cheapest,
round 3) was run **4 times per arm** — identical plan, prompt, neutral dir — measuring only the
developer-phase cost/effort metrics (quality parity is already established; no oracles/reviewers
here). Run 1 of each arm is the round-3 run; runs 2–4 are fresh sequential dispatches
(`round4-variance/{strict,batch}/run*.json`). All 8 runs finished green, no errors.

## Result

| Metric | Strict mean±std (min–max) | Batch mean±std (min–max) | Δmean | ranges disjoint? |
|---|---|---|--:|---|
| **Gradle runs** | 19±2 (18–22) | 8±1 (7–10) | **−57%** | **YES** |
| Cost (USD) | 3.72±0.29 (3.36–4.15) | 2.48±0.46 (2.11–3.27) | −33% | **YES** (by $0.09) |
| Turns | 79±4 (72–84) | 58±7 (54–70) | −26% | **YES** |
| Output tokens | 25,657±2,925 (21,606–28,879) | 21,213±4,794 (18,243–29,509) | −17% | **no** (overlap) |
| Wall-clock (s) | 451±40 (385–493) | 343±116 (245–538) | −24% | **no** (overlap) |

("disjoint" = the arms' [min,max] ranges don't overlap → the batch advantage exceeds *all*
observed run-to-run noise on that metric.)

## Interpretation

- **The mechanism is bulletproof.** Gradle-run counts are completely disjoint (strict 18–22,
  batch 7–10) with tiny variance — batch runs the test suite ~⅓ as often, every time. This is the
  causal core of the whole effect and it does not depend on luck.
- **Cost and turns still separate at n=4** — every batch run was cheaper and shorter than every
  strict run — but the cost margin is thinner than the n=3 headline suggested (−33% here), and one
  batch run came within **$0.09** of the cheapest strict run.
- **Tokens and wall-clock do NOT cleanly separate.** Batch has **fatter tails**: its token std is
  ~1.6× strict's, and one batch run ballooned to 29,509 tokens / 538 s — as much as, or more than,
  a typical strict run. Batch is cheaper *on average* but less predictable.

## Revised claim

The batch advantage is **real and directionally robust**, but its size should be stated as a
**central tendency, not a floor**:

- **Robust (noise-free):** batch runs the test suite far less often (~⅓), and is cheaper and
  shorter on every observed run. This alone is a strong reason to prefer it.
- **On-average (with variance):** the "≈half the cost / tokens" figure is a mean. Batch's
  occasional expensive run can approach a strict run's cost, so treat ~30–50% savings as the
  expected value, not a guarantee.

This *strengthens* the case for promoting batch-per-class (the win survives run-to-run noise on
the decision-relevant axes) while correctly deflating the magnitude: sell it as "fewer test runs,
cheaper on average," not "always half price."
