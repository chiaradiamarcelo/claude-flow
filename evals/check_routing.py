#!/usr/bin/env python3
"""Grader for /run-reviewers routing tests (the live command test).

Given the captured `--dry-run` command output, assert the right reviewers fired.
Deterministic, model-free — the assertion half of the live test (the `claude -p`
run is the model half). `grade_routing(spec, output)` is the pure entrypoint the
engine calls.

Assertion is tolerant: every reviewer in `fires` must appear in the command's
`fires:` line, and none of `doesNotFire` may — but extra reviewers (e.g. a
newly added one) don't fail the test.
"""
import re


_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")

def fired_set(output):
    """Extract the reviewer names from the command's `fires:` line, or None.

    Only kebab-case tokens are kept. The model occasionally lets the next
    `skips:` line bleed onto the `fires:` line; such a token ("skips: api-reviewer")
    carries a space/colon and is dropped — it is not a fired reviewer. A
    genuinely over-fired reviewer name still matches and still counts, so this
    removes format noise without masking a real misroute."""
    # [ \t] (not \s) after the colon: \s includes \n, so on an EMPTY `fires:`
    # line it would swallow the newline and capture the next line (`skips:`),
    # reporting the skipped reviewers as fired. That bug only ever bites the
    # universal-negative (empty fires) case.
    m = re.search(r"(?im)^[ \t]*fires:[ \t]*(.*)$", output)
    if not m:
        return None
    return {tok for raw in m.group(1).split(",")
            if (tok := raw.strip()) and _NAME.match(tok)}


def grade_routing(spec, output):
    """Return a list of failure strings (empty = pass). spec carries fires /
    doesNotFire. A None fired-set (no 'fires:' line) is a fault unless quarantined."""
    fired = fired_set(output)
    if fired is None:
        return ["no 'fires:' line in command output"]
    fails = []
    for r in spec.get("fires", []):
        if r not in fired:
            fails.append(f"expected {r!r} to fire — it did not")
    for r in spec.get("doesNotFire", []):
        if r in fired:
            fails.append(f"expected {r!r} NOT to fire — it did")
    return fails
