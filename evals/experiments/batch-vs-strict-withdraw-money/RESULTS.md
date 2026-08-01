# Results — strict row-by-row-red vs batch-red-per-class (developer phase)

**Three structurally different scenarios, one run per arm each (n=3).**
Round 1 = `withdraw-money` (write-side command, 19-row plan);
round 2 = `deposit-money` (write-side command, 14-row plan, `round2-deposit-money/`);
round 3 = `account-overview` (**read-side CQRS query**, 7-row plan, `round3-account-overview/`).
In each round both arms executed the *same* architect + test-designer plan; the only variable is
the developer's execution discipline. All six runs were in a neutral dir outside `~/.claude` (see
the confound note) via the real `developer` agent (`claude -p --agent developer --output-format stream-json`).

**Headline (n=3): batch-red-per-class is consistently ~half the cost and ~⅓ the Gradle runs, with
quality parity, across write-side *and* read-side slices.** The direction replicated in all three
scenarios; margins are larger on bigger plans.

## Combined (all three rounds summed)

| Metric | Strict | Batch | Δ |
|---|--:|--:|--:|
| Cost (USD) | $17.16 | $9.18 | **−46%** |
| **Gradle runs** | 107 | 42 | **−61%** |
| Output tokens | 100,974 | 74,951 | −26% |
| Turns | 342 | 210 | −39% |
| Wall-clock (s) | 1,904 | 1,216 | −36% |

Per-round cost delta: **−55% / −39% / −39%**. Per-round Gradle-run delta: **−65% / −54% / −61%**.

Quality across all three rounds: **all six runs green; CRAP parity** (strict 1.26/1.21/1.15,
batch 1.28/1.24/1.18); **zero duplication everywhere**; **mutation parity on business logic**
(every logic mutant killed in all six runs; round-3 read slice was 100% both arms — see the
mutation note). Reviewer findings overlap heavily and are plan/architecture-level, not
discipline-level; the ±few-finding spread flips direction across rounds (strict had more in r1/r2,
batch had more in r3), i.e. noise.

---

## Round 1 — withdraw-money

## Cost & effort (the axis the experiment set out to measure)

| Metric | Strict | Batch | Δ (batch vs strict) |
|---|---:|---:|---:|
| Output tokens | 43,016 | 27,724 | **−36%** |
| Cost (USD) | $7.82 | $3.50 | **−55%** |
| Turns | 153 | 77 | **−50%** |
| **Gradle runs** | 52 | 18 | **−65%** |
| Wall-clock (s) | 856 | 409 | **−52%** |
| API duration (s) | 701 | 375 | **−47%** |
| Write / Edit tool calls | 23 / 50 | 24 / 5 | discipline signature |

The `gradle_runs` collapse (52→18) is the mechanism: strict runs the suite ~twice per row
(red, then green) across ~19 rows; batch runs it ~twice per *class* (batch-red, then green)
across 4 classes, plus fixes. The Write/Edit split is the other fingerprint — strict grows
code by many small **edits** (50), batch writes whole classes up front (5 edits).

## Quality (the axis batch has to defend — parity or it doesn't count)

| Axis | Strict | Batch | Verdict |
|---|---|---|---|
| Build (`./gradlew test`) | ✅ green | ✅ green | tie |
| Files (prod / test) | 15 / 8 | 16 / 9 | comparable |
| **Mutation score** (PIT) | 14/16 killed (**88%**) | 15/18 killed (**83%**) | parity |
| **CRAP** (JaCoCo) | 42 methods, mean **1.26**, 0 over-30 | 47 methods, mean **1.28**, 0 over-30 | parity |
| **DRY** (PMD CPD) | 0 duplicated blocks | 0 duplicated blocks | tie |
| Reviewer findings | 8 (5 test + 3 refactor) | 7 (4 test + 3 refactor) | parity |

Mutation counts differ only because batch generated slightly more mutable code (18 vs 16
mutants); both leave 2–3 survivors and both sit in the mid-80s. Per the Kotlin-bytecode caveat
the absolute score is noisy, but the **delta is small and non-directional**.

**The reviewer findings are the same on both arms** — both flag: (1) domain invariants tested
on the entity rather than through the use case, (2) no malformed-input/parse-error 400 case,
(3) `Account`'s constructor missing a non-negative-balance invariant, (4) primitive obsession
on `accountId`/`amount`. These are **plan-level** gaps (the test list has no malformed-JSON row;
the use-case invariant coverage is delegated to the entity), reproduced identically regardless
of discipline. That is the cleanest possible evidence that **the discipline did not move
quality** — the same plan produced the same code shape and the same defects both ways.

---

## Round 2 — deposit-money (replication)

Smaller plan (14 rows; deposit has only the positive-amount invariant, no overdraft).

| Metric | Strict | Batch | Δ |
|---|--:|--:|--:|
| Output tokens | 36,352 | 28,984 | −20% |
| Cost (USD) | $5.73 | $3.48 | **−39%** |
| Turns | 117 | 78 | −33% |
| **Gradle runs** | 37 | 17 | **−54%** |
| Wall-clock (s) | 663 | 562 | −15% |
| Write / Edit | 21 / 31 | 22 / 5 | same signature |

Quality: both **green**; **CRAP** 1.21 vs 1.24 (parity); **DRY** 0 vs 0; reviewer findings 10 vs
8 (again the same plan-level set: missing-field 400, no `Account(...)` fixture builder, missing
constructor invariant, primitive obsession). **Mutation** raw score 82% (9/11) vs 67% (10/15) —
this looks like a batch regression but is **not** (see the note).

