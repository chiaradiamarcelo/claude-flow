# Worktree dependency warming

Automatic, zero-token dependency warming for fresh git worktrees created by the
`EnterWorktree` tool. When a feature pipeline enters a worktree off up-to-date
master, the right dependencies are installed in the background before you run any
code — without Claude spending tokens on it.

## How it fits together

| Piece | Location | Role |
| --- | --- | --- |
| `worktree.baseRef: fresh` | `~/.claude/settings.json` | New worktrees branch off `origin/<default-branch>` |
| `EnterWorktree` PostToolUse hook | `~/.claude/settings.json` | Fires the dispatcher when a worktree is created |
| Dispatcher | `~/.claude/hooks/on-enter-worktree.sh` | Picks the warm script, launches it detached & silent |
| **Global default** warm script | `~/.claude/warm-deps.sh` | Auto-detects ecosystem; works out of the box |
| **Per-repo override** (optional) | `<repo>/.claude/warm-deps.sh` | Repo-specific warming; takes precedence over the default |

## Resolution order

On `EnterWorktree`, the dispatcher runs, in the new worktree:

1. `<worktree>/.claude/warm-deps.sh` — **override** (if the repo ships one), else
2. `~/.claude/warm-deps.sh` — **global default**, else
3. nothing.

The chosen script is launched **detached** (fire-and-forget) with cwd = the
worktree, all output redirected to `<worktree>/.claude/warm-deps.log`. The hook
emits nothing on stdout, so **Claude spends zero tokens** on warming. A
single-flight `mkdir` lock (`.claude/.warm-deps.lock`) ensures the script runs
once even if both a global and a project hook fire.

## The global default (`~/.claude/warm-deps.sh`)

Auto-detects by lockfile:

- `pnpm-lock.yaml`     → `pnpm install --prefer-offline`
- `yarn.lock`         → `yarn install --prefer-offline`
- `package-lock.json` → `npm ci --prefer-offline`
- `package.json` only → `npm install`
- otherwise (JVM/Gradle/Maven, Go, Rust, unknown) → **no-op** (deps are in a
  global cache; nothing to warm per-worktree)

To support a new ecosystem everywhere, add a branch here.

## Writing a per-repo override

Drop an executable `.claude/warm-deps.sh` in the repo. Contract:

- It is invoked with **cwd = the worktree root**; stdout/stderr already go to
  `.claude/warm-deps.log` (don't redirect yourself).
- Write a **one-line `.claude/warm-deps.status`**:
  - `ok` on success or when there's nothing to do
  - `error: <hint>` on failure
- Keep it quiet — the status file is the only thing Claude ever reads.

Minimal example:

```bash
#!/usr/bin/env bash
set -uo pipefail
mkdir -p .claude
if pnpm install --prefer-offline; then
  echo ok >.claude/warm-deps.status
else
  echo "error: pnpm install failed - see .claude/warm-deps.log" >.claude/warm-deps.status
fi
```

## Checking status

Success is silent. To confirm deps are ready before running tests:

```bash
cat .claude/warm-deps.status   # "ok" = ready
```

Never read `.claude/warm-deps.log` into context — it's the verbose install output.

## Git hygiene

The runtime artifacts and native worktree dirs are ignored globally via
`~/.config/git/ignore`, so no per-repo `.gitignore` edits are needed:

```
**/.claude/worktrees/
**/.claude/warm-deps.status
**/.claude/warm-deps.log
**/.claude/.warm-deps.lock
```

A checked-in per-repo `.claude/warm-deps.sh` **should** be committed — that's how
a repo stays self-contained for teammates who don't have the global default.
