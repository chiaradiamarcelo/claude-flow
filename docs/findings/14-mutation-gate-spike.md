# Finding 14 — Mutation/CRAP/DRY as a pipeline gate: spike says "mutation, but filtered, and only as a safety net"

**Date:** 2026-08 · **Area:** `evals/` (oracle tooling), pipeline review stage (proposed)
**Status:** spike complete, **not wired into the pipeline**. Recommendation below; the decision
to build the gate is deferred to the reader. Builds on [finding 13](13-batch-vs-strict-tdd.md),
whose oracle tooling is archived at tag `experiment/batch-vs-strict-tdd`.

---

## TL;DR

Should the pipeline gain a mutation / CRAP / DRY gate after the reviewers, feeding surviving
findings into the fix-loop? We spiked it before building it (same discipline as finding 13).
Result:

- **A naive mutation gate would be 100% false positives** on the pipeline's own output — every
  surviving mutant is `equals`/`hashCode`/`toString` boilerplate or a Kotlin null-check
  intrinsic. Wiring it as-is would spam the fix-loop with junk like "add a test for
  `Account.toString`".
- **A *filtered* mutation gate** (drop boilerplate-method + Kotlin-intrinsic survivors) is
  **silent on good output** (0 findings) and **fires precisely on a genuine test regression**
  (a deliberately weakened assertion surfaced a real "dropped `save()`" survivor, correctly kept
  while the junk was filtered).
- **CRAP and DRY add nothing here** — both produced **zero findings on all six arms**; on
  clean-architecture output they're silent, and they overlap `refactor-advisor` anyway.

**Recommendation:** if we add anything, add **filtered mutation testing** as an **optional
audit/safety-net gate**, not a blocking fix-loop step — because on the pipeline's current
(mutation-strong) output it fires nothing. Its value is *insurance against a future test-quality
regression*, not improvement of today's output. Skip CRAP and DRY.

---

## What was tested & why

Finding 12 recommended a mutation/CRAP/DRY gate but flagged a risk: PIT's **Kotlin
equivalent-mutant noise** (round 2 of that experiment saw surviving mutants that were pure
`equals`/`hashCode`/`toString`/`checkNotNull` junk). If most survivors are junk, a gate that
emits them as fix-loop findings would generate false work. So the spike question is:
**what fraction of surviving mutants on real pipeline output are actionable vs junk, and can a
filter separate them without hiding real gaps?**

## Method

- **Re-ran PIT** ($0, compute-only) on all **six archived arm repos** from finding 13 (withdraw /
  deposit / account-overview × strict / batch) using the same pure-Kotlin sidecar oracle.
- **Classified every surviving mutant** (`classify-survivors.py`) into **junk** (methods
  `equals`/`hashCode`/`toString`/`copy`/`componentN`/`<init>`/`<clinit>`, or descriptions
  containing Kotlin intrinsics `checkNotNull*`/`Intrinsics`/`$default`) vs **candidate-real**
  (a survivor in any other method = a business-logic gap to inspect).
- **Two sensitivity tests** — deliberately weakened real assertions and re-ran PIT, to check the
  filter catches genuine regressions rather than just being inert.

## Results

### On the pipeline's own (good) output — survivors are 100% junk

| Arm | mutants | killed | survived | junk | real |
|---|--:|--:|--:|--:|--:|
| r1 withdraw strict / batch | 16 / 18 | 14 / 15 | 2 / 3 | 2 / 3 | 0 / 0 |
| r2 deposit strict / batch | 11 / 15 | 9 / 10 | 2 / 5 | 2 / 5 | 0 / 0 |
| r3 overview strict / batch | 3 / 5 | 3 / 5 | 0 / 0 | 0 / 0 | 0 / 0 |
| **Total** | **68** | **56** | **12** | **12** | **0** |

