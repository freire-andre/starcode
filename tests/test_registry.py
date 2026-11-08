"""Tests for scripts/registry.py (R7, R8, R10, R11). Never touches the network."""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import FIXTURES, ROOT

import registry

REG = FIXTURES / "registry"
SCRIPT = ROOT / "scripts" / "registry.py"


def with_fixture(name: str):
    return mock.patch.dict(os.environ, {"STARCODE_REGISTRY_FIXTURE": str(REG / name)})


class RegistryTests(unittest.TestCase):
    def test_registry_stable_latest_per_registry(self) -> None:
        with with_fixture("ok.json"):
            self.assertEqual(registry.latest_stable("pypi", "flask"), "3.1.3")
            self.assertEqual(registry.latest_stable("npm", "vite"), "8.3.6")
            self.assertEqual(registry.latest_stable("crates", "tauri"), "2.12.4")
            self.assertEqual(registry.latest_stable("dockerhub", "postgres"), "17")
            self.assertEqual(registry.latest_stable("pypi", "flask", series="3.0".split(".")[0]), "3.1.3")
            self.assertEqual(registry.latest_stable("pypi", "flask", series="2"), "2.9.9")
            self.assertEqual(registry.latest_stable("npm", "vite", series="7"), "7.9.1")
            self.assertEqual(registry.latest_stable("crates", "tauri", series="2"), "2.12.4")
            self.assertEqual(registry.latest_stable("crates", "gpui", series="0.2"), "0.2.10")

    def test_registry_in_series(self) -> None:
        self.assertTrue(registry.in_series("3.1.3", "3"))
        self.assertFalse(registry.in_series("4.0.0", "3"))
        self.assertTrue(registry.in_series("0.2.5", "0.2"))
        self.assertFalse(registry.in_series("0.3.1", "0.2"))

    def test_registry_rejects_prereleases(self) -> None:
        for v in ("1.0.0-alpha", "1.0.0-beta.2", "1.0.0-rc.1", "1.0a1", "1.0b2", "1.0rc1", "1.0.dev0", "18-rc"):
            self.assertTrue(registry.is_prerelease(v), v)
        for v in ("1.0.0", "17", "0.2.9"):
            self.assertFalse(registry.is_prerelease(v), v)
        with with_fixture("only_pre.json"):
            for reg, pkg in (("pypi", "x"), ("npm", "y"), ("crates", "z"), ("dockerhub", "w")):
                with self.assertRaises(registry.RegistryError, msg=reg):
                    registry.latest_stable(reg, pkg)
        with with_fixture("ok.json"):
            self.assertEqual(registry.latest_stable("dockerhub", "postgres"), "17")

    def test_scaffold_registry_error_writes_nothing(self) -> None:
        with with_fixture("ok.json"), tempfile.TemporaryDirectory() as d:
            res = subprocess.run([sys.executable, str(SCRIPT), "pypi", "inexistente"], cwd=d,
                                 capture_output=True, text=True, env=os.environ.copy())
            self.assertEqual(res.returncode, 2)
            self.assertIn("registro pypi indisponível para inexistente:", res.stdout + res.stderr)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_registry_http_errors_become_registry_error(self) -> None:
        from urllib.error import HTTPError, URLError
        env = {k: v for k, v in os.environ.items() if k != "STARCODE_REGISTRY_FIXTURE"}
        with mock.patch.dict(os.environ, env, clear=True):
            http_error = HTTPError("u", 404, "Not Found", None, None)
            self.addCleanup(http_error.close)
            for exc in (http_error, URLError("sem rede"), TimeoutError("t")):
                with mock.patch("urllib.request.urlopen", side_effect=exc):
                    with self.assertRaises(registry.RegistryError) as cm:
                        registry.latest_stable("npm", "foo")
                    self.assertTrue(str(cm.exception).startswith("registro npm indisponível para foo: "))
            bad = mock.MagicMock()
            bad.__enter__.return_value.read.return_value = b"{nao json"
            with mock.patch("urllib.request.urlopen", return_value=bad):
                with self.assertRaises(registry.RegistryError):
                    registry.latest_stable("npm", "foo")

    def test_registry_fixture_marks_source(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STARCODE_REGISTRY_FIXTURE", None)
            self.assertEqual(registry.source(), "registry")
        with with_fixture("ok.json"):
            self.assertEqual(registry.source(), "fixture")
            with mock.patch("urllib.request.urlopen", side_effect=AssertionError("rede!")):
                self.assertEqual(registry.latest_stable("npm", "vite"), "8.3.6")

    def test_registry_cli_json(self) -> None:
        env = {**os.environ, "STARCODE_REGISTRY_FIXTURE": str(REG / "ok.json")}
        res = subprocess.run([sys.executable, str(SCRIPT), "crates", "gpui", "--series", "0.2", "--json"],
                             capture_output=True, text=True, env=env)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["version"], "0.2.10")
        self.assertEqual(data["source"], "fixture")


if __name__ == "__main__":
    unittest.main()
