from __future__ import annotations

import struct
import sys
import unittest
import zlib
from pathlib import Path

from helpers import TempRepoCase, run_git

import check_proofs
import validate_verification as vv

PY = Path(sys.executable).as_posix()
APPROVED = '**Approved**: 2026-11-04 - user: "sim"\n\n'

SPEC = f"""# Demo: Spec

{APPROVED}**Size**: LARGE
**Status**: Approved

## Requirements

- **R1** - WHEN o usuário abre o app THEN the system SHALL mostrar a tela de `captures/home.png`.

## Sources

- ![home](captures/home.png) - binding - desenha a tela inicial
"""
SPEC_SEM_TELAS = f"# Demo: Spec\n\n{APPROVED}**Size**: LARGE\n**Status**: Approved\n"
TASKS = f"""# Demo: Tasks

{APPROVED}## Checks

**Build**: none - sem build
**Run unit**: `"{PY}" -c "print('test_alpha ... ok')"`

**C1** - alpha (R1)
Proof: run unit | test_alpha ... ok
"""
VERIFICATION = ("# Demo - verification\n\n**Verdict**: PASS\n**Verifier**: codex · requested gpt · effective unconfirmed\n\n"
                "## Checks\n\n| Check | Test | Holds |\n| --- | --- | --- |\n| C1 | `tests/t.py` `test_alpha` | yes |\n\n"
                "## Findings\n\nNone.\n")


def png(w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IEND", b"")


def screens(verdict: str = "match", round_: str = "**Round**: 1\n", verifier: str = "**Verifier**: codex · requested gpt · effective gpt\n",
            pictures: str = "**Pictures**: running\n") -> str:
    return (f"# Demo screens\n\n{verifier}{round_}{pictures}\n| Screen | Compared with | Verdict | Finding |\n"
            f"| --- | --- | --- | --- |\n| `captures/home.running.png` | `captures/home.png` | {verdict} | - |\n")


class ScreensTests(TempRepoCase):
    def montar(self, spec: str = SPEC, capture: str | None = "home.png", cap_size=(320, 200), running=(320, 200),
               screens_md: str | None = None) -> Path:
        fdir = self.repo / ".specs" / "features" / "demo"
        (fdir / "captures").mkdir(parents=True)
        (fdir / "spec.md").write_text(spec, encoding="utf-8")
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        if capture:
            (fdir / "captures" / capture).write_bytes(png(*cap_size))
        if running:
            (fdir / "captures" / "home.running.png").write_bytes(png(*running))
        (self.repo / "app.py").write_text("x = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: app")
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)
        (fdir / "verification.md").write_text(VERIFICATION, encoding="utf-8")
        if screens_md is not None:
            (fdir / "screens.md").write_text(screens_md, encoding="utf-8")
        run_git(self.repo, "add", ".specs")
        run_git(self.repo, "commit", "-q", "-m", "docs: verificação")
        return fdir

    def erros(self, **kw) -> str:
        strict = kw.pop("strict", False)
        self.montar(**kw)
        return "\n".join(vv.evaluate("demo", self.repo, strict=strict).errors)

    def test_feature_sem_telas_inalterada(self):
        self.montar(spec=SPEC_SEM_TELAS, capture=None, running=None)
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertEqual(res.warnings, [])

    def test_telas_sem_screens_md(self):
        self.assertIn("a feature tem tela mas falta `screens.md` (juiz de telas)", self.erros())

    def test_tela_diverges_reprova(self):
        errs = self.erros(screens_md=screens("diverges"))
        self.assertIn("captures/home.running.png", errs)
        self.assertIn("diverges", errs)

    def test_screens_sem_round_ou_round_3(self):
        self.assertIn("screens.md sem `**Round**:`", self.erros(screens_md=screens(round_="")))
        self.tearDown()
        self.setUp()
        self.assertIn("não há rodada 3: o que ainda difere vai para o usuário",
                      self.erros(screens_md=screens(round_="**Round**: 3\n")))

    def test_screens_sem_verifier(self):
        self.assertIn("screens.md sem `**Verifier**:`", self.erros(screens_md=screens(verifier="")))

    def test_captura_sem_running(self):
        self.assertIn("a captura `home.png` não tem `home.running.png`",
                      self.erros(running=None, screens_md=screens()))

    def test_running_em_outro_tamanho(self):
        errs = self.erros(running=(300, 200), screens_md=screens())
        self.assertIn("`home.running.png` tem 300x200 e a captura tem 320x200: tire a foto no tamanho da captura", errs)

    def test_running_2x_de_captura_1x_passa(self):
        self.montar(running=(640, 400), screens_md=screens())
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertEqual(res.warnings, [])

    def test_imagem_ilegivel_vira_erro(self):
        fdir = self.montar(screens_md=screens())
        (fdir / "captures" / "home.running.png").write_bytes(b"isto nao e uma imagem")
        errs = "\n".join(vv.evaluate("demo", self.repo).errors)
        self.assertIn("home.running.png", errs)
        self.assertIn("formato não suportado", errs)
        self.assertNotIn("Traceback", errs)

    def test_fotos_do_autor_degradada_e_strict(self):
        self.montar(screens_md=screens(pictures="**Pictures**: author's\n"))
        res = vv.evaluate("demo", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertTrue(any("o juiz julgou as fotos do autor" in w for w in res.warnings), res.report())
        strict = vv.evaluate("demo", self.repo, strict=True)
        self.assertFalse(strict.ok)
        self.assertTrue(any("o juiz julgou as fotos do autor" in e for e in strict.errors))


if __name__ == "__main__":
    unittest.main()
