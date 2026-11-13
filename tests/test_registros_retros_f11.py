from __future__ import annotations

import re
import unittest

from helpers import ROOT


class RegistrosRetrosF11Tests(unittest.TestCase):
    def test_compatibilidade_cita_limite_do_drive(self) -> None:
        text = (ROOT / "docs/compatibilidade.md").read_text(encoding="utf-8")
        linhas = [l for l in text.splitlines() if "orca plugin test" in l]
        self.assertTrue(linhas)
        linha = linhas[0]
        for frag in ("orca plugin check", "1.4.257", "drive", "orca-runtime.mjs", "worktree"):
            self.assertIn(frag, linha)

    def test_relato_orca_tem_as_secoes(self) -> None:
        text = (ROOT / "docs/relatos/orca-plugin-test-drive.md").read_text(encoding="utf-8")
        for sec in ("Orca version", "OS", "Steps to reproduce", "Expected", "Actual", "Workaround"):
            self.assertRegex(text, rf"(?m)^## {re.escape(sec)}\s*$")
        self.assertIn("orca-runtime.mjs", text)
        self.assertIn("1.4.257", text)
        self.assertNotRegex(text, r"[ãõçáéíóúâêô]")
        self.assertNotRegex(text, r"(?i)\b(não|para|com|uma|que|está|quando)\b")

    def test_decisions_registra_os_itens_de_scripts(self) -> None:
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entradas = re.findall(r"(?ms)^### F12-\d+:.*?(?=^### |\Z)", text)
        junto = "\n".join(entradas)
        for item in (
            "handoff.py",
            "check_proofs.py",
            "dispatch.py brief",
            "dispatch.py start",
            "dispatch.py settle",
            "validate_tasks.py",
        ):
            self.assertIn(item, junto)


if __name__ == "__main__":
    unittest.main()
