# Experiment: strict row-by-row-red vs batch-red-per-class TDD (developer phase)

**Status:** COMPLETE (n=3) — see [`RESULTS.md`](RESULTS.md). Verdict: across three structurally
different scenarios (`withdraw-money` r1 + `deposit-money` r2 = write-side commands;
`account-overview` r3 = read-side CQRS query), batch-red-per-class is combined **−46% cost /
−61% Gradle runs** with no quality regression (all 6 runs green, mutation parity on logic, CRAP
parity, zero duplication, plan-level reviewer findings). NOT merged; this branch is a lab
notebook (promote the process rule + oracle separately if adopted).

## Hypothesis

Strict red-green-refactor's micro-cycle buys two distinct things:

1. **Cognitive drip-feed** — one failing test at a time so a *human* isn't overwhelmed and is
   nudged to the smallest next step. This is a human aid. An LLM holds the whole ordered test
   list + contracts in context, so it doesn't need the drip.
2. **Red-before-green verification** — a test seen to fail, then pass, is evidence it is
   non-vacuous and that the production code is what made it pass. This is about the *code*, not
   the coder — and it matters *more* for a machine, which can otherwise emit a test and its
   production code co-adapted to a fake green.

This pipeline front-loads design into the **architect** and **test-designer** phases, so the
**developer** *executes* a plan rather than discovering one — exactly the setting where strict
row-by-row earns least. So the real question is **row-by-row-red vs batch-red**, NOT TDD-vs-not.

## Design (A/B)

- **Same base, same plan.** One architect → test-designer plan for `withdraw-money` on
  `golden-repo-spring` (plain Kotlin/JVM). The plan is *identical* across arms; only the
  developer's execution discipline differs.
- **Arm `strict`** — developer as-is: one failing test → minimal code → next.
- **Arm `batch`** — same developer, dispatch-scoped prompt override: write *all* tests for a
  class → run once → implement the class → run once. **Not** a change to the global `developer`
  agent (promote only if it wins).
- **Non-negotiable guardrail — batch-red verified.** Write a class's tests, run once, and every
  row must be red *for the reason the plan states*. A row green on first run is vacuous and is
  fixed before any production code. This is the one part of red-green that batching threatens.
- **TPP stays.** The test-designer's TPP-ordered test *set* is kept verbatim (nil → constant →
  scalar isolates a different hard-coding per row); only ordering-as-incremental-design-driver
  becomes documentation, and that was already spent upstream.

Outer pipeline is unchanged (12 scenarios, one at a time). Only the **inner** loop within one
scenario is batched.

## Metrics (developer phase only)

| Axis | Source |
|------|--------|
| Output tokens (the real cost) | `claude -p --output-format stream-json` → final `usage.output_tokens` |
| Cost (USD) | same → `total_cost_usd` |
| Wall-clock, turns | same → `duration_api_ms`, `num_turns` |
| Gradle-run count | count Bash `gradlew` tool_use events in the transcript |
| Build green | `./gradlew test` |
| Reviewer findings | `test-reviewer` + `refactor-advisor` |
| Plan ↔ code fidelity | `evals/check_fidelity.py` |
| **Mutation score** | PIT (`oracle/`) |
| **CRAP** | JaCoCo XML → `oracle/crap.py` |
| **DRY / duplication** | detekt XML |

Quality is the weak axis without mutation testing; that's why the oracle is built first.

## Oracle (all $0 / no model) — setup notes

Built on `golden-repo-spring` (Kotlin 2.1 / Spring Boot 4 / Gradle 9.4). Toolchain gotchas
discovered and pinned (see `oracle-smoke/`):

- **`gradle-pitest-plugin` must be ≥ 1.19.0** — 1.15.0 uses a `reporting.baseDir` API removed
  in Gradle 9.
- **JVM pin.** The user's global `~/.gradle/gradle.properties` points `org.gradle.java.home` at
  Android Studio's JBR (Java 21); PIT's forked coverage minion crashes under it
  (`Minion exited abnormally / UNKNOWN_ERROR`). A repo-local `gradle.properties` pins a plain
  Temurin JDK instead.
- **Bytecode target 21.** PIT 1.19.1 bundles ASM 9.7.1, which reads bytecode only up to Java 23.
  So even on a Temurin 25 JDK we compile Kotlin/Java to **JVM 21** bytecode. (This is also why
  Java 25 as the *bytecode* target is off the table for PIT.)
- **PIT targets pure logic** — `domain.*` + `application.*`, never the `@SpringBootTest` (booting
  a Spring context inside PIT's agent is a minion-killer and isn't what mutation testing is for).

## swarm-forge note

`github.com/unclebob/swarm-forge` (R. Martin) validated CRAP/DRY/mutation as the right quality
gates but is an agent-*orchestration* platform (Clojure/Babashka + tmux) that *implements none of
them* — agents invoke external tools. So the oracle here is built from scratch (PIT + JaCoCo-CRAP
+ detekt), which also delivers pipeline issues #3 (mutation) and #4 (CRAP).

## Layout

```
README.md          # this file
oracle/            # crap.py + oracle-run notes; the shared build config lives per-repo
oracle-smoke/      # a known-good reference slice used to PROVE the oracle emits sane numbers
plan/              # the shared architect→test-designer plan (identical to both arms)   [pending]
arm-strict/        # generated tests+code + metrics.json                                 [pending]
arm-batch/         # generated tests+code + metrics.json                                 [pending]
RESULTS.md         # the axes side by side + verdict                                      [pending]
```

## Sequence (all complete)

1. ✅ Prove the oracle (PIT sidecar + JaCoCo-CRAP + CPD) on `oracle-smoke`.
2. ✅ Regenerate the architect → test-designer plan for `withdraw-money` (`plan/`).
3. ✅ Run developer `strict` arm, then `batch` arm — in a neutral scratch dir (see the confound
   note in RESULTS.md), copied back into `arm-strict/`, `arm-batch/`.
4. ✅ Run the three oracles + reviewers + capture tokens/time per arm → `RESULTS.md`.
5. ✅ PR open, **not merged**.

## How to reproduce the oracle on an arm

```
oracle/run-oracle.sh <arm-repo>       # green build + JaCoCo→CRAP + CPD/DRY + PIT sidecar
oracle/metrics.py <arm>/transcript.jsonl --wall <s>   # tokens/cost/turns/gradle-runs
```
