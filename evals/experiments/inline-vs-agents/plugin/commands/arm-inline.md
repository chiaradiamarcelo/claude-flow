---
description: "[experiment arm B — INLINE] Plan and implement one scenario inline in this session, spawning nothing."
argument-hint: <feature-slug>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Skill
---

Implement the feature: **$ARGUMENTS**

You plan and you implement, **inline, in this session**. You spawn nothing.

## Step 1 — read the specification

Read `docs/specifications/<feature-slug>/specification.md`. If it does not exist, or the
slug does not uniquely identify one folder under `docs/specifications/`, **STOP** and
report that no approved specification was found. Write no code.

## Step 2 — load the convention skills once, now

Load these **once, for the whole run** — never again, whatever phase you are in:

- `clean-architecture`
- `testing`
- `comments`
- `cqrs` if any scenario adds a port or a read-side query
- `api-conventions` if any scenario adds or changes an HTTP endpoint

Then load `inline-plan` and `inline-implement` once as well — they are the phase
procedures. Re-loading any of these is the cost this arm exists to avoid.

## Step 3 — per scenario, in order

For each unchecked scenario in `## BDD Acceptance Progress`, top-to-bottom, one at a time:

1. Follow `inline-plan` for that scenario — it writes `SCENARIO-XX.md` with both
   `## Structure & Contracts` and `## Ordered Test List (FLFI · TPP · Contradiction)`.
2. Follow `inline-implement` for that scenario — it executes the ordered test list
   red→green.
3. Check its box.

Never interleave two scenarios' planning or red/green cycles.

## Rules

- **Never dispatch a subagent.** No `architect`, no `test-designer`, no `developer`, no
  general-purpose agent. That is the whole point of this arm.
- **Do not run reviewers.** Review is measured separately, outside this run.
- The project is **Kotlin / Gradle / JUnit 5 / Spring Boot**. The suite is
  `./gradlew test`; a scoped run is `./gradlew test --tests '<pattern>'`.
- Auto-continue — do not ask for permission between steps.

## Step 4 — report

Scenarios completed, and for each: the plan file written and whether the suite is green.
