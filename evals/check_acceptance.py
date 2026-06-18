#!/usr/bin/env python3
"""Acceptance grader for the FULL pipeline (architect -> developer -> reviewers).

The top of the confidence pyramid. After the architect plans a scenario and the
developer implements it, this grades the only signals that say the *tool works*:

  1. the generated code compiles and its tests pass  (objective build outcome)
  2. the reviewers — the consistency oracle — find NO must-fix VIOLATION in what
     the producers built  (the cross-artifact drift alarm)

WARNING / SUGGESTION findings are reported but non-gating: an advisory reviewer
(refactor-advisor) always finds *something*, so gating on VIOLATIONs is the
meaningful "no drift, no must-fix defect" floor. (See the strict-gate discussion
— this grader deliberately does not require an all-clean PASS.)

`grade(spec, scratch_dir, build_exit)` is the pure entrypoint the engine calls.
Build results come from the JUnit XML the harness's independent `./gradlew test`
produced; reviewer verdicts from `<scratch>/.reviews/<reviewer>.json` (each a
machine-first verdict the harness captured).

Checks (spec keys)
------
  buildMustPass     : bool   — ./gradlew test exited 0
  minTests          : int    — >= N tests actually ran
  maxFailures       : int    — <= N failing/erroring tests (default 0)
  reviewersMustRun  : [str]   — each named reviewer produced a parseable verdict
  maxViolations     : int    — <= N reviewer VIOLATIONs total (default 0)
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_build import _collect  # noqa: E402  (reuse the JUnit XML parser)


def _reviews(scratch_dir):
    out = {}
    for p in glob.glob(os.path.join(scratch_dir, ".reviews", "*.json")):
        name = os.path.basename(p)[:-5]
        try:
            with open(p) as fh:
                out[name] = json.load(fh)
        except Exception:
            out[name] = None
    return out


def grade(spec, scratch_dir, build_exit):
    fails, notes = [], []

    if spec.get("buildMustPass") and build_exit != 0:
        fails.append(f"buildMustPass: ./gradlew test exited {build_exit} (compile or test failure)")

    collected = _collect(scratch_dir)
    if collected is None:
        fails.append("no JUnit reports — the build never reached the test phase "
                     "(likely a compile failure)")
    else:
        ran, failed, _ = collected
        if failed > spec.get("maxFailures", 0):
            fails.append(f"maxFailures: {failed} failing/erroring tests")
        mt = spec.get("minTests")
        if mt is not None and ran < mt:
            fails.append(f"minTests: {ran} tests ran, expected >= {mt}")

    reviews = _reviews(scratch_dir)
    for r in spec.get("reviewersMustRun", []):
        v = reviews.get(r)
        if not v or "status" not in v:
            fails.append(f"reviewersMustRun: {r} did not produce a parseable verdict")

    total_viol = 0
    for name, v in reviews.items():
        if not v:
            continue
        for i in (v.get("issues") or []):
            if i.get("severity") == "VIOLATION":
                total_viol += 1
                notes.append(f"VIOLATION [{name}] {i.get('file')}:{i.get('line')} "
                             f"{str(i.get('message', ''))[:160]}")

    maxv = spec.get("maxViolations", 0)
    if total_viol > maxv:
        fails.append(f"maxViolations: reviewers found {total_viol} VIOLATION(s) (allowed {maxv})")

    return fails, notes, reviews
