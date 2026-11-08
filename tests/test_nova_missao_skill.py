"""Content tests for the Kirk skill nova-missao (R33-R35, R43, R44)."""
from __future__ import annotations

import unittest
from pathlib import Path

from helpers import ROOT

CLIS = ("claude", "codex", "antigravity", "opencode")


def _roots() -> list[Path]:
    return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]


def _read(root: Path, rel: str = "skills/nova-missao/SKILL.md") -> str:
    return (root / rel).read_text(encoding="utf-8")


class NovaMissaoSkillTests(unittest.TestCase):
    def test_nova_missao_skill_order(self):
        # R33: perguntas -> versions -> Context7 -> new -> gates -> commit -> relatório
        for root in _roots():
            text = _read(root)
            self.assertRegex(text, r"\A---\r?\nname: nova-missao\r?\n", root)
            if root != ROOT:
                self.assertNotIn("{{", text)
            steps = ["experimental: API 0.x muda entre versões", "scaffold.py\" versions",
                     "stack_cache.py\" write", "scaffold.py\" new", "scaffold.py\" gates",
                     "git -C <parent>/<name> init", "chore: projeto inicial (", "## 7. Report"]
            pos = [text.find(s) for s in steps]
            self.assertNotIn(-1, pos, f"{root}: {[s for s, p in zip(steps, pos) if p < 0]}")
            self.assertEqual(pos, sorted(pos), root)
            self.assertIn("--description", text)
            for needle in ("one message", "Name", "Parent folder", "App profile", "Optional database",
                           "One sentence", "recommend", "Uhura", "main: true", "empty folder",
                           "crew_live.py"):
                self.assertIn(needle, text, f"{root}: {needle}")
        claude = _read(ROOT / "dist" / "claude")
        self.assertIn("disable-model-invocation: true", claude)

    def test_nova_missao_gates_fail_no_commit(self):
        # R34
        for root in _roots():
            text = _read(root)
            for needle in ("FAIL", "last 20 lines", "No commit", "McCoy", "keep the folder",
                           "remove the folder", "confirmation"):
                self.assertIn(needle, text, f"{root}: {needle}")

    def test_nova_missao_offers_setup_and_first_mission(self):
        # R35
        for root in _roots():
            text = _read(root)
            self.assertIn("{{CMD:setup}}" if root == ROOT else "setup", text)
            for needle in ("engajar", "first mission", "single message",
                           "run neither", "never create a remote", "push", "deploy"):
                self.assertIn(needle, text, f"{root}: {needle}")

    def test_nova_missao_series_choice(self):
        # R43
        for root in _roots():
            text = _read(root)
            for needle in ("fora da série testada", "--pin-tested", "--allow-new-series", "(recommended)",
                           "Context7 summary", "new version"):
                self.assertIn(needle, text, f"{root}: {needle}")
            self.assertLess(text.find("--pin-tested"), text.find("--allow-new-series"))

    def test_nova_missao_without_context7(self):
        # R44
        for root in _roots():
            text = _read(root)
            for needle in ("Without Context7", "one line", "não verificada", "--verified",
                           "does not block"):
                self.assertIn(needle, text, f"{root}: {needle}")


class NovaMissaoRoutingEvalsTests(unittest.TestCase):
    def test_routing_cases_exist(self):
        base = ROOT / "evals" / "routing"
        for name in ("pos-uhura-cache", "neg-uhura-pr-gh", "pos-scotty-detect", "neg-scotty-deploy",
                     "pos-nova-missao", "neg-nova-missao-existing"):
            text = (base / name / "case.yaml").read_text(encoding="utf-8")
            self.assertIn("tool: Skill", text, name)
            self.assertIn("min:", text, name)
            if name.startswith("neg-"):
                self.assertIn("min: 0", text, name)


if __name__ == "__main__":
    unittest.main()
