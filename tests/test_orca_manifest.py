"""Manifesto do plugin da Orca (src/orca/orca-plugin.json): R20 e R35."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "src" / "orca" / "orca-plugin.json"


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_capabilities_e_engines(self):
        kinds = sorted(c["kind"] for c in self.m["capabilities"])
        self.assertEqual(
            kinds,
            sorted(["workspace:read", "agent:read", "workspace:write", "agent:launch", "storage:own"]),
        )
        self.assertEqual(self.m["engines"]["orca"], ">=1.4.248")
        self.assertEqual(self.m["id"], "starcode-ponte")
        self.assertNotIn("publisher", self.m)
        self.assertEqual(self.m["execution"], "trusted-worker")
        self.assertEqual(self.m["main"], "src/worker.ts")
        self.assertEqual(self.m["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        panels = {p["id"]: p for p in self.m["contributes"]["panels"]}
        self.assertEqual(panels["ponte"]["ui"], "components")
        events = sorted(e["on"] for e in self.m["contributes"]["events"])
        self.assertEqual(events, ["agent.status.changed", "workspace.changed"])

    def test_manifest_toggle_da_barra(self):
        commands = {c["id"]: c for c in self.m["contributes"]["commands"]}
        self.assertEqual(commands["starcode-ponte.toggle"]["action"], "sidebar.right.toggle")
        self.assertNotIn("action", commands["starcode-ponte.refresh"])
        items = {i["id"]: i for i in self.m["contributes"]["statusBarItems"]}
        self.assertEqual(items["ponte"]["command"], "starcode-ponte.toggle")


if __name__ == "__main__":
    unittest.main()
