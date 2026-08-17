#!/usr/bin/env python3
"""Reduce one `claude -p --output-format stream-json` run to a gradeable verdict.

Reads the event stream on stdin and writes a single JSON object on stdout: the
agent's own machine-first verdict, plus `_skillsInvoked` — the skills it actually
loaded with the Skill tool.

That second field is the point. `mustMention` greps the agent's prose, so it passes
whether or not the skill its rules live in ever loaded; every reviewer's Agent.md
restates enough of its skill to satisfy it. The tool calls are the ground truth.

A run that produced no parseable verdict yields `{"_skillsInvoked": [...]}`, which
fails the schema check in eval_grade — the same way a prose answer already did.
"""
import json
import re
import sys


def _events(stream):
    for line in stream:
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _tool_uses(event):
    message = event.get("message")
    if not isinstance(message, dict):
        return
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            yield block


def reduce_stream(stream):
    skills, texts = [], []
    for event in _events(stream):
        for block in _tool_uses(event):
            if block.get("name") != "Skill":
                continue
            skill = (block.get("input") or {}).get("skill")
            if skill and skill not in skills:
                skills.append(skill)
        if event.get("type") == "result" and event.get("result"):
            texts.append(str(event["result"]))

    verdict = _first_json_object(texts)
    verdict["_skillsInvoked"] = skills
    return verdict


def _first_json_object(texts):
    """The agent is told to answer with one JSON object; take the outermost."""
    for text in texts:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            continue
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


if __name__ == "__main__":
    json.dump(reduce_stream(sys.stdin), sys.stdout)
    print()
