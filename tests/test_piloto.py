"""Tests for the autopilot: piloto.py (mandate + decision log), the gates accepting a `piloto:` approval only on
tasks.md with a confirmed mandate, the banner line and the skill contents (Troi grill mode, piloto-automatico)."""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase

import banner
import gates_common as gc
import piloto

CLIS = ("claude", "codex", "antigravity", "opencode")
SLUG = "export-csv"


class PilotoCase(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.fdir = self.repo / ".specs" / "features" / SLUG
        self.fdir.mkdir(parents=True)
        piloto.start(SLUG, self.repo)
        self.path = self.fdir / "piloto.md"

    def cli(self, *args, slug=SLUG):
        """Run piloto.py as a process; `slug=None` omits the slug (commands without one)."""
        cmd = [sys.executable, str(ROOT / "scripts" / "piloto.py"), args[0]] + ([slug] if slug else []) + list(args[1:])
        return subprocess.run(cmd + ["--root", str(self.repo)], capture_output=True, text=True, encoding="utf-8")

    def snapshot(self):
        """Bytes of every file under the repo's .specs plus the file list: a refusal must change neither."""
        base = self.repo / ".specs"
        return {str(f.relative_to(base)): f.read_bytes() for f in sorted(base.rglob("*")) if f.is_file()}

    def register_args(self):
        return ("registrar", "--by", "data", "--question", "q", "--options", "a | b", "--decision", "a",
                "--reason", "r", "--basis", "M1")

    def confirmed(self):
        piloto.add_mandate(SLUG, self.repo, "principio", "simplicidade antes de completude", "Q3")
        piloto.add_mandate(SLUG, self.repo, "limite", "nunca adicionar dependência nova", "Q7")
        piloto.confirm(SLUG, self.repo, 'sim, é isso "fechado"')


class PilotoScriptTests(PilotoCase):
    def test_start_is_idempotent_and_fixed_format(self):
        before = self.snapshot()
        first = self.path.read_bytes()
        self.assertIn("já existe (ativo)", piloto.start(SLUG, self.repo))
        self.assertEqual(self.path.read_bytes(), first)
        res = self.cli("start")
        self.assertEqual((res.returncode, res.stdout.strip()), (0, f"piloto.md já existe (ativo): {self.path}"))
        self.assertEqual(self.snapshot(), before)
        text = self.path.read_text(encoding="utf-8")
        self.assertRegex(text, r"\*\*Status:\*\* ativo\n\*\*Iniciado:\*\* \S+Z\n"
                               r"\*\*Mandato confirmado:\*\* pendente\n")
        for needle in ("# Piloto automático: export-csv", "**Status:** ativo", "**Mandato confirmado:** pendente",
                       "## Mandato", "## Decisões"):
            self.assertIn(needle, text)

    def test_no_decision_before_confirmed_mandate(self):
        refused = (1, "ERRO: mandato não confirmado: o piloto ainda não decide nada")
        before = self.snapshot()
        with self.assertRaisesRegex(piloto.PilotoError, "mandato não confirmado"):
            piloto.record(SLUG, self.repo, "data", "q", "a | b", "a", "r", "Q1")
        with self.assertRaisesRegex(piloto.PilotoError, "mandato vazio"):
            piloto.confirm(SLUG, self.repo, "ok")
        self.assertFalse(piloto.is_active(SLUG, self.repo))
        self.assertEqual(self.snapshot(), before)
        res = self.cli("registrar", "--by", "data", "--question", "q", "--options", "a | b", "--decision", "a",
                       "--reason", "r")
        self.assertEqual((res.returncode, res.stdout.strip()), refused)
        self.assertEqual(self.snapshot(), before)
        # a pending mandate (items, no confirmation) still decides nothing
        piloto.add_mandate(SLUG, self.repo, "limite", "x", "Q1")
        before = self.snapshot()
        res = self.cli(*self.register_args())
        self.assertEqual((res.returncode, res.stdout.strip()), refused)
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("### D1", self.path.read_text(encoding="utf-8"))

    def test_mandate_numbered_and_locked_after_confirm(self):
        self.confirmed()
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("- **M1** · princípio · simplicidade antes de completude · origem: Q3", text)
        self.assertIn("- **M2** · limite · nunca adicionar dependência nova · origem: Q7", text)
        self.assertLess(text.index("**M2**"), text.index("## Decisões"))
        self.assertRegex(text, r"\*\*Mandato confirmado:\*\* \d{4}-\d{2}-\d{2} - user: \"sim, é isso 'fechado'\"")
        before = self.snapshot()
        with self.assertRaisesRegex(piloto.PilotoError, "já confirmado"):
            piloto.add_mandate(SLUG, self.repo, "preferencia", "x", "Q9")
        self.assertEqual(self.snapshot(), before)
        res = self.cli("mandato", "--kind", "preferencia", "--text", "x", "--source", "Q9")
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout.strip(), "ERRO: mandato já confirmado: mudanças só com uma nova entrevista "
                                             "(encerre e reinicie o piloto)")
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("M3", self.path.read_text(encoding="utf-8"))
        self.assertTrue(piloto.is_active(SLUG, self.repo))

    def test_record_decisions_confidence_and_review(self):
        self.confirmed()
        self.assertEqual(piloto.record(SLUG, self.repo, "data", "Aprova as tasks?", "sim | ajustes", "sim",
                                       "cobre todos os requisitos", "M1,q3"), "D1 registrada (confiança alta)")
        out = piloto.record(SLUG, self.repo, "laforge", "Usar lib X?", "lib X | código próprio", "código próprio",
                            "opção mais segura", "", "alta")
        self.assertEqual(out, "D2 registrada (confiança baixa, revisar)")  # no basis: never above baixa
        out = piloto.record(SLUG, self.repo, "data", "Pagina?", "sim | não", "não", "sem pedido", "M1", "baixa")
        self.assertEqual(out, "D3 registrada (confiança baixa, revisar)")  # baixa with a basis is flagged too
        text = self.path.read_text(encoding="utf-8")
        self.assertRegex(text, r"### D1 · \S+Z · data · confiança alta\n- \*\*Pergunta:\*\* Aprova as tasks\?")
        self.assertIn("- **Base:** M1, Q3", text)
        self.assertRegex(text, r"### D2 · \S+Z · laforge · confiança baixa · ⚠️ revisar\n")
        self.assertRegex(text, r"### D3 · \S+Z · data · confiança baixa · ⚠️ revisar\n")
        self.assertIn("- **Base:** nenhuma na entrevista (opção mais segura e reversível)", text)
        self.assertEqual(text.count("⚠️ revisar"), 2)  # D1 (alta) is not flagged
        today = dt.date.today().isoformat()
        expected = ["Status: ativo", f"Mandato: 2 item(ns), confirmado em {today}", "Decisões: 3",
                    "Revisar: D2 ⚠️ revisar, D3 ⚠️ revisar"]
        self.assertEqual(piloto.status(SLUG, self.repo), expected)
        res = self.cli("status")
        self.assertEqual((res.returncode, res.stdout.splitlines()), (0, expected))
        with self.assertRaisesRegex(piloto.PilotoError, "inexistente: M9"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "M9")
        with self.assertRaisesRegex(piloto.PilotoError, "--basis aceita"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "R1")

    def test_finish_stops_decisions(self):
        self.confirmed()
        piloto.finish(SLUG, self.repo, "assumo daqui")
        self.assertFalse(piloto.is_active(SLUG, self.repo))
        self.assertIn("**Encerrado:**", self.path.read_text(encoding="utf-8"))
        before = self.snapshot()
        with self.assertRaisesRegex(piloto.PilotoError, "encerrado"):
            piloto.record(SLUG, self.repo, "data", "q", "a", "a", "r", "M1")
        res = self.cli(*self.register_args())
        self.assertEqual((res.returncode, res.stdout.strip()),
                         (1, "ERRO: piloto encerrado: a decisão é do usuário"))
        self.assertEqual(self.snapshot(), before)
        self.assertNotIn("### D1", self.path.read_text(encoding="utf-8"))
        self.assertEqual(piloto.actives(self.repo), [])

    def test_cli_exit_codes(self):
        run = self.cli
        other = self.repo / ".specs" / "features" / "sem-piloto"  # a feature without piloto.md
        other.mkdir(parents=True)
        # 0: success
        self.assertEqual(run("status").returncode, 0)
        self.assertEqual(run("start").returncode, 0)  # already exists: idempotent
        self.assertEqual(run("ativos", slug=None).returncode, 0)
        # 1: feature or piloto missing, invalid slug, rule refused
        sem = ("status", "mandato --kind limite --text x --source Q1", "confirmar --words ok",
               "registrar --by a --question q --options a --decision a --reason r", "encerrar", "ativo")
        for slug in ("nao-existe", "sem-piloto"):
            for cmd in sem:
                res = run(*cmd.split(), slug=slug)
                self.assertEqual(res.returncode, 1, (slug, cmd, res.stdout))
        self.assertEqual(run("start", slug="nao-existe").returncode, 1)
        self.assertEqual(run("start", slug="Nao_Valido").returncode, 1)
        self.assertEqual(run("ativo").returncode, 1)  # pending mandate
        self.assertEqual(run(*self.register_args()).returncode, 1)
        # 2: usage error
        for args, slug in ((("mandato", "--kind", "limite", "--text", "x"), SLUG),  # --source missing
                           (("mandato", "--kind", "invalido", "--text", "x", "--source", "Q1"), SLUG),
                           (("confirmar",), SLUG), (("registrar", "--by", "data"), SLUG),
                           (("status",), None), (("inexistente",), SLUG)):
            res = run(*args, slug=slug)
            self.assertEqual(res.returncode, 2, (args, res.stdout, res.stderr))
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "piloto.py")], capture_output=True, text=True)
        self.assertEqual(res.returncode, 2)
        self.confirmed()
        self.assertEqual(run("ativo").returncode, 0)
        res = run("ativos", slug=None)
        self.assertIn("export-csv: 0 decisão(ões), 0 para revisar", res.stdout)

    def test_ativo_exit_before_and_after_confirm_and_finish(self):
        def ativo():
            res = self.cli("ativo")
            return res.returncode, res.stdout.strip()
        self.assertEqual(ativo(), (1, "inativo"))  # started, mandate empty
        piloto.add_mandate(SLUG, self.repo, "limite", "x", "Q1")
        self.assertEqual(ativo(), (1, "inativo"))  # items but not confirmed
        piloto.confirm(SLUG, self.repo, "sim")
        self.assertEqual(ativo(), (0, "ativo"))
        piloto.finish(SLUG, self.repo)
        self.assertEqual(ativo(), (1, "inativo"))  # finished: no longer active


