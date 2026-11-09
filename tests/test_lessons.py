"""Tests for scripts/lessons.py (R22, R23)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

SCRIPT = ROOT / "scripts" / "lessons.py"


def run(root: Path, *args: str):
    res = subprocess.run([sys.executable, "-I", str(SCRIPT), "--root", str(root), *args],
                         capture_output=True, stdin=subprocess.DEVNULL)
    return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")


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
