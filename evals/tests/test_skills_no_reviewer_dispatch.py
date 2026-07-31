"""Structural regression lint (pure, model-free, $0).

Pins the root cause of a real bug: the `testing` skill once said "Every new or
modified test must be reviewed by the `test-reviewer` agent." The `developer`
loads `testing` and has the `Agent` tool, so it self-dispatched `test-reviewer`
ONCE PER SCENARIO — instead of review happening once, at the end, via the
pipeline's `/run-reviewers` step. The fake-worker orchestration eval can't catch
this (fakes don't load skills), so we guard it structurally instead: no skill and
no pipeline WORKER agent may instruct its reader to dispatch a reviewer agent.

Descriptive mentions are fine ("Invoke when writing or reviewing", "from a
`refactor-advisor` agent"); only the imperative "route your work to a reviewer"
construction is forbidden.
"""
import re
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]

# Files a pipeline worker reads: every skill, plus the write-side worker agents.
# NOT the reviewer agents themselves (they legitimately talk about reviewing).
SCANNED = sorted(ROOT.glob("skills/*/SKILL.md")) + [
    ROOT / "agents/architect/Agent.md",
    ROOT / "agents/test-designer/Agent.md",
    ROOT / "agents/developer/Agent.md",
]

# The imperative "have this reviewed / dispatch a reviewer" construction.
BAD = re.compile(
    r"must be reviewed by"
    r"|reviewed by (?:the |a )?`?[\w-]*-reviewer"
    r"|(?:dispatch|invoke|run|call)(?:es|ing)?\s+(?:the\s+)?`?(?:[\w-]*-reviewer|refactor-advisor)",
    re.I,
)


class NoReviewerDispatchInSkillsTest(unittest.TestCase):
    def test_no_worker_file_instructs_dispatching_a_reviewer(self):
        offenders = []
        for f in SCANNED:
            if not f.exists():
                continue
            for i, line in enumerate(f.read_text().splitlines(), 1):
                if BAD.search(line):
                    offenders.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()}")
        self.assertEqual(
            offenders, [],
            "A worker-loaded file instructs dispatching a reviewer agent. Review runs "
            "ONCE at the end via the pipeline's /run-reviewers step — remove the "
            "directive:\n" + "\n".join(offenders),
        )

    def test_lint_regex_actually_matches_the_original_bug(self):
        # positive control: the exact line that caused the per-scenario dispatch
        self.assertTrue(
            BAD.search("Every new or modified test must be reviewed by the `test-reviewer` agent.")
        )

    def test_descriptive_mentions_are_not_flagged(self):
        # these SHOULD pass (they exist in real skills)
        self.assertFalse(BAD.search("Invoke when writing or reviewing:"))
        self.assertFalse(BAD.search("Reviewing whether a class is a middleman (e.g. from a `refactor-advisor` agent)."))


if __name__ == "__main__":
    unittest.main()
