#!/usr/bin/env python3
"""Production entrypoint for the acceptance pipeline (run_all.sh Phase 1d).

Injects the REAL ClaudeCliAgent + a real `./gradlew test` builder into the
injectable orchestration (pipeline.run_pipeline), then grades with the existing
check_acceptance. The tests inject a FakeAgent + a fake builder into the SAME
run_pipeline — same orchestration code, different adapters.

Usage: run_pipeline.py <expected.json> <scratch-dir>
Exit 0 = accepted (build green + 0 reviewer VIOLATIONs), 1 = not.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

_EVALS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # evals/
sys.path.insert(0, _EVALS)

from harness.agent import ClaudeCliAgent              # noqa: E402
from harness.pipeline import run_pipeline             # noqa: E402
import check_acceptance                                # noqa: E402

ARCH_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Skill"]
DEV_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
REV_TOOLS = ["Read", "Glob", "Grep"]
INTENT_TOOLS = ["Read", "Write", "Glob", "Grep", "Skill"]


def gradle_build(workspace) -> int:
    """Run the build ourselves — the independent verdict (never the agent's word)."""
    log = Path(workspace) / ".gradle.log"
    with open(log, "w") as fh:
        proc = subprocess.run(["./gradlew", "test", "--console=plain"],
                              cwd=str(workspace), stdout=fh, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL)
    return proc.returncode


def main(argv):
    expected_path, scratch = argv[0], argv[1]
    cfg = json.load(open(expected_path))

    outcome = run_pipeline(
        ClaudeCliAgent(), scratch, cfg, gradle_build,
        arch_tools=ARCH_TOOLS, dev_tools=DEV_TOOLS,
        rev_tools=REV_TOOLS, intent_tools=INTENT_TOOLS,
    )
    if outcome.rounds:
        print(f"  fix rounds used: {outcome.rounds}")

    spec = cfg.get("agents", {}).get("pipeline", {})
    stem = cfg.get("fixture", os.path.basename(os.path.dirname(expected_path)))
    fails, notes, reviews = check_acceptance.grade(spec, scratch, outcome.build_exit)

    summary = []
    for name, v in sorted(reviews.items()):
        c = {}
        for i in ((v or {}).get("issues") or []):
            c[i.get("severity")] = c.get(i.get("severity"), 0) + 1
        summary.append(f"{name}={(v or {}).get('status','?')}"
                       f"({c.get('VIOLATION',0)}V/{c.get('WARNING',0)}W/{c.get('SUGGESTION',0)}S)")

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
