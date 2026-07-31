"""Harness self-test: the /run-pipeline agentSkills PARSER + grader (check_skills).

Pins the additive-injection contract deterministically ($0, no model): the
`SKILLS` block lists ONLY the project-injected skills per agent, and the grader
must (a) require an agent's injected set to match exactly, (b) flag a missing
agent, (c) flag skills leaking into a no-injection agent, and (d) not read prose
outside the block.
"""
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401  (puts evals/ on sys.path)
from check_skills import parse_skills, grade_skills, grade_skill_loaded, read_skill_log

_BLOCK = (
    "SKILLS\n"
    "architect: (none)\n"
    "test-designer: android-testing\n"
    "developer: android-testing, android-ui-testing\n"
    "test-reviewer: android-testing\n"
)


class ParseSkillsTest(unittest.TestCase):
    def test_parses_each_agents_injected_set(self):
        parsed = parse_skills(_BLOCK)

        self.assertEqual(parsed["developer"], {"android-testing", "android-ui-testing"})

    def test_none_marker_is_an_empty_set(self):
        self.assertEqual(parse_skills(_BLOCK)["architect"], set())

    def test_missing_block_returns_none(self):
        self.assertIsNone(parse_skills("no skills block here"))

    def test_block_stops_at_first_non_row_so_trailing_prose_is_ignored(self):
        output = _BLOCK + "\nThen I dispatched the architect and it loaded three skills.\n"

        parsed = parse_skills(output)

        self.assertNotIn("then", parsed)
        self.assertEqual(set(parsed), {"architect", "test-designer", "developer", "test-reviewer"})


class GradeSkillsTest(unittest.TestCase):
    def test_exact_injected_set_passes(self):
        spec = {"injects": {"developer": ["android-ui-testing", "android-testing"]},
                "noInjection": ["architect"]}

        self.assertEqual(grade_skills(spec, _BLOCK), [])

    def test_missing_expected_skill_fails(self):
        spec = {"injects": {"developer": ["android-testing", "android-ui-testing", "cqrs"]}}

        fails = grade_skills(spec, _BLOCK)

        self.assertTrue(any("developer" in f for f in fails))

    def test_skill_leaking_into_no_injection_agent_fails(self):
        block = _BLOCK.replace("architect: (none)", "architect: android-testing")
        spec = {"noInjection": ["architect"]}

        fails = grade_skills(spec, block)

        self.assertTrue(any("architect" in f for f in fails))

    def test_absent_block_is_a_failure(self):
        self.assertEqual(grade_skills({"injects": {"developer": ["x"]}}, "nothing"),
                         ["no 'SKILLS' block in command output"])


class GradeSkillLoadedTest(unittest.TestCase):
    """The DIRECT loading check reads the Skill hook log (one skill per line)."""

    def _log(self, *skills):
        f = tempfile.NamedTemporaryFile("w", suffix=".log", delete=False)
        f.write("".join(s + "\n" for s in skills))
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        return f.name

    def test_read_skill_log_parses_lines(self):
        self.assertEqual(read_skill_log(self._log("android-testing", "clean-architecture")),
                         {"android-testing", "clean-architecture"})

    def test_missing_log_is_empty_set(self):
        self.assertEqual(read_skill_log("/no/such/file.log"), set())
        self.assertEqual(read_skill_log(None), set())

    def test_must_load_present_passes(self):
        log = self._log("android-testing")
        self.assertEqual(grade_skill_loaded({"mustLoad": ["android-testing"]}, log), [])

    def test_must_load_absent_fails(self):
        log = self._log("clean-architecture")
        fails = grade_skill_loaded({"mustLoad": ["android-testing"]}, log)
        self.assertTrue(any("android-testing" in f for f in fails))

    def test_must_not_load_present_fails(self):
        log = self._log("android-testing")
        fails = grade_skill_loaded({"mustNotLoad": ["android-testing"]}, log)
        self.assertTrue(any("android-testing" in f for f in fails))

    def test_must_not_load_absent_passes_even_with_missing_log(self):
        # the no-injection control: no Skill call -> no log -> android-testing absent
        self.assertEqual(grade_skill_loaded({"mustNotLoad": ["android-testing"]}, "/no/log"), [])


if __name__ == "__main__":
    unittest.main()
