#!/usr/bin/env python3
"""Deterministic, model-free eval grader.

Grades recorded agent outputs ("actuals") against per-fixture `expected.json`
specs, with no model and no judgment — only coarse, non-determinism-tolerant
checks: status match, issue-count range, and must-mention substrings. This is
what lets a grader of a non-deterministic agent run as a flake-free gate.

Modes
-----
--check-corpus   Structural only (no actuals): every fixtures/<stem>/expected.json
                 is valid and pairs with a non-empty input/. Free, always-on.
default          Grade --actuals against the corpus.

Exit codes
----------
0  all graded pairs pass (or, with --baseline, no baseline-passing pair regressed)
1  a failure / regression / structural fault was detected
"""
import argparse
import json
import sys
from pathlib import Path


def _load(path):
    with open(path) as f:
        return json.load(f)


def _in_range(n, rng):
    if rng is None:
        return True
    if "min" in rng and n < rng["min"]:
        return False
    if "max" in rng and n > rng["max"]:
        return False
    return True


def _mentions(haystack, needle):
    return needle.lower() in haystack.lower()


def grade_agent(spec, actual):
    """Return a list of failure strings (empty = pass)."""
    fails = []

    if actual is None or "status" not in actual:
        return ["no verdict block emitted (agent did not produce a parseable "
                "<!-- EVAL-VERDICT --> json block)"]

    exp_status = spec.get("expectedStatus")
    got_status = actual.get("status")
    if exp_status is not None and got_status != exp_status:
        fails.append(f"status: expected {exp_status!r}, got {got_status!r}")

    issues = actual.get("issues", []) or []
    count = len(issues)
    rng = spec.get("issueCount")
    if not _in_range(count, rng):
        fails.append(f"issueCount {count} outside expected range {rng}")

    haystack = " ".join(
        str(i.get("message", "")) for i in issues
    ) + " " + str(actual.get("summary", ""))
    for needle in spec.get("mustMention", []):
        if not _mentions(haystack, needle):
            fails.append(f"mustMention: no issue mentioned {needle!r}")

    return fails


def _fixtures(evals_dir):
    fixtures_root = evals_dir / "fixtures"
    if not fixtures_root.is_dir():
        return []
    return sorted(p for p in fixtures_root.iterdir() if (p / "expected.json").is_file())


def check_corpus(evals_dir):
    faults = []
    fixtures = _fixtures(evals_dir)
    if not fixtures:
        faults.append(f"no fixtures with expected.json under {evals_dir}/fixtures")
    for fx in fixtures:
        stem = fx.name
        try:
            spec = _load(fx / "expected.json")
        except (OSError, json.JSONDecodeError) as e:
            faults.append(f"{stem}: invalid expected.json ({e})")
            continue
        for key in ("fixture", "applicableAgents", "agents"):
            if key not in spec:
                faults.append(f"{stem}: expected.json missing key {key!r}")
        input_dir = fx / "input"
        if not input_dir.is_dir() or not any(input_dir.iterdir()):
            faults.append(f"{stem}: missing or empty input/ directory")
    return faults


def run_grading(evals_dir, actuals, baseline_pass, only):
    results = []  # (pair, ok, detail)
    for fx in _fixtures(evals_dir):
        stem = fx.name
        spec = _load(fx / "expected.json")
        for agent, aspec in spec.get("agents", {}).items():
            if only and agent not in only:
                continue
            pair = f"{stem}::{agent}"
            got = actuals.get(stem, {}).get("agents", {}).get(agent)
            fails = grade_agent(aspec, got)
            results.append((pair, not fails, "; ".join(fails)))
    return results


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals-dir", required=True, type=Path)
    ap.add_argument("--actuals", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--only", help="comma-separated agent names to grade")
    ap.add_argument("--check-corpus", action="store_true")
    args = ap.parse_args(argv)

    if args.check_corpus:
        faults = check_corpus(args.evals_dir)
        if faults:
            print("# Corpus check — FAIL\n")
            for f in faults:
                print(f"- {f}")
            return 1
        print(f"# Corpus check — OK ({len(_fixtures(args.evals_dir))} fixtures)")
        return 0

    if not args.actuals:
        print("error: --actuals is required unless --check-corpus", file=sys.stderr)
        return 2

    actuals = _load(args.actuals)
    only = {s.strip() for s in args.only.split(",")} if args.only else None
    baseline_pass = set(_load(args.baseline).get("passing", [])) if args.baseline else None

    results = run_grading(args.evals_dir, actuals, baseline_pass, only)
    passed = [r for r in results if r[1]]

    print(f"# Eval grade — {len(passed)}/{len(results)} pairs passed\n")
    exit_code = 0
    for pair, ok, detail in results:
        if ok:
            print(f"- PASS  {pair}")
        else:
            regressed = baseline_pass is not None and pair in baseline_pass
            tag = "REGRESSION" if regressed else "FAIL"
            print(f"- {tag}  {pair} — {detail}")
            # With a baseline, only regressions red-line the run.
            if baseline_pass is None or regressed:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
