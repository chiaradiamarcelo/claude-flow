#!/usr/bin/env python3
"""Extract a normalised scorecard for one pipeline run.

Emits per-unit metrics (per scenario, per test row) rather than totals, because
runs are compared ACROSS FEATURES, not by repeating the same feature. Totals are
meaningless for that comparison; rates are not.

Usage:
    extract_run.py <subagents-dir> [--plans <spec-folder>] [--label NAME]
                   [--scenarios N] [--json out.json]

<subagents-dir>  …/<session-id>/subagents/  (agent-*.jsonl + agent-*.meta.json)
--plans          docs/specifications/<feature>/  (for row-level quality metrics)
"""
import json, glob, os, re, sys, argparse, collections
from datetime import datetime

# --- where generated characters landed -------------------------------------

def bucket(path: str) -> str:
    p = path.replace("\\", "/")
    if re.search(r"/specifications?/.*/specification\.md$", p):
        return "spec_sot"
    if re.search(r"/specifications?/.*\.md$", p):
        return "spec_plan"
    if p.endswith(".md"):
        return "other_md"
    if re.search(r"\.(kt|java|ts|tsx|py|go|rs)$", p):
        if re.search(r"(^|/)(test|tests)/|Test\.(kt|java|ts)$|\.contract\.kt$"
                     r"|Robot\.kt$|Fixtures?\.kt$|Assertions\.kt$|(^|/)fakes?/"
                     r"|_test\.(py|go)$|\.spec\.tsx?$", p):
            return "code_test"
        return "code_prod"
    return "other"

def generated(inp: dict):
    """(path, chars) for each Write/Edit/MultiEdit payload."""
    path = inp.get("file_path") or inp.get("notebook_path") or "?"
    if "content" in inp:
        yield path, len(inp["content"] or "")
    if "new_string" in inp:
        yield path, len(inp["new_string"] or "")
    for e in inp.get("edits") or []:
        yield path, len(e.get("new_string") or "")

BUILD = re.compile(r"\b(gradlew|gradle|mvn|npm (run )?test|pytest|cargo test|go test)\b")
COMMIT = re.compile(r"\bgit\s+commit\b")
REVIEWER = re.compile(r"reviewer|refactor-advisor", re.I)
FIXMODE = re.compile(r"\bfix\b", re.I)

# --- transcript mining ------------------------------------------------------

def parse_ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def mine(subagents_dir):
    runs = []
    for meta_path in sorted(glob.glob(f"{subagents_dir}/*.meta.json")):
        meta = json.load(open(meta_path))
        tx = meta_path.replace(".meta.json", ".jsonl")
        if not os.path.exists(tx):
            continue
        r = {
            "role": meta.get("agentType", "?"),
            "desc": meta.get("description", ""),
            "depth": meta.get("spawnDepth", 1),
            "out_tok": 0, "cache_read": 0, "in_tok": 0,
            "chars": collections.Counter(),
            "tools": collections.Counter(),
            "models": set(), "efforts": set(),
            "build_calls": 0, "commits": 0,
            "start": None, "end": None,
        }
        for line in open(tx, errors="replace"):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = parse_ts(ev.get("timestamp", ""))
            if ts:
                r["start"] = ts if r["start"] is None else min(r["start"], ts)
                r["end"] = ts if r["end"] is None else max(r["end"], ts)
            if ev.get("effort"):
                r["efforts"].add(ev["effort"])
            msg = ev.get("message") or {}
            if msg.get("model"):
                r["models"].add(msg["model"])
            u = msg.get("usage") or {}
            r["out_tok"] += u.get("output_tokens", 0) or 0
            r["in_tok"] += u.get("input_tokens", 0) or 0
            r["cache_read"] += u.get("cache_read_input_tokens", 0) or 0
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name = b.get("name", "")
                r["tools"][name] += 1
                inp = b.get("input") or {}
                if name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                    for path, n in generated(inp):
                        r["chars"][bucket(path)] += n
                elif name == "Bash":
                    cmd = inp.get("command", "") or ""
                    if BUILD.search(cmd):
                        r["build_calls"] += 1
                    if COMMIT.search(cmd):
                        r["commits"] += 1
        r["dur_s"] = (r["end"] - r["start"]).total_seconds() if r["start"] and r["end"] else 0
        runs.append(r)
    return runs

# --- row-level quality from plan files --------------------------------------

STATUS = re.compile(r"\|\s*(✅|☑|☐|❌)([^|\n]*)\|?\s*$", re.M)

def rows_from_plans(plans_dir):
    """Classify Status cells. Heuristic today; a mandated status vocabulary in
    the developer prompt makes this exact for future runs."""
    c = collections.Counter()
    for f in sorted(glob.glob(f"{plans_dir}/*.md")):
        if os.path.basename(f) == "specification.md":
            continue
        for mark, tail in STATUS.findall(open(f, errors="replace").read()):
            t = tail.lower()
            c["total"] += 1
            if mark == "☐":
                c["open"] += 1
            elif "unplanned" in t:
                c["unplanned"] += 1
            elif "early-green" in t or "early green" in t:
                c["early_green"] += 1
            elif "red" in t:
                c["red_then_green"] += 1
            elif "executed green" in t or "emulator" in t:
                c["deferred_blind"] += 1
            else:
                c["unclassified"] += 1
    return c

