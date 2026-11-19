"""Tests for SC-205: lessons ordered by recurrence, before the worker rules, and `dispatch.py fix-brief`."""
from __future__ import annotations

import contextlib
import io
import json
import unittest

from helpers import ROOT, TempRepoCase, run_git

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

    def test_fix_brief(self):
        rows = ("| C1 frouxa | `tests/t.py:4` | assert valor | abc1234 · C1 |\n"
                "| C2 inventado | `tests/t.py:9` | troque o assert | |\n"
                "| C3 sem teste | `tests/t.py:12` | cubra o caso | |\n")
        self.feature(ver=verification(rows))
        self.store([les(1, ["a"], "2026-03-01")])
        code, out, err = self.run_fix()
        self.assertEqual(code, 0, err)
        self.assertIn("Issue: PROJ-9", out)
        self.assertNotIn("## Achado 1", out)
        self.assertNotIn("C1 frouxa", out)
        self.assertIn("## Achado 2", out)
        self.assertIn("## Achado 3", out)
        self.assertIn("- Finding: C2 inventado", out)
        self.assertIn("- Evidence: `tests/t.py:12`", out)
        self.assertIn("- Fix: cubra o caso", out)
        self.assertIn("May change: app/a.py, tests/test_a.py", out)
        self.assertIn("## Lessons", out)
        self.assertIn("- L1: texto 1", out)
        for rule in ("- Um commit por achado, com `Refs: <ID do Linear>` no corpo",
                     "- Nunca escreva em `.specs/`.",
                     "- Nunca rode `git push`, `git reset`, `git restore` nem `git stash`.",
                     "a suíte inteira verde e", "run_gates.py", "ticket demo",
                     "- Relatório final: o commit e o teste de cada achado corrigido."):
            self.assertIn(rule, out, rule)
        dest = self.repo / "brief.md"
        code, _, _ = self.run_fix("--out", str(dest))
        self.assertEqual(code, 0)
        self.assertEqual(dest.read_text(encoding="utf-8"), out)
        # sem achado aberto: exit 2 e mensagem exata
        (self.repo / ".specs" / "features" / "demo" / "verification.md").write_text(
            verification("| C1 frouxa | e | f | abc1234 · C1 |\n"), encoding="utf-8", newline="\n")
        code, out3, err3 = self.run_fix()
        self.assertEqual((code, out3, err3), (2, "", "nada a corrigir: demo sem achados abertos\n"))

    def test_fix_brief_uniao_do_tasks(self):
        self.feature(tasks=TASKS, ver=verification("| C1 x | e | f | |\n"))
        code, out, err = self.run_fix()
        self.assertEqual(code, 0, err)
        self.assertIn("May change: app/model.py, app/cli.py", out)

    def test_execute_e_decisions(self):
        execute = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
        sec5 = execute.split("## 5.")[1].split("\n## ")[0]
        self.assertIn('dispatch.py" fix-brief <slug>', sec5)
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = next((p for p in text.split("\n### ") if p.startswith("SC-205:")), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-205:")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for frase in ("`len(features)` decrescente", "`updated` decrescente", "número do ID", "limite de 10", INTRO,
                      "antes de `## Regras fixas do worker (StarCode)`", "o `q_brief` mantém a seção no fim",
                      "`dispatch.py fix-brief <slug> [--out <arquivo>]`", "`Closed` vazia", "`Achado <n>`",
                      "`May change` da feature", "um commit por achado com `Refs:`",
                      "`git push`/`reset`/`restore`/`stash`",
                      "sai com 2 e `nada a corrigir: <slug> sem achados abertos`", "`execute.md`, seção 5"):
            self.assertIn(frase, decisao, frase)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_ordem_por_recorrencia", "test_licoes_antes_das_regras", "test_fix_brief",
                     "test_execute_e_decisions"):
            self.assertIn(name, nao_bug, name)
        unreleased = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("SC-205" in ln and "fix-brief" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    unittest.main()
