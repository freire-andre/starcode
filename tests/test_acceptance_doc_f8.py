"""R37: aceite real da Fase 8 (nova-missao, scaffold e gates) registrado em docs/aceite/fase-8.md."""
from __future__ import annotations

import re
import unittest

from helpers import ROOT

import scaffold

DOC = ROOT / "docs" / "aceite" / "fase-8.md"
SECTIONS = (
    "Nova missão: python-flask + postgresql",
    "Nova missão: tauri",
    "Scaffold e gates por perfil",
    "Série fora da testada",
    "Contêineres efêmeros",
)
SOURCES = r"\((?:pypi|npm|crates|dockerhub)[,)]"
DATE = r"\b20\d\d-\d\d-\d\d\b"


PROFILES = ROOT / "profiles"
GATE_KEYS = ("lint", "typecheck", "unit", "build", "integration")
PASS_LINE = re.compile(r"`PASS ([^`]+)`")
# seção -> perfis cujos gates cada cenário tem de cobrir (o 3º cenário tem um perfil por item da lista)
PROFILES_BY_SECTION = {
    "Nova missão: python-flask + postgresql": ["python-flask", "postgresql"],
    "Nova missão: tauri": ["tauri"],
    "Série fora da testada": ["python-flask"],
}
PER_PROFILE_BULLET = (
    ("**rust**", ["rust"]), ("**typescript**", ["typescript"]), ("**gpui**", ["gpui"]),
    ("**python-flask + mysql**", ["python-flask", "mysql"]),
)


def _expected(names: list[str]) -> list[str]:
    """Install de todos os perfis e depois os gates na ordem de GATE_ORDER, lidos do profile.yaml."""
    docs = [scaffold.loads((PROFILES / n / "profile.yaml").read_text(encoding="utf-8")) for n in names]
    out = [str(c) for d in docs for c in d.get("install") or []]
    for d in docs:
        for key in GATE_KEYS:
            for g in (d.get("gates") or {}).get(key) or []:
                cmd, cwd = (str(g.get("run") or g.get("cmd")), g.get("cwd")) if isinstance(g, dict) else (str(g), None)
                out.append(f"{cmd} [{cwd}]" if cwd else cmd)
    return out


def _bullet(body: str, label: str) -> str:
    items = re.split(r"^- (?=\*\*)", body, flags=re.M)
    found = [i for i in items if i.startswith(label)]
    assert len(found) == 1, f"item {label} ausente ou repetido"
    return found[0]


def _parts() -> dict[str, str]:
    text = DOC.read_text(encoding="utf-8")
    return {p.split("\n", 1)[0].strip(): p for p in re.split(r"^## ", text, flags=re.M)[1:]}


class AcceptanceDocF8Tests(unittest.TestCase):
    def test_doc_has_five_sections_and_versions_table(self):
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            self.assertRegex(parts[name], r"\*\*Resultado\*\*: \S", f"{name}: sem **Resultado**")
        self.assertIn("Versões", parts)
        self.assertIn("| Item | Versão |", parts["Versões"])

    def test_fase8_acceptance_all_scenarios_approved(self):
        parts = _parts()
        for name in SECTIONS:
            self.assertIn(name, parts, f"falta a seção {name}")
            body = parts[name]
            self.assertRegex(body, r"\*\*Resultado\*\*: aprovado\b", f"{name}: sem **Resultado**: aprovado")
            self.assertNotIn("reprovado", body, f"{name}: reprovado")
            self.assertNotIn("pendente", body, f"{name}: campo pendente")
        for name in SECTIONS[:4]:
            body = parts[name]
            self.assertRegex(body, SOURCES, f"{name}: versões sem fonte")
            self.assertRegex(body, DATE, f"{name}: sem data")
            self.assertRegex(body, r"\bPASS\b", f"{name}: sem linhas PASS")
            self.assertNotRegex(body, r"^\s*(?:- )?FAIL\b", f"{name}: linha FAIL")
        for name, profiles in PROFILES_BY_SECTION.items():
            self.assertEqual(PASS_LINE.findall(parts[name]), _expected(profiles),
                             f"{name}: PASS não cobre exatamente os gates de {profiles}")
        body = parts["Scaffold e gates por perfil"]
        for label, profiles in PER_PROFILE_BULLET:
            self.assertEqual(PASS_LINE.findall(_bullet(body, label)), _expected(profiles),
                             f"{label}: PASS não cobre exatamente os gates de {profiles}")
        self.assertNotRegex(body, r"\bFAIL\b", "cenário por perfil com FAIL")
        pend = parts["Achados e pendências"]
        items = re.findall(r"^\d+\. (.*)$", pend, flags=re.M)
        self.assertTrue(items)
        for it in items:
            if it.startswith("**Limpeza**"):  # pastas fora do repo, a cargo do usuário
                continue
            self.assertTrue(it.startswith("**Corrigido"), f"pendência aberta: {it[:70]}")
        for name in SECTIONS[:2]:
            self.assertIn(".specs/stack/", parts[name], f"{name}: sem as entradas do cache")
        serie = parts["Série fora da testada"]
        self.assertRegex(serie, r"(?s)exit 5.*\*\*`new --pin-tested`\*\*: exit 0", "série: exit 5 e depois exit 0")
        containers = parts["Contêineres efêmeros"]
        self.assertIn("docker ps -a", containers)
        eph = [ln for ln in containers.splitlines() if "starcode-eph-" in ln]
        self.assertTrue(eph, "contêineres: sem a conclusão sobre starcode-eph-")
        for ln in eph:
            self.assertRegex(ln, r"\b(zero|nenhum)\b", f"restou contêiner starcode-eph-: {ln}")
        self.assertNotIn("pendente", parts["Versões"], "tabela de versões incompleta")


if __name__ == "__main__":
    unittest.main()
