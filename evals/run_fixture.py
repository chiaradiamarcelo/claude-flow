#!/usr/bin/env python3
"""Fixture-level eval runner — the agent-TDD primitive.

  eval.py --test <fixture>        run ONE fixture, always (no cache); red/green + diff
  eval.py --test <f> --agent X    disambiguate a name that exists in >1 corpus
  eval.py --list                  list every fixture with its when/then

A fixture is DATA: input/ (the GIVEN) + a manifest carrying the WHEN and THEN.
The manifest is `test.json`:

  { "given": {"files": "input/"},
    "when":  {"do": "agent", "agent": "api-reviewer"},
    "then":  {"grader": "verdict", "expectedStatus": "FAIL",
              "severities": {"VIOLATION": {"min": 1}}, "mustMention": ["logic"]} }

Legacy flat `expected.json` is also read — the triple is synthesized
(when = agent <corpus dir>, then = its agents.<agent> block) — so every existing
fixture runs untouched.

WHEN is a small CLOSED enum (one handler each), NOT free-text steps — there is no
glue layer to rot (the thing that makes Cucumber an anti-pattern). If the enum
starts sprawling, that's the signal to switch fixtures to code.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import eval_grade  # noqa: E402  (reuse grade_agent + its tolerant checks)

# Keys that mark a legacy spec as a reviewer verdict spec.
_VERDICT_KEYS = {"expectedStatus", "severities", "issueCount", "mustMention"}
_JSON = re.compile(r"\{.*\}", re.S)
_REVIEW_PROMPT = ("Review the file(s) under {given}/ (read them directly with the "
                  "Read tool). Return ONLY your machine-first JSON verdict.")
_REV_TOOLS = ["Read", "Glob", "Grep"]


# ---- manifest loading (test.json, or legacy expected.json) ------------------
def load_manifest(fixture_dir):
    """Return {given, when, then, description} for a fixture, or None if neither
    manifest exists. The corpus agent is the grandparent dir name."""
    agent = fixture_dir.parent.parent.name  # evals/<agent>/fixtures/<name>

    tj = fixture_dir / "test.json"
    if tj.is_file():
        m = json.loads(tj.read_text())
        m.setdefault("given", {"files": "input/"})
        return m

    ej = fixture_dir / "expected.json"
    if ej.is_file():
        doc = json.loads(ej.read_text())
        spec = (doc.get("agents") or {}).get(agent, {})
        grader = "verdict" if _VERDICT_KEYS & set(spec) else f"unsupported:{agent}"
        then = dict(spec)
        then["grader"] = grader
        return {"given": {"files": "input/"},
                "when": {"do": "agent", "agent": agent},
                "then": then,
                "description": doc.get("description", "")}
    return None


# ---- WHEN handlers (the closed enum) ----------------------------------------
def do_agent(fixture_dir, when, given_dir):
    """Dispatch a reviewer in a FRESH process (finding 04: in-session caches a
    stale agent def) and return its parsed JSON verdict (None if unparseable)."""
    proc = subprocess.run(
        ["claude", "-p", _REVIEW_PROMPT.format(given=given_dir),
         "--agent", when["agent"], "--allowedTools", *_REV_TOOLS],
        capture_output=True, text=True, stdin=subprocess.DEVNULL)
    m = _JSON.search(proc.stdout or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


STEPS = {"agent": do_agent}
GRADERS = {"verdict": eval_grade.grade_agent}


# ---- resolution -------------------------------------------------------------
def find_fixtures(name, agent=None, base=EVALS):
    hits = []
    for d in sorted(base.glob("*/fixtures/*")):
        if not d.is_dir() or d.name != name:
            continue
        if agent and d.parent.parent.name != agent:
            continue
        if (d / "test.json").is_file() or (d / "expected.json").is_file():
            hits.append(d)
    return hits


def all_fixtures(base=EVALS):
    return [d for d in sorted(base.glob("*/fixtures/*"))
            if d.is_dir() and ((d / "test.json").is_file() or (d / "expected.json").is_file())]


# ---- run one fixture --------------------------------------------------------
def run_one(fixture_dir):
    corpus = fixture_dir.parent.parent.name
    label = f"{corpus} / {fixture_dir.name}"
    m = load_manifest(fixture_dir)
    when, then = m["when"], m["then"]

    handler = STEPS.get(when.get("do"))
    if handler is None:
        print(f"✗ {label}: unknown when.do={when.get('do')!r}")
        return 1
    grader = GRADERS.get(then.get("grader"))
    if grader is None:
        print(f"- SKIP  {label}: grader {then.get('grader')!r} not supported "
              f"by --test yet (MVP covers the reviewer 'verdict' kind)")
        return 0

    given_dir = fixture_dir / m.get("given", {}).get("files", "input/").rstrip("/")
    t0 = time.perf_counter()
    actual = handler(fixture_dir, when, given_dir)
    dt = time.perf_counter() - t0

    spec = {k: v for k, v in then.items() if k != "grader"}
    fails = grader(spec, actual)

    if fails:
        print(f"✗ RED   {label}   ({when.get('do')} {when.get('agent', '')}, {dt:.1f}s)")
        print(f"  then:  grader={then.get('grader')}")
        for f in fails:
            print(f"    · {f}")
        print(f"  actual: {json.dumps(actual) if actual is not None else '(no parseable JSON)'}")
        return 1

    print(f"✓ GREEN {label}   ({dt:.1f}s)")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", help="fixture name to run")
    ap.add_argument("--agent", help="disambiguate a fixture name across corpora")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    if args.list:
        for d in all_fixtures():
            m = load_manifest(d)
            w, t = m["when"], m["then"]
            print(f"{d.parent.parent.name:18} {d.name:42} "
                  f"when={w.get('do')}:{w.get('agent', '')}  then={t.get('grader')}")
        return 0

    if not args.test:
        ap.error("need --test <fixture> or --list")

    hits = find_fixtures(args.test, args.agent)
    if not hits:
        where = f" under agent {args.agent!r}" if args.agent else ""
        print(f"no fixture named {args.test!r}{where}")
        return 2
    if len(hits) > 1:
        corpora = ", ".join(h.parent.parent.name for h in hits)
        print(f"ambiguous {args.test!r} — found in: {corpora}. Pass --agent <name>.")
        return 2
    return run_one(hits[0])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
