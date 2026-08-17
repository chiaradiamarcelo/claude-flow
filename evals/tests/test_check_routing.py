"""Harness self-test: the /run-reviewers routing-output PARSER (check_routing).

This is the bug from docs/findings/01 — the parser read the model's `fires:`
line wrong, which *looked* like the model "routing by topic" and cost a wrongful
quarantine + a whole throwaway router script. The fix is one regex; this pins it
so it can never silently regress. Pure parsing of our own code — no model, $0.
"""
import unittest

from . import _bootstrap  # noqa: F401  (puts evals/ on sys.path)
from check_routing import fired_set, grade_routing, scoped_files

DRY_RUN = """ROUTING
fires: arch-reviewer, refactor-advisor
skips: api-reviewer

SKILLS
arch-reviewer: (none)
refactor-advisor: kotlin-conventions

SCOPE
arch-reviewer: src/main/App.kt, src/main/presentation/WallPickerTags.kt
refactor-advisor: src/main/App.kt, src/main/presentation/WallPickerTags.kt
"""


class FiredSetTest(unittest.TestCase):
    def test_empty_fires_line_does_not_swallow_the_skips_line(self):
        # finding 01: an EMPTY `fires:` line means NOBODY fired — even though a
        # `skips:` line follows. The old `\s*` regex matched the newline and
        # captured the next line, reporting the SKIPPED reviewers as FIRED.
        output = "ROUTING\nfires:\nskips: api-reviewer, arch-reviewer\n"

        fired = fired_set(output)

        self.assertEqual(fired, set())

    def test_fires_line_with_reviewers_is_parsed(self):
        output = "fires: api-reviewer, test-reviewer\nskips: arch-reviewer\n"

        fired = fired_set(output)

        self.assertEqual(fired, {"api-reviewer", "test-reviewer"})

    def test_missing_fires_line_returns_none(self):
        self.assertIsNone(fired_set("no routing here at all"))

    def test_non_kebab_noise_tokens_are_dropped(self):
        # the model sometimes writes "(none)" or prose; only kebab-case names count
        output = "fires: api-reviewer, (none)\n"

        fired = fired_set(output)

        self.assertEqual(fired, {"api-reviewer"})

    def test_case_and_leading_whitespace_tolerated(self):
        output = "   Fires:   ui-test-reviewer  \n"

        fired = fired_set(output)

        self.assertEqual(fired, {"ui-test-reviewer"})


class ScopedFilesTest(unittest.TestCase):
    """A reviewer is dispatched with the files that matched its own triggers. Left
    as a bare path, `refactor-advisor` read the layers it prefers and returned a
    pass on files it never opened — with a flawless `fires:` line."""

    def test_each_fired_reviewers_file_list_is_parsed(self):
        scope = scoped_files(DRY_RUN)

        self.assertEqual({"src/main/App.kt", "src/main/presentation/WallPickerTags.kt"},
                         scope["refactor-advisor"])

    def test_the_block_ends_before_the_next_section(self):
        output = "SCOPE\narch-reviewer: a.kt\n\nROUTING\nfires: arch-reviewer\n"

        self.assertEqual({"arch-reviewer": {"a.kt"}}, scoped_files(output))

    def test_no_scope_block_is_an_empty_map_not_a_crash(self):
        self.assertEqual({}, scoped_files("fires: arch-reviewer\n"))


class MustScopeTest(unittest.TestCase):
    def test_passes_when_the_required_file_is_in_the_reviewers_scope(self):
        spec = {"fires": ["refactor-advisor"],
                "mustScope": {"refactor-advisor": ["presentation/WallPickerTags.kt"]}}

        self.assertEqual([], grade_routing(spec, DRY_RUN))

    def test_fails_when_a_matched_file_never_reaches_the_reviewer(self):
        spec = {"fires": ["refactor-advisor"],
                "mustScope": {"refactor-advisor": ["infrastructure/WallFileAdapter.kt"]}}

        fails = grade_routing(spec, DRY_RUN)

        self.assertEqual(1, len(fails))
        self.assertIn("WallFileAdapter.kt", fails[0])

    def test_a_bare_path_dispatch_with_no_scope_block_is_a_fault(self):
        spec = {"fires": ["refactor-advisor"],
                "mustScope": {"refactor-advisor": ["presentation/WallPickerTags.kt"]}}

        fails = grade_routing(spec, "ROUTING\nfires: refactor-advisor\nskips:\n")

        self.assertIn("matched file list", fails[0])

    def test_routing_only_specs_are_unaffected(self):
        spec = {"fires": ["arch-reviewer"], "doesNotFire": ["api-reviewer"]}

        self.assertEqual([], grade_routing(spec, DRY_RUN))


if __name__ == "__main__":
    unittest.main()
