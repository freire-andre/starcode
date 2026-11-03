import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROOT

import validate_config as vc

SCRIPT = ROOT / "scripts" / "config" / "validate_config.py"


def kind_of(path: Path) -> str:
    return path.name.split("-", 1)[0]


class ValidFixtures(unittest.TestCase):
    def test_all_valid_fixtures_pass(self):
        files = sorted((FIXTURES / "config" / "valid").glob("*.json"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            with self.subTest(f=f.name):
                data, errors = vc.load(kind_of(f), f)
                self.assertEqual(errors, [])
                self.assertIsNotNone(data)


class InvalidFixtures(unittest.TestCase):
    EXPECT = {
        "user-unknown-key.json": ["theme: chave desconhecida"],
        "user-newer-schema.json": ["mais nova que este StarCode"],
        "user-bad-crew.json": ["kirk2: tripulante desconhecido", "crew.q.cli", "crew.laforge: objeto vazio"],
        "user-bad-fleet.json": ["fleet.maxBatch: mínimo 1", "fleet.timeoutMinutes: esperado inteiro",
                                "qStrategy: item repetido"],
        "repo-missing-states.json": ["linear.states: obrigatório"],
        "repo-bad-values.json": ["linear.team: não pode ser vazio", "linear.states.review: esperado texto ou null",
                                 "verifiedAt: data", "baseBranch: nome de ramo Git inválido",
                                 "stack[0]: valor 'java'"],
        "repo-not-json.json": ["JSON inválido"],
        "repo-no-schema.json": ["schemaVersion: obrigatório", "linear.workspace: obrigatório"],
    }

    def test_each_invalid_fixture_fails_with_clear_message(self):
        files = sorted((FIXTURES / "config" / "invalid").glob("*.json"))
        self.assertEqual({f.name for f in files}, set(self.EXPECT))
        for f in files:
            with self.subTest(f=f.name):
                data, errors = vc.load(kind_of(f), f)
                self.assertIsNone(data)
                joined = "\n".join(errors)
                for needle in self.EXPECT[f.name]:
                    self.assertIn(needle, joined)


class Cli(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                              encoding="utf-8", input=stdin)

    def test_check_valid_and_invalid(self):
        ok = self.run_cli("--kind", "repo", str(FIXTURES / "config" / "valid" / "repo-full.json"))
        self.assertEqual(ok.returncode, 0, ok.stdout)
        self.assertIn("OK (repo)", ok.stdout)
        bad = self.run_cli("--kind", "user", str(FIXTURES / "config" / "invalid" / "user-unknown-key.json"))
        self.assertEqual(bad.returncode, 1)
        self.assertIn("INVÁLIDO", bad.stdout)

    def test_write_refuses_invalid_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / ".starcode" / "config.json"
            res = self.run_cli("--kind", "repo", "--write", str(dest), "--from", "-",
                               stdin='{"schemaVersion": 1, "extra": true}')
            self.assertEqual(res.returncode, 1)
            self.assertIn("nada foi gravado", res.stdout)
            self.assertFalse(dest.exists())

    def test_write_valid_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / ".starcode" / "config.json"
            src = FIXTURES / "config" / "valid" / "repo-full.json"
            res = self.run_cli("--kind", "repo", "--write", str(dest), "--from", str(src))
            self.assertEqual(res.returncode, 0, res.stdout)
            self.assertEqual(json.loads(dest.read_text(encoding="utf-8")),
                             json.loads(src.read_text(encoding="utf-8")))

    def test_write_invalid_keeps_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "config.json"
            dest.write_text('{"schemaVersion": 1}', encoding="utf-8")
            res = self.run_cli("--kind", "user", "--write", str(dest), "--from", "-", stdin='{"schemaVersion": 9}')
            self.assertEqual(res.returncode, 1)
            self.assertEqual(dest.read_text(encoding="utf-8"), '{"schemaVersion": 1}')


class CrewListInSync(unittest.TestCase):
    def test_validator_crew_matches_crew_yaml(self):
        import miniyaml

        doc = miniyaml.loads((ROOT / "src" / "crew.yaml").read_text(encoding="utf-8"))
        self.assertEqual(set(vc.CREW), set(doc["crew"]))


if __name__ == "__main__":
    unittest.main()
