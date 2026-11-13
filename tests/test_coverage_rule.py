from __future__ import annotations

import unittest
from unittest import mock

from test_validate_tasks_citations import OLD_MAY, OLD_TASK, CitationCase

import check_scope
import gates_common
import validate_tasks


class CoverageRuleTests(unittest.TestCase):
    def test_covers_pasta_igualdade_e_glob(self):
        self.assertTrue(gates_common.covers("dist/x.json", "dist/"))
        self.assertTrue(gates_common.covers("dist\\a\\x.json", "dist/"))
        self.assertTrue(gates_common.covers("scripts/a.py", "scripts/a.py"))
        self.assertTrue(gates_common.covers("tests/test_x.py", "tests/test_*.py"))
        self.assertFalse(gates_common.covers("tests/other.py", "tests/test_*.py"))
        self.assertFalse(gates_common.covers("scripts/a.py", "dist/"))

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
