"""Tests for SC-205: lessons ordered by recurrence, before the worker rules, and `dispatch.py fix-brief`."""
from __future__ import annotations

import contextlib
import io
import json
import unittest

from helpers import ROOT, TempRepoCase, run_git
from test_support import execute_text, changelog_recent

import dispatch
from test_dispatch import TASKS

INTRO = "Estas lições se repetiram em features anteriores; o Q reprova um teste que viole alguma delas."
RULES = "## Regras fixas do worker (StarCode)"
SPEC = ("# Demo: Spec\n\n**Linear**: PROJ-9\n**May change**: `app/a.py`, `tests/test_a.py`\n\n"
        "## Scope\nAlgo.\n\n## Requirements\nR1\n\n## Checks\n\n**Build**: none - sem build\n"
        "**Run unit**: `python -m unittest -v 2>&1`\n\n**C1** - a (R1)\nProof: run unit | test_a ... ok\n")


def les(n: int, features: list[str], updated: str, status: str = "confirmed") -> dict:
    return {"id": f"L{n}", "text": f"texto {n}", "signal": "gate_fail", "status": status,
            "features": features, "sources": [], "scope": "", "created": "2026-01-01", "updated": updated}


def verification(rows: str) -> str:
    return ("# Demo - verification\n\n**Verdict**: PASS\n\n## Checks\n\n| Check | Test | Holds |\n| --- | --- | --- |\n"
            f"| C1 | `tests/t.py` `test_a` | yes |\n\n## Findings\n\n"
            f"| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n{rows}\n")


