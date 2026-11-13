from __future__ import annotations

import unittest
from unittest import mock

from test_validate_tasks_citations import OLD_MAY, OLD_TASK, CitationCase

import check_scope
import gate_common
import validate_tasks


class CoverageRuleTests(unittest.TestCase):
    def test_covers_pasta_igualdade_e_glob(self):
        self.assertTrue(gate_common.covers("dist/x.json", "dist/"))
        self.assertTrue(gate_common.covers("dist\\a\\x.json", "dist/"))
        self.assertTrue(gate_common.covers("scripts/a.py", "scripts/a.py"))
        self.assertTrue(gate_common.covers("tests/test_x.py", "tests/test_*.py"))
        self.assertFalse(gate_common.covers("tests/other.py", "tests/test_*.py"))
        self.assertFalse(gate_common.covers("scripts/a.py", "dist/"))

    def test_gates_usam_a_mesma_regra(self):
        with mock.patch.object(gate_common, "covers", return_value=False) as spy:
            self.assertFalse(check_scope.allowed("a/b.py", ["a/b.py"]))
            self.assertEqual(spy.call_count, 1)
        with mock.patch.object(gate_common, "covers", return_value=True) as spy:
            self.assertTrue(check_scope.allowed("zzz.py", ["a/b.py"]))
            self.assertEqual(spy.call_count, 1)

    def test_covers_recusa_travessia(self):
        for path in ("scripts/../../outside.py", "/etc/x.py", "../x.py", ".."):
            for entry in ("*", "scripts/*", "*.py"):
                with self.subTest(path=path, entry=entry):
                    self.assertFalse(gate_common.covers(path, entry))


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
