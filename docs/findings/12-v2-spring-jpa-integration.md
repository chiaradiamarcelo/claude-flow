# Finding 12 — v2 integration: a framework-ful golden repo (Spring/JPA vertical slice)

**Date:** 2026-06 · **Area:** `evals/golden-repo-spring/`, `evals/developer/`
**Status:** $0 scaffolding done (skeleton builds, fixture wired); paid developer run deferred (spend limit)

Finding 07's developer integration ran on a **framework-free** golden repo (plain
Kotlin + JUnit5, domain + use case only). That left the biggest structural gap in
the confidence pyramid: the pipeline was never proven to produce **building,
passing code for a full vertical slice** — HTTP delivery + relational persistence,
the layers where most real bugs live (wiring, mapping, transaction boundaries).

## The change
A second buildable skeleton, `evals/golden-repo-spring/`: Spring Boot + Spring Data
JPA + H2 (in-memory, so the build is self-contained — no external DB), Kotlin +
Gradle wrapper copied from `golden-repo`. The engine's `setup_workspace` was
generalized (finding 11's `run_fixture.py`) from a hardcoded `"golden-repo"` to
**any skeleton dir under `evals/`** (copy + strip `build`/`.gradle`/`.kotlin`);
`git-scratch` stays special. A fixture now selects its workspace by name —
`given.workspace: "golden-repo-spring"`. A new developer fixture
(`withdraw-money-spring`) freezes a spec + an architect plan covering the whole
slice (domain → write-side port → contract → fake → use case → JPA adapter → REST
controller) and grades on the objective build: `./gradlew test` green, ≥6 real
tests, and test classes for the **controller** (HTTP), **JPA adapter** (persistence,
proving contract-equivalence to the fake), and **use case** (application).

## The flagged risk, resolved
JDK 25 is very new; PROGRESS flagged "verify a Spring Boot that runs on JDK 25 +
Kotlin 2.1.0 + Gradle 9.4." Resolved empirically: a real reference project on this
machine (`~/git/test-java-spring-boot`) pins **Spring Boot 4.0.4** +
`io.spring.dependency-management` 1.1.7 + Gradle 9.4.0, and those deps (+ H2 2.4.240)
were already in `~/.gradle` (no cold download). The Kotlin skeleton — `kotlin("jvm")`
+ `plugin.spring` + `plugin.jpa` all 2.1.0, Spring Boot 4.0.4 — builds **green on
JDK 25.0.2**: a `@SpringBootTest` context-load smoke test boots the full context
(Hikari pool + JPA EntityManagerFactory) and passes. So the toolchain combo is
confirmed; the skeleton itself is the $0 proof.

## Status / next
- ✅ `$0`: skeleton builds standalone; `setup_workspace` generalized (TDD red→green,
  `golden-repo` still resolves); fixture wires (wiring scan + corpus check green);
  full harness self-tests 22/22.
- ⏭️ **paid:** `run_all.sh developer withdraw-money-spring` (opus + a real Spring
  build, minutes, ~$1–4) — deferred until the org spend limit clears, same as the
  pending finding-11 developer/pipeline re-runs. Optionally a pipeline-kind v2
  fixture later, to run the full `/run-pipeline` on the slice.
