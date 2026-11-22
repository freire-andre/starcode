from __future__ import annotations

import contextlib
import ntpath
import os
import unittest
from pathlib import Path
from unittest import mock

from test_validate_tasks_citations import OLD_MAY, OLD_TASK, CitationCase

import check_scope
import gates_common
import validate_tasks
from test_support import changelog_recent


class CoverageRuleTests(unittest.TestCase):
    def test_covers_pasta_igualdade_e_glob(self):
        self.assertTrue(gates_common.covers("dist/x.json", "dist/"))
        self.assertTrue(gates_common.covers("dist\\a\\x.json", "dist/"))
        self.assertTrue(gates_common.covers("scripts/a.py", "scripts/a.py"))
        self.assertTrue(gates_common.covers("tests/test_x.py", "tests/test_*.py"))
        self.assertFalse(gates_common.covers("tests/other.py", "tests/test_*.py"))
        self.assertFalse(gates_common.covers("scripts/a.py", "dist/"))

    def test_covers_tabela_portavel(self):
        tabela = [
            ("src/a.py", "src/*.py", True),
            ("src/deep/x/a.py", "src/*.py", False),
            ("src/a.py", "src/**/*.py", True),
            ("src/deep/x/a.py", "src/**/*.py", True),
            ("a/b", "a/**/b", True),
            ("a/x/y/b", "a/**/b", True),
            ("a/x/c", "a/**/b", False),
            ("a/b/c/d", "a/**", True),
            ("a", "a/**", False),
            ("app/[id]/page.tsx", "app/[id]/*.tsx", True),
            ("app/i/page.tsx", "app/[id]/*.tsx", False),
            ("tests/test_x.py", "Tests/test_*.py", False),
            ("tests/test_a.py", "tests/test_?.py", True),
            ("tests/test_ab.py", "tests/test_?.py", False),
            ("tests/test_/.py", "tests/test_?.py", False),
            ("dist/a/b", "dist/", True),
            ("scripts/a.py", "dist/", False),
        ]
        windows = [mock.patch.object(os, "name", "nt"),
                   mock.patch.object(os.path, "normcase", ntpath.normcase)]
        for modo in ("nativo", "windows"):
            with contextlib.ExitStack() as stack:
                if modo == "windows":
                    for p in windows:
                        stack.enter_context(p)
                for path, entry, esperado in tabela:
                    with self.subTest(modo=modo, path=path, entry=entry):
                        self.assertIs(gates_common.covers(path, entry), esperado)

    def test_decisions_covers_portavel(self):
        raiz = Path(__file__).resolve().parent.parent
        texto = (raiz / "DECISIONS.md").read_text(encoding="utf-8")
        inicio = texto.index("### SC-209:")
        proximo = texto.find("\n### ", inicio + 5)
        entrada = texto[inicio: proximo if proximo != -1 else len(texto)]
        campos = {}
        for nome in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            marca = f"- **{nome}**: "
            self.assertEqual(entrada.count(marca), 1, nome)
            campos[nome] = entrada.split(marca, 1)[1].split("\n- **", 1)[0]
        decisao = campos["Decisão"]
        for termo in ("fnmatchcase", "diferencia maiúsculas", "`*`", "`?`", "`/`", "`**`",
                      "a/**/b", "a/**", "`[`", "`]`", "literais", "pasta", "absoluto", "`..`"):
            self.assertIn(termo, decisao, termo)
        self.assertIn("test_covers_tabela_portavel", campos["Por que não é bug"])
        self.assertIn("test_decisions_covers_portavel", campos["Por que não é bug"])
        changelog = (raiz / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog_recent()
        self.assertEqual(sum(1 for ln in unreleased.splitlines()
                             if ln.startswith("- ") and "(SC-209)" in ln), 1)

    def test_gates_usam_a_mesma_regra(self):
        calls = []

        def fake(path, entry):
            calls.append((path, entry))
            return True

        task = validate_tasks.Task(
            "T1", "t", blocks={"TASK": ["Veja `src/x.py`."], "BOUNDARIES": ["- May change: `a/b.py`"]})
        with mock.patch.object(gates_common, "covers", side_effect=fake):
            self.assertEqual(validate_tasks.uncovered_citations(task), [])
        self.assertEqual(calls, [("src/x.py", "a/b.py")])

        calls.clear()
        with mock.patch.object(gates_common, "covers", side_effect=fake):
            self.assertTrue(check_scope.allowed("zzz.py", ["a/b.py"]))
        self.assertEqual(calls, [("zzz.py", "a/b.py")])

        with mock.patch.object(gates_common, "covers", return_value=False) as spy:
            self.assertEqual(validate_tasks.uncovered_citations(task), ["src/x.py"])
            self.assertFalse(check_scope.allowed("a/b.py", ["a/b.py"]))
            self.assertEqual(spy.call_count, 2)

    def test_covers_recusa_travessia(self):
        for path in ("scripts/../../outside.py", "/etc/x.py", "../x.py", ".."):
            for entry in ("*", "scripts/*", "*.py"):
                with self.subTest(path=path, entry=entry):
                    self.assertFalse(gates_common.covers(path, entry))

    def test_covers_recusa_letra_de_drive(self):
        for path in ("C:/x/y.py", "c:\\x\\y.py", "D:/a.py"):
            for entry in ("*", "*.py", "C:/x/"):
                with self.subTest(path=path, entry=entry):
                    self.assertFalse(gates_common.covers(path, entry))


class CoverageCitationTests(CitationCase):
    def cit(self):
        return [e for e in self.errors() if "o TASK cita" in e]

    def test_citacao_coberta_por_glob(self):
        self.edit(OLD_MAY, OLD_MAY + ", `tests/test_*.py`")
        self.edit(OLD_TASK, OLD_TASK + " Veja `tests/test_x.py`.")
        self.assertEqual(self.cit(), [])

    def test_travessia_nao_coberta_por_glob(self):
        self.edit(OLD_MAY, OLD_MAY + ", `*`, `scripts/*`")
        self.edit(OLD_TASK, OLD_TASK + " Veja `scripts/../../outside.py` e `/etc/x.py`.")
        self.assertEqual(len(self.cit()), 2)

    def test_nome_sem_pasta_continua_coberto(self):
        self.edit(OLD_MAY, OLD_MAY + ", `scripts/snapshot.py`")
        self.edit(OLD_TASK, OLD_TASK + " Ajuste `snapshot.py`.")
        self.assertEqual(self.cit(), [])


if __name__ == "__main__":
    unittest.main()
