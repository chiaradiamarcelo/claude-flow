#!/usr/bin/env python3
"""Deterministic, model-free grader for plan↔code FIDELITY after a developer run.

The developer executes the test-designer's `## Ordered Test List` and must leave
it a COMPLETE inventory: every row maps to a real test method, and every test
method maps to a row (a TDD-forced supporting test gets appended as an unplanned
row). This grader detects the drift we observed in a real slice — tests written
with no corresponding row (a constructor guard, a value-object query) — by
comparing the row names in the produced plan against the test methods in the
produced source.

`grade_fidelity(spec, scratch_dir)` is the pure entrypoint. `scratch_dir` holds
BOTH the updated `SCENARIO-XX.md` (rows) and the test sources (methods) after the
developer ran.

Matching is coarse and normalization-tolerant (lowercase, strip non-alphanumeric)
so `returns_x_when_y` (row) ≈ `returns_x_when_y()` (Kotlin/Java) ≈
`it("returns x when y")` (TS). We compare NAMES, never bodies.

Checks (spec keys, all optional)
------
  everyRowHasTest : bool   — each Ordered-List row name appears as a test method
  everyTestHasRow : bool   — each test method appears as an Ordered-List row
                             (this is the drift alarm: an unplanned, unlogged test)
  minRows         : int    — the plan has >= N rows (guards a vacuous empty plan)
  ignoreTests     : [str]  — regex list; test methods matching are exempt from
                             everyTestHasRow (e.g. inherited contract-suite methods)
"""
import re
from pathlib import Path

TEST_EXTS = {".kt", ".java", ".ts", ".tsx", ".js", ".jsx", ".scala", ".groovy", ".py"}
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|\s*$")
SECTION_RE = re.compile(r"^##\s+Ordered Test List", re.I | re.M)

# test-method name shapes across stacks
# Kotlin/Scala/Groovy: only snake_case funs are test methods (our naming rule);
# camelCase helpers like `fun repository()` / `fun anAccount()` are excluded.
FUN_RE = re.compile(r"\bfun\s+([a-z][a-z0-9]*_[\w]*)\s*\(")
JVOID_RE = re.compile(r"\b(?:void|public|private|protected)\s+([a-z_][\w]*)\s*\(")  # Java-ish
IT_RE = re.compile(r"""\b(?:it|test)\s*\(\s*['"`]([^'"`]+)['"`]""")  # JS/TS
PYDEF_RE = re.compile(r"\bdef\s+(test_[\w]*)\s*\(")             # pytest


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _rel(root):
    root = Path(root)
    return [p for p in root.rglob("*") if p.is_file()]


def _row_names(scratch):
    names = []
    for p in _rel(scratch):
        if not re.search(r"SCENARIO-[^/]*\.md$", p.name, re.I):
            continue
        text = p.read_text(errors="ignore")
        m = SECTION_RE.search(text)
        if not m:
            continue
        section, header = text[m.start():], None
        for ln in section.splitlines():
            if SEP_RE.match(ln):
                continue
            if not TABLE_ROW_RE.match(ln):
                header = None  # a new `###` table below re-reads its own header row
                continue
            cells = [c.strip() for c in TABLE_ROW_RE.match(ln).group(1).split("|")]
            if header is None:
                header = [c.lower() for c in cells]
                continue
            # the FLFI name column: first cell containing "name", else 2nd column
            ni = next((i for i, h in enumerate(header) if "name" in h), 1)
            if ni < len(cells) and cells[ni]:
                names.append(cells[ni].strip("`"))
    return names


def _test_methods(scratch):
    methods = []
    for p in _rel(scratch):
        if p.suffix.lower() not in TEST_EXTS:
            continue
        if not re.search(r"(test|spec)", p.name, re.I):
            continue
        text = p.read_text(errors="ignore")
        for rx in (FUN_RE, IT_RE, PYDEF_RE):
            methods += [(p.name, m) for m in rx.findall(text)]
    return methods


def grade_fidelity(spec, scratch_dir):
    fails = []
    rows = _row_names(scratch_dir)
    methods = _test_methods(scratch_dir)

    min_rows = spec.get("minRows")
    if min_rows is not None and len(rows) < min_rows:
        fails.append(f"minRows: plan has {len(rows)} rows, expected >= {min_rows}")

    norm_methods = {_norm(m) for _, m in methods}
    norm_rows = {_norm(r) for r in rows}
    ignore = [re.compile(p, re.I) for p in spec.get("ignoreTests", [])]

    if spec.get("everyRowHasTest"):
        for r in rows:
            nr = _norm(r)
            if nr and not any(nr in nm or nm in nr for nm in norm_methods):
                fails.append(f"everyRowHasTest: row {r!r} has no matching test method")

    if spec.get("everyTestHasRow"):
        for fname, m in methods:
            if any(rx.search(m) for rx in ignore):
                continue
            nm = _norm(m)
            if nm and not any(nm in nr or nr in nm for nr in norm_rows):
                fails.append(f"everyTestHasRow: test {m!r} ({fname}) maps to no Ordered-List "
                             f"row — an unplanned test that was never logged (plan↔code drift)")

    return fails
