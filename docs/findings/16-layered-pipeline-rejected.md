# Finding 16 — The layered pipeline is rejected; its specification review is kept

**Date:** 2026-08 · **Area:** `commands/run-pipeline-layered` (rejected), `agents/system-architect` (rejected), `commands/intent-and-goal` Phase 2 gap check (adopted as a step)
**Status:** decided on four arms. `/run-pipeline` remains the pipeline. Continues
[finding 15](15-pipeline-cost-stage-1-and-2.md); the experimental method is
[finding 13](13-batch-vs-strict-tdd.md)'s and the mutation oracle is
[finding 14](14-mutation-gate-spike.md)'s.

---

## TL;DR

We forked the pipeline to change the unit of work from the **scenario** to the
**layer**: one whole-feature design pass up front, then test-design and implement layer
by layer. The hypothesis was that coarser batches would be cheaper and would open the
door to parallel workers.

**Rejected.** Across three arms it saved ~10% wall-clock and 20% tokens, and cost **2.3
candidate-real mutation survivors on average against the adopted config's 0**, with test
strength that swung wildly run to run.

**One piece is kept and is worth more than the thing it came from.** The global design
agent, asked to check each business rule for a scenario that would falsify it, found an
undriven uniqueness invariant that had silently produced a data-destroying defect in
**all four** previous arms. It cost 2.2 minutes and 10,500 tokens. That review is now a
phase of `/intent-and-goal`. It was first extracted into a `spec-gap-reviewer` agent;
that agent was later **dropped** and the review kept as an instruction — see §3.

---

## 1. The results

| arm | span | out-tok | rows | red arrival | unplanned | catches | **mut-real** |
|---|---|---|---|---|---|---|---|
| **s1s2 (adopted)** | 104 | 429,198 | 101 | 89.1% | 3.0% | 18 | **0** |
| layered-1 | **74** | 280,012 | 116 | 83.6% | 0.9% | 11 | 1 |
| layered-2 | 103 | 356,013 | 126 | **81.0%** | **14.3%** | 10 | **4** |
| layered-3 | 103 | 401,981 | 157 | 93.6% | 4.5% | 6 | 2 |

> **Corrected 2026-08-12.** Output tokens were per-log-event, not per-API-request (see
> [finding 15](15-pipeline-cost-stage-1-and-2.md)). The test-strength column was
> `red_then_green`, which a classifier bug made **exclusive** with `unplanned` — so an
> arm that added unplanned rows was docked for it even when those rows had genuinely
> gone red first. It is now **red arrival**, counted across all green rows from the
> failure evidence in each Status cell. Layered-2's figure rises 71.4% → 81.0%, which
> softens the instability argument; the mutation column, which is the actual grounds for
> rejection, is untouched.

Layered spans **74, 103, 103** — mean 93 against 104. The two confirmation arms finished
**19 seconds apart** (105m28s and 105m47s), which makes 74 the outlier.

Tokens are a real win: mean 346,002 vs 429,198, **−19%**, consistent in direction across
all three arms.

## 2. Why it was rejected

**Candidate-real mutation survivors: 1, 4, 2 — mean 2.3, against 0.** Worse in every
arm, and layered-2's four are not boilerplate:

- `TransferMoneyUseCase.settleWithinOneAccount` — two survivors including a
  `VoidMethodCallMutator`: a call can be deleted from the same-account transfer path and
  no test notices.
- `AccountNumber.constructor-impl` survives in **two** arms — the validation guard is
  unprotected.
- A comparator survivor on the statement-ordering tie-break.

This is the predicted mechanism, confirmed. Finding 14's justification for *not* gating
on mutation was precisely that the test-designer's **per-scenario** mutation reasoning
made the gate redundant. Coarsen that reasoning to per-layer and the justification goes
with it.

