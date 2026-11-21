"""Testes de restauracao-e-telas (SC-210): restore pelo snapshot, capture restrito, veredito e IDAT."""
from __future__ import annotations

import contextlib
import io
import re
import struct
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

from helpers import ROOT  # noqa: F401  (ajusta sys.path)

import gates_common as gc
import images
import screens
import snapshot
import validate_verification as vv
from test_images import png_bytes


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def png_sem_idat(w: int, h: int, iend: bool = True) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    return out + (chunk(b"IEND", b"") if iend else b"")


def spec_md(may: str) -> str:
    return f"# Feat: Spec\n\n## Scope\n- x\n\n**May change**: {may}\n"


def arvore(root: Path) -> dict[str, bytes]:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        if p.is_file() and not rel.startswith(".git/"):
            out[rel] = p.read_bytes()
    return out


SPEC_TELA = """# Demo: Spec

## Requirements

- **R1** - WHEN o usuário abre o app THEN the system SHALL mostrar a tela de `captures/login.png`.

## Sources

- ![login](captures/login.png) - binding - tela de login
"""


class RestauracaoETelasTests(unittest.TestCase):
    # ---- R1 ----
    def repo(self):
        tmp = tempfile.TemporaryDirectory(prefix="starcode-sc210-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        git(root, "init", "-q")
        git(root, "config", "user.name", "T")
        git(root, "config", "user.email", "t@example.com")
        git(root, "config", "commit.gpgsign", "false")
        (root / "a.txt").write_text("a\n")
        (root / "b.txt").write_text("b\n")
        return root

    def cli(self, root, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = snapshot.main([*args, "--root", str(root)])
        return code, out.getvalue()

    def test_restore_le_escopo_do_snapshot(self):
        root = self.repo()
        fdir = root / ".specs" / "features" / "feat"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(spec_md("a.txt"))
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "init")
        (root / "a.txt").write_text("a do snapshot\n")
        (root / "b.txt").write_text("b do snapshot\n")
        self.assertEqual(self.cli(root, "take", "feat", "SC-1")[0], 0)
        # depois do snapshot o escopo cresce na árvore e os dois arquivos mudam
        (fdir / "spec.md").write_text(spec_md("a.txt, b.txt"))
        (root / "a.txt").write_text("a da arvore\n")
        (root / "b.txt").write_text("b da arvore\n")

        code, out = self.cli(root, "restore", "feat", "SC-1")
        self.assertEqual(code, 0)
        self.assertEqual(out, "plano feat/SC-1 (May change: a.txt)\n"
                              "  voltar   a.txt\n"
                              "fora do ticket (não tocados):\n"
                              "  .specs/features/feat/spec.md\n"
                              "  b.txt\n"
                              "nada foi alterado: rode de novo com --yes depois da confirmação do usuário\n")
        code, out = self.cli(root, "restore", "feat", "SC-1", "--yes")
        self.assertEqual(code, 0)
        self.assertEqual((root / "a.txt").read_text(), "a do snapshot\n")
        self.assertEqual((root / "b.txt").read_text(), "b da arvore\n")

    def test_restore_prefere_tasks_do_snapshot(self):
        root = self.repo()
        fdir = root / ".specs" / "features" / "feat"
        fdir.mkdir(parents=True)
        tasks = ("# Feat: Tasks\n\n## Tasks\n\n### T1: x\n\n**Depends on**: none\n\n#### BOUNDARIES\n"
                 "- May change: `{}`\n")
        (fdir / "tasks.md").write_text(tasks.format("a.txt"))
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "init")
        (root / "a.txt").write_text("a do snapshot\n")
        self.cli(root, "take", "feat", "T1")
        (fdir / "tasks.md").write_text(tasks.format("a.txt`, `b.txt"))
        (root / "a.txt").write_text("a da arvore\n")
        (root / "b.txt").write_text("b da arvore\n")
        _, out = self.cli(root, "restore", "feat", "T1")
        self.assertTrue(out.startswith("plano feat/T1 (May change: a.txt)\n  voltar   a.txt\n"), out)

    def test_restore_snapshot_sem_artefato_sai_2(self):
        root = self.repo()
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "init")
        (root / "a.txt").write_text("a do snapshot\n")
        self.cli(root, "take", "feat", "SC-1")
        # a árvore ganha spec.md depois do snapshot: não pode ser lida
        fdir = root / ".specs" / "features" / "feat"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(spec_md("a.txt"))
        (root / "a.txt").write_text("a da arvore\n")
        antes = (arvore(root), git(root, "for-each-ref"), git(root, "status", "--porcelain"))
        for extra in ((), ("--yes",)):
            code, out = self.cli(root, "restore", "feat", "SC-1", *extra)
            self.assertEqual(code, 2)
            self.assertEqual(out, "snapshot sem tasks.md nem spec.md de feat: restauração recusada\n")
            self.assertEqual(antes, (arvore(root), git(root, "for-each-ref"), git(root, "status", "--porcelain")))

    # ---- R2 e R3 ----
    def run_capture(self, url, out, *extra):
        err = io.StringIO()
        with mock.patch.object(screens, "capture", return_value={"ok": 1}) as cap, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = screens.main(["capture", "--url", url, "--width", "10", "--height", "10", "--out", out, *extra])
        return code, err.getvalue(), cap

    def test_capture_so_host_local(self):
        out = "captures/x.running.png"
        passam = [("http://localhost:3000/", ()), ("http://127.0.0.1:5173/a", ()), ("http://[::1]:8080/", ()),
                  ("http://app.localhost/", ()), ("http://LOCALHOST:3000/", ()),
                  ("https://Exemplo.com/", ("--allow-host", "exemplo.com")),
                  ("http://a.com/", ("--allow-host", "b.com", "--allow-host", "a.com"))]
        for url, extra in passam:
            with self.subTest(url=url):
                code, err, cap = self.run_capture(url, out, *extra)
                self.assertEqual((code, err), (0, ""))
                cap.assert_called_once()
        recusam = [("http://example.com/", "example.com"), ("http://localhost.evil.com/", "localhost.evil.com"),
                   ("http://evil.com/?h=localhost", "evil.com"), ("http://notlocalhost/", "notlocalhost"),
                   ("http://user@evil.com:80/", "evil.com")]
        for url, host in recusam:
            with self.subTest(url=url):
                code, err, cap = self.run_capture(url, out)
                self.assertEqual(code, 2)
                self.assertEqual(err, f"host fora do padrão local: {host} (use --allow-host {host} para liberar)\n")
                cap.assert_not_called()

    def test_capture_out_restrito(self):
        url = "http://localhost:3000/"
        code, err, cap = self.run_capture(url, "captures/x.running.png")
        self.assertEqual((code, err), (0, ""))
        cap.assert_called_once()
        for bad in ("captures/x.png", "outro/x.running.png", "x.running.png", "captures/.running.png"):
            with self.subTest(out=bad):
                code, err, cap = self.run_capture(url, bad)
                self.assertEqual(code, 2)
                self.assertEqual(err, f"--out precisa ser captures/<nome>.running.png: {bad}\n")
                cap.assert_not_called()

    # ---- R4 e R5 ----
    def feature(self, rows: list[str], running: bytes | None = None):
        tmp = tempfile.TemporaryDirectory(prefix="starcode-sc210-feat-")
        self.addCleanup(tmp.cleanup)
        fdir = Path(tmp.name) / ".specs" / "features" / "demo"
        (fdir / "captures").mkdir(parents=True)
        (fdir / "spec.md").write_text(SPEC_TELA, encoding="utf-8")
        (fdir / "captures" / "login.png").write_bytes(png_bytes(10, 10))
        (fdir / "captures" / "login.running.png").write_bytes(running or png_bytes(10, 10))
        table = "".join(f"| {r} | `captures/login.png` | match | - |\n" for r in rows)
        (fdir / "screens.md").write_text(
            "# Demo screens\n\n**Verifier**: codex · requested gpt · effective gpt\n**Round**: 1\n"
            "**Pictures**: running\n\n| Screen | Compared with | Verdict | Finding |\n| --- | --- | --- | --- |\n"
            + table, encoding="utf-8")
        return fdir

    def erros_telas(self, fdir):
        res = gc.Result("t")
        vv._check_screens(fdir, False, res)
        return res.errors

    def test_veredito_nome_inteiro(self):
        sem = "screens.md sem veredito para `login.png`"
        self.assertIn(sem, self.erros_telas(self.feature(["`captures/admin-login.running.png`"])))
        self.assertIn(sem, self.erros_telas(self.feature(["`captures/admin-login.png`"])))
        self.assertNotIn(sem, self.erros_telas(self.feature(["`captures/login.running.png`"])))
        self.assertNotIn(sem, self.erros_telas(self.feature(["`captures/login.png`"])))
        self.assertEqual(self.erros_telas(self.feature(["`captures/login.running.png`"])), [])
        erros = self.erros_telas(self.feature(["`captures/admin-login.running.png`"]))
        self.assertEqual(erros, [sem])

    def test_png_sem_idat(self):
        with tempfile.TemporaryDirectory(prefix="starcode-sc210-png-") as tmp:
            for nome, data in (("so-cabecalho.png", png_sem_idat(4, 4, iend=False)),
                               ("com-iend.png", png_sem_idat(4, 4))):
                p = Path(tmp) / nome
                p.write_bytes(data)
                with self.subTest(nome=nome):
                    with self.assertRaises(images.ImageError) as ctx:
                        images.image_size(p)
                    self.assertEqual(str(ctx.exception), f"{p.as_posix()}: PNG sem dados de imagem (nenhum IDAT)")
            ok = Path(tmp) / "ok.png"
            ok.write_bytes(png_bytes(7, 5))
            self.assertEqual(images.image_size(ok), (7, 5))
        # regra compartilhada: o gate de veredito recusa a foto sem IDAT pelo mesmo caminho
        fdir = self.feature(["`captures/login.running.png`"], running=png_sem_idat(10, 10))
        run = fdir / "captures" / "login.running.png"
        self.assertEqual(self.erros_telas(fdir), [f"{run.as_posix()}: PNG sem dados de imagem (nenhum IDAT)"])

    def test_png_idat_truncado_ou_vazio(self):
        def chunk(tag, data):
            return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

        base = png_sem_idat(4, 4, iend=False)
        idat = chunk(b"IDAT", zlib.compress(b"\x00" * 13))
        tabela = (
            ("ihdr-so.png", base, "PNG sem dados de imagem (nenhum IDAT)"),
            ("idat-cabecalho.png", base + struct.pack(">I", 100) + b"IDAT", "PNG truncado (chunk IDAT incompleto)"),
            ("idat-sem-crc.png", base + idat[:-4], "PNG truncado (chunk IDAT incompleto)"),
            ("idat-meio.png", base + idat[:-6], "PNG truncado (chunk IDAT incompleto)"),
            ("idat-zero.png", base + chunk(b"IDAT", b"") + chunk(b"IEND", b""),
             "PNG sem dados de imagem (nenhum IDAT)"),
            ("idat-ok.png", base + idat + chunk(b"IEND", b""), None),
        )
        with tempfile.TemporaryDirectory(prefix="starcode-sc210-idat-") as tmp:
            for nome, data, msg in tabela:
                p = Path(tmp) / nome
                p.write_bytes(data)
                with self.subTest(nome=nome):
                    if msg is None:
                        self.assertEqual(images.image_size(p), (4, 4))
                    else:
                        with self.assertRaises(images.ImageError) as ctx:
                            images.image_size(p)
                        self.assertEqual(str(ctx.exception), f"{p.as_posix()}: {msg}")

    # ---- R6 ----
    def test_decisions_e_changelog(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-210:.*?(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        entry = m.group(0)
        partes = {k: re.search(rf"^- \*\*{k}\*\*: (.*)$", entry, re.M) for k in
                  ("Problema", "Decisão", "Motivo", "Por que não é bug")}
        for k, v in partes.items():
            self.assertIsNotNone(v, k)
            self.assertTrue(v.group(1).strip(), k)
        decisao = partes["Decisão"].group(1)
        termos = ["git show", "tasks.md", "spec.md", "snapshot sem tasks.md nem spec.md de", "sai com 2",
                  "localhost", "127.0.0.1", "[::1]", ".localhost", "--allow-host", "host fora do padrão local",
                  "captures/<nome>.running.png", "--out precisa ser", "nome inteiro", "admin-login.running.png",
                  "IDAT", "PNG sem dados de imagem", "PNG truncado (chunk <tipo> incompleto)", "comprimento maior que zero"]
        for t in termos:
            self.assertIn(t, decisao, t)
        porque = partes["Por que não é bug"].group(1)
        for t in ("test_restore_le_escopo_do_snapshot", "test_capture_so_host_local", "test_capture_out_restrito",
                  "test_veredito_nome_inteiro", "test_png_sem_idat", "test_png_idat_truncado_ou_vazio", "test_decisions_e_changelog"):
            self.assertIn(t, porque, t)
        change = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = re.search(r"^## \[Unreleased\](.*?)(?=^## \[)", change, re.M | re.S).group(1)
        self.assertEqual(len([ln for ln in unreleased.splitlines() if ln.startswith("- ") and "(SC-210)" in ln]), 1)


if __name__ == "__main__":
    unittest.main()
