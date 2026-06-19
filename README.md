# claude-flow

Personal Claude Code configuration: global instructions, custom agents, skills, hooks, and settings. Implements a multi-agent development pipeline with Clean Architecture, TDD, and parallel review gates.

## Prerequisites

### RTK (Rust Token Killer)

RTK is a token-optimized CLI proxy used by the hook in `settings.json`. Install it before using this config:

```bash
cargo install rtk
```

Requires `rtk >= 0.23.0` and `jq`.

- RTK repo: https://github.com/rtk-ai/rtk
- jq: https://jqlang.github.io/jq/download/

### Other dependencies

- `jq` — used by hooks and the statusline script

## How the flow works

The pipeline takes a feature from intent to reviewed, tested code — with human involvement only at the front (defining intent and approving scenarios). After that it runs autonomously, **one scenario at a time**.

### Step 0: Fresh worktree (mandatory)

Every feature starts in a clean, isolated worktree branched off the current default branch — never on the shared checkout's branch. The `EnterWorktree` tool creates it (with `worktree.baseRef: fresh` it fetches and branches off `origin/<default-branch>`), and a `PostToolUse` hook warms dependencies. All pipeline artifacts live inside this one worktree. (Skipped if the session is already in a worktree.)

### Phase 1: Intent and scenarios (human-driven)

Start any new feature or use case with:

```
/intent-and-goal <brief description of feature>
```

This command is interactive:

1. **Intent refinement** — clarifying questions to define the primary goal, secondary goals, and constraints.
2. **Scenario generation** — first reads existing domain models and use cases to reuse the project's ubiquitous language, then proposes Gherkin scenarios (happy path, empty state, edge cases, errors) with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …). Iterate until you approve.
3. **Specification creation** — on approval, writes the Source-of-Truth `docs/specifications/<feature-slug>/specification.md` (intent, business rules, scenarios, and a `## BDD Acceptance Progress` checklist). Scenario plan files are written later, by the architect.

Then it **hands off automatically**: once `specification.md` is written it runs `/run-pipeline <feature-slug>`. You don't trigger the rest by hand.

### Phase 2: Execution — `/run-pipeline` (sequential)

`/run-pipeline <feature-slug>` is the execution orchestrator. It first reads the approved `specification.md`; **if no approved spec exists it STOPs and writes no code**. (It knows nothing about how the spec was produced — its only precondition is "an approved spec exists," so it works equally well when run by hand.)

Then, for each unchecked scenario in `## BDD Acceptance Progress`, **top-to-bottom, one at a time** (never parallel or batched):

1. **`architect`** plans the scenario → writes `SCENARIO-XX.md`: a checklist of files/classes in inside-out Clean Architecture order (domain → ports → fakes → use case → infrastructure → API). It writes no code. (Planning rules: test behavior through the use case, every port adapter has a contract test, entities with identity include equality.)
2. **`developer`** implements that plan with strict TDD — failing test (red) → minimal code (green) → refactor — checking off each step.
3. The scenario's box gets checked, then the next scenario begins.

```
docs/specifications/deposit-money/
  specification.md          # SoT: intent, rules, scenarios, progress checklist
  SCENARIO-01.md            # Architect's plan (checkboxes), written per scenario
  SCENARIO-02.md
```

### Phase 3: Review

After **all** scenarios are implemented, `/run-pipeline` runs `/run-reviewers` once over all changed files. `/run-reviewers` runs in the main conversation (not as a sub-agent, so it can spawn reviewer agents). With no arguments (pipeline mode), it:

1. Gets changed files via `git diff --name-only`. Falls back to `git ls-files` if no diff is available.
2. Discovers reviewer agents by grepping for `type: reviewer` in agent frontmatter (global + project).
3. Applies project trigger overrides from `.claude/review-triggers.json` if it exists.
4. Matches changed files against each reviewer's `triggers` glob patterns.
5. Spawns **only relevant reviewers in parallel** (multiple Agent tool calls in a single message).
6. Consolidates all findings into a single report with a PASS/FAIL verdict.

