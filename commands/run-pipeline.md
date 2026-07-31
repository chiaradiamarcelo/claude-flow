---
description: Execute the implementation pipeline for a feature that has an approved SoT specification — runs each scenario (architect → test-designer → developer) one at a time, then reviewers, then a fix-loop.
argument-hint: <feature-slug, e.g. withdraw-money>
allowed-tools: Read, Glob, Grep, Edit, Bash, Agent, Skill
---

Run the implementation pipeline for: **$ARGUMENTS**

## Step 0: Resolve project skill injection

Check if `.claude/pipeline.json` exists in the project root. If it does, read its
optional `agentSkills` object — a map of agent `name` → array of skill names. These
are **additive**: an agent always loads its own core skills (listed in its agent
body), plus any listed here. Never treat this as a replacement, and never drop a
core skill. Agents with no entry are unaffected. If the file or the `agentSkills`
key is absent, no skills are injected.

When you later dispatch `architect`, `test-designer`, or `developer` (and when
`/run-reviewers` dispatches a reviewer), append to that agent's invocation prompt:

> Project skills (load these **in addition to** your core skills): `<comma-separated list>`

Only append the line for an agent that has a non-empty entry.

### Dry run (skill-injection assertion — used by the live test)

If `--dry-run` appears in **$ARGUMENTS**, resolve `agentSkills` as above, print the
resolution in exactly this format (machine-greppable), then **STOP** — do not read
the specification, dispatch any agent, or write code:

```
SKILLS
architect: <comma-separated project skills, or (none)>
test-designer: <…>
developer: <…>
test-reviewer: <…>
```

List one line per agent that appears in `agentSkills`; use `(none)` for an agent
with no injected skills. List **only** the injected (project) skills — never the
agent's core skills.

## Step 1: Run the pipeline

Read `docs/specifications/<feature-slug>/specification.md`. If it doesn't exist
(or no slug uniquely identifies one feature under `docs/specifications/`),
**STOP** and report that no approved specification was found — write no code.

**For each unchecked scenario in `## BDD Acceptance Progress` (top-to-bottom, one at a time):**
1. Run **`architect`** to plan its structure (produces `SCENARIO-XX.md` with a `## Structure & Contracts` section).
2. Run **`test-designer`** to append the `## Ordered Test List (FLFI · TPP · Contradiction)` section to that file.
3. Run **`developer`** to implement it (executes the ordered test list red-green; honors any `> Note to architect:` lines).
4. Check its box.

**After all scenarios are implemented:**
4. Run **`/run-reviewers`** (no arguments).
5. If **FAIL**: run **`developer`** in fix mode with the consolidated VIOLATION + WARNING findings.
6. Run **`/run-reviewers`** again; repeat until PASS or 3 fix rounds.

**Rules:**
- One scenario at a time. Never run architect / test-designer / developer in parallel or batched, and always in that order — the test-designer needs the architect's `## Structure & Contracts` section, and the developer needs the test-designer's ordered list.
- Never skip `/run-reviewers`.
- Auto-continue — do not ask for permission between steps.
