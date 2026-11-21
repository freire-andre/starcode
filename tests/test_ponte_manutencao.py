"""SC-207: leitor único do `**Dispatched:**`, manifesto sem `storage:own` e pulo visível do `orca` no CI."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase, run_git

import dispatch
import handoff
import ponte
from test_dispatch import make_tasks
from test_dispatch_settle import FakeGate

CI = ROOT / ".github" / "workflows" / "ci.yml"
AVISO = "::warning title=orca ausente::validação e testes do plugin da Ponte pulados"
RESUMO = "- orca plugin validate: pulado (orca ausente)"

# Entradas gravadas de verdade pelo `start` (test_dispatch_start: primeira gravação e gravação final com o id).
START_SEM_ID = "T1 · PROJ-9 · base 1a2b3c4 · claude:claude-sonnet-5-5 · 2026-11-13T09:08:07Z"
START_COM_ID = START_SEM_ID + " · ctx_abc"
START_BLOCKED = START_COM_ID + " · blocked"
ANTIGO = "T2 · SC-122 · base def5678 · dispatch ctx_bbb222 · model claude-opus-5-5"

HANDOFF = "\n## Handoff\n**Phase:** execute\n**Integration branch:** feature/demo\n**Dispatched:** {d}\n"


def find_bash() -> str | None:
    """Um bash que enxerga caminhos do Windows: no Windows, o do Git (o `bash.exe` do system32 é o WSL)."""
    if os.name != "nt":
        return shutil.which("bash")
    git = shutil.which("git")
    if git is None:
        return None
    base = Path(git).resolve().parent
    for root in (base.parent, base.parent.parent):
        for rel in ("bin/bash.exe", "usr/bin/bash.exe"):
            if (root / rel).is_file():
                return str(root / rel)
    return None


def run_step() -> str:
    """O `run` do passo `orca plugin validate` do CI, lido do ci.yml."""
    for line in CI.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("run: 'if command -v orca"):
            return line.strip()[len("run: '"):-1]
    raise AssertionError("passo orca plugin validate ausente no ci.yml")


def decisions_entry(n: str) -> str:
    text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    m = re.search(rf"^### {n}:.*?(?=^### |\Z)", text, re.S | re.M)
    assert m, f"entrada {n} ausente"
    return m.group(0)


class PonteManutencaoTests(TempRepoCase):
    def test_parse_dispatch_entry(self):  # C1
        vazio = {"ticket": None, "issues": [], "issues_text": None, "base": None, "model": None, "at": None, "dispatch": None,
                 "blocked": False}
        tabela = [
            (START_SEM_ID, {"ticket": "T1", "issues": ["PROJ-9"], "issues_text": "PROJ-9", "base": "1a2b3c4",
                            "model": "claude:claude-sonnet-5-5", "at": "2026-11-13T09:08:07Z",
                            "dispatch": None, "blocked": False}),
            (START_COM_ID, {"ticket": "T1", "issues": ["PROJ-9"], "issues_text": "PROJ-9", "base": "1a2b3c4",
                            "model": "claude:claude-sonnet-5-5", "at": "2026-11-13T09:08:07Z",
                            "dispatch": "ctx_abc", "blocked": False}),
            (START_BLOCKED, {"ticket": "T1", "issues": ["PROJ-9"], "issues_text": "PROJ-9", "base": "1a2b3c4",
                             "model": "claude:claude-sonnet-5-5", "at": "2026-11-13T09:08:07Z",
                             "dispatch": "ctx_abc", "blocked": True}),
            (START_SEM_ID + " · blocked", {"ticket": "T1", "issues": ["PROJ-9"], "issues_text": "PROJ-9", "base": "1a2b3c4",
                                            "model": "claude:claude-sonnet-5-5", "at": "2026-11-13T09:08:07Z",
                                            "dispatch": None, "blocked": True}),
            (ANTIGO, {"ticket": "T2", "issues": ["SC-122"], "issues_text": "SC-122", "base": "def5678", "model": "claude-opus-5-5",
                      "at": None, "dispatch": "ctx_bbb222", "blocked": False}),
            ("T3 · SC-1, SC-2 · base abc1234 · dispatch ctx_x · model m · blocked",
             {"ticket": "T3", "issues": ["SC-1", "SC-2"], "issues_text": "SC-1, SC-2", "base": "abc1234", "model": "m", "at": None,
              "dispatch": "ctx_x", "blocked": True}),
            ("T4", {**vazio, "ticket": "T4"}),
            ("T5 · -", {**vazio, "ticket": "T5", "issues_text": "-"}),
            ("", vazio),
        ]
        for entry, esperado in tabela:
            with self.subTest(entry=entry):
                self.assertEqual(handoff.parse_dispatch_entry(entry), esperado)

    def test_ponte_modelo_do_start(self):  # C2
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "tasks.md").write_text(
            make_tasks([{"tid": "T1"}, {"tid": "T2"}]) + HANDOFF.format(d=f"{START_COM_ID}; {ANTIGO}"),
            encoding="utf-8")
        workers = ponte.snapshot(self.repo)["workers"]
        self.assertEqual(workers, [
            {"label": "T1", "issues": ["PROJ-9"], "base": "1a2b3c4", "dispatch": "ctx_abc",
             "model": "claude:claude-sonnet-5-5"},
            {"label": "T2", "issues": ["SC-122"], "base": "def5678", "dispatch": "ctx_bbb222",
             "model": "claude-opus-5-5"},
        ])
        self.assertEqual(ponte.parse_dispatched(START_SEM_ID), [
            {"label": "T1", "issues": ["PROJ-9"], "base": "1a2b3c4", "dispatch": None,
             "model": "claude:claude-sonnet-5-5"}])

    def test_dispatch_usa_leitor_unico(self):  # C2
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        late = "T1 · PROJ-7 · base abc1234 · claude:claude-sonnet-5-5 · 2026-11-07T16:00:00Z · disp_1"
        blocked = "T2 · PROJ-8 · base abc1234 · codex:gpt-6-luna · 2026-11-07T16:00:00Z · disp_2 · blocked"
        sem_base = "T3 · PROJ-9 · claude:x"

        def grava(value: str) -> None:
            (fdir / "tasks.md").write_text(
                make_tasks([{"tid": "T1"}, {"tid": "T2"}, {"tid": "T3"}]) + HANDOFF.format(d=value),
                encoding="utf-8")
            run_git(self.repo, "add", ".")
            run_git(self.repo, "commit", "-q", "--allow-empty", "-m", "specs")

        spy = mock.Mock(wraps=handoff.parse_dispatch_entry)
        # overdue: o horário e o `blocked` vêm do leitor; a saída é a de sempre
        grava(f"{late}; {blocked}")
        with mock.patch.object(handoff, "parse_dispatch_entry", spy):
            res = dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z")
        self.assertEqual(res, (0, ["T1 · PROJ-7 · 45 min · disp_1"]))
        self.assertEqual([c.args[0] for c in spy.call_args_list], [late, blocked])
        grava("T1 · PROJ-7 · base abc1234")
        with self.assertRaises(ValueError) as cm:
            dispatch.overdue("demo", self.repo, 30, "2026-11-07T16:45:00Z")
        self.assertEqual(str(cm.exception), "entrada de Dispatched sem horário legível: T1 · PROJ-7 · base abc1234")
        # settle: a base vem do leitor; entrada sem base é recusada com saída 2, antes do gate
        run_git(self.repo, "checkout", "-q", "-b", "feature/demo")
        out: list[str] = []
        grava(sem_base)
        spy.reset_mock()
        gate = FakeGate()
        with mock.patch.object(handoff, "parse_dispatch_entry", spy):
            code = dispatch.settle("demo", "T3", "main", self.repo, runner=gate, emit=out.append)
        self.assertEqual((code, out), (2, ["settle recusado: a entrada de T3 em Dispatched não traz a base"]))
        self.assertEqual([c.args[0] for c in spy.call_args_list], [sem_base])
        self.assertEqual(gate.gates(), [])
        # com a entrada do start, o gate recebe `<base>..<ramo>` lida pelo leitor
        grava(START_SEM_ID)
        out.clear()
        spy.reset_mock()
        gate = FakeGate(code=1, out="FALHA: x")
        with mock.patch.object(handoff, "parse_dispatch_entry", spy):
            code = dispatch.settle("demo", "T1", "main", self.repo, runner=gate, emit=out.append)
        self.assertEqual((code, out), (1, ["gate vermelho: T1", "FALHA: x"]))
        self.assertEqual([c.args[0] for c in spy.call_args_list], [START_SEM_ID])
        self.assertEqual(gate.calls[gate.gates()[0]][-5:-2], ["demo", "T1", "1a2b3c4..main"])
        # caminho de sucesso: gate verde, merge do ramo do ticket e a mesma saída de sempre
        run_git(self.repo, "checkout", "-q", "-b", "ticket/t1")
        (self.repo / "a.txt").write_text("x\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feat: T1")
        run_git(self.repo, "checkout", "-q", "feature/demo")
        grava(START_SEM_ID)
        out.clear()
        spy.reset_mock()
        gate = FakeGate()
        with mock.patch.object(handoff, "parse_dispatch_entry", spy):
            code = dispatch.settle("demo", "T1", "ticket/t1", self.repo, runner=gate, emit=out.append)
        short = run_git(self.repo, "rev-parse", "--short", "HEAD")
        self.assertEqual((code, out), (0, [f"integrado T1 em feature/demo: {short}"]))
        self.assertEqual([c.args[0] for c in spy.call_args_list], [START_SEM_ID])
        self.assertEqual(gate.calls[gate.gates()[0]][2:6], ["ticket", "demo", "T1", "1a2b3c4..ticket/t1"])

    def test_overdue_preserva_campo_de_issues(self):  # C2 (achado 1)
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        entry = "T8 · SC-2,SC-3 · base abc1234 · claude:m · 2026-11-07T16:00:00Z · ctx_1"
        (fdir / "tasks.md").write_text(make_tasks([{"tid": "T8"}]) + HANDOFF.format(d=entry), encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        res = dispatch.overdue("demo", self.repo, 30, "2026-11-07T17:00:00Z")
        self.assertEqual(res, (0, ["T8 · SC-2,SC-3 · 60 min · ctx_1"]))

    def test_manifesto_sem_storage(self):  # C3
        m = json.loads((ROOT / "src" / "orca" / "orca-plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(c["kind"] for c in m["capabilities"]),
                         ["agent:launch", "agent:read", "workspace:read", "workspace:write"])
        self.assertNotIn("storage:own", json.dumps(m))

    def test_ci_pulo_visivel(self):  # C7
        bash = find_bash()
        if bash is None:
            self.skipTest("sem bash compatível com caminhos do Windows (bash do Git ausente)")
        script = run_step()
        self.assertEqual(script.count("orca plugin validate src/orca --json"), 1)
        work = Path(tempfile.mkdtemp(prefix="starcode-ci-"))
        self.addCleanup(shutil.rmtree, work, True)
        # PATH só com o essencial para o bash: nenhuma pasta que tenha `orca`
        sem_orca = work / "bin-sem"
        sem_orca.mkdir()
        for tool in ("cat", "echo", "dirname", "env"):
            found = shutil.which(tool)
            if found:
                shutil.copy(found, sem_orca / Path(found).name)
        summary = work / "summary.md"
        env = {**os.environ, "GITHUB_STEP_SUMMARY": summary.as_posix(), "PATH": str(sem_orca)}
        res = subprocess.run([bash, "-c", script], env=env, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.splitlines(), ["orca ausente: validação do plugin pulada", AVISO])
        self.assertEqual(summary.read_text(encoding="utf-8"), RESUMO + "\n")
        # com um `orca` falso no PATH, chama o validate e não avisa nem grava o resumo
        fake = work / "bin-com"
        fake.mkdir()
        log = work / "orca.log"
        (fake / "orca").write_text(f'#!/bin/sh\necho "$@" > "{log.as_posix()}"\n', encoding="utf-8", newline="\n")
        (fake / "orca").chmod((fake / "orca").stat().st_mode | stat.S_IXUSR)
        summary2 = work / "summary2.md"
        env2 = {**env, "GITHUB_STEP_SUMMARY": summary2.as_posix(), "PATH": f"{fake}{os.pathsep}{sem_orca}"}
        res = subprocess.run([bash, "-c", script], env=env2, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(log.read_text(encoding="utf-8"), "plugin validate src/orca --json\n")
        self.assertEqual(res.stdout, "")
        self.assertFalse(summary2.exists())

    def test_decisions_e_changelog(self):  # C8
        entry = decisions_entry("SC-207")
        partes = {}
        for nome in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            m = re.search(rf"^- \*\*{nome}\*\*: (.+)$", entry, re.M)
            self.assertIsNotNone(m, nome)
            partes[nome] = m.group(1)
        decisao = partes["Decisão"]
        # cada requisito R1..R8, na ordem, traz as suas condições e campos no próprio trecho
        trechos = re.split(r"(?:(?<=\. )|^)(?=R[1-8]: )", decisao)
        trechos = [t for t in trechos if t]
        self.assertEqual([t[:3] for t in trechos], [f"R{n}:" for n in range(1, 9)])
        exigidos = {
            "R1": ["`handoff.parse_dispatch_entry(entry)`", "`ticket`", "`issues` (lista)",
                   "`issues_text` (o campo como foi gravado)", "`base`", "`model`", "`at`", "`dispatch`",
                   "`blocked`", "formato do `start`", "`<cli>:<modelo>`", "`at` o horário",
                   "`dispatch` o id quando houver", "formato antigo", "`dispatch` e `model` dos campos prefixados",
                   "campo ausente vira `None`", "nunca exceção"],
            "R2": ["`parse_dispatched` (`ponte.py`)", "o horário do `overdue`", "a base do `settle`",
                   "(`dispatch.py`)", "esse leitor", "sem mudar a saída nem os códigos de saída",
                   "`issues_text`", "`SC-2,SC-3`", "`_entry_base` saiu"],
            "R3": ["`src/orca/orca-plugin.json`", "deixa de declarar `storage:own`"],
            "R4": ["`worker.ts`", "`issue.url`", "começa com `https://linear.app/`", "o resto vira `null`"],
            "R5": ["`agentFor`", "rótulo e issues", "título do agente", "token inteiro",
                   "início, fim ou caractere que não seja letra nem número Unicode",
                   "`T1` não casa com `T1é`", "`T1` casa com `LaForge T1`", "não com `LaForge T10`"],
            "R6": ["nome do worktree no diário", "último trecho separado por `/` ou `\\`"],
            "R7": ["sem `orca` no PATH", AVISO, RESUMO, "`$GITHUB_STEP_SUMMARY`", "com `orca`",
                   "`orca plugin validate src/orca --json`"],
            "R8": ["esta entrada", "`CHANGELOG.md`"],
        }
        for trecho in trechos:
            req = trecho[:2]
            for termo in exigidos[req]:
                with self.subTest(req=req, termo=termo):
                    self.assertIn(termo, trecho)
        prova = partes["Por que não é bug"]
        for nome in ("test_parse_dispatch_entry", "test_ponte_modelo_do_start", "test_dispatch_usa_leitor_unico",
                     "test_manifesto_sem_storage", "test_ci_pulo_visivel", "test_decisions_e_changelog",
                     "test_overdue_preserva_campo_de_issues",
                     "issue.url fora do linear vira null", "agentFor casa por token inteiro",
                     "nome do worktree com barra invertida"):
            self.assertIn(nome, prova)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]
        self.assertEqual(len([ln for ln in unreleased.splitlines() if ln.startswith("- Manutenção da Ponte (SC-207):")]), 1)


if __name__ == "__main__":
    unittest.main()
