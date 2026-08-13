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
2. Propose Gherkin scenarios with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …).
3. Ask clarifying questions if business rules are ambiguous.
4. Iterate with the user — add, remove, or refine scenarios as needed.
5. Wait for explicit user approval before proceeding to Phase 3.

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

## Phase 2b: Gap review (before the SoT is written)

Once the user is happy with the scenarios, run the **`spec-gap-reviewer`** agent on the
draft rules and scenarios. It answers one question per business rule: *is there a
scenario that would fail if this rule were violated?*

Report its findings to the user in full, then ask which gaps they want to close with a
new scenario and which they accept as-is. **Do not add scenarios yourself, and do not
proceed to Phase 3 until they have answered.** A gap the user knowingly accepts is a
decision; one nobody mentioned is an accident.

Record every accepted gap in the specification's `## Business Rules & Invariants` as a
note on the rule — *"no scenario drives this; accepted at refinement"* — so the next
reader finds the hole labelled rather than discovering it in production.

Why this phase exists, measured: a feature shipped a rule stating account numbers were
unique, with no scenario exercising a collision. Four separate pipeline runs all
produced code where re-opening an existing account silently destroyed its movement
history, and all of them passed every scenario. The review found it in 2 minutes for
~10k tokens, along with two further undriven rules the author had missed. See
[finding 16](../docs/findings/16-layered-pipeline-rejected.md).

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
