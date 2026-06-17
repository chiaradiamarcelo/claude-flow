#!/usr/bin/env python3
"""Grader for the CLAUDE.md orchestration (choreography) test.

The real orchestrator ran the pipeline over FAKE worker agents that logged each
invocation to a call log. This grades the *choreography* recorded there — NOT
agent quality. Tolerant, like the reviewer graders: assert the key events appear
in the right ORDER (an ordered subsequence — extra entries, e.g. other reviewers
interleaved, are fine), not an exact transcript.

Inputs: check_choreography.py <expected.json> --scratch-dir <run dir>
Reads <scratch>/<logFile>.

Checks (under "orchestration" in expected.json):
  logFile             : the call-log filename the fakes append to
  expectedSubsequence : [str] — must appear in this order in the log
  endsAfterReview     : bool — the last log entry is a reviewer, not a developer
                        (i.e. it stopped after a passing review, no dangling fix)
  maxArchitects       : int  — architect dispatched at most N times (one scenario,
                        not re-planned in a loop)

Exit 0 = pass, 1 = fail.
"""
import argparse
import json
import os
import sys


def _is_subsequence(needles, haystack):
    """True iff `needles` appears in order within `haystack` (gaps allowed).
    Returns (ok, first_missing_index)."""
    i = 0
    for item in haystack:
        if i < len(needles) and item == needles[i]:
            i += 1
    return (i == len(needles), i)


def grade(spec, log_lines):
    fails = []

    seq = spec.get("expectedSubsequence", [])
    ok, reached = _is_subsequence(seq, log_lines)
    if not ok:
        fails.append(f"expectedSubsequence: matched {reached}/{len(seq)} in order "
                     f"({seq[reached]!r} not found after the earlier events). "
                     f"log={log_lines}")

    if spec.get("endsAfterReview"):
        if not log_lines:
            fails.append("endsAfterReview: the call log is empty")
        elif log_lines[-1].startswith("developer"):
            fails.append(f"endsAfterReview: log ends on {log_lines[-1]!r} — a "
                         f"developer dispatch with no following review (didn't stop on PASS)")

    max_arch = spec.get("maxArchitects")
    if max_arch is not None:
        n = sum(1 for ln in log_lines if ln == "architect")
        if n > max_arch:
            fails.append(f"maxArchitects: architect dispatched {n} times (allowed {max_arch})")

    return fails


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("--scratch-dir", required=True)
    args = ap.parse_args(argv)

    doc = json.load(open(args.expected))
    spec = doc.get("orchestration", {})
    stem = doc.get("fixture", os.path.basename(os.path.dirname(args.expected)))

    log_path = os.path.join(args.scratch_dir, spec.get("logFile", "pipeline-calls.log"))
    try:
        with open(log_path) as fh:
            log_lines = [ln.strip() for ln in fh if ln.strip()]
    except OSError:
        log_lines = []

    fails = grade(spec, log_lines)
    if fails:
        print(f"- FAIL  {stem}::orchestration")
        for f in fails:
            print(f"    · {f}")
        return 1
    print(f"- PASS  {stem}::orchestration  (log: {' -> '.join(log_lines)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
