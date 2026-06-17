"""Harness self-test for the choreography grader (pure, model-free, $0)."""
import unittest

from . import _bootstrap  # noqa: F401
from check_choreography import grade, _is_subsequence

SEQ = ["architect", "developer:impl", "test-reviewer", "developer:fix", "test-reviewer"]
SPEC = {"expectedSubsequence": SEQ, "endsAfterReview": True, "maxArchitects": 1}


class ChoreographyGraderTest(unittest.TestCase):
    def test_clean_log_with_interleaved_reviewers_passes(self):
        log = ["architect", "developer:impl", "test-reviewer", "arch-reviewer",
               "refactor-advisor", "developer:fix", "test-reviewer", "arch-reviewer"]

        self.assertEqual(grade(SPEC, log), [])

    def test_out_of_order_fails(self):
        # developer:impl before architect — plan must precede implement
        log = ["developer:impl", "architect", "test-reviewer"]

        fails = grade(SPEC, log)

        self.assertTrue(any("expectedSubsequence" in f for f in fails))

    def test_no_fix_pass_after_fail_fails_the_subsequence(self):
        # review happened but no developer:fix → the fix pass never triggered
        log = ["architect", "developer:impl", "test-reviewer"]

        fails = grade(SPEC, log)

        self.assertTrue(any("expectedSubsequence" in f for f in fails))

    def test_dangling_developer_at_end_fails_ends_after_review(self):
        log = SEQ + ["developer:fix"]  # stopped on a fix, not a passing review

        fails = grade(SPEC, log)

        self.assertTrue(any("endsAfterReview" in f for f in fails))

    def test_replanning_loop_trips_max_architects(self):
        log = ["architect", "developer:impl", "architect", "developer:impl", "test-reviewer"]

        fails = grade(SPEC, log)

        self.assertTrue(any("maxArchitects" in f for f in fails))

    def test_subsequence_helper(self):
        self.assertEqual(_is_subsequence(["a", "b"], ["a", "x", "b"]), (True, 2))
        self.assertEqual(_is_subsequence(["a", "b"], ["b", "a"])[0], False)


if __name__ == "__main__":
    unittest.main()