Test strength is also unstable in a way the adopted config is not: red arrival 81.0% →
93.6%, unplanned 0.9% → 14.3%, catches sliding 11 → 10 → 6 against 18. (The red-arrival
spread is narrower than first reported — see the correction above — so **the mutation
column carries this rejection almost alone.** Stated plainly because it is the weaker
version of the argument.)

The fork would only be adoptable **with** a mutation gate feeding the fix loop — which is
swarm-forge's bargain (generated tests plus measured falsifiability, instead of designed
falsifiability), and a bigger build than the thing it was meant to speed up.

## 3. What is kept, and why it is the better half

`system-architect`'s mandatory `## Specification Gaps` section, given only the frozen
9-scenario spec and no hint about what to look for, reported:

- **Rule 1 (unique account numbers).** *"SCENARIO-01 presupposes the account is absent,
  so nothing exercises the collision. An implementation that overwrites the existing
  account on a second open — destroying its movements — passes all nine scenarios."*
  The baseline arm's reviewers found this only after burning all three fix rounds, and
  then ran out of budget.

  > **Corrected 2026-08-12.** This originally read "the exact defect all four earlier
  > arms shipped." Checked directly against every arm's source: the guard is **absent in
  > two of eight** — `baseline` and `treatment-s1s2` — and **present in the other six**,
  > including both Stage 3 arms and all three layered arms. So the pipeline usually
  > guards the rule unprompted; it is the **adopted config** that happens not to, which
  > is worse news than the original claim, not better. The gap in the *specification* is
  > real and unchanged — no scenario drives the rule — which is why the review is still
  > worth its two minutes; but it is a coin-flip defect, not a universal one.
- **Rule 8 (a failed store is reported and applies nothing).** The spec's own notes claim
  the refusal scenarios carry it. They don't: scenarios 03 and 05 are refused *before* any
  store is attempted, so no scenario ever reaches a failing store.
- **Rule 5's atomicity half.** SCENARIO-06's third `Then` pins identity but only the happy
  path; two sequential saves pass it.

Plus five ambiguities (how a legacy row is recognised, refusal status codes, ordering ties,
money precision, whether a legacy record blocks reuse of its number).

Two of those three gaps were in a specification **I wrote and reviewed**, and I missed
them. Cost: 2.2 min, 10,500 tokens.

It is now a **step inside `/intent-and-goal` Phase 2** — run on the draft scenarios
*before* they are shown for approval, so gaps feed the same iteration the user is already
having rather than reopening a set they have already blessed. It was briefly a separate
"Phase 2b" that ran once the user was happy with the scenarios; that ordering made the
first approval premature. It reports; the user decides what to close; accepted gaps are
labelled on the rule so the next reader finds the hole named.

### The agent this was extracted into has since been dropped (2026-08-13)

The review was first packaged as a `spec-gap-reviewer` agent. This finding flagged the
extraction as **unmeasured** — the gaps had been found by an agent that was also
*designing*, and whether the reasoning survived without the design artifact was untested.
It was then tested, on this same frozen spec, against a plain review pass as the control:

| ground-truth gap | `spec-gap-reviewer` | plain review pass |
|---|---|---|
| Rule 1, uniqueness (the data-loss one) | found | found |
| Rule 8, a failed store | found | found |
| Rule 5, atomicity | found | found |
| **Rule 4 boundary** — withdrawing *exactly* the balance | **missed, and listed Rule 4 as "verified as driven"** | found |
| **Self-transfer** — same account twice, destroys or creates money | **not mentioned** | found |

Both gaps the agent missed are real: all three scored arms independently guarded
self-transfer and wrote an exact-balance withdrawal test, so the pipeline had to discover
them unaided. The agent also produced ~2× the output (10.7KB vs 5.8KB).

The decisive part is not that it tied on the three known gaps — it is that its one
distinctive feature, a per-rule "verified as driven" sweep, is where it produced a **false
all-clear**. Certifying coverage that does not exist is worse than saying nothing.

