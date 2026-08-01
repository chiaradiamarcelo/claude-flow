#!/usr/bin/env python3
"""Repeated-run variance analysis for the strict-vs-batch A/B.

Collects N runs per arm of the same scenario (account-overview) and reports, per metric,
each arm's mean / std / min / max — then the key question: does the between-arm gap
(strict.mean - batch.mean) exceed the within-arm noise, and do the per-arm [min,max]
ranges stay disjoint (clean separation)?

Usage: analyze-variance.py <strict_metrics.json>... -- <batch_metrics.json>...
Each metrics.json is a `metrics.py --json` dump.
"""
import sys, json, statistics

METRICS = [
    ("output_tokens", "tokens", 0),
    ("total_cost_usd", "cost $", 2),
    ("gradle_runs", "gradle", 0),
    ("num_turns", "turns", 0),
    ("wall_seconds", "wall s", 0),
]


def load(paths):
    out = []
    for p in paths:
        with open(p) as fh:
            out.append(json.load(fh))
    return out


def stats(vals):
    return {
        "mean": statistics.mean(vals),
        "std": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "min": min(vals),
        "max": max(vals),
    }


def main(argv):
    if "--" not in argv:
        print(__doc__); return 2
    i = argv.index("--")
    strict = load(argv[1:i])
    batch = load(argv[i + 1:])
    print(f"n = {len(strict)} strict runs, {len(batch)} batch runs\n")
    header = f"{'metric':>8} | {'strict mean±std (min–max)':>34} | {'batch mean±std (min–max)':>34} | {'Δmean':>8} | separated?"
    print(header); print("-" * len(header))
    for key, label, nd in METRICS:
        s = stats([r[key] for r in strict])
        b = stats([r[key] for r in batch])
        # clean separation: strict range and batch range do not overlap
        sep = s["min"] > b["max"] or b["min"] > s["max"]
        dmean = s["mean"] - b["mean"]
        pct = (dmean / s["mean"] * 100) if s["mean"] else 0
        fmt = f"%.{nd}f"
        s_str = f"{fmt % s['mean']}±{fmt % s['std']} ({fmt % s['min']}–{fmt % s['max']})"
        b_str = f"{fmt % b['mean']}±{fmt % b['std']} ({fmt % b['min']}–{fmt % b['max']})"
        print(f"{label:>8} | {s_str:>34} | {b_str:>34} | {pct:>6.0f}% | {'YES' if sep else 'no'}")
    print("\n'separated?' = the two arms' [min,max] ranges are disjoint for this metric "
          "(the batch advantage exceeds all observed run-to-run noise).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
