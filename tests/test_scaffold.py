"""Tests for scripts/scaffold.py (R9-R19, R40, R41, R45). Fake profiles and fixture registry: no network."""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import FIXTURES, ROOT

import registry
import scaffold

PROFILES = FIXTURES / "profiles"
SCRIPT = ROOT / "scripts" / "scaffold.py"


def run(*argv: str, registry_fixture: str | None = "reg-ok.json", profiles: Path = PROFILES):
    env = {"STARCODE_PROFILES_DIR": str(profiles)}
    if registry_fixture:
        env["STARCODE_REGISTRY_FIXTURE"] = str(PROFILES / registry_fixture)
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, env), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = scaffold.main(list(argv))
        except SystemExit as exc:  # argparse usage errors
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class ScaffoldCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-scaffold-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def profiles_with(self, extra: dict[str, str]) -> Path:
        dest = self.tmp / "profiles"
        shutil.copytree(PROFILES, dest, dirs_exist_ok=True)
        for name, text in extra.items():
            (dest / name).mkdir(exist_ok=True)
            (dest / name / "profile.yaml").write_text(text, encoding="utf-8")
        return dest

    def generate(self, name: str = "meu-app", db: bool = True) -> Path:
        folder = self.tmp / name
        extra = ["--db", "fakedb"] if db else []
        code, _, err = run("new", str(folder), "--profile", "fakeapp", *extra)
        self.assertEqual(code, 0, err)
        return folder


