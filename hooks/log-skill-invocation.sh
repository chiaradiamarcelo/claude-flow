#!/usr/bin/env bash
# PreToolUse hook on the `Skill` tool.
#
# Why: a dispatched sub-agent's tool calls are NOT surfaced to its parent (the
# Agent tool returns only the sub-agent's final result), so you cannot otherwise
# see whether a reviewer/worker actually LOADED an injected `agentSkills` skill.
# This hook records every Skill invocation so loading is observable after a run.
#
# One skill name per line -> readable by humans and by eval graders.
# Log: $CLAUDE_PROJECT_DIR/.skill-invocations.log (falls back to $PWD).
# Never blocks: always exits 0 with no decision output, so the Skill call proceeds.
#
# CAVEAT (unverified): whether PreToolUse hooks fire for *sub-agent* tool calls,
# or only the top-level agent, is a harness behaviour. If this log stays empty
# during a run where a sub-agent demonstrably applied an injected skill, hooks do
# not reach sub-agents and a different probe is needed.

command -v jq >/dev/null 2>&1 || exit 0

skill="$(jq -r '.tool_input.skill // empty' 2>/dev/null)"
[ -n "$skill" ] && printf '%s\n' "$skill" >> "${CLAUDE_PROJECT_DIR:-$PWD}/.skill-invocations.log"

exit 0
