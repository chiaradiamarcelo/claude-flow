#!/usr/bin/env python3
"""Grader for a command's REFUSAL guard (e.g. /run-pipeline with no approved spec).

The command should STOP at its precondition: write no code and report why — never
dispatch a worker. We assert the negative (nothing was produced) plus a tolerant
substring in the command's output. Lives alongside check_choreography (same CLI);
run_all.sh Phase 1f picks the grader by which block the fixture carries.

Inputs: check_refusal.py <expected.json> --scratch-dir <run dir>
Reads <scratch>/.orchestrator.log for the command's stdout.

Checks (under "refusal" in expected.json):
  mustNotWrite : [str] — none of these paths may exist in the scratch afterwards
                 (e.g. "src/main", "src/test" — proof it wrote no code)
  mustMention  : [str] — each substring (case-insensitive) appears in the output
"""
import argparse
import json
import os
import sys


def grade(spec, scratch_dir, output):
    fails = []
    low = (output or "").lower()

    for path in spec.get("mustNotWrite", []):
        full = os.path.join(scratch_dir, path)
        if os.path.exists(full) and (not os.path.isdir(full) or os.listdir(full)):
            fails.append(f"mustNotWrite: {path!r} exists — the guard did not stop "
                         f"before producing output")

    for needle in spec.get("mustMention", []):
        if needle.lower() not in low:
            fails.append(f"mustMention: {needle!r} not found in the command output")

    return fails


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("--scratch-dir", required=True)
    args = ap.parse_args(argv)

    doc = json.load(open(args.expected))
    spec = doc.get("refusal", {})
    stem = doc.get("fixture", os.path.basename(os.path.dirname(args.expected)))

    log_path = os.path.join(args.scratch_dir, ".orchestrator.log")
    try:
        with open(log_path) as fh:
            output = fh.read()
    except OSError:
        output = ""

    fails = grade(spec, args.scratch_dir, output)
    if fails:
        print(f"- FAIL  {stem}::refusal")
        for f in fails:
            print(f"    · {f}")
        return 1
    print(f"- PASS  {stem}::refusal")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
