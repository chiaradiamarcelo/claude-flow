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


def scoped_files(output):
    """Map fired reviewer -> the file paths the SCOPE block says it will receive.

    Routing decides *whether* a reviewer runs; scope decides *what it is held to*.
    They are separate failures: a correctly-routed reviewer handed a bare
    directory instead of its matched files can review a familiar subset and
    report a pass on files it never opened, and the `fires:` line looks perfect.
    Absent block -> {} , so a spec that asserts nothing about scope is unaffected.
    """
    block = re.search(r"(?ims)^[ \t]*SCOPE[ \t]*$\n(.*?)(?=^[ \t]*[A-Z]{3,}[ \t]*$|\Z)", output)
    if not block:
        return {}
    scope = {}
    for line in block.group(1).splitlines():
        name, _, paths = line.partition(":")
        if _NAME.match(name.strip()):
            scope[name.strip()] = {p.strip() for p in paths.split(",") if p.strip()}
    return scope


def grade_routing(spec, output):
    """Return a list of failure strings (empty = pass). spec carries fires /
    doesNotFire / mustScope. A None fired-set (no 'fires:' line) is a fault
    unless quarantined."""
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

    scope = scoped_files(output)
    for reviewer, required in (spec.get("mustScope") or {}).items():
        got = scope.get(reviewer)
        if got is None:
            fails.append(f"no SCOPE line for {reviewer!r} — it must be dispatched with its "
                         f"matched file list, not a bare path")
            continue
        for path in required:
            if not any(path in g for g in got):
                fails.append(f"{reviewer} scope is missing {path!r} — got {sorted(got)}")

    # The other half of a wide trigger. `**/src/**` matches
    # node_modules/foo/src/index.ts, and a matched file is now a MANDATORY scope
    # item — so an unfiltered path does not merely add noise, it makes a reviewer
    # answerable for vendored code. Asserting the absence is the only way to tell a
    # working ignore list from one that never ran.
    for reviewer, forbidden in (spec.get("mustNotScope") or {}).items():
        got = scope.get(reviewer) or set()
        for path in forbidden:
            hits = [g for g in got if path in g]
            if hits:
                fails.append(f"{reviewer} scope must not contain {path!r} — got {sorted(hits)}")
    return fails
