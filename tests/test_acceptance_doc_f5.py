"""C23: a seção Codex de docs/aceite/fase-5.md está preenchida com a evidência da sessão real (R19)."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

import miniyaml  # noqa: E402 (helpers puts tools/ on sys.path)

DOC = ROOT / "docs" / "aceite" / "fase-5.md"
CAPS = ROOT / "src" / "capabilities.yaml"
COMPAT = ROOT / "docs" / "compatibilidade.md"
CLIS = {"Codex": "codex", "Antigravity": "antigravity", "OpenCode": "opencode"}


def doc_section(name: str) -> str:
    parts = re.split(r"^## ", DOC.read_text(encoding="utf-8"), flags=re.M)
    return next(p for p in parts if p.startswith(name))


def field(sec: str, label: str) -> str:
    m = re.search(rf"^- \*\*{re.escape(label)}\*\*: (.+(?:\n  .+)*)", sec, flags=re.M)
    assert m, f"falta o campo '{label}'"
    return m.group(1)


class AcceptanceDocF5Tests(unittest.TestCase):
    def test_acceptance_doc_f5_codex_filled(self):
        sec = doc_section("Codex")
        result = re.search(r"\*\*Resultado\*\*: (.+)", sec)
        self.assertIsNotNone(result, "Codex: sem **Resultado**")
        self.assertRegex(result.group(1), r"^(aprovado|reprovado \(.+\))", "Codex: Resultado inválido")
        self.assertRegex(field(sec, "Versão"), r"\d+\.\d+\.\d+", "Codex: sem versão do CLI")
        self.assertIn("/hooks", field(sec, "Trust (`/hooks`)"))
        push = field(sec, "Bloqueio de push forçado")
        self.assertIn("git push --force origin main", push)
        self.assertIn("StarCode bloqueou", push)
        secret = field(sec, "Bloqueio de segredo")
        self.assertIn("possível segredo", secret)
        self.assertNotIn("q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3", sec, "o valor de teste do segredo não vai no doc")
        normal = field(sec, "Comandos normais")
        for cmd in ("git status", "git add .", "git commit", "git switch -c", "git merge --no-ff",
                    "orca linear issue", "run_gates.py", "unittest discover"):
            self.assertIn(cmd, normal, f"Comandos normais sem '{cmd}'")
        self.assertIn("CLI: codex", field(sec, "Banner"))
        for label in ("Versão", "Trust (`/hooks`)", "Bloqueio de push forçado", "Bloqueio de segredo",
                      "Comandos normais", "Banner"):
            self.assertNotIn("pendente", field(sec, label).lower(), f"Codex: '{label}' pendente")
        self.assertNotIn("pendente", result.group(1).lower())

    def test_acceptance_doc_f5_antigravity_filled(self):
        sec = doc_section("Antigravity")
        result = re.search(r"\*\*Resultado\*\*: (.+)", sec)
        self.assertIsNotNone(result, "Antigravity: sem **Resultado**")
        self.assertRegex(result.group(1), r"^(aprovado|reprovado \(.+\))", "Antigravity: Resultado inválido")
        self.assertNotIn("pendente", result.group(1).lower())
        self.assertRegex(field(sec, "Versão"), r"agy \d+\.\d+\.\d+", "Antigravity: sem versão do CLI")
        self.assertRegex(field(sec, "Contagem de hooks"), r"hooks [1-9]", "Antigravity: contagem de hooks")
        self.assertIn("aspas", field(sec, "Tentativa 1 (T10)"), "falta a tentativa 1 reprovada (aspas)")
        self.assertIn("git push --force origin main", field(sec, "Bloqueio de push forçado"))
        self.assertIn("segredo", field(sec, "Bloqueio de segredo"))
        self.assertNotIn("q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3", sec, "o valor de teste do segredo não vai no doc")
        self.assertIn("Comandos normais", sec)
        self.assertIn("Banner", sec)
        if result.group(1).startswith("aprovado"):
            normal = field(sec, "Comandos normais")
            for cmd in ("git status", "git add .", "git commit", "git switch -c", "git merge --no-ff",
                        "orca linear issue", "run_gates.py", "unittest discover"):
                self.assertIn(cmd, normal, f"Comandos normais sem '{cmd}'")
            self.assertIn("antigravity", field(sec, "Banner").lower())
            self.assertIn("StarCode bloqueou", field(sec, "Bloqueio de push forçado"))
            self.assertIn("possível segredo", field(sec, "Bloqueio de segredo"))
        else:
            self.assertIn("(Bloqueio", result.group(1), "reprovação deve citar o passo")

    def test_acceptance_doc_f5_opencode_filled(self):
        sec = doc_section("OpenCode")
        result = re.search(r"\*\*Resultado\*\*: (.+)", sec)
        self.assertIsNotNone(result, "OpenCode: sem **Resultado**")
        self.assertRegex(result.group(1), r"^(aprovado|reprovado \(.+\))", "OpenCode: Resultado inválido")
        self.assertNotIn("pendente", result.group(1).lower())
        self.assertRegex(field(sec, "Versão"), r"\d+\.\d+\.\d+", "OpenCode: sem versão do CLI")
        self.assertIn(".config/opencode/plugins/starcode.js", field(sec, "Plugin na pasta global"))
        self.assertIn("git push --force origin main", field(sec, "Bloqueio de push forçado"))
        self.assertIn("StarCode bloqueou", field(sec, "Bloqueio de push forçado"))
        self.assertIn("segredo", field(sec, "Bloqueio de segredo"))
        self.assertNotIn("q8Zr2Lm9Xv4Tn7Wp1Ks6Yd3", sec, "o valor de teste do segredo não vai no doc")
        normal = field(sec, "Comandos normais")
        for cmd in ("git status", "git add .", "git commit", "git switch -c", "git merge --no-ff",
                    "orca linear issue", "run_gates.py", "unittest discover"):
            self.assertIn(cmd, normal, f"Comandos normais sem '{cmd}'")
        self.assertIn("n/a", field(sec, "Banner"))
        for label in ("Versão", "Plugin na pasta global", "Bloqueio de push forçado", "Bloqueio de segredo",
                      "Comandos normais", "Banner"):
            self.assertNotIn("pendente", field(sec, label).lower(), f"OpenCode: '{label}' pendente")
        if result.group(1).startswith("reprovado"):
            self.assertIn("(Bloqueio de segredo", result.group(1), "a reprovação deve citar o passo")
            self.assertRegex(sec, r"`[^`\n]{8,}`", "reprovado sem a evidência do erro")

    def test_capabilities_match_f5_acceptance(self):
        # R18: aprovado = hooks ok; reprovado = unavailable com motivo; OpenCode mantém banner_hook unavailable.
        caps = miniyaml.loads(CAPS.read_text(encoding="utf-8"))
        text = DOC.read_text(encoding="utf-8")
        for name, key in CLIS.items():
            sec = doc_section(name)
            approved = re.search(r"\*\*Resultado\*\*: (.+)", sec).group(1).startswith("aprovado")
            hooks = caps[key]["hooks"]
            if approved:
                self.assertEqual(hooks["status"], "ok", f"{key}: aprovado, hooks deve ser ok")
            else:
                self.assertEqual(hooks["status"], "unavailable", f"{key}: reprovado, hooks deve ser unavailable")
                self.assertTrue(hooks.get("fallback"), f"{key}: unavailable sem motivo")
            banner = caps[key]["banner_hook"]["status"]
            if key == "opencode":
                self.assertEqual(banner, "unavailable", "OpenCode não tem banner por hook")
            else:
                self.assertEqual(banner, "ok" if approved else "unavailable", f"{key}: banner_hook")
        self.assertIn("Fase 5", COMPAT.read_text(encoding="utf-8"), "docs/compatibilidade.md sem a nota da Fase 5")
        self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
