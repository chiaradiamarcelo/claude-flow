#!/usr/bin/env python3
"""The pipeline orchestration — as an injectable function.

This is the chain that used to live inline in run_all.sh Phase 1d
(architect → developer → build → reviewers → fix-loop), lifted out of bash so it
depends on the **Agent port** and an injected **build** callable. That makes it:

  - the single source of truth for the orchestration (no bash/python duplicate), and
  - testable for $0 — inject a FakeAgent + a fake builder and the whole
    orchestrate→review→loop control flow runs deterministically, no model.

run_pipeline ORCHESTRATES; it does not grade. Grading stays in check_acceptance
(reading the .reviews/ files this writes + the build's JUnit XML). The fix-loop
gates on VIOLATIONs (must-fix); WARNING/SUGGESTION are advisory.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # evals/
from _review_findings import _issues, FIX_SEVERITIES  # noqa: E402

# Glob routing, mirroring the reviewer triggers: tests -> test-reviewer;
# main -> arch-reviewer + refactor-advisor (no api/ui code in the core slice).
ROUTES = (("test-reviewer", "src/test"),
          ("arch-reviewer", "src/main"),
          ("refactor-advisor", "src/main"))

REVIEW_PROMPT = ("Review the Kotlin source file(s) under {dir}/ (read them directly "
                 "with the Read tool). Return ONLY your machine-first JSON verdict.")

_JSON = re.compile(r"\{.*\}", re.S)


def extract_verdict(stdout: str) -> dict:
    """Pull the machine-first JSON verdict out of an agent's stdout (same as the
    bash one-liner did). Returns {} if nothing parseable — which the schema check
    in the grader then catches."""
    m = _JSON.search(stdout or "")
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def count_violations(reviews: dict) -> int:
    return sum(1 for v in reviews.values() if v
               for i in (v.get("issues") or []) if i.get("severity") == "VIOLATION")


def format_findings(reviews_dir) -> str:
    """The fix-mode '## Review Findings' block (VIOLATION + WARNING only — feeding
    back endless SUGGESTIONs would never converge)."""
    issues = [(r, i) for r, i in _issues(reviews_dir) if i.get("severity") in FIX_SEVERITIES]
    if not issues:
        return ""
    lines = ["## Review Findings", ""]
    for reviewer, i in issues:
        lines.append(f"- {i.get('file')}:{i.get('line')} [{i.get('severity')}] "
                     f"({reviewer}) {i.get('message', '')}")
    return "\n".join(lines)


def run_reviews(agent, workspace, *, routes=ROUTES, tools=()) -> dict:
    """Dispatch each routed reviewer through the Agent port, persist its verdict to
    .reviews/<reviewer>.json (for the grader + debugging), and return {reviewer: verdict}."""
    ws = Path(workspace)
    reviews_dir = ws / ".reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    for old in reviews_dir.glob("*.json"):
        old.unlink()
    reviews = {}
    for reviewer, d in routes:
        res = agent.run(ws, REVIEW_PROMPT.format(dir=d), agent_name=reviewer, tools=tools)
        verdict = extract_verdict(res.stdout)
        (reviews_dir / f"{reviewer}.json").write_text(json.dumps(verdict))
        reviews[reviewer] = verdict
    return reviews


@dataclass
class Outcome:
    build_exit: int
    reviews: dict
    rounds: int          # fix-loop rounds actually run


def run_pipeline(agent, workspace, cfg: dict, build: Callable[[Path], int], *,
                 arch_tools: Sequence[str] = (), dev_tools: Sequence[str] = (),
                 rev_tools: Sequence[str] = (), intent_tools: Sequence[str] = ()) -> Outcome:
    """Run the full chain through the injected agent + builder. Pure orchestration.

    cfg keys (from a pipeline fixture's expected.json): intentPrompt?,
    architectPrompt?, developerPrompt, developerFixPrompt?, and
    agents.pipeline.maxFixRounds."""
    ws = Path(workspace)
    pipe = cfg.get("agents", {}).get("pipeline", {})

    if cfg.get("intentPrompt"):
        agent.run(ws, cfg["intentPrompt"], tools=intent_tools)          # command: no --agent
    if cfg.get("architectPrompt"):
        agent.run(ws, cfg["architectPrompt"], agent_name="architect", tools=arch_tools)
    agent.run(ws, cfg["developerPrompt"], agent_name="developer", tools=dev_tools)

    build_exit = build(ws)
    reviews = run_reviews(agent, ws, tools=rev_tools)

    rounds = 0
    K = int(pipe.get("maxFixRounds", 0))
    fix_prompt = cfg.get("developerFixPrompt")
    while count_violations(reviews) > 0 and rounds < K and fix_prompt:
        rounds += 1
        findings = format_findings(ws / ".reviews")
        agent.run(ws, f"{fix_prompt}\n\n{findings}", agent_name="developer", tools=dev_tools)
        build_exit = build(ws)
        reviews = run_reviews(agent, ws, tools=rev_tools)

    return Outcome(build_exit=build_exit, reviews=reviews, rounds=rounds)
