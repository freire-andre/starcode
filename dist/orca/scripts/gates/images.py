"""images.py: leitura de tamanho de imagem e regras de captura, só com a stdlib.

Adapted from tlc-spec-driven `scripts/validate_verification.py` (`_image_size`, `_same_layout`;
Felipe Rodrigues, github.com/felipfr, CC-BY-4.0).
Changes: StarCode layout (`<feature>/captures/`), escala pelo nome (`@2x`/`@3x`), tamanho em CSS,
`ImageError` com mensagens em PT-BR no lugar de retornar None.

Usado pelos gates e por scripts/screens.py. Nunca lança outra coisa além de ImageError.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

EXTENSOES = {".png", ".jpg", ".jpeg", ".webp"}
_ESCALA = re.compile(r"@([23])x$", re.IGNORECASE)


class ImageError(Exception):
    """Imagem ausente, ilegível ou fora de PNG/JPEG/WebP (a mensagem traz o caminho)."""


def _erro(path, motivo: str) -> ImageError:
    return ImageError(f"{Path(path).as_posix()}: {motivo}")


def image_size(path) -> tuple[int, int]:
    p = Path(path)
    try:
        data = p.read_bytes()
    except FileNotFoundError:
        raise _erro(p, "arquivo não encontrado") from None
    except OSError as exc:
        raise _erro(p, f"não foi possível ler o arquivo ({exc.strerror or exc})") from None
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            size = _png(data)
        elif data[:2] == b"\xff\xd8":
            size = _jpeg(data)
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            size = _webp(data)
        else:
            raise _erro(p, "formato não suportado (use PNG, JPEG ou WebP)")
    except (struct.error, IndexError):
        raise _erro(p, "cabeçalho da imagem ilegível") from None
    except ImageError as exc:
        if str(exc).startswith(p.as_posix()):
            raise
        raise _erro(p, str(exc)) from None
    if size[0] <= 0 or size[1] <= 0:
        raise _erro(p, "cabeçalho da imagem ilegível (tamanho zero)")
    return size


def _png(data: bytes) -> tuple[int, int]:
    if data[12:16] != b"IHDR":
        raise ImageError("cabeçalho PNG ilegível (IHDR ausente)")
    return struct.unpack(">II", data[16:24])


def _jpeg(data: bytes) -> tuple[int, int]:
    i, n = 2, len(data)
    while i + 4 <= n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker == 0xFF:  # preenchimento
            i += 1
            continue
        if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:  # sem tamanho
            i += 2
            continue
        if marker == 0xD9:
            break
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ImageError("cabeçalho JPEG ilegível (marcador SOF ausente)")


def _webp(data: bytes) -> tuple[int, int]:
    kind = data[12:16]
    if kind == b"VP8 ":
        if data[23:26] != b"\x9d\x01\x2a":
            raise ImageError("cabeçalho WebP ilegível (VP8 sem assinatura)")
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        if data[20] != 0x2F:
            raise ImageError("cabeçalho WebP ilegível (VP8L sem assinatura)")
        bits = struct.unpack("<I", data[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8X":
        w = int.from_bytes(data[24:27], "little") + 1
        h = int.from_bytes(data[27:30], "little") + 1
        return w, h
    raise ImageError("WebP não suportado (variante desconhecida)")


def capture_scale(nome) -> int:
    stem = Path(str(nome)).stem
    m = _ESCALA.search(stem)
    return int(m.group(1)) if m else 1


def css_size(path) -> tuple[int, int]:
    w, h = image_size(path)
    k = capture_scale(Path(path).name)
    return w // k, h // k


def running_path(capture) -> Path:
    p = Path(capture)
    base = _ESCALA.sub("", p.stem)
    return p.with_name(f"{base}.running.png")


def same_css(running_px, capture_css) -> bool:
    rw, rh = running_px
    cw, ch = capture_css
    return any(rw == cw * k and rh == ch * k for k in (1, 2, 3))


def list_captures(fdir) -> list[Path]:
    cdir = Path(fdir) / "captures"
    if not cdir.is_dir():
        return []
    found = sorted(
        (p for p in cdir.iterdir()
         if p.is_file() and p.suffix.lower() in EXTENSOES
         and not p.name.lower().endswith(".running.png")),
        key=lambda p: p.name,
    )
    seen: dict[str, Path] = {}
    for p in found:
        run = running_path(p).name
        if run in seen:
            raise ImageError(f"duas capturas para `{run}`: "
                             f"{seen[run].name} e {p.name}")
        seen[run] = p
    return found
