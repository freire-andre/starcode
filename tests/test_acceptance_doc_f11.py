"""R35 a R38: aceite real da Fase 11 (telas) registrado em docs/aceite/fase-11.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

DOC = ROOT / "docs" / "aceite" / "fase-11.md"
SECTIONS = ("App", "Mockup", "Rodada 1", "Rodada 2", "Gate")
RESULT = re.compile(r"^\*\*Resultado\*\*: (aprovado|reprovado)$", re.M)
FILE = re.compile(r"`(docs/aceite/fase-11/[\w.-]+)`")


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF11Tests(unittest.TestCase):
    def test_fase11_acceptance_sections(self):
        text = DOC.read_text(encoding="utf-8")
        parts = _parts()
        head = text.split("\n## ", 1)[0]
        self.assertEqual(len(RESULT.findall(head)), 1, "falta o **Resultado** geral no topo")
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertEqual(len(RESULT.findall(parts[name])), 1,
                             f"{name}: precisa de um **Resultado** aprovado ou reprovado")
            for rel in FILE.findall(parts[name]):
                path = ROOT / rel
                self.assertTrue(path.is_file(), f"{name}: arquivo ausente {rel}")
                if rel.endswith(".png"):
                    self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n", f"{rel} não é PNG")
        overall = RESULT.search(head).group(1)
        if overall == "aprovado":
            for name in SECTIONS:
                self.assertIn("**Resultado**: aprovado", parts[name], f"{name} não aprovado")
        # R35: app Tauri novo, issues PROJ e mockup
        self.assertIn("aceite/telas/", parts["App"])
        self.assertTrue((ROOT / "aceite" / "telas" / "package.json").is_file())
        self.assertIn("PROJ-34", parts["App"])
        self.assertIn("800x600", parts["Mockup"])
        self.assertTrue(FILE.search(parts["Mockup"]), "Mockup: sem cópia do mockup")
        # R36: screens.md todo em matches, fotos running, gate com 0
        self.assertIn("matches", parts["Rodada 2"])
        self.assertIn("running", parts["Rodada 2"])
        self.assertIn("exit 0", parts["Gate"])
        self.assertIn("validate_verification", parts["Gate"])
        # R37: divergência plantada em copy na rodada 1, fechada na 2
        self.assertIn("diverges", parts["Rodada 1"])
        self.assertIn("copy", parts["Rodada 1"])
        self.assertIn("same", parts["Rodada 2"])
        for rel in ("mockup-saudacao.png", "rodada1-saudacao.running.png",
                    "rodada2-saudacao.running.png", "screens-rodada1.md", "screens-rodada2.md"):
            self.assertTrue((ROOT / "docs" / "aceite" / "fase-11" / rel).is_file(), rel)


ASSETS = ROOT / "docs" / "aceite" / "fase-11"
ROW = re.compile(r"^\| (?P<el>[^|]+) \| (?P<res>same|differs) \| .*\|$", re.M)


def _inventory(name: str) -> list[tuple[str, str]]:
    text = (ASSETS / name).read_text(encoding="utf-8")
    return [(m.group("el").strip(), m.group("res")) for m in ROW.finditer(text)]


def _verdict_row(name: str) -> str:
    text = (ASSETS / name).read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if re.search(r"\| (matches|diverges) \|", ln)]
    assert len(rows) == 1, f"{name}: esperava uma linha de veredito, achei {len(rows)}"
    return rows[0]


class AcceptanceArtifactsF11Tests(unittest.TestCase):
    """Valida os artefatos COPIADOS para docs/aceite/fase-11/, não reexecuta o fluxo.

    O aceite rodou num repositório externo (`F:\\Projetos\\starcode-telas`) que não existe
    no CI; por isso estes testes leem as cópias registradas (fotos, screens.md e a seção
    Gate do doc) e checam o que elas afirmam, sem tocar na Orca nem no app.
    """

    def test_mockup_e_fotos_running_medem_800x600(self):
        import images
        for rel in ("mockup-saudacao.png", "rodada1-saudacao.running.png",
                    "rodada2-saudacao.running.png"):
            self.assertEqual(images.image_size(ASSETS / rel), (800, 600), rel)

    def test_rodada1_diverge_com_uma_linha_copy(self):
        self.assertIn("| diverges |", _verdict_row("screens-rodada1.md"))
        self.assertIn("(copy)", _verdict_row("screens-rodada1.md"))
        inv = _inventory("screens-rodada1.md")
        differs = [el for el, res in inv if res == "differs"]
        self.assertEqual(len(differs), 1, inv)
        self.assertEqual(sum(1 for _, res in inv if res == "same"), len(inv) - 1)
        self.assertGreater(len(inv), 1)

    def test_rodada2_casa_e_a_linha_corrigida_virou_same(self):
        self.assertIn("| matches |", _verdict_row("screens-rodada2.md"))
        inv1, inv2 = _inventory("screens-rodada1.md"), _inventory("screens-rodada2.md")
        self.assertFalse([el for el, res in inv2 if res == "differs"], inv2)
        corrigida = [el for el, res in inv1 if res == "differs"][0]
        self.assertIn((corrigida, "same"), inv2)

    def test_screens_md_tem_pictures_running_e_verifier(self):
        for name in ("screens-rodada1.md", "screens-rodada2.md"):
            text = (ASSETS / name).read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^\*\*Pictures\*\*: running$", name)
            self.assertRegex(text, r"(?m)^\*\*Verifier\*\*: \S+", name)

    def test_secao_gate_cita_comando_e_exit_0(self):
        gate = _parts()["Gate"]
        self.assertIn("validate_verification", gate)
        self.assertIn("exit 0", gate)


if __name__ == "__main__":
    unittest.main()
