#!/usr/bin/env python3
"""Classify PIT mutants: which surviving ones are real, actionable test gaps.

Usage: classify-survivors.py <dir | mutations.xml>

Given a directory, reads every `*.mutations.xml` (the benchmark rig's per-arm
copies) **and** a plain `mutations.xml` — which is what PIT itself writes, under
`build/reports/pitest/` (Gradle) or `target/pit-reports/<timestamp>/` (Maven).

Buckets, and why each exists. Same vocabulary as classify-stryker.py, so a JVM
number and a TS number mean the same thing:

  killed      KILLED + TIMED_OUT + MEMORY_ERROR + RUN_ERROR. **PIT counts all four
              as detected**, and so does its own mutation score. Counting a timeout
              as surviving was worth 38 phantom survivors on one Kotlin run — and it
              is systematic rather than marginal on Flow code, where a negated
              conditional in a collector hangs far more often than it fails.
  excluded    NON_VIABLE. Bytecode PIT produced that will not load. Not a result, so
              not in the denominator either.
  uncovered   NO_COVERAGE. A gap, but a different one: no test executes the line, so
              "strengthen the assertion" is the wrong ask. Kotlin also manufactures
              these — an `internal inline fun` has a standalone copy that is never
              called, and PIT reports every mutant in it as uncovered.
  junk        Not source-expressible, or provably equivalent. See below.
  real        Candidate actionable gaps. Candidates, not certainties.

JUNK, and the honest limit of it. Two families:

  1. Generated Kotlin that has no source form. The compiler emits a coroutine state
     machine (`invokeSuspend`, `create`), inlining artefacts (`$inlined$map$1$2.emit`,
     `$inlined$...collect`), serializer plumbing (`$$serializer.deserialize`),
     data-class synthetics (`component1`, `copy`, property accessors) and null-check
     intrinsics. **No test can kill a mutant here, because no author can write the
     line it mutates.** These are dropped without apology.
  2. Data-class synthetics, property accessors and null-check intrinsics — as before.

DELIBERATELY NOT FILTERED: suspend-function entry lines. On the run that motivated
this file, many survivors were `VoidMethodCall`/`NullReturnVals` mutants landing on
the coroutine state-machine `label` switch rather than on a statement anyone wrote —
`MarkBoulderSentUseCase.invoke:14` three times over. That was established by reading
the source, and **this script cannot do that.** PIT's XML gives no way to tell an
entry-line mutant from a real one inside the same suspend function, and dropping
every void-call mutant in every suspend function would discard exactly where real
gaps live in coroutine code. Writing that rule needs a report to validate against;
the one that motivated it is gone, so it waits for the next coroutine run.

The deeper limit, which no rule fixes: PIT can mutate a *different bytecode
conditional* than the one you would edit. On that same run the single reproducible
survivor was a `NegateConditionals` inside an inlined `any {}` — applying the obvious
source edit killed it, with 4 failing tests. **A candidate-real survivor is a lead to
reproduce, never a verdict.**
"""
import sys, glob, os, xml.etree.ElementTree as ET

# PIT's own mutation score counts these as detected. Not survivors.
KILLED_STATUSES = {"KILLED", "TIMED_OUT", "MEMORY_ERROR", "RUN_ERROR"}
EXCLUDED_STATUSES = {"NON_VIABLE"}

BOILERPLATE_METHODS = {"equals", "hashCode", "toString", "copy", "<init>", "<clinit>"}
JUNK_DESC_MARKERS = ("Intrinsics", "checkNotNull", "requireNotNull", "checkNotNullExpressionValue",
                     "checkNotNullParameter", "$default")

# Compiler-generated members with no source form. `invokeSuspend`/`create` are the
# coroutine state machine; `emit`/`collect` reach here only on an `$inlined$` class;
# `serialize`/`deserialize`/`childSerializers` are kotlinx.serialization plumbing.
GENERATED_METHODS = {"invokeSuspend", "create", "serialize", "deserialize",
                     "childSerializers", "getDescriptor", "typeParametersSerializers",
                     "access$getLabel", "box", "unbox"}
# Synthetic class-name markers. Matched against the mutated CLASS, not the method.
GENERATED_CLASS_MARKERS = ("$inlined$", "$$serializer", "$WhenMappings", "$Continuation",
                           "$invokeSuspend$", "$special$$inlined")


def is_property_accessor(method):
    """Kotlin compiles `val x` into a synthetic getX()/setX() that contains no
    behaviour of its own. PIT will happily mutate the return of one and report a
    survivor, but there is no test anyone could write that kills it other than a
    test of the property's initialiser — which lives elsewhere. Treated as junk
    for the same reason equals/hashCode are: it is generated, not authored."""
    return (
        (method.startswith("get") or method.startswith("set"))
        and len(method) > 3
        and method[3].isupper()
    )


