#!/usr/bin/env python3
"""Deterministic, model-free grader for the `test-designer` agent.

The test-designer appends an `## Ordered Test List (FLFI · TPP · Contradiction)`
section (one markdown table per level) to an existing `SCENARIO-XX.md` that the
architect already populated with `## Structure & Contracts`. It writes no code.

Like `check_plan.py`, this inspects the **artifact** and asserts coarse,
non-determinism-tolerant facts about the produced table(s) — never wording.

`grade_testplan(spec, input_dir, scratch_dir)` is the pure entrypoint. The
Ordered Test List is parsed from the scenario plan file(s) present after the run.

Checks (spec keys, all optional)
------
  testPlanMustExist   : bool  — an `## Ordered Test List` section was produced
  writesNoCode        : bool  — no new source/test file was created (plan-only)
  minRows             : int   — the table(s) have >= N data rows total
  everyRowHasContradiction : bool — no row has an empty Contradiction cell
  tppFromCatalog      : bool  — every TPP cell is `n/a` or matches a canonical
                                transformation keyword (catches invented tags)
  noteToArchitect     : bool  — at least one `> Note to architect:` line appears
                                (used when the input structure is under-specified)
  maxContractRows     : int   — at most N rows under a `### Contract` table
                                (0 asserts NO contract level — e.g. no-port scenarios)
  mustMention         : [str] — each substring appears in the Ordered Test List
  mustNotMention      : [str] — none of these appear in the Ordered Test List
"""
import re
from pathlib import Path

CODE_EXTS = {".kt", ".kts", ".java", ".ts", ".tsx", ".js", ".jsx", ".py",
             ".go", ".rs", ".rb", ".cs", ".swift", ".scala", ".groovy"}

# Canonical TPP transformations (Robert C. Martin). A TPP cell is valid if it is
# `n/a` or mentions one of these keyword pairs. Kept loose (keyword, not exact
# arrow) so phrasing varies but invented transformations are still caught.
TPP_KEYWORDS = [
    "n/a", "{}", "nil", "constant", "scalar", "statement", "statements",
    "conditional", "unconditional", "array", "container", "recursion",
    "loop", "expression", "function", "variable", "assignment",
]

SECTION_RE = re.compile(r"^##\s+Ordered Test List", re.I | re.M)
LEVEL_RE = re.compile(r"^###\s+(.*)$", re.I)
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def _rel_files(root):
    root = Path(root)
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def _scenario_files(root):
    return sorted(f for f in _rel_files(root)
                  if re.search(r"SCENARIO-[^/]*\.md$", f, re.I)
                  and "specifications/" in f)


def _cells(row_line):
    inner = TABLE_ROW_RE.match(row_line).group(1)
    return [c.strip() for c in inner.split("|")]


def _parse_rows(text):
    """Return list of (level, cells) data rows across all tables in the section."""
    rows, level, header = [], None, None
    for ln in text.splitlines():
        m = LEVEL_RE.match(ln)
        if m:
            level, header = m.group(1).strip(), None
            continue
        if SEP_RE.match(ln):
            continue
        if TABLE_ROW_RE.match(ln):
            cells = _cells(ln)
            if header is None:
                header = [c.lower() for c in cells]
                continue
            rows.append((level, header, cells))
    return rows


def _col(header, *names):
    for i, h in enumerate(header):
        if any(n in h for n in names):
            return i
    return None


def grade_testplan(spec, input_dir, scratch_dir):
    fails = []

    new_files = _rel_files(scratch_dir) - _rel_files(input_dir)
    code = sorted(f for f in new_files if Path(f).suffix.lower() in CODE_EXTS)
    if spec.get("writesNoCode") and code:
        fails.append(f"writesNoCode: test-designer created source/test file(s) {code} "
                     f"(it must only edit the plan .md)")

    plan_text = "\n".join((Path(scratch_dir) / p).read_text()
                          for p in _scenario_files(scratch_dir))

    if not SECTION_RE.search(plan_text):
        if spec.get("testPlanMustExist"):
            fails.append("testPlanMustExist: no `## Ordered Test List` section was produced")
        return fails  # nothing else is gradable without the section

    section = plan_text[SECTION_RE.search(plan_text).start():]
    rows = _parse_rows(section)

    min_rows = spec.get("minRows")
    if min_rows is not None and len(rows) < min_rows:
        fails.append(f"minRows: {len(rows)} table rows, expected >= {min_rows}")

    if spec.get("everyRowHasContradiction"):
        for level, header, cells in rows:
            ci = _col(header, "contradiction")
            if ci is None or ci >= len(cells) or not cells[ci]:
                fails.append(f"everyRowHasContradiction: a row under {level!r} has an "
                             f"empty/absent Contradiction cell: {cells}")
                break

    if spec.get("tppFromCatalog"):
        for level, header, cells in rows:
            ti = _col(header, "tpp")
            if ti is None or ti >= len(cells):
                continue
            val = cells[ti].lower()
            if val and not any(k in val for k in TPP_KEYWORDS):
                fails.append(f"tppFromCatalog: row under {level!r} has a non-catalog "
                             f"TPP tag {cells[ti]!r} (expected a canonical transformation or n/a)")
                break

    max_contract = spec.get("maxContractRows")
    if max_contract is not None:
        n = sum(1 for level, _, _ in rows if re.search(r"contract", level or "", re.I))
        if n > max_contract:
            fails.append(f"maxContractRows: {n} contract-level rows, expected <= {max_contract} "
                         f"(this scenario has no persistence port)")

    if spec.get("noteToArchitect") and "note to architect" not in section.lower():
        fails.append("noteToArchitect: expected a `> Note to architect:` line, none found")

    hay = section.lower()
    for needle in spec.get("mustMention", []):
        if needle.lower() not in hay:
            fails.append(f"mustMention: Ordered Test List never mentions {needle!r}")
    for needle in spec.get("mustNotMention", []):
        if needle.lower() in hay:
            fails.append(f"mustNotMention: Ordered Test List mentions {needle!r} but should not")

    return fails
