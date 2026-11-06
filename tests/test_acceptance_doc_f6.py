"""R22: roteiros e esqueleto do aceite da Fase 6."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-6.md"
SCRIPTS = ROOT / "docs" / "aceite" / "roteiros-fase-6"


class AcceptanceDocF6Tests(unittest.TestCase):
    def test_roteiros_exist_with_required_parts(self):
        for name in ("claude", "codex", "antigravity", "opencode"):
            f = SCRIPTS / f"{name}.md"
            self.assertTrue(f.is_file(), f"falta {f.name}")
            text = f.read_text(encoding="utf-8")
            for part in ("Remoção", "Instalação", "Banner", "Skills carregadas", "git push --force origin main",
                         "1.0.0", "feature/fase-6-release"):
                self.assertIn(part, text, f"{name}: sem '{part}'")
        self.assertIn("marketplace remove starcode", (SCRIPTS / "codex.md").read_text(encoding="utf-8"))
        mission = SCRIPTS / "dia-de-missao.md"
        self.assertTrue(mission.is_file())
        self.assertIn("modo Git 2", mission.read_text(encoding="utf-8"))

    def test_skeleton_has_five_sections(self):
        text = DOC.read_text(encoding="utf-8")
        parts = {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}
        for name in ("Claude", "Codex", "Antigravity", "OpenCode", "Dia de missão"):
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertRegex(parts[name], r"\*\*Resultado\*\*: \S", f"{name}: sem **Resultado**")
        self.assertIn("Versões", parts)
        self.assertIn("| Item | Versão |", parts["Versões"])

    def _section(self, name):
        parts = {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", DOC.read_text(encoding="utf-8"), flags=re.M)[1:]}
        return parts[name]

    def _field(self, sec, label):
        m = re.search(rf"^- \*\*{re.escape(label)}\*\*: (.+(?:\n  .+)*)", sec, flags=re.M)
        self.assertIsNotNone(m, f"falta o campo '{label}'")
        return m.group(1)

    def test_acceptance_doc_f6_claude_codex_filled(self):
        versions = self._section("Versões")
        for name in ("Claude", "Codex"):
            sec = self._section(name)
            result = re.search(r"\*\*Resultado\*\*: (.+)", sec)
            self.assertIsNotNone(result, f"{name}: sem **Resultado**")
            self.assertRegex(result.group(1), r"^(aprovado|reprovado \(.+\))", f"{name}: Resultado inválido")
            self.assertTrue(result.group(1).startswith("aprovado"), f"{name}: aceite reprovado")
            self.assertRegex(self._field(sec, "Versão do CLI"), r"\d+\.\d+\.\d+", f"{name}: sem versão do CLI")
            cmds = self._field(sec, "Comandos")
            for part in ("marketplace add", "marketplace remove starcode", "feature/fase-6-release"):
                self.assertIn(part, cmds, f"{name}: Comandos sem '{part}'")
            banner = self._field(sec, "Banner")
            self.assertIn("Diário do Capitão", banner)
            if name == "Codex":
                self.assertIn("CLI: codex", banner)
                self.assertIn("/hooks", self._field(sec, "Trust (`/hooks`)"))
            skills = self._field(sec, "Skills")
            for s in ("engajar", "setup", "spock", "troi", "data", "laforge", "mccoy", "q"):
                self.assertIn(s, skills, f"{name}: Skills sem '{s}'")
            push = self._field(sec, "Bloqueio de push forçado")
            self.assertIn("git push --force origin main", push)
            self.assertIn("StarCode bloqueou", push)
            self.assertRegex(self._field(sec, "Versão do plugin"), r"1\.0\.0", f"{name}: sem versão 1.0.0")
            self.assertNotIn("pendente", sec.lower(), f"{name}: ainda pendente")
        for row in ("Claude Code", "Codex"):
            line = next(l for l in versions.splitlines() if l.startswith(f"| {row}"))
            self.assertRegex(line, r"\d+\.\d+\.\d+", f"Versões: {row} sem versão")


if __name__ == "__main__":
    unittest.main()
