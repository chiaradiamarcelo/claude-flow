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
2. **Scenario generation** — reads existing domain models and use cases to reuse the project's ubiquitous language, grills you with clarifying questions, then proposes Gherkin scenarios (happy path, empty state, edge cases, errors) with unique IDs (`SCENARIO-01`, `SCENARIO-02`, …). It then checks every business rule against the scenarios — *would any scenario fail if this rule were violated?* — and comes back with a question wherever none would. Iterate until you approve.
3. **Specification creation** — on approval, writes the Source-of-Truth `docs/specifications/<feature-slug>/specification.md` (intent, business rules, scenarios, and a `## BDD Acceptance Progress` checklist). Scenario plan files are written later, by the architect.

Then it **hands off automatically**: once `specification.md` is written it runs `/run-pipeline <feature-slug>`. You don't trigger the rest by hand.

The coverage check in step 2 is not the same as asking whether a rule is *ambiguous*. A rule
can be perfectly clear and still have nothing that falsifies it — which is how a spec
stating that account numbers were unique reached implementation with no scenario exercising
a collision, and why an uncovered rule becomes a question to you rather than a note in the
margin (finding 16).

### Phase 2: Execution — `/run-pipeline` (sequential)

`/run-pipeline <feature-slug>` is the execution orchestrator. It first reads the approved `specification.md`; **if no approved spec exists it STOPs and writes no code**. (It knows nothing about how the spec was produced — its only precondition is "an approved spec exists," so it works equally well when run by hand.)

Then, for each unchecked scenario in `## BDD Acceptance Progress`, **top-to-bottom, one at a time** (never parallel or batched):

1. **`architect`** plans the scenario's **structure** → writes `SCENARIO-XX.md` with a `## Structure & Contracts` section: which layers/ports/adapters/controllers exist, where they live, the CQRS side, contract-test obligations, and the API surface (URL, method, status mapping). It enumerates no tests and writes no code.
2. **`test-designer`** (the "prophet") appends a `## Ordered Test List (FLFI · TPP · Contradiction)` section: the ordered, justified sequence of tests that will drive the implementation — each row named by its business rule (FLFI), tagged with the transformation it forces (TPP), and the assumption it contradicts. Flags any structural gap with a `> Note to architect:` line. Writes no code.
3. **`developer`** executes the ordered test list **batch-red-per-class** — for each class: write its whole test batch, run once and verify every test is red for its planned reason (*batch-red-verified*), then implement the class to green and refactor — flipping each row's `Status ☐ → ✅` and honoring any notes. (Per-class rather than per-test because the design is decided up front by the architect + test-designer — see [finding 13](docs/findings/13-batch-vs-strict-tdd.md).)
4. The scenario's box gets checked, then the next scenario begins.

```
docs/specifications/deposit-money/
  specification.md          # SoT: intent, rules, scenarios, progress checklist
  SCENARIO-01.md            # architect's Structure & Contracts + test-designer's Ordered Test List
  SCENARIO-02.md
```

### Phase 3: Review

After **all** scenarios are implemented, `/run-pipeline` runs `/run-reviewers` once over all changed files. `/run-reviewers` runs in the main conversation (not as a sub-agent, so it can spawn reviewer agents). With no arguments (pipeline mode), it:

1. Gets changed files via `git diff --name-only`. Falls back to `git ls-files` if no diff is available.
2. Discovers reviewer agents by grepping for `type: reviewer` in agent frontmatter (global + project).
3. Applies project trigger overrides from the `reviewers` section of `.claude/pipeline.json` if it exists.
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
| `ui-test-reviewer` | `**/*.test.tsx`, `**/*.test.jsx` | React component/hook tests: naming, query priority, mocking, behavioral focus |
| `android-presentation-reviewer` | `**/presentation/**` | Compose screens/ViewModels: Humble View, atomic screen state, Composed Method |
| `android-ui-test-reviewer` | `**/androidTest/**`, `**/androidInstrumentedTest/**` | Compose UI tests: robot pattern, test tags, Robolectric caveats |

### Phase 4: Fix loop (bounded)

The verdict gates on **VIOLATIONs** (an advisory reviewer always emits a SUGGESTION, so gating on those would never pass):

