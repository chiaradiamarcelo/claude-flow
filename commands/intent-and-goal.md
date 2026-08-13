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
2. **Ask clarifying questions — a lot of them.** Grill the user: every rule that admits two
   readings, every condition with an unstated boundary, every outcome that is only implied.
   This is the cheapest point in the flow to be wrong, and the only one where asking costs
   nothing.
3. Propose Gherkin scenarios with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …).
4. **Then check every business rule against the scenarios.** For each rule ask: *would any
   scenario fail if this rule were violated?* If none would, the rule is uncovered — go
   back to the user with a question. Three shapes to watch for, each of which has shipped
   a defect:
   - a scenario that **presupposes its own rule** — "Given the bank has no account ACC-001"
     asserts uniqueness instead of exercising a collision, so nothing enforces it;
   - a rule whose **failure path is never reached** — scenarios refused on their merits
     never reach the store, so they cannot carry a rule about the store failing;
   - **half a rule** — "as one change, *or not at all*" needs a scenario where the second
     leg fails; no happy path falsifies the second clause, however many `Then`s it has.
5. Iterate with the user — add, remove, or refine scenarios as needed.
6. Wait for explicit user approval before proceeding to Phase 3.

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