So the agent was deleted and the review became an instruction inside Phase 2, keeping the
two things that demonstrably worked in both runs: enumerate every rule and name the laziest
implementation that passes while violating it, and propose the smallest scenario that would
go red. A fourth trap was added from the agent's own failure — never call a rule covered
without naming the mutant the scenarios kill.

### And then the step itself was tested against no step (2026-08-13)

Keeping a review step on the argument that it *ought* to help is the same mistake this
programme keeps correcting, so it was measured too. Two arms, same model, same day, given
the frozen spec's intent and rules with **the scenarios removed**, each running one version
of Phase 2:

- **control** — Phase 2 exactly as it stood on `main`: draft scenarios, ask clarifying
  questions if a rule is ambiguous, cover happy/empty/edge/error.
- **treatment** — the same, plus the gap check on the draft before presenting it.

Scored on the three rules the frozen spec left undriven, pre-registered before reading the
output:

| | control (27 scenarios) | treatment (30 scenarios) |
|---|---|---|
| **Rule 1, duplicate open** | **fails — presupposition trap** | passes |
| Rule 5, failed transfer leg | passes | passes |
| Rule 8, store failure | passes | passes |

The control's Rule 1 scenario reads:

```gherkin
Given the bank has an account with account number "N"
When another account is opened
Then its account number is not "N"
```

It never attempts a duplicate. It asserts the bank *generates* distinct numbers, so an
unconditional `save` that overwrites on a second open passes it. That is the data-loss
defect, presented as coverage — and it is the first trap the gap check names. The treatment
instead opened the same number against a seeded account and asserted its movements
survived.

So the step is kept on one differentiating rule out of three, and it is the rule that
actually shipped the defect. Scenario counts are comparable, so this is not the treatment
simply being more thorough.

**A caution about scoring, not the result.** An automated keyword pass scored the control as
*covering* Rule 1 — "share an account number" matches. Only reading the scenario body
caught it. Same lesson as the mutation oracle: the metric said covered, the source said
otherwise.

**What this does not show.** n=1 per arm, and the *agent* comparison above used a dedicated
review prompt, not the real
Phase 2 flow, where the model is generating scenarios and motivated to feel finished. The
result therefore supports "the dedicated review **step** earns its place, the separate
**agent** does not" — it does not support removing the phase.

**And it corrects the case for the phase downward.** This finding originally claimed the
undriven Rule 1 produced the data-loss defect in "all four earlier arms". Checked against
every arm's source: the guard is absent in **two of eight** and present in the other six.
The pipeline usually guards an undriven rule unprompted, so this phase is insurance
against a coin flip, not a systematic failure — cheap insurance, but not the certainty
first reported.

## 4. What this cost, and the mistake worth remembering

Four arms, ~6 hours of runtime. The result is a rejection plus one 2-minute agent.

**The mistake:** I reported layered-1's 74 minutes as "−42%, cut by more than half" from a
single arm — one turn after telling the user that variance now rivals effect size and that
nothing under ~20 minutes could be claimed at n=1. The confirmation arms exist because the
user asked for them.

Single-arm spans have now misled twice in this programme (the 1-deep arm, then this one).
The standing rule from here: **no wall-clock claim from fewer than three arms.** Quality
metrics have been better behaved — mutation and red→green moved consistently and in the
predicted direction every time — so a two-arm quality signal is worth more than a two-arm
speed signal.

## 5. Standing position

**Adopted:** `/run-pipeline` with Stage 1 + Stage 2 — **−18% time, −30% tokens**, mutation
survivors **0**, red→green 86.1%, catches 18.

**Rejected with evidence:** Stage 3 planning lookahead at both depths (finding 15), Stage 4
scenario DAG (cut before building), the layered pipeline (this finding).

**Open, unrun:** Stage 5 small-scenario fast path (~3% tokens), Stage 6 deliberation budget
— the only remaining large lever, since `effort` is uniform `medium` on every dispatch and
file content is just 20–26% of output tokens. Stage 6 needs three arms per configuration to
say anything, on the rule above.