NOTE_TO_ARCHITECT = re.compile(r"^>\s*Note to (?:system-)?architect:", re.M)
STALE_PLAN = re.compile(r"^>\s*Stale plan:(.*)$", re.M)


def staleness_from_plans(plans_dir):
    """Plan-vs-code divergences the developer recorded, split by what mis-predicted.

    This is the measurement Stage 3 exists for. Planning a scenario ahead of its
    predecessor's implementation is safe only if divergences are rare AND mostly
    trace to a predecessor's PLAN (which exists when the planner reads it) rather
    than its CODE (which does not yet). A run heavy in code-attributed staleness
    means the lookahead is too deep for that feature."""
    events, by_source = [], collections.Counter()
    for f in sorted(glob.glob(f"{plans_dir}/*.md")):
        for tail in STALE_PLAN.findall(open(f, errors="replace").read()):
            events.append((os.path.basename(f), tail.strip()))
            m = re.search(r"SOURCE\s*=\s*(code|plan)\b", tail, re.I)
            by_source[m.group(1).lower() if m else "unattributed"] += 1
    return events, by_source

def catches_from_plans(plans_dir):
    """Agent-corrects-agent events. The test-designer prompt MANDATES a
    `> Note to architect:` line for every structural gap, so these are the one
    mechanically-countable proxy for judgment (as opposed to artifacts).
    Human-corrects-agent and defects-found-by-red-state are still hand-logged."""
    n = 0
    for f in sorted(glob.glob(f"{plans_dir}/*.md")):
        n += len(NOTE_TO_ARCHITECT.findall(open(f, errors="replace").read()))
    return n

def reviewer_rounds(runs):
    """Group reviewer dispatches into rounds, and score how parallel each was.

      ratio = sum(durations) / span   →  1.0 = fully serial, n = fully parallel

    A round boundary is a DEVELOPER dispatch, not an idle gap. The baseline arm
    proved why: its four review rounds were separated by fix dispatches shorter
    than any sensible gap threshold, so a 15-minute-gap heuristic collapsed all
    eleven reviewers into one 'round' and understated the serialisation.
    Review → fix → review is the actual cycle, so the fix is the delimiter."""
    ordered = sorted((r for r in runs if r["start"]), key=lambda r: r["start"])
    rounds, cur = [], []
    for r in ordered:
        if REVIEWER.search(r["role"]):
            cur.append(r)
        elif cur:                      # a non-reviewer closes the open round
            rounds.append(cur); cur = []
    if cur:
        rounds.append(cur)
    out = []
    for rd in rounds:
        span = (max(x["end"] for x in rd) - min(x["start"] for x in rd)).total_seconds()
        tot = sum(x["dur_s"] for x in rd)
        out.append({"n": len(rd), "span_min": span / 60, "sum_min": tot / 60,
                    "ratio": (tot / span) if span else float("nan"),
                    "names": [x["role"] for x in rd]})
    return out

def fix_rounds(runs):
    fx = [r for r in runs if r["role"] == "developer" and FIXMODE.search(r["desc"])]
    return {"n": len(fx), "min": sum(r["dur_s"] for r in fx) / 60,
            "out_tok": sum(r["out_tok"] for r in fx)}

# --- reporting --------------------------------------------------------------