**Every one of the 12 survivors is junk.** A naive gate → 100% false-positive findings. A
filtered gate → **0 findings** (correct: the test-designer already produces mutation-strong
tests, so there's nothing to fix).

### Sensitivity — does the filtered gate catch a real regression?

Two weakenings of the withdraw-strict arm:

1. **Vacuous-ify the overdraft-rejection assertion** → survivors **unchanged** (still 2 junk).
   *Instructive non-result:* the overdraft guard's mutants are **incidentally killed** by the
   happy-path and boundary tests (a mutation dies if it makes any executing test *error*, not
   only assert-fail). Mutation testing is robust to a single weak assertion on multiply-covered
   code — you can't easily manufacture a survivor.
2. **Unpin the subtraction math** (weaken all 4 balance-value assertions) → **3 survivors: 2
   junk + 1 real** — `WithdrawMoneyUseCase.execute` with `save()` removed **SURVIVED**, because
   the weakened persistence assertion (`isNotNull` instead of `== 150`) no longer catches a
   dropped save. The filter **correctly kept this one real finding and dropped the 2 junk**
   (an `Account.hashCode` boilerplate mutant and an `Account.withdraw` Kotlin-intrinsic
   equivalent mutant).

So the filter is **precise on this sample**: 0 findings when tests are strong, exactly the 1
real finding when a test genuinely regressed.

### CRAP / DRY

Across all six arms: **CRAP = 0 methods over threshold; CPD = 0 duplication blocks.** On
clean-architecture pipeline output they never fire. `refactor-advisor` already reasons about
duplication/complexity. No marginal value as gates.

## Recommendation

1. **Mutation — worth building, but only *filtered*, and as an *optional safety-net* gate.**
   - The filter (boilerplate methods + Kotlin-intrinsic descriptions — see `classify-survivors.py`)
     is **mandatory**: without it the gate is 100% noise.
   - Placement: after `run-reviewers`, **once per feature** on the final green tree (PIT is
     CPU-expensive; not per scenario), over the framework-free `domain`+`application` layers via
     the sidecar.
   - Wire it as **audit/log-only first** (report filtered-real survivors), *not* a blocking
     fix-loop step — because on today's output it emits nothing, so a blocking gate would add
     latency for zero benefit. Promote it to fix-loop-feeding only if/when real survivors are
     actually observed.
2. **CRAP, DRY — do not wire.** Silent on clean output; redundant with existing reviewers.

## Honest caveats

- **Tiny slices** (3–18 mutants/arm). Junk ratio and filter precision must be re-checked on a
  real, larger feature before trusting them — a bigger codebase has more mutable surface and may
  expose filter false-negatives (a real gap the filter wrongly drops) or new junk categories.
- **The value is defensive.** The spike shows the pipeline *already* produces mutation-strong
  tests, so a mutation gate mostly proves a negative. That's insurance, not improvement — weigh
  the CPU/latency cost against a failure mode that isn't currently occurring.
- **Equivalent-mutant detection is undecidable in general.** The filter is a heuristic
  (method-name + description); it is not a proof that a filtered mutant is truly equivalent.

## Tooling / reproduce

The **PIT sidecar oracle** is archived with finding 13 (tag `experiment/batch-vs-strict-tdd`,
`evals/experiments/batch-vs-strict-withdraw-money/oracle/run-oracle.sh`). The **filter/classifier**
was written for this spike; its rules are fully specified in the *Method* section above
(junk = boilerplate methods `equals`/`hashCode`/`toString`/`copy`/`componentN`/`<init>`/`<clinit>`
or descriptions containing `checkNotNull*`/`Intrinsics`/`$default`; everything else = candidate-real).
To reproduce: `oracle/run-oracle.sh <repo>` produces
`build/pit-sidecar/build/reports/pitest/mutations.xml`; apply the classification rules to its
`<mutation status!="KILLED">` entries for the junk/real split. If the gate is built for real (a
future PR), the classifier graduates into the pipeline alongside the oracle tooling.
