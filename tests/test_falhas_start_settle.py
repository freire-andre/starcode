"""SC-208: falhas do start e do settle, handoff.py set com trava e run_git com tempo limite."""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from unittest import mock

from helpers import ROOT, TempRepoCase, run_git

import dispatch
import handoff
import impact
import snapshot
import starcode_common as sc
from test_dispatch import make_tasks
from test_dispatch_settle import FakeGate, entry
from test_dispatch_start import FakeOrca, HANDOFF, RECEIPT

HANDOFF_PY = ROOT / "scripts" / "handoff.py"
LINHA_TIMEOUT = "git excedeu 30 s: git status"


def decisions_entry(n: str) -> str:
    text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    m = re.search(rf"^### {n}:.*?(?=^### |\Z)", text, re.S | re.M)
    assert m, f"entrada {n} ausente"
    return m.group(0)


class TextoAntesOrca(FakeOrca):
    """O worker-start imprime uma linha de aviso antes do JSON."""

    def __call__(self, cmd, **kw):
        res = super().__call__(cmd, **kw)
        if self.key(cmd) == "worker-start":
            return SimpleNamespace(returncode=0, stdout="aviso: atualizando\n" + res.stdout, stderr="")
        return res


class FalhasStartSettleTests(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        self.write_repo_config()
        self.fdir = self.repo / ".specs" / "features" / "demo"
        self.fdir.mkdir(parents=True)
        (self.fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        self.base = self.publish("none")
        run_git(self.repo, "checkout", "-q", "-b", "feature/demo")

    def publish(self, dispatched: str) -> str:
        text = make_tasks([{"tid": "T1"}, {"tid": "T2"}]) + HANDOFF.format(d=dispatched)
        (self.fdir / "tasks.md").write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")
        return run_git(self.repo, "rev-parse", "--short", "HEAD")

    def fields(self) -> dict[str, str]:
        lines = (self.fdir / "tasks.md").read_text(encoding="utf-8").splitlines()
        return handoff.read_fields(lines, handoff.section_bounds(lines))

    def start(self, runner):
        out: list[str] = []
        code, res = dispatch.start("demo", "T1", "claude", "claude-sonnet-5-5", self.repo, runner=runner,
                                   emit=out.append)
        return code, res, out

    def start_json(self, runner):
        real = dispatch.start
        with mock.patch.object(dispatch, "start", side_effect=lambda *a, **k: real(*a, runner=runner, **k)),                 mock.patch("sys.stdout", new_callable=io.StringIO) as so,                 mock.patch("sys.stderr", new_callable=io.StringIO) as se:
            code = dispatch.main(["start", "demo", "T1", "--cli", "claude", "--model", "claude-sonnet-5-5",
                                  "--json", "--root", str(self.repo)])
        return code, so.getvalue(), se.getvalue()

    def ticket_branch(self, fname: str, text: str = "x\n") -> None:
        run_git(self.repo, "checkout", "-q", "-b", "ticket/t1")
        (self.repo / fname).write_text(text, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: T1", "-m", "Refs: PROJ-1")
        run_git(self.repo, "checkout", "-q", "feature/demo")

    def settle(self, runner):
        out: list[str] = []
        code = dispatch.settle("demo", "T1", "ticket/t1", self.repo, runner=runner, emit=out.append)
        return code, out

    # C1
    def test_recibo_com_texto_antes(self):
        corpo = json.dumps({"dispatch": {"id": "ctx_9"}, "model": "m1", "worktree": {"id": "wt-9"}})
        esperado = {"dispatch": "ctx_9", "model": "m1", "worktree": "wt-9"}
        self.assertEqual(dispatch._receipt(corpo), esperado)
        self.assertEqual(dispatch._receipt("aviso: x y\nsegunda\n" + corpo), esperado)
        self.assertEqual(dispatch._receipt(corpo + "\nrodapé"), esperado)
        vazio = {"dispatch": "", "model": "", "worktree": ""}
        self.assertEqual(dispatch._receipt("sem json algum"), vazio)
        self.assertEqual(dispatch._receipt(""), vazio)
        self.assertEqual(dispatch._receipt("texto { quebrado"), vazio)
        code, res, out = self.start(TextoAntesOrca())
        self.assertEqual(code, 0)
        self.assertEqual(res["dispatch"], "ctx_abc")
        self.assertIn("worker iniciado: T1 · claude:claude-sonnet-5-5 · ctx_abc", out)

    # C2
    def test_start_sem_id_sai_com_3(self):
        fake = FakeOrca(receipt={"model": "claude-sonnet-5-5", "worktree": {"id": "wt-123"}})
        code, res, out = self.start(fake)
        self.assertEqual(code, 3)
        self.assertIn("worker ativo sem id de despacho: T1 · wt-123: confira com orca orchestration list", out)
        self.assertFalse([ln for ln in out if ln.startswith("worker iniciado")])
        entries = handoff.dispatch_entries(self.fields()["dispatched"])
        self.assertEqual(len(entries), 1)
        self.assertRegex(entries[0],
                         r"^T1 · PROJ-1 · base \w+ · claude:claude-sonnet-5-5 · \d{4}-\d\d-\d\dT[\d:]+Z$")
        self.assertEqual(res, {"ticket": "T1", "issue": "PROJ-1", "base": self.base, "dispatch": "",
                               "worktree": "wt-123", "model": "claude-sonnet-5-5"})
        # sem worktree no recibo: o traço ocupa o lugar
        self.publish("none")
        code2, _, out2 = self.start(FakeOrca(receipt={"model": "m"}))
        self.assertEqual(code2, 3)
        self.assertIn("worker ativo sem id de despacho: T1 · -: confira com orca orchestration list", out2)
        # --json: o main roda o start de verdade, com o runner falso, e imprime o recibo com código 3
        base3 = self.publish("none")
        code3, so, se = self.start_json(FakeOrca(receipt={"model": "claude-sonnet-5-5", "worktree": {"id": "wt-123"}}))
        self.assertEqual(code3, 3)
        self.assertEqual(json.loads(so), {"ticket": "T1", "issue": "PROJ-1", "base": base3, "dispatch": "",
                                          "worktree": "wt-123", "model": "claude-sonnet-5-5"})
        self.assertEqual(so.count("\n"), 1)  # uma só linha de JSON no stdout
        brief, *resto = se.splitlines()
        self.assertRegex(brief, r"^briefing: .+demo-T1.md$")
        self.assertEqual(resto, [f"Dispatched: T1 registrado (base {base3})", "status In Progress: PROJ-1",
                                 "label crew:laforge: PROJ-1",
                                 "worker ativo sem id de despacho: T1 · wt-123: confira com orca orchestration list",
                                 "worktree wt-123 ligado a PROJ-1"])
        # com id, o caminho de sempre segue com 0
        self.publish("none")
        code4, _, _ = self.start(FakeOrca(receipt=RECEIPT))
        self.assertEqual(code4, 0)
        # com id e --json: código 0 e o objeto de recibo completo
        base5 = self.publish("none")
        code5, so5, se5 = self.start_json(FakeOrca(receipt=RECEIPT))
        self.assertEqual(code5, 0)
        self.assertEqual(json.loads(so5), {"ticket": "T1", "issue": "PROJ-1", "base": base5,
                                           "dispatch": "ctx_abc", "worktree": "wt-123",
                                           "model": "claude-sonnet-5-5"})
        brief5, *resto5 = se5.splitlines()
        self.assertRegex(brief5, r"^briefing: .+demo-T1.md$")
        self.assertEqual(resto5, [f"Dispatched: T1 registrado (base {base5})", "status In Progress: PROJ-1",
                                  "label crew:laforge: PROJ-1",
                                  "worker iniciado: T1 · claude:claude-sonnet-5-5 · ctx_abc",
                                  "worktree wt-123 ligado a PROJ-1"])

    # C3
    def test_merge_falha_sem_conflito(self):
        self.publish(entry("T1", self.base))
        self.ticket_branch("a.txt", "do ticket\n")
        (self.repo / "a.txt").write_text("sujo\n", encoding="utf-8")  # não rastreado: o merge se recusa
        antes = run_git(self.repo, "rev-parse", "HEAD")
        fake = FakeGate()
        code, out = self.settle(fake)
        self.assertEqual(code, 1)
        self.assertEqual(out[-1], "merge de T1 falhou: error: The following untracked working tree files would be "
                                  "overwritten by merge:")
        self.assertNotIn(["git", "merge", "--abort"], fake.calls)
        self.assertEqual(run_git(self.repo, "rev-parse", "HEAD"), antes)
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"), "sujo\n")
        self.assertEqual(len(handoff.dispatch_entries(self.fields()["dispatched"])), 1)
        # com conflito: a linha de sempre e o abort roda uma vez
        (self.repo / "a.txt").unlink()
        (self.repo / "a.txt").write_text("do ramo\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "chore: a.txt")
        fake2 = FakeGate()
        code2, out2 = self.settle(fake2)
        self.assertEqual(code2, 1)
        self.assertEqual(out2[-1], "conflito no merge de T1: a.txt")
        self.assertEqual(fake2.calls.count(["git", "merge", "--abort"]), 1)
        self.assertEqual(run_git(self.repo, "status", "--porcelain"), "")

    # C4
    def test_handoff_concorrente(self):
        for i in range(4):
            procs = [subprocess.Popen([sys.executable, str(HANDOFF_PY), "set", "demo", "--root", str(self.repo),
                                       opt, f"v{i}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for opt in ("--next", "--size")]
            for p in procs:
                _, err = p.communicate(timeout=60)
                self.assertEqual(p.returncode, 0, err)
            campos = self.fields()
            self.assertEqual((campos["next"], campos["size"]), (f"v{i}", f"v{i}"))
        fdir = handoff.feature_dir("demo", self.repo)
        held = threading.Event()
        done = threading.Event()

        def hold():
            with sc.locked(fdir / ".handoff"):
                held.set()
                done.wait(30)

        t = threading.Thread(target=hold)
        t.start()
        try:
            self.assertTrue(held.wait(10))
            t0 = time.monotonic()
            res = subprocess.run([sys.executable, str(HANDOFF_PY), "set", "demo", "--root", str(self.repo),
                                  "--next", "x"], capture_output=True, text=True, timeout=60)
            self.assertGreaterEqual(time.monotonic() - t0, 4.5)
        finally:
            done.set()
            t.join()
        self.assertEqual(res.returncode, 2)
        self.assertEqual(res.stderr, f"handoff ocupado: {fdir}\n")
        self.assertEqual(res.stdout, "")
        self.assertEqual(self.fields()["next"], "v3")
        self.assertTrue((fdir / ".handoff.lock").exists())
        self.assertIn(".handoff.lock", (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        ign = subprocess.run(["git", "check-ignore", "-q", "--no-index", ".handoff.lock"], cwd=ROOT)
        self.assertEqual(ign.returncode, 0)

    # C5
    def test_run_git(self):
        code, out, err = sc.run_git(["--version"], self.repo)
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("git version"))
        self.assertEqual(err, "")
        code, out, err = sc.run_git(["rev-parse", "--verify", "nao-existe"], self.repo)
        self.assertNotEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(err, "fatal: Needed a single revision\n")
        code, out, err = sc.run_git(["var", "GIT_AUTHOR_IDENT"], self.repo,
                                    env={"GIT_AUTHOR_NAME": "Zed", "GIT_AUTHOR_EMAIL": "z@x.io"})
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("Zed <z@x.io>"))
        code, out, err = sc.run_git(["cat-file", "blob", "HEAD:README.md"], self.repo, binary=True)
        self.assertEqual((code, out, err), (0, b"hello\n", b""))
        code, out, err = sc.run_git(["cat-file", "blob", "HEAD:nao"], self.repo, binary=True)
        self.assertNotEqual(code, 0)
        self.assertIsInstance(err, bytes)
        with mock.patch.object(subprocess, "run", side_effect=subprocess.TimeoutExpired(["git"], 2)):
            self.assertEqual(sc.run_git(["log", "-1"], self.repo, timeout=2),
                             (124, "", "git excedeu 2 s: git log -1"))
            self.assertEqual(sc.run_git(["log", "-1"], self.repo, timeout=2, binary=True),
                             (124, b"", b"git excedeu 2 s: git log -1"))
        with mock.patch.object(subprocess, "run", side_effect=FileNotFoundError("git")):
            self.assertEqual(sc.run_git(["log"], self.repo), (127, "", "git não encontrado"))
            self.assertEqual(sc.run_git(["log"], self.repo, binary=True), (127, b"", "git não encontrado".encode()))
        with mock.patch.object(subprocess, "run", wraps=subprocess.run) as spy:
            sc.run_git(["--version"], self.repo, timeout=7)
        self.assertEqual(spy.call_args.kwargs["timeout"], 7)

    # C5 (achado 2: argumentos e ambiente inválidos)
    def test_run_git_argumentos_invalidos(self):
        esperado = (126, "", "argumentos inválidos para o git: environment can only contain strings")
        self.assertEqual(sc.run_git(["status"], self.repo, env={"BAD": 1}), esperado)
        self.assertEqual(sc.run_git(["status"], self.repo, env={"BAD": 1}, binary=True),
                         (126, b"", esperado[2].encode("utf-8")))
        code, out, err = sc.run_git(["status", "a\0b"], self.repo)
        self.assertEqual((code, out), (126, ""))
        self.assertTrue(err.startswith("argumentos inválidos para o git: "), err)
        self.assertEqual(sc.run_git(["--version"], self.repo)[0], 0)  # o caminho feliz segue igual

    # C6
    def test_scripts_usam_run_git(self):
        for nome in ("snapshot.py", "impact.py", "dispatch.py"):
            src = (ROOT / "scripts" / nome).read_text(encoding="utf-8")
            with self.subTest(nome):
                self.assertNotRegex(src, r"subprocess\.\w+\(\s*\[\s*\"git\"")
                self.assertIn("sc.run_git(", src)
        for nome in ("snapshot.py", "impact.py"):
            self.assertNotIn("import subprocess", (ROOT / "scripts" / nome).read_text(encoding="utf-8"))
        lento = (124, "", LINHA_TIMEOUT)
        with mock.patch.object(sc, "run_git", return_value=lento):
            with self.assertRaises(snapshot.GitError) as cm:
                snapshot.run_git(self.repo, "status")
            self.assertEqual(str(cm.exception), f"status: {LINHA_TIMEOUT}")
            with self.assertRaises(snapshot.GitError) as cm:
                snapshot.valid_names("demo", "t1")
            self.assertEqual(str(cm.exception), f"check-ref-format: {LINHA_TIMEOUT}")
            with self.assertRaises(snapshot.GitError) as cm:
                snapshot._write_blob(self.repo, "HEAD", "README.md")
            self.assertEqual(str(cm.exception), "ls-tree HEAD: " + LINHA_TIMEOUT)
            with self.assertRaises(impact.ImpactError) as cm:
                impact.run_git(self.repo, "status")
            self.assertEqual(str(cm.exception), f"status: {LINHA_TIMEOUT}")
            with self.assertRaises(ValueError) as cm:
                dispatch._git(self.repo, "status")
            self.assertEqual(str(cm.exception), f"git status falhou em {self.repo}: {LINHA_TIMEOUT}")
            with self.assertRaises(ValueError) as cm:
                dispatch.q_check("demo", self.repo)
            self.assertEqual(str(cm.exception), f"git status falhou em {self.repo}: {LINHA_TIMEOUT}")
            self.assertTrue(dispatch.regression_block(self.repo, "a", "b").startswith("seleção indisponível: "))
        with mock.patch.object(sc, "run_git", return_value=(127, "", "git não encontrado")):
            with self.assertRaises(ValueError) as cm:
                dispatch.q_check("demo", self.repo)
            self.assertEqual(str(cm.exception), f"git status falhou em {self.repo}: git não encontrado")
        # caminho feliz mantido pelos três
        self.assertEqual(snapshot.run_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").strip(), "feature/demo")
        self.assertEqual(impact.run_git(self.repo, "rev-parse", "--abbrev-ref", "HEAD").strip(), "feature/demo")
        self.assertEqual(dispatch._git(self.repo, "rev-parse", "--abbrev-ref", "HEAD"), (0, "feature/demo\n"))
        self.assertTrue(snapshot.valid_names("demo", "t1"))

    # C6 (achado 3: o tempo esgotado chega aos chamadores de valid_names e de _git)
    def test_timeout_chega_aos_chamadores(self):
        lento = (124, "", LINHA_TIMEOUT)
        # valid_names: nome inválido segue False, o tempo esgotado e o git ausente levantam
        self.assertFalse(snapshot.valid_names("demo", "t 1"))
        self.assertFalse(snapshot.valid_names("Demo!", "t1"))
        self.assertTrue(snapshot.valid_names("demo", "t1"))
        with mock.patch.object(sc, "run_git", return_value=(127, "", "git não encontrado")):
            with self.assertRaises(snapshot.GitError) as cm:
                snapshot.valid_names("demo", "t1")
            self.assertEqual(str(cm.exception), "check-ref-format: git não encontrado")
        # take e restore: erro do snapshot, código 1, nada de "nome inválido"
        for cmd, func, prefixo in (("take", snapshot.cmd_take, "snapshot falhou"),
                                   ("restore", snapshot.cmd_restore, "restauração falhou")):
            args = SimpleNamespace(slug="demo", ticket="t1", root=self.repo, yes=True, json=False)
            with self.subTest(cmd), mock.patch.object(sc, "run_git", return_value=lento),                     mock.patch("sys.stdout", new_callable=io.StringIO) as so:
                code = func(args)
            self.assertEqual(code, 1)
            self.assertEqual(so.getvalue(), f"{prefixo}: check-ref-format: {LINHA_TIMEOUT}\n")
        # nome realmente inválido segue com 2 e a mensagem de sempre
        args = SimpleNamespace(slug="demo", ticket="t 1", root=self.repo, yes=True, json=False)
        with mock.patch("sys.stdout", new_callable=io.StringIO) as so:
            self.assertEqual(snapshot.cmd_take(args), 2)
        self.assertEqual(so.getvalue(), "nome inválido para o snapshot: t 1\n")
        # _git no dispatch: integrated e require_committed deixam o erro subir, com o stderr
        with mock.patch.object(sc, "run_git", return_value=lento):
            with self.assertRaises(ValueError) as cm:
                dispatch.integrated([], self.repo, "main", "feature/demo")
            self.assertEqual(str(cm.exception), f"git log falhou em {self.repo}: {LINHA_TIMEOUT}")
            with self.assertRaises(ValueError) as cm:
                dispatch.require_committed(self.fdir, ("spec.md",))
            self.assertEqual(str(cm.exception), f"git cat-file falhou em {self.repo}: {LINHA_TIMEOUT}")
        # código 128 do git (caminho ausente) continua sendo resposta, não erro
        self.assertEqual(dispatch._git(self.repo, "cat-file", "-e", "HEAD:nao-existe")[0], 128)
        with self.assertRaises(LookupError):
            dispatch.require_committed(self.fdir, ("nao-existe.md",))

    # C6 (achado 1: o diff de HEAD)
    def test_regressao_diff_head_com_erro(self):
        sel = mock.patch.object(impact, "select", return_value={})
        fmt = mock.patch.object(impact, "format_text", return_value="OK")
        for code, err in ((124, LINHA_TIMEOUT), (128, "fatal: não é um repositório"), (127, "git não encontrado")):
            with self.subTest(code=code), sel as s, fmt as f,                     mock.patch.object(sc, "run_git", return_value=(code, "", err)):
                texto = dispatch.regression_block(self.repo, "base", "HEAD")
            self.assertEqual(texto, f"seleção indisponível: git diff --quiet HEAD falhou: {err}; "
                                    "rode a suíte inteira")
            s.assert_not_called()
            f.assert_not_called()
        # sem mensagem do git, o código aparece
        with sel, fmt, mock.patch.object(sc, "run_git", return_value=(9, "", "")):
            self.assertEqual(dispatch.regression_block(self.repo, "base", "HEAD"),
                             "seleção indisponível: git diff --quiet HEAD falhou: código 9; rode a suíte inteira")
        # 0: a faixa base..HEAD; 1: a árvore de trabalho contra a base
        for code, diff in ((0, "base..HEAD"), (1, "base")):
            with self.subTest(code=code), sel as s, fmt, mock.patch.object(sc, "run_git", return_value=(code, "", "")):
                self.assertEqual(dispatch.regression_block(self.repo, "base", "HEAD"), "OK")
                self.assertEqual(s.call_args.kwargs["diff"], diff)
        # fora de HEAD o diff não é consultado
        with sel as s, fmt, mock.patch.object(sc, "run_git", side_effect=AssertionError("não chamar")):
            self.assertEqual(dispatch.regression_block(self.repo, "a", "b"), "OK")
            self.assertEqual(s.call_args.kwargs["diff"], "a..b")

    # C7
    def test_decisions_e_changelog(self):
        e = decisions_entry("SC-208")
        partes = {}
        for nome in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            m = re.search(rf"^- \*\*{nome}\*\*: (.+)$", e, re.M)
            self.assertIsNotNone(m, nome)
            partes[nome] = m.group(1)
        for caso in ("Caso 1", "Caso 2", "Caso 3", "Caso 4", "já resolvido", "estava aberto"):
            self.assertIn(caso, partes["Problema"])
        trechos = [t for t in re.split(r"(?:(?<=\. )|^)(?=R[1-7]: )", partes["Decisão"]) if t]
        self.assertEqual([t[:3] for t in trechos], [f"R{n}:" for n in range(1, 8)])
        exigidos = {
            "R1": ["`_receipt`", "primeiro `{`", "sem `{` o recibo continua vazio"],
            "R2": ["sai com 0", "id de despacho", "mantém a entrada do `Dispatched`",
                   "`worker ativo sem id de despacho: <T> · <worktree ou ->: confira com orca orchestration list`",
                   "sai com 3", "`--json`", "o mesmo objeto de recibo"],
            "R3": ["`git diff --name-only --diff-filter=U`", "`conflito no merge de <T>: <arquivos>`",
                   "`merge de <T> falhou: <primeira linha do stderr, ou do stdout, do git merge>`",
                   "`git merge --abort` só quando há merge em andamento", "sai com 1"],
            "R4": ["`set_handoff`", "`starcode_common.locked(<pasta da feature>/.handoff)`", "5 s", "sai com 2",
                   "`handoff ocupado: <pasta da feature>`", "`.handoff.lock`", "`.gitignore`"],
            "R5": ["`starcode_common.run_git(args, cwd, timeout=30, binary=False, env=None)`",
                   "`(código, stdout, stderr)`", "bytes", "124", "`git excedeu <n> s: git <args>`", "127",
                   "`git não encontrado`", "nunca levanta exceção"],
            "R6": ["`snapshot.py`", "`valid_names`", "`_write_blob`", "`impact.py`", "`dispatch.py`", "`_git`",
                   "`git diff --quiet`", "`q_check`", "só por `starcode_common.run_git`",
                   "`GitError`", "`ImpactError`", "`ValueError`", "texto do stderr"],
            "R7": ["esta entrada", "`CHANGELOG.md`"],
        }
        for trecho in trechos:
            for termo in exigidos[trecho[:2]]:
                with self.subTest(req=trecho[:2], termo=termo):
                    self.assertIn(termo, trecho)
        for nome in ("test_recibo_com_texto_antes", "test_start_sem_id_sai_com_3", "test_merge_falha_sem_conflito",
                     "test_handoff_concorrente", "test_run_git", "test_scripts_usam_run_git",
                     "test_decisions_e_changelog"):
            self.assertIn(nome, partes["Por que não é bug"])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertEqual(len([ln for ln in unreleased.splitlines() if "(SC-208)" in ln]), 1)
