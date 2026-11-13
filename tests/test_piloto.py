"""Tests for the autopilot: piloto.py (mandate + decision log), the gates accepting a `piloto:` approval only on
tasks.md with a confirmed mandate, the banner line and the skill contents (Troi grill mode, piloto-automatico)."""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase

import banner
import gates_common as gc
import piloto

CLIS = ("claude", "codex", "antigravity", "opencode")
SLUG = "export-csv"


class PilotoCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.fdir = self.repo / ".specs" / "features" / SLUG
        self.fdir.mkdir(parents=True)
        piloto.start(SLUG, self.repo)
        self.path = self.fdir / "piloto.md"

    def confirmed(self):
        piloto.add_mandate(SLUG, self.repo, "principio", "simplicidade antes de completude", "Q3")
        piloto.add_mandate(SLUG, self.repo, "limite", "nunca adicionar dependência nova", "Q7")
        piloto.confirm(SLUG, self.repo, 'sim, é isso "fechado"')


class PilotoScriptTests(PilotoCase):
    def test_start_is_idempotent_and_fixed_format(self):
        self.assertIn("já existe (ativo)", piloto.start(SLUG, self.repo))
        text = self.path.read_text(encoding="utf-8")
        for needle in ("# Piloto automático: export-csv", "**Status:** ativo", "**Mandato confirmado:** pendente",
                       "## Mandato", "## Decisões"):
            self.assertIn(needle, text)

    def test_no_decision_before_confirmed_mandate(self):
        with self.assertRaisesRegex(piloto.PilotoError, "mandato não confirmado"):
            piloto.record(SLUG, self.repo, "data", "q", "a | b", "a", "r", "Q1")
        with self.assertRaisesRegex(piloto.PilotoError, "mandato vazio"):
            piloto.confirm(SLUG, self.repo, "ok")
        self.assertFalse(piloto.is_active(SLUG, self.repo))

    def test_mandate_numbered_and_locked_after_confirm(self):
        self.confirmed()
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("- **M1** · princípio · simplicidade antes de completude · origem: Q3", text)
        self.assertIn("- **M2** · limite · nunca adicionar dependência nova · origem: Q7", text)
        self.assertLess(text.index("**M2**"), text.index("## Decisões"))
        self.assertRegex(text, r"\*\*Mandato confirmado:\*\* \d{4}-\d{2}-\d{2} - user: \"sim, é isso 'fechado'\"")
        with self.assertRaisesRegex(piloto.PilotoError, "já confirmado"):
            piloto.add_mandate(SLUG, self.repo, "preferencia", "x", "Q9")
        self.assertTrue(piloto.is_active(SLUG, self.repo))

    def test_record_decisions_confidence_and_review(self):
        self.confirmed()
        self.assertEqual(piloto.record(SLUG, self.repo, "data", "Aprova as tasks?", "sim | ajustes", "sim",
                                       "cobre todos os requisitos", "M1,q3"), "D1 registrada (confiança alta)")
        out = piloto.record(SLUG, self.repo, "laforge", "Usar lib X?", "lib X | código próprio", "código próprio",
                            "opção mais segura", "", "alta")
        self.assertEqual(out, "D2 registrada (confiança baixa, revisar)")  # no basis: never above baixa
        text = self.path.read_text(encoding="utf-8")
        self.assertRegex(text, r"### D1 · \S+Z · data · confiança alta\n- \*\*Pergunta:\*\* Aprova as tasks\?")
        self.assertIn("- **Base:** M1, Q3", text)
        self.assertRegex(text, r"### D2 · .* · confiança baixa · ⚠️ revisar")
        self.assertIn("- **Base:** nenhuma na entrevista", text)
        self.assertEqual(piloto.status(SLUG, self.repo)[-1], "Revisar: D2")
        with self.assertRaisesRegex(piloto.PilotoError, "inexistente: M9"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "M9")
        with self.assertRaisesRegex(piloto.PilotoError, "--basis aceita"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "R1")

    def test_finish_stops_decisions(self):
        self.confirmed()
        piloto.finish(SLUG, self.repo, "assumo daqui")
        self.assertFalse(piloto.is_active(SLUG, self.repo))
        self.assertIn("**Encerrado:**", self.path.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(piloto.PilotoError, "encerrado"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "M1")
        self.assertEqual(piloto.actives(self.repo), [])

    def test_cli_exit_codes(self):
        script = str(ROOT / "scripts" / "piloto.py")

        def run(*args):
            return subprocess.run([sys.executable, script, *args, "--root", str(self.repo)], capture_output=True,
                                  text=True, encoding="utf-8")
        self.assertEqual(run("ativo", SLUG).returncode, 1)
        self.assertEqual(run("registrar", SLUG, "--by", "data", "--question", "q", "--options", "a",
                             "--decision", "a", "--reason", "r").returncode, 1)
        self.assertEqual(run("start", "Nao_Valido").returncode, 1)
        self.confirmed()
        self.assertEqual(run("ativo", SLUG).returncode, 0)
        res = run("ativos")
        self.assertIn("export-csv: 0 decisão(ões), 0 para revisar", res.stdout)


class PilotApprovalGateTests(PilotoCase):
    LINE = '**Approved**: 2026-11-13 - piloto: "D4 tasks cobrem a spec"'

    def test_pilot_line_needs_confirmed_active_mandate(self):
        self.assertFalse(gc.approved([self.LINE], self.fdir, allow_pilot=True))
        self.confirmed()
        self.assertTrue(gc.approved([self.LINE], self.fdir, allow_pilot=True))
        self.assertFalse(gc.approved([self.LINE], self.fdir))  # the spec never accepts it
        self.assertFalse(gc.approved(['**Approved**: 2026-11-13 - piloto: "sem id"'], self.fdir, allow_pilot=True))
        piloto.finish(SLUG, self.repo)
        self.assertFalse(gc.approved([self.LINE], self.fdir, allow_pilot=True))

    def test_user_line_still_accepted(self):
        self.assertTrue(gc.approved(['**Approved**: 2026-11-13 - user: "sim"']))

    def test_gates_pass_pilot_only_on_tasks(self):
        import validate_tasks as vt

        gates = ROOT / "tests" / "fixtures" / "gates" / "large" / ".specs" / "features" / "export-csv"
        for name in ("spec.md", "tasks.md"):
            text = (gates / name).read_text(encoding="utf-8")
            (self.fdir / name).write_text(text, encoding="utf-8")
        self.confirmed()
        tasks = self.fdir / "tasks.md"
        text = tasks.read_text(encoding="utf-8")
        text = re.sub(r"^\*\*Approved\*\*:.*$", self.LINE, text, flags=re.M)
        if self.LINE not in text:
            text = text.replace("\n", "\n" + self.LINE + "\n", 1)
        tasks.write_text(text, encoding="utf-8")
        res = vt.evaluate(SLUG, self.repo, execute=True)
        self.assertFalse([e for e in res.errors if "tasks.md sem" in e], res.errors)
        spec = self.fdir / "spec.md"
        spec.write_text(re.sub(r"^\*\*Approved\*\*:.*$", self.LINE, spec.read_text(encoding="utf-8"), flags=re.M),
                        encoding="utf-8")
        res = vt.evaluate(SLUG, self.repo, execute=True)
        self.assertTrue([e for e in res.errors if "spec.md sem" in e], res.errors)


class PilotBannerTests(PilotoCase):
    def test_banner_shows_active_autopilot(self):
        self.write_repo_config()
        self.confirmed()
        piloto.record(SLUG, self.repo, "data", "q", "a | b", "a", "r", "")
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            text = banner.build_banner(str(self.repo), False)[0]
        self.assertIn("🛸 Piloto automático: ativo em export-csv (1 decisão(ões), 1 para revisar;", text)


class PilotSkillTests(unittest.TestCase):
    def roots(self):
        return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]

    def test_piloto_skill_rules(self):
        for root in self.roots():
            text = (root / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: piloto-automatico\n"), root)
            for needle in ("mode: grill", 'piloto.py" confirmar', 'piloto.py" registrar', "Record before acting",
                           "approve the spec yourself", "never write a `user:` line the user did not say",'piloto: "D<n> <resumo>"', "Never widen the spec",
                           "**push**", "**opening the PR**", "**merge into the base branch**", "**deploy**",
                           "never run\n  `git_mode.py authorize-merge`", "the Git mode is still asked",
                           "safest and most reversible"):
                self.assertIn(needle, text, f"{root}: {needle}")
        claude = (ROOT / "dist" / "claude" / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: true", claude)

    def test_troi_grill_mode(self):
        for root in self.roots():
            text = (root / "skills" / "troi" / "SKILL.md").read_text(encoding="utf-8")
            sec = text.split("## 2G. Grill mode", 1)[1].split("\n## 3.", 1)[0]
            for needle in ("frontier", "❓ **Q<n>**", "➡️", 'so "sim" accepts', "never restart", "No round cap",
                           'piloto.py" mandato', "ask the\n  user to confirm it", "mattpocock/skills, MIT"):
                self.assertIn(needle, sec, f"{root}: {needle}")

    def test_flow_hooks_into_autopilot(self):
        engajar = (ROOT / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('piloto.py" ativo <slug>', engajar)
        data = (ROOT / "skills" / "data" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('piloto: "D<n> <resumo>"', data)
        guinan = (ROOT / "skills" / "guinan" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Piloto automático", guinan)


if __name__ == "__main__":
    unittest.main()
