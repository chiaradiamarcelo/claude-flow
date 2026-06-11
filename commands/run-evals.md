---
description: Run the eval corpus for a pipeline agent (opt-in, diff-scoped). Plans which fixtures actually changed, dispatches only those in a fresh process, and grades with the deterministic model-free grader.
argument-hint: <agent-name, e.g. test-reviewer | --all>
allowed-tools: Read, Glob, Bash, Agent
---

Run evals for: **$ARGUMENTS**

The corpus lives at `~/.claude/evals/<agent>/`. This command is **opt-in** — it
is the *only* trigger for the paid live gate; nothing runs it automatically. It
is also **diff-scoped + cached**: it only dispatches fixtures whose fingerprint
(agent definition + the skills it `@`-references + the fixture input + expected)
has changed since the last green run. Unchanged fixtures cost **zero tokens**.

## Step 0: Resolve which agents to run

- A named agent (e.g. `test-reviewer`) → just that one.
- `--all` or no argument → every agent under `~/.claude/evals/*/`.
- To scope to what you just edited, ask the grader:

```bash
python3 ~/.claude/evals/eval_grade.py --changed-agents
```

Run evals only for the agents it prints. If it prints nothing, there is nothing
to test — stop.

For each resolved `<agent>`:

## Step 1: Structural pre-check (free, no model)

```bash
python3 ~/.claude/evals/eval_grade.py --evals-dir ~/.claude/evals/<agent> --check-corpus
```

If it fails, the corpus is malformed — stop and report; don't spend tokens.

## Step 2: Plan — what actually needs running (free, no model)

```bash
python3 ~/.claude/evals/eval_grade.py --evals-dir ~/.claude/evals/<agent> --plan
```

This prints `RUN` / `CACHED` per fixture. **If 0 fixtures are RUN**, skip
Steps 3–4 entirely: jump to Step 5 (the grader replays cached passes for free)
and report. Only the `RUN` fixtures proceed to dispatch.

## Step 3: Dispatch the RUN fixtures — in a FRESH process

**Do not use the in-session `Agent` tool.** Claude Code caches an agent's
definition at first use in a session, so an `Agent` dispatch tests a *stale*
copy — an edit you just made to `Agent.md` will not be reflected. Evals must run
the agent in a **fresh process**, which loads the current definition:

```bash
claude -p "Review the file(s) under <abs path to fixture>/input/. \
Read them directly with the Read tool. Return ONLY your machine-first JSON verdict." \
  --agent <agent>
```

One fresh process per **RUN** fixture (via Bash; run them in parallel). Do NOT
review the files yourself — only orchestrate.

## Step 4: Parse verdicts → actuals.json

Machine-first reviewers return **a single JSON object as their entire output**
(optionally wrapped in one ```json fence). Strip a surrounding fence if present,
then `JSON.parse`. Assemble **only the RUN fixtures** (cached ones are filled in
by the grader):

```json
{
  "<fixture-stem>": {
    "agents": {
      "<agent>": { "status": "...", "issues": [{ "severity": "...", "message": "..." }] }
    }
  }
}
```

If a fixture's output does **not** parse as a JSON object (e.g. the agent emitted
prose — a non-machine-first agent), record that fixture's agent as `{}`. The
grader fails it with "no machine-readable verdict" — the correct RED for an
un-migrated agent. Write the object to `/tmp/<agent>-actuals.json`.

## Step 5: Grade + update the cache (deterministic, model-free)

```bash
python3 ~/.claude/evals/eval_grade.py \
  --evals-dir ~/.claude/evals/<agent> \
  --actuals /tmp/<agent>-actuals.json \
  --write-cache
```

The grader grades the RUN fixtures fresh, replays CACHED passes, and (with
`--write-cache`) records the fingerprint of every freshly-graded pair so the
next run can skip it. Add `--baseline ~/.claude/evals/<agent>/baseline.json` if a
baseline exists — then only **regressions** red-line the run.

## Step 6: Report

Relay the grader's verdict (`PASS` / `CACHED` / `FAIL` / `REGRESSION`). For any
FAIL, show the fixture, its `expected.json`, and the agent's actual verdict so
the gap is debuggable.
