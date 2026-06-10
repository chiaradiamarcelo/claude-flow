# Eval corpus

Fixtures and their expected gradings for the pipeline's agents (reviewers,
architect, …). This is the **unit-test layer** of "using the tool to build the
tool": each fixture pins one agent's behavior on one frozen input, so a prompt
edit that regresses the agent is caught cheaply.

Inspired by `bdfinst/agentic-dev-team`'s eval corpus: a **deterministic,
model-free grader** (`eval_grade.py`) checks *coarse, non-determinism-tolerant*
properties of a lightly-structured agent output — not exact wording.

## Layout

```
evals/
  eval_grade.py                       # deterministic grader (model-free)
  <agent>/
    fixtures/
      <fixture-stem>/
        input/        <files fed to the agent>
        expected.json <the grading spec for this fixture>
```

## What the agent emits (the contract)

Each gradable agent ends its output with one machine-readable verdict block:

```
<!-- EVAL-VERDICT -->
{ "status": "fail", "issues": [{ "severity": "error", "message": "..." }] }
```

`status` is `pass`/`fail`; `issues` lists only hard violations. The
`/run-evals` orchestrator dispatches the agent on each fixture, extracts this
block, and assembles `actuals.json` (shape below).

### `actuals.json`

```json
{
  "<fixture-stem>": {
    "agents": {
      "<agent>": { "status": "fail",
                   "issues": [{ "severity": "error", "message": "..." }] }
    }
  }
}
```

## What `expected.json` asserts (coarse, drift-tolerant)

```json
{
  "fixture": "dirty-loop-and-camelcase",
  "applicableAgents": ["test-reviewer"],
  "agents": {
    "test-reviewer": {
      "expectedStatus": "fail",
      "issueCount": { "min": 1 },
      "mustMention": ["loop"]
    }
  }
}
```

It grades **stable facts** — pass/fail, an issue-count *range*, and
*must-mention* substrings — never the exact prose. That is what keeps a grader
of a non-deterministic agent deterministic and flake-free.

## Two-tier gate

1. **Structural (always, free, no model):**
   `python3 evals/eval_grade.py --evals-dir evals/<agent> --check-corpus`
   asserts every `expected.json` is well-formed and pairs with a non-empty
   `input/`. No tokens, no flakes.
2. **Live (paid):** `/run-evals <agent>` dispatches the agent, records
   `actuals.json`, and grades it:
   `python3 evals/eval_grade.py --evals-dir evals/<agent> --actuals actuals.json`.
