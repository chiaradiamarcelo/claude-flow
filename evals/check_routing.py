#!/usr/bin/env python3
"""Grader for /run-reviewers routing tests (the live command test).

Given a fixture's expected.json and the captured `--dry-run` command output,
assert the right reviewers fired. Deterministic, model-free — the assertion half
of the live test (the `claude -p` run is the model half).

Assertion is tolerant: every reviewer in `fires` must appear in the command's
`fires:` line, and none of `does_not_fire` may — but extra reviewers (e.g. a
newly added one) don't fail the test.

Usage: check_routing.py <expected.json> <command-output-file>
Exit 0 = pass, 1 = fail.
"""
import json
import re
import sys


def fired_set(output):
    """Extract the reviewer names from the command's `fires:` line, or None."""
    m = re.search(r"(?im)^\s*fires:\s*(.*)$", output)
    if not m:
        return None
    return {name.strip() for name in m.group(1).split(",") if name.strip()}


def main(argv):
    expected = json.load(open(argv[0]))
    output = open(argv[1]).read()
    name = expected.get("fixture", argv[0])

    fired = fired_set(output)
    if fired is None:
        print(f"FAIL  {name} — no 'fires:' line in command output")
        return 1

    fails = []
    for r in expected.get("fires", []):
        if r not in fired:
            fails.append(f"expected {r!r} to fire — it did not")
    for r in expected.get("does_not_fire", []):
        if r in fired:
            fails.append(f"expected {r!r} NOT to fire — it did")

    if fails:
        print(f"FAIL  {name}  (fired: {sorted(fired)})")
        for f in fails:
            print(f"      - {f}")
        return 1

    print(f"PASS  {name}  (fired: {sorted(fired)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
