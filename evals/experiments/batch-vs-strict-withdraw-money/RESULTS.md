# Results — strict row-by-row-red vs batch-red-per-class (developer phase)

**One scenario (`withdraw-money` SCENARIO-01), one run per arm, identical plan.** Both arms
executed the same architect + test-designer plan (`plan/…/SCENARIO-01.md`); the only variable
is the developer's execution discipline. Both ran in a neutral dir outside `~/.claude` (see
the confound note below) via the real `developer` agent
(`claude -p --agent developer --output-format stream-json`).

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

## Verdict

For this pipeline — where the architect and test-designer front-load design, so the developer
*executes* a plan rather than discovering one — **batch-red-per-class is strictly better on
cost/effort (roughly half the cost, a third of the Gradle runs) with no measurable quality
regression** (green build, mutation parity ~85%, identical CRAP, zero duplication, matching
reviewer findings). The batch-red-verified guardrail held: the batch developer wrote each
class's tests, ran once, and reported observing them red before implementing.

This supports promoting batch-per-class to the standing **inner-loop** rule (outer loop — one
scenario at a time — unchanged), and it is consistent with the hypothesis that strict
row-by-row's value is largely a *human* cognitive aid the LLM doesn't need, while the part that
protects the *code* (red-before-green) is preserved by the batch-red gate.

## Honest caveats (do not over-read)

- **n = 1 per arm, one scenario.** This is a spike, not a statistically robust result. It shows
  the effect is large enough to care about; it does not bound the variance. Repeat across
  scenarios/seeds before hard-coding the rule.
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
