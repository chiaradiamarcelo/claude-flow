# Variance study — and the retraction of the headline

**4 runs per arm, `withdraw-money`, all eight green.** This was the round with the largest
single-run effect (−31% cost for inline), chosen deliberately: if the effect were real
anywhere, it would be here.

**It is not. The n=1 result does not replicate.** On cost, the sign flips between runs.

## Cost, effort, scope (n=4 each)

| axis | agents (sorted) | mean | inline (sorted) | mean | Δ | separates? |
|---|---|---|---|---|---|---|
| **cost $** | 4.34 4.46 5.84 6.01 | 5.16 | 4.08 4.84 6.42 7.33 | **5.67** | **+9.8%** | overlap |
| **wall s** | 557 585 733 1018 | 723 | 471 488 708 894 | 640 | −11.5% | overlap |
| **gradle runs** | 12 12 19 21 | 16.0 | 12 13 18 26 | 17.3 | +7.8% | overlap |
| **tests** | 18 20 21 22 | 20.3 | 23 24 25 26 | **24.5** | **+21%** | **DISJOINT** |
| **$/test** | .197 .248 .286 .292 | .256 | .170 .210 .247 .293 | .230 | −10.0% | overlap |

**Inline was more expensive on average, not cheaper.** Run 2 and run 3 both had inline
costing more than agents ($6.42 vs $5.84; $7.33 vs $6.01). The −31% from the original R1
was the luckiest draw in a wide, overlapping distribution — inline's cost range (4.08–7.33)
is *wider* than agents' (4.34–6.01).

## Quality (n=4 each)

| axis | agents | mean | inline | mean | Δ |
|---|---|---|---|---|---|
| **mutation killed %** | 76 81 81 82 | **80.0%** | 70 73 73 87 | 75.8% | **−4.2 pp** |
| CRAP mean | 1.27–1.33 | ~1.30 | 1.28–1.37 | ~1.31 | parity |
| CRAP methods >30 | 0 | 0 | 0 | 0 | parity |
| duplicated lines | 0 | 0 | 0 | 0 | parity |

The single-run R1 finding (inline 88% vs agents 62%) **also fails to replicate** — it
reversed. Over four runs the subagent arm has the higher mean kill rate and a much tighter
spread (76–82 vs 70–87).

`run2/inline` initially printed `(no report)`; the PIT report existed and was read directly
(13/15, 87%). A transient sidecar timing artifact, not a failed run.

## What actually survives

**One effect, and only one: the inline arm reliably writes ~21% more tests** (23–26 vs
18–22, fully disjoint across four runs each).

Those extra tests do **not** buy kill power — mutation rate is flat-to-slightly-worse. So
inline produces more test code and more production code of equivalent complexity and
duplication, with proportionally weaker discrimination per test. That is not a quality win;
at best it is neutral, at worst it is dilution.

## The arms were not model-matched (found after the fact)

Neither arm was given `--model`, so both defaulted to **Opus 5**. But the subagent arm's
`architect` carries `model: sonnet` in its own frontmatter, so **one phase of arm-agents ran
on Sonnet 5 while arm-inline did that same planning work on Opus 5.**

Pricing those Sonnet events at Opus rates (a *lower bound* — streaming under-reports output
tokens):

| | run1 | run2 | run3 | run4 | mean |
|---|---|---|---|---|---|
| understatement | $1.01 | $1.16 | $1.50 | $1.49 | **$1.29** |
| as % of that run | 22.5% | 19.8% | 25.0% | 34.4% | ~25% |

| cost $ | agents | inline | Δ |
|---|---|---|---|
| **as run** | 5.16 | 5.67 | **+9.8%** (inline worse) |
| **model-matched** | 6.45 | 5.67 | **−12.2%** (inline better) |

The ranges still overlap heavily either way ([5.46–7.51] vs [4.08–7.33]), so **"no reliable
cost difference" survives** — but the *direction* of the mean flips, and the original
"+9.8% worse" should not be quoted without this caveat.

**Two defensible framings, and they disagree:**

1. **Topology-only.** A clean test needs the architect on Opus in both arms. Not run;
   estimated above at inline ≈ −12%.
2. **As-deployed.** The subagent topology *can* route a cheap phase to a cheap model, and a
   single inline session structurally cannot — it is one session on one model. On that
   reading the Sonnet architect is not a confound at all but a **real advantage of the
   topology**, and the as-run numbers are the honest ones.

Framing 2 is arguably the more useful one for the actual decision, and it is the framing
under which the subagent arm is cheaper.

**The quality result is unaffected, and if anything strengthened:** arm-agents achieved the
higher mutation kill rate (80.0% vs 75.8%) *while* running its planning phase on the cheaper
model.

## Verdict

**No case for switching to the inline pipeline.** Cost, wall-clock, suite runs and code
quality are indistinguishable between the topologies at n=4 — on cost the mean direction
depends on whether you model-match the arms (see above), and the ranges overlap either way. The only reliable difference
favours neither: more tests of lower average yield.

This also **retracts the combined 3-round headline in `RESULTS.md`** (−21% cost, mutation
73%→85%). Both were single-run artifacts of a high-variance process. The 3-round table
stands as recorded data; its interpretation does not.

## The methodological lesson

The prior experiment's variance study already warned this would happen — it found that
cost and turns separated only at n=4 and that wall-clock *overlapped*. This study ran the
same instrument against a different treatment and reproduced that warning exactly: **a
single run per cell on this pipeline cannot distinguish a 30% effect from noise.** Any
future pipeline A/B here should budget n=4 per cell from the start, or not bother running.

The value of the ~$70 spent: a plausible, well-motivated change that looked like a 21% cost
win at n=1 is now known not to be one, before it was promoted into the standing pipeline.
