"""Harness library for the eval suite.

The `Agent` port + adapters (`ClaudeCliAgent`, `FakeAgent`) — the seam that lets
orchestration be driven by the real model (CLI) for agent-quality evals, or by a
scripted fake for free, deterministic harness/orchestration tests.
"""
from .agent import Agent, RunResult, Call, FakeResponse, ClaudeCliAgent, FakeAgent

__all__ = [
    "Agent", "RunResult", "Call", "FakeResponse", "ClaudeCliAgent", "FakeAgent",
]
