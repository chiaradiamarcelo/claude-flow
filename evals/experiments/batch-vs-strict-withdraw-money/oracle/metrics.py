#!/usr/bin/env python3
"""Developer-phase metrics from a `claude -p --output-format stream-json` transcript.

Reads a JSONL transcript and emits the cost/effort axes the experiment compares:
output tokens (the real cost), total cost USD, turns, API duration, and the number of
`./gradlew` invocations (the batch hypothesis predicts far fewer for the batch arm).

Usage: metrics.py <transcript.jsonl> [--wall <seconds>] [--json]
"""
import sys, json


def parse(path):
    result = None
    gradle_runs = 0
    bash_calls = 0
    tool_calls = {}
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
            msg = ev.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        name = block.get("name", "?")
                        tool_calls[name] = tool_calls.get(name, 0) + 1
                        if name == "Bash":
                            bash_calls += 1
                            cmd = (block.get("input") or {}).get("command", "")
                            if "gradlew" in cmd or "gradle " in cmd:
                                gradle_runs += 1
    usage = (result or {}).get("usage", {}) or {}
    return {
        "output_tokens": usage.get("output_tokens"),
        "input_tokens": usage.get("input_tokens"),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens"),
        "total_cost_usd": (result or {}).get("total_cost_usd"),
        "num_turns": (result or {}).get("num_turns"),
        "duration_ms": (result or {}).get("duration_ms"),
        "duration_api_ms": (result or {}).get("duration_api_ms"),
        "is_error": (result or {}).get("is_error"),
        "gradle_runs": gradle_runs,
        "bash_calls": bash_calls,
        "tool_calls": tool_calls,
    }


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    m = parse(args[0])
    for i, a in enumerate(argv):
        if a == "--wall" and i + 1 < len(argv):
            m["wall_seconds"] = float(argv[i + 1])
    if "--json" in argv:
        print(json.dumps(m, indent=2)); return 0
    print(f"output_tokens : {m['output_tokens']}")
    print(f"cost_usd      : {m['total_cost_usd']}")
    print(f"num_turns     : {m['num_turns']}")
    print(f"gradle_runs   : {m['gradle_runs']}")
    print(f"bash_calls    : {m['bash_calls']}")
    print(f"duration_api_s: {round((m['duration_api_ms'] or 0)/1000, 1)}")
    if "wall_seconds" in m:
        print(f"wall_seconds  : {m['wall_seconds']}")
    print(f"tool_calls    : {m['tool_calls']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