class LicoesNoBriefTests(TempRepoCase):
    def feature(self, spec: str = SPEC, tasks: str | None = None, ver: str | None = None) -> None:
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text(spec, encoding="utf-8")
        if tasks:
            (fdir / "tasks.md").write_text(tasks, encoding="utf-8")
        if ver is not None:
            (fdir / "verification.md").write_text(ver, encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")

    def store(self, rows: list[dict]) -> None:
        (self.repo / ".specs" / "lessons.json").write_text(json.dumps({"lessons": rows}), encoding="utf-8")

    def test_ordem_por_recorrencia(self):
        self.feature()
        rows = [les(1, ["a"], "2026-03-01"), les(2, ["a", "b", "c"], "2026-01-01"),
                les(3, ["a", "b"], "2026-02-01"), les(4, ["a", "b"], "2026-02-01"),
                les(5, ["a", "b"], "2026-02-05"), les(6, ["a", "b", "c", "d"], "2026-01-01", "candidate")]
        rows += [les(n, [], f"2026-01-{n:02d}") for n in range(10, 18)]
        self.store(rows)
        got = dispatch.lessons_section(self.repo)
        self.assertEqual(got.count("## Lessons"), 1)
        body = [ln for ln in got.split("## Lessons")[1].strip().splitlines() if ln]
        self.assertEqual(body[0], INTRO)
        self.assertEqual(body[1:], [f"- L{n}: texto {n}" for n in (2, 5, 4, 3, 1, 17, 16, 15, 14, 13)])

    def test_licoes_antes_das_regras(self):
        self.feature(tasks=TASKS)
        self.store([les(1, ["a"], "2026-03-01")])
        w = dispatch.worker_brief("demo", "T2", self.repo)
        self.assertEqual(w.count("## Lessons"), 1)
        self.assertEqual(w.count(RULES), 1)
        self.assertLess(w.index("## Lessons"), w.index(RULES))
        self.assertIn(INTRO + "\n", w)
        # spec sem tasks.md
        (self.repo / ".specs" / "features" / "demo" / "tasks.md").unlink()
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "-q", "-m", "sem tasks")
        w = dispatch.worker_brief("demo", "T1", self.repo)
        self.assertEqual(w.count("## Lessons"), 1)
        self.assertEqual(w.count(RULES), 1)
        self.assertLess(w.index("## Lessons"), w.index(RULES))
        q = dispatch.q_brief("demo", self.repo, "main", "abc1234")
        self.assertEqual(q.count("## Lessons"), 1)
        self.assertEqual(q.rstrip().splitlines()[-3:], [INTRO, "", "- L1: texto 1"])

    def run_fix(self, *extra: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = dispatch.main(["fix-brief", "demo", "--root", str(self.repo), *extra])
        return code, out.getvalue(), err.getvalue()

    def expected_fix(self, achados: str, may: str, ticket: str, issue: str = "PROJ-9") -> str:
        plugin = dispatch.sc.PLUGIN_ROOT.as_posix()
        return (f"# Correção dos achados do Q: Demo\n\n**Plugin:** StarCode {dispatch.sc.plugin_version()}\n\nIssue: {issue}\n\nFeature: `demo`\n\n{achados}"
                f"## BOUNDARIES\nMay change: {may}\n\n"
                f"## Lessons\n\n{INTRO}\n\n- L1: texto 1\n\n"
                "## Regras fixas da correção (StarCode)\n\n"
                f"- Um commit por achado, com `Refs: {issue}` no corpo, citando o achado.\n"
                "- Nunca escreva em `.specs/`.\n"
                "- Nunca rode `git push`, `git reset`, `git restore` nem `git stash`.\n"
                "- Antes de terminar: os testes escolhidos por "
                f"`python \"{plugin}/scripts/impact.py\" select --diff <base>` verdes "
                "(a suíte inteira só quando o veredito for `rodar tudo` ou a seleção falhar) e "
                f"`python \"{plugin}/scripts/gates/run_gates.py\" ticket demo {ticket} <base>..HEAD` verde.\n"
                "- Relatório final: o commit e o teste de cada achado corrigido.\n")

    def test_fix_brief(self):
        rows = ("| C1 frouxa | `tests/t.py:4` | assert valor | abc1234 · C1 |\n"
                "| C2 inventado | `tests/t.py:9` | troque o assert | |\n"
                "| C3 sem teste | `tests/t.py:12` | cubra o caso | |\n")
        self.feature(ver=verification(rows))
        self.store([les(1, ["a"], "2026-03-01")])
        code, out, err = self.run_fix()
        self.assertEqual(code, 0, err)
        achados = ("## Achado 2\n\n- Finding: C2 inventado\n- Evidence: `tests/t.py:9`\n- Fix: troque o assert\n\n"
                   "## Achado 3\n\n- Finding: C3 sem teste\n- Evidence: `tests/t.py:12`\n- Fix: cubra o caso\n\n")
        self.assertEqual(out, self.expected_fix(achados, "app/a.py, tests/test_a.py", "T1"))
        dest = self.repo / "brief.md"
        code, _, _ = self.run_fix("--out", str(dest))
        self.assertEqual(code, 0)
        self.assertEqual(dest.read_text(encoding="utf-8"), out)
        # sem achado aberto: exit 2 e mensagem exata
        (self.repo / ".specs" / "features" / "demo" / "verification.md").write_text(
            verification("| C1 frouxa | e | f | abc1234 · C1 |\n"), encoding="utf-8", newline="\n")
        code, out3, err3 = self.run_fix()
        self.assertEqual((code, out3, err3), (2, "", "nada a corrigir: demo sem achados abertos\n"))

    def test_fix_brief_uniao_tickets(self):
        self.feature(tasks=TASKS, ver=verification("| C1 x | e | f | |\n"))
        self.store([les(1, ["a"], "2026-03-01")])
        code, out, err = self.run_fix()
        self.assertEqual(code, 0, err)
        achados = "## Achado 1\n\n- Finding: C1 x\n- Evidence: e\n- Fix: f\n\n"
        self.assertEqual(out, self.expected_fix(achados, "app/model.py, app/cli.py", "<ticket>"))
        # um só ticket no tasks.md: o ID dele
        um = TASKS.split("### T2")[0]
        (self.repo / ".specs" / "features" / "demo" / "tasks.md").write_text(um, encoding="utf-8", newline="\n")
        code, out1, err = self.run_fix()
        self.assertEqual(code, 0, err)
        self.assertEqual(out1, self.expected_fix(achados, "app/model.py", "T1"))

    def test_execute_e_decisions(self):
        execute = execute_text()
        sec5 = execute.split("## 5.")[1].split("\n## ")[0]
        self.assertIn('dispatch.py" fix-brief <slug>', sec5)
        self.assertIn("- Screens (R28): the `fix-brief` covers only the Q findings: the Picard adds the `differs` rows "
                      "of `screens.md`, when it exists, to the same brief; when only screen divergences remain, "
                      "`fix-brief` exits 2 and the Picard writes the brief by hand from `screens.md`. After the",
                      sec5)
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ") if p.startswith("SC-205:")), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-205:")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for frase in ("`len(features)` decrescente", "`updated` decrescente", "número do ID", "limite de 10", INTRO,
                      "antes de `## Regras fixas do worker (StarCode)`", "o `q_brief` mantém a seção no fim",
                      "`dispatch.py fix-brief <slug> [--out <arquivo>]`", "`Closed` vazia", "`Achado <n>`",
                      "R1: `lessons_section` ordena as confirmadas por", "mantém o limite de 10",
                      "`## Lessons` entra antes de", "nos dois caminhos (tasks.md e spec sem tasks.md)", "uma vez só",
                      "a tabela `## Findings` do `verification.md`", "o leitor de `validate_verification.py`",
                      "gera o brief com título, issue (`**Linear**` da spec)",
                      "cada achado com a célula `Closed` vazia numerado pela posição na tabela",
                      "com Finding, Evidence e Fix",
                      "(spec ou união dos tickets do tasks.md), `## Lessons` e as regras fixas",
                      "`May change` da feature", "um commit por achado com `Refs:`", "nunca escrever `.specs/`",
                      "suíte inteira e `run_gates.py ticket` verdes",
                      "relatório com o commit e o teste de cada achado",
                      "esta entrada e a linha no `CHANGELOG.md`",
                      "o `fix-brief` cobre só os achados do Q, o Picard acrescenta ao mesmo brief as linhas "
                      "`differs` do `screens.md`, quando ele existir, e com só divergências de tela o `fix-brief` "
                      "sai com 2 e o Picard escreve o brief à mão a partir do `screens.md`",
                      "`git push`/`reset`/`restore`/`stash`",
                      "sai com 2 e `nada a corrigir: <slug> sem achados abertos`", "`execute.md`, seção 5"):
            self.assertIn(frase, decisao, frase)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_ordem_por_recorrencia", "test_licoes_antes_das_regras", "test_fix_brief",
                     "test_execute_e_decisions"):
            self.assertIn(name, nao_bug, name)
        unreleased = changelog_recent()
        self.assertTrue(any("SC-205" in ln and "fix-brief" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