- **FAIL** (one or more VIOLATIONs) → the `developer` runs in fix mode with the consolidated VIOLATION + WARNING findings, then `/run-reviewers` runs again. Repeat until **PASS or 3 fix rounds**.
- **PASS** → done.

```
Step 0:   EnterWorktree         (fresh branch off origin/<default>)
Phase 1:  /intent-and-goal      → scenarios approved → writes specification.md
Phase 2:  /run-pipeline         architect → test-designer → developer, per scenario, ONE AT A TIME
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
/new-reviewer android-presentation-reviewer
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
name: dto-reviewer
description: Reviews API response DTOs for leaking domain internals.
type: reviewer
triggers: ["**/api/**", "**/controller/**", "**/dto/**"]
tools: Read, Glob, Grep
model: sonnet
---
```

### Global vs. project-specific reviewers

- **Global** (`~/.claude/agents/`) — run on every project (e.g., `test-reviewer`, `arch-reviewer`)
- **Project-specific** (`<project>/.claude/agents/`) — run only in that project (e.g., `android-presentation-reviewer`)

Both are discovered automatically. A project agent with the same name as a global agent overrides it entirely (Claude Code built-in behavior).

### Per-project pipeline config (`.claude/pipeline.json`)

A single optional file at the project root customizes the pipeline per project. Both sections are optional:

```json
{
  "reviewers":   { "<reviewer-name>": ["glob", "!negglob"] },
  "agentSkills": { "<agent-name>":    ["skill-name"] }
}
```

- **`reviewers`** overrides a reviewer's frontmatter triggers by name. Global reviewers ship with defaults suited for Kotlin/Java conventions, so **no override is needed for Kotlin/Java projects**. Reviewers without an entry keep their defaults. `/run-reviewers` reads this section.
- **`agentSkills`** injects **additional** skills into a pipeline agent's session, keyed by agent name — write-side agents (`architect`, `test-designer`, `developer`) and reviewers (`test-reviewer`, …) alike. It is **additive**: the agent always loads its core skills, plus whatever is listed here. This is how a project layers in stack-specific conventions (e.g. Android) without editing the global agents.

To set up config, copy a template:

```bash
cp ~/.claude/examples/pipeline.typescript.json <project>/.claude/pipeline.json
```

Available templates:

| Template | For |
|---|---|
| `examples/pipeline.typescript.json` | TypeScript projects (`*.spec.ts`, `*.test.ts`, `__tests__/`) |
| `examples/pipeline.android.json` | Android/Kotlin projects (adds `android-ui-test-reviewer` triggers + `android-testing`/`android-ui-testing` skill injection into `test-designer`/`developer`/`test-reviewer`) |

## What's included