class PilotApprovalGateTests(PilotoCase):
    LINE = '**Approved**: 2026-11-13 - piloto: "D4 tasks cobrem a spec"'

    def test_pilot_line_needs_confirmed_active_mandate(self):
        self.assertFalse(gc.approved([self.LINE], self.fdir, allow_pilot=True))
        self.confirmed()
        for _ in range(4):
            piloto.record(SLUG, self.repo, "data", "q?", "a | b", "a", "porque", "M1")
        self.assertTrue(gc.approved([self.LINE], self.fdir, allow_pilot=True))
        self.assertFalse(gc.approved([self.LINE], self.fdir))  # the spec never accepts it
        self.assertFalse(gc.approved(['**Approved**: 2026-11-13 - piloto: "sem id"'], self.fdir, allow_pilot=True))
        piloto.finish(SLUG, self.repo)
        self.assertTrue(gc.approved([self.LINE], self.fdir, allow_pilot=True))  # finished: still valid (SC-187)

    def test_user_line_still_accepted(self):
        self.assertTrue(gc.approved(['**Approved**: 2026-11-13 - user: "sim"']))

    def test_gates_pass_pilot_only_on_tasks(self):
        import validate_tasks as vt

        gates = ROOT / "tests" / "fixtures" / "gates" / "large" / ".specs" / "features" / "export-csv"
        for name in ("spec.md", "tasks.md"):
            text = (gates / name).read_text(encoding="utf-8")
            (self.fdir / name).write_text(text, encoding="utf-8")
        self.confirmed()
        for _ in range(4):
            piloto.record(SLUG, self.repo, "data", "q?", "a | b", "a", "porque", "M1")
        tasks = self.fdir / "tasks.md"
        text = tasks.read_text(encoding="utf-8")
        text = re.sub(r"^\*\*Approved\*\*:.*$", self.LINE, text, flags=re.M)
        if self.LINE not in text:
            text = text.replace("\n", "\n" + self.LINE + "\n", 1)
        tasks.write_text(text, encoding="utf-8")
        res = vt.evaluate(SLUG, self.repo, execute=True)
        self.assertFalse([e for e in res.errors if "tasks.md sem" in e], res.errors)
        spec = self.fdir / "spec.md"
        spec.write_text(re.sub(r"^\*\*Approved\*\*:.*$", self.LINE, spec.read_text(encoding="utf-8"), flags=re.M),
                        encoding="utf-8")
        res = vt.evaluate(SLUG, self.repo, execute=True)
        self.assertTrue([e for e in res.errors if "spec.md sem" in e], res.errors)


