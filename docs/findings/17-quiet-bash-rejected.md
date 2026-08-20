# Finding 17 — Quieting Bash output is rejected; two metric lessons are the return

**Date:** 2026-08 · **Area:** `agents/developer` (rejected), `evals/scorecard/extract_run.py` (caveat recorded)
**Status:** decided on two complete arms. Continues [finding 15](15-pipeline-cost-stage-1-and-2.md)
and [finding 16](16-layered-pipeline-rejected.md).

---

## TL;DR

Adding *"keep build output small on success and complete on failure"* to the developer
was expected to cut context by shrinking Gradle output. It **increased** the developer's
Bash bytes by 31%, left cost flat, and was rejected.

The return on the two arms is not the rejection. It is:

1. an **interim reading inverted on the full arm for the fourth time** — this one would
   have shipped a false mechanism story had the arm died early, as its predecessor did;
2. **`red_arrival` measures prose, not behaviour**, and moves when an arm's verbosity
   changes for unrelated reasons.

---

## 1. The result

`main-control` (current `main`) against `quiet-bash-2` (the same, plus the rule). Both
9/9, both scored. Same frozen 9-scenario spec, so **per scenario** is the honest
denominator.

| | control | treatment | |
|---|---|---|---|
| output tokens | 473,784 | 472,770 | −0.2% |
| API calls | 618 | 621 | +0.5% |
| cache-read | 36.0M | 36.4M | +1.1% |
| span | 102 min | 97 min | not claimable (3-arm rule) |
| **mutation candidate-real** | **3** | **0** | better |
| red arrival | 84.1% | 83.0% | flat |
| CRAP over threshold | 0 (mean 1.26) | 0 (mean 1.24) | flat |
| DRY | 7.21% | 7.53% | marginally worse |
| test rows | 82 | 100 | |

**The stated mechanism runs backwards:**

| developer Bash bytes | control | treatment | |
|---|---|---|---|
| total | 229,860 | **300,263** | **+31%** |
| — file inspection | 148,486 | 209,957 | +41% |
| — gradle | 80,909 | 85,861 | +6% |

The rule exists to shrink build output. Build output grew.

**Per-row normalisation would have flattered it** — out-tok/row reads −18%, because the
treatment produced 100 rows against 82. Row count is an *output* of the run, not a fixed
unit of work; dividing by it rewards an arm for writing more tests. Per-row is right when
comparing across different features (that is why the scorecard emits it), and wrong within
one frozen spec.

## 2. The premise was also wrong

The issue asserted *"Gradle output is the bulk"* of the developer's Bash bytes. On the
control it is **35%**. The majority — 64.6% — is 59 shell calls averaging 2.5 KB that
inspect files, duplicating what `Read` and `Grep` already do, while `Read` results are
separately ~50% of context. That correction is the one durable output of the issue, and
became a separate issue rather than being folded in.

## 3. Lesson one: the fourth interim reading to invert

At 2 of 11 developer dispatches, the treatment showed Bash bytes **−46%** and file
inspection **−78%**. On the complete arm: **+31%** and **+41%**.

The standing rule already said *no claim from an interim reading*, and the reading was
labelled diagnostic-only when taken. That was not enough — the earlier attempt at this same
arm **died at 7/9 on a spend limit**, and had this one died likewise, a −46% mechanism
story would have been written up from partial data and believed.

**Strengthened rule: a partial arm produces no mechanism claim either, not merely no cost
claim.** The four inversions to date: a 1-deep arm's speed confounded by row count; a
74-minute layered span that was 103 on confirmation; developer tool-calls-per-call reading
1.86–1.90 early and 1.57 complete; and this one.

## 4. Lesson two: `red_arrival` measures prose

The treatment showed 12 rows with no red evidence against the control's 3 — apparently a
batch-red regression, and exactly the risk this rule was flagged for.

It was not. Suite runs were **103 against 110**, with comparable output per run, so
verification happened just as often. What changed is that Status cells averaged **109
characters against 187**: the instruction to keep output small generalised to the agent
writing terser records, and the `RED_EVIDENCE` regex had less prose to match.

**`red_arrival` is unreliable whenever an arm's verbosity changes.** It is a proxy for
whether a test was seen to fail, read out of a natural-language cell. Any treatment that
touches how much the agent writes moves it for free.

This is the **third** metric in this programme to measure prose rather than behaviour, after
usage-summed-per-log-event and `red_then_green` being exclusive with `unplanned`. The
pattern is worth naming: *a metric parsed out of agent prose measures the prose.* Cross-check
against a behavioural counter — here, suite-run counts — before believing it.

## 5. What this says about the previously suspected regression

`main-control` scored 3 candidate-real survivors where the previous prompt set had scored 0,
raising the possibility that trimming the test-designer's budget section had regressed
quality on merged `main`.

`quiet-bash-2` shares that same test-designer prompt and scored **0**. The 3 did not
reproduce. Filtered candidate-real has now ranged **0–4 across eleven arms** with no
treatment explaining the spread, so a single-arm move inside that band is noise.

**Consequence for every gate in this programme:** a mutation gate of the form *"candidate-real
must not increase"* cannot distinguish a real regression from noise at n=1. It is a floor
against gross failure — the layered fork's 4 — not a precision instrument.

## 6. Standing position

**Rejected:** Stage 3 lookahead at both depths (finding 15), Stage 4 (cut before building),
the layered pipeline (finding 16), the `spec-gap-reviewer` agent and its separate review
phase (finding 16), and Bash quieting (this finding).

**Shipped and measured:** Stage 1 + 2 plan-file caps and reviewer gate (finding 15), tool-call
batching (finding 15's method, measured by `batching-only-4`), and the rule-coverage check
inside `/intent-and-goal` Phase 2 (finding 16).

**Open:** shell file-inspection as the real Bash lever; one suite run per class; the
deliberation budget; splitting the testing skill; and `/run-pipeline` destroying an arm on a
529.
