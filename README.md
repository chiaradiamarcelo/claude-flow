# claude-flow

Personal Claude Code configuration: global instructions, custom agents, skills, hooks, and settings. Implements a multi-agent development pipeline with Clean Architecture, TDD, and parallel review gates.

## Setup

Clone into `~/.claude/`:

```bash
git clone git@github-chiaradiamarcelo:chiaradiamarcelo/claude-flow.git ~/.claude
```

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
3. **SoT creation** — on approval, creates a Source of Truth specification file at `docs/specifications/<feature-slug>.md` with the intent, business rules, scenarios, and placeholder sections for implementation plans.

### Phase 2: Implementation (autonomous)

Once scenarios are approved, trigger implementation one scenario at a time:

```
proceed with SCENARIO-01
```

This runs the following pipeline automatically:

```
architect → developer → review-gate → developer (fix) if needed
```

#### Step 1: Architect

The `architect` agent invokes the `clean-architecture` skill to load conventions, reads the SoT file and existing code, then writes an ordered implementation checklist into the SoT. It writes no code — only a plan of files and classes to create/modify, following inside-out Clean Architecture order (domain → ports → fakes → use case → infrastructure → API).

Planning rules: test behavior through the use case (not domain entities directly), every port adapter must have a contract test, domain entities with identity include equality.

#### Step 2: Developer

The `developer` agent invokes the `clean-architecture`, `tdd`, and `testing` skills, then executes the checklist step by step:

- Writes a failing test first (red)
- Writes the minimal code to pass (green)
- Refactors while keeping tests green
- Marks each step done in the SoT file

Can also run in **fix mode** — receives consolidated review findings and addresses all violations in one pass.

#### Step 3: Review gate (parallel, runs once)

The `review-gate` orchestrator agent:

1. Gets changed files via `git diff --name-only`. Falls back to `git ls-files` if no diff is available (e.g., single commit).
2. Discovers reviewer agents by grepping for `type: reviewer` in agent files (global + project). Reads matched files to extract `name` and `triggers`.
3. Applies project trigger overrides from `.claude/review-triggers.json` if it exists.
4. Matches changed files against each reviewer's `triggers` glob patterns.
4. Spawns **only relevant reviewers as sub-agents in parallel** (multiple Agent tool calls in a single message).
5. Consolidates all findings into a single report with a PASS/FAIL verdict.

The review-gate does not review code itself — it only orchestrates. Each reviewer agent runs independently in its own context.

Built-in reviewers (defined in `~/.claude/reviewers.json`):

| Reviewer | Default triggers | Checks |
|---|---|---|
| `test-reviewer` | `**/src/test/**`, `**/*Test.*`, `**/*IT.*`, `**/*AT.*` | GWT structure, naming, fakes vs mocks, redundant assertions, test logic, coverage strategy |
| `arch-reviewer` | `**/src/main/**` | Layer dependencies, domain purity, Clean Architecture patterns, TDD compliance |
| `refactor-advisor` | `**/src/main/**` | Primitive obsession, misplaced logic, intent-revealing methods, naming, mapper cleanliness |

#### Step 4: Fix pass

- **FAIL** (violations exist) → the developer is spawned in fix mode with all findings and addresses everything in one pass. Scenario is done.
- **PASS** (no violations) → scenario is done.

The review gate runs exactly once. No re-verification loop — the developer fixes all violations in a single pass.

### Scenarios run sequentially

Each scenario builds on a known-green, reviewed codebase before the next one starts. This guarantees no conflicts and full traceability from business behavior to implementation.

```
SCENARIO-01: architect → developer → review-gate → done
SCENARIO-02: architect → developer → review-gate → done
SCENARIO-03: architect → developer → review-gate → done
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

It creates the agent file at the chosen location with `type: reviewer` and `triggers` in its frontmatter, plus the review rules and output format. The review-gate auto-discovers it on the next run — no other registration needed.

### Reviewer discovery

The review-gate and `/run-reviewers` discover reviewers by grepping for `type: reviewer` in agent files (both `~/.claude/agents/` and `<project>/.claude/agents/`). Each reviewer declares its triggers in its own frontmatter:

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

The review-gate reads this file and replaces frontmatter triggers for matching reviewer names. Reviewers without an entry keep their defaults.

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
| `CLAUDE.md` | Global instructions — workflow rules, TDD methodology, test design rules |
| `RTK.md` | RTK usage reference (referenced by CLAUDE.md) |
| `refactor-catalog.md` | Language-agnostic catalog of code smells and refactorings |
| `settings.json` | Permissions, hooks, plugins, statusline config |
| `statusline-command.sh` | Context window usage bar for the statusline |
| **Commands** | |
| `commands/intent-and-goal.md` | `/intent-and-goal` — feature intent refinement and scenario generation |
| `commands/new-reviewer.md` | `/new-reviewer` — guided creation of reviewer agents |
| `commands/run-reviewers.md` | `/run-reviewers <path>` — ad-hoc review of any folder (legacy code, full project) |
| **Agents — pipeline** | |
| `agents/architect/` | Plans scenario implementation into the SoT file (invokes `clean-architecture` skill) |
| `agents/developer/` | Implements the plan with strict TDD (invokes `clean-architecture`, `tdd`, `testing` skills) |
| `agents/review-gate/` | Discovers `type: reviewer` agents, filters by triggers, spawns in parallel |
| **Agents — reviewers** | |
| `agents/test-reviewer/` | Reviews test quality (GWT, naming, fakes, assertions, coverage strategy) |
| `agents/arch-reviewer/` | Reviews Clean Architecture compliance (invokes `clean-architecture` skill) |
| `agents/refactor-advisor/` | Suggests clean code improvements (invokes `clean-architecture` skill) |
| **Skills** | |
| `skills/clean-architecture/` | Folder structure, dependency rules, design and code conventions |
| `skills/tdd/` | TDD red-green-refactor cycle enforcement |
| `skills/testing/` | Test structure, naming, fakes, and coverage conventions |
| **Other** | |
| `hooks/rtk-rewrite.sh` | Pre-tool hook that rewrites commands through RTK |
| `examples/` | Template files (e.g., `reviewers.typescript.json` for project trigger overrides) |
| `memory/` | Persistent file-based memory for cross-conversation context |

## Note

`settings.json` contains hardcoded paths to `~/.claude/`. If your home directory differs from `/Users/mchiaradia`, update the paths accordingly.
