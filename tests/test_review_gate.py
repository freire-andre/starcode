"""Tests for scripts/review/review_gate.py (R4-R10)."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROOT

sys.path.insert(0, str(ROOT / "scripts" / "review"))
import review_gate  # noqa: E402

SCRIPT = ROOT / "scripts" / "review" / "review_gate.py"
REVIEW = FIXTURES / "review"
CRLF, LF = chr(13) + chr(10), chr(10)  # o stdout no Windows sai com CRLF


def load(name: str) -> dict:
    return json.loads((REVIEW / name).read_text(encoding="utf-8"))


def gate(data: dict):
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "review.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        res = subprocess.run([sys.executable, "-I", str(SCRIPT), str(p)], capture_output=True)
    return res.returncode, res.stdout.decode("utf-8").replace(CRLF, LF)


def finding(fid="W1", sev="should-fix", **kw) -> dict:
    f = {"id": fid, "severity": sev, "path": "a.py", "line": 1, "body": "problema real",
         "evidence": "a.py:1"}
    f.update(kw)
    return f


def review(findings, verdict=None, **kw) -> dict:
    v = verdict or review_gate.compute_verdict(findings)
    d = {"round": 1, "verdict": v, "summary": f"TL;DR: {v} - teste", "findings": findings,
         "carryover": {}}
    d.update(kw)
    return d


class ReviewGateTests(unittest.TestCase):
    def test_fixtures_pass(self) -> None:
        for name in ("review_ok.json", "review_clean.json"):
            self.assertEqual(gate(load(name)), (0, ""), name)

    def test_gate_rejects_severity_nits_and_missing_evidence(self) -> None:
        code, out = gate(review([finding(sev="critical")], verdict="APPROVE"))
        self.assertEqual(code, 1)
        self.assertIn('W1: severidade "critical" inválida', out)
        code, out = gate(review([finding(f"W{i}", "nit") for i in range(6)]))
        self.assertEqual(code, 1)
        self.assertIn("nits: 6 acima do limite de 5", out)
        self.assertEqual(gate(review([finding(f"W{i}", "nit") for i in range(5)]))[0], 0)
        for bad in ("", "sem formato", "http://x.com", "a.py:", None):
            for sev in ("blocker", "should-fix"):
                code, out = gate(review([finding(sev=sev, evidence=bad)]))
                self.assertEqual(code, 1, (sev, bad))
                self.assertIn(f"W1: {sev} sem evidence válida", out)
        for good in ("src/a.py:10", "https://docs.x.dev/a", "/org/lib", "/org/lib/v1.2"):
            self.assertEqual(gate(review([finding(evidence=good)])), (0, ""), good)

    def test_gate_requires_tldr_with_verdict(self) -> None:
        d = review([])
        d["summary"] = "APPROVE - sem achados"
        code, out = gate(d)
        self.assertEqual(code, 1)
        self.assertIn('summary: deve começar com "TL;DR:"', out)
        d["summary"] = "TL;DR: tudo certo"
        code, out = gate(d)
        self.assertEqual(code, 1)
        self.assertIn("summary: deve conter o veredito APPROVE", out)

    def test_compute_verdict_mapping(self) -> None:
        cv = review_gate.compute_verdict
        self.assertEqual(cv([]), "APPROVE")
        self.assertEqual(cv([finding(sev="nit")]), "APPROVE")
        self.assertEqual(cv([finding(sev="should-fix")]), "COMMENT")
        self.assertEqual(cv([finding(sev="should-fix"), finding("W2", "blocker")]), "REQUEST_CHANGES")
        self.assertEqual(cv([finding(sev="blocker", state="rejected")]), "APPROVE")
        self.assertEqual(cv([finding(sev="blocker", hardening=True)]), "APPROVE")
        self.assertEqual(cv([finding(sev="pre-existing")]), "APPROVE")
        self.assertEqual(cv([finding(sev="blocker", hardening=True), finding("W2")]), "COMMENT")
        self.assertEqual(review_gate.EMOJI, {"blocker": "🔴", "should-fix": "🟠", "nit": "🟡",
                                             "pre-existing": "🟣"})
        code, out = gate(review([finding(sev="blocker")], verdict="COMMENT"))
        self.assertEqual(code, 1)
        self.assertIn("verdict: esperado REQUEST_CHANGES, recebido COMMENT", out)

    def test_gate_rejects_banned_terms_accent_insensitive(self) -> None:
        code, out = gate(review([finding(body="Ótimo trabalho aqui")]))
        self.assertEqual(code, 1)
        self.assertIn('W1: termo proibido "otimo trabalho"', out)
        for text in ("EXCELENTE", "Vale ressaltar isto", "GREAT JOB", "Parabéns"):
            code, out = gate(review([finding(body=text)]))
            self.assertEqual(code, 1, text)
            self.assertIn("W1: termo proibido", out)
        d = review([])
        d["summary"] = "TL;DR: APPROVE - vale ressaltar"
        self.assertIn('summary: termo proibido "vale ressaltar"', gate(d)[1])
        self.assertEqual(gate(review([finding(body="a função simplificada falha")])), (0, ""))

    def test_gate_round_convergence_rules(self) -> None:
        for rnd in (2, 3):
            code, out = gate(review([finding("W9", "should-fix")], round=rnd,
                                    carryover={"W1": "open"}))
            self.assertEqual(code, 1)
            self.assertIn(f"round {rnd}: só verificação de resolução e blockers novos", out)
            self.assertEqual(gate(review([finding("W9", "blocker")], round=rnd,
                                         carryover={"W1": "resolved"})), (0, ""))
            self.assertEqual(gate(review([finding("W1", "should-fix")], round=rnd,
                                         carryover={"W1": "open"})), (0, ""))
        code, out = gate(review([], round=4))
        self.assertEqual(code, 1)
        self.assertIn("round: limite de 3 rodadas", out)
        self.assertEqual(gate(review([finding("W9", "should-fix")], round=1))[0], 0)

    def test_gate_security_fields_required(self) -> None:
        base = load("review_ok.json")
        for name in review_gate.SECURITY_FIELDS:
            d = copy.deepcopy(base)
            del d["findings"][0][name]
            code, out = gate(d)
            self.assertEqual(code, 1, name)
            self.assertIn(f"W1: security: campo {name} ausente", out)
            for bad in ([], {}, 0, "   "):
                d = copy.deepcopy(base)
                d["findings"][0][name] = bad
                code, out = gate(d)
                self.assertEqual(code, 1, f"{name}={bad!r}")
                self.assertIn(f"W1: security: campo {name} ausente", out, f"{name}={bad!r}")
        d = copy.deepcopy(base)
        d["findings"][0]["state"] = "maybe"
        code, out = gate(d)
        self.assertEqual(code, 1)
        self.assertIn('W1: security: state "maybe" inválido', out)

    def test_gate_security_states_and_hardening(self) -> None:
        sec = load("review_ok.json")["findings"][0]

        def mk(**kw):
            return {**sec, **kw}

        code, out = gate(review([mk(state="needs-validation", severity="should-fix")]))
        self.assertEqual(code, 1)
        self.assertIn("W1: security: needs-validation exige missing_fact", out)
        self.assertEqual(gate(review([mk(state="needs-validation", severity="should-fix",
                                         missing_fact="versão do proxy")])), (0, ""))
        code, out = gate(review([mk(state="needs-validation", missing_fact="x")]))
        self.assertEqual(code, 1)
        self.assertIn("needs-validation permite no máximo should-fix", out)
        self.assertIn("W1: security: rejected exige reason", gate(review([mk(state="rejected")]))[1])
        self.assertEqual(gate(review([mk(state="rejected", reason="barrado pelo WAF")],
                                     verdict="APPROVE")), (0, ""))
        code, out = gate(review([mk(state="rejected", reason="barrado pelo WAF")],
                                verdict="REQUEST_CHANGES"))
        self.assertIn("verdict: esperado APPROVE, recebido REQUEST_CHANGES", out)
        self.assertEqual(gate(review([mk(hardening=True)], verdict="APPROVE")), (0, ""))

    def test_require_text_tabela(self) -> None:  # R1
        for v in ("texto", " a ", "0"):
            self.assertIs(review_gate.require_text(v), True, repr(v))
        for v in (None, "", "   ", "\t\n", [], {}, 0, False, ["x"], {"a": 1}, 1, True):
            self.assertIs(review_gate.require_text(v), False, repr(v))
        self.assertFalse(hasattr(review_gate, "blank"))
        self.assertNotIn("blank(", SCRIPT.read_text(encoding="utf-8"))
        base = {k: "x" for k in review_gate.SECURITY_FIELDS if k != "state"}
        for field in review_gate.SECURITY_FIELDS:
            for bad in ([], {}, 0, False, "  ", "", None):
                f = finding(category="security", state="confirmed", **base)
                f[field] = bad
                self.assertEqual(gate(review([f])), (1, f"W1: security: campo {field} ausente\n"),
                                 f"{field}={bad!r}")
            if field != "state":
                for good in ("x", " x ", "0"):
                    f = finding(category="security", state="confirmed", **base)
                    f[field] = good
                    self.assertEqual(gate(review([f])), (0, ""), f"{field}={good!r}")
        for bad in ([], {}, 0, False, "  ", "", None):  # campo condicional missing_fact
            f = finding(category="security", state="needs-validation", **base)
            if bad is not None:
                f["missing_fact"] = bad
            self.assertEqual(gate(review([f])),
                             (1, "W1: security: needs-validation exige missing_fact\n"), repr(bad))
        f = finding(category="security", state="needs-validation", missing_fact="versão do proxy", **base)
        self.assertEqual(gate(review([f])), (0, ""))
        for bad in ([], {}, 0, False, "  ", "", None):  # campo condicional reason
            f = finding(category="security", state="rejected", **base)
            if bad is not None:
                f["reason"] = bad
            self.assertEqual(gate(review([f], verdict="APPROVE")),
                             (1, "W1: security: rejected exige reason\n"), repr(bad))
        f = finding(category="security", state="rejected", reason="barrado pelo WAF", **base)
        self.assertEqual(gate(review([f], verdict="APPROVE")), (0, ""))

    def test_help_sai_com_zero(self) -> None:  # R2
        for flag in ("--help", "-h"):
            res = subprocess.run([sys.executable, "-I", str(SCRIPT), flag], capture_output=True)
            self.assertEqual(res.returncode, 0, flag)
            self.assertIn("review.json", res.stdout.decode("utf-8"))

    def test_uso_e_codigos_mantidos(self) -> None:  # R3
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            ok = tmp / "ok.json"
            ok.write_bytes((REVIEW / "review_clean.json").read_bytes())
            bad = tmp / "bad.json"
            bad.write_text("{nao e json", encoding="utf-8")
            viol = tmp / "viol.json"
            viol.write_text(json.dumps(review([finding(sev="nit", body="obviously x")])), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in tmp.iterdir()}

            def run(*args):
                return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True,
                                      cwd=t)
            for args in ((), (str(ok), str(ok))):
                res = run(*args)
                self.assertNotEqual(res.returncode, 0, args)
                self.assertEqual(res.stdout, b"", args)
            hy = tmp / "-review.json"  # caminho válido que começa com hífen
            hy.write_bytes(ok.read_bytes())
            hyv = tmp / "-viol.json"
            hyv.write_bytes(viol.read_bytes())
            before = {p.name: p.read_bytes() for p in tmp.iterdir()}
            self.assertEqual((run(str(ok)).returncode, run(str(ok)).stdout), (0, b""))
            res = run(str(bad))
            try:
                json.loads(bad.read_text(encoding="utf-8"))
            except ValueError as e:
                erro = str(e)
            self.assertEqual((res.returncode, res.stdout.decode("utf-8").replace(CRLF, LF)),
                             (1, f"summary: review.json ilegível: {erro}\n"))
            viol_out = 'W1: termo proibido "obviously"\n'
            res = run(str(viol))
            self.assertEqual((res.returncode, res.stdout.decode("utf-8").replace(CRLF, LF)), (1, viol_out))
            res = run("-review.json")
            self.assertEqual((res.returncode, res.stdout, res.stderr), (0, b"", b""))
            res = run("-viol.json")
            self.assertEqual((res.returncode, res.stdout.decode("utf-8").replace(CRLF, LF), res.stderr),
                             (1, viol_out, b""))
            after = {p.name: p.read_bytes() for p in tmp.iterdir()}
            self.assertEqual(before, after)

    def test_scripts_de_review_respondem_help(self) -> None:  # R4
        scripts = sorted((ROOT / "dist" / "claude" / "scripts" / "review").glob("*.py"))
        self.assertIn("review_gate.py", [p.name for p in scripts])
        for p in scripts:
            res = subprocess.run([sys.executable, "-I", str(p), "--help"], capture_output=True,
                                 stdin=subprocess.DEVNULL, timeout=60)
            self.assertEqual(res.returncode, 0, f"{p.name}: {res.stderr.decode('utf-8', 'replace')}")
            for flag in ("--help", "-h"):  # stdin aberto e sem escrita: --help não pode lê-lo
                proc = subprocess.Popen([sys.executable, "-I", str(p), flag], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    self.fail(f"{p.name} {flag} travou lendo o stdin")
                finally:
                    proc.stdin.close()
                    proc.stdout.close()
                    proc.stderr.close()
                self.assertEqual(proc.returncode, 0, f"{p.name} {flag}")

    def test_retro_fase9_estado(self) -> None:  # R5
        text = (ROOT / ".specs" / "features" / "fase-9-worf-guinan-diagnostico" / "retro.md").read_text(
            encoding="utf-8")
        lines = text.splitlines()
        header = next(ln for ln in lines if ln.startswith("| # |"))
        cells = [c.strip() for c in header.strip().strip("|").split("|")]
        self.assertEqual(cells[-1], "Estado")
        rows = [ln for ln in lines if re.match(r"\| \d+ \|", ln)]
        self.assertEqual(len(rows), 7)
        estados = {}
        for ln in rows:
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            self.assertEqual(len(c), len(cells), ln)
            estados[int(c[0])] = c[-1]
        for n in (3, 7):
            self.assertRegex(estados[n], r"^feito em [0-9a-f]{7,40}$", n)
        self.assertEqual(estados[3], estados[7])
        sha = estados[3].split()[-1]  # commit concreto desta feature: existe e tocou o gate
        log = subprocess.run(["git", "log", "--format=%H", "--", "scripts/review/review_gate.py"],
                             cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(log.returncode, 0, log.stderr)
        self.assertTrue(any(h.startswith(sha) for h in log.stdout.split()), sha)
        body = subprocess.run(["git", "show", "-s", "--format=%B", sha], cwd=ROOT, capture_output=True,
                              text=True, stdin=subprocess.DEVNULL)
        self.assertEqual(body.returncode, 0, body.stderr)
        self.assertIn("Refs: SC-190", body.stdout)
        self.assertEqual(estados[4], "aberto: SC-189")
        for n, sc in ((1, 191), (2, 192), (5, 193), (6, 194)):
            self.assertEqual(estados[n], f"aberto: SC-{sc}")

    def test_decisions_retro_fase9(self) -> None:  # R6
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = re.split(r"\n### ", text[text.index("### SC-190:"):], maxsplit=1)[0]
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertIn(field, entry)
        decision = entry.split("**Decisão**", 1)[1].split("**Motivo**", 1)[0]
        for phrase in ("R1: `require_text(value)` em `scripts/review/review_gate.py` devolve True só para uma "
                       "`str` com algum caractere que não seja espaço",
                       "False para `None`, `\"\"`, `\"   \"`, `[]`, `{}`, `0` e `False`",
                       "o `blank()` deixa de existir",
                       "o `check_finding` a usa em todo campo que passava pelo `blank()` (os sete campos de "
                       "segurança, `state`, o `missing_fact` do needs-validation e o `reason` do rejected)",
                       "com exatamente um argumento que não seja `-h` nem `--help`, esse argumento é o "
                       "caminho, mesmo que comece com hífen",
                       "o `scan_bypasses.py` passa a imprimir o uso e sair com 0 em `--help`/`-h` sem ler "
                       "o stdin",
                       "linha 1 aberta na SC-191, linha 2 aberta na SC-192, linha 5 aberta na SC-193 e "
                       "linha 6 aberta na SC-194",
                       "linha 4 aberta na SC-189",
                       "R2: `review_gate.py --help` (ou `-h`) imprime o uso, que cita `review.json`, e sai com 0",
                       "R3: sem argumento ou com mais de um sai com código diferente de 0, sem gravar nada",
                       "com um caminho mantém a saída e os códigos de hoje (0 sem violação, 1 com violação ou "
                       "com JSON ilegível)",
                       "R4: o teste roda cada `dist/claude/scripts/review/*.py` com `--help` e exige exit 0",
                       "sem lista fixa",
                       "R5: a tabela da retro da fase 9 ganha a coluna `Estado` nas 7 linhas",
                       "`feito em <commit ou PR>`, `recusado: <motivo>` ou `aberto: SC-<n>`"):
            self.assertIn(phrase, decision, phrase)
        proof = entry.split("**Por que não é bug**", 1)[1]
        for name in ("test_require_text_tabela", "test_help_sai_com_zero", "test_uso_e_codigos_mantidos",
                     "test_scripts_de_review_respondem_help", "test_retro_fase9_estado",
                     "test_decisions_retro_fase9"):
            self.assertIn(name, proof, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("(SC-190)", unreleased)


if __name__ == "__main__":
    unittest.main()
