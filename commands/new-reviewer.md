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
5. **Checklist**: What specific things should it check? Ask the user to describe the rules, conventions, or patterns this reviewer enforces. Probe for:
   - What violations look like (must fix)
   - What warnings look like (should fix)
   - What good practices look like (positive notes)
6. **Model**: Which model tier? Default to `sonnet` for reviewers.

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

## What to check

<Generated from the checklist in Step 1 — organized as numbered sections>

## Output format

Report findings grouped by severity:

**VIOLATIONS** (must fix):
<categories derived from the checklist>

**WARNINGS** (should fix):
<categories derived from the checklist>

**GOOD PRACTICES**:
- Positive notes for clean patterns observed
```

## Step 4: Project trigger overrides

If the reviewer is **global** but the user mentions it will be used in projects with different file conventions (e.g., TypeScript uses `*.spec.ts` instead of `*Test.*`), inform them they can override triggers per project by adding an entry to `.claude/review-triggers.json`:

```json
{
  "<reviewer-name>": ["**/*.spec.ts", "**/*.test.ts"]
}
```

The review-gate reads this file and replaces the agent's frontmatter triggers with the override. Only reviewers that need different patterns need an entry.

## Step 6: Confirm

Show the user the generated file path and a summary of what the reviewer will check and when it triggers. Remind them it is registered in the reviewer table and will be picked up by the `review-gate` on the next scenario run.
