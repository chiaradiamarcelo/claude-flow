#!/usr/bin/env python3
"""CRAP score from a JaCoCo XML report.

CRAP(m) = comp(m)^2 * (1 - cov(m))^3 + comp(m)

  comp(m) = cyclomatic complexity of the method (JaCoCo COMPLEXITY counter total)
  cov(m)  = fraction of the method's lines covered by tests (JaCoCo LINE counter)

A method is "crappy" above 30 (Alberto Savoia / the original crap4j threshold).
Emits a per-method table and the summary the experiment compares between arms:
method count, methods over threshold, and total/mean CRAP.

Usage: crap.py <path/to/jacocoTestReport.xml> [--threshold 30] [--json]
"""
import sys
import json
import xml.etree.ElementTree as ET


def coverage(counters, ctype):
    for c in counters:
        if c.get("type") == ctype:
            covered = int(c.get("covered", 0))
            missed = int(c.get("missed", 0))
            return covered, missed
    return 0, 0


def crap(comp, cov):
    return comp ** 2 * (1 - cov) ** 3 + comp


def analyse(xml_path, threshold=30.0):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    methods = []
    for pkg in root.iter("package"):
        pkg_name = pkg.get("name", "")
        for cls in pkg.iter("class"):
            cls_name = cls.get("name", "").split("/")[-1]
            for m in cls.findall("method"):
                counters = m.findall("counter")
                comp_cov, comp_missed = coverage(counters, "COMPLEXITY")
                comp = comp_cov + comp_missed
                if comp == 0:
                    continue
                line_cov, line_missed = coverage(counters, "LINE")
                total_lines = line_cov + line_missed
                cov = (line_cov / total_lines) if total_lines else 1.0
                score = crap(comp, cov)
                methods.append({
                    "package": pkg_name,
                    "class": cls_name,
                    "method": m.get("name"),
                    "complexity": comp,
                    "coverage": round(cov, 3),
                    "crap": round(score, 2),
                })
    methods.sort(key=lambda x: x["crap"], reverse=True)
    over = [m for m in methods if m["crap"] > threshold]
    total = sum(m["crap"] for m in methods)
    return {
        "threshold": threshold,
        "methods": len(methods),
        "over_threshold": len(over),
        "total_crap": round(total, 2),
        "mean_crap": round(total / len(methods), 2) if methods else 0.0,
        "worst": methods[:10],
        "over": over,
    }


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv
    threshold = 30.0
    for a in argv:
        if a.startswith("--threshold"):
            threshold = float(a.split("=", 1)[1]) if "=" in a else 30.0
    if not args:
        print(__doc__)
        return 2
    result = analyse(args[0], threshold)
    if as_json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"methods={result['methods']}  over_{int(threshold)}={result['over_threshold']}  "
          f"total_crap={result['total_crap']}  mean_crap={result['mean_crap']}")
    print(f"{'CRAP':>8}  {'comp':>4}  {'cov':>5}  method")
    for m in result["worst"]:
        print(f"{m['crap']:>8}  {m['complexity']:>4}  {m['coverage']:>5}  "
              f"{m['class']}.{m['method']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
