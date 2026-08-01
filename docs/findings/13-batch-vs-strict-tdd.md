# Finding 13 — Strict row-by-row TDD vs batch-red-per-class in the pipeline developer

**Date:** 2026-08 · **Area:** `agents/developer/`, `CLAUDE.md`, `skills/tdd/` (removed), `evals/experiments/`
**Status:** decided and shipped. The decision was merged in **PR #7**
(`promote/batch-red-per-class`). The full experiment lived in **PR #6**
(`exp/batch-vs-strict-withdraw-money`), which was **closed, not merged** — its raw
artifacts are archived under the git tag **`experiment/batch-vs-strict-tdd`**. This
finding is the durable record; the tag is the reproducible bundle.

---

## TL;DR

We A/B-tested the developer agent's inner-loop discipline — **strict row-by-row-red** (one
failing test → minimal code → next) vs **batch-red-per-class** (write all of a class's tests,
verify they all fail for their stated reasons, then implement the class). Across **three
structurally different scenarios plus a four-runs-per-arm variance study**, batch-per-class was
**~46% cheaper and ran the test suite ~61% less** with **no measurable quality regression**. We
promoted batch-per-class to the standing inner-loop rule, and — because it made the standalone
`tdd` skill redundant — removed that skill and the TDD methodology prose from `CLAUDE.md`,
leaving TDD owned operationally by the pipeline agents (test-designer selects, developer executes)
and enforced by the reviewers.

---

## 1. The question and why it was worth asking

This project's feature pipeline (`/intent-and-goal`) front-loads design into two dedicated
phases before any code is written:

- **architect** → the "Structure & Contracts" skeleton (which classes/ports/adapters exist).
- **test-designer** → the "Ordered Test List" (each row: an FLFI-named test, its TPP
  transformation, and the mutant/contradiction it kills), justified and mutation-aware.

So by the time the **developer** runs, the design is *already decided*. The developer *executes*
a plan; it does not *discover* one.

Strict per-test red-green-refactor is a discipline inherited from human practice. Its value
splits in two:

1. **Cognitive drip-feed** — one test at a time so a person, who can't hold a whole design in
   working memory, isn't overwhelmed and is nudged to the smallest next step. This is a *human*
   aid.
2. **Red-before-green verification** — a test seen to fail, then pass, is evidence it is
   non-vacuous and that the production code is what made it pass. This is about the *code*, not
   the coder — and it arguably matters *more* for an LLM, which can otherwise emit a test and its
   production code co-adapted into a fake green.

**Hypothesis:** because the pipeline front-loads design, (1) buys the developer nothing (it holds
the whole plan in context), while (2) can be preserved at coarser granularity. So the real
question is **row-by-row-red vs batch-red — not TDD vs no-TDD** — and batching should be cheaper
with equal quality.

---

## 2. Method — how it was set up and run

**One variable.** In each round both arms ran the **same** architect + test-designer plan; the
*only* difference was the developer's execution-discipline instruction:

- **`strict` arm** — one failing test → minimal code → next, row by row.
- **`batch` arm** — per class: write all its tests, run once, verify **every** test is red for
  its planned reason (*batch-red-verified*; a first-run green is vacuous and is fixed before any
  production code), then implement the class to green.

**Real agent, faithful dispatch.** Each arm was the real `developer` agent invoked as
`claude -p --agent developer --allowedTools Read Write Edit Glob Grep Bash Skill
--output-format stream-json --verbose` inside a fresh copy of `evals/golden-repo-spring` (Kotlin
2.1 / Spring Boot 4 / Gradle 9). This mirrors the eval harness's own `_claude()` invocation, so
the arms are faithful to what the pipeline actually runs.

**Substrate: plain Kotlin/JVM, no Android.** Deliberately avoided the emulator confound; a real
`gradle build` is a hard green-or-not oracle.

