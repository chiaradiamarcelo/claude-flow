#!/usr/bin/env python3
"""Deterministic, model-free grader for the `/intent-and-goal` command.

`/intent-and-goal` is a *command* (not an agent) and it's interactive — it asks
clarifying questions and waits for approval before writing the SoT
`specification.md`. Headless (`claude -p`) it's run NON-INTERACTIVELY (the
fixture prompt tells it to assume + proceed). This grades the artifact it
writes: the `specification.md`, the same "grade the artifact, not stdout"
approach as `check_plan.py` (the architect).

Inputs
------
  check_spec.py <expected.json> --input-dir <fixture input/> --scratch-dir <run dir>

Checks (under agents["intent-and-goal"])
------
  specMustExist : bool   — a new specification.md was created under specifications/
  writesNoCode  : bool   — no source file (code extension) was created
  minScenarios  : int    — the spec has >= N Gherkin `Scenario:` blocks
  mustMention   : [str]   — each substring (case-insensitive) appears in the spec
  mustNotMention: [str]   — none of these appear

Exit codes: 0 pass · 1 a check failed.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_plan import _new_files, _code_files  # noqa: E402  (shared artifact diff)

SCENARIO_RE = re.compile(r"^\s*Scenario:", re.M)


def _spec_files(new_files):
    return sorted(f for f in new_files
                  if re.search(r"specification\.md$", f, re.I)
                  and "specifications/" in f)


def grade_spec(spec, input_dir, scratch_dir):
    fails = []
    new = _new_files(input_dir, scratch_dir)
    specs = _spec_files(new)
    code = _code_files(new)

    if spec.get("specMustExist") and not specs:
        fails.append("specMustExist: no new specification.md created under docs/specifications/")
    if spec.get("writesNoCode") and code:
        fails.append(f"writesNoCode: created source file(s) {code} (should write only the spec .md)")

    text = "\n".join(open(os.path.join(scratch_dir, p)).read() for p in specs)

    ms = spec.get("minScenarios")
    if ms is not None:
        n = len(SCENARIO_RE.findall(text))
        if n < ms:
            fails.append(f"minScenarios: {n} Gherkin Scenario blocks, expected >= {ms}")

    hay = text.lower()
    for needle in spec.get("mustMention", []):
        if needle.lower() not in hay:
            fails.append(f"mustMention: spec never mentions {needle!r}")
    for needle in spec.get("mustNotMention", []):
        if needle.lower() in hay:
            fails.append(f"mustNotMention: spec mentions {needle!r} but should not")

    return fails


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--scratch-dir", required=True)
    args = ap.parse_args(argv)

    doc = json.load(open(args.expected))
    spec = doc.get("agents", {}).get("intent-and-goal", {})
    stem = doc.get("fixture", os.path.basename(os.path.dirname(args.expected)))

    fails = grade_spec(spec, args.input_dir, args.scratch_dir)
    if fails:
        print(f"- FAIL  {stem}::intent-and-goal")
        for f in fails:
            print(f"    · {f}")
        return 1
    print(f"- PASS  {stem}::intent-and-goal")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
