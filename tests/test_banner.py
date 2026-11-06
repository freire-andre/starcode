"""Banner lines for the execution phase: open breaker and degraded verification (R30, R36)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import TempRepoCase

import banner
import handoff


class BannerExecutionTests(TempRepoCase):
    def build(self):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            return banner.build_banner(str(self.repo), False)

    def feature(self, slug: str = "task-priority"):
        self.write_repo_config()
        feat = self.repo / ".specs" / "features" / slug
        feat.mkdir(parents=True)
        (feat / "tasks.md").write_text("# Tasks\n", encoding="utf-8")
        return feat

    def test_banner_shows_open_breaker(self):
        self.feature()
        for _ in range(3):
            handoff.set_handoff("task-priority", self.repo, {"phase": "execute"}, attempt="worker-T2=fail")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Disjuntor aberto: task-priority (worker-T2)\n", "\n" + text + "\n")
        self.assertIn("disjuntor aberto", line)

    def test_banner_shows_degraded_verification(self):
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text("# v\n\n**Verification:** self-verified\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Verificação: degradada (task-priority)\n", "\n" + text + "\n")
        self.assertIn("verificação degradada", line)

    def test_banner_shows_degraded_verification_marker(self):
        # C14/R30: the `**Verification:** degraded (<reason>)` marker counts as much as `self-verified`.
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text(
            "# v\n\n**Verification:** degraded (Q na mesma família: claude)\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertIn("\n⚠️ Verificação: degradada (task-priority)\n", "\n" + text + "\n")
        self.assertIn("verificação degradada", line)

    def test_no_breaker_line_when_closed(self):
        self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "execute"}, attempt="worker-T2=fail")
        text, _, _ = self.build()
        self.assertNotIn("Disjuntor aberto", text)

    def test_markers_in_prose_before_handoff_are_ignored(self):
        # tasks.md prose may quote `## Handoff`, `**Phase:**` and `**Breaker:** open (<id>)`;
        # only the real `## Handoff` heading section counts.
        feat = self.feature()
        (feat / "tasks.md").write_text(
            "# Tasks\n\nNunca altere a seção `## Handoff`; o banner lê `**Phase:**` e "
            "`**Breaker:** open (<id>)`.\n", encoding="utf-8")
        handoff.set_handoff("task-priority", self.repo, {"phase": "execute"})
        text, _, _ = self.build()
        self.assertIn("task-priority (fase: execute)", text)
        self.assertNotIn("Disjuntor aberto", text)


class BannerDegradedMarkerTests(BannerExecutionTests):
    def test_degraded_only_from_marker_line(self):
        # C8/R5: a table row that merely mentions `self-verified` is not the marker.
        feat = self.feature()
        handoff.set_handoff("task-priority", self.repo, {"phase": "review"})
        (feat / "verification.md").write_text(
            "# v\n\n**Verification:** independent\n\n| C1 | self-verified? | no |\n"
            "Texto com **Verification:** degraded no meio da linha.\n", encoding="utf-8")
        text, line, _ = self.build()
        self.assertNotIn("Verificação: degradada", text)
        self.assertNotIn("verificação degradada", line)


class BannerCliTests(TempRepoCase):
    def build(self, cli, plugin_root):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]), \
             mock.patch.object(banner.sc, "PLUGIN_ROOT", plugin_root):
            return banner.build_banner(str(self.repo), False, cli)[0]

    def plugin(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def lines(self, text):
        return text.split("\n")

    def test_banner_lists_unavailable_extras(self):
        root = self.plugin()
        (root / "capabilities.json").write_text(json.dumps({"schemaVersion": 1, "cli": "codex", "extras": {
            "hooks": {"status": "unavailable", "fallback": "Fase 5"},
            "orca_worker": {"status": "ok"}}}), encoding="utf-8")
        lines = self.lines(self.build("codex", root))
        self.assertIn("CLI: codex", lines)
        self.assertIn("Indisponível neste CLI: hooks → Fase 5", lines)
        self.assertFalse(any("orca_worker" in l for l in lines))

    def test_banner_without_cli_keeps_phase3_output(self):
        text = self.build(None, self.plugin())
        self.assertNotIn("CLI:", text)
        self.assertNotIn("Indisponível", text)

    def test_falls_back_to_source_yaml(self):
        # C7/R4: no capabilities.json beside the plugin -> src/capabilities.yaml (that CLI's section).
        real = Path(__file__).resolve().parent.parent
        root = self.plugin()
        (root / "src").mkdir()
        shutil.copy(real / "src" / "capabilities.yaml", root / "src" / "capabilities.yaml")
        (root / "tools").mkdir()
        shutil.copy(real / "tools" / "miniyaml.py", root / "tools" / "miniyaml.py")
        lines = self.lines(self.build("codex", root))
        self.assertIn("Indisponível neste CLI: linear_mcp → issue-mãe pelo orca linear", lines)
        self.assertFalse(any("orca_worker" in l for l in lines))

    def test_claude_lists_nothing_unavailable(self):
        root = self.plugin()
        (root / "capabilities.json").write_text(json.dumps({"schemaVersion": 1, "cli": "claude", "extras": {
            "hooks": {"status": "ok"}}}), encoding="utf-8")
        text = self.build("claude", root)
        self.assertIn("CLI: claude", self.lines(text))
        self.assertNotIn("Indisponível", text)


WARN = "Hooks do Codex sem trust: aprove em /hooks"
KEY = "starcode@starcode:hooks/hooks.json:session_start:0:0"


class BannerCodexTrustTests(TempRepoCase):
    build = BannerCliTests.build
    plugin = BannerCliTests.plugin
    lines = BannerCliTests.lines

    def codex_cfg(self, text):
        home = Path(os.environ["STARCODE_HOME"])
        (home / ".codex").mkdir(parents=True, exist_ok=True)
        (home / ".codex" / "config.toml").write_text(text, encoding="utf-8")

    def banner_lines(self):
        return self.lines(self.build("codex", self.plugin()))

    def test_codex_banner_warns_hooks_without_trust(self):  # C15
        # arquivo ausente
        self.assertIn(WARN, self.banner_lines())
        # só de outro plugin
        self.codex_cfg('[hooks.state."impeccable@impeccable:hooks/hooks.json:session_start:0:0"]\n'
                       'trusted_hash = "sha256:abc"\n')
        self.assertIn(WARN, self.banner_lines())
        # chave do starcode sem trusted_hash
        self.codex_cfg(f'[hooks.state."{KEY}"]\nenabled = true\n')
        self.assertIn(WARN, self.banner_lines())
        # com trust, mas uma chave desabilitada
        self.codex_cfg(f'[hooks.state."{KEY}"]\ntrusted_hash = "sha256:a"\n'
                       '[hooks.state."starcode@starcode:hooks/hooks.json:pre_tool_use:0:0"]\n'
                       'trusted_hash = "sha256:b"\nenabled = false\n')
        self.assertIn(WARN, self.banner_lines())
        # TOML inválido não quebra o banner
        self.codex_cfg("[[[ nao e toml")
        self.assertIn(WARN, self.banner_lines())
        # com trust: sem aviso
        self.codex_cfg(f'[hooks.state."{KEY}"]\ntrusted_hash = "sha256:a"\n')
        self.assertNotIn(WARN, self.banner_lines())
        # outros CLIs nunca avisam
        self.assertNotIn(WARN, self.lines(self.build("claude", self.plugin())))

    def test_banner_hook_mode_matches_text_per_cli(self):  # C16
        script = Path(banner.__file__)

        def run(*args):
            res = subprocess.run([sys.executable, str(script), "--cwd", str(self.repo), *args],
                                 input="{}", capture_output=True, text=True, encoding="utf-8", timeout=60)
            self.assertEqual(res.returncode, 0, res.stderr)
            return res.stdout.rstrip("\r\n")

        text = run("--cli", "codex", "--text")
        self.assertIn(WARN, text.splitlines())
        hook = json.loads(run("--cli", "codex"))
        self.assertEqual(hook["hookSpecificOutput"]["additionalContext"], text)
        agy_text = run("--cli", "antigravity", "--text")
        agy = json.loads(run("--cli", "antigravity", "--agy"))
        self.assertEqual(agy["injectSteps"][0]["ephemeralMessage"], agy_text)


if __name__ == "__main__":
    unittest.main()


class BannerCommandFormatTests(TempRepoCase):  # R19
    EXPECTED_SETUP = {
        None: "/starcode:setup",
        "claude": "/starcode:setup",
        "opencode": "/sc-setup",
        "codex": "a skill `setup` do StarCode",
        "antigravity": "a skill `setup` do StarCode",
    }

    def text(self, cli, full):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner, "check_linear", return_value=[]), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            return banner.build_banner(str(self.repo), full, cli)[0]

    def test_banner_setup_command_per_cli(self):
        for cli, expected in self.EXPECTED_SETUP.items():
            for full in (False, True):  # sem StarCode no repositório / config de repositório ausente
                with self.subTest(cli=cli, full=full):
                    text = self.text(cli, full)
                    self.assertIn(expected, text)
                    if cli not in (None, "claude"):
                        self.assertNotIn("/starcode:", text)
                    if cli == "codex" or cli == "antigravity":
                        self.assertNotIn("/sc-", text)

    def test_banner_engajar_command_matches_cmd_ref(self):
        import build
        for cli in ("claude", "opencode", "codex", "antigravity"):
            with self.subTest(cli=cli):
                self.assertEqual(banner.cmd_ref(cli, "engajar"), build.cmd_ref(cli, "engajar"))
                self.assertEqual(banner.cmd_ref(cli, "setup"), build.cmd_ref(cli, "setup"))
                self.assertIn(build.cmd_ref(cli, "engajar"), self.text(cli, False))
        self.assertEqual(banner.cmd_ref(None, "engajar"), build.cmd_ref("claude", "engajar"))

    def test_banner_linear_missing_states_uses_cli_format(self):
        cfg = {"linear": {"team": "SC", "workspace": "w", "states": {"a": "X"}}}
        outs = [(0, "{}"), (0, json.dumps({"states": []}))]
        with mock.patch.object(banner, "_run", side_effect=outs):
            lines = banner.check_linear(cfg, "opencode")
        self.assertTrue(any("/sc-setup" in l for l in lines))