**A methodology confound we found and corrected (important).** The *first* arm runs were
invalid: the arm repos were placed **under `~/.claude`**, which Claude Code treats as a protected
config directory — so the sub-agent's `Write` tool and `mkdir` were **refused as "sensitive
file" edits**. The batch arm was fully blocked (0 files; it correctly reported the block and
refused to circumvent it); the strict arm only "passed" because it happened to write files via
Bash heredocs, which slip past the Write-tool guard. That asymmetry was *environment*, not
discipline. **All arms were re-run in a neutral scratch dir** (a real path, not a symlink),
where `Write` works normally. Every number in this finding is from the clean runs.
**Lesson: never run agent-write experiments inside `~/.claude`.**

---

## 3. How it was measured

### Cost / effort (the axis the experiment set out to measure)

Parsed from each run's stream-json transcript (`oracle/metrics.py`):

- **Output tokens** — the real cost driver.
- **Cost (USD)**, **turns**, **API duration** — from the final `result` event.
- **Gradle runs** — count of `./gradlew` invocations in the transcript. This is the *mechanism*:
  strict runs the suite ~twice per row (red, then green); batch runs it ~twice per *class*.
- **Write / Edit tool-call split** — a discipline fingerprint (strict edits incrementally; batch
  writes whole classes up front).

### Quality (the axis batch has to *defend* — parity or the cost win doesn't count)

Because "cheaper" is worthless if it's worse, we built a quality oracle from scratch
(`oracle/run-oracle.sh`), all `$0`/no-model:

- **Mutation testing (PIT)** — the real test-strength oracle: does the suite actually kill
  semantic changes to the code? Surviving mutants = weak tests.
- **CRAP** (from JaCoCo XML, `oracle/crap.py`) — `complexity²·(1−coverage)³ + complexity` per
  method: flags under-tested complex code.
- **DRY** (PMD CPD, Kotlin tokenizer) — duplication.
- **Green build** (`./gradlew test`), **plan↔code fidelity**, and the project's **`test-reviewer`
  + `refactor-advisor`** agents (finding counts) as additional quality axes.

**Toolchain notes (why the oracle is shaped the way it is).** Getting PIT to run on this stack
took four fixes, recorded here so the next person doesn't re-discover them:
`gradle-pitest-plugin` must be ≥ 1.19 for Gradle 9; PIT's forked JVM must be pinned to a plain
Temurin JDK (the machine's Android-Studio JBR crashes PIT's coverage minion); bytecode must be
targeted at Java 21 so PIT's ASM can read it; and — the real blocker — **Spring Boot 4 forces
JUnit Platform 6, which the pitest-junit5 plugin cannot drive**, so **mutation testing runs in a
pure-Kotlin sidecar** (JUnit 5) over the framework-free `domain` + `application` layers, which is
where mutation testing has value anyway. Controller/adapter wiring is covered by green-build +
reviewers, not mutation — by design.

---

## 4. The experiments we ran (four variations) and why

| # | Round | Scenario | Shape | Plan size | Why this one |
|---|---|---|---|---|---|
| 1 | withdraw-money | write-side command (aggregate `withdraw` + invariants: positive, no-overdraft) | vertical slice: domain → port + fake + contract → use case → JPA adapter → REST controller | 19 rows | the canonical clean-arch write slice — the richest, most-invariant case |
| 2 | deposit-money | write-side command (only a positive-amount invariant, no overdraft) | same shape, smaller | 14 rows | **replication** on a smaller plan the developer hadn't seen; tests whether the effect survives less "batchable" surface |
| 3 | account-overview | **read-side CQRS query** (Query port + read model + derived `tier`, no aggregate/UseCase/write-invariants) | the `query/` path the write slices never touch | 7 rows | **generalization** to a structurally different slice — does the win depend on write-side command TDD? |
| 4 | variance study | re-run round 3 **4× per arm** | identical plan/prompt/dir | — | **bound run-to-run noise**: is the batch↔strict gap real signal, or could an unlucky run erase it? |

Rounds 1→3 answer *does it replicate and generalize*; round 4 answers *is it bigger than noise*.