Built-in reviewers (defined in agent frontmatter):

| Reviewer | Default triggers | Checks |
|---|---|---|
| `test-reviewer` | `**/src/test/**`, `**/*Test.*`, `**/*IT.*`, `**/*AT.*` | GWT structure, naming, fakes vs mocks, redundant assertions, test logic, coverage strategy |
| `arch-reviewer` | `**/src/main/**` | Layer dependencies, domain purity, Clean Architecture patterns, TDD compliance |
| `refactor-advisor` | `**/src/main/**` | Primitive obsession, misplaced logic, intent-revealing methods, naming, mapper cleanliness |
| `api-reviewer` | `**/api/**`, `**/controller/**`, `**/dto/**` | HTTP conventions, thin controllers, REST URLs, response modeling |

### Phase 4: Fix loop (bounded)

The verdict gates on **VIOLATIONs** (an advisory reviewer always emits a SUGGESTION, so gating on those would never pass):

- **FAIL** (one or more VIOLATIONs) → the `developer` runs in fix mode with the consolidated VIOLATION + WARNING findings, then `/run-reviewers` runs again. Repeat until **PASS or 3 fix rounds**.
- **PASS** → done.

```
Step 0:   EnterWorktree         (fresh branch off origin/<default>)
Phase 1:  /intent-and-goal      → scenarios approved → writes specification.md
Phase 2:  /run-pipeline         architect → developer, per scenario, ONE AT A TIME
Phase 3:  /run-reviewers        (once, all changed files; relevant reviewers in parallel)
Phase 4:  developer fix → /run-reviewers again, until PASS or 3 rounds
```

## Ad-hoc reviews

To review code outside the normal pipeline (legacy code, full project audit, specific layers):

```
/run-reviewers src/main, src/test
```

- Accepts one or more comma-separated paths
- Lists all files under each path, matches against reviewer triggers, spawns only relevant reviewers in parallel
- `/run-reviewers src/test` → only `test-reviewer` runs
- `/run-reviewers src/main` → only `arch-reviewer` + `refactor-advisor` run
- `/run-reviewers` (no path) → reviews all tracked files in the project

## Adding a new reviewer

Run:

```
/new-reviewer
```

or:

```
/new-reviewer presentation-reviewer
```

The command asks for:
- **Name** — kebab-case identifier
- **Purpose** — what the reviewer checks for
- **Triggers** — file glob patterns that activate it
- **Placement** — global (`~/.claude/agents/`) or project-specific (`.claude/agents/`)
- **Checklist** — the specific rules it enforces
- **Model** — which model tier (defaults to sonnet)

It creates the agent file at the chosen location with `type: reviewer` and `triggers` in its frontmatter, plus the review rules and output format. The /run-reviewers auto-discovers it on the next run — no other registration needed.

### Reviewer discovery

`/run-reviewers` discovers reviewers by grepping for `type: reviewer` in agent files (both `~/.claude/agents/` and `<project>/.claude/agents/`). Each reviewer declares its triggers in its own frontmatter:

```yaml
---
name: presentation-reviewer
description: Reviews API response DTOs for leaking domain internals.
type: reviewer
triggers: ["**/api/**", "**/controller/**", "**/dto/**"]
tools: Read, Glob, Grep
model: sonnet
---
```

### Global vs. project-specific reviewers

- **Global** (`~/.claude/agents/`) — run on every project (e.g., `test-reviewer`, `arch-reviewer`)
- **Project-specific** (`<project>/.claude/agents/`) — run only in that project (e.g., `presentation-reviewer`)

Both are discovered automatically. A project agent with the same name as a global agent overrides it entirely (Claude Code built-in behavior).

### Project trigger overrides

Global reviewers ship with default triggers suited for Kotlin/Java conventions. **No override is needed for Kotlin/Java projects** — the defaults just work.

