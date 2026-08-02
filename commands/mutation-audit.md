---
description: On-demand, filtered mutation audit — run PIT over target/changed business logic and report only real, actionable surviving mutants. NOT part of /run-pipeline.
argument-hint: <optional paths (default = git-changed files); add --crap for a complexity×coverage report>
allowed-tools: Read, Glob, Grep, Bash
---

Run a filtered mutation audit on: **$ARGUMENTS**

## What this is (and is not)

Runs **mutation testing** on demand and reports only *actionable* surviving mutants — a real
code change no test kills. It is a **deliberate backstop, not a pipeline gate.**

Why not in `/run-pipeline`: the `test-designer` already does mutation analysis *by reasoning*
(the `testing` skill's mutation-question + the `Contradiction` kill-list + TPP forcing minimal
code), so on freshly generated pipeline output this audit almost always reports **nothing** —
wiring it into every run would add latency and noise for a failure mode that isn't occurring.
Measured: [finding 14](../docs/findings/14-mutation-gate-spike.md).

**Reach for it when auditing a suite you did *not* generate:** legacy/inherited tests, a
pre-release confidence check on a critical module, or a suite you distrust. It is slow (CPU) and,
on good output, silent — do not run it as routine development.

## Step 1 — scope

- Paths given → target them. Otherwise → `git diff --name-only` (fall back to `src/main`).
- Audit **framework-free business logic only** — `domain/` + `application/` (or the project's
  equivalent). Skip controllers / JPA adapters / config: mutating framework wiring is slow and
  low-value (finding 14).

## Step 2 — run the mutation tool

Detect the stack.

**JVM / Kotlin (Gradle) → PIT (`pitest`).** Prefer a Gradle **init script** (`--init-script`) so
you don't edit the project's build files. Scope `targetClasses` to the `domain.*`/`application.*`
packages in range and `targetTests` to their unit tests. Toolchain caveats — carried from finding
14 so you don't rediscover them:

- `gradle-pitest-plugin` **≥ 1.19** for Gradle 9.
- Pin PIT's forked JVM to a **plain Temurin JDK** — Android Studio's JBR crashes PIT's coverage
  minion (`Minion exited abnormally / UNKNOWN_ERROR`).
- Compile to **Java-21 bytecode** — PIT's bundled ASM can't read Java 24/25 class files.
- **Spring Boot 4 / JUnit Platform 6**: the pitest-junit5 plugin can't drive JUnit 6 → run PIT
  over a **pure-Kotlin sidecar** holding just the framework-free sources + their JUnit-5 unit
  tests. (The finding-12/13 archive tag `experiment/batch-vs-strict-tdd` has a working
  `oracle/run-oracle.sh` + `pit-sidecar/` to copy from.)

Output: `build/reports/pitest/mutations.xml`.

**TS / JS → Stryker (`@stryker-mutator`).** Not yet templated here — do your best or report that
this stack isn't supported yet.

## Step 3 — FILTER (mandatory) then report

Raw PIT survivors on Kotlin are ~100% noise (`equals`/`hashCode`/`toString` boilerplate + Kotlin
null-check intrinsics — finding 14). **Never report raw survivors.** Run the filter:

```bash
python3 ~/.claude/tools/mutation/classify-survivors.py <dir-containing-mutations.xml>
```

It splits survivors into **junk** (dropped) and **candidate-real** (business-logic gaps). Report
ONLY the candidate-real list, as **advisory** findings:

- **Zero real survivors** → *"Suite is mutation-strong on the audited scope — no actionable
  gaps."* (Expected for pipeline-generated code.)
- **Real survivors** → per survivor: `file:line`, the method, the mutator, and the ask — *"no
  test kills this change; add or strengthen a test that fails when this mutation is applied."*
  Flag that these are **candidates, not certainties** — a survivor can still be an equivalent
  mutant; the reader inspects before writing a test.

**Advisory only — this command never blocks anything.** It produces a report.

## Optional: `--crap`

Complexity × coverage risk. Near-silent on clean-arch code (finding 14) but useful on messy /
legacy code. Needs a JaCoCo XML report (`build/reports/jacoco/test/jacocoTestReport.xml`):

```bash
python3 ~/.claude/tools/mutation/crap.py <jacocoTestReport.xml>
```

Report methods over the CRAP threshold (30) — candidates for more tests or a smaller method.
