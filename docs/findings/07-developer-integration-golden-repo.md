# Finding 07 — Developer integration on a golden repo (the build layer)

**Date:** 2026-06 · **Area:** `evals/golden-repo/`, `evals/check_build.py`,
`evals/developer/`, `run_all.sh` Phase 1c
**Status:** built and green (1 fixture; the integration layer of the pyramid)

## The change

The reviewers and the architect are graded on *what they say/write*. The
developer can only honestly be graded on **what it produces compiling and
passing**. So this layer runs the **real `opus` developer agent** through a full
red-green TDD loop in a **buildable Kotlin repo**, then *independently* runs
`./gradlew test` and grades the objective outcome.

- **`evals/golden-repo/`** — a pristine, self-contained Kotlin/JUnit5 Gradle
  skeleton (Gradle 9.4.0 wrapper, Kotlin 2.1.0, `kotlin("test")` + JUnit
  platform). **Framework-free on purpose**: no Spring, no JPA, no DB — so the
  build is seconds, not the 10-30s of a Spring context boot.
- **`evals/check_build.py`** — parses the JUnit XML under
  `build/test-results/test/`: asserts build exit 0, `>= minTests` tests actually
  ran (not skipped), zero failures/errors, and that required test classes exist.
- **`evals/developer/fixtures/withdraw-money-core/`** — freezes both the
  `specification.md` **and** the architect's `SCENARIO-01.md` plan (trimmed to the
  core: domain → port → fake → contract test → use case). Freezing the plan keeps
  this a clean *developer* test; chaining architect→developer is the acceptance
  layer.
- **`run_all.sh` Phase 1c** — copies the golden repo to a scratch dir, overlays
  the frozen spec+plan, dispatches `claude -p --agent developer` there
  (Read/Write/Edit/Glob/Grep/Bash/Skill), then runs the build itself.

## Why these specific design choices

- **Kotlin, not TS/Vitest — fidelity over toolchain convenience.** The developer,
  the architect's plans, and the three skills it loads are all Kotlin/Spring-
  shaped. A TS golden repo would test a *different pipeline than ships*; the green
  light would be meaningless. The legitimate cost of Kotlin (slow Spring context)
  was removed by **cutting scope** (framework-free core), not by switching stack.
- **We run the build, not the agent's self-report.** The developer runs Gradle
  during its own loop, but the grade comes from an *independent* `./gradlew test`
  the harness runs afterward — the agent cannot mark its own homework.
- **Vacuous-pass guard.** `minTests >= 2` + an explicit "no JUnit reports → fail"
  (a compile failure produces no reports) stop a "0 tests, exit 0" from looking
  green. `mustHaveTestClasses: ["WithdrawMoney"]` pins that the *intended*
  behavior was tested, not just something.
- **Strictly opt-in.** It's `opus` + a full TDD loop + Gradle ≈ minutes and
  ~$1-4 per fixture, so Phase 1c runs ONLY for `./evals/run_all.sh developer` —
  never in the default suite or a bare `--agents` run. Not fingerprint-cached.
- **Scratch kept on failure.** On a red build the scratch dir is preserved and
  the gradle tail printed, so a failure is debuggable (compile error vs test
  failure vs missing tests); on pass it's cleaned.

## Toolchain reality (the spike)

`gradle`/`kotlinc` aren't on PATH, but `~/.gradle` is **3.8 GB** (Gradle is used
here via `./gradlew` wrappers) and only **JDK 25** is installed. Gradle 8.9
predates JDK 25; **Gradle 9.4.0** (also cached, and used by another repo here)
runs on JDK 25. A throwaway one-test skeleton built green in 39s (first run,
daemon start) — proving the toolchain before authoring the fixture. The wrapper
was copied from an existing project rather than generated (no `gradle` on PATH).

## Result

`withdraw-money-core::developer` → **PASS**: the developer implemented the core
(entity + equality test, Repository port, contract test, in-memory fake + its
contract test, use case + unit test) and the independent build went green with
real tests executed. First proof in this harness that **generated code actually
compiles and runs**, not just that an artifact reads correctly.

## Limitations / next

- **One fixture, one run.** The developer is non-deterministic; a single green
  proves it *can* succeed, not that it always will. If it proves flaky, switch to
  `pass@k` (run k times, track a rate) per the strategy doc.
- **Core only.** The controller-IT / infra-adapter slice (Spring/JPA/DB/
  Testcontainers) is deliberate v2 — heavier build, separate golden repo.
- **Acceptance layer still open.** Chaining architect→developer→`/run-reviewers`
  from a frozen spec, asserting tests pass + reviewers reach PASS, builds on this.
