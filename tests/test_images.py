"""Testes de scripts/gates/images.py (R11, R12)."""
from __future__ import annotations

import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from helpers import TempRepoCase  # noqa: F401  (ajusta sys.path para scripts/gates)

import images


def png_bytes(w: int, h: int) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def jpeg_bytes(w: int, h: int) -> bytes:
    def seg(marker: int, data: bytes) -> bytes:
        return bytes([0xFF, marker]) + struct.pack(">H", len(data) + 2) + data

    sof = struct.pack(">BHHB", 8, h, w, 1) + b"\x01\x11\x00"
    return (b"\xff\xd8" + seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
            + seg(0xC4, b"\x00" * 17) + seg(0xC2, sof) + b"\xff\xd9")


def webp_bytes(kind: str, w: int, h: int) -> bytes:
    if kind == "VP8 ":
        payload = b"\x00\x00\x00" + b"\x9d\x01\x2a" + struct.pack("<HH", w, h)
    elif kind == "VP8L":
        bits = (w - 1) | ((h - 1) << 14)
        payload = b"\x2f" + struct.pack("<I", bits)
    else:
        payload = (b"\x00\x00\x00\x00" + (w - 1).to_bytes(3, "little")
                   + (h - 1).to_bytes(3, "little"))
    body = b"WEBP" + kind.encode() + struct.pack("<I", len(payload)) + payload
    if len(payload) % 2:
        body += b"\x00"
    return b"RIFF" + struct.pack("<I", len(body)) + body


class ImagesCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name: str, data: bytes = b"") -> Path:
        p = self.dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p


class ImageTests(ImagesCase):
    def test_image_size_png(self):
        self.assertEqual(images.image_size(self.write("a.png", png_bytes(7, 5))), (7, 5))

    def test_image_size_jpeg(self):
        self.assertEqual(images.image_size(self.write("a.jpg", jpeg_bytes(30, 20))), (30, 20))

    def test_image_size_webp_variantes(self):
        for kind in ("VP8 ", "VP8L", "VP8X"):
            p = self.write(f"w{kind.strip()}.webp", webp_bytes(kind, 321, 123))
            self.assertEqual(images.image_size(p), (321, 123), kind)

    def test_image_size_ilegivel(self):
        casos = {
            "ausente.png": None,
            "vazio.png": b"",
            "texto.png": b"isto nao e imagem",
            "gif.gif": b"GIF89a" + b"\x00" * 20,
            "png_curto.png": png_bytes(2, 2)[:20],
            "jpeg_sem_sof.jpg": b"\xff\xd8\xff\xe0\x00\x04\x00\x00\xff\xd9",
        }
        for nome, dados in casos.items():
            p = self.dir / nome
            if dados is not None:
                p.write_bytes(dados)
            with self.assertRaises(images.ImageError) as cm:
                images.image_size(p)
            self.assertIn(nome, str(cm.exception))

    def test_capture_scale_e_css(self):
        self.assertEqual(images.capture_scale("home.png"), 1)
        self.assertEqual(images.capture_scale("home@2x.png"), 2)
        self.assertEqual(images.capture_scale(Path("x/home@3x.JPG")), 3)
        p = self.write("home@2x.png", png_bytes(40, 20))
        self.assertEqual(images.css_size(p), (20, 10))
        q = self.write("outra.png", png_bytes(40, 20))
        self.assertEqual(images.css_size(q), (40, 20))

    def test_same_css_1x_2x_3x(self):
        self.assertTrue(images.same_css((100, 50), (100, 50)))
        self.assertTrue(images.same_css((200, 100), (100, 50)))
        self.assertTrue(images.same_css((300, 150), (100, 50)))
        self.assertFalse(images.same_css((201, 100), (100, 50)))
        self.assertFalse(images.same_css((400, 200), (100, 50)))
        self.assertFalse(images.same_css((100, 50), (200, 100)))

    def test_list_captures_ignora_running_e_duplicadas(self):
        fdir = self.dir / "feat"
        for n in ("a.png", "b@2x.PNG", "c.jpeg", "d.webp", "a.running.png", "notas.txt"):
            self.write(f"feat/captures/{n}")
        nomes = [p.name for p in images.list_captures(fdir)]
        self.assertEqual(nomes, ["a.png", "b@2x.PNG", "c.jpeg", "d.webp"])
        self.assertEqual(images.running_path(fdir / "captures" / "b@2x.PNG").name, "b.running.png")
        self.write("feat/captures/a@2x.png")
        with self.assertRaises(images.ImageError) as cm:
            images.list_captures(fdir)
        self.assertIn("duas capturas para `a.running.png`", str(cm.exception))
        self.assertEqual(images.list_captures(self.dir / "vazia"), [])