MSG_D4 = "tasks.md: a aprovação do piloto cita D4, que não está registrada no piloto.md"
SEM_APPROVED = "tasks.md sem `**Approved**: <AAAA-MM-DD> - user: \"<palavras do usuário>\"`"
APPROVED_LINE_RE = re.compile(r"^\*\*Approved\*\*:.*\n", re.M)
MANDATE_DATE_RE = re.compile(r"^(\*\*Mandato confirmado:\*\* \d{4}-\d{2}-\d{2}).*$", re.M)


class PilotDecisaoCitadaTests(PilotoCase):
    def setUp(self):
        super().setUp()
        gates = ROOT / "tests" / "fixtures" / "gates" / "large" / ".specs" / "features" / "export-csv"
        for name in ("spec.md", "tasks.md"):
            (self.fdir / name).write_text((gates / name).read_text(encoding="utf-8"), encoding="utf-8")

    def register(self, upto):
        for _ in range(upto):
            piloto.record(SLUG, self.repo, "data", "q?", "a | b", "a", "porque", "M1")

    def set_approval(self, *lines, target="tasks.md"):
        path = self.fdir / target
        text = APPROVED_LINE_RE.sub("", path.read_text(encoding="utf-8"))
        path.write_text(text.replace("\n", "\n" + "\n".join(lines) + "\n", 1), encoding="utf-8")

    def gate_errors(self):
        import validate_tasks as vt
        import validate_verification as vv

        return (vt.evaluate(SLUG, self.repo, execute=True).errors, vv.evaluate(SLUG, self.repo).errors)

    def pil(self, text):
        return f'**Approved**: 2026-11-14 - piloto: "{text}"'

    def assert_tasks_ok(self):
        for errors in self.gate_errors():
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [], errors)

    def test_gates_leem_piloto_pelo_piloto_py(self):
        src = (ROOT / "scripts" / "gates" / "gates_common.py").read_text(encoding="utf-8")
        for needle in ("Mandato confirmado", "\\*\\*Status:", "### D"):
            self.assertNotIn(needle, src)
        body = src[src.index("def approved("):src.index("def size_of")]
        self.assertIn("pilot_approved(", body)
        pilot = src[src.index("def pilot_approved("):src.index("def pilot_unregistered(")]
        self.assertIn("approval_valid_in(", pilot)
        self.assertIn("registered_decisions_in(", src[src.index("def pilot_unregistered("):src.index("def approval_error")])

    def test_aprovacao_com_decisao_registrada_passa_nos_dois_gates(self):
        self.confirmed()
        self.register(5)
        for _ in range(2):  # the 6th and 7th are review decisions (no basis): still accepted by the gates
            piloto.record(SLUG, self.repo, "data", "q?", "a | b", "a", "porque")
        self.assertIn("⚠️ revisar", self.path.read_text(encoding="utf-8").split("### D7 · ")[1])
        self.set_approval(self.pil("D7 tasks cobrem a spec"))
        self.assert_tasks_ok()

    def test_decisao_inexistente_reprova_nos_dois_gates(self):
        self.confirmed()
        self.register(1)
        self.set_approval(self.pil("D4 tasks cobrem a spec"))
        for errors in self.gate_errors():
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [MSG_D4], errors)

    def test_id_longo_nao_derruba_o_gate(self):
        self.confirmed()
        self.register(1)
        self.assertEqual(gc.pilot_cited([self.pil("D" + "9" * 5000 + " x")]), [])
        self.set_approval(self.pil("D" + "9" * 5000 + " x"))
        self.assertFalse(gc.approved([self.pil("D" + "9" * 5000 + " x")], self.fdir, allow_pilot=True))
        for errors in self.gate_errors():
            self.assertEqual(len([e for e in errors if e.startswith(SEM_APPROVED)]), 1, errors)

    def test_spec_recusa_piloto_com_decisao_registrada(self):
        self.confirmed()
        self.register(1)
        self.set_approval(self.pil("D1 ok"))
        self.set_approval(self.pil("D1 ok"), target="spec.md")
        for errors in self.gate_errors():
            self.assertEqual(len([e for e in errors if e.startswith("spec.md sem")]), 1, errors)
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [], errors)

    def test_mandato_sem_user_nao_vale(self):
        self.confirmed()
        self.register(1)
        # finished pilot with the decision registered before the end: both gates accept the line (SC-187)
        piloto.finish(SLUG, self.repo)
        self.assertTrue(gc.approved([self.pil("D1 ok")], self.fdir, allow_pilot=True))
        self.set_approval(self.pil("D1 ok"))
        self.assert_tasks_ok()
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(MANDATE_DATE_RE.sub(r"\1", text), encoding="utf-8")
        self.assertEqual(piloto.main(["ativo", SLUG, "--root", str(self.repo)]), 1)
        self.assertFalse(gc.approved([self.pil("D1 ok")], self.fdir, allow_pilot=True))
        self.set_approval(self.pil("D1 ok"))
        for errors in self.gate_errors():
            self.assertEqual(len([e for e in errors if e.startswith(SEM_APPROVED)]), 1, errors)

    def test_sem_piloto_md_reprova_sem_excecao(self):
        self.path.unlink()
        self.set_approval(self.pil("D1 ok"))
        tasks_msg = SEM_APPROVED + (": a execução só começa depois da aprovação; "
                                    "nunca escreva uma aprovação que o usuário não deu")
        for errors, expected in zip(self.gate_errors(), (tasks_msg, SEM_APPROVED)):
            self.assertEqual([e for e in errors if e.startswith("tasks.md sem")], [expected], errors)
            self.assertEqual([e for e in errors if "não está registrada" in e], [], errors)

    def test_d07_cita_d7(self):
        self.confirmed()
        self.register(7)
        self.assertTrue(gc.approved([self.pil("D07 ok")], self.fdir, allow_pilot=True))
        self.set_approval(self.pil("D07 ok"))
        self.assert_tasks_ok()

    def test_uma_linha_valida_basta(self):
        self.confirmed()
        self.register(1)
        self.set_approval(self.pil("D9 ok"), self.pil("D1 ok"))
        self.assert_tasks_ok()

    def test_registrar_exige_mandato_com_user(self):
        self.confirmed()
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(MANDATE_DATE_RE.sub(r"\1", text), encoding="utf-8")
        res = subprocess.run([sys.executable, str(ROOT / "scripts" / "piloto.py"), "registrar", SLUG, "--by", "data",
                              "--question", "q", "--options", "a", "--decision", "a", "--reason", "r",
                              "--root", str(self.repo)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 1)
        self.assertEqual(res.stdout.strip(), "ERRO: mandato não confirmado: o piloto ainda não decide nada")
        self.assertNotIn("### D1 · ", self.path.read_text(encoding="utf-8"))

    def test_decisao_registrada_longa_nao_derruba_o_gate(self):
        self.confirmed()
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write("\n### D" + "9" * 5000 + " · x\n")
        self.set_approval(self.pil("D1 tasks cobrem a spec"))
        msg = "tasks.md: a aprovação do piloto cita D1, que não está registrada no piloto.md"
        for errors in self.gate_errors():
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [msg], errors)
        self.assertEqual(piloto.registered_decisions_in(self.fdir), set())

    def test_decisions_piloto_decisao_citada(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-170.*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        body = m.group(0)
        needles = ["**Problema:**", "**Decisão:**", "**Motivo:**", "**Por que não é bug:**", MSG_D4, "- user:", "D07"]
        needles += [f"`{n}`" for n in (
            "test_gates_leem_piloto_pelo_piloto_py", "test_aprovacao_com_decisao_registrada_passa_nos_dois_gates",
            "test_decisao_inexistente_reprova_nos_dois_gates", "test_spec_recusa_piloto_com_decisao_registrada",
            "test_mandato_sem_user_nao_vale", "test_sem_piloto_md_reprova_sem_excecao", "test_d07_cita_d7",
            "test_uma_linha_valida_basta")]
        for needle in needles:
            self.assertIn(needle, body)


FREIO_MSG = "freio: 3ª decisão ⚠️ revisar nesta feature; devolva a pergunta ao usuário"
CATEGORIAS = ("dependencia", "esquema", "arquitetura")


def categoria_msg(valor):
    return f"categoria {valor} exige item de mandato (--basis M<n>); devolva a pergunta ao usuário"


class PilotFreiosTests(PilotoCase):
    STAMP = "2026-11-14T10:00:00Z"
    TASKS_MSG = SEM_APPROVED + (": a execução só começa depois da aprovação; "
                                "nunca escreva uma aprovação que o usuário não deu")

    def setUp(self):
        super().setUp()
        gates = ROOT / "tests" / "fixtures" / "gates" / "large" / ".specs" / "features" / "export-csv"
        for name in ("spec.md", "tasks.md"):
            (self.fdir / name).write_text((gates / name).read_text(encoding="utf-8"), encoding="utf-8")

    # --- gates (R1 a R3) ---
    def register_n(self, n, stamp=STAMP):
        with mock.patch.object(piloto, "_now", return_value=stamp):
            for _ in range(n):
                piloto.record(SLUG, self.repo, "data", "q?", "a | b", "a", "porque", "M1")

    def finish_at(self, stamp):
        with mock.patch.object(piloto, "_now", return_value=stamp):
            piloto.finish(SLUG, self.repo, "feature concluída")

    def set_approval(self, *lines):
        path = self.fdir / "tasks.md"
        text = APPROVED_LINE_RE.sub("", path.read_text(encoding="utf-8"))
        path.write_text(text.replace("\n", "\n" + "\n".join(lines) + "\n", 1), encoding="utf-8")

    def gate_errors(self):
        import validate_tasks as vt
        import validate_verification as vv

        return (vt.evaluate(SLUG, self.repo, execute=True).errors, vv.evaluate(SLUG, self.repo).errors)

    def pil(self, text):
        return f'**Approved**: 2026-11-14 - piloto: "{text}"'

    def assert_accepted(self):
        for errors in self.gate_errors():
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [], errors)

    def assert_refused(self):
        for errors, expected in zip(self.gate_errors(), (self.TASKS_MSG, SEM_APPROVED)):
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [expected], errors)

    def test_aprovacao_vale_depois_de_encerrar(self):
        self.confirmed()
        self.register_n(2)
        self.set_approval(self.pil("D2 tasks cobrem a spec"))
        self.assertTrue(gc.approved([self.pil("D2 ok")], self.fdir, allow_pilot=True))  # active
        self.assert_accepted()
        self.finish_at(self.STAMP)  # same stamp as D2: counts as before
        self.assertIn("**Status:** encerrado", self.path.read_text(encoding="utf-8"))
        self.assertTrue(gc.approved([self.pil("D2 ok")], self.fdir, allow_pilot=True))
        self.assertFalse(gc.approved([self.pil("D2 ok")], self.fdir))  # the spec never accepts it
        self.assert_accepted()
        later = self.path.read_text(encoding="utf-8").replace(f"**Encerrado:** {self.STAMP}",
                                                              "**Encerrado:** 2026-11-14T10:00:05Z")
        self.path.write_text(later, encoding="utf-8")
        self.assert_accepted()  # earlier stamp counts too
        self.set_approval(self.pil("D9 nao existe"))
        self.assert_refused_unregistered()

    def assert_refused_unregistered(self):
        msg = "tasks.md: a aprovação do piloto cita D9, que não está registrada no piloto.md"
        for errors in self.gate_errors():
            self.assertEqual([e for e in errors if e.startswith("tasks.md")], [msg], errors)

    def test_decisao_depois_do_encerramento_reprova(self):
        self.confirmed()
        self.register_n(2)
        self.finish_at(self.STAMP)
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(text.replace(f"### D2 · {self.STAMP}", "### D2 · 2026-11-14T10:00:01Z"),
                             encoding="utf-8")
        self.assertFalse(gc.approved([self.pil("D2 ok")], self.fdir, allow_pilot=True))
        self.set_approval(self.pil("D2 tasks cobrem a spec"))
        self.assert_refused()
        self.set_approval(self.pil("D1 tasks cobrem a spec"))  # D1 is not after the end
        self.assert_accepted()
        self.set_approval(self.pil("D2 ok"), self.pil("D1 ok"))
        self.assert_accepted()

    def test_mandato_sem_user_reprova_ativo_e_encerrado(self):
        self.confirmed()
        self.register_n(1)
        text = self.path.read_text(encoding="utf-8")
        self.path.write_text(MANDATE_DATE_RE.sub(r"\1", text), encoding="utf-8")
        self.set_approval(self.pil("D1 ok"))
        self.assertFalse(gc.approved([self.pil("D1 ok")], self.fdir, allow_pilot=True))
        self.assert_refused()  # active
        self.finish_at(self.STAMP)
        self.assertFalse(gc.approved([self.pil("D1 ok")], self.fdir, allow_pilot=True))
        self.assert_refused()  # finished

    # --- freio e categoria (R4 a R9) ---
    def reg(self, decision="a", basis="", *extra):
        args = ["registrar", "--by", "data", "--question", "q", "--options", "a | b", "--decision", decision,
                "--reason", "r"] + (["--basis", basis] if basis else []) + list(extra)
        return self.cli(*args)

    def assert_refused_cli(self, res, code, message, before):
        self.assertEqual((res.returncode, res.stdout, res.stderr), (code, "", message + "\n"))
        self.assertEqual(self.snapshot(), before)

    def test_freio_na_terceira_revisar(self):
        self.confirmed()
        for _ in range(2):
            self.assertEqual(self.reg().returncode, 0)
        before = self.snapshot()
        self.assert_refused_cli(self.reg(), 3, FREIO_MSG, before)
        # baixa with a basis is also a review decision
        self.assert_refused_cli(self.reg("a", "M1", "--confidence", "baixa"), 3, FREIO_MSG, before)
        self.assertNotIn("### D3", self.path.read_text(encoding="utf-8"))

    def test_segunda_revisar_segue(self):
        self.confirmed()
        self.assertEqual(self.reg("a", "M1").returncode, 0)  # alta: not counted
        first = self.reg()
        self.assertEqual((first.returncode, first.stdout.strip()), (0, "D2 registrada (confiança baixa, revisar)"))
        second = self.reg()
        self.assertEqual((second.returncode, second.stdout.strip(), second.stderr),
                         (0, "D3 registrada (confiança baixa, revisar)", ""))
        text = self.path.read_text(encoding="utf-8")
        self.assertRegex(text, r"### D3 · \S+Z · data · confiança baixa · ⚠️ revisar\n")
        self.assertEqual(text.count("⚠️ revisar"), 2)

    def test_freio_fica_e_alta_segue(self):
        self.confirmed()
        for _ in range(2):
            self.assertEqual(self.reg().returncode, 0)
        before = self.snapshot()
        self.assert_refused_cli(self.reg(), 3, FREIO_MSG, before)
        alta = self.reg("a", "M1")
        self.assertEqual((alta.returncode, alta.stdout.strip()), (0, "D3 registrada (confiança alta)"))
        media = self.reg("a", "M2", "--confidence", "media")
        self.assertEqual((media.returncode, media.stdout.strip()), (0, "D4 registrada (confiança média)"))
        before = self.snapshot()
        self.assert_refused_cli(self.reg(), 3, FREIO_MSG, before)  # the brake stays
        self.assertEqual(self.path.read_text(encoding="utf-8").count("⚠️ revisar"), 2)

    def test_devolvido_ao_usuario_fora_do_freio(self):
        self.confirmed()
        self.assertEqual(self.reg().returncode, 0)  # D1 revisar
        devolvido = self.reg("devolvido ao usuário")
        self.assertEqual((devolvido.returncode, devolvido.stderr), (0, ""))
        text = self.path.read_text(encoding="utf-8")
        self.assertRegex(text, r"### D2 · \S+Z · data · confiança baixa\n- \*\*Pergunta:\*\* q\n"
                               r"- \*\*Opções:\*\* a \| b\n- \*\*Decisão:\*\* devolvido ao usuário\n")
        self.assertEqual(text.count("⚠️ revisar"), 1)  # D2 not flagged
        self.assertEqual(self.reg().returncode, 0)  # D3 is only the 2nd revisar: D2 did not count
        self.assertEqual(self.path.read_text(encoding="utf-8").count("⚠️ revisar"), 2)
        again = self.reg("devolvido ao usuário")  # brake on: still recorded
        self.assertEqual((again.returncode, again.stdout.strip()), (0, "D4 registrada (confiança baixa)"))
        self.assertEqual(self.path.read_text(encoding="utf-8").count("⚠️ revisar"), 2)
        before = self.snapshot()
        self.assert_refused_cli(self.reg(), 3, FREIO_MSG, before)

    def test_categoria_exige_mandato(self):
        self.confirmed()
        for cat in CATEGORIAS:
            for basis in ("", "Q5"):
                before = self.snapshot()
                res = self.reg("a", basis, "--categoria", cat)
                self.assert_refused_cli(res, 3, categoria_msg(cat), before)
        for cat in CATEGORIAS:  # the returned-to-user entry is not exempt: the exemption is only for the brake
            for basis in ("", "Q5"):
                before = self.snapshot()
                res = self.reg("devolvido ao usuário", basis, "--categoria", cat)
                self.assert_refused_cli(res, 3, categoria_msg(cat), before)
        for n, cat in enumerate(CATEGORIAS, 1):
            res = self.reg("a", "M1", "--categoria", cat)
            self.assertEqual((res.returncode, res.stdout.strip()), (0, f"D{n} registrada (confiança alta)"))
            self.assertRegex(self.path.read_text(encoding="utf-8"),
                             rf"### D{n} · \S+Z · data · confiança alta · categoria {cat}\n")
        before = self.snapshot()
        res = self.reg("a", "M9", "--categoria", "esquema")  # nonexistent mandate item
        self.assertEqual((res.returncode, res.stdout.strip()), (1, "ERRO: item de mandato inexistente: M9"))
        self.assertEqual(self.snapshot(), before)

    def test_categoria_invalida_sai_2(self):
        self.confirmed()
        before = self.snapshot()
        for value in ("outra", "", "Esquema"):
            res = self.reg("a", "M1", "--categoria", value)
            self.assertEqual((res.returncode, res.stdout), (2, ""), value)
            self.assertIn("--categoria", res.stderr)
            self.assertEqual(self.snapshot(), before)
        self.assertNotIn("### D1", self.path.read_text(encoding="utf-8"))

    # --- skill, DECISIONS e CHANGELOG (R10, R11) ---
    def test_skill_descreve_freio_e_categoria(self):
        step4 = ("[--categoria dependencia|esquema|arquitetura]",
                 "   A new dependency, a database schema change or a deviation from an architecture decision: pass\n"
                 "   `--categoria dependencia|esquema|arquitetura` together with the mandate item that covers it "
                 "(`--basis M<n>`).",
                 "   **Brake:** the 3rd decision marked `⚠️ revisar` in a feature is refused with exit 3\n"
                 "   (`freio: 3ª decisão ⚠️ revisar nesta feature; devolva a pergunta ao usuário`), and so is every "
                 "one after it;",
                 "   the user (section 5), then record it with `--decision \"devolvido ao usuário\"` "
                 "(never marked, never counted by the brake).\n"
                 "   Record the return **without** `--categoria`: with it and no `M<n>` the script refuses again "
                 "(exit 3).")
        gate = ("   only on tasks.md, with the mandate confirmed by the user and piloto.md active or finished "
                "(`encerrar` does not\n   void it), as long as the cited decision was recorded up to the "
                "`**Encerrado:**` stamp; a decision recorded\n   after it does not count.")
        never = ("- A new dependency, a database schema change and a deviation from an architecture decision, "
                 "unless a mandate\n  item covers it (`--categoria` with `--basis M<n>`); and any question the "
                 "brake refused (exit 3).")
        for root in [ROOT] + [ROOT / "dist" / cli for cli in CLIS]:
            text = (root / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
            s4 = text.split("## 4. Autopilot rules", 1)[1].split("\n## 5.", 1)[0]
            s5 = text.split("## 5. What the autopilot never decides", 1)[1].split("\n## 6.", 1)[0]
            s7 = text.split("## 7. End", 1)[1]
            for needle in step4 + (gate,):
                self.assertIn(needle, s4, f"{root}: {needle}")
            step5 = s4.split("5. Where the flow writes an approval", 1)[1].split("\n6. ", 1)[0]
            self.assertIn(gate, step5, root)
            self.assertIn(never, s5, root)
            self.assertNotIn("only while piloto.md is active", text, root)
            self.assertIn("Finishing does not void the `piloto:` approval", s7, root)

    def test_decisions_piloto_freios(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-187:.*\n(.*?)(?=^### |\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        body = m.group(0)
        for field in ("**Problema**:", "**Decisão**:", "**Motivo**:", "**Por que não é bug**:"):
            self.assertEqual(body.count(field), 1, field)
        decisao = body.split("**Decisão**:", 1)[1].split("- **Motivo**:", 1)[0]
        for term in ("`ativo` ou `encerrado`", "`- user:`", "carimbo", "`**Encerrado:**`", "(R1)", "(R2)", "(R3)",
                     "inclusive `baixa` com `--basis`", FREIO_MSG, "exit 3", "(R4)", "2ª é gravada com exit 0", "(R5)",
                     "o freio fica", "`alta` e `media` com base continuam gravadas", "(R6)",
                     "`--decision \"devolvido ao usuário\"` é gravada sem `⚠️ revisar`, não conta no freio", "(R7)",
                     "`--categoria dependencia|esquema|arquitetura`", categoria_msg("<valor>"), "cita `categoria <valor>`",
                     "(R8)", "sai com 2 (uso), sem gravar", "(R9)", "seção 4", "seção 5", "seção 7", "(R10)"):
            self.assertIn(term, decisao, term)
        motivo = body.split("**Motivo**:", 1)[1].split("- **Por que não é bug**:", 1)[0]
        self.assertIn("disjuntor D27", motivo)
        bug = body.split("**Por que não é bug**:", 1)[1]
        for name in ("test_aprovacao_vale_depois_de_encerrar", "test_decisao_depois_do_encerramento_reprova",
                     "test_mandato_sem_user_reprova_ativo_e_encerrado", "test_freio_na_terceira_revisar",
                     "test_segunda_revisar_segue", "test_freio_fica_e_alta_segue",
                     "test_devolvido_ao_usuario_fora_do_freio", "test_categoria_exige_mandato",
                     "test_categoria_invalida_sai_2", "test_skill_descreve_freio_e_categoria",
                     "test_decisions_piloto_freios"):
            self.assertIn(f"`{name}`", bug, name)
            self.assertTrue(hasattr(PilotFreiosTests, name), name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertIn("- Freios do piloto automático (SC-187):", unreleased)


class PilotBannerTests(PilotoCase):
    def banner_text(self):
        with mock.patch.object(banner, "check_orca", return_value="Orca: ✅ disponível"), \
             mock.patch.object(banner.conflicts, "scan", return_value=[]):
            return banner.build_banner(str(self.repo), False)[0]

    def test_banner_shows_active_autopilot(self):
        self.write_repo_config()
        # started, mandate pending: not active, so not in the banner (same rule as `ativo`)
        self.assertEqual(piloto.actives(self.repo), [])
        self.assertNotIn("Piloto automático", self.banner_text())
        piloto.add_mandate(SLUG, self.repo, "principio", "simplicidade", "Q3")
        self.assertEqual(piloto.actives(self.repo), [])
        self.assertNotIn("Piloto automático", self.banner_text())
        piloto.confirm(SLUG, self.repo, "sim")
        self.assertEqual(piloto.actives(self.repo), [(SLUG, 0, 0)])
        piloto.record(SLUG, self.repo, "data", "q", "a | b", "a", "r", "")
        self.assertEqual(piloto.actives(self.repo), [(SLUG, 1, 1)])
        self.assertIn("🛸 Piloto automático: ativo em export-csv (1 decisão(ões), 1 para revisar;", self.banner_text())
        piloto.finish(SLUG, self.repo)
        self.assertNotIn("Piloto automático", self.banner_text())


class PilotSkillTests(unittest.TestCase):
    def roots(self):
        return [ROOT] + [ROOT / "dist" / cli for cli in CLIS]

    def test_piloto_skill_rules(self):
        reserved = ("- The Git mode, the spec approval, **push**, **opening the PR**, publishing Worf's review to the PR,\n"
                    "  **merge into the base branch**, **deploy** (the merge authorization is the user's: never run\n"
                    "  `git_mode.py authorize-merge` on their behalf).")
        for root in self.roots():
            text = (root / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\nname: piloto-automatico\n"), root)
            for needle in ("mode: grill", 'piloto.py" confirmar', 'piloto.py" registrar', "Record before acting",
                           "approve the spec yourself", "never write a `user:` line the user did not say",
                           'piloto: "D<n> <resumo>"', "Never widen the spec",
                           "the Git mode is still asked", "safest and most reversible"):
                self.assertIn(needle, text, f"{root}: {needle}")
            # push, PR, merge and deploy are one bullet of "never decides" (the user's), with the full rule
            section = text.split("## 5. What the autopilot never decides", 1)[1].split("\n## 6.", 1)[0]
            self.assertIn("These still stop and ask the user", section, root)
            self.assertIn(reserved, section, root)
            # a decision without a basis is forced to low confidence and marked for review
            self.assertIn("No basis → leave `--basis` empty: the script forces `baixa` and marks `⚠️ revisar`.",
                          text, root)
            self.assertIn("each `⚠️ revisar` decision (ID and one line)", text, root)
            self.assertIn("Push, PR, merge and deploy still need the user.", text, root)
        claude = (ROOT / "dist" / "claude" / "skills" / "piloto-automatico" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("disable-model-invocation: true", claude)

    def test_troi_grill_mode(self):
        for root in self.roots():
            text = (root / "skills" / "troi" / "SKILL.md").read_text(encoding="utf-8")
            sec = text.split("## 2G. Grill mode", 1)[1].split("\n## 3.", 1)[0]
            for needle in ("frontier", "❓ **Q<n>**", "➡️", 'so "sim" accepts', "never restart", "No round cap",
                           'piloto.py" mandato', "ask the\n  user to confirm it", "mattpocock/skills, MIT"):
                self.assertIn(needle, sec, f"{root}: {needle}")

    def test_flow_hooks_into_autopilot(self):
        engajar = (ROOT / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('piloto.py" ativo <slug>', engajar)
        data = (ROOT / "skills" / "data" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('piloto: "D<n> <resumo>"', data)
        guinan = (ROOT / "skills" / "guinan" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Piloto automático", guinan)


if __name__ == "__main__":
    unittest.main()
