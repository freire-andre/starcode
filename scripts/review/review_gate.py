#!/usr/bin/env python3
# Origem: adaptado de the-judge/scripts/review_gate.py (the-judge 1.4.0, Felipe Rodrigues,
# licença CC-BY-4.0). Mudanças: formato review.json do StarCode, saída `<local>: <regra>`,
# portão de evidência de segurança (escrito do zero a partir do plano §3.1, inspirado na
# Cloudflare security-audit-skill, MIT), só stdlib e sem rede.
"""Gate do review do Worf (R4-R10). Só stdlib, sem rede.

  review_gate.py <review.json>

Sai com 0 sem violações. Com violações, sai com 1 e imprime `<local>: <regra>` por violação
(`<local>` = summary, verdict, round ou W<n>).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

SEVERITIES = ("blocker", "should-fix", "nit", "pre-existing")
EMOJI = {"blocker": "🔴", "should-fix": "🟠", "nit": "🟡", "pre-existing": "🟣"}
VERDICTS = ("APPROVE", "COMMENT", "REQUEST_CHANGES")
MAX_NITS = 5
MAX_ROUNDS = 3
SECURITY_FIELDS = ("attacker", "entry", "control", "boundary", "impact", "proof", "state")
SECURITY_STATES = ("confirmed", "needs-validation", "rejected")

BANNED_TERMS = [
    # EN
    "obviously", "simply", "delve", "seamless", "streamline", "leverage", "crucial", "pivotal",
    "tapestry", "foster", "landscape", "furthermore", "moreover", "kudos", "awesome", "sorry",
    "apologies", "excellent", "you forgot", "you missed", "great job", "nice work", "good catch",
    "hope this helps", "let me know", "feel free", "happy to", "it's worth noting",
    "its worth noting", "worth noting", "note that", "just a heads up", "as you can see",
    "thanks for", "thank you for", "i think maybe", "perhaps consider", "you might want to",
    "it would be beneficial", "testament to",
    # PT-BR
    "obviamente", "simplesmente", "ademais", "parabens", "desculpe", "desculpa", "excelente",
    "otimo trabalho", "bom trabalho", "espero que ajude", "fique a vontade",
    "sinta-se a vontade", "vale ressaltar", "vale a pena notar", "vale notar", "note que",
    "alem disso", "voce esqueceu", "com toda certeza",
]

INTERNAL_REF = re.compile(r"^\S.*:\d+$")
CONTEXT7_ID = re.compile(r"^/[\w.-]+/[\w.-]+(?:/[\w.-]+)?$")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


_BANNED = [norm(t) for t in BANNED_TERMS]


def banned_in(text: str) -> list[str]:
    n = norm(text)
    return [t for t in _BANNED
            if re.search(r"(?<![\w])" + re.escape(t) + r"(?![\w])", n)]


def evidence_ok(ev) -> bool:
    items = ev if isinstance(ev, list) else [ev]
    items = [e.strip() for e in items if isinstance(e, str) and e.strip()]
    if not items:
        return False
    return all((e.startswith("https://") and len(e) > 8) or INTERNAL_REF.match(e)
               or CONTEXT7_ID.match(e) for e in items)


def counts(f: dict) -> bool:
    """Conta no veredito? Não contam: rejected, hardening e pre-existing."""
    return not (f.get("state") == "rejected" or f.get("hardening") is True
                or f.get("severity") == "pre-existing")


def compute_verdict(findings: list) -> str:
    live = [f for f in findings if isinstance(f, dict) and counts(f)]
    sevs = {f.get("severity") for f in live}
    if "blocker" in sevs:
        return "REQUEST_CHANGES"
    if "should-fix" in sevs:
        return "COMMENT"
    return "APPROVE"


def require_text(value) -> bool:
    """True só para str com algum caractere que não seja espaço."""
    return isinstance(value, str) and bool(value.strip())


def check_finding(label: str, f: dict) -> list[str]:
    out: list[str] = []
    sev = f.get("severity")
    if sev not in SEVERITIES:
        out.append(f'{label}: severidade "{sev}" inválida')
    elif sev in ("blocker", "should-fix") and not evidence_ok(f.get("evidence")):
        out.append(f"{label}: {sev} sem evidence válida (arquivo:linha, https://... ou ID do Context7)")
    for t in banned_in(str(f.get("body", ""))):
        out.append(f'{label}: termo proibido "{t}"')
    if f.get("category") == "security":
        for name in SECURITY_FIELDS:
            if not require_text(f.get(name)):
                out.append(f"{label}: security: campo {name} ausente")
        state = f.get("state")
        if require_text(state):
            if state not in SECURITY_STATES:
                out.append(f'{label}: security: state "{state}" inválido')
            elif state == "needs-validation":
                if not require_text(f.get("missing_fact")):
                    out.append(f"{label}: security: needs-validation exige missing_fact")
                if sev == "blocker":
                    out.append(f"{label}: security: needs-validation permite no máximo should-fix")
            elif state == "rejected" and not require_text(f.get("reason")):
                out.append(f"{label}: security: rejected exige reason")
    return out


def check(data: dict) -> list[str]:
    out: list[str] = []
    findings = data.get("findings")
    if not isinstance(findings, list):
        out.append("summary: findings deve ser uma lista")
        findings = []
    findings = [f for f in findings if isinstance(f, dict)]
    summary = data.get("summary") if isinstance(data.get("summary"), str) else ""
    verdict = data.get("verdict")

    nits = sum(1 for f in findings if f.get("severity") == "nit")
    if nits > MAX_NITS:
        out.append(f"nits: {nits} acima do limite de {MAX_NITS}")

    for i, f in enumerate(findings, 1):
        out += check_finding(str(f.get("id") or f"F{i}"), f)

    if not summary.lstrip().startswith("TL;DR:"):
        out.append('summary: deve começar com "TL;DR:"')
    if verdict in VERDICTS and verdict not in summary:
        out.append(f"summary: deve conter o veredito {verdict}")
    for t in banned_in(summary):
        out.append(f'summary: termo proibido "{t}"')

    expected = compute_verdict(findings)
    if verdict != expected:
        out.append(f"verdict: esperado {expected}, recebido {verdict}")

    rnd = data.get("round", 1)
    if not isinstance(rnd, int) or isinstance(rnd, bool) or rnd < 1:
        out.append(f"round: valor inválido {rnd!r}")
    elif rnd > MAX_ROUNDS:
        out.append(f"round: limite de {MAX_ROUNDS} rodadas")
    elif rnd >= 2:
        carry = data.get("carryover")
        carry = carry if isinstance(carry, dict) else {}
        for f in findings:
            if f.get("id") not in carry and f.get("severity") != "blocker":
                out.append(f"round {rnd}: só verificação de resolução e blockers novos ({f.get('id', '?')})")
    return out


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="review_gate.py",
        description="Gate do review do Worf: valida o review.json. Sai com 0 sem violações e "
                    "com 1 com violações ou com review.json ilegível.")
    parser.add_argument("review_json", metavar="review.json", help="caminho do review.json")
    args = parser.parse_args(argv[1:])
    try:
        with open(args.review_json, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("raiz deve ser um objeto")
    except (OSError, ValueError) as e:
        print(f"summary: review.json ilegível: {e}")
        return 1
    violations = check(data)
    for v in violations:
        print(v)
    return 1 if violations else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv))
