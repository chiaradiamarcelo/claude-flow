#!/usr/bin/env python3
"""Deterministic, model-free grader for the `developer` agent (integration layer).

The developer is generative *and* its only honest grade is an objective build
outcome: after it implements a scenario, do the generated tests compile and
pass? So this grader does not look at prose or the agent's self-report — it
inspects the **JUnit XML** that `./gradlew test` produced in the scratch repo and
the build's exit code.

Inputs
------
  check_build.py <expected.json> --scratch-dir <run dir> --build-exit <code>

`--build-exit` is the exit code of the independent `./gradlew test` the harness
ran *after* the developer finished (never trust the agent's own run). Test
reports are read from `<scratch>/build/test-results/test/*.xml`.

Checks (declared per fixture under agents.developer)
------
  buildMustPass      : bool   — ./gradlew test exited 0
  minTests           : int    — at least N tests actually ran (executed, not skipped)
  maxFailures        : int    — at most N failing/erroring tests (default 0)
  mustHaveTestClasses: [str]   — each substring appears in some testcase classname

A vacuous pass (build green, 0 tests) is caught by minTests + the explicit
"no test results" fault when the XML dir is empty/missing (a compile failure
produces no reports).

Exit codes: 0 pass · 1 a check failed / structural fault.
"""
import argparse
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET


def _collect(scratch_dir):
    """Return (ran, failed, classnames) parsed from JUnit XML, or None if no reports."""
    pat = os.path.join(scratch_dir, "build", "test-results", "test", "*.xml")
    files = glob.glob(pat)
    if not files:
        return None
    ran = failed = 0
    classnames = set()
    for f in files:
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError:
            continue
        suites = [root] if root.tag == "testsuite" else root.iter("testsuite")
        for s in suites:
            tests = int(s.get("tests", 0))
            skipped = int(s.get("skipped", 0))
            failures = int(s.get("failures", 0))
            errors = int(s.get("errors", 0))
            ran += tests - skipped
            failed += failures + errors
            for tc in s.iter("testcase"):
                cn = tc.get("classname", "")
                if cn:
                    classnames.add(cn)
    return ran, failed, classnames


def grade_build(spec, scratch_dir, build_exit):
    fails = []

    if spec.get("buildMustPass") and build_exit != 0:
        fails.append(f"buildMustPass: ./gradlew test exited {build_exit} (compile or test failure)")

    collected = _collect(scratch_dir)
    if collected is None:
        fails.append("no JUnit test reports under build/test-results/test/ — the "
                     "build never reached the test phase (likely a compile failure)")
        return fails

    ran, failed, classnames = collected

    max_failures = spec.get("maxFailures", 0)
    if failed > max_failures:
        fails.append(f"maxFailures: {failed} failing/erroring tests (allowed {max_failures})")

    min_tests = spec.get("minTests")
    if min_tests is not None and ran < min_tests:
        fails.append(f"minTests: {ran} tests ran, expected >= {min_tests} "
                     f"(guards against a vacuous 0-test pass)")

    for needle in spec.get("mustHaveTestClasses", []):
        if not any(needle.lower() in cn.lower() for cn in classnames):
            fails.append(f"mustHaveTestClasses: no test class matches {needle!r} "
                         f"(saw: {sorted(classnames) or 'none'})")

    return fails


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("expected", type=str)
    ap.add_argument("--scratch-dir", required=True)
    ap.add_argument("--build-exit", type=int, required=True)
    args = ap.parse_args(argv)

    doc = json.load(open(args.expected))
    spec = doc.get("agents", {}).get("developer", {})
    stem = doc.get("fixture", os.path.basename(os.path.dirname(args.expected)))

    fails = grade_build(spec, args.scratch_dir, args.build_exit)
    if fails:
        print(f"- FAIL  {stem}::developer")
        for f in fails:
            print(f"    · {f}")
        return 1
    print(f"- PASS  {stem}::developer")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
