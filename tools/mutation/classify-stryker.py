#!/usr/bin/env python3
"""Classify Stryker (JS/TS) surviving mutants into actionable vs not-actionable.

Sibling of classify-survivors.py, which does the same job for PIT/JVM. Stryker
emits the mutation-testing-report-schema JSON, not PIT's XML, so nothing about
the parsing or the noise rules transfers.

Buckets, and why each exists:

  killed        Killed + Timeout. Stryker's own mutation score counts a timeout
                as detected: the mutant changed observable behaviour enough to
                hang the suite. Counting it as surviving is exactly the bug that
                inflated the PIT numbers on Kotlin (see docs/findings/14).
  excluded      CompileError, RuntimeError, Ignored, Pending. Not results. These
                are outside the denominator, as they are in Stryker's own score.
  uncovered     NoCoverage. A survivor, but a *different* defect: no test
                executes the line at all. Reported separately — "strengthen the
                assertion" is the wrong ask for code nothing runs.
  static        `static: true`. Stryker's docs flag these as unreliable unless
                `ignoreStatic: true` is set, because the mutated module is
                evaluated once at load. Reported separately, never as a gap.
  junk          Provably or structurally unkillable — see JUNK RULES below.
  real          Everything else: candidate actionable gaps. Candidates, not
                certainties; an equivalent mutant can still land here.

JUNK RULES. Two are true by construction and always on:

  1. no-op replacement — the replacement text, spliced back into the reported
     source range, is identical to what was already there. Provably equivalent.
  2. out-of-scope file — a generated, vendored or test file that a loose
     `mutate` glob pulled in. Nothing to fix in the suite.

The third is a heuristic prior, not a measurement, and can be switched off with
`--no-log-rule`:

  3. log-message string literal — a StringLiteral mutant on a line that is a
     console/logger call. Killable only by a test asserting a log message.

The PIT rules were derived from a measured run (finding 14). There is no
equivalent Stryker run on record yet, so rule 3 is a prior: the first real audit
should check what it dropped before anyone trusts it. Every dropped mutant is
counted in the output and listed under `--show-junk`, so the filter can never
quietly hide the finding it was supposed to surface.

Usage: classify-stryker.py <report.json | dir containing *.json> [--show-junk] [--no-log-rule]
"""
import glob
import json
import os
import re
import sys

KILLED_STATUSES = {"Killed", "Timeout"}
EXCLUDED_STATUSES = {"CompileError", "RuntimeError", "Ignored", "Pending"}

OUT_OF_SCOPE = re.compile(
    r"(^|/)(dist|build|coverage|node_modules|__mocks__|__generated__)(/|$)"
    r"|\.d\.ts$|\.(spec|test)\.[cm]?[jt]sx?$|\.generated\.[cm]?[jt]sx?$"
)
LOG_CALL = re.compile(r"\b(console\.(log|info|warn|error|debug|trace)|logger?\.\w+|\w*[Ll]ogger\.\w+)\s*\(")


def source_lines(file_report):
    src = file_report.get("source")
    return src.split("\n") if src else []


def mutated_text(mutant, lines):
    """The source the mutant replaced, sliced out of the report's own `source`.

    Returns None when the location is absent or out of range — the caller must
    not treat "cannot tell" as "identical".
    """
    loc = mutant.get("location") or {}
    start, end = loc.get("start"), loc.get("end")
    if not start or not end or not lines:
        return None
    s_line, e_line = start.get("line"), end.get("line")
    if not s_line or not e_line or s_line > len(lines) or e_line > len(lines):
        return None
    if s_line == e_line:
        return lines[s_line - 1][start.get("column", 1) - 1:end.get("column", 1) - 1]
    chunk = [lines[s_line - 1][start.get("column", 1) - 1:]]
    chunk += lines[s_line:e_line - 1]
    chunk.append(lines[e_line - 1][:end.get("column", 1) - 1])
    return "\n".join(chunk)


def line_text(mutant, lines):
    line_no = ((mutant.get("location") or {}).get("start") or {}).get("line")
    return lines[line_no - 1] if line_no and 0 < line_no <= len(lines) else ""


def classify(mutant, path, lines, log_rule=True):
    """-> (bucket, reason). Buckets: killed|excluded|uncovered|static|junk|real."""
    status = mutant.get("status")
    if status in KILLED_STATUSES:
        return "killed", status
    if status in EXCLUDED_STATUSES:
        return "excluded", f"{status} — not a result"
    if status == "NoCoverage":
        return "uncovered", "no test executes this line"
    if mutant.get("static"):
        return "static", "static mutant — unreliable unless `ignoreStatic: true`"
    if OUT_OF_SCOPE.search(path):
        return "junk", "out-of-scope file (generated / vendored / test)"
    original = mutated_text(mutant, lines)
    if original is not None and original == mutant.get("replacement"):
        return "junk", "no-op replacement (provably equivalent)"
    if log_rule and mutant.get("mutatorName") == "StringLiteral" and LOG_CALL.search(line_text(mutant, lines)):
        return "junk", "log-message string literal (heuristic — see --no-log-rule)"
    return "real", f"survivor in {os.path.basename(path)} ({mutant.get('mutatorName')})"


def report_files(target):
    if os.path.isdir(target):
        return sorted(glob.glob(os.path.join(target, "*.json")))
    return [target]


def collect(paths, log_rule=True):
    totals = dict.fromkeys(("total", "killed", "excluded", "uncovered", "static", "junk", "real"), 0)
    real, junk = [], []
    for report_path in paths:
        with open(report_path) as fh:
            report = json.load(fh)
        for path, file_report in (report.get("files") or {}).items():
            lines = source_lines(file_report)
            for mutant in file_report.get("mutants") or []:
                bucket, reason = classify(mutant, path, lines, log_rule)
                totals["total"] += 1
                totals[bucket] += 1
                where = (f"  {path}:{((mutant.get('location') or {}).get('start') or {}).get('line')} — "
                         f"{mutant.get('mutatorName')} -> {mutant.get('replacement')!r} :: {reason}")
                if bucket == "real":
                    real.append(where)
                elif bucket == "junk":
                    junk.append(where)
    return totals, real, junk


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    paths = report_files(args[0])
    if not paths:
        print("no Stryker JSON report found")
        return 1

    totals, real, junk = collect(paths, log_rule="--no-log-rule" not in flags)
    scored = totals["total"] - totals["excluded"]
    print(f"mutants {totals['total']}  scored {scored}  killed {totals['killed']}  "
          f"excluded {totals['excluded']}")
    print(f"survivors: candidate-real {totals['real']}  uncovered {totals['uncovered']}  "
          f"static {totals['static']}  junk (dropped) {totals['junk']}")
    if totals["uncovered"]:
        print(f"\n{totals['uncovered']} mutant(s) on lines no test executes — that is a coverage "
              f"gap, not a weak assertion. Fix coverage first, then re-audit.")
    print("\n--- CANDIDATE-REAL survivors (inspect each: genuine gap vs equivalent) ---")
    print("\n".join(real) if real else "  (none)")
    if junk:
        if "--show-junk" in flags:
            print("\n--- DROPPED as junk ---")
            print("\n".join(junk))
        else:
            print(f"\n{len(junk)} mutant(s) dropped as junk — re-run with --show-junk to audit them.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
