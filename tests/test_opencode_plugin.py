import json
import os
import shutil
import subprocess
import unittest

from helpers import ROOT, TempRepoCase, run_git

PLUGIN = ROOT / "hooks" / "opencode" / "starcode.js"
NODE = shutil.which("node")

RUNNER = """
import { pathToFileURL } from "node:url"
const mod = await import(pathToFileURL(process.argv[2]).href)
const plugin = mod.default
let handler = null
await plugin.setup({ tool: { hook: async (name, fn) => { if (name === "execute.before") handler = fn } } })
let out = { registered: handler !== null, error: null }
const input = { command: process.argv[3] }
if (process.argv[4]) input.workdir = process.argv[4]
try { await handler({ input }) } catch (e) { out.error = e.message }
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

    def run_plugin(self, command: str, env: dict | None = None, workdir: str | None = None, cwd=None):
        d = self.prepare()
        res = subprocess.run([NODE, os.path.join(d, "runner.mjs"), os.path.join(d, "starcode.js"), command, *([workdir] if workdir else [])],
                             capture_output=True, text=True, encoding="utf-8", cwd=cwd or self.repo, env=env, stdin=subprocess.DEVNULL)
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
        self.assertIn("push` for\u00e7ado", out["error"])  # motivo concreto do git_guard

    def test_opencode_plugin_allows_normal_command(self):
        out, err = self.run_plugin("git status")
        self.assertIsNone(out["error"])
        self.assertNotIn("StarCode hook:", err)

    def test_opencode_plugin_uses_event_workdir(self):
        secret = "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
        (self.repo / "cfg.py").write_text(f"TOKEN = '{secret}'\n", encoding="utf-8")
        run_git(self.repo, "add", "cfg.py")
        outside = self.tmp / "outside"
        outside.mkdir()
        out, _ = self.run_plugin("git commit -m x", workdir=str(self.repo), cwd=outside)
        self.assertIsNotNone(out["error"])
        self.assertIn("cfg.py", out["error"])

    def test_opencode_plugin_fails_open_with_warning(self):
        env = {"PATH": str(self.tmp), "SystemRoot": os.environ.get("SystemRoot", "")}
        out, err = self.run_plugin("git push --force origin main", env=env)
        self.assertIsNone(out["error"])
        self.assertIn("StarCode hook:", err)


if __name__ == "__main__":
    unittest.main()
