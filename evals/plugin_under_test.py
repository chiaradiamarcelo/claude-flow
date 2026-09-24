"""The plugin every live eval dispatches against: THIS checkout, not an installed copy.

`claude -p --plugin-dir <root>` loads the working tree as the `claude-flow` plugin for
that one session, so an eval grades the edit under test rather than whatever version
happens to be installed. Its agents, skills and commands are then namespaced, and a
bare name may reach a personal agent of the same name instead — so every dispatch
names them in full.
"""
from pathlib import Path

PLUGIN = "claude-flow"
ROOT = Path(__file__).resolve().parents[1]


def plugin_args():
    return ["--plugin-dir", str(ROOT)]


def qualified(agent):
    """`test-reviewer` -> `claude-flow:test-reviewer`; an already-qualified name is kept."""
    return agent if ":" in agent else f"{PLUGIN}:{agent}"


def unqualified(name):
    """`claude-flow:testing` -> `testing`. Fixtures name components bare."""
    prefix = f"{PLUGIN}:"
    return name[len(prefix):] if name.startswith(prefix) else name
