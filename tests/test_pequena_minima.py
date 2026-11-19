"""Caminho da PEQUENA (SC-197, D-a): spec mínima sem aprovação, T1 pelo start/settle, Q dispensado por q-waive."""
from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git

import dispatch
import run_gates
import validate_spec
import validate_verification
from test_dispatch_settle import FakeGate, entry
from test_dispatch_start import FakeOrca

HANDOFF = "\n## Handoff\n**Phase:** execute\n**Integration branch:** feature/peq\n**Dispatched:** {d}\n"

SMALL = """# Pequena: Spec

**Size**: SMALL
**Linear**: PROJ-9
**May change**: a.py, b.py

## Scope

- Faz a coisa.

## Checks

**Build**: none - sem build
**C1** - a coisa funciona
Proof: run unit | test_a ... ok
"""

PROOFS = """# Proofs

**HEAD**: {head}
**Tree**: clean

| Check | Proof | Result |
|---|---|---|
| C1 | run unit | pass |
"""

WAIVED = ("# peq: Verification\n\n**Verification:** waived (PEQUENA)\n\n"
          "Q dispensado: tarefa PEQUENA (D-a).\n")


NL = chr(10)


def tree_bytes(path: Path) -> dict[str, bytes]:
    return {str(p.relative_to(path)): p.read_bytes() for p in sorted(path.rglob("*")) if p.is_file()}


class PequenaTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "peq"
        self.fdir.mkdir(parents=True)

    def spec(self, text: str = SMALL, handoff: str = "") -> None:
        (self.fdir / "spec.md").write_text(text + handoff, encoding="utf-8", newline="\n")

    def commit(self, msg: str = "specs") -> str:
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", msg)
        return run_git(self.repo, "rev-parse", "--short", "HEAD")

    def spec_res(self, text: str, approved: bool = False):
        self.spec(text)
        return validate_spec.evaluate("peq", self.repo, approved)

    # --- R1 -------------------------------------------------------------------------------------
    def test_spec_small_minima(self):
        r = self.spec_res(SMALL)
        self.assertEqual((r.errors, r.warnings), ([], []))
        r = self.spec_res(SMALL.replace("**Size**: SMALL", "**Size**: PEQUENA"), approved=True)
        self.assertEqual(r.errors, [])
        r = self.spec_res(SMALL, approved=True)  # a linha Approved é opcional: nada é exigido
        self.assertEqual(r.errors, [])
        r = self.spec_res(SMALL.replace("**Linear**: PROJ-9\n", "**Linear**: PROJ-9\n**Approved**: 2026-11-19 - user: \"sim\"\n"))
        self.assertEqual(r.errors, [])
        def cut(old):
            return SMALL.replace(old, "")
        cases = (
            (cut("## Scope" + NL + NL + "- Faz a coisa." + NL + NL), "falta a seção obrigatória `## Scope`"),
            (cut("- Faz a coisa." + NL), "`## Scope` está vazia"),
            (cut("**C1** - a coisa funciona" + NL + "Proof: run unit | test_a ... ok" + NL), "`## Checks` sem nenhum check"),
            (SMALL.split("## Checks")[0], "falta a seção obrigatória `## Checks`"),
            (cut("**May change**: a.py, b.py" + NL), "falta a linha `**May change**:`"),
            (cut("**Linear**: PROJ-9" + NL), "falta a linha `**Linear**:` com o ID da issue"),
        )
        for text, error in cases:
            with self.subTest(error=error):
                r = self.spec_res(text)
                self.assertEqual(len(r.errors), 1, r.errors)
                self.assertIn(error, r.errors[0])
        r = self.spec_res(SMALL.replace("PROJ-9", "sem id"))
        self.assertEqual(r.errors, ["falta a linha `**Linear**:` com o ID da issue"])
        # W1: cada check precisa da sua linha Proof:
        two = SMALL + "**C2** - a outra coisa funciona" + NL + "Proof: run unit | test_b ... ok" + NL
        r = self.spec_res(two)
        self.assertEqual((r.errors, r.warnings), ([], []))
        r = self.spec_res(two.replace("Proof: run unit | test_a ... ok" + NL, ""))
        self.assertEqual(len(r.errors), 1, r.errors)
        self.assertIn("C1 sem `Proof:`", r.errors[0])
        r = self.spec_res(two.replace("Proof: run unit | test_b ... ok" + NL, ""))
        self.assertEqual(len(r.errors), 1, r.errors)
        self.assertIn("C2 sem `Proof:`", r.errors[0])
        r = self.spec_res(SMALL.replace("Proof: run unit | test_a ... ok" + NL, ""))
        self.assertEqual(len(r.errors), 1, r.errors)
        self.assertIn("C1 sem `Proof:`", r.errors[0])

    # --- R2 -------------------------------------------------------------------------------------
    def test_spec_small_limite(self):
        def make(checks: int, may: str) -> str:
            body = "".join(f"**C{i}** - afirma {i}\nProof: run unit | test_{i} ... ok\n" for i in range(1, checks + 1))
            head, _ = SMALL.split("## Checks")
            return (head.replace("a.py, b.py", may) + "## Checks\n\n**Build**: none - sem build\n" + body)
        self.assertEqual(self.spec_res(make(5, "a.py, b.py, c.py")).errors, [])
        self.assertEqual(self.spec_res(make(5, "a.py, b.py, c.py, DECISIONS.md, CHANGELOG.md, dist/, src/x/")).errors, [])
        self.assertEqual(
            self.spec_res(make(6, "a.py, b.py")).errors,
            ["PEQUENA passou do limite (6 checks, 2 arquivos): reclassifique para MÉDIA"])
        self.assertEqual(
            self.spec_res(make(1, "a.py, b.py, c.py, d.py, DECISIONS.md, dist/")).errors,
            ["PEQUENA passou do limite (1 checks, 4 arquivos): reclassifique para MÉDIA"])
        self.assertEqual(
            self.spec_res(make(7, "a.py, b.py, c.py, d.py, e.py")).errors,
            ["PEQUENA passou do limite (7 checks, 5 arquivos): reclassifique para MÉDIA"])

    # --- R3 -------------------------------------------------------------------------------------
    def done_repo(self, text: str = SMALL, verification: str | None = WAIVED) -> None:
        self.spec(text, HANDOFF.format(d="none"))
        head = self.commit("spec")
        (self.fdir / "proofs.md").write_text(PROOFS.format(head=head), encoding="utf-8", newline="\n")
        if verification is not None:
            (self.fdir / "verification.md").write_text(verification, encoding="utf-8", newline="\n")
        self.commit("proofs")

    def test_small_sem_aprovacao(self):
        self.spec(SMALL)
        for stage in ("execute",):
            results = run_gates.run_stage(stage, "peq", self.repo)
            self.assertTrue(all(r.ok for r in results), [r.report() for r in results])
            self.assertEqual(run_gates.render(stage, results)[1], 0)
        self.done_repo()
        res = validate_verification.evaluate("peq", self.repo)
        self.assertFalse(any("Approved" in e for e in res.errors), res.errors)
        self.assertEqual(res.errors, [])
        # MEDIUM, LARGE e COMPLEX sem a linha continuam com erro, nos dois gates
        for size in ("MEDIUM", "LARGE", "COMPLEX"):
            with self.subTest(size=size):
                self.spec(SMALL.replace("**Size**: SMALL", f"**Size**: {size}"))
                errs = validate_spec.evaluate("peq", self.repo, True).errors
                self.assertTrue(any("**Approved**" in e for e in errs), errs)
                self.done_repo(SMALL.replace("**Size**: SMALL", f"**Size**: {size}"),
                               verification=WAIVED.replace("waived (PEQUENA)", "degraded"))
                errs = validate_verification.evaluate("peq", self.repo).errors
                self.assertTrue(any("spec.md sem `**Approved**" in e for e in errs), errs)

    # --- R4 -------------------------------------------------------------------------------------
    def test_dispatch_small_t1(self):
        self.spec(SMALL, HANDOFF.format(d="none"))
        self.commit()
        run_git(self.repo, "branch", "-f", "feature/peq")
        want = ["## Checks", "**C1** - a coisa funciona", "Proof: run unit | test_a ... ok",
                "## BOUNDARIES", "May change: a.py, b.py", "Issue: PROJ-9", "Feature: `peq` · Ticket T1"]
        for ticket in ("T1", "PROJ-9"):
            text = dispatch.worker_brief("peq", ticket, self.repo)
            for line in want[:-1]:
                self.assertIn(line, text, ticket)
            self.assertIn(f"Ticket {ticket}", text)
        out_file = self.repo / "brief.md"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = dispatch.main(["brief", "peq", "T1", "--out", str(out_file), "--root", str(self.repo)])
        self.assertEqual(code, 0)
        self.assertIn("May change: a.py, b.py", out_file.read_text(encoding="utf-8"))
        # start com o runner falso
        base = run_git(self.repo, "rev-parse", "--short", "feature/peq")
        fake = FakeOrca()
        out: list[str] = []
        code, res = dispatch.start("peq", "PROJ-9", "claude", "claude-sonnet-5-5", self.repo, runner=fake,
                                   emit=out.append)
        self.assertEqual(code, 0, out)
        self.assertEqual((res["ticket"], res["issue"]), ("T1", "PROJ-9"))
        added = fake.calls[1][fake.calls[1].index("--dispatch-add") + 1]
        self.assertTrue(added.startswith(f"T1 · PROJ-9 · base {base} · claude:claude-sonnet-5-5 · "), added)
        self.assertIn("worker-start", fake.keys())
        # ticket errado
        fake2 = FakeOrca()
        out2: list[str] = []
        code, _ = dispatch.start("peq", "PROJ-8", "claude", "claude-sonnet-5-5", self.repo, runner=fake2,
                                 emit=out2.append)
        self.assertEqual(code, 2)
        self.assertEqual(fake2.calls, [])

    def test_settle_small_roda_gate_ticket(self):
        self.spec(SMALL, HANDOFF.format(d="none"))
        base = self.commit()
        run_git(self.repo, "checkout", "-q", "-b", "feature/peq")
        self.spec(SMALL, HANDOFF.format(d=entry("T1", base).replace("PROJ-1", "PROJ-9")))
        after = self.commit("dispatch")
        run_git(self.repo, "checkout", "-q", "-b", "ticket/t1")
        (self.repo / "a.py").write_text("x = 1\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat(a): faz a coisa", "-m", "Refs SC-197\n\nRefs: PROJ-9")
        run_git(self.repo, "checkout", "-q", "feature/peq")
        fake = FakeGate()
        out: list[str] = []
        code = dispatch.settle("peq", "PROJ-9", "ticket/t1", self.repo, runner=fake, emit=out.append)
        self.assertEqual(code, 0, out)
        self.assertEqual(len(fake.gates()), 1)
        self.assertLess(fake.gates()[0], fake.merges()[0])
        self.assertEqual(fake.calls[fake.gates()[0]][2:6], ["ticket", "peq", "T1", f"{base}..ticket/t1"])
        self.assertEqual(run_git(self.repo, "log", "-1", "--format=%s"), "merge: integra T1 (PROJ-9) em feature/peq")
        # o gate de verdade, sobre o mesmo intervalo, olha o May change da spec SMALL
        res = run_gates.run_stage("ticket", "peq", self.repo, ticket="T1", rng=f"{after}..ticket/t1")
        self.assertTrue(all(r.ok for r in res), [r.report() for r in res])
        (self.repo / "fora.py").write_text("y = 1\n", encoding="utf-8")
        run_git(self.repo, "checkout", "-q", "ticket/t1")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat(a): fora", "-m", "Refs: PROJ-9")
        res = run_gates.run_stage("ticket", "peq", self.repo, ticket="T1", rng=f"{after}..ticket/t1")
        self.assertFalse(all(r.ok for r in res))
        self.assertTrue(any("fora.py" in e for r in res for e in r.errors), [r.report() for r in res])

    # --- R5 -------------------------------------------------------------------------------------
    def test_q_waive(self):
        self.spec(SMALL)
        out: list[str] = []
        self.assertEqual(dispatch.q_waive("peq", self.repo, emit=out.append), 0)
        vpath = self.fdir / "verification.md"
        self.assertEqual(vpath.read_bytes(), WAIVED.encode("utf-8"))
        self.assertIn("**Verification:** waived (PEQUENA)", vpath.read_text(encoding="utf-8").splitlines())
        self.assertIn("Q dispensado: tarefa PEQUENA (D-a).", vpath.read_text(encoding="utf-8").splitlines())
        self.assertEqual(dispatch.q_waive("peq", self.repo, emit=out.append), 0)  # de novo: o mesmo conteúdo
        self.assertEqual(vpath.read_bytes(), WAIVED.encode("utf-8"))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(dispatch.main(["q-waive", "peq", "--root", str(self.repo)]), 0)
        # W3: um verification.md do Q (sem o marcador waived) nunca é sobrescrito
        report = "# peq: Verification\n\n**Verification:** pass\n\n| Check | Result |\n|---|---|\n| C1 | pass |\n"
        vpath.write_bytes(report.encode("utf-8"))
        before = vpath.read_bytes()
        refusal = "q-waive recusado: verification.md já existe (relatório do Q)"
        lines = []
        self.assertEqual(dispatch.q_waive("peq", self.repo, emit=lines.append), 2)
        self.assertEqual(lines, [refusal])
        self.assertEqual(vpath.read_bytes(), before)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(dispatch.main(["q-waive", "peq", "--root", str(self.repo)]), 2)
        self.assertEqual(buf.getvalue().strip(), refusal)
        self.assertEqual(vpath.read_bytes(), before)
        vpath.write_bytes(WAIVED.encode("utf-8"))  # sobre um arquivo waived continua funcionando
        self.assertEqual(dispatch.q_waive("peq", self.repo, emit=out.append), 0)
        self.assertEqual(vpath.read_bytes(), WAIVED.encode("utf-8"))
        for size in ("MEDIUM", "LARGE", "COMPLEX"):
            with self.subTest(size=size):
                vpath.unlink(missing_ok=True)
                self.spec(SMALL.replace("**Size**: SMALL", f"**Size**: {size}"))
                before = tree_bytes(self.repo / ".specs")
                lines: list[str] = []
                self.assertEqual(dispatch.q_waive("peq", self.repo, emit=lines.append), 2)
                self.assertEqual(lines, [f"q-waive recusado: só a PEQUENA dispensa o Q (Size: {size})"])
                self.assertEqual(tree_bytes(self.repo / ".specs"), before)
                self.assertFalse(vpath.exists())
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    self.assertEqual(dispatch.main(["q-waive", "peq", "--root", str(self.repo)]), 2)
                self.assertEqual(buf.getvalue().strip(), lines[0])
                self.assertEqual(tree_bytes(self.repo / ".specs"), before)

    # --- R6 -------------------------------------------------------------------------------------
    def test_done_waived(self):
        self.done_repo()
        for strict in (False, True):
            res = validate_verification.evaluate("peq", self.repo, strict)
            self.assertEqual((res.errors, res.warnings), ([], ["Q dispensado (PEQUENA)"]), strict)
            results = run_gates.run_stage("done", "peq", self.repo, strict=strict)
            self.assertEqual(run_gates.render("done", results)[1], 0)
        # fim a fim: o arquivo que o q-waive grava é o que o gate lê
        (self.fdir / "verification.md").unlink()
        self.assertEqual(dispatch.q_waive("peq", self.repo, emit=lambda m: None), 0)
        self.commit("waive")
        self.assertEqual(validate_verification.evaluate("peq", self.repo, True).errors, [])
        # o proofs.md continua exigido
        (self.fdir / "proofs.md").unlink()
        errs = validate_verification.evaluate("peq", self.repo).errors
        self.assertEqual(len(errs), 1)
        self.assertIn("falta proofs.md", errs[0])
        # waived fora da PEQUENA é erro
        self.done_repo(SMALL.replace("**Size**: SMALL", "**Size**: MEDIUM"))
        (self.fdir / "spec.md").write_text(
            SMALL.replace("**Size**: SMALL", "**Size**: MEDIUM").replace(
                "**Linear**: PROJ-9", "**Approved**: 2026-11-19 - user: \"sim\"\n**Linear**: PROJ-9")
            + HANDOFF.format(d="none"), encoding="utf-8", newline="\n")
        self.commit("medium aprovada")
        errs = validate_verification.evaluate("peq", self.repo).errors
        self.assertIn("`**Verification:** waived` só vale para a PEQUENA", errs)
        # degraded vence waived: as tabelas voltam a ser exigidas
        self.done_repo(verification=WAIVED + "**Verification:** degraded\n")
        errs = validate_verification.evaluate("peq", self.repo).errors
        self.assertTrue(any("sem tabela em `## Checks`" in e for e in errs), errs)
        self.assertFalse(any("waived" in e for e in errs), errs)
        # só `waived` como palavra inteira dispensa: o resto não dispensa as tabelas
        for value in ("waivedness", "unwaived", "waived-x", "waived (OUTRA)"):
            with self.subTest(value=value):
                self.done_repo(verification=f"# peq: Verification{NL}{NL}**Verification:** {value}{NL}")
                res = validate_verification.evaluate("peq", self.repo)
                self.assertTrue(any("sem tabela em `## Checks`" in e for e in res.errors), res.errors)
                self.assertNotIn("Q dispensado (PEQUENA)", res.warnings)

    # --- R7 -------------------------------------------------------------------------------------
    def test_textos_fluxo_pequena(self):
        base = ROOT / "skills"
        files = {
            "execute": base / "engajar" / "references" / "execute.md",
            "engajar": base / "engajar" / "SKILL.md",
            "risk": base / "engajar" / "references" / "risk-sizing.md",
            "state": base / "engajar" / "references" / "state-format.md",
            "piloto": base / "piloto-automatico" / "SKILL.md",
        }
        text = {k: p.read_text(encoding="utf-8") for k, p in files.items()}
        for key, body in text.items():
            for banned in ("inline checks", "checks inline"):
                self.assertNotIn(banned, body, f"{key} ainda diz {banned!r}")
        execute = text["execute"]
        sec8 = execute[execute.index("## 8. MEDIUM and SMALL"):]
        for needle in ("**Size**: SMALL", "## Scope", "## Checks", "**May change**:", "**Linear**:",
                       'dispatch.py" start', 'dispatch.py" settle', 'run_gates.py" proofs',
                       'dispatch.py" q-waive <slug>', "**Verification:** waived (PEQUENA)",
                       "run_gates.py done <slug>",
                       "no approval", "PEQUENA passou do limite"):
            with self.subTest(needle=needle):
                self.assertIn(needle, sec8)
        flat = " ".join(sec8.split())
        self.assertIn("4. PR in modes 3/4 and the Worf on the PR (section \"Review (Worf)\") stay.", flat)
        self.assertIn("The Guinan is **not** invoked: no retro for a PEQUENA task.", flat)
        route = next(ln for ln in text["engajar"].splitlines() if ln.startswith("| PEQUENA"))
        self.assertIn("spec mínima do Picard + LaForge (Q dispensado)", route)
        flow = next(ln for ln in text["risk"].splitlines() if ln.startswith("| PEQUENA"))
        self.assertIn("spec mínima do Picard + LaForge (Q dispensado)", flow.split("|")[3])
        self.assertIn("**Size:** SMALL | MEDIUM | LARGE | COMPLEX", text["state"])
        pil = next(ln for ln in text["piloto"].splitlines() if ln.startswith("PEQUENA:"))
        self.assertIn("spec mínima do Picard + LaForge, Q dispensado", pil)
        self.assertIn("execute.md", pil)

    # --- R8 -------------------------------------------------------------------------------------
    def test_decisions_pequena_minima(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        start = text.index("### SC-197:")
        nxt = text.find("\n### ", start + 1)
        entry_text = text[start:nxt if nxt != -1 else len(text)]
        for field in ("- **Problema**", "- **Decisão**", "- **Motivo**", "- **Por que não é bug**"):
            self.assertIn(field, entry_text)
        decision = next(ln for ln in entry_text.splitlines() if ln.startswith("- **Decisão"))
        for phrase in (
            # R1 e R2
            "`**Size**: SMALL` (ou `PEQUENA`)", "só `## Scope` não vazia, `## Checks` com ao menos um check, "
            "`**May change**:` e `**Linear**:` com um ID",
            "mais de 5 checks", "mais de 3 entradas no `**May change**:` sem contar `DECISIONS.md`, `CHANGELOG.md` e "
            "entradas terminadas em `/`",
            "`PEQUENA passou do limite (<n> checks, <m> arquivos): reclassifique para MÉDIA`",
            # R3
            "a D-a", "spec mínima sem aprovação", "`run_gates.py execute` e o gate `done` aceitam a spec SMALL sem a "
            "linha `**Approved**`", "MEDIUM, LARGE e COMPLEX sem a linha continuam com erro",
            # R4
            "`dispatch.py brief`, `start` e `settle` tratam a spec SMALL sem `tasks.md` como `T1`", "gate `ticket` antes do merge",
            # R5
            "`q-waive`", "`**Verification:** waived (PEQUENA)`", "`Q dispensado: tarefa PEQUENA (D-a).`",
            "`q-waive recusado: só a PEQUENA dispensa o Q (Size: <size>)`", "sai com 2", "sem gravar",
            # R6
            "aviso `Q dispensado (PEQUENA)`", "continua aviso com `--strict`", "`proofs.md` continua exigido",
            "`**Verification:** waived só vale para a PEQUENA`", "`degraded` vale sobre `waived`",
            # R7
            "a dispensa da Guinan", "Worf no PR", "`execute.md` (seção 8", "`risk-sizing.md`", "`state-format.md`",
            "`piloto-automatico`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, decision)
        why = next(ln for ln in entry_text.splitlines() if ln.startswith("- **Por que não é bug"))
        for name in ("test_spec_small_minima", "test_spec_small_limite", "test_small_sem_aprovacao",
                     "test_dispatch_small_t1", "test_settle_small_roda_gate_ticket", "test_q_waive",
                     "test_done_waived", "test_textos_fluxo_pequena", "test_decisions_pequena_minima"):
            with self.subTest(test=name):
                self.assertIn(f"`{name}`", why)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog[changelog.index("## [Unreleased]"):]
        unreleased = unreleased[:unreleased.find("\n## [", 5)] if "\n## [" in unreleased[5:] else unreleased
        self.assertTrue(any("(SC-197)" in ln and "PEQUENA" in ln for ln in unreleased.splitlines()))
        gates = (ROOT / "tests" / "test_gates.py").read_text(encoding="utf-8")
        self.assertNotIn("small_rejected", gates)
        self.assertNotRegex(gates, r"\*\*Size\*\*: SMALL")


if __name__ == "__main__":
    unittest.main()
