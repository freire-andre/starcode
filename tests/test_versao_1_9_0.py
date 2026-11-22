"""SC-214: versão 1.9.0 em manifestos, CHANGELOG e README."""
from __future__ import annotations

import ast
import json
import re
import subprocess
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from helpers import ROOT
from test_support import changelog_recent

import release

ISSUES = ([186, 187, 188, 190] + list(range(195, 201)) + list(range(202, 214)))


def _itens(secao: str) -> list[tuple[str, str]]:
    """(seção `### ...`, linha do item `- ...`) na ordem do texto."""
    atual, itens = "", []
    for linha in secao.splitlines():
        if linha.startswith("### "):
            atual = linha
        elif linha.startswith("- "):
            itens.append((atual, linha))
    return itens


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class Versao190Tests(unittest.TestCase):
    def test_versao_1_9_0_em_todos_os_manifestos(self):  # C2
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "1.9.0")
        self.assertEqual(_json("src/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json("dist/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json(".claude-plugin/marketplace.json")["plugins"][0]["version"], "1.9.0")
        market = _json(".agents/plugins/marketplace.json")
        self.assertEqual(len(market["plugins"]), 1)
        plugin = market["plugins"][0]
        self.assertEqual(plugin["name"], "starcode")
        self.assertEqual(plugin["source"], {"source": "local", "path": "./dist/codex"})
        self.assertNotIn("version", plugin)
        self.assertEqual(_json("dist/codex/.codex-plugin/plugin.json")["version"], "1.9.0")
        for alvo in ("antigravity", "claude", "codex", "opencode", "orca"):
            path = ROOT / "dist" / alvo / "crew.json"
            self.assertTrue(path.is_file(), str(path))
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
        antes = subprocess.run(["git", "show", "8b86df0:CHANGELOG.md"], cwd=ROOT, capture_output=True)
        if antes.returncode != 0:
            self.skipTest("commit 8b86df0 ausente neste clone (CI raso)")
        antigo = antes.stdout.decode("utf-8").replace("\r\n", "\n")
        ma = re.search(r"^## \[Unreleased\]\n(.*?)^## \[1\.8\.0\]", antigo, re.M | re.S)
        self.assertIsNotNone(ma)
        self.assertEqual(len(_itens(ma.group(1))), 24)
        self.assertEqual(_itens(secao), _itens(ma.group(1)))
        notas = release._notes(ROOT, "1.9.0")
        self.assertIsNotNone(notas)
        self.assertIn("SC-213", notas)

    def test_changelog_recent(self):  # C5
        fake = """# Changelog

## [Unreleased]

- novo (SC-1)

## [3.0.0] - 2026-03-03

- do tres (SC-3)

## [2.0.0] - 2026-02-02

- do dois (SC-2)

## [1.0.0] - 2026-01-01

- do um (SC-4)
"""
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "CHANGELOG.md").write_text(fake, encoding="utf-8")
            got = changelog_recent(Path(tmp))
        esperado = """## [Unreleased]

- novo (SC-1)

## [3.0.0] - 2026-03-03

- do tres (SC-3)

"""
        self.assertEqual(got, esperado)
        for fora in ("SC-2", "SC-4", "2.0.0", "1.0.0"):
            self.assertNotIn(fora, got)

    def test_nenhum_teste_le_unreleased_nem_busca_issue_fora_do_helper(self):  # C5
        # Exceções por nome, cada uma com o motivo:
        livre = {
            "test_support.py": "define o helper changelog_recent",
            "test_versao_1_9_0.py": "este teste confere o helper e o fechamento da seção",
            "test_release.py": "confere o formato da seção [Unreleased] do release.py (CHANGELOG de fixture)",
            "test_release_docs.py": "confere o formato da seção [Unreleased] do CHANGELOG (Keep a Changelog)",
        }
        unreleased = re.compile(r"\?\[Unreleased\?\]|[\"']Unreleased[\"']|\bUnreleased\b")
        issue = re.compile(r"SC-\d+")
        arquivos = sorted((ROOT / "tests").glob("*.py"))
        self.assertGreater(len(arquivos), 30)
        for path in arquivos:
            if path.name in livre:
                continue
            src = path.read_text(encoding="utf-8")
            self.assertIsNone(unreleased.search(src), path.name)
            for fn in ast.walk(ast.parse(src)):
                if not isinstance(fn, ast.FunctionDef):
                    continue
                consts = [n.value for n in ast.walk(fn) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
                if "CHANGELOG.md" not in consts or not any(issue.search(c) for c in consts):
                    continue
                onde = f"{path.name}::{fn.name}"
                chamadas = [n.func.id for n in ast.walk(fn)
                            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
                self.assertIn("changelog_recent", chamadas, onde)
                lidos = set()
                for n in ast.walk(fn):
                    if isinstance(n, ast.Assign) and any(isinstance(c, ast.Constant) and c.value == "CHANGELOG.md"
                                                         for c in ast.walk(n.value)):
                        lidos |= {t.id for t in n.targets if isinstance(t, ast.Name)}
                usados = [n.id for n in ast.walk(fn)
                          if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id in lidos]
                self.assertEqual(usados, [], f"{onde}: busca no CHANGELOG inteiro")

    def test_readme_estado_1_9_0(self):  # C4
        linhas = [l for l in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if l.startswith("Estado:")]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0], "Estado: **v1.9.0**, com suporte em três níveis:")
        self.assertNotIn("v1.8.0", linhas[0])


if __name__ == "__main__":
    unittest.main()