def is_boilerplate_method(method):
    return (method in BOILERPLATE_METHODS
            or method.startswith("component")
            or method.endswith("$default")
            or is_property_accessor(method))


def is_generated(cls, method):
    """Compiler-emitted member with no source form — a mutant here is unkillable by
    construction, because there is no line an author could change to kill it."""
    return (method in GENERATED_METHODS
            or any(mark in cls for mark in GENERATED_CLASS_MARKERS))


def classify(m):
    """-> (bucket, reason). Buckets: killed|excluded|uncovered|junk|real."""
    cls = m.findtext("mutatedClass") or "?"
    method = m.findtext("mutatedMethod") or "?"
    desc = m.findtext("description") or ""
    status = m.get("status")

    if status in KILLED_STATUSES:
        return "killed", status
    if status in EXCLUDED_STATUSES:
        return "excluded", f"{status} — bytecode that will not load"
    if status == "NO_COVERAGE":
        return "uncovered", f"no test executes `{method}`"

    if is_generated(cls, method):
        return "junk", f"compiler-generated `{cls.split('.')[-1]}.{method}` (no source form)"
    if any(mark in desc for mark in JUNK_DESC_MARKERS):
        return "junk", "kotlin-intrinsic/synthetic (equivalent)"
    if is_boilerplate_method(method):
        return "junk", f"boilerplate method `{method}` ({status})"
    # A survivor in a real method — candidate actionable gap (may still be equivalent; inspect)
    return "real", f"business-logic survivor in `{method}` ({status})"


def report_files(target):
    if os.path.isfile(target):
        return [target]
    return sorted(set(glob.glob(os.path.join(target, "*.mutations.xml")))
                  | set(glob.glob(os.path.join(target, "mutations.xml"))))


BUCKETS = ("killed", "excluded", "uncovered", "junk", "real")


def collect(files):
    """-> (per_arm, grand, real_list, junk_list). One pass, no status logic outside classify."""
    per_arm, grand, real_list, junk_list = [], dict.fromkeys(("total",) + BUCKETS, 0), [], []
    for f in files:
        name = os.path.basename(f).replace(".mutations.xml", "").replace("mutations.xml", "pit")
        muts = ET.parse(f).getroot().findall("mutation")
        counts = dict.fromkeys(BUCKETS, 0)
        for m in muts:
            bucket, why = classify(m)
            counts[bucket] += 1
            if bucket in ("real", "junk"):
                cls = (m.findtext("mutatedClass") or "?").split(".")[-1]
                line = (f"  [{name}] {cls}.{m.findtext('mutatedMethod')}:"
                        f"{m.findtext('lineNumber')} — "
                        f"{(m.findtext('mutator') or '?').split('.')[-1]} "
                        f"({m.get('status')}) :: {why}")
                (real_list if bucket == "real" else junk_list).append(line)
        per_arm.append((name, len(muts), counts))
        grand["total"] += len(muts)
        for b in BUCKETS:
            grand[b] += counts[b]
    return per_arm, grand, real_list, junk_list


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__); return 2
    files = report_files(args[0])
    if not files:
        print(f"no mutations.xml found in {args[0]}"); return 1

    per_arm, grand, real_list, junk_list = collect(files)

    head = f"{'arm':<22} {'mutants':>7} {'killed':>6} {'uncov':>5} {'excl':>4} {'junk':>4} {'real':>4}"
    print(head); print("-" * len(head))
    for name, total, c in per_arm:
        print(f"{name:<22} {total:>7} {c['killed']:>6} {c['uncovered']:>5} "
              f"{c['excluded']:>4} {c['junk']:>4} {c['real']:>4}")
    print("-" * len(head))
    print(f"{'TOTAL':<22} {grand['total']:>7} {grand['killed']:>6} {grand['uncovered']:>5} "
          f"{grand['excluded']:>4} {grand['junk']:>4} {grand['real']:>4}")

    survivors = grand["junk"] + grand["real"]
    print()
    if survivors:
        print(f"Surviving mutants: {survivors}  |  junk (noise): {grand['junk']} "
              f"({100*grand['junk']/survivors:.0f}%)  |  candidate-real: {grand['real']} "
              f"({100*grand['real']/survivors:.0f}%)")
    if grand["uncovered"]:
        print(f"{grand['uncovered']} mutant(s) on lines no test executes — a coverage gap, not a "
              f"weak assertion. Kotlin also manufactures these for `internal inline fun`.")
    print("\n--- CANDIDATE-REAL survivors (reproduce each as a source edit before believing it) ---")
    print("\n".join(real_list) if real_list else "  (none)")
    if junk_list:
        if "--show-junk" in flags:
            print("\n--- DROPPED as junk ---")
            print("\n".join(junk_list))
        else:
            print(f"\n{len(junk_list)} mutant(s) dropped as junk — re-run with --show-junk to audit them.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
