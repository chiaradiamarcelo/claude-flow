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

### Scenarios are implemented one at a time, but planned ahead

Only the **developer** writes code, so only the developer must be serial. The
`architect` and `test-designer` read files and write their own plan — they cannot
collide with an implementation in flight. Run them alongside it.

**Steady state — two dispatches per scenario:**

1. **`developer` N ∥ `architect` N+1** in a single message. Wait for both.
2. **`test-designer` N+1** alone.

Then N+1 becomes N and repeat.

**Only the architect looks ahead, and only by one.** The `test-designer` is
deliberately *not* pipelined: it always runs after the predecessor's code exists, so
it sees the real world. That is not a missed optimisation, it is the point —
measured, a deeper schedule that also pipelined the test-designer cut wall-clock 28%
and took red→green from 86% to 64%, with 28% of tests arriving unplanned. The
test-designer's judgement about *which guards are still missing* is what makes rows
arrive red, and it cannot make that judgement against code that has not been written.

The architect can look ahead safely because it plans structure rather than
falsifiability, and because the test-designer re-derives that structure from current
code immediately afterwards — so an architect mis-prediction is caught one step later
by an agent that can see the truth.

**Priming:** `architect` 1 → `test-designer` 1 → steady state.

**Winding down:** when there is no N+1 or N+2 left to plan, dispatch what remains.
Never invent work to fill a slot.

**After each developer returns:**
1. Check the scenario's box.
2. **Commit the scenario's work** (`git add -A && git commit`) with the scenario ID in the message. A green scenario is a checkpoint; leaving a whole feature uncommitted across hours puts every earlier scenario at the mercy of the next agent's `git` command.
3. **If the developer reported a `> Stale plan:` note**, read it before dispatching the next batch. It means a plan was drafted against structure that has since changed. One is normal. Several in a row means the lookahead is too deep for this feature — drop `architect` back to **N+1** and note it in your final report.

**What planning ahead does and does not change:** the architect and test-designer are
now planning against code that **does not exist yet**. They are told to plan against
the earlier scenarios' *plans* as well as the committed code (see their agent
definitions). Do not compensate for this by feeding them extra context; if a plan
comes back wrong, that is the signal this stage exists to measure.

**After all scenarios are implemented:**
1. Run **`/run-reviewers`** (no arguments).
2. **Triage the findings before dispatching any fix**, in this order:
   - **Every VIOLATION is fixed.** No exceptions, no deferrals.
   - **Then warnings and suggestions, most-consequential first** — anything that can lose or corrupt stored data, break an invariant the specification names, or mislead a reader about what the code does, ranks above style and structure.
   - **Then stop at the budget: at most 2 fix rounds.** Everything not fixed is recorded in the specification's `## Follow-ups` with the reason it was deferred. A deferral on the record is a decision; an unfixed finding that was simply never reached is an accident.
3. Run **`developer`** in fix mode with the triaged findings, highest severity first.
4. Re-run **`/run-reviewers`**; repeat until PASS or the budget is spent.
5. **If any VIOLATION remains unfixed when the budget is spent, say so as the headline of your final report** — not as a footnote. An unfixed violation is the single most important thing the run has to tell the reader.

**Rules:**
- **Exactly one `developer` in flight at any time.** Two developers on different scenarios would collide on files, and worse, would destroy the red-arrival property the whole method rests on: a scenario's tests are red only because its predecessor deliberately has not built the thing yet. Concurrency is for planning only.
- **Order within a scenario is still strict** — architect → test-designer → developer. The test-designer needs the `## Structure & Contracts` section; the developer needs the ordered list.
- Never skip `/run-reviewers`.
- Auto-continue — do not ask for permission between steps.