The cost/effort advantage replicated in direction on every axis, with **smaller margins than
round 1** — expected, since the smaller plan gives batching less to amortise, and wall-clock is
the noisiest axis (batch 562 vs strict 663 here, machine-load-sensitive).

### Mutation note — the round-2 "gap" is Kotlin boilerplate noise, not weaker tests

Inspecting the surviving mutants directly:

- **Batch (5 survivors):** 1 equivalent mutant (`Account.deposit` — a Kotlin
  `checkNotNull` intrinsic that cannot be triggered) + 4 **NO_COVERAGE** in `equals` /
  `hashCode` / **`toString`** boilerplate.
- **Strict (2 survivors):** the *same* equivalent `Account.deposit` intrinsic + 1 NO_COVERAGE
  `hashCode`.

**Every business-logic mutant was killed in both arms** (the deposit calculation, the
positive-amount invariant, the not-found branch). The entire raw-score difference is untested
`equals`/`hashCode`/`toString` surface the batch arm happened to emit — precisely the synthetic-
bytecode noise the oracle design flagged for Kotlin. On the axis that matters, round 2 is
parity, same as round 1.

---

## Round 3 — account-overview (read-side / CQRS query — structurally different)

The first two rounds were write-side command slices (aggregate + `withdraw`/`deposit` + invariants).
Round 3 is a **read slice**: a `Query` port + read model + a derived `tier` projection
(`AccountTier.forBalance`, PREMIUM ≥ 1000), no aggregate, no UseCase, no write invariants — the
`query/` path the other two never touched. Smallest plan (7 rows).

| Metric | Strict | Batch | Δ |
|---|--:|--:|--:|
| Output tokens | 21,606 | 18,243 | −16% |
| Cost (USD) | $3.61 | $2.20 | **−39%** |
| Turns | 72 | 55 | −24% |
| **Gradle runs** | 18 | 7 | **−61%** |
| Wall-clock (s) | 385 | 245 | −36% |
| Write / Edit | 17 / 13 | 16 / 5 | same signature |

Quality — **the cleanest parity of the three**: both **green**; **mutation 100% both** (strict
3/3, batch 5/5 — *no survivors either arm*, so not even boilerplate noise this time); **CRAP** 1.15
vs 1.18; **DRY** 0 vs 0. Reviewer findings 8 (strict) vs 11 (batch) — same core set (no 500 test,
`AccountOverviewView` tier-invariant, hard-coded threshold, fixture builder, contract-file naming);
batch drew slightly *more* this round, the opposite of r1/r2, confirming that spread is noise.

The cost/effort advantage held on a structurally different slice (batch even cheaper *per Gradle
run* here), showing the effect isn't specific to write-side command TDD.

## Verdict

For this pipeline — where the architect and test-designer front-load design, so the developer
*executes* a plan rather than discovering one — **batch-red-per-class is consistently better on
cost/effort (n=3: −46% cost, −61% Gradle runs combined) with no measurable quality regression**
(all six runs green, mutation parity on logic, CRAP parity, zero duplication, matching plan-level
reviewer findings). The batch-red-verified guardrail held every round: the batch developer wrote
each class's tests, ran once, and reported observing them red before implementing. The effect
replicated across three structurally different scenarios — two write-side command slices and one
read-side CQRS query slice — with larger margins on larger plans.

This supports promoting batch-per-class to the standing **inner-loop** rule (outer loop — one
scenario at a time — unchanged), and it is consistent with the hypothesis that strict
row-by-row's value is largely a *human* cognitive aid the LLM doesn't need, while the part that
protects the *code* (red-before-green) is preserved by the batch-red gate.

## Honest caveats (do not over-read)

- **n = 3 scenarios, one run per arm each — plus a 4-runs-per-arm variance study** (round 4,
  `round4-variance/VARIANCE.md`). Run-to-run noise is now measured, not assumed: **Gradle runs
  separate completely** (strict 18–22 vs batch 7–10, disjoint) and cost/turns separate at n=4,
  but **tokens and wall-clock overlap** — batch has fatter tails (an occasional expensive run
  approaches strict's cost). So the direction is robust and the *mechanism* (far fewer test-suite
  runs) is noise-free, but the **≈½-cost magnitude is a central tendency, not a floor** — expect
  ~30–50% savings, not a guarantee. Margins also vary with plan size.
- **Mutation absolute scores are noisy** on Kotlin (synthetic bytecode → equivalent mutants).
  The systematic component cancels in a same-shape A/B, but treat 88 vs 83 as "the same."
- **Sequential runs** (strict then batch); no evidence of machine/model drift, and each
  `claude -p` is a fresh session (no cross-arm prompt-cache advantage), but it is not a
  randomized order.
- **The oracle mutation-tests domain + application only** (the framework-free layers, via the
  pure-Kotlin sidecar). Controller/adapter wiring is covered by green-build + reviewer findings,
  not mutation — by design.

## Confound found and corrected (methodology note)

The **first** arm runs were invalid: the repos were placed under `~/.claude`, which Claude Code
treats as a protected config directory, so the sub-agent's **Write tool + `mkdir` were refused
as "sensitive file" edits**. The batch arm was fully blocked (0 files; it correctly reported the
block and refused to circumvent it); the strict arm only "passed" because it happened to write
files via Bash heredocs, which slip past the Write-tool guard. That asymmetry was
*environment*, not discipline. Both arms were re-run in a neutral scratch dir (a real path, not
a symlink) where `Write` works normally — the numbers above are from those clean runs. Lesson:
never run agent-write experiments inside `~/.claude`.
