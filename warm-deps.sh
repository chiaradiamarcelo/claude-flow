#!/usr/bin/env bash
# GLOBAL DEFAULT dependency warming for a fresh worktree.
#
# Runs when a worktree has NO project-specific .claude/warm-deps.sh override.
# Invoked detached by the EnterWorktree hook (~/.claude/hooks/on-enter-worktree.sh)
# with cwd = the worktree root and stdout/stderr already redirected to
# .claude/warm-deps.log.
#
# Contract (same for any override): write a one-line .claude/warm-deps.status
#   - "ok"        on success or when there is nothing to warm
#   - "error: ..." on failure
# Claude only ever reads that status file, never the log.
#
# Auto-detects the ecosystem by lockfile. JVM (Gradle/Maven), Go, Rust, and
# unknown repos are a silent no-op: their dependencies live in a global cache,
# so there is nothing to warm per-worktree. To customise a single repo, drop a
# .claude/warm-deps.sh in it (this default is then ignored).
set -uo pipefail

mkdir -p .claude
status=.claude/warm-deps.status

run() {
  echo "warming: $* ($(date))"
  if "$@"; then
    echo ok >"$status"
  else
    echo "error: '$*' failed - see .claude/warm-deps.log" >"$status"
  fi
}

if [ -f pnpm-lock.yaml ]; then
  run pnpm install --prefer-offline
elif [ -f yarn.lock ]; then
  run yarn install --prefer-offline
elif [ -f package-lock.json ]; then
  run npm ci --prefer-offline
elif [ -f package.json ]; then
  run npm install
else
  # JVM/Go/Rust/unknown: deps are in a global cache; nothing to warm.
  echo "no per-worktree warming needed for this ecosystem ($(date))"
  echo ok >"$status"
fi
