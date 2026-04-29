---
description: Refine the intent and goal for a new feature, generate Gherkin scenarios with IDs, and create a Source of Truth (SoT) specification file.
argument-hint: <brief-description-of-feature>
allowed-tools: Read, Write, Glob, Grep, Skill
---

Refine the intent and goal for: **$ARGUMENTS**

## Phase 1: Intent & Goal Refinement

1. Ask the user clarifying questions to understand the "Why" and the "Who" behind the request.
2. Define the **Primary Goal** (the main business value).
3. Identify **Secondary Goals** or constraints (security, performance, audit, etc.).
4. Summarize the refined intent and ask: "Does this capture it correctly? I'll move on to proposing scenarios."

## Phase 2: Scenario Generation

Once the intent is confirmed, automatically:

1. **Invoke the `clean-architecture` skill** to load folder structure and conventions.
2. Read existing domain models in the domain source directory.
3. Read existing use cases in the use case source directory.
4. Propose Gherkin scenarios with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …).
5. Ask clarifying questions if business rules are ambiguous.
6. Iterate with the user — add, remove, or refine scenarios as needed.
7. Wait for explicit user approval before proceeding to Phase 3.

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
```
