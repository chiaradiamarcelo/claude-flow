"""Harness self-test for the plan↔code fidelity grader (pure, model-free, $0)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
from check_fidelity import grade_fidelity, _norm

PLAN = """# SCENARIO-01

## Ordered Test List (FLFI · TPP · Contradiction)
### Unit — WithdrawMoneyUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | reduces_the_balance_by_the_withdrawn_amount | nil → constant | code does nothing | ✅ |
| 2 | fails_when_the_amount_exceeds_the_balance | unconditional → conditional | no guard yet | ✅ |
"""

# A multi-table plan — the second table's header must NOT be captured as a row
# (regression for a real grader bug: header 'Test Name (FLFI)' read as a test).
MULTI_TABLE_PLAN = PLAN + """
### Contract — BankAccountRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 3 | returns_the_saved_account_for_its_id | n/a | store returns nothing | ✅ |
"""

# Kotlin test whose methods exactly match the two rows.
MATCHING = """package x
class WithdrawMoneyUseCaseTest {
    @Test fun reduces_the_balance_by_the_withdrawn_amount() {}
    @Test fun fails_when_the_amount_exceeds_the_balance() {}
}
"""

# Adds an UNPLANNED test with no row (the real-slice drift: a constructor guard).
DRIFT = MATCHING.replace(
    "fun fails_when_the_amount_exceeds_the_balance() {}",
    "fun fails_when_the_amount_exceeds_the_balance() {}\n    @Test fun fails_when_created_with_a_negative_balance() {}",
)


def _workspace(plan, test_src):
    root = tempfile.mkdtemp()
    spec = Path(root) / "docs/specifications/withdraw-money"
    spec.mkdir(parents=True)
    (spec / "SCENARIO-01.md").write_text(plan)
    tdir = Path(root) / "src/test/kotlin"
    tdir.mkdir(parents=True)
    (tdir / "WithdrawMoneyUseCaseTest.kt").write_text(test_src)
    return root


class FidelityGraderTest(unittest.TestCase):
    def _grade(self, spec, plan=PLAN, src=MATCHING):
        root = _workspace(plan, src)
        try:
            return grade_fidelity(spec, root)
        finally:
            shutil.rmtree(root)

    def test_matching_plan_and_code_passes_both_directions(self):
        spec = {"everyRowHasTest": True, "everyTestHasRow": True, "minRows": 2}
        self.assertEqual(self._grade(spec), [])

    def test_unplanned_test_is_caught_as_drift(self):
        fails = self._grade({"everyTestHasRow": True}, src=DRIFT)
        self.assertTrue(any("everyTestHasRow" in f and "negative_balance" in f for f in fails))

    def test_unplanned_test_passes_once_appended_as_a_row(self):
        appended = PLAN + "| 3 | fails_when_created_with_a_negative_balance | n/a | reconstitution guard | ✅ — unplanned |\n"
        self.assertEqual(self._grade({"everyTestHasRow": True}, plan=appended, src=DRIFT), [])

    def test_missing_test_for_a_row_is_caught(self):
        one_method = """package x
class WithdrawMoneyUseCaseTest {
    @Test fun reduces_the_balance_by_the_withdrawn_amount() {}
}
"""
        fails = self._grade({"everyRowHasTest": True}, src=one_method)
        self.assertTrue(any("everyRowHasTest" in f and "exceeds_the_balance" in f for f in fails))

    def test_ignore_tests_exempts_inherited_contract_methods(self):
        withc = MATCHING.replace("}", "    @Test fun returns_every_stored_field() {}\n}", 1)
        spec = {"everyTestHasRow": True, "ignoreTests": ["returns_every_stored_field"]}
        self.assertEqual(self._grade(spec, src=withc), [])

    def test_norm_bridges_snake_case_and_it_string(self):
        self.assertEqual(_norm("returns_x_when_y"), _norm("returns x when y"))

    def test_camelcase_helpers_are_not_treated_as_tests(self):
        withhelpers = MATCHING.replace(
            "}",
            "    private fun anAccount() {}\n    fun repository() {}\n}",
            1,
        )
        # helpers have no row, but must NOT trip everyTestHasRow (they aren't tests)
        self.assertEqual(self._grade({"everyTestHasRow": True}, src=withhelpers), [])

    def test_multi_table_headers_are_not_captured_as_rows(self):
        src = MATCHING.replace(
            "}",
            "    @Test fun returns_the_saved_account_for_its_id() {}\n}",
            1,
        )
        # 3 real rows across 2 tables; the 2nd table's header must not leak in
        fails = self._grade({"everyRowHasTest": True, "minRows": 3},
                            plan=MULTI_TABLE_PLAN, src=src)
        self.assertEqual(fails, [])


if __name__ == "__main__":
    unittest.main()
