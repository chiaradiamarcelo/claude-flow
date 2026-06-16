#!/usr/bin/env python3
"""Helper for the acceptance fix-loop (run_all.sh Phase 1d).

Reads the captured reviewer verdicts in <reviews_dir>/*.json and either:
  --count     prints the number of VIOLATION findings (the loop's gate signal)
  --findings  prints a '## Review Findings' block (VIOLATION + WARNING only)
              in the shape the developer agent's fix-mode expects — one line per
              finding: file:line [SEVERITY] (reviewer) message.

SUGGESTIONs are deliberately excluded from the fix block: an advisory reviewer
emits them endlessly, so feeding them back would never converge. The loop gates
on VIOLATIONs; WARNINGs are included as should-fixes.
"""
import glob
import json
import os
import sys

FIX_SEVERITIES = ("VIOLATION", "WARNING")


def _issues(reviews_dir):
    out = []
    for p in sorted(glob.glob(os.path.join(reviews_dir, "*.json"))):
        try:
            with open(p) as fh:
                v = json.load(fh)
        except Exception:
            continue
        if not v:
            continue
        reviewer = os.path.basename(p)[:-5]
        for i in (v.get("issues") or []):
            out.append((reviewer, i))
    return out


def main(argv):
    reviews_dir, mode = argv[0], argv[1]
    issues = _issues(reviews_dir)

    if mode == "--count":
        print(sum(1 for _, i in issues if i.get("severity") == "VIOLATION"))
        return 0

    if mode == "--findings":
        fixable = [(r, i) for r, i in issues if i.get("severity") in FIX_SEVERITIES]
        if not fixable:
            print("")
            return 0
        lines = ["## Review Findings", ""]
        for reviewer, i in fixable:
            lines.append(f"- {i.get('file')}:{i.get('line')} [{i.get('severity')}] "
                         f"({reviewer}) {i.get('message', '')}")
        print("\n".join(lines))
        return 0

    print(f"unknown mode {mode!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
