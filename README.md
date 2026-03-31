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

The pipeline takes a feature from intent to reviewed, tested code — with human involvement only at the front (defining intent and approving scenarios). After that, agents run autonomously.

### Phase 1: Intent and scenarios (human-driven)

Start any new feature or use case with:

```
/intent-and-goal <brief description of feature>
```

This command walks through three phases interactively:

1. **Intent refinement** — clarifying questions to define the primary goal, secondary goals, and constraints.
2. **Scenario generation** — proposes Gherkin scenarios (happy path, empty state, edge cases, errors) with unique IDs (`SCENARIO-01`, `SCENARIO-02`, ...). Iterate until satisfied.
3. **Specification creation** — on approval, creates a folder at `docs/specifications/<feature-slug>/` with a `specification.md` containing the intent, business rules, scenarios, and a progress checklist. Scenario plan files are created later by the architect.

### Phase 2: Planning (parallel)

All scenarios are planned before any code is written:

```
proceed
```

This runs one `architect` agent per scenario, all in parallel. Each architect invokes the `clean-architecture` skill, reads `specification.md` and existing code, then creates a scenario plan file (`SCENARIO-XX.md`) in the same folder. It writes no code — only a plan of files and classes to create/modify, following inside-out Clean Architecture order (domain → ports → fakes → use case → infrastructure → API).

```
docs/specifications/deposit-money/
  specification.md          # Intent, rules, scenarios, progress checklist
  SCENARIO-01.md            # Architect's plan with checkboxes
  SCENARIO-02.md            # Created when that scenario is planned
```

Planning rules: test behavior through the use case (not domain entities directly), every port adapter must have a contract test, domain entities with identity include equality.

### Phase 3: Implementation (parallel)

All scenarios are implemented in parallel — one `developer` agent per scenario, each in its own worktree for isolation.

Each developer reads `specification.md` for context and the scenario plan file for the checklist, then executes step by step:

- Writes a failing test first (red)
- Writes the minimal code to pass (green)
- Refactors while keeping tests green
- Marks each step done in the scenario plan file

### Phase 4: Review

After all scenarios are implemented, `/run-reviewers` runs once on all changed files. It runs in the main conversation (not as a sub-agent, so it can spawn reviewer agents). With no arguments (pipeline mode), it:

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

### Phase 5: Fix pass

- **FAIL** → developers are spawned in fix mode (one per scenario with findings, in parallel). All findings (violations, warnings, suggestions) addressed in one pass. Then `/run-reviewers` runs again.
- **PASS** → done.

```
Phase 1:  /intent-and-goal → scenarios approved
Phase 2:  architect × N  (parallel)
Phase 3:  developer × N  (parallel, worktree isolation)
Phase 4:  /run-reviewers  (once, all changed files)
Phase 5:  developer fix × N if FAIL → /run-reviewers again
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

The /run-reviewers and `/run-reviewers` discover reviewers by grepping for `type: reviewer` in agent files (both `~/.claude/agents/` and `<project>/.claude/agents/`). Each reviewer declares its triggers in its own frontmatter:

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

The /run-reviewers reads this file and replaces frontmatter triggers for matching reviewer names. Reviewers without an entry keep their defaults.

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
| [refactor-catalog.md](refactor-catalog.md) | Language-agnostic catalog of code smells and refactorings |
| [settings.json](settings.json) | Permissions, hooks, plugins, statusline config |
| [statusline-command.sh](statusline-command.sh) | Context window usage bar for the statusline |
| **Commands** | |
| [commands/intent-and-goal.md](commands/intent-and-goal.md) | `/intent-and-goal` — feature intent refinement and scenario generation |
| [commands/new-reviewer.md](commands/new-reviewer.md) | `/new-reviewer` — guided creation of reviewer agents |
| [commands/run-reviewers.md](commands/run-reviewers.md) | `/run-reviewers <path>` — ad-hoc review of any folder (legacy code, full project) |
| [commands/continue-scenario.md](commands/continue-scenario.md) | `/continue-scenario` — find next unchecked scenario and run the pipeline |
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
| **Other** | |
| [hooks/rtk-rewrite.sh](hooks/rtk-rewrite.sh) | Pre-tool hook that rewrites commands through RTK |
| [examples/](examples/) | Template files (e.g., `review-triggers.typescript.json` for project trigger overrides) |
| [scripts/run-scenarios.sh](scripts/run-scenarios.sh) | Ralph loop — batch scenario runner for unattended execution |

## Ralph loop - Batch scenario runner (unattended)

For running multiple scenarios unattended (e.g., overnight or while away), use the batch script. Each scenario gets a fresh Claude session — no context contamination between scenarios.

```bash
./scripts/run-scenarios.sh deposit-money
```

This loops through all unchecked scenarios in `docs/specifications/deposit-money/specification.md`, running one per fresh Claude session via `/continue-scenario`. It handles rate-limit retries and verifies each scenario is marked done before proceeding.

**When to use it:**
- You have several scenarios approved and want to let Claude work through them unattended
- You want guaranteed fresh context per scenario (no context window bloat)

**When NOT to use it:**
- Most of the time. The normal interactive flow (`/intent-and-goal` → "proceed") is preferred when you're at the keyboard and want to steer the work.