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

The `architect` agent reads the SoT file and existing code, then writes an ordered implementation checklist into the SoT. It writes no code — only a plan of files and classes to create/modify, following inside-out Clean Architecture order (domain → ports → fakes → use case → infrastructure → API).

#### Step 2: Developer

The `developer` agent executes the checklist step by step using strict TDD:

- Writes a failing test first (red)
- Writes the minimal code to pass (green)
- Refactors while keeping tests green
- Marks each step done in the SoT file

#### Step 3: Review gate (parallel)

The `review-gate` orchestrator agent:

1. Runs `git diff --name-only` to get changed files.
2. Discovers all agents with `type: reviewer` in their frontmatter (from both `~/.claude/agents/` and `.claude/agents/`).
3. Matches changed files against each reviewer's `triggers` glob patterns.
4. Launches **only relevant reviewers in parallel**.
5. Consolidates all findings into a single report with a PASS/FAIL verdict.

Built-in reviewers:

| Reviewer | Triggers on | Checks |
|---|---|---|
| `test-reviewer` | `**/src/test/**`, `**/*Test.*`, `**/*IT.*`, `**/*AT.*` | GWT structure, naming, fakes vs mocks, test logic, coverage strategy |
| `arch-reviewer` | `**/src/main/**` | Layer dependencies, domain purity, Clean Architecture patterns, TDD compliance |
| `refactor-advisor` | `**/src/main/**` | Primitive obsession, misplaced logic, naming, mapper cleanliness |

#### Step 4: Fix loop

- **FAIL** (violations exist) → the developer is spawned in fix mode with all findings and addresses everything in one pass. Scenario is done.
- **PASS** (no violations) → scenario is done.

### Scenarios run sequentially

Each scenario builds on a known-green, reviewed codebase before the next one starts. This guarantees no conflicts and full traceability from business behavior to implementation.

```
SCENARIO-01: architect → developer → review-gate → done
SCENARIO-02: architect → developer → review-gate → done
SCENARIO-03: architect → developer → review-gate → done
```

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

It generates the agent file with the correct frontmatter. The `review-gate` auto-discovers it on the next run — no other changes needed.

### Reviewer agent frontmatter

Reviewers are identified by `type: reviewer` and activated by `triggers`:

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
- **Project-specific** (`<project>/.claude/agents/`) — run only in that project (e.g., `presentation-reviewer` for a specific API)

Both are discovered and merged by the review gate.

### Project trigger overrides

Global reviewers ship with default triggers in their frontmatter, suited for Kotlin/Java conventions (e.g., `**/*Test.*`, `**/src/main/**`). **No override file is needed for Kotlin/Java projects** — the defaults just work.

For projects using different file conventions (e.g., TypeScript, Python), create a `.claude/review-triggers.json` **in that project** to override triggers. The review-gate checks for this file first — if a reviewer has an entry, its frontmatter triggers are replaced. Reviewers without an entry keep their defaults.

To set up overrides, copy the appropriate template from `examples/` and rename it:

```bash
cp ~/.claude/examples/review-triggers.typescript.json <project>/.claude/review-triggers.json
```

Then edit the patterns to match your project's conventions. Available templates:

| Template | For |
|---|---|
| `examples/review-triggers.typescript.json` | TypeScript projects (`*.spec.ts`, `*.test.ts`, `__tests__/`) |

## What's included

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions (Clean Architecture & TDD playbook) |
| `RTK.md` | RTK usage reference (referenced by CLAUDE.md) |
| `refactor-catalog.md` | Language-agnostic catalog of code smells and refactorings |
| `settings.json` | Permissions, hooks, plugins, statusline config |
| `statusline-command.sh` | Context window usage bar for the statusline |
| `hooks/rtk-rewrite.sh` | Pre-tool hook that rewrites commands through RTK |
| `commands/intent-and-goal.md` | `/intent-and-goal` — feature intent refinement and scenario generation |
| `commands/new-reviewer.md` | `/new-reviewer` — guided creation of reviewer agents |
| `agents/architect/` | Plans scenario implementation into the SoT file |
| `agents/developer/` | Implements the plan with strict TDD |
| `agents/review-gate/` | Orchestrates parallel reviewer discovery, filtering, and execution |
| `agents/test-reviewer/` | Reviews test quality (GWT, naming, fakes, coverage) |
| `agents/arch-reviewer/` | Reviews Clean Architecture compliance |
| `agents/refactor-advisor/` | Suggests clean code improvements |
| `skills/clean-architecture/` | Folder structure, dependency rules, design and code conventions |
| `skills/tdd/` | TDD red-green-refactor cycle enforcement |
| `skills/testing/` | Test structure, naming, fakes, and coverage conventions |
| `memory/` | Persistent file-based memory for cross-conversation context |

## Note

`settings.json` contains hardcoded paths to `~/.claude/`. If your home directory differs from `/Users/mchiaradia`, update the paths accordingly.
