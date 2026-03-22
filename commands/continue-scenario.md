---
description: Find the next unchecked scenario in a specification and run the pipeline for it. Used by the run-scenarios script.
argument-hint: <spec-folder, e.g. docs/specifications/deposit-money>
allowed-tools: Read, Glob, Grep, Bash, Agent, Skill
---

Continue with the next scenario from: **$ARGUMENTS**

## Step 1: Find the next scenario

Read `$ARGUMENTS/specification.md`. Find the `## BDD Acceptance Progress` section. Identify the first unchecked scenario (`- [ ] SCENARIO-XX`).

If all scenarios are checked (`- [x]`), respond with exactly: "All scenarios complete." and stop.

## Step 2: Run the pipeline

Proceed with the identified scenario following the CLAUDE.md workflow rules (architect → developer → /run-reviewers → fix if needed).
