"""Harness self-test: which report files the PIT classifier picks up.

Regression: the only glob was `*.mutations.xml`, which matches the benchmark
rig's renamed per-arm copies but NOT `mutations.xml` — the name PIT itself
writes. `/mutation-audit`'s documented invocation therefore reported nothing on
a real PIT run, on both the Gradle and the Maven path.
"""
import importlib.util
import tempfile
import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "mutation" / "classify-survivors.py"
_spec = importlib.util.spec_from_file_location("classify_survivors", _MODULE_PATH)
classify_survivors = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(classify_survivors)

report_files = classify_survivors.report_files
classify = classify_survivors.classify


def mutant(status="SURVIVED", cls="com.example.domain.Wall", method="rename",
           mutator="org.pitest.mutationtest.engine.gregor.mutators.NegateConditionalsMutator",
           description="negated conditional"):
    return ET.fromstring(
        f'<mutation status="{status}">'
        f"<mutatedClass>{cls}</mutatedClass><mutatedMethod>{method}</mutatedMethod>"
        f"<lineNumber>12</lineNumber><mutator>{mutator}</mutator>"
        f"<description>{description}</description></mutation>")


class StatusBucketTest(unittest.TestCase):
    """PIT's own mutation score counts KILLED, TIMED_OUT, MEMORY_ERROR and RUN_ERROR as
    detected. Counting a timeout as surviving is systematic on Flow code, where a negated
    conditional in a collector hangs more often than it fails."""

    def test_a_timeout_is_detected_not_surviving(self):
        self.assertEqual("killed", classify(mutant(status="TIMED_OUT"))[0])

    def test_a_memory_error_is_detected(self):
        self.assertEqual("killed", classify(mutant(status="MEMORY_ERROR"))[0])

    def test_a_run_error_is_detected(self):
        self.assertEqual("killed", classify(mutant(status="RUN_ERROR"))[0])

    def test_non_viable_bytecode_is_not_a_result(self):
        self.assertEqual("excluded", classify(mutant(status="NON_VIABLE"))[0])

    def test_an_uncovered_line_is_not_a_weak_assertion(self):
        self.assertEqual("uncovered", classify(mutant(status="NO_COVERAGE"))[0])

    def test_a_plain_survivor_is_a_candidate_gap(self):
        self.assertEqual("real", classify(mutant())[0])

    def test_a_void_call_in_a_suspend_function_is_reported_not_filtered(self):
        """Deliberate: many of these are the coroutine `label` switch rather than
        authored code, but the XML cannot tell those from a dropped repository call,
        and that is where real gaps in coroutine code live. Reported as a lead."""
        m = mutant(method="invoke",
                   mutator="org.pitest.mutationtest.engine.gregor.mutators.VoidMethodCallMutator")

        self.assertEqual("real", classify(m)[0])


class GeneratedKotlinTest(unittest.TestCase):
    """Signatures taken from the boulder-friend run that motivated this: no author can
    write the line these mutants change, so no test can kill them."""

    def test_the_coroutine_state_machine_entry_point_is_junk(self):
        self.assertEqual("junk", classify(mutant(method="invokeSuspend"))[0])

    def test_a_continuation_factory_is_junk(self):
        self.assertEqual("junk", classify(mutant(method="create"))[0])

    def test_an_inlining_artefacts_emit_is_junk(self):
        m = mutant(cls="com.example.CatalogKt$special$$inlined$map$1$2", method="emit")

        self.assertEqual("junk", classify(m)[0])

    def test_a_serializer_is_junk(self):
        m = mutant(cls="com.example.dto.BoulderDto$$serializer", method="deserialize")

        self.assertEqual("junk", classify(m)[0])

    def test_an_ordinary_emit_outside_generated_code_is_still_reviewed(self):
        m = mutant(cls="com.example.domain.EventBus", method="emit")

        self.assertEqual("real", classify(m)[0])


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
