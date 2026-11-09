"""Perfil python-flask (T8): renderiza com o registro de fixture em pasta temporária."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

PROFILE = ROOT / "profiles" / "python-flask"
SCRIPT = ROOT / "scripts" / "scaffold.py"
REGISTRY = {"pypi": {"flask": ["3.1.3", "3.2.0rc1"], "pytest": ["9.2.0"], "ruff": ["0.17.4"],
                     "mypy": ["2.4.1"]}}


def scaffold(reg: Path, *argv: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "STARCODE_REGISTRY_FIXTURE": str(reg)}
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, env=env,
                          stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")


class PythonFlaskProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="starcode-flask-")
        reg = Path(cls._tmp.name) / "registry.json"
        reg.write_text(json.dumps(REGISTRY), encoding="utf-8")
        cls.folder = Path(cls._tmp.name) / "meu-app"
        res = scaffold(reg, "new", str(cls.folder), "--profile", "python-flask",
                       "--description", "Minha API.")
        assert res.returncode == 0, res.stderr
        cls.out = res.stdout

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_expected_files(self) -> None:
        for rel in ("pyproject.toml", "README.md", ".gitignore", ".github/workflows/ci.yml",
                    "src/meu_app/__init__.py", "src/meu_app/config.py", "src/meu_app/health.py",
                    "tests/test_health.py", "tests/conftest.py", ".starcode/stack.json"):
            self.assertTrue((self.folder / rel).is_file(), rel)

    def test_template_has_no_versions_and_markers_replaced(self) -> None:
        for path in (PROFILE / "template").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"[=<>~]=?\s*\d+\.\d", text), path.name)
        for path in self.folder.rglob("*"):
            if path.is_file() and ".starcode" not in path.parts:
                self.assertNotIn("{{", path.read_text(encoding="utf-8"), path.name)
        pyproject = (self.folder / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('"flask==3.1.3"', pyproject)
        self.assertIn('name = "meu-app"', pyproject)
        self.assertIn("# starcode:inject deps", pyproject)

    def test_readme_and_ci(self) -> None:
        readme = (self.folder / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# meu-app"))
        self.assertIn("Minha API.", readme)
        self.assertIn("## Gates", readme)
        ci = (self.folder / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        for gate in ("uv run ruff check .", "uv run ruff format --check .", "uv run mypy src",
                     "uv run pytest -v"):
            self.assertIn(gate, ci)
            self.assertIn(gate, readme)

    def test_stack_json_source_is_fixture(self) -> None:
        stack = json.loads((self.folder / ".starcode/stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["profiles"], ["python-flask"])
        self.assertEqual(stack["versions"]["flask"]["source"], "fixture")

    def test_integration_tests_excluded_from_unit_gate(self) -> None:
        pyproject = (self.folder / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("not integration", pyproject)
        self.assertIn("integration:", pyproject)


if __name__ == "__main__":
    unittest.main()
