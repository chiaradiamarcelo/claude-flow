#!/usr/bin/env python3
"""Deterministic, model-free grader for the `architect` agent.

The architect is not a machine-first JSON agent — it *writes a plan file*
(`docs/specifications/<feature>/SCENARIO-XX.md`). So it can't be graded by
`eval_grade.py` (which grades a JSON verdict on stdout). This grader instead
inspects the **artifact the architect produced** and asserts coarse,
non-determinism-tolerant facts about it — the same philosophy as the reviewer
graders, applied to a markdown plan.

`grade_plan(spec, input_dir, scratch_dir)` is the pure entrypoint the engine
calls. `input_dir` is the frozen fixture input (what the architect read);
`scratch_dir` is a copy of it *after* the architect ran. New files =
scratch − input. This is how `writesNoCode` is checked: the architect must add
only the plan `.md`, never source files.

Checks (spec keys, all optional)
------
  planMustExist : bool   — a new SCENARIO-*.md plan file was created
  writesNoCode  : bool   — no new source file (code extension) was created
  minSteps      : int    — plan has >= N checklist steps (`- [ ]` / `- [x]`)
  mustMention   : [str]   — each substring (case-insensitive) appears in the plan
  mustNotMention: [str]   — none of these substrings appear in the plan
  orderedBefore : [[a,b]] — first line matching regex `a` precedes first matching `b`
"""
import re
from pathlib import Path

CODE_EXTS = {".kt", ".kts", ".java", ".ts", ".tsx", ".js", ".jsx", ".py",
             ".go", ".rs", ".rb", ".cs", ".swift", ".scala", ".groovy"}
STEP_RE = re.compile(r"^\s*-\s*\[[ xX]\]")


def _rel_files(root):
    root = Path(root)
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def _new_files(input_dir, scratch_dir):
    return _rel_files(scratch_dir) - _rel_files(input_dir)


def _plan_files(new_files):
    return sorted(f for f in new_files
                  if re.search(r"SCENARIO-[^/]*\.md$", f, re.I)
                  and "specifications/" in f)


def _code_files(new_files):
    return sorted(f for f in new_files if Path(f).suffix.lower() in CODE_EXTS)


def grade_plan(spec, input_dir, scratch_dir):
    """Return a list of failure strings (empty = pass)."""
    fails = []
    new_files = _new_files(input_dir, scratch_dir)
    plans = _plan_files(new_files)
    code = _code_files(new_files)

    if spec.get("planMustExist") and not plans:
        fails.append("planMustExist: no new SCENARIO-*.md plan file was created")

    if spec.get("writesNoCode") and code:
        fails.append(f"writesNoCode: architect created source file(s) {code} "
                     f"(it must write only the plan .md)")

    plan_text = "\n".join((Path(scratch_dir) / p).read_text() for p in plans)
    lines = plan_text.splitlines()

    min_steps = spec.get("minSteps")
    if min_steps is not None:
        n = sum(1 for ln in lines if STEP_RE.match(ln))
        if n < min_steps:
            fails.append(f"minSteps: plan has {n} checklist steps, expected >= {min_steps}")

    hay = plan_text.lower()
    for needle in spec.get("mustMention", []):
        if needle.lower() not in hay:
            fails.append(f"mustMention: plan never mentions {needle!r}")
    for needle in spec.get("mustNotMention", []):
        if needle.lower() in hay:
            fails.append(f"mustNotMention: plan mentions {needle!r} but should not")

    for pair in spec.get("orderedBefore", []):
        a, b = pair
        ia = next((i for i, ln in enumerate(lines) if re.search(a, ln, re.I)), None)
        ib = next((i for i, ln in enumerate(lines) if re.search(b, ln, re.I)), None)
        if ia is None:
            fails.append(f"orderedBefore: no plan line matches {a!r}")
        elif ib is None:
            fails.append(f"orderedBefore: no plan line matches {b!r}")
        elif ia >= ib:
            fails.append(f"orderedBefore: {a!r} (line {ia}) does not precede {b!r} (line {ib})")

    return fails
