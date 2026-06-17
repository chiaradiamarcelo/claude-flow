#!/usr/bin/env python3
"""Independent verifier for the acceptance pipeline (run_all.sh Phase 1d).

The REAL `/run-pipeline` command already orchestrated the feature (architect →
developer → reviewers → its own fix-loop). This does NOT trust that: it
independently runs `./gradlew test` and a fresh reviewer pass over the produced
code, then grades with check_acceptance (build green + zero reviewer VIOLATIONs).

Same "never trust the agent's self-report" rule the rest of the harness follows —
the producer ran reviewers to fix; WE run them to judge.

Usage: verify_acceptance.py <expected.json> <scratch-dir>
Exit 0 = accepted, 1 = not.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # evals/
import check_acceptance  # noqa: E402

# Same glob routing as the reviewers' triggers: tests -> test-reviewer;
# main -> arch-reviewer + refactor-advisor (no api/ui code in the core slice).
ROUTES = (("test-reviewer", "src/test"),
          ("arch-reviewer", "src/main"),
          ("refactor-advisor", "src/main"))
REV_TOOLS = ["Read", "Glob", "Grep"]
REVIEW_PROMPT = ("Review the Kotlin source file(s) under {d}/ (read them directly with "
                 "the Read tool). Return ONLY your machine-first JSON verdict.")
_JSON = re.compile(r"\{.*\}", re.S)


def gradle_build(ws) -> int:
    log = Path(ws) / ".gradle.log"
    with open(log, "w") as fh:
        proc = subprocess.run(["./gradlew", "test", "--console=plain"],
                              cwd=str(ws), stdout=fh, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL)
    return proc.returncode


def review(ws, reviewer, d) -> dict:
    proc = subprocess.run(
        ["claude", "-p", REVIEW_PROMPT.format(d=d), "--agent", reviewer,
         "--allowedTools", *REV_TOOLS],
        cwd=str(ws), capture_output=True, text=True, stdin=subprocess.DEVNULL)
    m = _JSON.search(proc.stdout or "")
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def main(argv):
    expected_path, scratch = argv[0], argv[1]
    cfg = json.load(open(expected_path))
    spec = cfg.get("agents", {}).get("pipeline", {})
    stem = cfg.get("fixture", os.path.basename(os.path.dirname(expected_path)))

    build_exit = gradle_build(scratch)

    rdir = Path(scratch) / ".reviews"
    rdir.mkdir(parents=True, exist_ok=True)
    for old in rdir.glob("*.json"):
        old.unlink()
    for reviewer, d in ROUTES:
        (rdir / f"{reviewer}.json").write_text(json.dumps(review(scratch, reviewer, d)))

    fails, notes, reviews = check_acceptance.grade(spec, scratch, build_exit)

    summary = []
    for name, v in sorted(reviews.items()):
        c = {}
        for i in ((v or {}).get("issues") or []):
            c[i.get("severity")] = c.get(i.get("severity"), 0) + 1
        summary.append(f"{name}={(v or {}).get('status', '?')}"
                       f"({c.get('VIOLATION', 0)}V/{c.get('WARNING', 0)}W/{c.get('SUGGESTION', 0)}S)")

    tag = "FAIL " if fails else "PASS "
    print(f"- {tag} {stem}::pipeline")
    for f in fails:
        print(f"    · {f}")
    for n in notes:
        print(f"    · {n}")
    if summary:
        print(f"    reviewers: {' '.join(summary)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
