"""C32: the Phase 3 acceptance doc has the five scripts, each with a result and evidence (R48)."""
from __future__ import annotations

import re
import subprocess
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-3.md"
SANDBOX = ROOT.parent / "starcode-sandbox"
SCRIPTS = ("modo 2", "modo 1", "verificação degradada", "disjuntor", "escritor único")


class AcceptanceDocTests(unittest.TestCase):
    def test_acceptance_doc_has_all_scripts(self):
        text = DOC.read_text(encoding="utf-8")
        sections = re.split(r"^## ", text, flags=re.M)
        for n, name in enumerate(SCRIPTS, start=1):
            sec = next((s for s in sections if s.lower().startswith(f"roteiro {n}: {name}")), None)
            self.assertIsNotNone(sec, f"falta a seção '## Roteiro {n}: {name}'")
            self.assertRegex(sec, r"\*\*Resultado\*\*: ✅", f"roteiro {n} sem resultado aprovado")
            evidence = re.search(r"\*\*Evidência\*\*:(.+?)(?=\n\*\*|\Z)", sec, re.S)
            self.assertIsNotNone(evidence, f"roteiro {n} sem evidência")
            # evidence must cite something checkable: a commit hash, an issue or a gate verdict line
            self.assertRegex(evidence.group(1), r"\b[0-9a-f]{7}\b|PROJ-\d+|VEREDITO|DISJUNTOR",
                             f"roteiro {n}: evidência sem commit, issue ou veredito")

    def test_cited_hashes_are_real_commits(self):
        # C32: every 7+ char hash the evidence cites is a commit of this repo or of the sandbox.
        text = DOC.read_text(encoding="utf-8")
        repos = [ROOT] + ([SANDBOX] if SANDBOX.is_dir() else [])
        hashes = sorted(set(re.findall(r"\b[0-9a-f]{7,40}\b", text)))
        self.assertTrue(hashes, "a evidência não cita nenhum commit")
        for h in hashes:
            found = any(subprocess.run(["git", "cat-file", "-e", f"{h}^{{commit}}"], cwd=r, capture_output=True,
                                       stdin=subprocess.DEVNULL).returncode == 0 for r in repos)
            self.assertTrue(found, f"hash citado não é um commit: {h}")


if __name__ == "__main__":
    unittest.main()
