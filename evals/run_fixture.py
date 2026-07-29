#!/usr/bin/env python3
"""Fixture-level eval runner — the single eval engine.

Every fixture is DATA: a `test.json` manifest with given / when / then.
  given : where inputs live + which workspace to set up (golden-repo, git-scratch, none)
  when  : the action — a CLOSED enum  do: "agent" | "command" | "build"
  then  : grader name + its tolerant spec

  ./evals/evals --test <fixture>        run one, always (no cache); red/green + diff
  ./evals/evals --test <f> --agent X    disambiguate a name across corpora
  ./evals/evals --list                  every fixture with its when/then

WHEN is a closed enum (3 handlers), NOT free-text steps — there is no glue layer
to rot (the Cucumber failure mode). A new kind = a new `do` handler + a `then`
grader, both small. Graders are the existing pure grade_* functions, reused.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

EVALS = Path(__file__).resolve().parent
sys.path.insert(0, str(EVALS))
import eval_grade          # noqa: E402  grade_agent (verdict)
import check_plan          # noqa: E402
import check_testplan      # noqa: E402
import check_fidelity      # noqa: E402
import check_build         # noqa: E402
import check_spec          # noqa: E402
import check_choreography  # noqa: E402
import check_refusal       # noqa: E402
import check_routing       # noqa: E402
import verify_acceptance   # noqa: E402

_JSON = re.compile(r"\{.*\}", re.S)
_REVIEW_PROMPT = ("Review the file(s) under {d}/ (read them directly with the "
                  "Read tool). Return ONLY your machine-first JSON verdict.")
REVIEW_TOOLS = ["Read", "Glob", "Grep"]
PLAN_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Skill"]
DEV_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Skill"]
CMD_TOOLS = ["Task", "Agent", "Read", "Write", "Edit", "Bash", "Glob", "Grep", "Skill"]


def _extract_json(text):
    m = _JSON.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _claude(prompt, cwd, tools, agent=None):
    cmd = ["claude", "-p", prompt] + (["--agent", agent] if agent else []) \
        + ["--allowedTools", *tools]
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)


# ---------- GIVEN: workspace setup -------------------------------------------
def setup_workspace(fixture_dir, given):
    """Make a scratch dir per given.workspace and overlay given.files. (Verdict
    reviewers don't call this — they read input/ in place.)"""
    scratch = Path(tempfile.mkdtemp(prefix="eval-"))
    ws = given.get("workspace")
    if ws == "git-scratch":
        subprocess.run(["git", "init", "-q"], cwd=str(scratch))
        for f in given.get("changedFiles", []):
            p = scratch / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
    elif ws and (EVALS / ws).is_dir():  # any buildable skeleton (golden-repo, golden-repo-spring, ...)
        shutil.copytree(EVALS / ws, scratch, dirs_exist_ok=True)
        shutil.rmtree(scratch / "build", ignore_errors=True)
        shutil.rmtree(scratch / ".gradle", ignore_errors=True)
        shutil.rmtree(scratch / ".kotlin", ignore_errors=True)
    files = given.get("files")
    if files and (fixture_dir / files.rstrip("/")).is_dir():
        shutil.copytree(fixture_dir / files.rstrip("/"), scratch, dirs_exist_ok=True)
    return scratch


# ---------- WHEN: the closed enum of handlers --------------------------------
def do_agent(fixture_dir, when, scratch):
    if "prompt" in when:  # artifact-producing agent (e.g. architect writes a plan)
        _claude(when["prompt"], scratch, when.get("tools", PLAN_TOOLS), agent=when["agent"])
        return {"scratch": scratch, "input_dir": fixture_dir / "input"}
    given_dir = fixture_dir / "input"  # verdict reviewer: read in place
    proc = _claude(_REVIEW_PROMPT.format(d=given_dir), fixture_dir,
                   when.get("tools", REVIEW_TOOLS), agent=when["agent"])
    return {"verdict": _extract_json(proc.stdout)}


def do_command(fixture_dir, when, scratch):
    proc = _claude(when["command"], scratch, when.get("tools", CMD_TOOLS))
    (scratch / ".output.log").write_text((proc.stdout or "") + (proc.stderr or ""))
    return {"scratch": scratch, "output": proc.stdout or ""}


def do_build(fixture_dir, when, scratch):
    _claude(when["prompt"], scratch, when.get("tools", DEV_TOOLS), agent=when["agent"])
    return {"scratch": scratch, "build_exit": verify_acceptance.gradle_build(scratch)}


HANDLERS = {"agent": do_agent, "command": do_command, "build": do_build}


# ---------- THEN: grader registry (reuse the pure grade_* functions) ---------
def _g_choreography(spec, ctx):
    log = Path(ctx["scratch"]) / spec.get("logFile", "pipeline-calls.log")
    lines = ([ln.strip() for ln in log.read_text().splitlines() if ln.strip()]
             if log.is_file() else [])
    return check_choreography.grade(spec, lines)


GRADERS = {
    "verdict":      lambda spec, ctx: eval_grade.grade_agent(spec, ctx.get("verdict")),
    "plan":         lambda spec, ctx: check_plan.grade_plan(spec, ctx["input_dir"], ctx["scratch"]),
    "testplan":     lambda spec, ctx: check_testplan.grade_testplan(spec, ctx["input_dir"], ctx["scratch"]),
    "fidelity":     lambda spec, ctx: check_fidelity.grade_fidelity(spec, ctx["scratch"]),
    "build":        lambda spec, ctx: check_build.grade_build(spec, ctx["scratch"], ctx["build_exit"]),
    "spec":         lambda spec, ctx: check_spec.grade_spec(spec, ctx["fixture_dir"] / "input", ctx["scratch"]),
    "acceptance":   lambda spec, ctx: verify_acceptance.verify(spec, ctx["scratch"])[0],
    "choreography": _g_choreography,
    "refusal":      lambda spec, ctx: check_refusal.grade(spec, ctx["scratch"], ctx["output"]),
    "routing":      lambda spec, ctx: check_routing.grade_routing(spec, ctx["output"]),
}

_NEEDS_SCRATCH = {"command", "build"}  # plus any agent-with-prompt (handled in run_one)


# ---------- resolution -------------------------------------------------------
def find_fixtures(name, agent=None, base=EVALS):
    return [d for d in sorted(base.glob("*/fixtures/*"))
            if d.is_dir() and d.name == name and (d / "test.json").is_file()
            and (agent is None or d.parent.parent.name == agent)]


def all_fixtures(base=EVALS):
    return [d for d in sorted(base.glob("*/fixtures/*"))
            if d.is_dir() and (d / "test.json").is_file()]


def load_manifest(fixture_dir):
    return json.loads((fixture_dir / "test.json").read_text())


# ---------- run one fixture --------------------------------------------------
def run_one(fixture_dir):
    corpus = fixture_dir.parent.parent.name
    label = f"{corpus} / {fixture_dir.name}"
    m = load_manifest(fixture_dir)
    when, then = m["when"], m["then"]

    handler = HANDLERS.get(when.get("do"))
    grader = GRADERS.get(then.get("grader"))
    if handler is None:
        print(f"✗ {label}: unknown when.do={when.get('do')!r}"); return 1
    if grader is None:
        print(f"✗ {label}: unknown then.grader={then.get('grader')!r}"); return 1

    needs_scratch = when["do"] in _NEEDS_SCRATCH or "prompt" in when
    scratch = setup_workspace(fixture_dir, m.get("given", {})) if needs_scratch else None
    spec = {k: v for k, v in then.items() if k != "grader"}

    t0 = time.perf_counter()
    ctx = handler(fixture_dir, when, scratch)
    ctx["fixture_dir"] = fixture_dir
    fails = grader(spec, ctx)
    dt = time.perf_counter() - t0

    if fails:
        print(f"✗ RED   {label}   ({when['do']} {when.get('agent', '')}, {dt:.1f}s)".replace("  ", " "))
        print(f"  then:  grader={then.get('grader')}")
        for f in fails:
            print(f"    · {f}")
        if "verdict" in ctx:
            print(f"  actual: {json.dumps(ctx['verdict']) if ctx['verdict'] is not None else '(no parseable JSON)'}")
        if scratch:
            print(f"  scratch kept: {scratch}")
        return 1

    if scratch:
        shutil.rmtree(scratch, ignore_errors=True)
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
            line = (f"{d.parent.parent.name:18} {d.name:42} "
                    f"when={w.get('do')}:{w.get('agent', '')}".rstrip())
            print(f"{line}  then={t.get('grader')}")
        return 0

    if not args.test:
        ap.error("need --test <fixture> or --list")
    hits = find_fixtures(args.test, args.agent)
    if not hits:
        where = f" under agent {args.agent!r}" if args.agent else ""
        print(f"no fixture named {args.test!r}{where}"); return 2
    if len(hits) > 1:
        print(f"ambiguous {args.test!r} — in: "
              + ", ".join(h.parent.parent.name for h in hits) + ". Pass --agent.")
        return 2
    return run_one(hits[0])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
