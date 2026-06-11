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


_NAME = re.compile(r"^[a-z0-9][a-z0-9-]*$")

def fired_set(output):
    """Extract the reviewer names from the command's `fires:` line, or None.

    Only kebab-case tokens are kept. The model occasionally lets the next
    `skips:` line bleed onto the `fires:` line; such a token ("skips: api-reviewer")
    carries a space/colon and is dropped — it is not a fired reviewer. A
    genuinely over-fired reviewer name still matches and still counts, so this
    removes format noise without masking a real misroute."""
    m = re.search(r"(?im)^\s*fires:\s*(.*)$", output)
    if not m:
        return None
    return {tok for raw in m.group(1).split(",")
            if (tok := raw.strip()) and _NAME.match(tok)}


def main(argv):
    expected = json.load(open(argv[0]))
    output = open(argv[1]).read()
    name = expected.get("fixture", argv[0])
    # A quarantined fixture still runs and reports its real result, but never
    # gates (exit 0 either way). Use it for genuinely flaky pairs — e.g. a
    # universal-negative routing case where the model occasionally over-fires
    # despite an explicit instruction. See evals/README.md (pass@k / quarantine).
    quarantined = bool(expected.get("quarantine"))

    fired = fired_set(output)
    if fired is None:
        print(f"{'QUAR' if quarantined else 'FAIL'}  {name} — no 'fires:' line in command output")
        return 0 if quarantined else 1

    fails = []
    for r in expected.get("fires", []):
        if r not in fired:
            fails.append(f"expected {r!r} to fire — it did not")
    for r in expected.get("does_not_fire", []):
        if r in fired:
            fails.append(f"expected {r!r} NOT to fire — it did")

    if fails:
        label = "QUAR" if quarantined else "FAIL"
        suffix = "  [quarantined — non-gating]" if quarantined else ""
        print(f"{label}  {name}  (fired: {sorted(fired)}){suffix}")
        for f in fails:
            print(f"      - {f}")
        return 0 if quarantined else 1

    print(f"PASS  {name}  (fired: {sorted(fired)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
