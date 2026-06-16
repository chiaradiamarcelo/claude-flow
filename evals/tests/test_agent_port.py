"""Contract test for the Agent port.

The pipeline's own rule: every port with a fake needs a contract test proving the
fake honors the same contract as the real adapter. For an *agent* the contract is
the RunResult shape + the side-effect protocol (stdout, exit code, workspace file
writes) and the call-recording the orchestration relies on — NOT identical
content (that's the model's job). We assert the FakeAgent honors that contract;
the ClaudeCliAgent side is exercised by the real (CLI-marked) evals.
"""
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
from harness.agent import FakeAgent, FakeResponse, RunResult


class FakeAgentContractTest(unittest.TestCase):
    def test_returns_scripted_stdout_and_exit_code(self):
        agent = FakeAgent(script=[FakeResponse(stdout='{"status":"PASS"}', exit_code=0)])

        with tempfile.TemporaryDirectory() as ws:
            result = agent.run(ws, "review the code", agent_name="test-reviewer")

        self.assertIsInstance(result, RunResult)
        self.assertEqual(result.stdout, '{"status":"PASS"}')
        self.assertEqual(result.exit_code, 0)

    def test_applies_file_effects_to_the_workspace(self):
        agent = FakeAgent(script=[FakeResponse(
            writes={"docs/specifications/x/SCENARIO-01.md": "# plan\n- [ ] Step 1\n"})])

        with tempfile.TemporaryDirectory() as ws:
            agent.run(ws, "plan it", agent_name="architect")
            written = Path(ws) / "docs/specifications/x/SCENARIO-01.md"

            self.assertTrue(written.is_file())
            self.assertIn("Step 1", written.read_text())

    def test_records_calls_in_order_for_assertions(self):
        agent = FakeAgent(script=[FakeResponse(), FakeResponse()])

        with tempfile.TemporaryDirectory() as ws:
            agent.run(ws, "first", agent_name="architect", tools=["Read"])
            agent.run(ws, "second", agent_name="developer")

        self.assertEqual([c.agent_name for c in agent.calls], ["architect", "developer"])
        self.assertEqual(agent.calls[0].prompt, "first")
        self.assertEqual(agent.calls[0].tools, ("Read",))

    def test_default_responder_when_script_unsized(self):
        agent = FakeAgent(default=lambda call: FakeResponse(stdout=f"ack:{call.agent_name}"))

        with tempfile.TemporaryDirectory() as ws:
            r1 = agent.run(ws, "a", agent_name="arch-reviewer")
            r2 = agent.run(ws, "b", agent_name="test-reviewer")

        self.assertEqual(r1.stdout, "ack:arch-reviewer")
        self.assertEqual(r2.stdout, "ack:test-reviewer")

    def test_exhausted_script_fails_loudly(self):
        agent = FakeAgent(script=[])

        with tempfile.TemporaryDirectory() as ws:
            with self.assertRaises(AssertionError):
                agent.run(ws, "unscripted", agent_name="developer")


if __name__ == "__main__":
    unittest.main()
