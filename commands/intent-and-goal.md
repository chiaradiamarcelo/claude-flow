---
description: Entry point for feature work. Refine the intent and goal, generate Gherkin scenarios with IDs, create the Source of Truth (SoT) specification file, then hand off to /run-pipeline to implement it.
argument-hint: <brief-description-of-feature>
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent, Skill
---

Refine the intent and goal for: **$ARGUMENTS**

## Phase 1: Intent & Goal Refinement

1. Ask the user clarifying questions to understand the "Why" and the "Who" behind the request.
2. Define the **Primary Goal** (the main business value).
3. Identify **Secondary Goals** or constraints (security, performance, audit, etc.).
4. Summarize the refined intent and ask: "Does this capture it correctly? I'll move on to proposing scenarios."

## Phase 2: Scenario Generation

Once the intent is confirmed, automatically:

1. Read any existing domain models and use cases to reuse the project's
   ubiquitous language and avoid duplicating behavior that already exists.
2. Draft Gherkin scenarios with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …).
3. **Check the draft against every rule before showing it** — see *Gap check* below.
4. Present the scenarios **together with** anything the check turned up: each undriven
   rule, each ambiguity, and for a gap the smallest scenario that would close it.
5. Ask which gaps to close and which to accept as-is. Don't add scenarios yourself — a
   gap the user knowingly accepts is a decision; one nobody mentioned is an accident.
6. Iterate — add, remove, or refine scenarios as needed.
7. Wait for explicit user approval before proceeding to Phase 3.

### Gap check (step 3)

Stop generating and read what you drafted **adversarially, against the rules rather than
the scenarios**. Take every rule in turn, including the ones that look obviously covered:

> **What is the laziest implementation that passes all of these scenarios while
> violating this rule?**

Name one and the rule is undriven. Propose the smallest scenario that would go red
against it — a concrete `Given/When/Then`, not a description of one.

This is **not** the same as asking whether a rule is *ambiguous*. A rule can be perfectly
clear and still have nothing that falsifies it: *"no two accounts share one"* is
unmistakable, and a scenario set can leave it entirely undriven. Flag ambiguities too —
places the rules permit two readings and an implementer will silently pick one (status
codes, precision, ordering ties, an operation naming the same entity twice) — but count
them separately.

Four traps, each of which has produced a shipped defect:

- **A `Given` that presupposes its own rule** — "Given the bank has no account ACC-001"
  asserts uniqueness instead of exercising a collision.
- **A refusal that happens before the mechanism** — scenarios refused on their merits
  never reach the store, so they cannot carry a rule about the store failing.
- **Half a rule** — "as one change, *or not at all*" needs a scenario where the second leg
  fails; no happy path falsifies the second clause, however many `Then`s it has.
- **A false all-clear.** Never write that a rule is covered without naming the mutant the
  scenarios kill. Certifying absent coverage is worse than silence. Boundaries are where
  it happens: "refused when the balance is insufficient" does not cover withdrawing
  *exactly* the balance, and `<` versus `<=` survives.

Record each accepted gap in the specification's `## Business Rules & Invariants` as a note
on the rule — *"no scenario drives this; accepted at refinement"* — so the next reader
finds the hole labelled rather than discovering it in production.

### Scenario format

```gherkin
Scenario: <clear description>
  Given <precondition>
  When <action>
  Then <expected outcome>
```

### What to cover

- **Happy path** — primary success case first.
- **Empty state** — no data, no matches, no candidates.
- **Edge cases** — boundaries, thresholds, equal values, min/max limits.
- **Error scenarios** — invalid input, dependency unavailable, malformed data.

### Scenario rules

- Use business-domain language; avoid generic CRUD wording.
- One behavior per scenario.
- Reuse existing domain objects when possible.
- Do not suggest implementation details or architecture in this phase.

## Phase 3: SoT Creation

Upon approval, create a folder at `docs/specifications/<feature-slug>/` and write the specification file inside it.

### Folder structure

```
docs/specifications/<feature-slug>/
  specification.md          # SoT — intent, rules, scenarios, progress
  SCENARIO-01.md            # Created later by the architect agent
  SCENARIO-02.md            # Created later by the architect agent
```

Only create `specification.md` in this phase. Scenario plan files are created by the architect agent.

## Phase 4: Hand off to execution

Once `specification.md` is written, immediately run `/run-pipeline <feature-slug>`.
Do not implement anything yourself.

### Specification Template

```markdown
# Specification: <Feature Name>

## Intent & Goal

**Primary Goal**: <main business value>

**Out of Scope**: <explicitly excluded concerns>

**Business Rules**: <rules and constraints identified in Phase 1>

## Business Rules & Invariants
- Rule 1: ...

---

## Scenarios (Gherkin)
<Approved scenarios from Phase 2>

---

## BDD Acceptance Progress
- [ ] SCENARIO-01: <Title>
- [ ] SCENARIO-02: <Title>

---

## Follow-ups
<Empty at creation. `/run-pipeline` records here anything it left unfixed — a deferred
review finding, or a defect a developer reported rather than fixed — each with its reason.>
```
