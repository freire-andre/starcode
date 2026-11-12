from __future__ import annotations

import contextlib
import io
import json
import re
import struct
import unittest
import zlib

from helpers import TempRepoCase

import dispatch

SPEC = (
    "# Demo: Spec\n\n**Status**: Approved\n\n## Requirements\n\n"
    "- **R1** - WHEN abre THEN the system SHALL mostrar `captures/home@2x.png`.\n\n"
    "## Sources\n\n"
    "- ![home](captures/home@2x.png) - binding - tela inicial\n"
)
FORBIDDEN = ("tasks.md", "proofs.md", "Handoff", "## Checks", "git diff", "q-verify")


def png(w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


class DispatchScreensTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        (self.fdir / "captures").mkdir(parents=True)
        (self.fdir / "captures" / "home@2x.png").write_bytes(png(1600, 1200))
        (self.fdir / "spec.md").write_text(SPEC, encoding="utf-8")
        (self.fdir / "tasks.md").write_text("# Tasks\n\n## Checks\n\n**C1** - segredo-dos-checks\n", encoding="utf-8")
        (self.fdir / "proofs.md").write_text("# Proofs\n", encoding="utf-8")

    def brief(self, *extra: str) -> tuple[int, str, str]:
        out = self.repo / "screens-brief.md"
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            try:
                rc = dispatch.main(["screens-brief", "demo", "--root", str(self.repo), "--out", str(out), *extra])
            except SystemExit as exc:
                rc = int(exc.code)
        return rc, (out.read_text(encoding="utf-8") if out.exists() else ""), err.getvalue()

    def test_screens_brief_preenche_campos(self):
        rc, text, err = self.brief("--url", "http://localhost:5173", "--serve", "npm run dev")
        self.assertEqual(rc, 0, err)
        self.assertEqual(re.findall(r"\{\{[^}]+\}\}", text), [])
        for want in (".specs/features/demo/spec.md", "http://localhost:5173", "npm run dev",
                     ".specs/features/demo/screens.md", "screens.py", "captures/home@2x.png",
                     ".specs/features/demo/captures/home.running.png",
                     "gesture", "CSS size", "60 s", "Round: 1"):
            self.assertIn(want, text)
        listed = json.loads(text[text.index("[\n"):text.index("\n]\n```") + 2])
        self.assertEqual(listed[0]["css"], [800, 600])
        self.assertEqual(listed[0]["requirements"], ["R1"])

    def test_screens_brief_sem_captura_sai_2(self):
        (self.fdir / "spec.md").write_text("# Demo: Spec\n\n## Requirements\n", encoding="utf-8")
        rc, text, err = self.brief("--url", "http://localhost:5173")
        self.assertEqual(rc, 2)
        self.assertEqual(text, "")
        self.assertIn("a spec não cita captura vinculante: não há telas para julgar", err)

    def test_screens_brief_nao_leva_checks_nem_diff(self):
        rc, text, err = self.brief("--url", "http://localhost:5173")
        self.assertEqual(rc, 0, err)
        for bad in FORBIDDEN:
            self.assertNotIn(bad, text)
        self.assertNotIn("segredo-dos-checks", text)

    def test_screens_brief_regras_de_julgamento(self):
        rc, text, err = self.brief("--url", "http://localhost:5173")
        self.assertEqual(rc, 0, err)
        self.assertLess(text.index("inventory"), text.index("`same`"))
        for cat in ("controls", "arrangement", "copy", "drawing", "render"):
            self.assertIn(f"`{cat}`", text)
        for want in ("one `differs` line makes the screen `diverges`", "spacing, tone and weight",
                     "**Verifier**: pending", "**Round**:", "**Pictures**: running | author's",
                     "| Screen | Compared with | Verdict | Finding |", "| Element | Result | Picture draws |",
                     "## Limits", "author's picture", "UTF-8 without BOM", "Never commit"):
            self.assertIn(want, text)

    def test_screens_brief_rodada_2(self):
        rc, text, err = self.brief("--url", "http://localhost:5173", "--round", "2")
        self.assertEqual(rc, 0, err)
        self.assertIn("Round: 2", text)
        for want in ("only the pictures with a `differs` line", "no round 3", "nothing new enters the inventory"):
            self.assertIn(want, text)
        rc, _, _ = self.brief("--url", "http://localhost:5173", "--round", "3")
        self.assertNotEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
