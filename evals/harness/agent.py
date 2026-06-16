#!/usr/bin/env python3
"""The Agent port and its adapters.

Ports-and-adapters (the same shape the pipeline's own `clean-architecture` skill
enforces), applied to "run an agent against a workspace":

    Agent                ← port (the contract orchestration depends on)
      ClaudeCliAgent     ← adapter: shells out to `claude -p` (real model)
      FakeAgent          ← adapter: replays scripted output + file-effects (tests)

Why the port exists: today the dispatch (`claude -p …`) is hardcoded inline in
several places, so orchestration is welded to the real model and can't be tested
without spending tokens. Depending on this port instead lets a test inject a
`FakeAgent` and exercise the orchestrate→capture→parse→loop path for $0,
deterministically — while real agent-quality evals inject `ClaudeCliAgent`.

`FakeAgent` tests the *harness/orchestration* (our glue), NOT the model's
judgement — faking a reviewer's verdict to check the reviewer would be a
tautology. It is for control flow: routing, the fix-loop, chaining, parsing.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Sequence


@dataclass
class RunResult:
    """What an agent run produced. The side-effect protocol every adapter honors:
    stdout (where a machine-first verdict is read from), an exit code, and the
    workspace it ran in (where file-effects — written code, plan, JUnit XML —
    land for an inspector to examine)."""
    stdout: str = ""
    exit_code: int = 0
    workspace: Optional[Path] = None


@dataclass
class Call:
    """A recorded dispatch — lets a test assert *what* was dispatched and in what
    order (e.g. architect before developer; the fix dispatch carried the findings)."""
    prompt: str
    agent_name: Optional[str] = None
    tools: tuple = ()


class Agent:
    """The port. Orchestration depends on this, never on `claude -p` directly."""

    def run(self, workspace, prompt: str, agent_name: Optional[str] = None,
            tools: Sequence[str] = ()) -> RunResult:
        raise NotImplementedError


class ClaudeCliAgent(Agent):
    """Real adapter: dispatch via the Claude CLI in headless mode. This is the
    production path — what every paid, agent-quality eval injects."""

    def __init__(self, claude_bin: str = "claude"):
        self.claude_bin = claude_bin

    def run(self, workspace, prompt, agent_name=None, tools=()):
        cmd = [self.claude_bin, "-p", prompt]
        if agent_name:
            cmd += ["--agent", agent_name]
        if tools:
            cmd += ["--allowedTools", *tools]
        proc = subprocess.run(
            cmd, cwd=str(workspace), capture_output=True, text=True,
            stdin=subprocess.DEVNULL,
        )
        return RunResult(stdout=proc.stdout, exit_code=proc.returncode,
                         workspace=Path(workspace))


@dataclass
class FakeResponse:
    """One scripted reply. `stdout` is returned verbatim; `writes` (relpath →
    content) are applied to the workspace as the run's file-effects (e.g. a canned
    JUnit XML, a plan file, generated code). Sequence these to script a whole
    orchestration: round 1 returns FAIL findings, round 2 returns a clean verdict."""
    stdout: str = ""
    exit_code: int = 0
    writes: dict = field(default_factory=dict)


class FakeAgent(Agent):
    """Test adapter: replays a script of `FakeResponse`s and records every call.

    Honors the same `RunResult` contract as `ClaudeCliAgent` but touches no model
    — so a test can drive the real orchestration deterministically and for free,
    then assert on `.calls` (order/prompts) and the workspace (file-effects)."""

    def __init__(self, script: Optional[Sequence[FakeResponse]] = None,
                 *, default: Optional[Callable[[Call], FakeResponse]] = None):
        self._script = list(script or [])
        self._default = default
        self.calls: list[Call] = []

    def run(self, workspace, prompt, agent_name=None, tools=()):
        call = Call(prompt=prompt, agent_name=agent_name, tools=tuple(tools))
        self.calls.append(call)

        if self._script:
            resp = self._script.pop(0)
        elif self._default is not None:
            resp = self._default(call)
        else:
            raise AssertionError(
                f"FakeAgent: no scripted response for call #{len(self.calls)} "
                f"(agent_name={agent_name!r}). Script more responses or pass a default."
            )

        ws = Path(workspace)
        for rel, content in (resp.writes or {}).items():
            p = ws / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        return RunResult(stdout=resp.stdout, exit_code=resp.exit_code, workspace=ws)
