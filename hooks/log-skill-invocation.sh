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
# READING THE LOG — an EMPTY log is AMBIGUOUS, do not conclude from it alone:
#   - control first: the main loop invokes Skill(run-reviewers), so `run-reviewers`
#     MUST appear in the log. If even that is missing, the hook itself is broken
#     (wrong $CLAUDE_PROJECT_DIR, matcher not firing) — fix that before reading on.
#     (Firing is CONFIRMED for a top-level `claude -p --agent` dispatch — the
#     test-reviewer/loads-injected-android-testing eval logs `android-testing`. The
#     open question is only whether it also fires for a dispatched SUB-agent.)
#   - with the control present, cross the log against the reviewer's BEHAVIOUR on a
#     file that violates an injected-skill rule: log-has-skill => loaded (works,
#     hooks reach sub-agents). log-empty + rule applied anyway => it loaded but the
#     hook didn't capture the sub-agent's Skill call => hooks don't reach sub-agents
#     (fall back to the behavioural probe). log-empty + rule NOT applied on a file
#     that violates it => the agent ignored the injection => inline the skill.
#   - a reviewer that @-references a skill (e.g. android-ui-test-reviewer ->
#     android-ui-testing) inlines it and never calls Skill for it; only its
#     INJECTED skills appear here. Absence of an @-referenced skill is not failure.

command -v jq >/dev/null 2>&1 || exit 0

skill="$(jq -r '.tool_input.skill // empty' 2>/dev/null)"
[ -n "$skill" ] && printf '%s\n' "$skill" >> "${CLAUDE_PROJECT_DIR:-$PWD}/.skill-invocations.log"

exit 0
