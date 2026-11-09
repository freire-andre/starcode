"""Perfis postgresql e mysql (T9): renderização com o registro de fixture em pasta temporária."""
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

SCRIPT = ROOT / "scripts" / "scaffold.py"
REGISTRY = {
    "pypi": {"flask": ["3.1.3"], "pytest": ["9.2.0"], "ruff": ["0.17.4"], "mypy": ["2.4.1"],
             "sqlalchemy": ["2.0.55", "2.1.0b1"], "alembic": ["1.18.4"], "psycopg": ["3.3.8"],
             "pymysql": ["1.1.2"], "cryptography": ["46.0.3"]},
    "dockerhub": {"postgres": ["17", "17.2", "18-rc"], "mysql": ["9", "9.1", "10-rc"]},
}
ENGINES = {
    "postgresql": {"drivers": ['"psycopg[binary]==3.3.8"'], "image": "postgres:17",
                   "image_name": "postgres"},
    "mysql": {"drivers": ['"pymysql==1.1.2"', '"cryptography==46.0.3"'], "image": "mysql:9",
              "image_name": "mysql"},
}
INTEGRATION = "python scripts/ephemeral_db.py run {engine} -- uv run pytest -v -m integration"


def scaffold(reg: Path, *argv: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "STARCODE_REGISTRY_FIXTURE": str(reg)}
    return subprocess.run([sys.executable, str(SCRIPT), *argv], capture_output=True, env=env,
                          stdin=subprocess.DEVNULL, encoding="utf-8", errors="replace")


class DbProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="starcode-db-")
        reg = Path(cls._tmp.name) / "registry.json"
        reg.write_text(json.dumps(REGISTRY), encoding="utf-8")
        cls.folders: dict[str, Path] = {}
        for engine in ENGINES:
            folder = Path(cls._tmp.name) / f"meu-{engine}"
            res = scaffold(reg, "new", str(folder), "--profile", "python-flask", "--db", engine)
            assert res.returncode == 0, res.stderr
            cls.folders[engine] = folder

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_profile_yaml_contract(self) -> None:
        for engine, info in ENGINES.items():
            text = (ROOT / "profiles" / engine / "profile.yaml").read_text(encoding="utf-8")
            self.assertIn("kind: db", text)
            self.assertIn(f"image: {{name: {info['image_name']}, registry: dockerhub}}", text)
            self.assertIn(INTEGRATION.format(engine=engine), text)
            self.assertIn("tools: [uv, docker]", text)

    def test_expected_files(self) -> None:
        for engine, folder in self.folders.items():
            mod = f"meu_{engine}"
            for rel in ("alembic.ini", "migrations/env.py", "migrations/script.py.mako",
                        f"src/{mod}/db.py", "tests/integration/test_migrations.py",
                        "scripts/ephemeral_db.py", ".github/workflows/ci-db.yml",
                        ".starcode/stack.json"):
                self.assertTrue((folder / rel).is_file(), f"{engine}: {rel}")
            self.assertEqual(len(list((folder / "migrations/versions").glob("*.py"))), 1)

    def test_inject_and_stack(self) -> None:
        for engine, info in ENGINES.items():
            folder = self.folders[engine]
            pyproject = (folder / "pyproject.toml").read_text(encoding="utf-8")
            for dep in ['"flask==3.1.3"', '"sqlalchemy==2.0.55"', '"alembic==1.18.4"',
                        *info["drivers"]]:
                self.assertIn(dep, pyproject, engine)
            stack = json.loads((folder / ".starcode/stack.json").read_text(encoding="utf-8"))
            self.assertEqual(stack["profiles"], ["python-flask", engine])
            self.assertEqual(stack["image"], {engine: info["image"]})

    def test_template_has_no_versions_and_markers_replaced(self) -> None:
        for engine in ENGINES:
            for path in (ROOT / "profiles" / engine / "template").rglob("*"):
                if path.is_file():
                    text = path.read_text(encoding="utf-8")
                    self.assertIsNone(re.search(r"[=<>~]=?\s*\d+\.\d", text), path.name)
            for path in self.folders[engine].rglob("*"):
                if path.is_file() and not {".starcode", "scripts"} & set(path.parts):
                    self.assertNotIn("{{", path.read_text(encoding="utf-8"), path.name)

    def test_migration_is_reversible_and_db_reads_env(self) -> None:
        for engine, folder in self.folders.items():
            mig = next((folder / "migrations/versions").glob("*.py")).read_text(encoding="utf-8")
            self.assertIn("def upgrade", mig)
            self.assertIn("def downgrade", mig)
            self.assertIn("drop_table", mig)
            db = (folder / f"src/meu_{engine}/db.py").read_text(encoding="utf-8")
            self.assertIn("DATABASE_URL", db)
            test = (folder / "tests/integration/test_migrations.py").read_text(encoding="utf-8")
            for token in ("pytest.mark.integration", 'upgrade(cfg, "head")',
                          'downgrade(cfg, "base")'):
                self.assertIn(token, test)

    def test_ci_has_ephemeral_step(self) -> None:
        for engine, folder in self.folders.items():
            ci = (folder / ".github/workflows/ci-db.yml").read_text(encoding="utf-8")
            self.assertIn(INTEGRATION.format(engine=engine), ci)

    def test_checks_lists_integration_gate(self) -> None:
        for engine, folder in self.folders.items():
            res = subprocess.run([sys.executable, str(SCRIPT), "checks", str(folder)],
                                 capture_output=True, encoding="utf-8", errors="replace",
                                 env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn(INTEGRATION.format(engine=engine), res.stdout)


if __name__ == "__main__":
    unittest.main()
