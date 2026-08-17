"""Harness self-test: which report files the PIT classifier picks up.

Regression: the only glob was `*.mutations.xml`, which matches the benchmark
rig's renamed per-arm copies but NOT `mutations.xml` — the name PIT itself
writes. `/mutation-audit`'s documented invocation therefore reported nothing on
a real PIT run, on both the Gradle and the Maven path.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "mutation" / "classify-survivors.py"
_spec = importlib.util.spec_from_file_location("classify_survivors", _MODULE_PATH)
classify_survivors = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(classify_survivors)

report_files = classify_survivors.report_files


class ReportFilesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_finds_the_plain_report_name_that_pit_itself_writes(self):
        (self.dir / "mutations.xml").write_text("<mutations/>")

        self.assertEqual([str(self.dir / "mutations.xml")], report_files(str(self.dir)))

    def test_finds_the_benchmark_rigs_renamed_per_arm_copies(self):
        (self.dir / "main-control.mutations.xml").write_text("<mutations/>")
        (self.dir / "baseline.mutations.xml").write_text("<mutations/>")

        self.assertEqual([str(self.dir / "baseline.mutations.xml"),
                          str(self.dir / "main-control.mutations.xml")],
                         report_files(str(self.dir)))

    def test_accepts_a_report_path_directly(self):
        path = self.dir / "mutations.xml"
        path.write_text("<mutations/>")

        self.assertEqual([str(path)], report_files(str(path)))

    def test_reports_nothing_when_the_directory_holds_no_report(self):
        self.assertEqual([], report_files(str(self.dir)))


if __name__ == "__main__":
    unittest.main()
