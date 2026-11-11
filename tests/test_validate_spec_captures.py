"""Regras de captura do validate_spec (R1-R4 da fase 11)."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES

import validate_spec

IMG_OK = "![tela](captures/tela.png)"
LINHA_OK = f"- {IMG_OK} - binding - desenha a tela inicial"
REQ_OK = "- **R1** - WHEN o usuário salva `theme=dark` THEN o sistema SHALL persistir o valor (veja `captures/tela.png`)."


class CapturasCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-captures-")
        self.root = Path(self._tmp.name)
        shutil.copytree(FIXTURES / "gates" / "medium", self.root / "m")
        self.root = self.root / "m"
        self.fdir = self.root / ".specs" / "features" / "dark-mode"
        self.spec = self.fdir / "spec.md"

    def tearDown(self):
        self._tmp.cleanup()

    def captura(self, *nomes):
        (self.fdir / "captures").mkdir(exist_ok=True)
        for n in nomes:
            (self.fdir / "captures" / n).write_bytes(b"x")

    def escreve(self, sources=None, req=None, extra=""):
        text = self.spec.read_text(encoding="utf-8")
        if req is not None:
            text = text.replace(
                "- **R1** - WHEN o usuário salva `theme=dark` THEN o sistema SHALL persistir o valor no perfil.", req)
        if sources is not None:
            text += "\n## Sources\n\n" + "\n".join(sources) + "\n\n## Differences from the Source\n\nNone - o produto segue a fonte.\n"
        self.spec.write_text(text + extra, encoding="utf-8")

    def erros(self):
        return validate_spec.evaluate(None, self.root).errors

    def test_captura_sem_sources(self):
        self.captura("tela.png")
        msgs = self.erros()
        self.assertTrue(any("captures/ tem o design mas falta `## Sources`" in e for e in msgs), msgs)

    def test_captura_sem_linha_ou_non_binding_sem_citacao(self):
        self.captura("tela.png", "outra.png")
        self.escreve([LINHA_OK, "- ![outra](captures/outra.png) - non-binding - só referência"], REQ_OK)
        msgs = self.erros()
        self.assertTrue(any("outra.png" in e and "non-binding" in e for e in msgs), msgs)
        # sem linha nenhuma para a captura
        self.tearDown()
        self.setUp()
        self.captura("tela.png", "sem_linha.png")
        self.escreve([LINHA_OK], REQ_OK, extra="\n![sem](captures/sem_linha.png)\n")
        msgs = self.erros()
        self.assertTrue(any("sem_linha.png" in e and "## Sources" in e for e in msgs), msgs)

    def test_captura_vinculante_sem_requisito(self):
        self.captura("tela.png")
        self.escreve([LINHA_OK])
        msgs = self.erros()
        self.assertTrue(any("nenhum requisito cita a captura `tela.png`" in e for e in msgs), msgs)

    def test_captura_sem_imagem_na_spec(self):
        self.captura("tela.png")
        self.escreve(["- captures/tela.png - binding - desenha a tela inicial"], REQ_OK)
        msgs = self.erros()
        self.assertTrue(any("tela.png" in e and "![" in e for e in msgs), msgs)

    def test_spec_com_captura_completa_passa(self):
        self.captura("tela.png", "ref.png")
        self.escreve([LINHA_OK,
                      '- ![ref](captures/ref.png) - non-binding user: "só de inspiração" - clima visual'], REQ_OK)
        self.assertEqual(self.erros(), [])

    def test_spec_sem_captures_inalterada(self):
        self.assertEqual(self.erros(), [])
