"""C27/C28/C29: the Phase 4 acceptance doc and the compatibility matrix (R27, R28, R29)."""
from __future__ import annotations

import re
import subprocess
import unittest

from helpers import ROOT

import miniyaml  # noqa: E402 (helpers puts tools/ on sys.path)
from test_acceptance_doc import SANDBOX

DOC = ROOT / "docs" / "aceite" / "fase-4.md"
COMPAT = ROOT / "docs" / "compatibilidade.md"
CAPS = ROOT / "src" / "capabilities.yaml"
CLIS = ("Codex", "Antigravity", "OpenCode")
EXTRAS = ("hooks", "banner_hook", "linear_mcp", "subagent_model", "orca_worker")
COLUMNS = ("claude", "codex", "antigravity", "opencode")


def _sections(text: str, prefix: str = "## ") -> list[str]:
    return re.split(rf"^{re.escape(prefix)}", text, flags=re.M)


def _cli_section(text: str, cli: str):
    return next((s for s in _sections(text) if s.startswith(cli)), None)


class AcceptanceDocF4Tests(unittest.TestCase):
    def test_acceptance_doc_f4_has_all_clis(self):
        text = DOC.read_text(encoding="utf-8")
        for cli in CLIS:
            sec = _cli_section(text, cli)
            self.assertIsNotNone(sec, f"falta a seção '## {cli}'")
            self.assertRegex(sec, r"\*\*Resultado\*\*: ", f"{cli}: sem **Resultado**")
            self.assertRegex(sec, r"\*\*Evidência\*\*:", f"{cli}: sem **Evidência**")
            evidence = sec.split("**Evidência**:", 1)[1]
            self.assertRegex(evidence, r"\b[0-9a-f]{7}\b", f"{cli}: evidência sem commit")
            self.assertRegex(evidence, r"PROJ-\d+", f"{cli}: evidência sem issue PROJ")

    def test_cited_hashes_are_real_commits(self):
        text = DOC.read_text(encoding="utf-8")
        repos = [ROOT] + ([SANDBOX] if SANDBOX else [])
        hashes = sorted(set(re.findall(r"\b(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b", text)))
        self.assertTrue(hashes, "a evidência não cita nenhum commit")
        missing = [h for h in hashes if not any(
            subprocess.run(["git", "cat-file", "-e", f"{h}^{{commit}}"], cwd=r, capture_output=True,
                           stdin=subprocess.DEVNULL).returncode == 0 for r in repos)]
        if missing and SANDBOX is None:
            self.skipTest(f"sandbox não encontrado (STARCODE_SANDBOX); hashes não verificados: {', '.join(missing)}")
        self.assertFalse(missing, f"hash citado não é um commit: {', '.join(missing)}")

    def test_compat_matrix_has_phase4(self):
        text = COMPAT.read_text(encoding="utf-8")
        sec = next((s for s in _sections(text) if s.startswith("Fase 4")), None)
        self.assertIsNotNone(sec, "falta a seção '## Fase 4' em docs/compatibilidade.md")
        caps = miniyaml.loads(CAPS.read_text(encoding="utf-8"))
        rows = {}
        header = None
        for line in sec.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else None
            if not cells:
                continue
            if header is None:
                header = [c.lower() for c in cells]
                continue
            rows[cells[0].strip("`")] = cells
        self.assertIsNotNone(header, "seção da Fase 4 sem tabela")
        for col in COLUMNS:
            self.assertIn(col, header, f"tabela sem a coluna {col}")
        for extra in EXTRAS:
            self.assertIn(extra, rows, f"falta a linha do extra {extra}")
            for col in COLUMNS:
                cell = rows[extra][header.index(col)]
                want = caps[col][extra]["status"]
                self.assertTrue(cell.startswith(want), f"{extra}/{col}: esperado '{want}', veio '{cell}'")

    def test_failed_cli_recorded_as_reprovado(self):
        # R29: a failed core step is `reprovado (<passo>)` with the exact error line, never "unavailable".
        text = DOC.read_text(encoding="utf-8")
        for cli in CLIS:
            sec = _cli_section(text, cli)
            result = re.search(r"\*\*Resultado\*\*: (.+)", sec).group(1)
            if "reprovado" in result.lower() and "aprovado" not in result.lower().replace("reprovado", ""):
                self.assertRegex(result, r"reprovado \(.+\)", f"{cli}: reprovado sem o passo")
                self.assertRegex(sec, r"`[^`\n]{8,}`", f"{cli}: reprovado sem a linha do erro")
                self.assertNotIn("indispon", result.lower(), f"{cli}: reprovado marcado como indisponível")


if __name__ == "__main__":
    unittest.main()
