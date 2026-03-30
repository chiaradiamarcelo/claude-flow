---
name: adr
description: Create an Architecture Decision Record (ADR) in docs/adr/. Describe the decision and context, or have a conversation to refine it.
argument-hint: <decision-title-or-description>
allowed-tools: Read, Write, Glob, Bash
---

Create an Architecture Decision Record for: **$ARGUMENTS**

## Process

1. **Find next number**: Scan `docs/adr/` for existing ADRs and determine the next sequential number (zero-padded to 3 digits).
2. **Gather context**: If the argument is a clear decision with enough context, proceed. If it's vague or missing the "why", ask clarifying questions before writing — an ADR without a clear rationale is worthless.
3. **Write the ADR** using the template below.
4. **File name**: `docs/adr/NNN-slug.md` where `slug` is a lowercase, hyphenated summary (max 5 words).

## Template

```markdown
# ADR-NNN: Title

## Status

Accepted

## Context

Why this decision came up. What forces are at play — constraints, requirements, trade-offs.
Keep it concise but complete enough that a newcomer understands the problem.

## Decision

What we decided. State it as a fact, not a proposal.

## Consequences

What follows — both positive and negative. Be honest about trade-offs.
Use bullet points prefixed with **Positive:**, **Negative:**, or **Trade-off:**.
```

## Rules

- One decision per ADR. If there are multiple decisions, create multiple ADRs.
- Write in plain language. No jargon without explanation.
- The "Context" section must explain *why* — not just *what*.
- The "Consequences" section must include at least one negative or trade-off. Every decision has a cost.
- Keep each section concise — aim for 2-5 sentences in Context and Decision, 3-6 bullets in Consequences.
- If `docs/adr/` doesn't exist, create it.
- Don't modify existing ADRs unless explicitly asked. To reverse a decision, create a new ADR that supersedes the old one and update the old one's status to `Superseded by ADR-NNN`.
