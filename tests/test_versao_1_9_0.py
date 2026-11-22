"""SC-214: versão 1.9.0 em manifestos, CHANGELOG e README."""
from __future__ import annotations

import json
import re
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from helpers import ROOT
from test_support import changelog_recent

import release

ISSUES = ([186, 187, 188, 190] + list(range(195, 201)) + list(range(202, 214)))


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class Versao190Tests(unittest.TestCase):
    def test_versao_1_9_0_em_todos_os_manifestos(self):  # C2
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "1.9.0")
        self.assertEqual(_json("src/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json("dist/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json(".claude-plugin/marketplace.json")["plugins"][0]["version"], "1.9.0")
        market = _json(".agents/plugins/marketplace.json")
        for plugin in market["plugins"]:
            self.assertEqual(plugin.get("version", "1.9.0"), "1.9.0")
        crews = sorted((ROOT / "dist").glob("*/crew.json"))
        self.assertGreaterEqual(len(crews), 5)
        for path in crews:
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], "1.9.0", str(path))

    def test_changelog_fecha_1_9_0(self):  # C3
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(r"^## \[Unreleased\]\n(.*?)^## \[1\.9\.0\] - 2026-11-22\n(.*?)^## \[1\.8\.0\]",
                      text, re.M | re.S)
        self.assertIsNotNone(m, "ordem Unreleased, 1.9.0, 1.8.0 não encontrada")
        self.assertEqual(m.group(1).strip(), "")
        secao = m.group(2)
        self.assertEqual(sum(1 for l in secao.splitlines() if l.startswith("- ")), 24)
        self.assertEqual(sorted(set(re.findall(r"SC-\d+", secao))), sorted(f"SC-{n}" for n in ISSUES))
        self.assertEqual(len(ISSUES), 22)
        self.assertIn("### Alterado", secao)
        self.assertIn("### Corrigido", secao)
        notas = release._notes(ROOT, "1.9.0")
        self.assertIsNotNone(notas)
        self.assertIn("SC-213", notas)

    def test_changelog_recent(self):  # C5
        fake = """# Changelog

## [Unreleased]

- novo (SC-1)

## [2.0.0] - 2026-02-02

- do dois (SC-2)

## [1.0.0] - 2026-01-01

- do um (SC-3)
"""
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "CHANGELOG.md").write_text(fake, encoding="utf-8")
            got = changelog_recent(Path(tmp))
        esperado = """## [Unreleased]

- novo (SC-1)

## [2.0.0] - 2026-02-02

- do dois (SC-2)

"""
        self.assertEqual(got, esperado)
        self.assertNotIn("SC-3", got)
        self.assertNotIn("1.0.0", got)
        livre = {"test_release.py", "test_release_docs.py", "test_support.py", "test_versao_1_9_0.py"}
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if path.name in livre:
                continue
            src = path.read_text(encoding="utf-8")
            self.assertNotIn("[Unreleased]", src, path.name)

    def test_readme_estado_1_9_0(self):  # C4
        linhas = [l for l in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if l.startswith("Estado:")]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0], "Estado: **v1.9.0**, com suporte em três níveis:")
        self.assertNotIn("v1.8.0", linhas[0])


if __name__ == "__main__":
    unittest.main()
