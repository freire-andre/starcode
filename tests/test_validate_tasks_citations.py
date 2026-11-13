from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES

import validate_tasks

OLD_TASK = "Criar `app/reports/csv_export.py` com `sales_to_csv(rows)` que gera o CSV com `;` e cabeçalho."
OLD_CTX = "Siga o padrão dos serializadores em `app/reports/`."
OLD_MAY = "May change: `app/reports/csv_export.py`, `tests/unit/test_csv_export.py`"


class CitationCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-cit-")
        self.root = Path(self._tmp.name) / "large"
        shutil.copytree(FIXTURES / "gates" / "large", self.root)
        self.tasks = self.root / ".specs" / "features" / "export-csv" / "tasks.md"

    def tearDown(self):
        self._tmp.cleanup()

    def edit(self, old, new):
        text = self.tasks.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.tasks.write_text(text.replace(old, new, 1), encoding="utf-8")

    def errors(self):
        return validate_tasks.evaluate(None, self.root).errors

    def cit(self):
        return [e for e in self.errors() if "o TASK cita" in e]


class CitationTests(CitationCase):
    def test_task_cita_arquivo_fora_do_may_change_falha(self):
        self.assertEqual(self.cit(), [])
        self.edit(OLD_TASK, OLD_TASK + " Veja `scripts/y.py`.")
        self.assertEqual(self.cit(), ["T1: o TASK cita scripts/y.py, fora do May change: "
                                      "acrescente ao May change ou cite em CONTEXT"])

    def test_citacao_coberta_por_pasta_ou_nome(self):
        self.edit(OLD_MAY, OLD_MAY + ", `dist/`, `scripts/snapshot.py`")
        self.edit(OLD_TASK, OLD_TASK + " Gere `dist/x.json` e ajuste `snapshot.py`, `app/reports/csv_export.py`.")
        self.assertEqual(self.cit(), [])

    def test_versao_e_atributo_nao_contam(self):
        self.edit(OLD_TASK, OLD_TASK + " Suba para `1.6.0`, leia `os.environ` e copie `<arquivo>.py` e `*.py`.")
        self.assertEqual(self.cit(), [])

    def test_citacao_em_context_nao_conta(self):
        self.edit(OLD_CTX, OLD_CTX + " Veja também `scripts/y.py`.")
        self.assertEqual(self.cit(), [])

    def test_citacao_com_travessia_nao_e_coberta_pela_pasta(self):
        self.edit(OLD_MAY, OLD_MAY + ", `scripts/`")
        self.edit(OLD_TASK, OLD_TASK + " Veja `scripts/../../outside.py` e `scripts/../other.py`.")
        self.assertEqual(self.cit(), [
            "T1: o TASK cita scripts/../../outside.py, fora do May change: "
            "acrescente ao May change ou cite em CONTEXT",
            "T1: o TASK cita scripts/../other.py, fora do May change: "
            "acrescente ao May change ou cite em CONTEXT"])

    def test_citacao_com_ponto_dentro_da_pasta_continua_coberta(self):
        self.edit(OLD_MAY, OLD_MAY + ", `scripts/`")
        self.edit(OLD_TASK, OLD_TASK + " Veja `scripts/./a/../b.py`.")
        self.assertEqual(self.cit(), [])


if __name__ == "__main__":
    unittest.main()
