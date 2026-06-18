"""Harness self-test for the fixture runner's manifest loading, resolution, and
handler/grader wiring (pure, model-free, $0). The dispatch itself (claude -p) is
integration, not here."""
import json
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
import run_fixture as runner


def _fixture(base, corpus, name, manifest):
    d = Path(base) / corpus / "fixtures" / name
    d.mkdir(parents=True)
    (d / "test.json").write_text(json.dumps(manifest))
    return d


class ManifestLoadingTest(unittest.TestCase):
    def test_reads_given_when_then(self):
        with tempfile.TemporaryDirectory() as base:
            d = _fixture(base, "api-reviewer", "biz-logic", {
                "given": {"files": "input/"},
                "when": {"do": "agent", "agent": "api-reviewer"},
                "then": {"grader": "verdict", "expectedStatus": "FAIL"}})

            m = runner.load_manifest(d)

            self.assertEqual(m["when"], {"do": "agent", "agent": "api-reviewer"})
            self.assertEqual(m["then"]["grader"], "verdict")


class WiringTest(unittest.TestCase):
    def test_every_grader_named_in_a_fixture_is_registered(self):
        graders = {runner.load_manifest(d)["then"]["grader"] for d in runner.all_fixtures()}

        self.assertTrue(graders)  # the real corpus is non-empty
        self.assertEqual(graders - set(runner.GRADERS), set())

    def test_every_do_named_in_a_fixture_has_a_handler(self):
        dos = {runner.load_manifest(d)["when"]["do"] for d in runner.all_fixtures()}

        self.assertEqual(dos - set(runner.HANDLERS), set())


class WorkspaceSetupTest(unittest.TestCase):
    def test_copies_any_skeleton_under_evals_and_strips_build(self):
        with tempfile.TemporaryDirectory() as base:
            skeleton = Path(base) / "golden-repo-spring"
            (skeleton / "src").mkdir(parents=True)
            (skeleton / "src" / "marker.kt").write_text("// skeleton")
            (skeleton / "build").mkdir()
            (skeleton / "build" / "stale.class").write_text("stale")
            original = runner.EVALS
            runner.EVALS = Path(base)
            try:
                scratch = runner.setup_workspace(Path(base), {"workspace": "golden-repo-spring"})
            finally:
                runner.EVALS = original

            self.assertTrue((scratch / "src" / "marker.kt").is_file())
            self.assertFalse((scratch / "build").exists())


class ResolutionTest(unittest.TestCase):
    def test_finds_unique_fixture(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "api-reviewer", "biz-logic", {"when": {}, "then": {}})

            hits = runner.find_fixtures("biz-logic", base=Path(base))

            self.assertEqual(len(hits), 1)

    def test_name_collision_returns_all_candidates(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "developer", "withdraw-money", {"when": {}, "then": {}})
            _fixture(base, "pipeline", "withdraw-money", {"when": {}, "then": {}})

            hits = runner.find_fixtures("withdraw-money", base=Path(base))

            self.assertEqual(len(hits), 2)

    def test_agent_qualifier_disambiguates(self):
        with tempfile.TemporaryDirectory() as base:
            _fixture(base, "developer", "withdraw-money", {"when": {}, "then": {}})
            _fixture(base, "pipeline", "withdraw-money", {"when": {}, "then": {}})

            hits = runner.find_fixtures("withdraw-money", agent="pipeline", base=Path(base))

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].parent.parent.name, "pipeline")


if __name__ == "__main__":
    unittest.main()
