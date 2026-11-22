"""Tests for `dispatch.py close-finding` and the `done` gate rules on `Closed` and table cells (SC-199, R1 a R7)."""
from __future__ import annotations

import contextlib
import io
import re
import unittest
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git
from test_support import execute_text

import check_proofs
import dispatch
import validate_verification as vv
from test_validate_verification import APPROVED, SPEC, TASKS, verification

HEADER = "| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n"
ROW1 = "| C1 frouxa | `tests/t.py:4` e `a &#124; b` | assert valor | |\n"
ROW2 = "| C2 inventado | `tests/t.py:9` | x | old |\n"
FINDINGS = HEADER + ROW1 + ROW2
COVER_MSG = "`Closed` sem cobertura (C<n> ou test_<nome>): use dispatch.py close-finding"


def cli(repo: Path, *args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = dispatch.main(["close-finding", "demo", *args, "--root", str(repo)])
        except SystemExit as exc:  # argparse
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def snapshot(repo: Path) -> dict:
    return {p: p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts}


class FechaAchadoTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text(SPEC.format(approved=APPROVED), encoding="utf-8")
        (self.fdir / "tasks.md").write_text(TASKS.format(approved=APPROVED), encoding="utf-8")
        (self.repo / "tests").mkdir()
        (self.repo / "tests" / "t.py").write_text(
            "# def test_comentario(self):\nclass T:\n    def test_alpha(self):\n        pass\n", encoding="utf-8")
        self.vpath = self.fdir / "verification.md"
        self.vpath.write_text(verification(FINDINGS), encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: demo")
        self.sha = run_git(self.repo, "rev-parse", "HEAD")

    def cell(self, n: int) -> str:
        text = self.vpath.read_text(encoding="utf-8")
        rows = [ln for ln in text.splitlines() if ln.startswith(("| C1 frouxa", "| C2 inventado"))]
        return [c.strip() for c in rows[n - 1].strip("|").split("|")][-1]

    def test_close_finding_grava(self):
        code, out, err = cli(self.repo, "1", "--commit", self.sha, "--cover", "C1")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.cell(1), f"{self.sha[:7]} · C1")
        code, _, err = cli(self.repo, "2", "--commit", self.sha, "--cover", "test_alpha")  # replaces `old`
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.cell(2), f"{self.sha[:7]} · test_alpha")
        run_git(self.repo, "commit", "--allow-empty", "-q", "-m", "fix: x")
        sha2 = run_git(self.repo, "rev-parse", "HEAD")
        code, _, err = cli(self.repo, "1", "--commit", self.sha, "--commit", sha2, "--cover", "C1",
                           "--cover", "test_alpha", "--cover", "C2")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.cell(1), f"{self.sha[:7]}, {sha2[:7]} · C1, test_alpha, C2")

    def test_close_finding_recusa(self):
        bad = [
            (["1", "--commit", "deadbee1234", "--cover", "C1"], "o commit deadbee1234 não existe"),
            (["1", "--commit", self.sha, "--cover", "C9"], "cobertura 'C9' inválida"),
            (["1", "--commit", self.sha, "--cover", "test_comentario"], "cobertura 'test_comentario' inválida"),
            (["1", "--commit", self.sha, "--cover", "test_nao_existe"], "cobertura 'test_nao_existe' inválida"),
            (["1", "--commit", self.sha, "--cover", "C1", "--cover", "xyz"], "cobertura 'xyz' inválida"),
            (["3", "--commit", self.sha, "--cover", "C1"], "achado 3 fora da faixa: a tabela tem 2 achado(s)"),
            (["0", "--commit", self.sha, "--cover", "C1"], "achado 0 fora da faixa: a tabela tem 2 achado(s)"),
        ]
        for args, msg in bad:
            before = snapshot(self.repo)
            code, out, err = cli(self.repo, *args)
            self.assertEqual(code, 2, args)
            self.assertIn(msg, err, args)
            self.assertEqual(snapshot(self.repo), before, args)
        # a malformed table: one row with an extra cell
        self.vpath.write_text(verification(HEADER + ROW1 + "| C2 x | `a|b` | y | |\n"), encoding="utf-8", newline="\n")
        before = snapshot(self.repo)
        line = self.vpath.read_text(encoding="utf-8").splitlines().index("| C2 x | `a|b` | y | |") + 1
        code, out, err = cli(self.repo, "1", "--commit", self.sha, "--cover", "C1")
        self.assertEqual(code, 2)
        self.assertIn(f"verification.md:{line}: 5 células, o cabeçalho tem 4 (escape pipe como &#124;)", err)
        self.assertEqual(snapshot(self.repo), before)

    def test_close_finding_preserva_bytes(self):
        raw = verification(FINDINGS + "\nTexto | solto depois.\n").replace("\n", "\r\n")
        self.vpath.write_bytes(raw.encode("utf-8"))
        before = self.vpath.read_bytes()
        code, _, err = cli(self.repo, "1", "--commit", self.sha, "--cover", "C2")
        self.assertEqual((code, err), (0, ""))
        after = self.vpath.read_bytes()
        old_row = ROW1.rstrip("\n").encode()
        new_row = ROW1.rstrip("\n").replace("assert valor | |", f"assert valor | {self.sha[:7]} · C2 |").encode()
        self.assertEqual(after, before.replace(old_row, new_row))
        self.assertIn("a &#124; b".encode(), after)
        self.assertEqual(after.count(b"\r\n"), before.count(b"\r\n"))

    def done(self, findings: str, strict: bool = False):
        self.vpath.write_text(verification(findings), encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "docs: verification")
        return vv.evaluate("demo", self.repo, strict)

    def test_done_exige_cobertura(self):
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)
        sha = self.sha[:7]
        res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {sha} |\n")
        self.assertIn(f"achado 'C1 frouxa': {COVER_MSG}", res.errors)
        self.assertEqual(len([e for e in res.errors if "Closed" in e]), 1, res.report())
        for closed in (f"{sha} C9", f"{sha} · test_comentario", f"{sha} · test_nao_existe"):
            res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {closed} |\n")
            self.assertIn(f"achado 'C1 frouxa': {COVER_MSG}", res.errors, closed)
        for closed in (f"{sha} · C1", f"{sha} · test_alpha", f"{sha} · C9, C2"):
            res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {closed} |\n")
            self.assertTrue(res.ok, res.report())
        res = self.done(HEADER + "| C1 frouxa | `t.py:1` | x | degradada (modo 1) |\n")
        self.assertFalse(any("cobertura" in e for e in res.errors), res.report())

    def test_done_acusa_celulas(self):
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)
        sha = self.sha[:7]
        rows = (HEADER + f"| C1 ok | `t.py:1` | x | {sha} · C1 |\n"
                f"| C2 a mais | `a|b` | y | {sha} · C1 |\n"
                f"| C3 a menos | y | {sha} · C1 |\n"
                f"| C4 dupla | y | z | {sha} · C1 ||\n"
                f"| C5 escapada | `a &#124; b` | y | {sha} · C1 |\n"
                f"C6 | e | f | x | extra\n")
        res = self.done(rows)
        lines = self.vpath.read_text(encoding="utf-8").splitlines()

        def at(prefix: str) -> int:
            return next(i for i, ln in enumerate(lines, 1) if ln.startswith(prefix))

        msg = "verification.md:{}: {} células, o cabeçalho tem {} (escape pipe como &#124;)"
        want = [msg.format(at("| C2 a mais"), 5, 4), msg.format(at("| C3 a menos"), 3, 4),
                msg.format(at("| C4 dupla"), 5, 4), msg.format(at("C6 | e"), 5, 4)]
        self.assertEqual(res.errors, want, res.report())
        checks = ("| C1 | `tests/t.py` `test_alpha` | yes |\n| C2 | `a|b` | yes | extra |\n"
                  "| C3 | `tests/t.py` |\n"
                  "C4 | `tests/t.py` | yes | extra\n"
                  "| C2 | `tests/t.py` `test_beta` | yes |\n")
        self.vpath.write_text(verification("None.", checks=checks), encoding="utf-8", newline="\n")
        res = vv.evaluate("demo", self.repo)
        lines = self.vpath.read_text(encoding="utf-8").splitlines()
        msg3 = "verification.md:{}: {} células, o cabeçalho tem 3 (escape pipe como &#124;)"
        want = [msg3.format(at("| C2 | `a|b`"), 5), msg3.format(at("| C3 |"), 2), msg3.format(at("C4 |"), 4)]
        self.assertEqual([e for e in res.errors if "células" in e], want, res.report())
        self.assertFalse(any("commit" in e for e in res.errors), res.report())

    def commit_test_file(self, name: str, content: str) -> None:
        (self.repo / "tests" / name).write_text(content, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", f"test: {name}")

    def test_cobertura_le_ast(self):
        self.commit_test_file("doc.py", "texto = '''\n    def test_fantasma():\n'''\n")
        self.commit_test_file("quebrado.py", "def test_quebrado(:\n")
        self.commit_test_file("real.py", "async def test_assincrono():\n    pass\n\n\ndef test_real():\n    pass\n")
        sha = run_git(self.repo, "rev-parse", "HEAD")
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)
        for name in ("test_fantasma", "test_quebrado"):
            before = snapshot(self.repo)
            code, _, err = cli(self.repo, "1", "--commit", sha, "--cover", name)
            self.assertEqual(code, 2, name)
            self.assertIn(f"cobertura '{name}' inválida", err)
            self.assertEqual(snapshot(self.repo), before, name)
            res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {sha[:7]} · {name} |\n")
            self.assertIn(f"achado 'C1 frouxa': {COVER_MSG}", res.errors, name)
        for name in ("test_real", "test_assincrono"):
            code, _, err = cli(self.repo, "1", "--commit", sha, "--cover", name)
            self.assertEqual((code, err), (0, ""), name)
            res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {sha[:7]} · {name} |\n")
            self.assertTrue(res.ok, res.report())

    def test_cobertura_sem_tasks(self):
        tasks = (self.fdir / "tasks.md").read_text(encoding="utf-8")
        (self.fdir / "tasks.md").unlink()
        spec = self.fdir / "spec.md"
        spec.write_text(spec.read_text(encoding="utf-8") + "\n## Checks" + tasks.split("## Checks", 1)[1],
                        encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "chore: sem tasks")
        sha = run_git(self.repo, "rev-parse", "HEAD")
        self.assertTrue(check_proofs.evaluate("demo", self.repo).ok)
        code, _, err = cli(self.repo, "1", "--commit", sha, "--cover", "C1")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.cell(1), f"{sha[:7]} · C1")
        before = snapshot(self.repo)
        code, _, err = cli(self.repo, "1", "--commit", sha, "--cover", "C9")
        self.assertEqual(code, 2)
        self.assertIn("cobertura 'C9' inválida", err)
        self.assertEqual(snapshot(self.repo), before)
        res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {sha[:7]} · C1 |\n")
        self.assertFalse(any("cobertura" in e for e in res.errors), res.report())
        res = self.done(HEADER + f"| C1 frouxa | `t.py:1` | x | {sha[:7]} · C9 |\n")
        self.assertIn(f"achado 'C1 frouxa': {COVER_MSG}", res.errors)

    def test_textos_close_finding(self):
        q = (ROOT / "src" / "briefs" / "q-verify.md").read_text(encoding="utf-8")
        self.assertIn("Write every pipe inside a cell as `&#124;`, also inside backticks", q)
        ex = execute_text()
        sec = ex.split("## 5. Post-Q cycle", 1)[1].split("\n## ", 1)[0]
        self.assertIn("close each finding with", sec)
        self.assertIn('dispatch.py" close-finding <slug> <n> --commit <sha> --cover <C<n>|test_name>', sec)
        self.assertNotIn("write the commit in each `Closed` cell", sec)

    def test_decisions_fecha_achado(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-199:.*?(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        entry = m.group(0)
        fields = {k: re.search(rf"^- \*\*{k}\*\*: (.+)$", entry, re.M) for k in
                  ("Problema", "Decisão", "Motivo", "Por que não é bug")}
        for k, v in fields.items():
            self.assertIsNotNone(v, k)
        decisao = fields["Decisão"].group(1)
        for term in ("D-c", "close-finding", "<sha> · <cobertura>", "sair com 2"):
            self.assertIn(term, decisao, term)
        for phrase in ("a cobertura vale se for um `C<n>` dos checks da feature",
                       "ou um `test_<nome>` definido em `tests/` no HEAD",
                       "lido por `ast`",
                       "uma linha de `## Checks` ou `## Findings` com número de células diferente do cabeçalho "
                       "dá `verification.md:<linha>: <m> células, o cabeçalho tem <k> (escape pipe como &#124;)`",
                       "uma linha sem pipe inicial logo depois de uma linha da tabela"):
            self.assertIn(phrase, decisao, phrase)
        bug = fields["Por que não é bug"].group(1)
        for name in ("test_close_finding_grava", "test_close_finding_recusa", "test_close_finding_preserva_bytes",
                     "test_done_exige_cobertura", "test_done_acusa_celulas", "test_cobertura_le_ast", "test_cobertura_sem_tasks",
                     "test_textos_close_finding",
                     "test_decisions_fecha_achado"):
            self.assertIn(name, bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("(SC-199)", unreleased)
        self.assertIn("close-finding", unreleased)


if __name__ == "__main__":
    unittest.main()
