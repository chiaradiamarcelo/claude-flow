#!/usr/bin/env python3
"""Grader for /run-pipeline agentSkills injection (the live command test).

`agentSkills` in `.claude/pipeline.json` is ADDITIVE: each pipeline agent loads
its own core skills PLUS whatever the project injects, keyed by agent name. The
`/run-pipeline --dry-run` command resolves the injection and prints a
machine-greppable block listing, per agent, the skills the project adds (NOT the
core set — the command must not restate what lives in the agent bodies):

    SKILLS
    architect: (none)
    test-designer: android-testing
    developer: android-testing, android-ui-testing
    test-reviewer: android-testing

This grader is the deterministic half (the `claude -p` run is the model half).
`grade_skills(spec, output)` is the pure entrypoint the engine calls.

spec fields:
- `injects`:     {agent: [skill, ...]} — each agent's injected set must match EXACTLY
                 (additive routing is correct only if the project's skills, and no
                 others, reach that agent).
- `noInjection`: [agent, ...] — these agents must receive NO project skills.
"""
import re

_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_LINE = re.compile(r"^[ \t]*([a-z][a-z0-9-]*)[ \t]*:[ \t]*(.*)$", re.I)
_EMPTY = {"", "(none)", "none", "-"}


def parse_skills(output):
    """Return {agent: set(skills)} from the SKILLS block, or None if absent.

    Only lines after a `SKILLS` header are read, and only until a blank line or a
    line that isn't an `agent: csv` row — so surrounding prose can't leak in."""
    lines = output.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.strip().upper() == "SKILLS"), None)
    if start is None:
        return None
    out = {}
    for ln in lines[start + 1:]:
        if ln.strip() == "":
            break
        m = _LINE.match(ln)
        if not m:
            break
        agent, rest = m.group(1), m.group(2).strip()
        skills = set()
        if rest.lower() not in _EMPTY:
            skills = {tok for raw in rest.split(",")
                      if (tok := raw.strip()) and _NAME.match(tok)}
        out[agent] = skills
    return out


def grade_skills(spec, output):
    """Return a list of failure strings (empty = pass)."""
    parsed = parse_skills(output)
    if parsed is None:
        return ["no 'SKILLS' block in command output"]
    fails = []
    for agent, want in spec.get("injects", {}).items():
        got = parsed.get(agent)
        if got is None:
            fails.append(f"agent {agent!r} missing from SKILLS block")
        elif got != set(want):
            fails.append(f"agent {agent!r} injected {sorted(got)}, expected {sorted(set(want))}")
    for agent in spec.get("noInjection", []):
        got = parsed.get(agent, set())
        if got:
            fails.append(f"agent {agent!r} must receive no project skills, got {sorted(got)}")
    return fails
