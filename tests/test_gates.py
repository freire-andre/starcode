"""Selftest of the adapted gates (ADR-0002): valid fixtures pass, each broken rule fails with its message."""
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES

import check_commit
import gates_common as gc
import run_gates
import tasks_export
import validate_spec
import validate_tasks


class GateCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-gates-")
        self.root = Path(self._tmp.name)
        shutil.copytree(FIXTURES / "gates" / "large", self.root / "large")
        shutil.copytree(FIXTURES / "gates" / "medium", self.root / "medium")
        self.large = self.root / "large"
        self.medium = self.root / "medium"
        self.lf = self.large / ".specs" / "features" / "export-csv"
        self.mf = self.medium / ".specs" / "features" / "dark-mode"

    def tearDown(self):
        self._tmp.cleanup()

    def edit(self, path, old, new):
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture sem o trecho {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def spec_errors(self, root, approved=False):
        return validate_spec.evaluate(None, root, approved).errors

    def tasks_errors(self, **kw):
        return validate_tasks.evaluate(None, self.large, **kw).errors

    def assertHas(self, errors, needle):
        self.assertTrue(any(needle in e for e in errors), f"{needle!r} não está em {errors}")


class SpecTests(GateCase):
    def test_valid_fixtures_pass(self):
        r = validate_spec.evaluate(None, self.large, True)
        self.assertEqual((r.errors, r.warnings), ([], []))
        r = validate_spec.evaluate(None, self.medium, True)
        self.assertEqual((r.errors, r.warnings), ([], []))

    def test_size_required_and_small_rejected(self):
        spec = self.lf / "spec.md"
        self.edit(spec, "**Size**: LARGE", "**Size**: SMALL")
        self.assertHas(self.spec_errors(self.large), "SMALL")
        self.edit(spec, "**Size**: SMALL", "")
        self.assertHas(self.spec_errors(self.large), "**Size**")

    def test_full_template_sections(self):
        self.edit(self.lf / "spec.md", "## Non-Goals", "## Fora")
        self.assertHas(self.spec_errors(self.large), "## Non-Goals")

    def test_na_needs_reason_and_only_optional(self):
        spec = self.lf / "spec.md"
        self.edit(spec, "N/A - endpoint de download sem tela intermediária; o botão só dispara o download.", "N/A")
        self.assertHas(self.spec_errors(self.large), "sem justificativa")
        self.edit(spec, "- Nenhuma venda no intervalo: arquivo só com o cabeçalho.\n- Nome de cliente com `;`: campo entre aspas.",
                  "N/A - nada")
        self.assertHas(self.spec_errors(self.large), "`## Edge Cases` não pode ser N/A")

    def test_requirement_without_shall(self):
        self.edit(self.lf / "spec.md", "The sistema SHALL usar", "The sistema usa")
        self.assertHas(self.spec_errors(self.large), "R2: sem SHALL")

    def test_duplicate_requirement(self):
        self.edit(self.lf / "spec.md", "- **R3** -", "- **R2** -")
        self.assertHas(self.spec_errors(self.large), "R2: ID de requisito repetido")

    def test_open_questions_must_be_empty(self):
        self.edit(self.lf / "spec.md", "## Open Questions\n\nNone.", "## Open Questions\n\n- Qual o limite de linhas?")
        self.assertHas(self.spec_errors(self.large), "Open Questions")

    def test_decision_status_closed(self):
        self.edit(self.lf / "spec.md", "approved - user: \"ponto e vírgula\"", "pending")
        self.assertHas(self.spec_errors(self.large), "status 'pending'")

    def test_decisions_none_with_reason_ok(self):
        spec = self.lf / "spec.md"
        text = spec.read_text(encoding="utf-8")
        start = text.index("| Item |")
        end = text.index("## Open Questions")
        spec.write_text(text[:start] + "None - só havia um caminho viável.\n\n" + text[end:], encoding="utf-8")
        self.assertEqual(self.spec_errors(self.large), [])

    def test_checks_forbidden_in_large_spec(self):
        self.edit(self.lf / "spec.md", "## Open Questions", "## Checks\n\n**C1** - x (R1)\nProof: run a | ok\n\n## Open Questions")
        self.assertHas(self.spec_errors(self.large), "só em tasks.md")

    def test_binding_source_needs_differences(self):
        self.edit(self.lf / "spec.md", "## Open Questions", "## Sources\n\n- protótipo da equipe - binding\n\n## Open Questions")
        self.assertHas(self.spec_errors(self.large), "Differences from the Source")
        self.edit(self.lf / "spec.md", "## Open Questions",
                  "## Differences from the Source\n\nNone - o produto segue a fonte.\n\n## Open Questions")
        self.assertEqual(self.spec_errors(self.large), [])

    def test_approval_required_with_flag(self):
        self.edit(self.lf / "spec.md", '**Approved**: 2026-11-03 - user: "aprovado, pode seguir para as tasks"', "")
        self.assertEqual(self.spec_errors(self.large), [])
        self.assertHas(self.spec_errors(self.large, approved=True), "**Approved**")

    def test_approval_inside_code_block_does_not_count(self):
        self.edit(self.lf / "spec.md", '**Approved**: 2026-11-03 - user: "aprovado, pode seguir para as tasks"',
                  '```\n**Approved**: 2026-11-03 - user: "exemplo"\n```')
        self.assertHas(self.spec_errors(self.large, approved=True), "**Approved**")

    def test_medium_requires_checks_covering_requirements(self):
        spec = self.mf / "spec.md"
        self.edit(spec, "**C2** - Valor inválido responde 400 (R2)\nProof: run unit | ✓ profile > rejects invalid theme", "")
        self.assertHas(self.spec_errors(self.medium), "R2: nenhum check cobre")
        text = spec.read_text(encoding="utf-8")
        spec.write_text(text[: text.index("## Checks")], encoding="utf-8")
        self.assertHas(self.spec_errors(self.medium), "## Checks")

    def test_placeholder_warning(self):
        self.edit(self.lf / "spec.md", "Os gestores copiam", "<por que a feature existe> Os gestores copiam")
        r = validate_spec.evaluate(None, self.large)
        self.assertEqual(r.errors, [])
        self.assertTrue(any("marcador" in w for w in r.warnings))


class TasksTests(GateCase):
    def test_valid_fixture_passes_execute(self):
        r = validate_tasks.evaluate(None, self.large, execute=True)
        self.assertEqual((r.errors, r.warnings), ([], []))

    def test_missing_block_and_fields(self):
        t = self.lf / "tasks.md"
        self.edit(t, "#### DELIVERY\nCommits na branch do worktree. Relatório final: o que mudou", "#### ENTREGA\nx")
        self.edit(t, "**Gate**: quick\n", "")
        errs = self.tasks_errors()
        self.assertHas(errs, "T1: falta o bloco `#### DELIVERY`")
        self.assertHas(errs, "T1: falta o campo `**Gate**:`")

    def test_may_change_required(self):
        self.edit(self.lf / "tasks.md", "May change: `app/reports/csv_export.py`, `tests/unit/test_csv_export.py`", "Nada")
        self.assertHas(self.tasks_errors(), "T1: BOUNDARIES sem `May change")

    def test_independent_tasks_cannot_share_files(self):
        t = self.lf / "tasks.md"
        self.edit(t, "**Depends on**: T1", "**Depends on**: none")
        self.edit(t, "May change: `app/routes/reports.py`", "May change: `app/reports/`, `app/routes/reports.py`")
        self.assertHas(self.tasks_errors(), "T1 e T2 podem rodar ao mesmo tempo")

    def test_dependent_tasks_may_share_files(self):
        self.edit(self.lf / "tasks.md", "May change: `app/routes/reports.py`",
                  "May change: `app/reports/csv_export.py`, `app/routes/reports.py`")
        self.assertEqual(self.tasks_errors(), [])

    def test_sensitive_file_needs_runs_alone(self):
        t = self.lf / "tasks.md"
        self.edit(t, "May change: `app/routes/reports.py`", "May change: `pyproject.toml`, `app/routes/reports.py`")
        self.assertHas(self.tasks_errors(), "arquivo sensível (pyproject.toml)")
        self.edit(t, "**Gate**: full", "**Gate**: full\n**Runs alone**: yes")
        self.assertEqual(self.tasks_errors(), [])

    def test_sensitive_from_repo_config(self):
        cfg = self.large / ".starcode" / "config.json"
        cfg.parent.mkdir(parents=True)
        cfg.write_text(json.dumps({"sensitiveFiles": ["app/reports/*.py"]}), encoding="utf-8")
        self.assertHas(self.tasks_errors(), "T1: toca arquivo sensível")

    def test_unknown_dependency_and_cycle(self):
        t = self.lf / "tasks.md"
        self.edit(t, "**Depends on**: none", "**Depends on**: T2")
        errs = self.tasks_errors()
        self.assertHas(errs, "ciclo")
        self.edit(t, "**Depends on**: T2\n**Requirements**: R2", "**Depends on**: T9\n**Requirements**: R2")
        self.assertHas(self.tasks_errors(), "depende de T9, que não existe")

    def test_unknown_requirement(self):
        self.edit(self.lf / "tasks.md", "**Requirements**: R2", "**Requirements**: R7")
        self.assertHas(self.tasks_errors(), "T1: cita R7")

    def test_gate_must_be_declared(self):
        self.edit(self.lf / "tasks.md", "**Gate**: quick", "**Gate**: turbo")
        self.assertHas(self.tasks_errors(), "Gate 'turbo'")

    def test_checks_proofs(self):
        t = self.lf / "tasks.md"
        self.edit(t, "Proof: run unit | test_csv_export.py::test_header PASSED", "Proof: run unit")
        self.assertHas(self.tasks_errors(), "C2: `run unit` sem a linha esperada")
        self.edit(t, "Proof: run unit\n", "Proof: run e2e | x PASSED\n")
        errs = self.tasks_errors()
        self.assertHas(errs, "não há linha `**Run e2e**")
        self.edit(t, "**Build**: `ruff check .`; `mypy app`\n", "")
        self.assertHas(self.tasks_errors(), "**Build**")

    def test_requirement_without_check(self):
        self.edit(self.lf / "tasks.md", "**C3** - Intervalo de 367 dias responde 422 (R3)\nProof: run api | test_reports_csv.py::test_range_limit PASSED", "")
        self.assertHas(self.tasks_errors(), "R3: nenhum check cobre")

    def test_execute_needs_both_approvals(self):
        self.edit(self.lf / "tasks.md", '**Approved**: 2026-11-03 - user: "tasks aprovadas"', "**Approved**: pending")
        self.assertEqual(self.tasks_errors(), [])
        self.assertHas(self.tasks_errors(execute=True), "tasks.md sem `**Approved**")

    def test_published_needs_linear_ids_and_record(self):
        self.assertHas(self.tasks_errors(published=True), "T1: sem `**Linear**")
        msg, code = tasks_export.record("export-csv", self.large, ["T1=SC-20", "T2=SC-21"])
        self.assertEqual(code, 0, msg)
        self.assertEqual(self.tasks_errors(published=True), [])
        msg, code = tasks_export.record("export-csv", self.large, ["T1=SC-30"])
        self.assertEqual(code, 0, msg)
        text = (self.lf / "tasks.md").read_text(encoding="utf-8")
        self.assertIn("**Linear**: SC-30", text)
        self.assertEqual(text.count("**Linear**:"), 2)
        self.assertEqual(tasks_export.record("export-csv", self.large, ["T9=SC-1"])[1], 1)

    def test_publish_stage_passes_with_ids_and_no_project(self):
        # parent-issue path (R16): tasks.md carries only `**Linear**: <ID>` per task, no Project anywhere
        msg, code = tasks_export.record("export-csv", self.large, ["T1=SC-20", "T2=SC-21"])
        self.assertEqual(code, 0, msg)
        text = (self.lf / "tasks.md").read_text(encoding="utf-8")
        self.assertNotIn("Projeto", text)
        self.assertNotIn("Project", text)
        out, rc = run_gates.render("publish", run_gates.run_stage("publish", "export-csv", self.large))
        self.assertEqual(rc, 0, out)


class ExportTests(GateCase):
    def test_plan_bodies_and_relations(self):
        out = self.root / "out"
        data, code = tasks_export.plan("export-csv", self.large, out)
        self.assertEqual(code, 0)
        self.assertEqual([i["title"] for i in data["issues"]],
                         ["T1: Serializador CSV das vendas", "T2: Rota de download com validação do intervalo"])
        self.assertEqual(data["relations"], [{"blocker": "T1", "blocked": "T2"}])
        body = (out / "T2.md").read_text(encoding="utf-8")
        for b in ("#### TASK", "#### CONTEXT", "#### BOUNDARIES", "#### RULES", "#### DELIVERY"):
            self.assertIn(b, body)
        self.assertIn("May change: `app/routes/reports.py`", body)
        self.assertIn("T1 bloqueia T2", tasks_export.render_md(data))


class CommitTests(unittest.TestCase):
    def errs(self, msg, **kw):
        return check_commit.check(msg, **kw).errors

    def test_valid(self):
        self.assertEqual(self.errs("feat(export): gerar csv\n\nCorpo.\n\nRefs: SC-12", expect_ref="SC-12"), [])
        self.assertEqual(self.errs("fix: corrigir\n\nRefs: SC-1, SC-2"), [])

    def test_refs_required(self):
        self.assertTrue(any("Refs" in e for e in self.errs("feat: x")))
        self.assertEqual(self.errs("feat: x", refs_optional=True), [])
        self.assertTrue(any("SC-9" in e for e in self.errs("feat: x\n\nRefs: SC-1", expect_ref="SC-9")))

    def test_format(self):
        self.assertTrue(self.errs("Adicionar coisa\n\nRefs: SC-1"))
        self.assertTrue(any("tipo" in e for e in self.errs("feature: x\n\nRefs: SC-1")))
        self.assertTrue(any("minúscula" in e for e in self.errs("feat: Gerar\n\nRefs: SC-1")))
        self.assertTrue(any("ponto" in e for e in self.errs("feat: gerar.\n\nRefs: SC-1")))
        self.assertTrue(any("BREAKING" in e for e in self.errs("feat!: gerar\n\nRefs: SC-1")))


class RunGatesTests(GateCase):
    def test_verdict_first(self):
        text, code = run_gates.render("tasks", run_gates.run_stage("tasks", None, self.large))
        self.assertEqual(code, 0)
        self.assertTrue(text.startswith("VEREDITO: VERDE"))
        self.edit(self.lf / "tasks.md", "**Gate**: quick", "**Gate**: turbo")
        text, code = run_gates.render("tasks", run_gates.run_stage("tasks", None, self.large))
        self.assertEqual(code, 1)
        first = text.splitlines()
        self.assertTrue(first[0].startswith("VEREDITO: VERMELHO"))
        self.assertIn("FALHA validate_tasks", first[2])

    def test_execute_medium_without_tasks(self):
        results = run_gates.run_stage("execute", None, self.medium)
        self.assertEqual([r.gate for r in results], ["validate_spec"])
        self.assertTrue(results[0].ok)

    def test_usage_error(self):
        text, code = run_gates.render("spec", run_gates.run_stage("spec", "nao-existe", self.large))
        self.assertEqual(code, 2)
        self.assertIn("NÃO RODOU", text)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_gates.main(["commit"]), 2)


class CommonTests(unittest.TestCase):
    def test_overlap(self):
        self.assertTrue(gc.paths_overlap("app/", "app/x.py"))
        self.assertTrue(gc.paths_overlap("src/**/*.ts", "src/a/b.ts"))
        self.assertFalse(gc.paths_overlap("app/a.py", "app/b.py"))
        self.assertFalse(gc.paths_overlap("app/ab", "app/a"))

    def test_sensitive(self):
        pats = list(gc.DEFAULT_SENSITIVE)
        self.assertEqual(gc.is_sensitive("db/migrations/001.sql", pats), "migrations/")
        self.assertEqual(gc.is_sensitive("frontend/package.json", pats), "package.json")
        self.assertIsNone(gc.is_sensitive("app/main.py", pats))


if __name__ == "__main__":
    unittest.main()