---

## 5. Results

### Combined across the three scenarios (n=3)

| Metric | Strict | Batch | Δ |
|---|--:|--:|--:|
| Cost (USD) | $17.16 | $9.18 | **−46%** |
| **Gradle runs** | 107 | 42 | **−61%** |
| Output tokens | 100,974 | 74,951 | −26% |
| Turns | 342 | 210 | −39% |
| Wall-clock (s) | 1,904 | 1,216 | −36% |

Per-round cost Δ: **−55% / −39% / −39%**. Per-round Gradle-run Δ: **−65% / −54% / −61%**.
Batch was cheaper on **every axis in every round**; margins shrink on smaller plans (less to
amortise) and wall-clock is the noisiest axis.

### Per-round quality (batch has to match, not beat)

| Round | Build | Mutation (strict / batch) | CRAP mean (s / b) | DRY | Reviewer findings (s / b) |
|---|---|---|---|---|---|
| 1 withdraw | both green | 88% / 83% | 1.26 / 1.28 | 0 / 0 | 8 / 7 |
| 2 deposit | both green | 82% / 67%\* | 1.21 / 1.24 | 0 / 0 | 10 / 8 |
| 3 overview | both green | **100% / 100%** | 1.15 / 1.18 | 0 / 0 | 8 / 11 |

\* **The round-2 mutation "gap" is not a regression — it's Kotlin boilerplate noise.** Inspecting
the survivors directly: batch's 5 = 1 equivalent mutant (an uncoverable Kotlin `checkNotNull`
intrinsic) + 4 NO_COVERAGE in `equals`/`hashCode`/`toString`; strict's 2 = the *same* intrinsic +
1 NO_COVERAGE `hashCode`. **Every business-logic mutant was killed in both arms.** The difference
is entirely untested boilerplate the batch arm happened to emit — exactly the synthetic-bytecode
noise the oracle design anticipated. Round 3 had no survivors at all in either arm.

### The most telling quality result: reviewer findings are plan-level, not discipline-level

In all three rounds the `test-reviewer` + `refactor-advisor` findings were **near-identical
across the two arms**, and the substantive ones recurred every round: a missing constructor/
factory invariant (invalid state constructible), missing validation-matrix coverage
(malformed-input 400 / unexpected-failure 500), and primitive obsession. **Every substantive
finding is upstream of the developer** — a gap in the architect's contracts or the test-designer's
list — which the developer faithfully executed either way. The small count spread even *flipped
direction* across rounds (strict higher in r1/r2, batch higher in r3), i.e. noise. This is the
cleanest evidence that **the plan determines quality, not the inner-loop discipline** — and it
independently corroborates the whole result. (Corollary: the real lever for better output is
tightening the architect/test-designer phases, not the developer.)

### The Write/Edit fingerprint

Every round: strict grows code by many small **edits** (r1 50, r2 31, r3 13); batch writes whole
classes up front (**5 edits** every round). A clean signature of the two disciplines.

---

## 6. The variance study (round 4) — is the gap bigger than noise?

Re-ran `account-overview` **4× per arm** (identical plan/prompt/neutral-dir; all 8 runs green),
measuring only the cost/effort metrics.

| Metric | Strict mean±std (min–max) | Batch mean±std (min–max) | Δmean | ranges disjoint? |
|---|---|---|--:|---|
| **Gradle runs** | 19±2 (18–22) | 8±1 (7–10) | **−57%** | **YES** |
| Cost (USD) | 3.72±0.29 (3.36–4.15) | 2.48±0.46 (2.11–3.27) | −33% | **YES** (by $0.09) |
| Turns | 79±4 (72–84) | 58±7 (54–70) | −26% | **YES** |
| Output tokens | 25,657±2,925 | 21,213±4,794 | −17% | **no** (overlap) |
| Wall-clock (s) | 451±40 | 343±116 | −24% | **no** (overlap) |

