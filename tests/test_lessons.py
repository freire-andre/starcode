"""Tests for scripts/lessons.py (R22, R23)."""
from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from helpers import ROOT

SCRIPT = ROOT / "scripts" / "lessons.py"


def run(root: Path, *args: str):
    res = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(root), *args],
                         capture_output=True, stdin=subprocess.DEVNULL)
    return (res.returncode, res.stdout.decode("utf-8").replace("\r\n", "\n"),
            res.stderr.decode("utf-8").replace("\r\n", "\n"))


def add(root: Path, feature="f1", signal="weak_test", source="spec.md:10",
        text="Teste sem asserção não prova o critério", *extra: str):
    return run(root, "add", "--feature", feature, "--signal", signal, "--source", source,
               "--text", text, *extra)


def store(root: Path) -> dict:
    return json.loads((root / ".specs" / "lessons.json").read_text(encoding="utf-8"))


class LessonsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="lessons-test-")
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_lessons_add_rejects_invalid_input(self) -> None:
        cases = [
            ("signal", dict(signal="inventado")),
            ("source", dict(source="")),
            ("source", dict(source="   ")),
            ("text", dict(text="")),
            ("text", dict(text="x" * 301)),
        ]
        for field, kw in cases:
            code, out, err = add(self.root, **kw)
            self.assertEqual(code, 2, (field, kw))
            self.assertIn(f"{field} inválido:", out + err)
            self.assertFalse((self.root / ".specs" / "lessons.json").exists(), (field, kw))
            self.assertFalse((self.root / ".specs" / "LESSONS.md").exists(), (field, kw))
        code, _, _ = add(self.root, text="x" * 300)
        self.assertEqual(code, 0)
        code, _, _ = add(self.root, feature="f2", signal="review_finding", text="Outra lição válida")
        self.assertEqual(code, 0)

    def test_lessons_dedupe_and_promote_on_two_features(self) -> None:
        self.assertEqual(add(self.root, feature="f1", source="a:1",
                             text="Não use datas locais!")[0], 0)
        self.assertEqual(add(self.root, feature="f1", source="a:2",
                             text="nao use datas locais")[0], 0)
        lessons = store(self.root)["lessons"]
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["status"], "candidate")
        self.assertEqual(lessons[0]["features"], ["f1"])  # mesma feature não conta duas vezes
        self.assertEqual(lessons[0]["sources"], ["a:1", "a:2"])
        self.assertEqual(add(self.root, feature="f2", source="b:3",
                             text="NÃO USE datas locais.")[0], 0)
        data = store(self.root)
        self.assertEqual(len(data["lessons"]), 1)
        les = data["lessons"][0]
        self.assertEqual(les["id"], "L1")
        self.assertEqual(les["status"], "confirmed")
        self.assertEqual(les["features"], ["f1", "f2"])
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["promote_threshold"], 2)

    def _seed_l1(self) -> None:
        self.assertEqual(add(self.root, "f1", "weak_test", "a:1")[0], 0)

    def _bytes(self):
        return ((self.root / ".specs" / "lessons.json").read_bytes(),
                (self.root / ".specs" / "LESSONS.md").read_bytes())

    def test_lessons_add_id_registra_recorrencia_e_promove(self) -> None:
        self._seed_l1()
        before = store(self.root)["lessons"][0]
        time.sleep(1.1)  # o carimbo tem resolução de 1 s: a janela separa "antes" de "agora"
        t0 = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)
        code, out, err = run(self.root, "add", "--id", "L1", "--feature", "f1", "--signal", "weak_test",
                             "--source", "b:2")
        t1 = _dt.datetime.now(_dt.timezone.utc)
        self.assertEqual((code, out, err), (0, "atualizada L1 (features=1, status=candidate)\n", ""))
        les = store(self.root)["lessons"][0]
        self.assertEqual(les["features"], ["f1"])
        self.assertEqual(les["sources"], ["a:1", "b:2"])
        for k in ("text", "signal", "scope", "created"):
            self.assertEqual(les[k], before[k], k)
        upd = _dt.datetime.strptime(les["updated"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=_dt.timezone.utc)
        self.assertTrue(t0 <= upd <= t1, (t0, upd, t1))
        self.assertGreater(upd, _dt.datetime.strptime(before["updated"], "%Y-%m-%dT%H:%M:%SZ")
                           .replace(tzinfo=_dt.timezone.utc))
        code, out, _ = run(self.root, "add", "--id", "L1", "--feature", "f2", "--signal", "weak_test",
                           "--source", "c:3")
        self.assertEqual((code, out), (0, "atualizada L1 (features=2, status=confirmed) - promovida a confirmed\n"))
        for _ in range(2):
            code, out, _ = run(self.root, "add", "--id", "L1", "--feature", "f2", "--signal", "weak_test",
                               "--source", "c:3")
            self.assertEqual((code, out), (0, "atualizada L1 (features=2, status=confirmed)\n"))
        les = store(self.root)["lessons"][0]
        self.assertEqual(les["features"], ["f1", "f2"])
        self.assertEqual(les["sources"], ["a:1", "b:2", "c:3"])
        self.assertEqual(les["status"], "confirmed")
        self.assertEqual(len(store(self.root)["lessons"]), 1)

    def test_lessons_add_id_sem_caixa_e_text_ignorado(self) -> None:
        self._seed_l1()
        text = store(self.root)["lessons"][0]["text"]
        code, _, err = run(self.root, "add", "--id", "l1", "--feature", "f2", "--signal", "weak_test",
                           "--source", "b:2", "--text", "x" * 301)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(store(self.root)["lessons"][0]["text"], text)
        code, _, _ = run(self.root, "add", "--id", "L1", "--feature", "f3", "--signal", "weak_test",
                         "--source", "b:3")
        self.assertEqual(code, 0)
        self.assertEqual(len(store(self.root)["lessons"]), 1)

    def test_lessons_add_id_invalido_ou_quarentena_sai_2(self) -> None:
        self._seed_l1()
        before = self._bytes()
        base = ("--feature", "f2", "--signal", "weak_test", "--source", "b:2")
        code, out, err = run(self.root, "add", "--id", "L99", *base)
        self.assertEqual((code, out, err), (2, "", "id inválido: nenhuma lição L99\n"))
        self.assertEqual(self._bytes(), before)
        code, out, err = run(self.root, "add", "--id", "", *base, "--text", "nova")
        self.assertEqual((code, out, err), (2, "", "id inválido: nenhuma lição \n"))
        self.assertEqual(self._bytes(), before)
        run(self.root, "add", "--id", "L1", "--feature", "f2", "--signal", "weak_test", "--source", "c:3")
        self.assertEqual(run(self.root, "penalize", "--id", "L1")[0], 0)
        before = self._bytes()
        code, out, err = run(self.root, "add", "--id", "L1", *base)
        self.assertEqual((code, out, err),
                         (2, "", "id inválido: L1 está quarantined; recorrência não tira da quarentena\n"))
        self.assertEqual(self._bytes(), before)
        code, _, err = run(self.root, "add", "--id", "L1", "--feature", "f2", "--signal", "inventado",
                           "--source", "b:2")
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("signal inválido:"), err)
        self.assertEqual(self._bytes(), before)

    def test_lessons_add_sem_id_exige_text(self) -> None:
        code, out, err = run(self.root, "add", "--feature", "f1", "--signal", "weak_test", "--source", "a:1")
        self.assertEqual((code, out, err), (2, "", "text inválido: vazio\n"))
        self.assertFalse((self.root / ".specs" / "lessons.json").exists())
        self.assertFalse((self.root / ".specs" / "LESSONS.md").exists())

    def test_licoes_reprocessadas_n1(self) -> None:
        data = json.loads((ROOT / ".specs" / "lessons.json").read_text(encoding="utf-8"))
        by_id = {x["id"]: x for x in data["lessons"]}
        orig = {
            "L18": {
                "status": "candidate",
                "features": [
                    "ponte-missao-ativa"
                ],
                "sources": [
                    ".specs/features/ponte-missao-ativa/verification.md (rodada 2, C5)"
                ],
                "text": "Teste de texto composto exibido ao usu\u00e1rio compara a string inteira esperada, n\u00e3o substrings soltas que aceitam partes extras ou repetidas."
            },
            "L21": {
                "status": "candidate",
                "features": [
                    "fase-12-robustez"
                ],
                "sources": [
                    "verification.md:C33"
                ],
                "text": "Compare o bloco completo da mensagem de erro com o motivo retornado, n\u00e3o s\u00f3 o prefixo, porque qualquer texto com o prefixo passava no teste."
            },
            "L24": {
                "status": "candidate",
                "features": [
                    "manutencao-retros-f11"
                ],
                "sources": [
                    "verification.md:C32"
                ],
                "text": "Teste de idioma deve verificar o relato inteiro, n\u00e3o s\u00f3 palavras proibidas, porque a asser\u00e7\u00e3o deixava passar texto em portugu\u00eas."
            },
            "L26": {
                "status": "candidate",
                "features": [
                    "ajustes-review-pr39"
                ],
                "sources": [
                    "verification.md:C8 (tests/test_skills_exec.py:18)"
                ],
                "text": "Asser\u00e7\u00e3o sobre texto de contrato deve fixar o comando completo e o comportamento exigido, porque fragmentos aceitam textos que n\u00e3o cumprem o crit\u00e9rio."
            },
            "L29": {
                "status": "candidate",
                "features": [
                    "despacho-media-escopo"
                ],
                "sources": [
                    "verification.md: achado ID em min\u00fascula; spec.md Edge Cases"
                ],
                "text": "D\u00ea a cada item de Edge Cases da spec um check com teste pr\u00f3prio, porque a compara\u00e7\u00e3o sem diferen\u00e7a de mai\u00fasculas estava listada e nenhum check a fixava."
            },
            "L31": {
                "status": "candidate",
                "features": [
                    "q-familia-revendedor"
                ],
                "sources": [
                    "verification.md achado C7 (test_model_info.py:164)"
                ],
                "text": "D\u00ea a cada valor de uma tabela fixada no requisito pelo menos uma linha no teste, porque a tabela de prefixos testava 13 de 15 e o1/o4 ficaram sem prova."
            },
            "L34": {
                "status": "candidate",
                "features": [
                    "setup-grava-config"
                ],
                "sources": [
                    "verification.md:C4"
                ],
                "text": "No teste de uma entrada do DECISIONS.md, asserte os quatro campos (Problema, Decis\u00e3o, Motivo, Por que n\u00e3o \u00e9 bug) dentro da entrada, porque o teste conferia s\u00f3 o cabe\u00e7alho e um termo e passava sem os campos."
            },
            "L37": {
                "status": "candidate",
                "features": [
                    "snapshot-restauracao-segura"
                ],
                "sources": [
                    "verification.md:achado 3"
                ],
                "text": "Para conferir uma lista impressa, compare a lista exata de linhas analisadas, porque assertIn de um trecho aceita caminho maior ou texto extra."
            },
            "L38": {
                "status": "candidate",
                "features": [
                    "impacto-seleciona-real"
                ],
                "sources": [
                    "verification.md:C7"
                ],
                "text": "Quando o requisito fixa uma mensagem ou motivo, compare o texto integral com assertEqual, porque assertIn de um trecho aceita caminho ou texto errado."
            },
            "L39": {
                "status": "candidate",
                "features": [
                    "impacto-seleciona-real"
                ],
                "sources": [
                    "verification.md:C8"
                ],
                "text": "No teste de uma entrada de registro, asserte cada termo que o requisito manda citar, porque o teste conferia s\u00f3 parte deles e passava se um sumisse."
            }
        }
        groups = {
            "L2": (["ponte-missao-ativa", "fase-12-robustez", "manutencao-retros-f11", "ajustes-review-pr39",
                    "snapshot-restauracao-segura", "impacto-seleciona-real",
                    "fase-9-worf-guinan-diagnostico", "guardas-add-commit-powershell", "q-preserva-handoff"],
                   ["L18", "L21", "L24", "L26", "L37", "L38"]),
            "L10": (["fase-11-telas", "despacho-media-escopo", "q-familia-revendedor"], ["L29", "L31"]),
            "L32": (["q-familia-revendedor", "setup-grava-config", "impacto-seleciona-real"], ["L34", "L39"]),
        }
        for canon, (features, repeated) in groups.items():
            les = by_id[canon]
            self.assertEqual(les["status"], "confirmed", canon)
            for f in features:
                self.assertIn(f, les["features"], (canon, f))
            for rid in repeated:
                self.assertIn(f"{rid} ({orig[rid]['sources'][0]})", les["sources"], (canon, rid))
        for rid, want in orig.items():  # as repetidas continuam como estavam
            for k, v in want.items():
                self.assertEqual(by_id[rid][k], v, (rid, k))

    def test_decisions_licoes_recorrencia_por_id(self) -> None:
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text[text.index("### SC-183:"):]
        nxt = entry.find("### SC-", 4)
        entry = entry if nxt == -1 else entry[:nxt]
        for name in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            self.assertEqual(sum(1 for l in entry.splitlines() if l.startswith(f"- **{name}**: ")), 1, name)
        for needle in ("--id", "recorrência", "D-i"):
            self.assertIn(needle, entry, needle)

    def test_lessons_penalize_render_and_corrupt_store(self) -> None:
        add(self.root, feature="f1", text="Lição para quarentena")
        add(self.root, feature="f2", text="Lição para quarentena")
        md = (self.root / ".specs" / "LESSONS.md").read_text(encoding="utf-8")
        for sec in ("## Confirmed", "## Candidates", "## Quarantined"):
            self.assertIn(sec, md)
        self.assertLess(md.index("## Confirmed"), md.index("L1"))
        self.assertLess(md.index("L1"), md.index("## Candidates"))
        # penalize só vale para confirmed
        add(self.root, feature="f3", text="Ainda candidata")
        code, out, err = run(self.root, "penalize", "--id", "L2")
        self.assertEqual(code, 2)
        self.assertEqual(store(self.root)["lessons"][1]["status"], "candidate")
        code, _, _ = run(self.root, "penalize", "--id", "L1")
        self.assertEqual(code, 0)
        self.assertEqual(store(self.root)["lessons"][0]["status"], "quarantined")
        md = (self.root / ".specs" / "LESSONS.md").read_text(encoding="utf-8")
        self.assertGreater(md.index("L1"), md.index("## Quarantined"))
        # list: mais recentes primeiro, filtro por status, json, limit
        code, out, _ = run(self.root, "list", "--status", "all", "--json")
        self.assertEqual(code, 0)
        self.assertEqual({r["id"] for r in json.loads(out)}, {"L1", "L2"})
        code, out, _ = run(self.root, "list", "--status", "quarantined")
        self.assertIn("L1", out)
        code, out, _ = run(self.root, "list", "--status", "all", "--limit", "1", "--json")
        self.assertEqual(len(json.loads(out)), 1)
        code, out, _ = run(self.root, "status")
        self.assertEqual(code, 0)
        self.assertIn("quarantined=1", out)
        # store inválido: sai com 2 e não sobrescreve
        p = self.root / ".specs" / "lessons.json"
        p.write_text("{quebrado", encoding="utf-8")
        for args in (("status",), ("list",), ("prune",),
                     ("add", "--feature", "f", "--signal", "ac_gap", "--source", "s",
                      "--text", "texto qualquer"), ("penalize", "--id", "L1")):
            code, out, err = run(self.root, *args)
            self.assertEqual(code, 2, args)
            self.assertIn("lessons.json inválido:", out + err)
            self.assertEqual(p.read_text(encoding="utf-8"), "{quebrado")

    def test_lessons_init_prune_and_utf8(self) -> None:
        code, _, _ = run(self.root, "init")
        self.assertEqual(code, 0)
        self.assertEqual(store(self.root)["lessons"], [])
        add(self.root, text="Ação não coberta por ícone", source="café:1")
        data = store(self.root)
        data["lessons"][0]["updated"] = "2020-01-01"
        data["lessons"][0]["created"] = "2020-01-01"
        (self.root / ".specs" / "lessons.json").write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
        code, out, _ = run(self.root, "prune")
        self.assertEqual(code, 0)
        self.assertEqual(store(self.root)["lessons"], [])


if __name__ == "__main__":
    unittest.main()
