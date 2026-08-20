---
description: On-demand, filtered mutation audit — run PIT (JVM, Gradle or Maven) or Stryker (TS/JS) over target/changed business logic and report only real, actionable surviving mutants. NOT part of /run-pipeline.
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

- Paths given → target them. Otherwise → `git diff --name-only` (fall back to the project's
  source root — `src/main` on the JVM, `src/` on a TS/JS workspace).
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

**Java / Maven → PIT via `pitest-maven`.** Same tool, same report, different runner. Nothing
above about ASM, the forked JVM or the JUnit-6 sidecar changes; Java also produces *less*
synthetic noise than Kotlin, so the filter has less to do.

```bash
mvn -q org.pitest:pitest-maven:mutationCoverage \
  -DtargetClasses='com.example.domain.*,com.example.application.*' \
  -DtargetTests='com.example.domain.*Test,com.example.application.*Test' \
  -DoutputFormats=XML -DtimestampedReports=false
```

`-DtimestampedReports=false` is what makes the report findable — with timestamps on, each run
lands in a fresh `target/pit-reports/<yyyyMMddHHmm>/`. Output: `target/pit-reports/mutations.xml`.
Prefer `-D` flags over editing the project's `pom.xml`, for the same reason the Gradle path uses
an init script. If the project already configures the plugin, don't fight it — read its
`targetClasses` and narrow with `-DtargetClasses` only.

**TS / JS → Stryker (`@stryker-mutator`).** PIT is JVM-only, so this is a different tool with a
different report format (`mutation-testing-report-schema` JSON) and its own filter.

```bash
npx stryker run --reporters json --mutate 'src/domain/**/*.ts' --mutate 'src/application/**/*.ts'
```

- **Scope with `--mutate`, not with config**, so you don't edit the project's `stryker.conf`.
  Same scope rule as the JVM path: framework-free business logic only.
- **`--concurrency` defaults to CPUs−1 and Stryker re-runs the suite per mutant.** On a large
  scope this is the slowest thing in this command; narrow the glob before widening it.
- **Set `ignoreStatic: true`** if the project's config allows it. Stryker's own docs flag static
  mutants as unreliable — the mutated module is evaluated once at load, so the result depends on
  test ordering. The filter buckets them separately either way, never as findings.
- A `--reporters json` run writes `reports/mutation/mutation.json` unless the config says
  otherwise.

## Step 3 — FILTER (mandatory) then report

Raw PIT survivors on Kotlin are ~100% noise (`equals`/`hashCode`/`toString` boilerplate + Kotlin
null-check intrinsics — finding 14). **Never report raw survivors.** Run the filter for the stack
you ran:

```bash
# PIT (JVM/Kotlin, Gradle or Maven) — takes the report dir or the file itself
python3 ~/.claude/tools/mutation/classify-survivors.py build/reports/pitest/mutations.xml

# Stryker (TS/JS)
python3 ~/.claude/tools/mutation/classify-stryker.py reports/mutation/mutation.json
```

Both split survivors into **junk** (dropped) and **candidate-real** (business-logic gaps). Report
ONLY the candidate-real list, as **advisory** findings.

Both also separate two buckets that are **not** weak-test findings — do not report them as one:

- **uncovered** (`NoCoverage`) — no test executes the line. That is a coverage gap; the ask is a
  test that runs the code at all, not a stronger assertion. Say so, and say it first: auditing
  assertions on unexecuted code is meaningless.
- **static** (Stryker only) — its own unreliable class (above). Mention the count and the
  `ignoreStatic` fix; do not turn them into findings.

On the JVM side, `TIMED_OUT` / `MEMORY_ERROR` / `RUN_ERROR` are counted as **killed**, as PIT's
own mutation score counts them. On coroutine code this matters: a negated conditional inside a
collector hangs far more often than it fails, so counting timeouts as survivors inflates the
figure systematically rather than marginally.

**The Stryker junk rules are less trustworthy than PIT's.** PIT's were derived from a measured
run (finding 14); no equivalent Stryker run exists yet, so one of its three rules (log-message
string literals) is a stated prior, not a measurement. On the first real audit of a TS codebase,
re-run with `--show-junk` and check what it dropped before trusting the filtered number — and
record what you found, so the next audit doesn't have to.

Report per finding:

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
