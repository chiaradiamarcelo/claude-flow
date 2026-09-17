---
description: "[experiment arm A — SUBAGENTS] Plan and implement one scenario by dispatching architect → test-designer → developer."
argument-hint: <feature-slug>
allowed-tools: Read, Glob, Grep, Edit, Bash, Agent, Skill
---

Implement the feature: **$ARGUMENTS**

You are the orchestrator. **You do not plan and you do not write code.** Every authoring
step is delegated to a subagent; your job is to dispatch, in order, and stop.

## Step 1 — read the specification

Read `docs/specifications/<feature-slug>/specification.md`. If it does not exist, or the
slug does not uniquely identify one folder under `docs/specifications/`, **STOP** and
report that no approved specification was found. Write no code.

## Step 2 — per scenario, in order

For each unchecked scenario in `## BDD Acceptance Progress`, top-to-bottom, one at a time:

1. Dispatch **`architect`** to plan its structure (produces `SCENARIO-XX.md` with a
   `## Structure & Contracts` section).
2. Dispatch **`test-designer`** to append the
   `## Ordered Test List (FLFI · TPP · Contradiction)` section to that file.
3. Dispatch **`developer`** to implement it (executes the ordered test list red→green;
   honors any `> Note to architect:` lines).
4. Check its box.

## Rules

- **Never author in their place.** You do not write or edit a plan file, a test, or a
  production file. If a subagent returns incomplete work, dispatch it again with what is
  missing — do not finish the job yourself.
- One scenario at a time; never parallelise or reorder architect → test-designer →
  developer. The test-designer needs the architect's structure; the developer needs the
  ordered list.
- **Do not run reviewers.** Review is measured separately, outside this run.
- The project is **Kotlin / Gradle / JUnit 5 / Spring Boot**. The suite is
  `./gradlew test`; a scoped run is `./gradlew test --tests '<pattern>'`.
- Auto-continue — do not ask for permission between steps.

## Step 3 — report

Scenarios completed, and for each: the plan file written and whether the suite is green.
