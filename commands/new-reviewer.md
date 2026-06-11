---
description: Creates a new reviewer agent with the correct frontmatter and structure. Asks clarifying questions, then generates the agent file.
argument-hint: <optional-reviewer-name>
allowed-tools: Read, Write, Edit, Glob, AskUserQuestion
---

Create a new reviewer agent. If a name was provided: **$ARGUMENTS**

## Step 1: Gather information

Ask the user the following questions (skip any already answered via the argument):

1. **Name**: What should this reviewer be called? (e.g., `presentation-reviewer`, `security-reviewer`). Use kebab-case.
2. **Purpose**: What does this reviewer check for? (e.g., "ensures API response DTOs don't leak domain internals")
3. **Scope**: Which files should trigger this reviewer? Ask for one or more glob patterns. Offer examples based on common patterns:
   - Production code: `**/src/main/**`
   - Test code: `**/src/test/**`, `**/*Test.*`, `**/*IT.*`, `**/*AT.*`
   - API layer: `**/api/**`, `**/controller/**`, `**/dto/**`
   - Domain layer: `**/domain/**`
   - Infrastructure: `**/infrastructure/**`
   - Config files: `**/*.yml`, `**/*.yaml`, `**/*.properties`
   - Frontend: `**/*.tsx`, `**/*.vue`, `**/*.svelte`
4. **Placement**: Should this be a global reviewer (`~/.claude/agents/`) or project-specific (`.claude/agents/`)? Default to project-specific.
5. **Checklist**: What specific things should it check? Ask the user to describe the rules, conventions, or patterns this reviewer enforces. Probe for triggers of each severity the reviewer emits:
   - `VIOLATION` — a broken rule (must fix)
   - `WARNING` — a should-fix problem that does not break a hard rule
   - `SUGGESTION` — a concrete refinement / nice-to-have
6. **Source of truth**: Do the rules live in a skill (e.g. `skills/<name>/SKILL.md`)? Reviewers should `@`-reference their skill rather than restate it — that's the single-source-of-truth defense against cross-artifact drift. If yes, capture the skill path.
7. **Model**: Which model tier? Default to `sonnet` for reviewers.

## Step 2: Review existing reviewers

Before creating, glob for existing reviewer agents in the target location to avoid duplication. If a similar reviewer exists, ask the user if they want to update it instead.

## Step 3: Generate the agent file

Create the agent at `<placement>/<reviewer-name>/Agent.md` with this structure:

```markdown
---
name: <reviewer-name>
description: <one-line description of what it reviews>
type: reviewer
triggers: [<glob patterns from Step 1>]
tools: Read, Glob, Grep
model: <model>
color: <pick a color not used by existing reviewers>
---

You are a strict <purpose> reviewer for a project following Clean Architecture and TDD.

## Rules (source of truth)

@skills/<skill-name>/SKILL.md  <!-- omit this section if Step 1 found no backing skill -->

## Review procedure

For each file under review:

1. **Read the file.**
2. **Check every rule** (from the skill, if any). Pay special attention to:
   <categories derived from the checklist in Step 1>
3. **Turn each finding into an `issue`** with the right `severity` (see below).

## Output — machine-first JSON (your entire response)

Your **entire output is a single JSON object** — no prose before or after, no
markdown headings, no `<!-- -->` markers. Every reviewer in this pipeline shares
this one contract; do not invent a per-reviewer shape, and never mention who
consumes the output.

```json
{
  "status": "FAIL",
  "issues": [
    { "severity": "VIOLATION", "file": "<file>", "line": 0,
      "message": "<rule name>: <what is wrong> in `<symbol>`" }
  ],
  "summary": "<one sentence: the headline finding>"
}
```

Field rules:

- **`severity`** — classify each finding. Enumerate what triggers each level
  (when the rules live in a skill, frame these as *representative examples* and
  keep the skill as the source of truth):

  `VIOLATION` — a **broken rule** (must fix):
  <violation triggers derived from the checklist>

  `WARNING` — a **should-fix** problem that does not break a hard rule:
  <warning triggers derived from the checklist>

  `SUGGESTION` — a **concrete refinement** / nice-to-have:
  <suggestion triggers derived from the checklist>

- **`status`** — derived from the issues:
  - `FAIL` — one or more issues of **any** severity.
  - `PASS` — no issues at all.
- **`issues`** — one entry per finding. `message` names the rule and the symbol
  it occurs in. `file`/`line` locate it.
- **`summary`** — a single sentence. Strengths, if worth noting, go here — not
  as issues.

Emit nothing but this JSON object.
```

## Step 4: Project trigger overrides

If the reviewer is **global** but the user mentions it will be used in projects with different file conventions (e.g., TypeScript uses `*.spec.ts` instead of `*Test.*`), inform them they can override triggers per project by adding an entry to `.claude/review-triggers.json`:

```json
{
  "<reviewer-name>": ["**/*.spec.ts", "**/*.test.ts"]
}
```

The review-gate reads this file and replaces the agent's frontmatter triggers with the override. Only reviewers that need different patterns need an entry.

## Step 5: Scaffold a detection fixture (eval parity)

A reviewer is only trustworthy if a test pins its behavior. Offer to scaffold one detection fixture under `evals/<reviewer-name>/fixtures/<stem>/`:

- `input/<file>` — a frozen artifact that **breaks one rule** the reviewer must catch.
- `expected.json` — tolerant, non-determinism-safe facts (never exact prose):

```json
{
  "fixture": "<stem>",
  "applicableAgents": ["<reviewer-name>"],
  "agents": {
    "<reviewer-name>": {
      "expectedStatus": "FAIL",
      "severities": { "VIOLATION": { "min": 1 } },
      "mustMention": ["<robust substring the message will contain>"]
    }
  }
}
```

Verify with `./evals/run_all.sh --agents` (free structural check runs first; the live grade dispatches the new reviewer in a fresh `claude -p` and fingerprint-caches the result). See `evals/README.md` for the full strategy.

## Step 6: Confirm

Show the user the generated file path and a summary of what the reviewer will check and when it triggers. Remind them it is registered in the reviewer table and will be picked up by the `review-gate` on the next scenario run.
