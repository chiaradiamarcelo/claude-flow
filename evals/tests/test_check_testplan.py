"""Harness self-test for the test-designer plan grader (pure, model-free, $0)."""
import shutil
import tempfile
import unittest
from pathlib import Path

from . import _bootstrap  # noqa: F401
from check_testplan import grade_testplan, _parse_rows

SPEC_DIR = "docs/specifications/demo"

STRUCTURE = """# SCENARIO-01

## Structure & Contracts
- Use case: DemoUseCase (entry point)
"""

# A well-formed Ordered Test List: unit rows with catalog TPP + a contract table.
GOOD = STRUCTURE + """
## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — DemoUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | returns_x_when_y | nil → constant | code does nothing yet | ☐ |
| 2 | branches_when_z | unconditional → conditional | code always returns the constant | ☐ |

### Contract — DemoRepositoryContractTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 3 | returns_saved_row | n/a | store returns nothing | ☐ |
"""


def _workspace(scenario_text):
    """Return (input_dir, scratch_dir): input has only the structure; scratch has
    the structure + whatever scenario_text supplies (the produced plan)."""
    root = tempfile.mkdtemp()
    inp = Path(root) / "input"
    scr = Path(root) / "scratch"
    for base, text in ((inp, STRUCTURE), (scr, scenario_text)):
        d = base / SPEC_DIR
        d.mkdir(parents=True)
        (d / "SCENARIO-01.md").write_text(text)
    return str(inp), str(scr), root


class TestPlanGraderTest(unittest.TestCase):
    def _grade(self, spec, scenario_text=GOOD):
        inp, scr, root = _workspace(scenario_text)
        try:
            return grade_testplan(spec, inp, scr)
        finally:
            shutil.rmtree(root)

    def test_good_plan_passes_all_checks(self):
        spec = {"testPlanMustExist": True, "writesNoCode": True, "minRows": 3,
                "everyRowHasContradiction": True, "tppFromCatalog": True,
                "minContractRows": 1}
        self.assertEqual(self._grade(spec), [])

    def test_missing_section_fails_must_exist(self):
        fails = self._grade({"testPlanMustExist": True}, scenario_text=STRUCTURE)
        self.assertTrue(any("testPlanMustExist" in f for f in fails))

    def test_empty_contradiction_cell_is_caught(self):
        bad = GOOD.replace("code does nothing yet", "")
        fails = self._grade({"everyRowHasContradiction": True}, scenario_text=bad)
        self.assertTrue(any("everyRowHasContradiction" in f for f in fails))

    def test_non_catalog_tpp_is_caught(self):
        bad = GOOD.replace("nil → constant", "(surcharge applied after the base fee)")
        fails = self._grade({"tppFromCatalog": True}, scenario_text=bad)
        self.assertTrue(any("tppFromCatalog" in f for f in fails))

    def test_na_is_a_valid_tpp(self):
        self.assertEqual(self._grade({"tppFromCatalog": True}), [])

    def test_no_port_scenario_rejects_contract_rows(self):
        fails = self._grade({"maxContractRows": 0})
        self.assertTrue(any("maxContractRows" in f for f in fails))

    def test_with_port_scenario_requires_contract_rows(self):
        no_contract = STRUCTURE + """
## Ordered Test List (FLFI · TPP · Contradiction)

### Unit — DemoUseCaseTest
| # | Test Name (FLFI) | TPP | Contradiction | Status |
|---|------------------|-----|---------------|--------|
| 1 | returns_x_when_y | nil → constant | code does nothing yet | ☐ |
"""
        fails = self._grade({"minContractRows": 1}, scenario_text=no_contract)
        self.assertTrue(any("minContractRows" in f for f in fails))

    def test_note_to_architect_required_but_absent(self):
        fails = self._grade({"noteToArchitect": True})
        self.assertTrue(any("noteToArchitect" in f for f in fails))

    def test_note_to_architect_present(self):
        withnote = GOOD + "\n> Note to architect: the port needs a read method.\n"
        self.assertEqual(self._grade({"noteToArchitect": True}, scenario_text=withnote), [])

    def test_min_rows_enforced(self):
        fails = self._grade({"minRows": 5})
        self.assertTrue(any("minRows" in f for f in fails))

    def test_parser_counts_rows_across_tables(self):
        rows = _parse_rows(GOOD)
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