**Interpretation.** The **mechanism is bulletproof**: Gradle-run counts are completely disjoint
(strict 18–22 vs batch 7–10), so batch runs the suite ~⅓ as often *every time*, independent of
luck. Cost and turns still separate at n=4. But **tokens and wall-clock overlap** — batch has
**fatter tails** (one run ballooned to 29.5k tokens / 538 s, matching a strict run). So the
"≈half the cost" figure is a **central tendency, not a floor**: expect ~30–50% savings, not a
guarantee.

---

## 7. Caveats (do not over-read)

- **n = 3 scenarios, one run per arm, + one 4× variance study.** Direction is robust across three
  shapes; magnitude is an estimate, not a constant. No cross-scenario repeated-seed grid.
- **Mutation absolute scores are noisy** on Kotlin (equivalent/uncoverable mutants). The
  systematic component cancels in a same-shape A/B — treat "88 vs 83" as "the same."
- **Runs were sequential** (strict then batch); each `claude -p` is a fresh session (no cross-arm
  prompt-cache advantage), but the order wasn't randomized.
- **Mutation covered `domain` + `application` only** (the framework-free layers), by design.

---

## 8. Decision, and what shipped

**Promoted batch-red-per-class to the standing inner-loop rule** (outer loop — one scenario at a
time — unchanged). Concretely, in **PR #7**:

- **`agents/developer/Agent.md`** — implementation-mode step 4 now batches red-green **per
  class** with the mandatory **batch-red-verified** gate.
- **Removed `skills/tdd/SKILL.md`.** For an all-LLM, plan-executing pipeline it was redundant:
  test *selection* (ZOMBIES/TPP/ordering) is the test-designer's job; red-green *execution* is
  the developer's step 4. Its only loader was the developer's session setup.
- **Removed the TDD methodology from `CLAUDE.md`** (the Red-Green-Refactor cycle, the
  "every change preceded by a failing test" mandate, and the granularity note); kept only the
  test-naming conventions. TDD is now owned operationally by the agents and enforced by the
  reviewers, not restated as playbook prose.

**Doctrine now:** LLM TDD **defaults to batch-per-class** — per-test one-at-a-time is a human
cognitive aid the LLM doesn't need, because it designs the slice up front.

**What we deliberately kept:** the **batch-red-verified** gate in the developer agent. Mutation
testing gives the same "your tests aren't vacuous" confidence, but *late and it isn't built into
the pipeline yet*; the batch-red gate is the cheap, immediate, per-class version that stops a
fabricated-green test from ever being written. They are defense-in-depth, not substitutes.

**What we did NOT do (deferred, next PR):** wire mutation/CRAP/DRY *into* the pipeline as a
review-stage gate feeding the fix-loop. Mutation is the highest-value of the three; CRAP overlaps
it; DRY overlaps `refactor-advisor`. It belongs after the reviewers, run once per feature (not
per scenario — PIT is CPU-expensive). It needs its own spike first, because PIT's Kotlin
equivalent-mutant noise (see the round-2 note) would generate **false fix-loop findings** if
wired in naively — measure that false-positive rate before giving it a permanent slot. Same
spike → measure → promote loop this experiment used.

---

## 9. Reproduce / archive

The full experiment (all four rounds' plans, both arms' code + `metrics.json` + stream-json
transcripts + oracle logs + reviewer findings, and the oracle tooling —
`run-oracle.sh`, `crap.py`, `metrics.py`, `apply-oracle-build.py`, the PIT `pit-sidecar/`) is
archived at:

- **tag `experiment/batch-vs-strict-tdd`** → `evals/experiments/batch-vs-strict-withdraw-money/`
- source PR **#6** (closed, not merged).

To reproduce the oracle on any arm repo: `oracle/run-oracle.sh <arm-repo>` (green build +
JaCoCo→CRAP + CPD/DRY + the PIT sidecar); `oracle/metrics.py <transcript.jsonl> --wall <s>` for
the cost/effort numbers.
