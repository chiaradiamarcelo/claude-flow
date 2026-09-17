#!/usr/bin/env python3
"""Pipeline metrics from a `claude -p --output-format stream-json` transcript.

Supersedes metrics.py for experiments where one arm dispatches subagents.

The spike (2026-09-17) established that in a subagent-dispatching run:
  - `result.usage` counts the MAIN LOOP ONLY. A multi-agent arm scored from it
    undercounts by roughly the subagents' share -- in a toy 3-echo dispatch,
    main-loop-only cost was $0.11 against a reported total of $0.21.
  - `result.total_cost_usd` DOES roll subagents up, so it is valid as-is.
  - every subagent assistant event carries `parent_tool_use_id`, so usage and
    tool calls can be both summed and attributed.

So tokens are summed over ALL assistant events and split by origin; cost is
taken from the result event.

KNOWN LIMITATION -- per-event `output_tokens` is under-reported. In the spike the
main loop summed to 18 output tokens against the result event's 204, because
streaming assistant events carry partial usage. `tool_use` BLOCKS, by contrast,
are complete (the 3 dispatched echoes were all present and correctly attributed).
Therefore:
  - PRIMARY cost axis        -> `total_cost_usd` (complete, rolls subagents up)
  - PRIMARY mechanism axes   -> `gradle_runs_total`, tool-call counts (complete)
  - token counts             -> ATTRIBUTION ONLY; compare orchestrator/subagent
                                SHARE, never treat the absolute totals as spend.

Usage: metrics2.py <transcript.jsonl> [--wall <seconds>] [--json]
"""
import sys, json
from collections import Counter, defaultdict


def _usage_of(ev):
    return ((ev.get("message") or {}).get("usage")) or {}


def parse(path):
    result = None
    # per-origin accumulators: "orchestrator" or the parent tool_use id
    tokens = defaultdict(Counter)
    tool_calls = defaultdict(Counter)
    gradle_runs = Counter()
    assistant_events = Counter()
    subagent_types = Counter()

    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue

            if ev.get("type") == "result":
                result = ev

            parent = ev.get("parent_tool_use_id")
            origin = "orchestrator" if parent is None else "subagent"

            if ev.get("type") == "assistant":
                assistant_events[origin] += 1
                u = _usage_of(ev)
                for k in ("input_tokens", "output_tokens",
                          "cache_read_input_tokens", "cache_creation_input_tokens"):
                    tokens[origin][k] += u.get(k) or 0

            msg = ev.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                for block in content:
                    if not (isinstance(block, dict) and block.get("type") == "tool_use"):
                        continue
                    name = block.get("name", "?")
                    inp = block.get("input") or {}
                    tool_calls[origin][name] += 1
                    if name in ("Agent", "Task"):
                        subagent_types[inp.get("subagent_type") or "?"] += 1
                    if name == "Bash":
                        cmd = inp.get("command", "")
                        if "gradlew" in cmd or "gradle " in cmd:
                            gradle_runs[origin] += 1

    totals = Counter()
    for c in tokens.values():
        totals.update(c)

    return {
        # --- headline, valid across both arms ---
        "total_cost_usd": (result or {}).get("total_cost_usd"),
        "output_tokens_total": totals["output_tokens"],
        "input_tokens_total": totals["input_tokens"],
        "cache_read_total": totals["cache_read_input_tokens"],
        "cache_creation_total": totals["cache_creation_input_tokens"],
        "gradle_runs_total": sum(gradle_runs.values()),
        "assistant_events_total": sum(assistant_events.values()),
        # --- attribution ---
        "by_origin": {
            o: {
                "output_tokens": tokens[o]["output_tokens"],
                "cache_read": tokens[o]["cache_read_input_tokens"],
                "cache_creation": tokens[o]["cache_creation_input_tokens"],
                "assistant_events": assistant_events[o],
                "gradle_runs": gradle_runs[o],
                "tool_calls": dict(tool_calls[o]),
            }
            for o in sorted(set(list(tokens) + list(tool_calls)))
        },
        "subagents_dispatched": dict(subagent_types),
        # --- main-loop-only figures, kept for comparison with the old metrics.py ---
        "mainloop_only_usage": (result or {}).get("usage", {}),
        "num_turns_mainloop": (result or {}).get("num_turns"),
        "duration_ms": (result or {}).get("duration_ms"),
        "duration_api_ms": (result or {}).get("duration_api_ms"),
        "is_error": (result or {}).get("is_error"),
    }


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    m = parse(args[0])
    if "--wall" in argv:
        m["wall_seconds"] = float(argv[argv.index("--wall") + 1])
    print(json.dumps(m, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
