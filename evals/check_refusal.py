#!/usr/bin/env python3
"""Grader for a command's REFUSAL guard (e.g. /run-pipeline with no approved spec).

The command should STOP at its precondition: write no code and report why — never
dispatch a worker. We assert the negative (nothing was produced) plus a tolerant
substring in the command's output. `grade(spec, scratch_dir, output)` is the pure
entrypoint the engine calls (the engine captures the command's stdout as `output`).

Checks (spec keys):
  mustNotWrite : [str] — none of these paths may exist in the scratch afterwards
                 (e.g. "src/main", "src/test" — proof it wrote no code)
  mustMention  : [str] — each substring (case-insensitive) appears in the output
"""
import os


def grade(spec, scratch_dir, output):
    fails = []
    low = (output or "").lower()

    for path in spec.get("mustNotWrite", []):
        full = os.path.join(scratch_dir, path)
        if os.path.exists(full) and (not os.path.isdir(full) or os.listdir(full)):
            fails.append(f"mustNotWrite: {path!r} exists — the guard did not stop "
                         f"before producing output")

    for needle in spec.get("mustMention", []):
        if needle.lower() not in low:
            fails.append(f"mustMention: {needle!r} not found in the command output")

    return fails