For projects using different file conventions (e.g., TypeScript) where you want to use the global reviewer agents but with different triggers, create a `.claude/review-triggers.json` in the project:

```json
{
  "test-reviewer": ["**/*.spec.ts", "**/*.test.ts", "**/__tests__/**"],
  "arch-reviewer": ["**/src/**", "!**/*.spec.ts", "!**/*.test.ts"]
}
```

`/run-reviewers` reads this file and replaces frontmatter triggers for matching reviewer names. Reviewers without an entry keep their defaults.

To set up overrides, copy the template:

```bash
cp ~/.claude/examples/review-triggers.typescript.json <project>/.claude/review-triggers.json
```

Available templates:

| Template | For |
|---|---|
| `examples/review-triggers.typescript.json` | TypeScript projects (`*.spec.ts`, `*.test.ts`, `__tests__/`) |

## What's included

| Path | Purpose |
|---|---|
| **Config** | |
| [CLAUDE.md](CLAUDE.md) | Global instructions — workflow rules, TDD methodology, test design rules |
| [RTK.md](RTK.md) | RTK usage reference (referenced by CLAUDE.md) |
| [knowledge/refactor-catalog/](knowledge/refactor-catalog/index.md) | Language-agnostic catalog of code smells and refactorings (index + one file per pattern, loaded on demand by `refactor-advisor`) |
| [settings.json](settings.json) | Permissions, hooks, plugins, statusline config |
| [statusline-command.sh](statusline-command.sh) | Context window usage bar for the statusline |
| **Commands** | |
| [commands/intent-and-goal.md](commands/intent-and-goal.md) | `/intent-and-goal` — entry point: intent refinement + scenario generation, then hands off to `/run-pipeline` |
| [commands/run-pipeline.md](commands/run-pipeline.md) | `/run-pipeline <feature-slug>` — execution orchestrator: per-scenario architect→developer, reviewers, fix-loop (requires an approved spec) |
| [commands/new-reviewer.md](commands/new-reviewer.md) | `/new-reviewer` — guided creation of reviewer agents |
| [commands/run-reviewers.md](commands/run-reviewers.md) | `/run-reviewers <path>` — ad-hoc review of any folder (legacy code, full project) |
| **Agents — pipeline** | |
| [agents/architect/](agents/architect/Agent.md) | Creates scenario plan files (invokes `clean-architecture` skill) |
| [agents/developer/](agents/developer/Agent.md) | Implements the plan with strict TDD (invokes `clean-architecture`, `tdd`, `testing` skills) |
| **Agents — reviewers** | |
| [agents/test-reviewer/](agents/test-reviewer/Agent.md) | Reviews test quality (GWT, naming, fakes, assertions, coverage strategy) |
| [agents/arch-reviewer/](agents/arch-reviewer/Agent.md) | Reviews Clean Architecture structural compliance |
| [agents/refactor-advisor/](agents/refactor-advisor/Agent.md) | Suggests code quality improvements (invokes `clean-architecture` skill) |
| [agents/api-reviewer/](agents/api-reviewer/Agent.md) | Reviews API layer (HTTP conventions, thin controllers, REST URLs, response modeling) |
| **Skills** | |
| [skills/clean-architecture/](skills/clean-architecture/SKILL.md) | Folder structure, dependency rules, design and code conventions |
| [skills/tdd/](skills/tdd/SKILL.md) | TDD red-green-refactor cycle enforcement |
| [skills/testing/](skills/testing/SKILL.md) | Test structure, naming, fakes, and coverage conventions |
| [skills/adr/](skills/adr/SKILL.md) | Architecture Decision Record creation |
| **Evals — testing the pipeline** | |
| [evals/README.md](evals/README.md) | Eval corpus + **testing strategy** — every fixture is a `test.json` (given/when/then) run by one engine; the confidence pyramid (unit → integration → acceptance/choreography), non-determinism and drift |
| [evals/evals](evals/evals) → [run_fixture.py](evals/run_fixture.py) | **The eval engine.** `./evals/evals --test <fixture>` runs one fixture (the agent-TDD red/green loop); `--list` lists all. `when.do` (agent/command/build) → handler; `then.grader` → a pure grade_* function |
| [evals/run_all.sh](evals/run_all.sh) | Suite runner — structural + reviewers (fingerprint-cached) + the other kinds via the engine; heavy kinds (developer/pipeline/orchestration) opt-in |
| [evals/eval_grade.py](evals/eval_grade.py) | The reviewer `verdict` grader (`grade_agent`) + the fingerprint cache (caching + diff-scoping), keyed on `test.json` |
| [evals/check_routing.py](evals/check_routing.py) | Deterministic grader for the `/run-reviewers` routing test |
| [evals/check_plan.py](evals/check_plan.py) | Deterministic grader for the **architect** agent — grades the plan *artifact* it writes (plan exists, writes no code, step ordering, must-mention), not a stdout verdict |
| [evals/check_build.py](evals/check_build.py) | Deterministic grader for the **developer** agent (integration layer) — parses JUnit XML after an independent `./gradlew test`: build green, tests actually ran, zero failures, required test classes present |
| [evals/check_spec.py](evals/check_spec.py) | Deterministic grader for the **`/intent-and-goal`** command — grades the `specification.md` artifact it writes (exists, no code, template sections, ≥ N Gherkin scenarios) |
| [evals/check_acceptance.py](evals/check_acceptance.py) | Deterministic grader for the **full pipeline** (acceptance) — build green + zero reviewer VIOLATIONs across the produced code (WARNING/SUGGESTION non-gating) |
| [evals/verify_acceptance.py](evals/verify_acceptance.py) | The harness's **independent verifier** for acceptance — after the real `/run-pipeline` command runs, *it* runs `./gradlew test` + a fresh reviewer pass and grades (never trusts the command's self-report) |
| [evals/golden-repo/](evals/golden-repo/) | Buildable Kotlin/JUnit5 Gradle skeleton (framework-free core) the developer agent implements into during integration + acceptance evals |
| [evals/golden-repo-spring/](evals/golden-repo-spring/) | Buildable Spring Boot + Spring Data JPA + H2 skeleton (full vertical slice: HTTP + persistence) for the `withdraw-money-spring` developer fixture — builds green on JDK 25 (finding 12) |
| [evals/tests/](evals/tests/) | **Harness self-tests** (stdlib `unittest`, model-free, $0) — routing parser (finding-01), choreography/refusal graders, workspace setup, and a runner wiring scan that asserts every fixture's `when.do`/`then.grader` is registered. Run via `evals/run_tests.sh` |
| [evals/check_choreography.py](evals/check_choreography.py) | Grader for the **choreography** test — asserts the real `/run-pipeline` command's call log (real session + fake workers) follows plan→implement→review→fix→re-review as an ordered subsequence |
| [evals/orchestration/](evals/orchestration/) | Choreography fixture — an approved spec + **fake worker agent definitions** that self-log, for testing the real `/run-pipeline` command's dance (opt-in: `run_all.sh orchestration`) |
| [docs/README.md](docs/README.md) | **Engineering findings (lab notebook)** — 12 measured discoveries: a grader bug that looked like model flakiness, skill-loading cost (~1.8×), the cost model, exhaustive corpora, generative-agent + integration + acceptance testing, orchestration-as-a-command (10), the test.json migration + cache decision (11), and the v2 Spring/JPA vertical-slice integration (12) |
| **Other** | |
| [hooks/rtk-rewrite.sh](hooks/rtk-rewrite.sh) | Pre-tool hook that rewrites commands through RTK |
| [examples/](examples/) | Template files (e.g., `review-triggers.typescript.json` for project trigger overrides) |