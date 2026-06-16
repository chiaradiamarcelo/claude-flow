#!/usr/bin/env python3
"""Deterministic, model-free eval grader.

Grades recorded agent outputs ("actuals") against per-fixture `expected.json`
specs, with no model and no judgment — only coarse, non-determinism-tolerant
checks: status match, issue-count range, and must-mention substrings. This is
what lets a grader of a non-deterministic agent run as a flake-free gate.

Modes
-----
--check-corpus   Structural only (no actuals): every fixtures/<stem>/expected.json
                 is valid and pairs with a non-empty input/. Free, always-on.
--plan           Print, per fixture, RUN (must dispatch) vs CACHED (fingerprint
                 matches a prior pass → reuse, no tokens). Free. This is how the
                 orchestrator dispatches only what changed (caching + diff-scoping).
--changed-agents Print the agents touched by the current git diff (their Agent.md,
                 a skill they @-reference, or their fixtures). Coarse diff-scoping.
default          Grade --actuals against the corpus. With --write-cache, record
                 each freshly-graded pair's fingerprint so the next run can skip it.

Caching / diff-scoping
----------------------
Each fixture is fingerprinted over (agent Agent.md + every skill it @-references
+ the fixture input + expected.json). An unchanged fingerprint that previously
passed is reused for free — so an untouched agent's whole suite costs 0 tokens,
and editing an agent re-runs exactly its affected fixtures.

Exit codes
----------
0  all graded pairs pass (or, with --baseline, no baseline-passing pair regressed)
1  a failure / regression / structural fault was detected
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def _load(path):
    with open(path) as f:
        return json.load(f)


def _in_range(n, rng):
    if rng is None:
        return True
    if "min" in rng and n < rng["min"]:
        return False
    if "max" in rng and n > rng["max"]:
        return False
    return True


def _mentions(haystack, needle):
    return needle.lower() in haystack.lower()


# The machine-first verdict contract every reviewer must satisfy.
# Strict two-state gate: any issue (any severity) => FAIL. severity carries the detail.
VALID_STATUS = {"PASS", "FAIL"}
VALID_SEVERITY = {"VIOLATION", "WARNING", "SUGGESTION"}


def _schema_faults(actual):
    """Contract violations in the agent's verdict — independent of expectations.

    A prose answer (no parseable JSON) arrives as None/{} → fails here, which is
    exactly how a non-machine-first agent gets caught."""
    if actual is None or "status" not in actual:
        return ["no machine-readable verdict (agent output did not parse as a "
                "JSON object with a 'status' field — is it machine-first?)"]
    faults = []
    if actual.get("status") not in VALID_STATUS:
        faults.append(f"status {actual.get('status')!r} not in {sorted(VALID_STATUS)}")
    issues = actual.get("issues")
    if not isinstance(issues, list):
        faults.append("'issues' is missing or not a list")
        return faults
    for idx, i in enumerate(issues):
        if not isinstance(i, dict):
            faults.append(f"issues[{idx}] is not an object")
            continue
        if i.get("severity") not in VALID_SEVERITY:
            faults.append(f"issues[{idx}].severity {i.get('severity')!r} invalid")
        if not str(i.get("message", "")).strip():
            faults.append(f"issues[{idx}] missing 'message'")
    return faults


def grade_agent(spec, actual):
    """Return a list of failure strings (empty = pass)."""
    fails = _schema_faults(actual)
    if fails:
        return fails

    exp_status = spec.get("expectedStatus")
    got_status = actual.get("status")
    if exp_status is not None and got_status != exp_status:
        fails.append(f"status: expected {exp_status!r}, got {got_status!r}")

    issues = actual.get("issues", []) or []
    count = len(issues)
    rng = spec.get("issueCount")
    if not _in_range(count, rng):
        fails.append(f"issueCount {count} outside expected range {rng}")

    for sev, sev_rng in (spec.get("severities") or {}).items():
        n = sum(1 for i in issues if i.get("severity") == sev)
        if not _in_range(n, sev_rng):
            fails.append(f"severities.{sev}: count {n} outside {sev_rng}")

    haystack = " ".join(
        str(i.get("message", "")) for i in issues
    ) + " " + str(actual.get("summary", ""))
    for needle in spec.get("mustMention", []):
        if not _mentions(haystack, needle):
            fails.append(f"mustMention: no issue mentioned {needle!r}")

    return fails


def _fixtures(evals_dir):
    fixtures_root = evals_dir / "fixtures"
    if not fixtures_root.is_dir():
        return []
    return sorted(p for p in fixtures_root.iterdir() if (p / "expected.json").is_file())


# ---- Fingerprint cache: caching + per-fixture diff-scoping ------------------

_SKILL_REF = re.compile(r"@([A-Za-z0-9_./-]+\.md)")


def _file_hash(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return "MISSING"


def _agent_inputs(agent, agents_dir, root):
    """The agent definition plus every file it @-references (its skills)."""
    agent_md = agents_dir / agent / "Agent.md"
    files = [agent_md]
    try:
        text = agent_md.read_text()
    except OSError:
        return files
    files.extend(root / ref for ref in _SKILL_REF.findall(text))
    return files


def fingerprint(fixture_dir, agent, agents_dir, root):
    """Hash everything that can change a fixture's verdict."""
    parts = []
    for f in _agent_inputs(agent, agents_dir, root):
        parts.append((f"agent:{f}", _file_hash(f)))
    input_dir = fixture_dir / "input"
    if input_dir.is_dir():
        for f in sorted(p for p in input_dir.rglob("*") if p.is_file()):
            parts.append((f"input:{f.relative_to(fixture_dir)}", _file_hash(f)))
    parts.append(("expected", _file_hash(fixture_dir / "expected.json")))
    blob = "\n".join(f"{k}={v}" for k, v in parts)
    return hashlib.sha256(blob.encode()).hexdigest()


