"""Harness self-test for the refusal grader (pure, model-free, $0)."""
import os
import tempfile
import unittest

from . import _bootstrap  # noqa: F401
from check_refusal import grade

SPEC = {"mustNotWrite": ["src/main", "src/test"], "mustMention": ["specification"]}


class RefusalGraderTest(unittest.TestCase):
    def test_clean_refusal_passes(self):
        with tempfile.TemporaryDirectory() as d:
            output = "No approved specification found for ghost-feature. Run /intent-and-goal first."

            self.assertEqual(grade(SPEC, d, output), [])

    def test_code_written_trips_must_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "src", "main", "kotlin"))
            open(os.path.join(d, "src", "main", "kotlin", "Account.kt"), "w").close()

            fails = grade(SPEC, d, "No approved specification found.")

            self.assertTrue(any("mustNotWrite" in f for f in fails))

    def test_empty_dir_does_not_trip_must_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "src", "main"))  # exists but empty → not "wrote code"

            self.assertEqual(grade(SPEC, d, "no specification"), [])

    def test_missing_mention_fails(self):
        with tempfile.TemporaryDirectory() as d:
            fails = grade(SPEC, d, "I cannot find anything to do here.")

            self.assertTrue(any("mustMention" in f for f in fails))


if __name__ == "__main__":
    unittest.main()