| Path | Purpose |
|---|---|
| **Config** | |
| [CLAUDE.md](CLAUDE.md) | Global instructions — workflow rules, test naming + test design rules (TDD itself is owned by the pipeline agents, not restated here) |
| [RTK.md](RTK.md) | RTK usage reference (referenced by CLAUDE.md) |
| [knowledge/refactor-catalog/](knowledge/refactor-catalog/index.md) | Language-agnostic catalog of code smells and refactorings (index + one file per pattern, loaded on demand by `refactor-advisor`) |
| [settings.json](settings.json) | Permissions, hooks, plugins, statusline config |
| [statusline-command.sh](statusline-command.sh) | Context window usage bar for the statusline |
| **Commands** | |
| [commands/intent-and-goal.md](commands/intent-and-goal.md) | `/intent-and-goal` — entry point: intent refinement + scenario generation, then hands off to `/run-pipeline` |
| [commands/run-pipeline.md](commands/run-pipeline.md) | `/run-pipeline <feature-slug>` — execution orchestrator: per-scenario architect→test-designer→developer, reviewers, fix-loop (requires an approved spec) |
| [commands/new-reviewer.md](commands/new-reviewer.md) | `/new-reviewer` — guided creation of reviewer agents |
| [commands/run-reviewers.md](commands/run-reviewers.md) | `/run-reviewers <path>` — ad-hoc review of any folder (legacy code, full project) |
| [commands/mutation-audit.md](commands/mutation-audit.md) | `/mutation-audit <path>` — on-demand, filtered mutation audit (real survivors only; `--crap` for complexity×coverage). Backstop for suites you didn't generate; **not** part of `/run-pipeline` (see finding 14) |
| **Agents — pipeline** | |
| [agents/architect/](agents/architect/Agent.md) | Plans the scenario's **Structure & Contracts** (layers/ports/adapters); writes no tests or code (invokes `clean-architecture`, `cqrs`) |
| [agents/test-designer/](agents/test-designer/Agent.md) | Appends the **Ordered Test List** (FLFI · TPP · Contradiction) — the justified test order that drives the slice; writes no code (invokes `testing`) |
| [agents/developer/](agents/developer/Agent.md) | Implements the plan (batch-red-per-class TDD, batch-red-verified; invokes `clean-architecture`, `testing`) |
| **Agents — reviewers** | |
| [agents/test-reviewer/](agents/test-reviewer/Agent.md) | Reviews test quality (GWT, naming, fakes, assertions, coverage strategy) |
| [agents/arch-reviewer/](agents/arch-reviewer/Agent.md) | Reviews Clean Architecture structural compliance |
| [agents/refactor-advisor/](agents/refactor-advisor/Agent.md) | Suggests code quality improvements (invokes `clean-architecture` skill) |
| [agents/api-reviewer/](agents/api-reviewer/Agent.md) | Reviews API layer (HTTP conventions, thin controllers, REST URLs, response modeling) |
| [agents/ui-test-reviewer/](agents/ui-test-reviewer/Agent.md) | Reviews React component/hook tests (naming, query priority, mocking, behavioral focus) |
| [agents/android-presentation-reviewer/](agents/android-presentation-reviewer/Agent.md) | Reviews Android presentation layer (Compose screens, ViewModels, Humble View, atomic screen state) |
| [agents/android-ui-test-reviewer/](agents/android-ui-test-reviewer/Agent.md) | Reviews Compose UI tests (robot pattern, test tags, Robolectric caveats) |
| **Skills** | |
| [skills/clean-architecture/](skills/clean-architecture/SKILL.md) | Folder structure, dependency rules, design and code conventions |
| [skills/cqrs/](skills/cqrs/SKILL.md) | When to split write side (Repository + UseCase) from read side (Query); port naming, read-model shape |
| [skills/api-conventions/](skills/api-conventions/SKILL.md) | HTTP/REST boundary rules — controller shape, URL design, request/response modeling, status codes, validation ownership |
| [skills/testing/](skills/testing/SKILL.md) | Test structure, naming, fakes, coverage strategy, and the FLFI·TPP·Contradiction + mutation-question test-design procedure |
| [skills/ui-testing/](skills/ui-testing/SKILL.md) | React component/hook test conventions (naming, query priority, render, mocking) |
| [skills/android-testing/](skills/android-testing/SKILL.md) | General Android test conventions (JVM vs instrumented source set, Robolectric caveats) |
| [skills/android-ui-testing/](skills/android-ui-testing/SKILL.md) | Compose UI test conventions (robot pattern, test tags, Voyager patterns, Robolectric limits) |
| [skills/kotlin-conventions/](skills/kotlin-conventions/SKILL.md) | Kotlin style and idiom conventions |
| [skills/legacy-code/](skills/legacy-code/SKILL.md) | Working with untested/tangled/legacy code (Feathers) — characterization tests, seams, migrations |
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
| [docs/README.md](docs/README.md) | **Engineering findings (lab notebook)** — 16 measured discoveries: a grader bug that looked like model flakiness, skill-loading cost (~1.8×), the cost model, exhaustive corpora, generative-agent + integration + acceptance testing, orchestration-as-a-command (10), the test.json migration + cache decision (11), the v2 Spring/JPA vertical-slice integration (12), the strict-vs-batch-red TDD experiment (13), the mutation-gate spike (14), the pipeline cost programme (15), and the rejected layered pipeline (16) |
| **Other** | |
| [tools/mutation/](tools/mutation/) | Support scripts for `/mutation-audit` — `classify-survivors.py` (the mandatory junk-vs-real survivor filter) + `crap.py` (JaCoCo XML → CRAP) |
| [hooks/rtk-rewrite.sh](hooks/rtk-rewrite.sh) | Pre-tool hook that rewrites commands through RTK |
| [examples/](examples/) | Per-project `.claude/pipeline.json` templates (`pipeline.typescript.json`, `pipeline.android.json`) — reviewer trigger overrides + agent skill injection |