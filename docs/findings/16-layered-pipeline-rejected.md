# Finding 16 — The layered pipeline is rejected; its specification review is kept

**Date:** 2026-08 · **Area:** `commands/run-pipeline-layered` (rejected), `agents/system-architect` (rejected), `agents/spec-gap-reviewer` (adopted), `commands/intent-and-goal`
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
phase of `/intent-and-goal`, extracted into `spec-gap-reviewer`.

---

## 1. The results

| arm | span | out-tok | rows | red→green | unplanned | catches | **mut-real** |
|---|---|---|---|---|---|---|---|
| **s1s2 (adopted)** | 104 | 440,250 | 101 | 86.1% | 3.0% | 18 | **0** |
| layered-1 | **74** | 284,149 | 116 | 83.6% | 0.9% | 11 | 1 |
| layered-2 | 103 | 364,545 | 126 | **71.4%** | **14.3%** | 10 | **4** |
| layered-3 | 103 | 412,250 | 157 | 91.7% | 5.7% | 6 | 2 |

Layered spans **74, 103, 103** — mean 93 against 104. The two confirmation arms finished
**19 seconds apart** (105m28s and 105m47s), which makes 74 the outlier.

Tokens are a real win: mean 353,648 vs 440,250, **−20%**, consistent in direction across
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

Test strength is also unstable in a way the adopted config is not: red→green 71.4% →
91.7%, unplanned 0.9% → 14.3%, catches sliding 11 → 10 → 6 against 18.

The fork would only be adoptable **with** a mutation gate feeding the fix loop — which is
swarm-forge's bargain (generated tests plus measured falsifiability, instead of designed
falsifiability), and a bigger build than the thing it was meant to speed up.

## 3. What is kept, and why it is the better half

`system-architect`'s mandatory `## Specification Gaps` section, given only the frozen
9-scenario spec and no hint about what to look for, reported:

- **Rule 1 (unique account numbers).** *"SCENARIO-01 presupposes the account is absent,
  so nothing exercises the collision. An implementation that overwrites the existing
  account on a second open — destroying its movements — passes all nine scenarios."*
  This is the exact defect **all four earlier arms shipped**; the baseline arm's reviewers
  found it only after burning all three fix rounds, and then ran out of budget.
- **Rule 8 (a failed store is reported and applies nothing).** The spec's own notes claim
  the refusal scenarios carry it. They don't: scenarios 03 and 05 are refused *before* any
  store is attempted, so no scenario ever reaches a failing store.
- **Rule 5's atomicity half.** SCENARIO-06's third `Then` pins identity but only the happy
  path; two sequential saves pass it.

Plus five ambiguities (how a legacy row is recognised, refusal status codes, ordering ties,
money precision, whether a legacy record blocks reuse of its number).

Two of those three gaps were in a specification **I wrote and reviewed**, and I missed
them. Cost: 2.2 min, 10,500 tokens.

It is now `spec-gap-reviewer`, run at `/intent-and-goal` **Phase 2b** — after the user is
happy with the scenarios, before the SoT is written. It reports; the user decides what to
close; accepted gaps are labelled on the rule so the next reader finds the hole named.

**Unmeasured, and flagged as such:** the adopted agent is an extraction. The gaps were found
by an agent that was also designing, and the extraction keeps the design *reasoning* while
dropping the design *artifact*. Whether the reasoning survives without the artifact is
untested.

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
