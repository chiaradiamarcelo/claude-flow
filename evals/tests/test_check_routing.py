"""Harness self-test: the /run-reviewers routing-output PARSER (check_routing).

This is the bug from docs/findings/01 — the parser read the model's `fires:`
line wrong, which *looked* like the model "routing by topic" and cost a wrongful
quarantine + a whole throwaway router script. The fix is one regex; this pins it
so it can never silently regress. Pure parsing of our own code — no model, $0.
"""
import unittest

from . import _bootstrap  # noqa: F401  (puts evals/ on sys.path)
from check_routing import fired_set


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


if __name__ == "__main__":
    unittest.main()
