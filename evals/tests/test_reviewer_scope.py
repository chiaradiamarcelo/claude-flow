"""Harness self-test: a reviewer must be graded on the files it covered, not on
the words it produced ($0, no model).

`refactor-advisor`'s Process named a closed reading list — use case code, domain
types, use-case tests, controllers. Its trigger glob routed `presentation/` and
`infrastructure/` files to it; its own instructions then told it not to read them.
On a whole-codebase run it reported six findings from `application/` and `domain/`,
generalised about the rest, and returned a verdict with no finding from any other
layer — while 44 files it never opened had more comment lines than code.

Nothing caught it, because every existing assertion reads the reviewer's prose.
A reviewer that read one familiar layer and generalised about the others produces
prose indistinguishable from a full sweep. `mustFlagFiles` reads the `file` field
instead: a reviewer cannot report a file it never opened.
"""
import unittest

from . import _bootstrap  # noqa: F401  (puts evals/ on sys.path)
from eval_grade import check_corpus, grade_agent


def verdict(*files):
    return {"status": "FAIL", "summary": "comment bloat",
            "issues": [{"severity": "SUGGESTION", "file": f, "line": 1,
                        "message": "Comment that argues the design: move it to an ADR"}
                       for f in files]}


class MustFlagFilesTest(unittest.TestCase):
    def test_passes_when_the_reviewer_reported_the_required_file(self):
        spec = {"expectedStatus": "FAIL", "mustFlagFiles": ["WallPickerTags"]}

        self.assertEqual([], grade_agent(spec, verdict("presentation/wall/WallPickerTags.kt")))

    def test_fails_when_the_reviewer_only_covered_the_layer_it_prefers(self):
        spec = {"expectedStatus": "FAIL", "mustFlagFiles": ["WallPickerTags"]}

        fails = grade_agent(spec, verdict("application/RenameWallUseCase.kt"))

        self.assertEqual(1, len(fails))
        self.assertIn("mustFlagFiles", fails[0])

    def test_the_failure_names_what_was_reviewed_instead(self):
        spec = {"expectedStatus": "FAIL", "mustFlagFiles": ["WallPickerTags"]}

        fails = grade_agent(spec, verdict("application/RenameWallUseCase.kt"))

        self.assertIn("RenameWallUseCase.kt", fails[0])

    def test_right_words_about_comments_do_not_satisfy_a_file_requirement(self):
        spec = {"expectedStatus": "FAIL", "mustMention": ["comment"],
                "mustFlagFiles": ["WallPickerTags"]}

        fails = grade_agent(spec, verdict("application/RenameWallUseCase.kt"))

        self.assertEqual(["mustFlagFiles"], [f.split(":")[0] for f in fails])

    def test_a_spec_without_the_key_is_unaffected(self):
        spec = {"expectedStatus": "FAIL", "mustMention": ["comment"]}

        self.assertEqual([], grade_agent(spec, verdict("application/RenameWallUseCase.kt")))


class ShippedCorpusTest(unittest.TestCase):
    def test_the_shipped_refactor_advisor_corpus_is_structurally_valid(self):
        self.assertEqual([], check_corpus(_bootstrap.EVALS_DIR / "refactor-advisor"))


if __name__ == "__main__":
    unittest.main()
