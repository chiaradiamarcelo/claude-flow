"""Harness self-test for the fixture runner's manifest loading + resolution
(pure, model-free, $0). The dispatch itself (claude -p) is integration, not here."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
import run_fixture as runner


def _fixture(base, corpus, name, files):
    d = Path(base) / corpus / "fixtures" / name
    d.mkdir(parents=True)
    for fname, content in files.items():
        (d / fname).write_text(content)
    return d


class ManifestLoadingTest(unittest.TestCase):
    def test_reads_test_json_triple(self):
        with tempfile.TemporaryDirectory() as base:
            d = _fixture(base, "api-reviewer", "biz-logic", {"test.json": json.dumps({
                "given": {"files": "input/"},
                "when": {"do": "agent", "agent": "api-reviewer"},
                "then": {"grader": "verdict", "expectedStatus": "FAIL"},
            })})

            m = runner.load_manifest(d)

            self.assertEqual(m["when"], {"do": "agent", "agent": "api-reviewer"})
            self.assertEqual(m["then"]["grader"], "verdict")

    def test_legacy_expected_json_synthesizes_when_and_grader(self):
        with tempfile.TemporaryDirectory() as base:
            d = _fixture(base, "api-reviewer", "biz-logic", {"expected.json": json.dumps({
                "description": "x",
                "agents": {"api-reviewer": {"expectedStatus": "FAIL",
                                            "severities": {"VIOLATION": {"min": 1}}}},
            })})

            m = runner.load_manifest(d)

            self.assertEqual(m["when"], {"do": "agent", "agent": "api-reviewer"})
            self.assertEqual(m["then"]["grader"], "verdict")
            self.assertEqual(m["then"]["expectedStatus"], "FAIL")

    def test_legacy_non_verdict_spec_marks_grader_unsupported(self):
        with tempfile.TemporaryDirectory() as base:
            d = _fixture(base, "pipeline", "wm-core", {"expected.json": json.dumps({
                "agents": {"pipeline": {"buildMustPass": True}},
            })})

            m = runner.load_manifest(d)

            self.assertTrue(m["then"]["grader"].startswith("unsupported:"))


class ResolutionTest(unittest.TestCase):
    def test_finds_unique_fixture(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "api-reviewer", "biz-logic", {"expected.json": "{}"})

            hits = runner.find_fixtures("biz-logic", base=Path(base))

            self.assertEqual(len(hits), 1)

    def test_name_collision_returns_all_candidates(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "developer", "withdraw-money", {"expected.json": "{}"})
            _fixture(base, "pipeline", "withdraw-money", {"expected.json": "{}"})

            hits = runner.find_fixtures("withdraw-money", base=Path(base))

            self.assertEqual(len(hits), 2)

    def test_agent_qualifier_disambiguates(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "developer", "withdraw-money", {"expected.json": "{}"})
            _fixture(base, "pipeline", "withdraw-money", {"expected.json": "{}"})

            hits = runner.find_fixtures("withdraw-money", agent="pipeline", base=Path(base))

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].parent.parent.name, "pipeline")


if __name__ == "__main__":
    unittest.main()
