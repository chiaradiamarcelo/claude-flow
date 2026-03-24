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

Check if `.claude/review-triggers.json` exists in the project root. If it does, read it and override triggers for matching reviewer names. If it doesn't exist, skip this step.

## Step 4: Filter by relevance

For each reviewer, check if ANY target file matches ANY of its `triggers` glob patterns (after overrides). Skip reviewers with no matching files.

## Step 5: Launch relevant reviewers in parallel

Spawn all matching reviewers in a **single message** using the `Agent` tool:

```
Agent(subagent_type="<name>", prompt="Review the code in this project. Focus on files under <path>.")
```

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
FAIL if any VIOLATIONS, WARNINGS, or SUGGESTIONS exist. PASS only when all sections are empty.
```
