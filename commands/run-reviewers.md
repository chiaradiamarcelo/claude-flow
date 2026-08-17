---
description: Run reviewers on specific paths or on changed files. Used by the pipeline (no args = git diff) and for ad-hoc reviews (with paths).
argument-hint: <optional paths, e.g. src/main, src/test>
allowed-tools: Read, Glob, Grep, Bash, Agent
---

Run reviewers on: **$ARGUMENTS**

## Step 1: List target files

**If paths were provided** (one or more comma-separated, e.g., `src/main, src/test`):

Split on commas, trim whitespace, and use the `Glob` tool to list all files under each path:

```
Glob(pattern="**/*", path="<path1>")
Glob(pattern="**/*", path="<path2>")
```

Run all globs in parallel (single message).

**If no paths were provided** (pipeline mode), detect changed files via git:

```bash
git diff --name-only HEAD 2>/dev/null
git diff --name-only --cached 2>/dev/null
git ls-files --others --exclude-standard 2>/dev/null
git diff --name-only HEAD~1 2>/dev/null
```

Combine all results into a deduplicated list. If all commands return empty, fall back to `git ls-files`.

Collect all file paths into a single deduplicated list.

## Step 2: Discover reviewer agents

Use the `Grep` tool to find all agents with `type: reviewer` in their frontmatter. Run both searches in parallel:

```
Grep(pattern="type: reviewer", path="/Users/mchiaradia/.claude/agents/", glob="**/Agent.md")
Grep(pattern="type: reviewer", path=".claude/agents/", glob="**/Agent.md")
```

For each matched file, use the `Read` tool to read only the first 10 lines (the frontmatter). Check that `type: reviewer` appears **inside the YAML frontmatter block** (between the `---` markers), not in the body text. Discard any file where it only appears in the body.

From each valid reviewer's frontmatter, extract `name` and `triggers`. Read all matched files in parallel.

## Step 3: Apply project trigger overrides

Check if `.claude/pipeline.json` exists in the project root. If it does, read it and use its `reviewers` object (an optional top-level key mapping reviewer `name` → glob array) to **override** triggers for matching reviewer names. Reviewers not named in `reviewers` keep their frontmatter triggers. If the file or the `reviewers` key is absent, skip this step.

## Step 3b: Resolve project skill injection

From the same `.claude/pipeline.json`, read its optional `agentSkills` object (a map of agent `name` → array of skill names). For each reviewer that has a non-empty entry, remember its extra skills — you will inject them at dispatch (Step 5). These are **additive**: a reviewer always loads its own core skills, plus any listed here. If the file or the `agentSkills` key is absent, no skills are injected. (Handle only the reviewers you dispatch — entries for any other agent are not yours to apply.)

## Step 4: Filter by relevance

For each reviewer, check if ANY target file matches ANY of its `triggers` glob patterns (after overrides). Skip reviewers with no matching files.

**Matching is purely glob-based — mechanical, not topical.** A reviewer fires **if and only if** at least one target file *path* matches at least one of its trigger globs. Do **not** fire a reviewer because the changeset *seems* related to its domain, because a file's *content or topic* looks relevant, or "just in case." Only a glob path match counts.

- A reviewer with **zero** matching files goes in `skips`, never `fires`.
- A changeset that matches **no** reviewer (e.g. a docs-only change: `README.md`, `docs/**/*.md`) yields an **empty** `fires:` line with every reviewer in `skips`. That is a valid, expected outcome — not an error, and not a reason to fire a reviewer anyway.

### Dry run (routing assertion — used by the live test)

If `--dry-run` appears in **$ARGUMENTS**, stop after this step: do NOT dispatch
(Step 5) or consolidate (Step 6). Print the routing decision, then the skill
injection each fired reviewer would receive, in exactly this format
(machine-greppable), then stop:

```
ROUTING
fires: <comma-separated names of reviewers with >=1 matched file, sorted>
skips: <comma-separated names of discovered reviewers with no match, sorted>

SKILLS
<fired-reviewer-name>: <comma-separated project skills from Step 3b, or (none)>

SCOPE
<fired-reviewer-name>: <comma-separated matched file paths, sorted>
```

The `SCOPE` block is the file list Step 5 would pass to that reviewer — every
target file matching that reviewer's triggers, and nothing else. One line per
**fired** reviewer. Print the paths in full; never abbreviate the list or write
"and N more", because a scope that is silently narrower than it claims is the
defect this block exists to expose.

List one `SKILLS` line per **fired** reviewer (a skipped reviewer is never
dispatched, so it receives nothing); use `(none)` for a fired reviewer with no
`agentSkills` entry. List **only** the injected (project) skills — never the
reviewer's core skills. This exercises file detection (Step 1) → reviewer
discovery (Step 2) → trigger overrides (Step 3) → skill resolution (Step 3b) →
routing (Step 4) end-to-end, without spending tokens dispatching reviewers.

## Step 5: Launch relevant reviewers in parallel

Spawn all matching reviewers in a **single message** using the `Agent` tool. **Pass each
reviewer the files that matched *its own* triggers in Step 4** — not just a path:

```
Agent(subagent_type="<name>", prompt="Review these <N> files, all of them:
<one matched path per line>

This list is your scope. Read every file on it. If you cannot review them all, say which ones you did not read and how many.")
```

Step 4 already computed this list per reviewer; discarding it and passing a bare directory is
what lets a reviewer quietly substitute a familiar subset for its actual scope. A bare path also
gives it nothing to be held to — with the list in the prompt, an unreviewed file is visible.

If the list is long (a whole-tree ad-hoc run), **pass it anyway** — paths are cheap, and the
count is the point. Never trim it silently to keep the prompt small.

For a reviewer with a non-empty `agentSkills` entry (from Step 3b), append to its prompt:

> Project skills — before reviewing, invoke the `Skill` tool to load each of these, and apply their rules **in addition to** your own: `<comma-separated list>`

Do NOT review code yourself — only orchestrate.

## Step 6: Report

Consolidate all findings into a single report:

```
## Ad-hoc Review Report

### Target
<path or "all files">

### Triggered reviewers
- <name>: triggered by <matched files>

### Skipped reviewers
- <name>: no files matched triggers

### VIOLATIONS (must fix)
<all violations, prefixed with reviewer name>

### WARNINGS (should fix)
<all warnings, prefixed with reviewer name>

### SUGGESTIONS
<all suggestions, prefixed with reviewer name>

### GOOD PRACTICES
<positive notes>

### Verdict: PASS | FAIL
**FAIL if and only if there is at least one VIOLATION.** Warnings and suggestions are
reported in full and do **not** fail the review — whoever ran this command decides
which of them to act on.
```
