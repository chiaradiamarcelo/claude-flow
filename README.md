# claude-flow

Personal Claude Code configuration: global instructions, custom agents, skills, hooks, and settings.

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

## What's included

| Path | Purpose |
|---|---|
| `CLAUDE.md` | Global instructions (Clean Architecture & TDD playbook) |
| `RTK.md` | RTK usage reference (referenced by CLAUDE.md) |
| `refactor-catalog.md` | Language-agnostic catalog of code smells and refactorings |
| `settings.json` | Permissions, hooks, plugins, statusline config |
| `statusline-command.sh` | Context window usage bar for the statusline |
| `hooks/rtk-rewrite.sh` | Pre-tool hook that rewrites commands through RTK |
| `agents/` | Custom agents (architect, developer, test-reviewer, arch-reviewer, refactor-advisor) |
| `skills/` | Custom skills (tdd, testing) |
| `memory/` | Persistent file-based memory for cross-conversation context |

## Note

`settings.json` contains hardcoded paths to `~/.claude/`. If your home directory differs from `/Users/mchiaradia`, update the paths accordingly.
