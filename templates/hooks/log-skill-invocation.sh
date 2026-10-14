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
# READING THE LOG — CONFIRMED the hook fires for BOTH top-level agents AND
# dispatched SUB-agents: a real 5-agent /run-pipeline pass logged all 12 Skill
# calls, one line per invocation, no gaps. So the log is a COMPLETE record of
# runtime Skill invocations. It does NOT (by design) record two things:
#   - @-referenced skills. A reviewer that pulls a skill via @skills/.../SKILL.md
#     (e.g. android-ui-test-reviewer -> android-ui-testing) inlines it at
#     prompt-build time — never a Skill call — so it never appears here. Its absence
#     is not failure. (This is exactly why a self-report is unreliable: agents
#     conflate inlined and invoked; the log doesn't.)
#   - a skill the agent was asked to load but chose not to invoke.
# So: a skill IN the log was loaded at runtime; a skill ABSENT was not invoked
# (either inlined via @-ref, or the agent skipped it) — cross with the agent's
# output to tell which. Control: the orchestrator invokes Skill(run-reviewers) /
# Skill(run-pipeline), so one of those MUST appear; if not, the hook is broken
# (wrong $CLAUDE_PROJECT_DIR or matcher not firing) — check that first.

command -v jq >/dev/null 2>&1 || exit 0

skill="$(jq -r '.tool_input.skill // empty' 2>/dev/null)"
[ -n "$skill" ] && printf '%s\n' "$skill" >> "${CLAUDE_PROJECT_DIR:-$PWD}/.skill-invocations.log"

exit 0
