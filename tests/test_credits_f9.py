"""F9 T11 (C37): CREDITS.md tem as 6 fontes com licença e cada arquivo adaptado tem comentário de origem (R34)."""
from __future__ import annotations

import unittest

from helpers import ROOT


class CreditsF9Tests(unittest.TestCase):
    def test_credits_f9_sources_and_headers(self):
        credits = (ROOT / "CREDITS.md").read_text(encoding="utf-8")
        rows = {line.split("|")[1].strip(): line for line in credits.splitlines() if line.startswith("| ")}
        fontes = {
            "the-judge 1.4.0": ("CC-BY-4.0", "scripts/review/"),
            "harness-eval 1.8.3": ("CC-BY-4.0", "scripts/harness/"),
            "tlc-spec-driven": ("CC-BY-4.0", "scripts/lessons.py"),
            "mattpocock/skills": ("MIT", "skills/guinan/references/retro.md"),
            "Cloudflare security-audit-skill": ("MIT", "skills/worf/references/security-evidence.md"),
            "harness-score": ("npx", "scripts/diagnostico.py"),
        }
        for chave, (licenca, arquivo) in fontes.items():
            linha = next((v for k, v in rows.items() if k.startswith(chave)), None)
            self.assertIsNotNone(linha, chave)
            self.assertIn(licenca, linha, chave)
            self.assertIn(arquivo, linha, chave)
        self.assertNotIn("v1.3", credits)
        self.assertEqual(sum(1 for k in rows if k.startswith("the-judge")), 1)
        self.assertEqual(sum(1 for k in rows if k.startswith("Cloudflare")), 1)
        for path in sorted((ROOT / "scripts" / "review").glob("*.py")) + sorted(
                (ROOT / "scripts" / "harness").glob("*.py")) + [ROOT / "scripts" / "lessons.py"]:
            head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:6])
            self.assertIn("Origem:", head, path.name)


if __name__ == "__main__":
    unittest.main()
