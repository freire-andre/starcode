from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from helpers import ROOT  # noqa: F401  (sets sys.path)

import screens

FAKE = """\
import json, os, sys
d = os.environ["ORCA_FAKE"]
argv = sys.argv[1:]
key = "tab " + argv[1] if argv and argv[0] == "tab" and len(argv) > 1 else (argv[0] if argv else "")
log = os.path.join(d, "log.jsonl")
prev = 0
if os.path.exists(log):
    with open(log, encoding="utf-8") as fh:
        prev = sum(1 for ln in fh if json.loads(ln)["key"] == key)
with open(log, "a", encoding="utf-8") as fh:
    fh.write(json.dumps({"key": key, "argv": argv}) + "\\n")
with open(os.path.join(d, "cfg.json"), encoding="utf-8") as fh:
    cfg = json.load(fh)
resp = cfg[key]
r = resp[min(prev, len(resp) - 1)]
sys.stdout.write(r.get("stdout", ""))
sys.stderr.write(r.get("stderr", ""))
sys.exit(r.get("rc", 0))
"""


def png(w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def ok(result: dict) -> dict:
    return {"stdout": json.dumps({"ok": True, "result": result})}


def fail(msg: str) -> dict:
    return {"rc": 1, "stdout": json.dumps({"ok": False, "error": {"message": msg}})}


class ScreensTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.fakedir = self.tmp / "fake"
        self.fakedir.mkdir()
        (self.bin / "orca_fake.py").write_text(FAKE, encoding="utf-8")
        py = Path(sys.executable).as_posix()
        if os.name == "nt":
            (self.bin / "orca.cmd").write_text(
                f'@echo off\r\n"{py}" "%~dp0orca_fake.py" %*\r\n', encoding="utf-8")
        else:
            p = self.bin / "orca"
            p.write_text(f'#!/bin/sh\nexec "{py}" "$(dirname "$0")/orca_fake.py" "$@"\n', encoding="utf-8")
            p.chmod(p.stat().st_mode | stat.S_IEXEC)
        self.shot = self.tmp / "shot.png"
        self.shot.write_bytes(png(800, 600))
        self.cfg = {
            "tab create": [ok({"browserPageId": "p1"})],
            "tab switch": [ok({})],
            "tab close": [ok({})],
            "exec": [ok({"width": 800, "height": 600, "deviceScaleFactor": 1})],
            "screenshot": [ok({"path": str(self.shot)})],
        }
        self._env = {k: os.environ.get(k) for k in ("PATH", "ORCA_FAKE")}
        os.environ["ORCA_FAKE"] = str(self.fakedir)
        os.environ["PATH"] = str(self.bin) + os.pathsep + os.environ["PATH"]
        self.addCleanup(self._restore)

    def _restore(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def run_cli(self, *argv):
        (self.fakedir / "cfg.json").write_text(json.dumps(self.cfg), encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = screens.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def calls(self) -> list[list[str]]:
        log = self.fakedir / "log.jsonl"
        if not log.exists():
            return []
        return [json.loads(ln)["argv"] for ln in log.read_text(encoding="utf-8").splitlines()]

    def keys(self) -> list[list[str]]:
        return [c[:2] if c[0] == "tab" else c[:1] for c in self.calls()]

    def capture(self, url="http://127.0.0.1:5173", w="800", h="600", out=None):
        out = out or self.tmp / "sub" / "captures" / "foto.running.png"
        return self.run_cli("capture", "--url", url, "--width", w, "--height", h, "--out", str(out)), out

    def test_capture_chama_orca_na_ordem(self):
        (rc, out, err), dest = self.capture()
        self.assertEqual(rc, 0, err)
        calls = self.calls()
        self.assertEqual(self.keys(), [["tab", "create"], ["exec"], ["screenshot"], ["tab", "close"]])
        self.assertIn("http://127.0.0.1:5173", calls[0])
        self.assertIn("--json", calls[0])
        self.assertEqual(calls[1][calls[1].index("--page") + 1], "p1")
        self.assertEqual(calls[1][calls[1].index("--command") + 1], "set viewport 800 600")
        self.assertEqual(calls[2][calls[2].index("--page") + 1], "p1")
        self.assertEqual(calls[3][calls[3].index("--page") + 1], "p1")
        self.assertEqual(dest.read_bytes(), self.shot.read_bytes())
        self.assertEqual(json.loads(out), {"out": str(dest), "width": 800, "height": 600})

    def test_capture_url_data_recusada(self):
        (rc, out, err), dest = self.capture(url="data:text/html,<h1>oi</h1>")
        self.assertEqual(rc, 2)
        self.assertIn("use uma URL http(s): a Orca não desenha páginas data:", err)
        self.assertEqual(self.calls(), [])
        self.assertFalse(dest.exists())

    def test_capture_url_nao_ancorada_recusada(self):
        for url in ("junkhttps://example.com", "https://", "https://exemplo.com lixo"):
            with self.subTest(url=url):
                (rc, out, err), dest = self.capture(url=url)
                self.assertEqual(rc, 2)
                self.assertIn("use uma URL http(s)", err)
                self.assertEqual(self.calls(), [])
                self.assertFalse(dest.exists())

    def test_capture_falha_fecha_aba(self):
        self.cfg["exec"] = [fail("viewport rejected")]
        (rc, out, err), dest = self.capture()
        self.assertEqual(rc, 1)
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("exec", err)
        self.assertIn("viewport rejected", err)
        self.assertEqual(self.calls()[-1][:2], ["tab", "close"])
        self.assertNotIn(["screenshot"], self.keys())
        self.assertFalse(dest.exists())

    def test_capture_orca_fora_do_path(self):
        os.environ["PATH"] = str(self.tmp / "vazio")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = screens.main(["capture", "--url", "http://localhost", "--width", "8", "--height", "6",
                               "--out", str(self.tmp / "captures" / "a.running.png")])
        self.assertEqual(rc, 1)
        self.assertIn("orca", err.getvalue())

    def test_capture_tamanho_errado_falha(self):
        self.shot.write_bytes(png(799, 600))
        (rc, out, err), dest = self.capture()
        self.assertEqual(rc, 1)
        self.assertIn("799x600", err)
        self.assertIn("800x600", err)
        self.assertEqual(self.calls()[-1][:2], ["tab", "close"])

    def test_capture_sem_frame_tenta_de_novo(self):
        msg = "Screenshot timed out — the browser page did not draw a frame."
        self.cfg["screenshot"] = [fail(msg), ok({"path": str(self.shot)})]
        (rc, out, err), dest = self.capture()
        self.assertEqual(rc, 0, err)
        self.assertEqual(self.keys(), [["tab", "create"], ["exec"], ["screenshot"], ["tab", "switch"],
                                       ["screenshot"], ["tab", "close"]])
        sw = self.calls()[3]
        self.assertEqual(sw[sw.index("--page") + 1], "p1")

    def test_capture_sem_frame_duas_vezes_falha(self):
        self.cfg["screenshot"] = [fail("did not draw a frame")]
        (rc, out, err), dest = self.capture()
        self.assertEqual(rc, 1)
        self.assertIn("a página não desenhou: deixe o navegador da Orca visível e tente de novo", err)
        self.assertEqual(self.keys().count(["screenshot"]), 2)
        self.assertEqual(self.calls()[-1][:2], ["tab", "close"])

    def test_size_imprime_css(self):
        img = self.tmp / "card@2x.png"
        img.write_bytes(png(1600, 1200))
        rc, out, err = self.run_cli("size", str(img))
        self.assertEqual(rc, 0, err)
        self.assertEqual(out.strip(), "1600x1200 @2x css 800x600")
        bad = self.tmp / "ruim.png"
        bad.write_bytes(b"nada")
        rc, out, err = self.run_cli("size", str(bad))
        self.assertEqual(rc, 1)
        self.assertEqual(out, "")

    def test_list_capturas_da_spec(self):
        fdir = self.tmp / "proj" / ".specs" / "features" / "demo"
        (fdir / "captures").mkdir(parents=True)
        (fdir / "captures" / "home@2x.png").write_bytes(png(1600, 1200))
        (fdir / "captures" / "home.running.png").write_bytes(png(800, 600))
        (fdir / "captures" / "extra.png").write_bytes(png(100, 100))
        (fdir / "spec.md").write_text(
            "# Demo: Spec\n\n**Status**: Approved\n\n## Requirements\n\n"
            "- **R1** - WHEN abre THEN the system SHALL mostrar `captures/home@2x.png`.\n"
            "- **R4** - WHEN volta THEN the system SHALL mostrar de novo `captures/home@2x.png`.\n\n"
            "## Sources\n\n"
            "- ![home](captures/home@2x.png) - binding - tela inicial\n"
            "- ![extra](captures/extra.png) - non-binding - user: \"só referência\"\n",
            encoding="utf-8")
        rc, out, err = self.run_cli("list", "demo", "--root", str(self.tmp / "proj"))
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out), [{
            "capture": ".specs/features/demo/captures/home@2x.png",
            "running": ".specs/features/demo/captures/home.running.png",
            "exists": True,
            "px": [1600, 1200],
            "scale": 2,
            "css": [800, 600],
            "requirements": ["R1", "R4"],
        }])

    def test_list_sem_capturas(self):
        fdir = self.tmp / "proj" / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n\n## Requirements\n", encoding="utf-8")
        rc, out, err = self.run_cli("list", "demo", "--root", str(self.tmp / "proj"))
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out), [])


if __name__ == "__main__":
    unittest.main()
