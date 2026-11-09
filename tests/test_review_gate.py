"""Tests for scripts/review/review_gate.py (R4-R10)."""
from __future__ import annotations

import copy
import json
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


def load(name: str) -> dict:
    return json.loads((REVIEW / name).read_text(encoding="utf-8"))


def gate(data: dict):
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "review.json"
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        res = subprocess.run([sys.executable, "-I", str(SCRIPT), str(p)], capture_output=True)
    return res.returncode, res.stdout.decode("utf-8")


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


if __name__ == "__main__":
    unittest.main()