def _cache_path(evals_dir):
    return evals_dir / ".eval-cache.json"


def _load_cache(evals_dir):
    p = _cache_path(evals_dir)
    try:
        return _load(p) if p.is_file() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(evals_dir, cache):
    _cache_path(evals_dir).write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")


def _is_cached_pass(cache, pair, fp):
    c = cache.get(pair)
    return bool(c and c.get("fingerprint") == fp and c.get("passed"))


def plan(evals_dir, agents_dir, root, only):
    cache = _load_cache(evals_dir)
    rows = []
    for fx in _fixtures(evals_dir):
        spec = _load(fx / "expected.json")
        for agent in spec.get("agents", {}):
            if only and agent not in only:
                continue
            pair = f"{fx.name}::{agent}"
            fp = fingerprint(fx, agent, agents_dir, root)
            rows.append(("CACHED" if _is_cached_pass(cache, pair, fp) else "RUN", pair))
    return rows


def changed_agents(root, agents_dir):
    """Agents touched by the working tree: their Agent.md, a skill they
    @-reference, or anything under evals/<agent>/. Coarse diff-scoping."""
    cmds = (["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--name-only", "--cached"],
            ["git", "ls-files", "--others", "--exclude-standard"])
    files = set()
    for cmd in cmds:
        try:
            out = subprocess.run(cmd, cwd=root, capture_output=True, text=True).stdout
        except OSError:
            continue
        files.update(l.strip() for l in out.splitlines() if l.strip())

    agents, changed_skills = set(), set()
    for f in files:
        parts = f.split("/")
        if len(parts) >= 3 and parts[0] == agents_dir.name \
                and (root / parts[0] / parts[1] / "Agent.md").is_file():
            agents.add(parts[1])
        if len(parts) >= 3 and parts[0] == "evals" \
                and (root / "evals" / parts[1] / "fixtures").is_dir():
            agents.add(parts[1])
        if f.startswith("skills/"):
            changed_skills.add(f)
    if changed_skills and agents_dir.is_dir():
        for adir in agents_dir.iterdir():
            md = adir / "Agent.md"
            if md.is_file() and any(
                (root / ref) == (root / s) or ref == s
                for ref in _SKILL_REF.findall(md.read_text(errors="ignore"))
                for s in changed_skills
            ):
                agents.add(adir.name)
    return agents


def check_corpus(evals_dir):
    faults = []
    fixtures = _fixtures(evals_dir)
    if not fixtures:
        faults.append(f"no fixtures with expected.json under {evals_dir}/fixtures")
    for fx in fixtures:
        stem = fx.name
        try:
            spec = _load(fx / "expected.json")
        except (OSError, json.JSONDecodeError) as e:
            faults.append(f"{stem}: invalid expected.json ({e})")
            continue
        for key in ("fixture", "applicableAgents", "agents"):
            if key not in spec:
                faults.append(f"{stem}: expected.json missing key {key!r}")
        input_dir = fx / "input"
        if not input_dir.is_dir() or not any(input_dir.iterdir()):
            faults.append(f"{stem}: missing or empty input/ directory")
    return faults


