---
description: Run the review gate on a specific path or the entire project. Use for ad-hoc reviews on legacy code or any folder outside the normal pipeline flow.
argument-hint: <paths, e.g. src/main, src/test>
allowed-tools: Read, Glob, Bash, Agent
---

Run an ad-hoc review on: **$ARGUMENTS**

If no path was provided, review all source files in the project.

## Step 1: List target files

The argument may contain one or more comma-separated paths (e.g., `src/main, src/test`). Split on commas and trim whitespace.

If paths were provided, list all files under each path:

```bash
find <path1> <path2> ... -type f -not -path '*/\.*'
```

If no paths were provided, list all tracked files:

```bash
git ls-files
```

Collect all file paths into a single deduplicated list.

## Step 2: Load reviewer roster

Read both reviewer tables in parallel:

```
Read("/Users/mchiaradia/.claude/reviewers.json")
Read(".claude/reviewers.json")
```

The project table may not exist — that's fine. Merge using the same rules as the review-gate: project entries override global entries with the same name, new names are added.

## Step 3: Filter by relevance

For each reviewer, check if ANY target file matches ANY of its `triggers` glob patterns. Skip reviewers with no matching files.

## Step 4: Launch relevant reviewers in parallel

Spawn all matching reviewers in a **single message** using the `Agent` tool:

```
Agent(subagent_type="<name>", prompt="Review the code in this project. Focus on files under <path>.")
```

Do NOT review code yourself — only orchestrate.

## Step 5: Report

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

### SUGGESTIONS (optional)
<all suggestions, prefixed with reviewer name>

### GOOD PRACTICES
<positive notes>

### Verdict: PASS | FAIL
```
