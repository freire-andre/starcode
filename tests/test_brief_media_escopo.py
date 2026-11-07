"""Tests for SC-83: May change and the ticket gate on a MEDIUM feature (no tasks.md)."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROOT, TempRepoCase, run_git

import check_scope
import dispatch
import run_gates
import validate_spec

SPEC = """# Média: Spec

**Size**: MEDIUM
**Linear**: SC-90
{may}
## Scope

- Faz a coisa.

## Requirements

- **R1** - WHEN x THEN y.

## Checks

- **C1** - R1: teste prova y.

## Handoff

**Phase:** execute
"""


def spec(may: str = "**May change**: a.py, docs/\n") -> str:
    return SPEC.format(may=may)


class MediumScopeCase(TempRepoCase):
    def make(self, text: str) -> str:
        self.fdir = self.repo / ".specs" / "features" / "media"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        return run_git(self.repo, "rev-parse", "HEAD")

    def commit(self, files: dict[str, str], msg: str = "feat: x\n\nRefs: SC-90") -> str:
        for rel, body in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", msg)
        return run_git(self.repo, "rev-parse", "HEAD")

    def test_check_scope_medium_uses_spec_may_change(self):
        base = self.make(spec())
        head = self.commit({"a.py": "1\n", "docs/x.md": "2\n", "b.py": "3\n"})
        res = check_scope.evaluate("media", "SC-90", f"{base}..{head}", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn("b.py: fora do `May change`", errs)
        self.assertNotIn("a.py: fora", errs)
        self.assertNotIn("docs/x.md: fora", errs)

    def test_check_scope_medium_without_may_change_warns(self):
        base = self.make(spec(""))
        head = self.commit({"anything.py": "1\n"})
        res = check_scope.evaluate("media", "SC-90", f"{base}..{head}", self.repo)
        self.assertTrue(res.ok, res.report())
        self.assertIn("spec sem **May change**: escopo não conferido", res.warnings)
        head = self.commit({".specs/STATE.md": "x\n",
                            ".specs/features/media/spec.md": spec("").replace("execute", "outro")})
        res = check_scope.evaluate("media", "SC-90", f"{base}..{head}", self.repo)
        errs = "\n".join(res.errors)
        self.assertIn(".specs/STATE.md", errs)
        self.assertIn("## Handoff", errs)
        res = check_scope.evaluate("media", "SC-90", "HEAD..HEAD", self.repo)
        self.assertFalse(res.ok)
        self.assertIn("nenhum commit em", "\n".join(res.errors))

    def test_check_scope_medium_ticket_id(self):
        base = self.make(spec())
        head = self.commit({"a.py": "1\n"})
        for t in ("SC-90", "sc-90", "T1", "t1"):
            res = check_scope.evaluate("media", t, f"{base}..{head}", self.repo)
            self.assertTrue(res.ok, f"{t}: {res.report()}")
        res = check_scope.evaluate("media", "T2", f"{base}..{head}", self.repo)
        self.assertEqual(res.usage_error, "ticket T2 não é desta feature MÉDIA (use SC-90 ou T1)")

    def test_run_gates_ticket_medium_checks_commits(self):
        base = self.make(spec())
        bad = self.commit({"a.py": "1\n"}, "feat: x")
        results = run_gates.run_stage("ticket", "media", self.repo, ticket="SC-90", rng=f"{base}..{bad}")
        self.assertFalse(all(r.ok for r in results))
        self.assertIn("check_commit", [r.gate for r in results])
        good = self.commit({"a.py": "2\n"}, "feat: y\n\nRefs: SC-90")
        results = run_gates.run_stage("ticket", "media", self.repo, ticket="SC-90", rng=f"{bad}..{good}")
        self.assertTrue(all(r.ok for r in results), [r.report() for r in results])
        ok1 = self.commit({"a.py": "3\n"}, "feat: z\n\nRefs: SC-90")
        bad2 = self.commit({"a.py": "4\n"}, "feat: w")
        results = run_gates.run_stage("ticket", "media", self.repo, ticket="SC-90", rng=f"{good}..{bad2}")
        report = "\n".join(r.report() for r in results if r.gate == "check_commit")
        self.assertFalse(all(r.ok for r in results))
        self.assertIn(bad2[:7], report)
        self.assertNotIn(ok1[:7], report)
        ok2 = self.commit({"a.py": "5\n"}, "feat: v\n\nRefs: SC-90")
        ok3 = self.commit({"a.py": "6\n"}, "feat: u\n\nRefs: SC-90")
        results = run_gates.run_stage("ticket", "media", self.repo, ticket="SC-90", rng=f"{ok2}~1..{ok3}")
        self.assertTrue(all(r.ok for r in results), [r.report() for r in results])


class DocsTests(unittest.TestCase):
    def test_validate_spec_warns_medium_without_may_change(self):
        tmp = Path(tempfile.mkdtemp(prefix="starcode-sc83-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        shutil.copytree(FIXTURES / "gates" / "medium", tmp / "m")
        spec_path = next((tmp / "m" / ".specs" / "features").glob("*/spec.md"))
        text = spec_path.read_text(encoding="utf-8")
        text = "\n".join(ln for ln in text.splitlines() if not ln.startswith("**May change**")) + "\n"
        spec_path.write_text(text, encoding="utf-8")
        res = validate_spec.evaluate(None, tmp / "m")
        self.assertIn("MEDIUM sem a linha **May change**: o gate ticket não confere o escopo", res.warnings)
        self.assertTrue(res.ok, res.report())
        tpl = (ROOT / "skills" / "spock" / "references" / "spec-template.md").read_text(encoding="utf-8")
        brief = tpl.split("## Brief template (MEDIUM)", 1)[1]
        self.assertLess(brief.index("**Linear**:"), brief.index("**May change**: <paths separados por vírgula>"))

    def test_execute_medium_runs_ticket_gate(self):
        text = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
        sec = text.split("## 8. MEDIUM and SMALL", 1)[1]
        self.assertIn("run_gates.py ticket", sec)
        self.assertNotIn("no `check_scope`", sec)

    def test_decisions_records_f7_11_medium_scope(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### F7-11:", text)
        body = text.split("### F7-11:", 1)[1].split("\n### ", 1)[0]
        for needle in ("R1", "R7", "aviso", "ticket"):
            self.assertIn(needle, body)


if __name__ == "__main__":
    unittest.main()
