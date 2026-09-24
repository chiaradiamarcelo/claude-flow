"""Harness self-test: live evals dispatch against this checkout, loaded as the plugin
($0, no model).

A plugin's components are namespaced and coexist with personal ones of the same bare
name, so a dispatch that names `test-reviewer` bare can grade a personal copy instead
of the edit under test — and pass. These pin the naming, and the one layout rule whose
breakage is otherwise silent: the plugin loader reads flat `agents/<name>.md` files, and
an agent in a subdirectory simply never loads.
"""
import json
import unittest

from . import _bootstrap  # noqa: F401
from plugin_under_test import ROOT, plugin_args, qualified, unqualified


class PluginUnderTestTest(unittest.TestCase):

    def test_qualifies_a_bare_agent_name(self):
        self.assertEqual("claude-flow:test-reviewer", qualified("test-reviewer"))

    def test_keeps_an_already_qualified_name(self):
        self.assertEqual("claude-flow:architect", qualified("claude-flow:architect"))

    def test_strips_the_plugin_prefix(self):
        self.assertEqual("testing", unqualified("claude-flow:testing"))

    def test_keeps_a_name_from_another_plugin(self):
        self.assertEqual("other:testing", unqualified("other:testing"))

    def test_loads_the_checkout_that_holds_the_manifest(self):
        manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())

        self.assertEqual(["--plugin-dir", str(ROOT)], plugin_args())
        self.assertEqual("claude-flow", manifest["name"])


class PluginLayoutTest(unittest.TestCase):

    def test_every_agent_ships_as_a_flat_md_file(self):
        nested = sorted(p.name for p in (ROOT / "agents").iterdir() if p.is_dir())

        self.assertEqual([], nested)


if __name__ == "__main__":
    unittest.main()