class ScaffoldTests(ScaffoldCase):
    def test_scaffold_aligns_major_group(self) -> None:
        code, out, err = run("versions", "faketauri")
        self.assertEqual(code, 0, err)
        self.assertIn("@tauri-apps/cli 2.12.4", out)
        self.assertIn("tauri 2.12.4", out)
        self.assertIn("tauri-build 2.6.0", out)
        self.assertIn("@tauri-apps/api 2.12.4", out)
        code, _, err = run("versions", "faketauri", registry_fixture="reg-tauri-no-stable.json")
        self.assertEqual(code, 2)
        self.assertIn("tauri: crate sem versão estável no major 3", err)

    def test_scaffold_registry_error_writes_nothing(self) -> None:
        folder = self.tmp / "x"
        code, _, err = run("new", str(folder), "--profile", "fakeapp", registry_fixture="reg-missing.json")
        self.assertEqual(code, 2)
        self.assertIn("registro pypi indisponível para fakedev", err)
        self.assertFalse(folder.exists())

    def test_registry_fixture_marks_source(self) -> None:
        folder = self.generate(db=False)
        stack = json.loads((folder / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual({v["source"] for v in stack["versions"].values()}, {"fixture"})
        self.assertEqual(registry.source(), "registry")

    def test_scaffold_new_renders_and_writes_stack_json(self) -> None:
        folder = self.generate("meu-app")
        pyproject = (folder / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "meu-app"', pyproject)
        self.assertIn("fakelib==3.1.0", pyproject)
        self.assertIn('    "fakedriver==1.4.0",', pyproject)
        self.assertNotIn("starcode:inject", pyproject)
        self.assertNotIn("{{", pyproject)
        self.assertIn('NAME = "meu-app"', (folder / "src" / "meu_app" / "__init__.py").read_text(encoding="utf-8"))
        self.assertTrue((folder / "db" / "schema.sql").is_file())
        self.assertTrue((folder / "scripts" / "ephemeral_db.py").is_file())
        stack = json.loads((folder / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["schemaVersion"], 1)
        self.assertEqual(stack["profiles"], ["fakeapp", "fakedb"])
        self.assertEqual(stack["image"], {"fakedb": "postgres:17"})
        entry = stack["versions"]["fakelib"]
        self.assertEqual((entry["version"], entry["registry"], entry["source"]), ("3.1.0", "pypi", "fixture"))
        self.assertRegex(entry["at"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertNotIn("outsideTested", entry)
        code, out, _ = run("new", str(self.tmp / "outro"), "--profile", "fakeapp")
        self.assertIn("fakelib 3.1.0 (pypi, ", out)
        self.assertIn("template: fakeapp", out)
        self.assertIn("pasta: ", out)
        self.assertFalse((self.tmp / "outro" / "scripts").exists())

    def test_scaffold_rejects_invalid_name(self) -> None:
        for bad in ("Meu_App", "1app", "a" * 64):
            folder = self.tmp / "ok-dir"
            code, _, err = run("new", str(folder), "--profile", "fakeapp", "--name", bad)
            self.assertEqual(code, 2, bad)
            self.assertIn("nome inválido: use minúsculas, dígitos e hífen, começando por letra", err)
            self.assertFalse(folder.exists())

    def test_scaffold_rejects_non_empty_dir(self) -> None:
        folder = self.tmp / "ocupada"
        folder.mkdir()
        (folder / "a.txt").write_text("x", encoding="utf-8")
        code, _, err = run("new", str(folder), "--profile", "fakeapp")
        self.assertEqual(code, 2)
        self.assertIn(f"pasta não vazia: {folder.resolve()}", err)
        self.assertEqual([p.name for p in folder.iterdir()], ["a.txt"])

    def test_scaffold_rejects_unknown_combo(self) -> None:
        for argv in (["--profile", "faketauri", "--db", "fakedb"], ["--profile", "nada"]):
            folder = self.tmp / "combo"
            code, _, err = run("new", str(folder), *argv)
            self.assertEqual(code, 2)
            self.assertIn("fakeapp+fakedb", err)
            self.assertFalse(folder.exists())

    def test_scaffold_cleans_up_on_failure(self) -> None:
        profiles = self.profiles_with({"badtpl": (
            "name: badtpl\nkind: app\ncombinesWith: []\ntools: []\ninstall: []\ngates: {}\n"
            "deps:\n  - {name: fakelib, registry: pypi, main: true, tested: \"3\"}\n")})
        (profiles / "badtpl" / "template").mkdir()
        (profiles / "badtpl" / "template" / "ok.txt").write_text("ok", encoding="utf-8")
        (profiles / "badtpl" / "template" / "z.txt").write_text("{{version:nope}}", encoding="utf-8")
        folder = self.tmp / "novo" / "sub"
        code, _, err = run("new", str(folder), "--profile", "badtpl", profiles=profiles)
        self.assertEqual(code, 1)
        self.assertIn("nope", err)
        self.assertFalse(folder.exists())
        self.assertFalse((self.tmp / "novo").exists())
        empty = self.tmp / "vazia"
        empty.mkdir()
        code, _, _ = run("new", str(empty), "--profile", "badtpl", profiles=profiles)
        self.assertEqual(code, 1)
        self.assertTrue(empty.is_dir())
        self.assertEqual(list(empty.iterdir()), [])

    def test_scaffold_checks_lines(self) -> None:
        folder = self.generate()
        code, out, _ = run("checks", str(folder))
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("**Build**: "))
        self.assertIn("python gate_ok.py lint", lines[0])
        self.assertIn("cd sub && python check_cwd.py", lines[0])
        self.assertTrue(lines[1].startswith("**Run unit**: `python gate_ok.py unit`"))
        self.assertEqual(lines[2], "**Run integration**: `python gate_ok.py integration`")
        solo = self.generate("solo", db=False)
        _, out, _ = run("checks", str(solo))
        self.assertNotIn("Run integration", out)
        code, out, _ = run("checks", str(folder), "--json")
        self.assertEqual(set(json.loads(out)), {"Build", "Run unit", "Run integration"})
        code, _, err = run("checks", str(self.tmp / "vazio"))
        self.assertEqual(code, 1)
        self.assertIn("perfil não registrado: rode o Scotty", err)

    def project_for(self, profiles: Path, name: str, files: dict[str, str]) -> Path:
        folder = self.tmp / f"proj-{name}"
        (folder / ".starcode").mkdir(parents=True)
        (folder / ".starcode" / "stack.json").write_text(
            json.dumps({"schemaVersion": 1, "profiles": [name]}), encoding="utf-8")
        for rel, text in files.items():
            target = folder / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return folder

    def test_scaffold_gates_pass_fail_lines(self) -> None:
        folder = self.generate()
        code, out, err = run("gates", str(folder))
        self.assertEqual(code, 0, out + err)
        for cmd in ("python -c pass", "python gate_ok.py lint", "python gate_ok.py unit",
                    "python check_cwd.py [sub]", "python gate_ok.py integration"):
            self.assertIn(f"PASS {cmd}", out)
        self.assertNotIn("FAIL", out)
        profiles = self.profiles_with({"failapp": (
            "name: failapp\nkind: app\ncombinesWith: []\ntools: [python]\ninstall: []\n"
            "gates:\n  unit: [python ok.py, python bad.py]\ndeps: []\n")})
        bad = self.project_for(profiles, "failapp", {
            "ok.py": "pass\n", "bad.py": "import sys\nprint('quebrou aqui')\nsys.exit(4)\n"})
        code, out, _ = run("gates", str(bad), profiles=profiles)
        self.assertEqual(code, 1)
        self.assertIn("PASS python ok.py", out)
        self.assertIn("FAIL python bad.py", out)
        self.assertIn("quebrou aqui", out)
        code, out, _ = run("gates", str(bad), "--json", profiles=profiles)
        self.assertEqual([r["status"] for r in json.loads(out)["results"]], ["PASS", "FAIL"])
        slow = self.profiles_with({"slowapp": (
            "name: slowapp\nkind: app\ncombinesWith: []\ntools: [python]\ninstall: []\n"
            "gates:\n  unit: [python slow.py]\ndeps: []\n")})
        proj = self.project_for(slow, "slowapp", {"slow.py": "import time\ntime.sleep(60)\n"})
        code, out, _ = run("gates", str(proj), "--timeout-min", "0.01", profiles=slow)
        self.assertEqual(code, 1)
        self.assertIn("FAIL python slow.py: timeout 0.01 min", out)

    def test_scaffold_gates_skip_missing_tool(self) -> None:
        profiles = self.profiles_with({"toolapp": (
            "name: toolapp\nkind: app\ncombinesWith: []\ntools: [starcode-no-such-tool]\ninstall: []\n"
            "gates:\n  unit: [python ok.py]\ndeps: []\n"),
            "dockapp": (
            "name: dockapp\nkind: app\ncombinesWith: []\ntools: [python]\ninstall: []\n"
            "gates:\n  unit: [python scripts/ephemeral_db.py]\ndeps: []\n")})
        proj = self.project_for(profiles, "toolapp", {"ok.py": "pass\n"})
        code, out, _ = run("gates", str(proj), profiles=profiles)
        self.assertEqual(code, 3)
        self.assertIn("SKIP python ok.py: starcode-no-such-tool ausente", out)
        dock = self.project_for(profiles, "dockapp", {"scripts/ephemeral_db.py": "import sys\nsys.exit(3)\n"})
        code, out, _ = run("gates", str(dock), profiles=profiles)
        self.assertEqual(code, 3)
        self.assertIn("SKIP python scripts/ephemeral_db.py: Docker indisponível", out)

    def test_scaffold_outside_tested_series_exits_5(self) -> None:
        code, out, _ = run("versions", "fakeapp", registry_fixture="reg-new-series.json")
        self.assertEqual(code, 0)
        self.assertIn("fakelib 4.0.0", out)
        self.assertIn("fora da série testada (3)", out)
        self.assertIn("mais nova da série: 3.1.0", out)
        folder = self.tmp / "serie"
        code, _, err = run("new", str(folder), "--profile", "fakeapp", registry_fixture="reg-new-series.json")
        self.assertEqual(code, 5)
        self.assertIn("fakelib 4.0.0 fora da série testada 3: use --pin-tested ou --allow-new-series", err)
        self.assertFalse(folder.exists())

    def test_scaffold_pin_tested_and_allow_new_series(self) -> None:
        pinned, new = self.tmp / "pin", self.tmp / "new"
        code, _, err = run("new", str(pinned), "--profile", "fakeapp", "--pin-tested",
                           registry_fixture="reg-new-series.json")
        self.assertEqual(code, 0, err)
        stack = json.loads((pinned / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["versions"]["fakelib"]["version"], "3.1.0")
        self.assertNotIn("outsideTested", stack["versions"]["fakelib"])
        self.assertIn("fakelib==3.1.0", (pinned / "pyproject.toml").read_text(encoding="utf-8"))
        code, _, err = run("new", str(new), "--profile", "fakeapp", "--allow-new-series",
                           registry_fixture="reg-new-series.json")
        self.assertEqual(code, 0, err)
        stack = json.loads((new / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["versions"]["fakelib"]["version"], "4.0.0")
        self.assertTrue(stack["versions"]["fakelib"]["outsideTested"])
        code, _, _ = run("new", str(self.tmp / "ambos"), "--profile", "fakeapp", "--pin-tested", "--allow-new-series")
        self.assertEqual(code, 2)

    def test_scaffold_description_validation_and_readme(self) -> None:
        folder = self.tmp / "desc"
        code, _, err = run("new", str(folder), "--profile", "fakeapp", "--description", "Uma API de testes.")
        self.assertEqual(code, 0, err)
        self.assertIn("Uma API de testes.", (folder / "README.md").read_text(encoding="utf-8"))
        default = self.tmp / "padrao"
        run("new", str(default), "--profile", "fakeapp")
        self.assertIn("Projeto padrao.", (default / "README.md").read_text(encoding="utf-8"))
        for bad in ("linha 1\nlinha 2", "x" * 201):
            other = self.tmp / "ruim"
            code, _, err = run("new", str(other), "--profile", "fakeapp", "--description", bad)
            self.assertEqual(code, 2)
            self.assertIn("descrição inválida: uma linha, até 200 caracteres", err)
            self.assertFalse(other.exists())
        code, _, _ = run("new", str(self.tmp / "limite"), "--profile", "fakeapp", "--description", "x" * 200)
        self.assertEqual(code, 0)

    def test_scaffold_cli_subprocess_utf8(self) -> None:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "STARCODE_PROFILES_DIR": str(PROFILES),
               "STARCODE_REGISTRY_FIXTURE": str(PROFILES / "reg-tauri-no-stable.json")}
        res = subprocess.run([sys.executable, str(SCRIPT), "versions", "faketauri"], capture_output=True,
                             text=True, encoding="utf-8", env=env, stdin=subprocess.DEVNULL)
        self.assertEqual(res.returncode, 2)
        self.assertIn("versão estável no major 3", res.stderr)


class MiniYamlTests(unittest.TestCase):
    def test_loads_nested_flow_and_block_lists(self) -> None:
        doc = scaffold.loads(
            "a:\n  - {n: x, d: {id: /o/p, at: 2026-11-08}, t: \"3\"}\n  - k: v\n    l: [a, b]\nb: []\nc: true\n")
        self.assertEqual(doc["a"][0], {"n": "x", "d": {"id": "/o/p", "at": "2026-11-08"}, "t": "3"})
        self.assertEqual(doc["a"][1], {"k": "v", "l": ["a", "b"]})
        self.assertEqual((doc["b"], doc["c"]), ([], True))


if __name__ == "__main__":
    unittest.main()
