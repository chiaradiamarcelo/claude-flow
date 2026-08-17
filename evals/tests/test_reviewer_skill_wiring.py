"""Harness self-test: reviewers must actually LOAD the skills they call their
source of truth ($0, no model).

A bare `@skills/…/SKILL.md` line in an agent definition is not expanded — Claude
Code passes it through as literal text. Every reviewer relied on one, so every
reviewer was reviewing without its skill, and nothing noticed: `mustMention`
greps the agent's prose, and each Agent.md restates enough of its skill to
satisfy the keyword.

Three deterministic guards, pinned here:
  (a) Phase 0 rejects an inert `@…md` include in any agent definition;
  (b) a dispatch's Skill tool calls are recovered from the event stream;
  (c) `mustInvokeSkills` fails when a required skill was never invoked.
"""
import io
import json
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401  (puts evals/ on sys.path)
from eval_grade import dead_include_faults, grade_agent, _agent_inputs
from extract_verdict import reduce_stream


def _agent_md(body):
    directory = tempfile.mkdtemp()
    path = Path(directory, "Agent.md")
    path.write_text(body)
    return path


def _stream(*events):
    return io.StringIO("\n".join(json.dumps(e) for e in events))


def _skill_call(skill):
    return {"type": "assistant",
            "message": {"content": [{"type": "tool_use", "name": "Skill",
                                     "input": {"skill": skill}}]}}


class DeadIncludeFaultsTest(unittest.TestCase):

    def test_flags_a_bare_include_line(self):
        faults = dead_include_faults(_agent_md("## Rules\n\n@skills/testing/SKILL.md\n"))

        self.assertEqual(1, len(faults))
        self.assertIn("skills/testing/SKILL.md", faults[0])

    def test_flags_an_include_written_as_a_list_item(self):
        faults = dead_include_faults(_agent_md("- @skills/cqrs/SKILL.md — ports\n"))

        self.assertEqual(1, len(faults))

    def test_ignores_a_reference_quoted_inside_prose(self):
        faults = dead_include_faults(
            _agent_md("It supplements the base `@skills/testing/SKILL.md` too.\n")
        )

        self.assertEqual([], faults)

    def test_every_shipped_agent_is_free_of_inert_includes(self):
        offenders = [fault
                     for agent_md in sorted(Path("agents").glob("*/Agent.md"))
                     for fault in dead_include_faults(agent_md)]

        self.assertEqual([], offenders)


class ReduceStreamTest(unittest.TestCase):

    def test_recovers_the_verdict_and_the_invoked_skills(self):
        stream = _stream(
            _skill_call("testing"),
            {"type": "result", "result": 'ok {"status": "FAIL", "issues": []} done'},
        )

        verdict = reduce_stream(stream)

        self.assertEqual("FAIL", verdict["status"])
        self.assertEqual(["testing"], verdict["_skillsInvoked"])

    def test_ignores_tool_calls_that_are_not_skills(self):
        stream = _stream(
            {"type": "assistant",
             "message": {"content": [{"type": "tool_use", "name": "Read",
                                      "input": {"file_path": "a.kt"}}]}},
            {"type": "result", "result": '{"status": "PASS", "issues": []}'},
        )

        verdict = reduce_stream(stream)

        self.assertEqual([], verdict["_skillsInvoked"])

    def test_records_each_skill_once_in_invocation_order(self):
        stream = _stream(
            _skill_call("ui-testing"),
            _skill_call("testing"),
            _skill_call("ui-testing"),
            {"type": "result", "result": '{"status": "PASS", "issues": []}'},
        )

        verdict = reduce_stream(stream)

        self.assertEqual(["ui-testing", "testing"], verdict["_skillsInvoked"])

    def test_survives_an_unparseable_line(self):
        stream = io.StringIO(
            "not json\n" + json.dumps(
                {"type": "result", "result": '{"status": "PASS", "issues": []}'})
        )

        verdict = reduce_stream(stream)

        self.assertEqual("PASS", verdict["status"])

    def test_a_run_with_no_verdict_still_reports_the_skills(self):
        stream = _stream(_skill_call("testing"),
                         {"type": "result", "result": "I could not review that."})

        verdict = reduce_stream(stream)

        self.assertEqual(["testing"], verdict["_skillsInvoked"])
        self.assertNotIn("status", verdict)


class MustInvokeSkillsTest(unittest.TestCase):

    SPEC = {"expectedStatus": "FAIL", "mustInvokeSkills": ["testing"]}

    def test_passes_when_the_required_skill_was_invoked(self):
        fails = grade_agent(self.SPEC, {"status": "FAIL", "issues": [],
                                        "_skillsInvoked": ["testing"]})

        self.assertEqual([], fails)

    def test_fails_when_the_required_skill_was_never_invoked(self):
        fails = grade_agent(self.SPEC, {"status": "FAIL", "issues": [],
                                        "_skillsInvoked": ["cqrs"]})

        self.assertTrue(any("never invoked" in f for f in fails))

    def test_fails_when_no_tool_call_record_was_captured(self):
        fails = grade_agent(self.SPEC, {"status": "FAIL", "issues": []})

        self.assertTrue(any("stream-json" in f for f in fails))

    def test_a_fixture_without_the_key_is_unaffected(self):
        fails = grade_agent({"expectedStatus": "FAIL"},
                            {"status": "FAIL", "issues": []})

        self.assertEqual([], fails)


class FingerprintInputsTest(unittest.TestCase):

    def test_a_required_skill_is_fingerprinted_without_any_include(self):
        inputs = _agent_inputs("test-reviewer", Path("agents"), Path("."), ["testing"])

        self.assertIn(Path("skills/testing/SKILL.md"), inputs)


if __name__ == "__main__":
    unittest.main()
