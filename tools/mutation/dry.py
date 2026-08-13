"""Duplication summary from a jscpd JSON report.

Shaped to match classify-survivors.py and crap.py: read one report, print the
few numbers the experiment compares between arms, optionally as JSON.

jscpd is language-agnostic and has real Kotlin support, which detekt does not —
detekt has no cross-file clone detection at all.

Produce the input with:
    npx jscpd <src-dir> --reporters json --output <out-dir> --min-tokens 50

Usage: dry.py <path/to/jscpd-report.json> [--json]
"""
import sys
import json


def analyse(path):
    report = json.load(open(path))
    stats = report.get("statistics", {}).get("total", {})
    dups = report.get("duplicates", [])

    lines = stats.get("lines", 0) or 0
    cloned = stats.get("clones", 0) or 0
    dup_lines = stats.get("duplicatedLines", 0) or 0

    # Largest clones first — the ones worth a human's attention if any are.
    biggest = sorted(
        (
            {
                "lines": d.get("lines", 0),
                "a": f'{d.get("firstFile", {}).get("name", "?")}'
                     f':{d.get("firstFile", {}).get("start", "?")}',
                "b": f'{d.get("secondFile", {}).get("name", "?")}'
                     f':{d.get("secondFile", {}).get("start", "?")}',
            }
            for d in dups
        ),
        key=lambda d: -d["lines"],
    )

    return {
        "total_lines": lines,
        "clone_count": cloned,
        "duplicated_lines": dup_lines,
        "duplicated_pct": (100.0 * dup_lines / lines) if lines else 0.0,
        "largest_clones": biggest[:10],
    }


def main(argv):
    if not argv:
        sys.exit(__doc__)
    as_json = "--json" in argv
    path = [a for a in argv if not a.startswith("--")][0]
    r = analyse(path)

    if as_json:
        print(json.dumps(r, indent=2))
        return

    print(f"lines analysed      {r['total_lines']:,}")
    print(f"clones              {r['clone_count']}")
    print(f"duplicated lines    {r['duplicated_lines']:,} ({r['duplicated_pct']:.2f}%)")
    if r["largest_clones"]:
        print("\nlargest clones:")
        for c in r["largest_clones"]:
            print(f"  {c['lines']:>4} lines  {c['a']}  <->  {c['b']}")
    else:
        print("\nno clones above the token threshold")


if __name__ == "__main__":
    main(sys.argv[1:])