CATS = ["spec_plan", "spec_sot", "other_md", "code_prod", "code_test", "other"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subagents")
    ap.add_argument("--plans")
    ap.add_argument("--label", default="run")
    ap.add_argument("--scenarios", type=int, default=0)
    ap.add_argument("--json")
    a = ap.parse_args()

    runs = mine(a.subagents)
    if not runs:
        sys.exit(f"no subagent transcripts under {a.subagents}")

    span_start = min(r["start"] for r in runs if r["start"])
    span_end = max(r["end"] for r in runs if r["end"])
    span_min = (span_end - span_start).total_seconds() / 60
    agent_min = sum(r["dur_s"] for r in runs) / 60
    out_tok = sum(r["out_tok"] for r in runs)

    by_role = collections.defaultdict(
        lambda: {"n": 0, "out": 0, "dur": 0.0, "chars": collections.Counter(),
                 "builds": 0, "models": set(), "efforts": set(), "reads": 0})
    for r in runs:
        g = by_role[r["role"]]
        g["n"] += 1; g["out"] += r["out_tok"]; g["dur"] += r["dur_s"]
        g["chars"] += r["chars"]; g["builds"] += r["build_calls"]
        g["models"] |= r["models"]; g["efforts"] |= r["efforts"]
        g["reads"] += r["tools"]["Read"]

    rows = rows_from_plans(a.plans) if a.plans else collections.Counter()
    n_rows = rows.get("total", 0)
    n_scen = a.scenarios or 0

    def per(v, d):
        return v / d if d else float("nan")

    print(f"# Scorecard — {a.label}\n")
    print(f"- span **{span_min:.0f} min** · agent time {agent_min:.0f} min "
          f"· dispatches {len(runs)} · output tokens {out_tok:,}")
    if n_scen:
        print(f"- scenarios {n_scen} · **{per(span_min, n_scen):.1f} min/scenario** "
              f"· {per(out_tok, n_scen):,.0f} out-tok/scenario")
    if n_rows:
        print(f"- test rows {n_rows} · **{per(span_min, n_rows):.2f} min/row** "
              f"· {per(out_tok, n_rows):,.0f} out-tok/row")

    print("\n## Cost by role\n")
    print("| role | disp | min | out tok | tok/disp | md chars | code chars | md share | builds | reads | model | effort |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for role, g in sorted(by_role.items(), key=lambda kv: -kv[1]["out"]):
        md = g["chars"]["spec_plan"] + g["chars"]["spec_sot"] + g["chars"]["other_md"]
        code = g["chars"]["code_prod"] + g["chars"]["code_test"]
        share = f"{100*md/(md+code):.0f}%" if (md + code) else "—"
        models = ",".join(sorted(m.split("-2")[0] for m in g["models"])) or "—"
        efforts = ",".join(sorted(g["efforts"])) or "—"
        print(f"| {role} | {g['n']} | {g['dur']/60:.1f} | {g['out']:,} | "
              f"{g['out']//max(g['n'],1):,} | {md:,} | {code:,} | {share} | "
              f"{g['builds']} | {g['reads']} | {models} | {efforts} |")

    if n_rows:
        print("\n## Row-level quality (normalised)\n")
        print("| metric | count | rate |")
        print("|---|---|---|")
        for k in ("red_then_green", "early_green", "deferred_blind",
                  "unplanned", "unclassified", "open"):
            v = rows.get(k, 0)
            print(f"| {k} | {v} | {100*v/n_rows:.1f}% |")
        print(f"\n> `unclassified` is free-text Status cells the parser could not "
              f"classify. Mandating a status vocabulary in the developer prompt "
              f"drives this to 0 for future runs.")

    # --- Stage 1 treatment metrics ---
    rounds = reviewer_rounds(runs)
    fx = fix_rounds(runs)
    commits = sum(r["commits"] for r in runs)
    catches = catches_from_plans(a.plans) if a.plans else 0

    print("\n## Stage 1 metrics (reviewer gate · batching · commits)\n")
    print("| metric | value |")
    print("|---|---|")
    for i, rd in enumerate(rounds, 1):
        verdict = "SERIAL" if rd["ratio"] < 1.5 else ("parallel" if rd["ratio"] > 0.6 * rd["n"] else "partial")
        print(f"| reviewer round {i} | {rd['n']} reviewers · span {rd['span_min']:.1f} min "
              f"· sum {rd['sum_min']:.1f} min · **ratio {rd['ratio']:.2f} → {verdict}** |")
    print(f"| fix rounds | {fx['n']} · {fx['min']:.1f} min · {fx['out_tok']:,} out tok |")
    print(f"| git commits during run | {commits} |")
    print(f"| catches (`> Note to architect:`) | {catches} |")
    if a.plans:
        stale, by_src = staleness_from_plans(a.plans)
        print(f"| **plan staleness** (`> Stale plan:`) | **{len(stale)}** "
              f"— plan-attributed {by_src['plan']}, code-attributed {by_src['code']}, "
              f"unattributed {by_src['unattributed']} |")
    print("\n> ratio = sum(durations)/span. 1.0 means the reviewers ran one after "
          "another; n means all n went out in a single message, as `/run-reviewers` requires.")

    if a.json:
        payload = {
            "reviewer_rounds": rounds, "fix_rounds": fx,
            "commits": commits, "catches_note_to_architect": catches,
            "staleness": {"events": [{"file": f, "note": n} for f, n in
                                     (staleness_from_plans(a.plans)[0] if a.plans else [])],
                          "by_source": dict(staleness_from_plans(a.plans)[1]) if a.plans else {}},
            "label": a.label, "span_min": span_min, "agent_min": agent_min,
            "dispatches": len(runs), "output_tokens": out_tok,
            "scenarios": n_scen, "rows": n_rows,
            "min_per_scenario": per(span_min, n_scen),
            "min_per_row": per(span_min, n_rows),
            "out_tok_per_row": per(out_tok, n_rows),
            "roles": {r: {"n": g["n"], "min": g["dur"]/60, "out_tok": g["out"],
                          "chars": dict(g["chars"]), "builds": g["builds"],
                          "reads": g["reads"], "models": sorted(g["models"]),
                          "efforts": sorted(g["efforts"])}
                      for r, g in by_role.items()},
            "rows_detail": dict(rows),
        }
        json.dump(payload, open(a.json, "w"), indent=2)
        print(f"\n_wrote {a.json}_")

if __name__ == "__main__":
    main()
