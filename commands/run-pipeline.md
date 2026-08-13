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

When you later dispatch `architect`, `test-designer`, or `developer`, append to
that agent's invocation prompt:

> Project skills — invoke the `Skill` tool to load each of these at the start, in addition to your core skills: `<comma-separated list>`

Only append the line for an agent that has a non-empty entry. Reviewers are
dispatched by `/run-reviewers`, not here — it reads `agentSkills` and injects
into reviewer prompts itself (see its Step 3b), so do nothing extra for reviewers.

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
5. **Commit the scenario's work** (`git add -A && git commit`) with the scenario ID in the message. A green scenario is a checkpoint; leaving a whole feature uncommitted across hours puts every earlier scenario at the mercy of the next agent's `git` command.

**After all scenarios are implemented:**
1. Run **`/run-reviewers`** (no arguments).
2. **Triage the findings before dispatching any fix**, in this order:
   - **Every VIOLATION is fixed.** No exceptions, no deferrals.
   - **Then warnings and suggestions, most-consequential first** — anything that can lose or corrupt stored data, break an invariant the specification names, or mislead a reader about what the code does, ranks above style and structure.
3. Run **`developer`** in fix mode with the triaged findings, highest severity first.
4. Re-run **`/run-reviewers`**. Repeat from step 2 — **at most 2 fix rounds in total**.
5. **Record everything still unfixed** in the specification's `## Follow-ups`, each with the reason it was deferred. Include any defect a `developer` *reported rather than fixed*, in either mode — those arrive in its final message and are lost when the session ends unless you write them down. A deferral on the record is a decision; an unfixed finding that was never reached is an accident.
6. **If any VIOLATION remains unfixed, say so as the headline of your final report** — not as a footnote. An unfixed violation is the single most important thing the run has to tell the reader.

**Rules:**
- One scenario at a time. Never run architect / test-designer / developer in parallel or batched, and always in that order — the test-designer needs the architect's `## Structure & Contracts` section, and the developer needs the test-designer's ordered list.
- Never skip `/run-reviewers`.
- Auto-continue — do not ask for permission between steps.
