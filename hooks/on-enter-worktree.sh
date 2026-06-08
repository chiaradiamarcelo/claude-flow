#!/usr/bin/env bash
# GLOBAL PostToolUse hook for the EnterWorktree tool.
#
# Warms dependencies in the freshly-created worktree WITHOUT spending any Claude
# tokens: this runs outside the model loop and emits nothing on stdout, so Claude
# never sees its output. The install is launched detached (fire-and-forget) and
# writes to <worktree>/.claude/warm-deps.log; success is recorded as a single
# line in <worktree>/.claude/warm-deps.status.
#
# Per-repo customization lives in <worktree>/.claude/warm-deps.sh:
#   - present (e.g. a TypeScript repo)        -> it runs (pnpm install, etc.)
#   - absent  (e.g. a Kotlin/Java/Gradle/Maven repo, deps in a global cache)
#                                             -> silent no-op: zero work, zero tokens.
set -uo pipefail

input="$(cat)"

# Keep the last raw hook payload for debugging (outside any repo, overwritten
# each run, zero token impact). Safe to delete.
printf '%s' "$input" >/tmp/claude-warm-worktree-last.json 2>/dev/null || true

# Resolve the new worktree directory from the tool response, tolerant of field
# naming across versions; fall back to the current directory.
wt="$(printf '%s' "$input" | jq -r '
  (.tool_response // {}) as $r
  | ($r.path // $r.worktreePath // $r.worktree // $r.cwd
     // $r.newWorkingDirectory // .cwd // empty)' 2>/dev/null || true)"
if [ -z "${wt:-}" ] || [ ! -d "$wt" ]; then
  wt="$PWD"
fi

# Pick the warm script: per-repo override first, else the global default.
override="$wt/.claude/warm-deps.sh"
default="$HOME/.claude/warm-deps.sh"
if [ -f "$override" ]; then
  script="$override"
elif [ -f "$default" ]; then
  script="$default"
else
  exit 0   # nothing to run
fi

mkdir -p "$wt/.claude"

# Single-flight guard: an atomic mkdir lock prevents a second hook (e.g. a repo
# that also wires EnterWorktree) from launching a concurrent, conflicting
# install in the same worktree. Concurrent installs can corrupt a lockfile.
# Detached, non-blocking: the script runs in the background with cwd = the
# worktree, output to a log file; the hook returns immediately and prints nothing.
lock="$wt/.claude/.warm-deps.lock"
if mkdir "$lock" 2>/dev/null; then
  ( cd "$wt" && nohup bash -c 'bash "$1"; rmdir .claude/.warm-deps.lock 2>/dev/null' _ "$script" \
      >"$wt/.claude/warm-deps.log" 2>&1 </dev/null & )
fi

exit 0
