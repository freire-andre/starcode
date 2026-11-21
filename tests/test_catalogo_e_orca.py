"""SC-211: catálogo conferido (model_info) e adaptador único da Orca (orca_cli)."""
from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT

import banner
import dispatch
import model_info as mi
import orca_cli
import screens

FAKE = """\
import json, os, sys
cfg = json.load(open(os.environ["ORCA_FAKE_CFG"], encoding="utf-8"))
mode = cfg["mode"]
if mode == "ok":
    print(json.dumps({"ok": True, "result": {"x": 1}}))
elif mode == "okfalse":
    print(json.dumps({"ok": False, "error": {"message": "falhou aqui"}}))
elif mode == "erro-texto":
    print(json.dumps({"ok": False, "error": "erro em texto"}))
    sys.exit(1)
elif mode == "stderr":
    sys.stderr.write("\\n  quebrou no stderr  \\n")
    sys.exit(2)
elif mode == "stdout":
    sys.stdout.write("  so stdout  \\n")
    sys.exit(3)
elif mode == "mudo":
    sys.exit(4)
elif mode.startswith("sai"):
    sys.exit(int(mode[3:]))
elif mode == "lista":
    print("[1, 2]")
elif mode == "env":
    print(json.dumps({"ok": True, "env": sorted(os.environ), "cwd": os.getcwd()}))
"""

PROBE = """\
import shutil
x = shutil.which ( "orca")  # which("orca") em comentário
y = "shutil.which('orca')"
z = which("orca.cmd")
"""

FORBIDDEN = ("NODE_OPTIONS", "NODE_PATH", "ELECTRON_RUN_AS_NODE", "ORCA_NODE_OPTIONS", "ORCA_CLI_COMMAND")


def provider_catalog() -> dict:
    return {"acme": {"models": {"m1": {"name": "M1", "cost": {"input": 1, "output": 2}, "tool_call": True}}}}


def fake_response(payload) -> mock.MagicMock:
    resp = mock.MagicMock()
    resp.__enter__.return_value.read.return_value = json.dumps(payload).encode()
    return resp


class CatalogoEOrcaTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-sc211-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        patcher = mock.patch.dict(os.environ, {"STARCODE_HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        os.environ.pop("STARCODE_MODELS_DEV_FILE", None)
        mi._CATALOG.clear()
        self.addCleanup(mi._CATALOG.clear)

    # --- fake orca --------------------------------------------------------------------------
    def fake_orca(self, mode: str) -> Path:
        d = self.tmp / "bin"
        d.mkdir(exist_ok=True)
        script = d / "fake_orca.py"
        script.write_text(FAKE, encoding="utf-8")
        cfg = self.tmp / "cfg.json"
        cfg.write_text(json.dumps({"mode": mode}), encoding="utf-8")
        if os.name == "nt":
            (d / "orca.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
        else:
            exe = d / "orca"
            exe.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
            exe.chmod(0o755)
        patcher = mock.patch.dict(os.environ, {"PATH": str(d), "ORCA_FAKE_CFG": str(cfg)})
        patcher.start()
        self.addCleanup(patcher.stop)
        return d

    def files(self, d: Path) -> dict:
        return {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in sorted(d.iterdir())}

    # --- C1 ---------------------------------------------------------------------------------
    def test_download_confere_forma(self):
        dest = self.tmp / "cache" / "models-dev.json"
        dest.parent.mkdir()
        dest.write_bytes(b'{"antigo": {"models": {}}}')
        os.utime(dest, (1_000_000, 1_000_000))
        bad = [{}, {"p": {}}, {"p": {"name": "x"}}, {"p": {"models": []}}, {"p": {"models": "x"}},
               {"p": {"models": None}}, {"p": []}, {"p": "x"}, {"p": None}]
        for payload in bad:
            before = self.files(dest.parent)
            with mock.patch.object(mi.urllib.request, "urlopen", return_value=fake_response(payload)):
                self.assertIsNone(mi.download(dest), payload)
            self.assertEqual(self.files(dest.parent), before, payload)
        good = {"p": {"models": {}}, "outro": 3}
        with mock.patch.object(mi.urllib.request, "urlopen", return_value=fake_response(good)):
            self.assertEqual(mi.download(dest), good)
        self.assertEqual(json.loads(dest.read_bytes()), good)
        self.assertEqual(sorted(x.name for x in dest.parent.iterdir()), ["models-dev.json"])

    # --- C2 ---------------------------------------------------------------------------------
    def test_texto_do_catalogo_limpo(self):
        name = "Mo\x1b[31mdelo\r\n  X\t\x00Y" + "n" * 200
        desc = "linha1\n\n  linha2\x1b[0m\x07​" + "d" * 300
        catalog = {"acme": {"models": {"m1": {"name": name, "description": desc, "tool_call": True,
                                              "cost": {"input": 1, "output": 2}}}}}
        want_name = ("Mo[31mdelo X Y" + "n" * 200)[:80]
        want_desc = ("linha1 linha2[0m" + "d" * 300)[:200]
        self.assertEqual(len(want_name), 80)
        self.assertEqual(len(want_desc), 200)
        card = mi.info(catalog, "acme/m1")
        self.assertEqual(card["name"], want_name)
        self.assertEqual(card["description"], want_desc)
        lines = mi.render(card).split("\n")
        self.assertEqual(lines[0], f"🔎 {want_name} (acme/m1)")
        self.assertEqual(lines[2], f"   {want_desc}")
        rlines = mi.render(dict(card, name=name, description=desc)).split("\n")
        self.assertEqual(rlines[0], f"🔎 {want_name} (acme/m1)")
        self.assertEqual(rlines[2], f"   {want_desc}")
        path = self.tmp / "cat.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(path)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(mi.main(["--offline", "--json", "acme/m1"]), 0)
        data = json.loads(out.getvalue())
        self.assertEqual((data[0]["name"], data[0]["description"]), (want_name, want_desc))
        self.assertNotIn("\x1b", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(mi.main(["--offline", "acme/m1"]), 0)
        self.assertEqual(out.getvalue().split("\n")[0], f"🔎 {want_name} (acme/m1)")
        self.assertNotIn("\x1b", out.getvalue())

    # --- C3 ---------------------------------------------------------------------------------
    def test_catalogo_lido_uma_vez(self):
        path = self.tmp / "cat.json"
        path.write_text(json.dumps(provider_catalog()), encoding="utf-8")
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(path)
        with mock.patch.object(mi, "_read", wraps=mi._read) as spy:
            first = mi.load_catalog()
            self.assertEqual(first, provider_catalog())
            self.assertEqual(mi.cached_family("acme/m1"), "unknown")
            self.assertEqual(mi.cached_tier("acme/m1"), "$$")
            self.assertIs(mi.load_catalog(fetch=False), first)
            self.assertEqual(spy.call_count, 1)
        novo = {"acme": {"models": {"m2": {"name": "M2", "cost": {"output": 20}}}}}
        with mock.patch.object(mi.urllib.request, "urlopen", return_value=fake_response(novo)):
            self.assertEqual(mi.download(path), novo)
        with mock.patch.object(mi, "_read", wraps=mi._read) as spy:
            self.assertEqual(mi.load_catalog(), novo)
            self.assertEqual(mi.cached_tier("acme/m2"), "$$$")
            self.assertIsNone(mi.cached_tier("acme/m1"))
            self.assertEqual(spy.call_count, 0)
        # origem do cache: lido uma vez; o download atualiza
        os.environ.pop("STARCODE_MODELS_DEV_FILE")
        mi._CATALOG.clear()
        cache = mi.cache_path()
        cache.parent.mkdir(parents=True)
        cache.write_text(json.dumps(provider_catalog()), encoding="utf-8")
        with mock.patch.object(mi, "_read", wraps=mi._read) as spy:
            mi.load_catalog(fetch=False)
            mi.cached_family("acme/m1")
            mi.cached_tier("acme/m1")
            self.assertEqual(spy.call_count, 1)
        with mock.patch.object(mi.urllib.request, "urlopen", return_value=fake_response(novo)):
            self.assertEqual(mi.download(), novo)
        self.assertEqual(mi.load_catalog(fetch=False), novo)
        self.assertEqual(mi.cached_tier("acme/m2"), "$$$")

        # origem inválida: também interpretada uma vez; o download ainda atualiza
        mi._CATALOG.clear()
        cache.write_text("{invalido", encoding="utf-8")
        with mock.patch.object(mi, "_read", wraps=mi._read) as spy:
            self.assertIsNone(mi.load_catalog(fetch=False))
            self.assertIsNone(mi.load_catalog(fetch=False))
            self.assertIsNone(mi.cached_tier("acme/m1"))
            self.assertEqual(spy.call_count, 1)
        with mock.patch.object(mi.urllib.request, "urlopen", return_value=fake_response(novo)):
            self.assertEqual(mi.download(), novo)
        self.assertEqual(mi.load_catalog(fetch=False), novo)
        bad = self.tmp / "ruim.json"
        bad.write_text("{invalido", encoding="utf-8")
        os.environ["STARCODE_MODELS_DEV_FILE"] = str(bad)
        mi._CATALOG.clear()
        with mock.patch.object(mi, "_read", wraps=mi._read) as spy:
            self.assertIsNone(mi.load_catalog(False))
            self.assertIsNone(mi.load_catalog(False))
            self.assertEqual(spy.call_count, 1)

    # --- C4 ---------------------------------------------------------------------------------
    def test_orca_cli_run_e_env(self):
        base = {"PATH": "p", "KEEP": "1", "NODE_OPTIONS": "x", "NODE_PATH": "y", "ELECTRON_RUN_AS_NODE": "1",
                "ORCA_NODE_OPTIONS": "z", "ORCA_CLI_COMMAND": "c", "NODEX": "fica"}
        with mock.patch.dict(os.environ, base, clear=True), mock.patch.object(orca_cli.os, "name", "posix"):
            e = orca_cli.env()
            self.assertEqual(e, {"PATH": "p", "KEEP": "1", "NODEX": "fica"})
            e["KEEP"] = "2"
            self.assertEqual(os.environ["KEEP"], "1")
        with mock.patch.dict(os.environ, dict(base, USERPROFILE="/u", APPDATA="/a"), clear=True), \
                mock.patch.object(orca_cli.os, "name", "nt"):
            e = orca_cli.env()
            self.assertEqual(e["USERPROFILE"], "/u")
            self.assertEqual(e["APPDATA"], "/a")
            self.assertEqual(e["LOCALAPPDATA"], os.path.join("/u", "AppData", "Local"))
            self.assertFalse([k for k in FORBIDDEN if k in e])
        with mock.patch.dict(os.environ, {"PATH": "p"}, clear=True), mock.patch.object(orca_cli.os, "name", "nt"), \
                mock.patch.object(orca_cli.os.path, "expanduser", return_value="/h"):
            e = orca_cli.env()
            self.assertEqual(e["USERPROFILE"], "/h")
            self.assertEqual(e["APPDATA"], os.path.join("/h", "AppData", "Roaming"))
            self.assertEqual(e["LOCALAPPDATA"], os.path.join("/h", "AppData", "Local"))
        self.fake_orca("ok")
        self.assertEqual(orca_cli.resolve(), shutil.which("orca"))
        self.assertIsNotNone(orca_cli.resolve())
        r = orca_cli.run(["status", "--json"], 30)
        self.assertEqual((r["code"], r["data"], r["error"], r["stderr"]),
                         (0, {"ok": True, "result": {"x": 1}}, None, ""))
        self.assertEqual(json.loads(r["stdout"]), r["data"])
        cases = {"okfalse": (0, "falhou aqui"), "erro-texto": (1, "erro em texto"),
                 "stderr": (2, "quebrou no stderr"), "stdout": (3, "so stdout"), "mudo": (4, "saiu com 4")}
        for mode, (code, error) in cases.items():
            self.fake_orca(mode)
            r = orca_cli.run(["x"], 30)
            self.assertEqual((r["code"], r["error"]), (code, error), mode)
        self.fake_orca("lista")
        r = orca_cli.run(["x"], 30)
        self.assertEqual((r["code"], r["data"], r["error"], r["stdout"].strip()), (0, None, None, "[1, 2]"))
        self.fake_orca("env")
        with mock.patch.dict(os.environ, {"NODE_OPTIONS": "x", "ELECTRON_RUN_AS_NODE": "1", "ORCA_CLI_COMMAND": "c"}):
            cwd = self.tmp / "work"
            cwd.mkdir()
            r = orca_cli.run(["x"], 30, cwd=str(cwd))
            self.assertEqual(r["code"], 0, r)
            self.assertFalse([k for k in FORBIDDEN if k in r["data"]["env"]])
            self.assertEqual(Path(r["data"]["cwd"]).resolve(), cwd.resolve())
        with mock.patch.dict(os.environ, {"PATH": str(self.tmp / "vazio")}):
            r = orca_cli.run(["x"], 5)
            self.assertEqual((r["code"], r["stdout"], r["data"]), (127, "", None))
            self.assertTrue(r["error"])
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=subprocess.TimeoutExpired("orca", 7)):
            r = orca_cli.run(["x"], 7)
            self.assertEqual((r["code"], r["data"], r["error"]), (124, None, "tempo esgotado (7 s)"))
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=OSError(13, "Permissão negada")):
            r = orca_cli.run(["x"], 7)
            self.assertEqual((r["code"], r["data"], r["error"]), (126, None, "Permissão negada"))

    def test_saida_127_124_126_do_orca(self):
        falhas = {
            "timeout": subprocess.TimeoutExpired("orca", 7),
            "oserror": OSError(13, "negado"),
        }
        for code in (127, 124, 126):
            self.fake_orca(f"sai{code}")
            r = orca_cli.run(["x"], 30)
            self.assertEqual((r["code"], r["kind"], r["data"], r["error"]), (code, None, None, f"saiu com {code}"))
            with self.assertRaises(screens.ScreenError) as cm:
                screens._orca("exec", ["x"])
            self.assertEqual(str(cm.exception), f"exec: saiu com {code}")
            self.assertEqual(banner._run(["orca", "status"], 30), (code, ""))
            self.assertEqual(banner.check_orca(), "Orca: ⚠️ `orca status` falhou (a Orca está aberta?)")
        with mock.patch.dict(os.environ, {"PATH": str(self.tmp / "vazio")}):
            r = orca_cli.run(["x"], 5)
            self.assertEqual((r["code"], r["kind"]), (127, "missing"))
            self.assertEqual(banner.check_orca(), "Orca: ❌ comando `orca` não encontrado no PATH")
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=falhas["timeout"]):
            r = orca_cli.run(["x"], 7)
            self.assertEqual((r["code"], r["kind"]), (124, "timeout"))
            self.assertEqual(banner.check_orca(), "Orca: ⚠️ `orca status` não respondeu a tempo")
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=falhas["oserror"]):
            r = orca_cli.run(["x"], 7)
            self.assertEqual((r["code"], r["kind"]), (126, "oserror"))
            self.assertEqual(banner.check_orca(), "Orca: ⚠️ `orca status` falhou (a Orca está aberta?)")

    # --- C5 ---------------------------------------------------------------------------------
    @staticmethod
    def _which_orca_calls(path: Path) -> list[int]:
        """Linhas das chamadas efetivas (AST) de `which("orca")` ou `shutil.which ("orca")`."""
        found = []
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            f = node.func
            name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
            arg = node.args[0]
            if (name == "which" and isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                    and arg.value.startswith("orca")):
                found.append(node.lineno)
        return found

    def test_um_adaptador_da_orca(self):
        probe = self.tmp / "probe.py"
        probe.write_text(PROBE, encoding="utf-8")
        self.assertEqual(self._which_orca_calls(probe), [2, 4])  # acha chamada com espaço; ignora comentário e string
        offenders = []
        for folder in ("scripts", "hooks"):
            for p in (ROOT / folder).rglob("*.py"):
                if p.name != "orca_cli.py" and self._which_orca_calls(p):
                    offenders.append(p.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [])
        self.assertEqual(len(self._which_orca_calls(ROOT / "scripts" / "orca_cli.py")), 1)
        for mod in (screens, banner, dispatch):
            self.assertIs(mod.orca_cli, orca_cli, mod.__name__)
        # os três consumidores chamam o adaptador (espionado), não o executável
        calls = []

        def fake_run(args, timeout, cwd=None):
            calls.append(("run", list(args), timeout, cwd))
            return {"code": 0, "stdout": "{}", "stderr": "", "data": {}, "kind": None, "error": None}

        def fake_resolve():
            calls.append(("resolve",))
            return "/x/orca-falso"

        def fake_env():
            calls.append(("env",))
            return {"MARCA": "1"}

        with mock.patch.object(orca_cli, "run", side_effect=fake_run),                 mock.patch.object(orca_cli, "resolve", side_effect=fake_resolve),                 mock.patch.object(orca_cli, "env", side_effect=fake_env),                 mock.patch.object(shutil, "which", side_effect=AssertionError("which direto")),                 mock.patch.object(subprocess, "run") as sub:
            screens._orca("exec", ["a", "--json"])
            self.assertEqual(calls, [("run", ["a", "--json"], screens.TIMEOUT, None)])
            calls.clear()
            self.assertEqual(banner._run(["orca", "status", "--json"], 30, cwd="/c"), (0, "{}"))
            self.assertEqual(calls, [("run", ["status", "--json"], 30, "/c")])
            calls.clear()
            banner.check_orca()
            self.assertEqual(calls, [("run", ["status", "--json"], banner.ORCA_TIMEOUT, None)])
            calls.clear()
            dispatch.default_runner(["orca", "x"], capture_output=True)
            self.assertEqual(calls, [("resolve",), ("env",)])
            self.assertEqual(sub.call_args.args[0], ["/x/orca-falso", "x"])
            self.assertEqual(sub.call_args.kwargs["env"], {"MARCA": "1"})
        self.fake_orca("okfalse")
        with self.assertRaises(screens.ScreenError) as cm:
            screens._orca("exec", ["x"])
        self.assertEqual(str(cm.exception), "exec: falhou aqui")
        self.assertEqual(banner._run(["orca", "status", "--json"], 30)[0], 0)
        self.fake_orca("env")
        with mock.patch.dict(os.environ, {"ELECTRON_RUN_AS_NODE": "1"}):
            self.assertEqual(screens._orca("exec", ["x"])["ok"], True)
            code, out = banner._run(["orca", "status"], 30)
            self.assertEqual(code, 0)
            self.assertNotIn("ELECTRON_RUN_AS_NODE", json.loads(out)["env"])
            res = dispatch.default_runner(["orca", "x"], capture_output=True, text=True,
                                          stdin=subprocess.DEVNULL)
            self.assertEqual(res.returncode, 0)
            self.assertNotIn("ELECTRON_RUN_AS_NODE", json.loads(res.stdout)["env"])
        with mock.patch.dict(os.environ, {"PATH": str(self.tmp / "vazio")}):
            with self.assertRaises(screens.ScreenError) as cm:
                screens._orca("exec", ["x"])
            self.assertEqual(str(cm.exception), "exec: o CLI `orca` não está no PATH")
            self.assertEqual(banner._run(["orca", "status"], 5), (127, ""))
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=subprocess.TimeoutExpired("orca", 60)):
            with self.assertRaises(screens.ScreenError) as cm:
                screens._orca("exec", ["x"])
            self.assertEqual(str(cm.exception), "exec: tempo esgotado (60 s)")
            self.assertEqual(banner._run(["orca", "status"], 5), (124, ""))
        with mock.patch.object(orca_cli.subprocess, "run", side_effect=OSError(13, "negado")):
            with self.assertRaises(screens.ScreenError) as cm:
                screens._orca("exec", ["x"])
            self.assertEqual(str(cm.exception), "exec: não foi possível rodar o `orca` (negado)")
            self.assertEqual(banner._run(["orca", "status"], 5), (126, ""))

    # --- C6 ---------------------------------------------------------------------------------
    def test_stack_orca_documentada(self):
        path = ROOT / ".specs" / "stack" / "orca.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertIn("**Project version**: 1.4.268\n", text)
        self.assertIn("**Doc version**: 1.4.268\n", text)
        bullets = [ln for ln in text.splitlines() if ln.startswith("- ")]
        self.assertEqual(len(bullets), 5, bullets)
        temas = {
            "- Resolução do CLI (F10-14): ": (
                "o `orca` é um aplicativo Electron; para rodar como CLI ele usa `ELECTRON_RUN_AS_NODE`.",
                "acha o executável pelo PATH com `shutil.which` (no Windows acha o `orca.cmd`)",
                "sem shell, sem stdin e com tempo limite (`scripts/orca_cli.py`)."),
            "- Ambiente: ": (
                "o filho não herda `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` nem `ORCA_CLI_COMMAND`",
                "no Windows `USERPROFILE`, `APPDATA` e `LOCALAPPDATA` são completados a partir da pasta do usuário"
                " quando faltam."),
            "- `--current` (F10-8): ": (
                "\"atual\" é o terminal que chama;",
                "o resultado é o do terminal de quem chamou, não o do coordenador."),
            "- Falha com `ok:false`: ": (
                "com `--json` a resposta vem como `{\"ok\": false, \"error\": {\"message\": \"...\"}}`"
                " e o código de saída é diferente de 0;",
                "a mensagem de erro está em `error.message`"),
            "- `orca plugin test` e `orca plugin check` só rodam com o plugin no mesmo drive da instalação da Orca;": (
                "falham com `cannot import \"./orca-runtime.mjs\"`.",
                "Rode o gate num worktree no mesmo drive."),
        }
        for prefix, frases in temas.items():
            achadas = [b for b in bullets if b.startswith(prefix)]
            self.assertEqual(len(achadas), 1, prefix)
            for frase in frases:
                self.assertIn(frase, achadas[0], prefix + frase)
        fetched = re.search(r"^\*\*Fetched\*\*: (\d{4}-\d{2}-\d{2})$", text, re.M).group(1)
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "stack_cache.py"), "check", str(ROOT),
                              "--today", fetched], capture_output=True, text=True, encoding="utf-8",
                             stdin=subprocess.DEVNULL)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("orca: ok", res.stdout.splitlines())

    # --- C7 ---------------------------------------------------------------------------------
    def test_decisions_e_changelog(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-211:.*?(?=^### SC-|\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        entry = m.group(0)
        parts = {}
        for label in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            pm = re.search(rf"^- \*\*{label}\*\*: (.*)$", entry, re.M)
            self.assertIsNotNone(pm, label)
            parts[label] = pm.group(1)
        decisao = parts["Decisão"]
        esperado = {
            "R1": (
                "`model_info.download` só aceita JSON com ao menos um provedor cujo valor é objeto com `models` objeto; "
                "senão devolve `None` e não toca o cache (bytes e `mtime` iguais)."
            ),
            "R2": (
                "`model_info.info` limpa `name` e `description`: tira os caracteres de controle da categoria Unicode `C*` "
                "(ESC e quebras de linha inclusive), junta espaços seguidos num só e corta o `name` em 80 e a "
                "`description` em 200; a saída `--json` e o `render` usam o mesmo texto."
            ),
            "R3": (
                "`load_catalog` interpreta o arquivo (de `STARCODE_MODELS_DEV_FILE` ou do cache) no máximo uma vez por "
                "processo para a mesma origem; `cached_family` e `cached_tier` reutilizam o resultado e um `download` "
                "bem-sucedido atualiza o guardado."
            ),
            "R4": (
                "`scripts/orca_cli.py` oferece `resolve()` (`shutil.which`, `None` sem executável), `env()` (cópia do "
                "ambiente sem `NODE_*`, `ELECTRON_RUN_AS_NODE`, `ORCA_NODE_OPTIONS` e `ORCA_CLI_COMMAND`; no Windows "
                "completa `USERPROFILE`, `APPDATA` e `LOCALAPPDATA`) e `run(args, timeout, cwd=None)`, que devolve `code`, "
                "`stdout`, `stderr`, `data` (objeto JSON do stdout ou `None`) e `error` (`None` em sucesso; em falha a "
                "primeira mensagem não vazia entre `error.message`, `error` texto, stderr, stdout e `saiu com <código>`), "
                "sem levantar exceção: 127 sem executável, 124 com tempo esgotado e 126 com `OSError`, e o campo `kind` "
                "(`missing`, `timeout`, `oserror` ou `None`) diz se a falha foi de execução, de modo que o código de saída "
                "de um `orca` que rodou e saiu com 127, 124 ou 126 não é confundido com falha de execução."
            ),
            "R5": (
                "`screens.py` e `hooks/scripts/banner.py` chamam a Orca por `orca_cli.run` e `dispatch.default_runner` usa "
                "`orca_cli.resolve` e `orca_cli.env`; nenhum `.py` fora do `orca_cli.py` chama `shutil.which(\"orca\")`, e "
                "as mensagens e os códigos de saída dos três não mudam: `screens.py` e o banner escolhem a mensagem pelo "
                "`kind`, então um `orca` que sai com 127, 124 ou 126 de verdade segue como falha comum do passo (`saiu com "
                "<código>` ou a mensagem do JSON, do stderr ou do stdout)."
            ),
            "R6": (
                "`.specs/stack/orca.md` (gravado por `stack_cache.py write`, versão 1.4.268) resume a resolução do CLI "
                "(Electron, `ELECTRON_RUN_AS_NODE`, F10-14), o env, o `--current` do terminal que chama (F10-8), a "
                "resposta `ok:false` com `error.message` e o `orca plugin test` que só roda no mesmo drive da instalação."
            ),
            "R7": (
                "esta entrada e a linha no `CHANGELOG.md`."
            ),
        }
        achados = dict(re.findall(r"(R\d): (.*?)(?= R\d: |$)", decisao))
        self.assertEqual(sorted(achados), sorted(esperado))
        for chave, frase in esperado.items():
            self.assertEqual(achados[chave], frase, chave)  # afirmação completa de cada requisito, sem negar nem omitir
        tests = ("test_download_confere_forma", "test_texto_do_catalogo_limpo", "test_catalogo_lido_uma_vez",
                 "test_orca_cli_run_e_env", "test_saida_127_124_126_do_orca", "test_um_adaptador_da_orca", "test_stack_orca_documentada",
                 "test_decisions_e_changelog")
        for name in tests:
            self.assertIn(f"`{name}`", parts["Por que não é bug"], name)
            self.assertTrue(hasattr(type(self), name), name)
        self.assertIn("`test_catalogo_e_orca.CatalogoEOrcaTests`", parts["Por que não é bug"])
        change = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", change, re.M | re.S).group(1)
        self.assertEqual(len([ln for ln in unreleased.splitlines() if "(SC-211)" in ln]), 1)


if __name__ == "__main__":
    unittest.main()
