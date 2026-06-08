---
description: Run the eval corpus for a pipeline agent — dispatch it against each fixture, extract its machine-readable verdict, and grade with the deterministic model-free grader.
argument-hint: <agent-name, e.g. test-reviewer>
allowed-tools: Read, Glob, Bash, Agent
---

Run evals for agent: **$ARGUMENTS**

The corpus lives at `~/.claude/evals/<agent>/`. This command is the **live gate**
(it spends tokens dispatching the agent). For the free structural gate, run:

```bash
python3 ~/.claude/evals/eval_grade.py --evals-dir ~/.claude/evals/<agent> --check-corpus
```

## Step 1: Structural pre-check (free)

Run the corpus check first. If it fails, stop and report — the corpus is
malformed, no point spending tokens:

```bash
python3 ~/.claude/evals/eval_grade.py --evals-dir ~/.claude/evals/<agent> --check-corpus
```

## Step 2: List fixtures

```
Glob(pattern="*/expected.json", path="~/.claude/evals/<agent>/fixtures")
```

Each match is a fixture; its sibling `input/` holds the artifact(s) to feed the
agent.

## Step 3: Dispatch the agent on each fixture (parallel)

For each fixture, spawn the target agent in a **single message** (one `Agent`
call per fixture), pointing it at the fixture's `input/` files:

```
Agent(subagent_type="<agent>",
      prompt="Review the test file(s) under <abs path to fixture>/input/. "
             "Read them directly. Emit your full report and the required "
             "<!-- EVAL-VERDICT --> json block.")
```

Do NOT review the files yourself — only orchestrate.

## Step 4: Extract verdicts → actuals.json

From each agent's returned text, extract the single fenced json block that
follows the `<!-- EVAL-VERDICT -->` marker. Assemble:

```json
{
  "<fixture-stem>": {
    "agents": {
      "<agent>": { "status": "...", "issues": [{ "severity": "...", "message": "..." }] }
    }
  }
}
```

If a fixture's output has no parseable verdict block, record that fixture with
no `status` key — the grader will fail it with "no verdict block emitted".

Write the assembled object to a temp file (e.g. `/tmp/<agent>-actuals.json`).

## Step 5: Grade (deterministic, model-free)

```bash
python3 ~/.claude/evals/eval_grade.py \
  --evals-dir ~/.claude/evals/<agent> \
  --actuals /tmp/<agent>-actuals.json
```

Pass `--baseline ~/.claude/evals/<agent>/baseline.json` if a baseline exists —
then only **regressions** (a baseline-passing pair that now fails) red-line the
run.

## Step 6: Report

Relay the grader's markdown verdict. For any FAIL/REGRESSION, show the fixture,
the expected spec, and the agent's actual verdict so the gap is debuggable.