def run_grading(evals_dir, actuals, only, agents_dir, root, cache):
    """Grade each pair. A pair present in actuals is graded fresh; a pair absent
    from actuals passes iff its fingerprint matches a prior cached pass.

    Returns (pair, ok, detail, fingerprint, graded_fresh)."""
    results = []
    for fx in _fixtures(evals_dir):
        stem = fx.name
        spec = _load(fx / "expected.json")
        for agent, aspec in spec.get("agents", {}).items():
            if only and agent not in only:
                continue
            pair = f"{stem}::{agent}"
            fp = fingerprint(fx, agent, agents_dir, root)
            got = actuals.get(stem, {}).get("agents", {}).get(agent) if actuals else None
            if got is not None:
                fails = grade_agent(aspec, got)
                results.append((pair, not fails, "; ".join(fails), fp, True))
            elif _is_cached_pass(cache, pair, fp):
                results.append((pair, True, "cached (fingerprint match)", fp, False))
            else:
                results.append((pair, False,
                                "not run and no fresh cached pass — dispatch needed",
                                fp, False))
    return results


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--evals-dir", type=Path)
    ap.add_argument("--actuals", type=Path)
    ap.add_argument("--baseline", type=Path)
    ap.add_argument("--only", help="comma-separated agent names to grade")
    ap.add_argument("--agents-dir", type=Path, default=Path("agents"))
    ap.add_argument("--root", type=Path, default=Path("."),
                    help="repo root used to resolve @skills/... references")
    ap.add_argument("--check-corpus", action="store_true")
    ap.add_argument("--plan", action="store_true",
                    help="print RUN/CACHED per fixture (no model, no grading)")
    ap.add_argument("--write-cache", action="store_true",
                    help="after grading, record fingerprints of freshly-graded pairs")
    ap.add_argument("--changed-agents", action="store_true",
                    help="print agents touched by the current git diff")
    args = ap.parse_args(argv)

    if args.changed_agents:
        for a in sorted(changed_agents(args.root, args.agents_dir)):
            print(a)
        return 0

    if not args.evals_dir:
        print("error: --evals-dir is required", file=sys.stderr)
        return 2

    if args.check_corpus:
        faults = check_corpus(args.evals_dir)
        if faults:
            print("# Corpus check — FAIL\n")
            for f in faults:
                print(f"- {f}")
            return 1
        print(f"# Corpus check — OK ({len(_fixtures(args.evals_dir))} fixtures)")
        return 0

    only = {s.strip() for s in args.only.split(",")} if args.only else None

    if args.plan:
        rows = plan(args.evals_dir, args.agents_dir, args.root, only)
        runs = [p for a, p in rows if a == "RUN"]
        print(f"# Plan — {len(runs)}/{len(rows)} to RUN, {len(rows) - len(runs)} CACHED\n")
        for action, pair in rows:
            print(f"- {action:7} {pair}")
        return 0

    cache = _load_cache(args.evals_dir)
    actuals = _load(args.actuals) if args.actuals else {}
    baseline_pass = set(_load(args.baseline).get("passing", [])) if args.baseline else None

    results = run_grading(args.evals_dir, actuals, only, args.agents_dir, args.root, cache)
    passed = [r for r in results if r[1]]

    if args.write_cache:
        for pair, ok, _detail, fp, fresh in results:
            if fresh:
                cache[pair] = {"fingerprint": fp, "passed": ok}
        _save_cache(args.evals_dir, cache)

    print(f"# Eval grade — {len(passed)}/{len(results)} pairs passed\n")
    exit_code = 0
    for pair, ok, detail, _fp, fresh in results:
        if ok:
            tag = "PASS " if fresh else "CACHED"
            print(f"- {tag} {pair}")
        else:
            regressed = baseline_pass is not None and pair in baseline_pass
            tag = "REGRESSION" if regressed else "FAIL"
            print(f"- {tag}  {pair} — {detail}")
            # With a baseline, only regressions red-line the run.
            if baseline_pass is None or regressed:
                exit_code = 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
