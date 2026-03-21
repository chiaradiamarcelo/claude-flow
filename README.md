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
2. Reads the reviewer roster from `~/.claude/reviewers.json` (global) and `.claude/reviewers.json` (project, if exists). Merges them — project entries override global entries with the same name.
3. Matches changed files against each reviewer's `triggers` glob patterns.
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

It does two things:
1. Creates the agent file at the chosen location with the review rules and output format.
2. Registers the reviewer in the appropriate `reviewers.json` table (global or project) so the review-gate can discover it.

### Reviewer table

The review-gate discovers reviewers by reading a JSON table, not by scanning agent files. This makes discovery fast and reliable.

**Global table** (`~/.claude/reviewers.json`) — always loaded:

```json
[
  { "name": "test-reviewer", "triggers": ["**/src/test/**", "**/*Test.*", "**/*IT.*", "**/*AT.*"] },
  { "name": "arch-reviewer", "triggers": ["**/src/main/**"] },
  { "name": "refactor-advisor", "triggers": ["**/src/main/**"] }
]
```

**Project table** (`<project>/.claude/reviewers.json`) — optional, merged with global:

```json
[
  { "name": "presentation-reviewer", "triggers": ["**/api/**", "**/controller/**"] }
]
```

**Merge rules:**
- Global table is loaded first.
- Project entries with the same `name` as a global entry **override** the global triggers (project wins).
- Project entries with a new `name` are **added** to the roster.

This means project tables serve two purposes: adding project-specific reviewers, and overriding triggers for global reviewers (e.g., TypeScript file patterns).

### Global vs. project-specific reviewers

- **Global** (`~/.claude/agents/` + `~/.claude/reviewers.json`) — run on every project (e.g., `test-reviewer`, `arch-reviewer`)
- **Project-specific** (`<project>/.claude/agents/` + `<project>/.claude/reviewers.json`) — run only in that project (e.g., `presentation-reviewer`)

### Project trigger overrides

Global reviewers ship with default triggers suited for Kotlin/Java conventions. **No project table is needed for Kotlin/Java projects** — the defaults just work.

For projects using different file conventions (e.g., TypeScript), copy the appropriate template and use it as the project table:

```bash
cp ~/.claude/examples/reviewers.typescript.json <project>/.claude/reviewers.json
```

Available templates:

| Template | For |
|---|---|
| `examples/reviewers.typescript.json` | TypeScript projects (`*.spec.ts`, `*.test.ts`, `__tests__/`) |

## What's included

| Path | Purpose |
|---|---|
| **Config** | |
| `CLAUDE.md` | Global instructions — workflow rules, TDD methodology, test design rules |
| `RTK.md` | RTK usage reference (referenced by CLAUDE.md) |
| `refactor-catalog.md` | Language-agnostic catalog of code smells and refactorings |
| `reviewers.json` | Global reviewer roster — names + trigger patterns (source of truth for review-gate) |
| `settings.json` | Permissions, hooks, plugins, statusline config |
| `statusline-command.sh` | Context window usage bar for the statusline |
| **Commands** | |
| `commands/intent-and-goal.md` | `/intent-and-goal` — feature intent refinement and scenario generation |
| `commands/new-reviewer.md` | `/new-reviewer` — guided creation and registration of reviewer agents |
| `commands/run-reviewers.md` | `/run-reviewers <path>` — ad-hoc review of any folder (legacy code, full project) |
| **Agents — pipeline** | |
| `agents/architect/` | Plans scenario implementation into the SoT file (invokes `clean-architecture` skill) |
| `agents/developer/` | Implements the plan with strict TDD (invokes `clean-architecture`, `tdd`, `testing` skills) |
| `agents/review-gate/` | Orchestrates parallel reviewer spawning from `reviewers.json` |
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
