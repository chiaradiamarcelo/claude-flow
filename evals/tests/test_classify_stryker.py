"""Harness self-test: the Stryker survivor classifier (tools/mutation/classify-stryker.py).

Pins the bucketing contract deterministically ($0, no model). The rules worth
pinning are the ones a reader would otherwise have to trust: a timeout is a kill,
a compile error is not a result, an uncovered line is not a weak assertion, and
the heuristic log rule can be switched off.
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "mutation" / "classify-stryker.py"
_spec = importlib.util.spec_from_file_location("classify_stryker", _MODULE_PATH)
classify_stryker = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(classify_stryker)

classify = classify_stryker.classify
collect = classify_stryker.collect

ARITHMETIC_LINE = "const x = 1 + 2;"
PLUS_AT_COLUMN_13 = {"start": {"line": 1, "column": 13}, "end": {"line": 1, "column": 14}}


def mutant(status="Survived", mutator="ArithmeticOperator", replacement="-",
           location=None, static=False):
    return {"id": "1", "status": status, "mutatorName": mutator,
            "replacement": replacement, "static": static,
            "location": location or PLUS_AT_COLUMN_13}


def report(files):
    return {"schemaVersion": "1.0", "files": files}


def file_report(source, mutants):
    return {"language": "typescript", "source": source, "mutants": mutants}


class BucketingTest(unittest.TestCase):
    def test_a_survivor_in_production_code_is_a_candidate_real_gap(self):
        bucket, _ = classify(mutant(), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("real", bucket)

    def test_a_timeout_counts_as_killed_because_the_mutant_changed_behaviour(self):
        bucket, _ = classify(mutant(status="Timeout"), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("killed", bucket)

    def test_a_compile_error_is_not_a_result(self):
        bucket, _ = classify(mutant(status="CompileError"), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("excluded", bucket)

    def test_an_uncovered_mutant_is_reported_apart_from_weak_assertions(self):
        bucket, _ = classify(mutant(status="NoCoverage"), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("uncovered", bucket)

    def test_a_static_mutant_is_reported_apart_from_candidate_real_gaps(self):
        bucket, _ = classify(mutant(static=True), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("static", bucket)


class JunkRuleTest(unittest.TestCase):
    def test_a_replacement_identical_to_the_source_it_replaces_is_junk(self):
        bucket, reason = classify(mutant(replacement="+"), "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("junk", bucket)
        self.assertIn("no-op", reason)

    def test_a_mutant_in_a_test_file_the_mutate_glob_pulled_in_is_junk(self):
        bucket, reason = classify(mutant(), "src/planTier.spec.ts", [ARITHMETIC_LINE])

        self.assertEqual("junk", bucket)
        self.assertIn("out-of-scope", reason)

    def test_a_mutant_in_a_declaration_file_is_junk(self):
        bucket, _ = classify(mutant(), "src/types/planTier.d.ts", [ARITHMETIC_LINE])

        self.assertEqual("junk", bucket)

    def test_a_string_literal_inside_a_log_call_is_junk_by_the_heuristic_rule(self):
        source = ['logger.warn("render allowance spent");']

        bucket, _ = classify(mutant(mutator="StringLiteral", replacement="",
                                    location={"start": {"line": 1, "column": 13},
                                              "end": {"line": 1, "column": 37}}),
                             "src/planTier.ts", source)

        self.assertEqual("junk", bucket)

    def test_the_log_rule_can_be_switched_off_so_nothing_is_dropped_unseen(self):
        source = ['logger.warn("render allowance spent");']

        bucket, _ = classify(mutant(mutator="StringLiteral", replacement="",
                                    location={"start": {"line": 1, "column": 13},
                                              "end": {"line": 1, "column": 37}}),
                             "src/planTier.ts", source, log_rule=False)

        self.assertEqual("real", bucket)

    def test_a_string_literal_outside_a_log_call_is_a_candidate_real_gap(self):
        source = ['const message = "render allowance spent";']

        bucket, _ = classify(mutant(mutator="StringLiteral", replacement="",
                                    location={"start": {"line": 1, "column": 17},
                                              "end": {"line": 1, "column": 41}}),
                             "src/planTier.ts", source, log_rule=False)

        self.assertEqual("real", bucket)


class UnreadableLocationTest(unittest.TestCase):
    def test_a_mutant_with_no_location_is_not_assumed_equivalent(self):
        bucket, _ = classify({"status": "Survived", "mutatorName": "ArithmeticOperator",
                              "replacement": "-"}, "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("real", bucket)

    def test_a_location_past_the_end_of_the_source_is_not_assumed_equivalent(self):
        bucket, _ = classify(mutant(location={"start": {"line": 99, "column": 1},
                                              "end": {"line": 99, "column": 2}}),
                             "src/planTier.ts", [ARITHMETIC_LINE])

        self.assertEqual("real", bucket)

    def test_a_report_with_no_source_still_classifies_its_survivors(self):
        bucket, _ = classify(mutant(), "src/planTier.ts", [])

        self.assertEqual("real", bucket)


class CollectTest(unittest.TestCase):
    def test_the_scored_total_excludes_non_results(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "report.json"
        path.write_text(json.dumps(report({
            "src/planTier.ts": file_report(ARITHMETIC_LINE, [
                mutant(), mutant(status="Killed"), mutant(status="CompileError"),
            ]),
        })))

        totals, real, junk = collect([str(path)])

        self.assertEqual(3, totals["total"])
        self.assertEqual(1, totals["excluded"])
        self.assertEqual(1, totals["real"])
        self.assertEqual(1, len(real))
        self.assertEqual([], junk)


if __name__ == "__main__":
    unittest.main()
