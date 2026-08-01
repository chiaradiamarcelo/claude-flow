#!/usr/bin/env python3
"""Classify PIT surviving mutants as JUNK (equivalent / boilerplate noise) vs
CANDIDATE-REAL (business-logic survivors = actionable weak-test gaps).

Purpose: measure PIT's false-positive rate as a *gate* signal on Kotlin. If most
survivors are junk, a naive gate would spam the fix-loop; a filter is needed first.

Reads every *.mutations.xml in a directory. Usage: classify-survivors.py <dir>
"""
import sys, glob, os, xml.etree.ElementTree as ET

BOILERPLATE_METHODS = {"equals", "hashCode", "toString", "copy", "<init>", "<clinit>"}
JUNK_DESC_MARKERS = ("Intrinsics", "checkNotNull", "requireNotNull", "checkNotNullExpressionValue",
                     "checkNotNullParameter", "$default")


def is_boilerplate_method(method):
    return method in BOILERPLATE_METHODS or method.startswith("component") or method.endswith("$default")


def classify(m):
    method = m.findtext("mutatedMethod") or "?"
    desc = m.findtext("description") or ""
    status = m.get("status")
    # Kotlin-synthetic equivalent mutants (null-check intrinsics, data-class synthetics)
    if any(mark in desc for mark in JUNK_DESC_MARKERS):
        return "junk", "kotlin-intrinsic/synthetic (equivalent)"
    if is_boilerplate_method(method):
        return "junk", f"boilerplate method `{method}` ({status})"
    # A survivor in a real method — candidate actionable gap (may still be equivalent; inspect)
    return "real", f"business-logic survivor in `{method}` ({status})"


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    files = sorted(glob.glob(os.path.join(argv[1], "*.mutations.xml")))
    if not files:
        print("no *.mutations.xml found"); return 1
    grand = {"total": 0, "killed": 0, "survived": 0, "junk": 0, "real": 0}
    real_list = []
    print(f"{'arm':<22} {'mutants':>7} {'killed':>6} {'surv':>4} {'junk':>4} {'real':>4}")
    print("-" * 55)
    for f in files:
        name = os.path.basename(f).replace(".mutations.xml", "")
        muts = ET.parse(f).getroot().findall("mutation")
        killed = [m for m in muts if m.get("status") == "KILLED"]
        surv = [m for m in muts if m.get("status") != "KILLED"]
        junk = real = 0
        for m in surv:
            kind, why = classify(m)
            if kind == "junk":
                junk += 1
            else:
                real += 1
                cls = (m.findtext("mutatedClass") or "?").split(".")[-1]
                real_list.append(f"  [{name}] {cls}.{m.findtext('mutatedMethod')}:"
                                  f"{m.findtext('lineNumber')} — {m.findtext('mutator').split('.')[-1]} "
                                  f"({m.get('status')}) :: {why}")
        grand["total"] += len(muts); grand["killed"] += len(killed)
        grand["survived"] += len(surv); grand["junk"] += junk; grand["real"] += real
        print(f"{name:<22} {len(muts):>7} {len(killed):>6} {len(surv):>4} {junk:>4} {real:>4}")
    print("-" * 55)
    print(f"{'TOTAL':<22} {grand['total']:>7} {grand['killed']:>6} {grand['survived']:>4} "
          f"{grand['junk']:>4} {grand['real']:>4}")
    s = grand["survived"]
    print()
    if s:
        print(f"Surviving mutants: {s}  |  junk (noise): {grand['junk']} ({100*grand['junk']/s:.0f}%)  "
              f"|  candidate-real: {grand['real']} ({100*grand['real']/s:.0f}%)")
        print(f"=> naive-gate false-positive rate ≈ {100*grand['junk']/s:.0f}% of emitted findings would be junk")
    print("\n--- CANDIDATE-REAL survivors (inspect each: genuine gap vs equivalent) ---")
    print("\n".join(real_list) if real_list else "  (none)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
