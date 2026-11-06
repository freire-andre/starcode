import json
import os
import shutil
import subprocess
import unittest

from helpers import ROOT, TempRepoCase

PLUGIN = ROOT / "hooks" / "opencode" / "starcode.js"
NODE = shutil.which("node")

RUNNER = """
import { pathToFileURL } from "node:url"
const mod = await import(pathToFileURL(process.argv[2]).href)
const plugin = mod.default
let handler = null
await plugin.setup({ tool: { hook: async (name, fn) => { if (name === "execute.before") handler = fn } } })
let out = { registered: handler !== null, error: null }
try { await handler({ input: { command: process.argv[3] } }) } catch (e) { out.error = e.message }
console.log(JSON.stringify(out))
"""


@unittest.skipUnless(NODE, "node not on PATH")
class OpenCodePluginTest(TempRepoCase):
    def prepare(self) -> str:
        d = self.tmp / "plugin"
        d.mkdir()
        text = PLUGIN.read_text(encoding="utf-8").replace("{{STARCODE_ROOT}}", ROOT.as_posix())
        (d / "starcode.js").write_text(text, encoding="utf-8")
        (d / "package.json").write_text('{"type":"module"}', encoding="utf-8")
        (d / "runner.mjs").write_text(RUNNER, encoding="utf-8")
        return str(d)

    def run_plugin(self, command: str, env: dict | None = None):
        d = self.prepare()
        res = subprocess.run([NODE, os.path.join(d, "runner.mjs"), os.path.join(d, "starcode.js"), command],
                             capture_output=True, text=True, cwd=self.repo, env=env, stdin=subprocess.DEVNULL)
        self.assertEqual(res.returncode, 0, res.stderr)
        return json.loads(res.stdout.strip().splitlines()[-1]), res.stderr

    def test_opencode_plugin_in_dist_is_pure_object(self):
        dist = ROOT / "dist" / "opencode" / "plugins" / "starcode.js"
        self.assertTrue(dist.is_file())
        text = dist.read_text(encoding="utf-8")
        self.assertIn("export default", text)
        self.assertIn("execute.before", text)
        self.assertNotIn("@opencode", text)
        for line in text.splitlines():
            if line.startswith("import "):
                self.assertIn("node:", line)

    def test_opencode_plugin_throws_on_guard_deny(self):
        out, _ = self.run_plugin("git push --force origin main")
        self.assertTrue(out["registered"])
        self.assertIsNotNone(out["error"])
        self.assertTrue(out["error"].strip())

    def test_opencode_plugin_allows_normal_command(self):
        out, err = self.run_plugin("git status")
        self.assertIsNone(out["error"])
        self.assertNotIn("StarCode hook:", err)

    def test_opencode_plugin_fails_open_with_warning(self):
        env = {"PATH": str(self.tmp), "SystemRoot": os.environ.get("SystemRoot", "")}
        out, err = self.run_plugin("git push --force origin main", env=env)
        self.assertIsNone(out["error"])
        self.assertIn("StarCode hook:", err)


if __name__ == "__main__":
    unittest.main()
