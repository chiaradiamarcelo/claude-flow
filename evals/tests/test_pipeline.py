"""Harness self-test: the pipeline orchestration / fix-loop control flow.

Drives the REAL run_pipeline (the same code run_all.sh Phase 1d uses in
production) with a FakeAgent + a fake builder. Tests OUR control flow — loop
counting, termination, findings-passing, dispatch order — NOT the agents'
judgement. Deterministic, $0; today this logic costs real opus rounds to run.
"""
import json
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
from harness.agent import FakeAgent, FakeResponse
from harness.pipeline import run_pipeline, count_violations
import check_acceptance


def _verdict(status, issues):
    return json.dumps({"status": status, "issues": issues, "summary": ""})


def _clean():
    return FakeResponse(stdout=_verdict("PASS", []))


def _review_round(n_violations):
    """The 3 reviewer responses for one review pass (ROUTES order: test, arch,
    refactor). All violations land on test-reviewer; the other two are clean."""
    issues = [{"severity": "VIOLATION", "file": "C.kt", "line": i + 1, "message": "bad"}
              for i in range(n_violations)]
    test_rev = FakeResponse(stdout=_verdict("FAIL" if issues else "PASS", issues))
    return [test_rev, _clean(), _clean()]


def _fake_build_pass(workspace):
    """Stand-in for ./gradlew test: write a passing JUnit report, return 0."""
    d = Path(workspace) / "build" / "test-results" / "test"
    d.mkdir(parents=True, exist_ok=True)
    (d / "TEST-x.xml").write_text(
        '<testsuite tests="2" failures="0" errors="0" skipped="0">'
        '<testcase classname="WithdrawMoneyTest" name="reduces"/>'
        '<testcase classname="WithdrawMoneyTest" name="rejects"/></testsuite>')
    return 0


BASE_CFG = {
    "fixture": "t",
    "developerPrompt": "implement it",
    "developerFixPrompt": "fix it",
    "agents": {"pipeline": {"maxFixRounds": 2, "maxViolations": 0, "minTests": 2}},
}


class FixLoopControlFlowTest(unittest.TestCase):
    def test_clean_first_pass_runs_no_fix_rounds(self):
        agent = FakeAgent(script=[FakeResponse(), *_review_round(0)])  # developer, then clean reviews

        with tempfile.TemporaryDirectory() as ws:
            outcome = run_pipeline(agent, ws, BASE_CFG, _fake_build_pass)

        self.assertEqual(outcome.rounds, 0)
        self.assertEqual(count_violations(outcome.reviews), 0)

    def test_fail_then_pass_runs_one_round_and_feeds_findings(self):
        agent = FakeAgent(script=[
            FakeResponse(),            # developer (impl)
            *_review_round(2),         # review #1 → 2 violations
            FakeResponse(),            # developer (fix)
            *_review_round(0),         # review #2 → clean
        ])

        with tempfile.TemporaryDirectory() as ws:
            outcome = run_pipeline(agent, ws, BASE_CFG, _fake_build_pass)

        self.assertEqual(outcome.rounds, 1)
        self.assertEqual(count_violations(outcome.reviews), 0)
        fix_call = [c for c in agent.calls if c.agent_name == "developer"][1]
        self.assertIn("Review Findings", fix_call.prompt)
        self.assertIn("VIOLATION", fix_call.prompt)

    def test_never_converging_stops_at_max_fix_rounds(self):
        agent = FakeAgent(script=[
            FakeResponse(), *_review_round(2),   # impl + review (2)
            FakeResponse(), *_review_round(2),   # fix round 1 + review (2)
            FakeResponse(), *_review_round(2),   # fix round 2 + review (2)
        ])

        with tempfile.TemporaryDirectory() as ws:
            outcome = run_pipeline(agent, ws, BASE_CFG, _fake_build_pass)

            self.assertEqual(outcome.rounds, 2)               # bounded — didn't loop forever
            self.assertGreater(count_violations(outcome.reviews), 0)
            # and the official grader rejects it on the surviving VIOLATIONs
            fails, _notes, _reviews = check_acceptance.grade(
                BASE_CFG["agents"]["pipeline"], ws, outcome.build_exit)
            self.assertTrue(any("maxViolations" in f for f in fails))

    def test_full_chain_dispatches_in_order(self):
        cfg = dict(BASE_CFG,
                   intentPrompt="/intent-and-goal do X",
                   architectPrompt="plan it")
        agent = FakeAgent(script=[
            FakeResponse(),   # intent
            FakeResponse(),   # architect
            FakeResponse(),   # developer
            *_review_round(0),
        ])

        with tempfile.TemporaryDirectory() as ws:
            run_pipeline(agent, ws, cfg, _fake_build_pass)

        names = [c.agent_name for c in agent.calls]
        self.assertIsNone(names[0])                 # intent: a command, no --agent
        self.assertEqual(names[1], "architect")
        self.assertEqual(names[2], "developer")
        self.assertEqual(names[3], "test-reviewer")  # reviewers only after the build
        # architect strictly before developer strictly before any reviewer
        self.assertLess(names.index("architect"), names.index("developer"))
        self.assertLess(names.index("developer"), names.index("test-reviewer"))


if __name__ == "__main__":
    unittest.main()
