"""screens.py: fotos de tela pela Orca, tamanho de imagem e lista de capturas vinculantes (F11-4).

    python screens.py capture --url <http(s)://...> --width L --height A --out <arquivo.png>
    python screens.py size <imagem>
    python screens.py list <slug> [--root DIR]

`capture` abre uma aba no navegador da Orca, fixa o viewport, tira o screenshot, copia o PNG
para `--out` e fecha a aba. Exit: 0 ok, 1 falha (uma linha com o passo e o motivo), 2 uso.
Só a stdlib e o CLI `orca` (chamado sem shell, sem stdin, com tempo limite de 60 s).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "gates"))

import gates_common as gc  # noqa: E402
import images  # noqa: E402
import validate_verification as vv  # noqa: E402

TIMEOUT = 60
NO_FRAME = "did not draw a frame"
NO_FRAME_MSG = "a página não desenhou: deixe o navegador da Orca visível e tente de novo"


class ScreenError(Exception):
    """Falha de um passo: a mensagem é a linha impressa (`<passo>: <motivo>`)."""


def _one_line(text: str) -> str:
    return " ".join(str(text).split())


def _orca(step: str, args: list[str]) -> dict:
    exe = shutil.which("orca")
    if not exe:
        raise ScreenError(f"{step}: o CLI `orca` não está no PATH")
    try:
        res = subprocess.run([exe, *args], stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        raise ScreenError(f"{step}: tempo esgotado ({TIMEOUT} s)") from None
    except OSError as exc:
        raise ScreenError(f"{step}: não foi possível rodar o `orca` ({exc.strerror or exc})") from None
    stdout = (res.stdout or "").strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except ValueError:
        data = None
    failed = res.returncode != 0 or (isinstance(data, dict) and data.get("ok") is False)
    if failed:
        reason = ""
        if isinstance(data, dict):
            err = data.get("error")
            reason = err.get("message", "") if isinstance(err, dict) else (err or "")
        reason = reason or (res.stderr or "").strip() or stdout or f"saiu com {res.returncode}"
        raise ScreenError(f"{step}: {_one_line(reason)}")
    if not isinstance(data, dict):
        raise ScreenError(f"{step}: resposta do `orca` não é JSON")
    return data


def _result(data: dict) -> dict:
    r = data.get("result")
    return r if isinstance(r, dict) else {}


def _screenshot(page: str) -> str:
    data = _orca("screenshot", ["screenshot", "--page", page, "--json"])
    path = _result(data).get("path")
    if not path:
        raise ScreenError("screenshot: a Orca não devolveu o caminho do PNG")
    return str(path)


def capture(url: str, width: int, height: int, out: Path) -> dict:
    page = None
    try:
        data = _orca("tab create", ["tab", "create", "--url", url, "--json"])
        page = _result(data).get("browserPageId")
        if not page:
            raise ScreenError("tab create: a Orca não devolveu browserPageId")
        page = str(page)
        _orca("exec", ["exec", "--page", page, "--command", f"set viewport {width} {height}", "--json"])
        try:
            shot = _screenshot(page)
        except ScreenError as exc:
            if NO_FRAME not in str(exc):
                raise
            _orca("tab switch", ["tab", "switch", "--page", page, "--json"])
            try:
                shot = _screenshot(page)
            except ScreenError as exc2:
                if NO_FRAME not in str(exc2):
                    raise
                raise ScreenError(NO_FRAME_MSG) from None
        out.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(shot, out)
        except OSError as exc:
            raise ScreenError(f"copiar: {exc.strerror or exc}") from None
        try:
            got = images.image_size(out)
        except images.ImageError as exc:
            out.unlink(missing_ok=True)
            raise ScreenError(f"screenshot: {exc}") from None
        if got != (width, height):
            out.unlink(missing_ok=True)
            raise ScreenError(f"screenshot: o PNG tem {got[0]}x{got[1]} e o pedido era {width}x{height}")
        return {"out": str(out), "width": width, "height": height}
    finally:
        if page:
            try:
                _orca("tab close", ["tab", "close", "--page", page, "--json"])
            except ScreenError:
                pass


def list_screens(slug: str, root: Path) -> list[dict]:
    fdir = gc.resolve_feature(slug, root, "spec.md")
    res = gc.Result("screens")
    caps = vv._binding_captures(fdir, res)
    if res.errors:
        raise ScreenError("; ".join(res.errors))
    lines = gc.read_lines(fdir / "spec.md")
    reqs = [ln.strip() for ln in (gc.section(lines, "Requirements") or []) if gc.REQ_LINE_RE.match(ln.strip())]
    base = root.resolve()

    def rel(p: Path) -> str:
        try:
            return p.resolve().relative_to(base).as_posix()
        except ValueError:
            return p.as_posix()

    out = []
    for cap in caps:
        run = images.running_path(cap)
        cited = re.compile(rf"`(?:[^`]*/)?captures/{re.escape(cap.name)}`")
        ids = [m.group(1) for r in reqs if cited.search(r)
               for m in [re.match(r"[-*]?\s*\*\*(R\d+)\*\*", r)] if m]
        px = images.image_size(cap)
        out.append({
            "capture": rel(cap),
            "running": rel(run),
            "exists": run.is_file(),
            "px": list(px),
            "scale": images.capture_scale(cap.name),
            "css": list(images.css_size(cap)),
            "requirements": ids,
        })
    return out


def _die(msg: str, code: int) -> int:
    print(msg, file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="screens.py", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--url", required=True)
    c.add_argument("--width", type=int, required=True)
    c.add_argument("--height", type=int, required=True)
    c.add_argument("--out", required=True)
    s = sub.add_parser("size")
    s.add_argument("image")
    ls = sub.add_parser("list")
    ls.add_argument("slug")
    ls.add_argument("--root", default=".")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "capture":
            if not re.match(r"https?://", args.url):
                return _die("use uma URL http(s): a Orca não desenha páginas data:", 2)
            if args.width <= 0 or args.height <= 0:
                return _die("use --width e --height positivos", 2)
            print(json.dumps(capture(args.url, args.width, args.height, Path(args.out)), ensure_ascii=False))
        elif args.cmd == "size":
            w, h = images.image_size(args.image)
            k = images.capture_scale(Path(args.image).name)
            print(f"{w}x{h} @{k}x css {w // k}x{h // k}")
        else:
            print(json.dumps(list_screens(args.slug, Path(args.root)), ensure_ascii=False, indent=2))
    except (ScreenError, images.ImageError, LookupError) as exc:
        return _die(_one_line(exc), 1)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    sys.exit(main())
