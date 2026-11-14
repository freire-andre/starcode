"""Testes do restore de scripts/snapshot.py (fase 12, T2)."""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

import helpers  # noqa: F401  (sys.path)
import handoff
import snapshot

SLUG = "feat"
TASKS = """# Feat: Tasks

## Tasks

### T1: Primeiro
**Linear**: SC-1
**Depends on**: none

#### TASK
Fazer.

#### BOUNDARIES
May change: `src/`
Do not touch: `docs/`

### T2: Sem May change
**Depends on**: none

#### TASK
Fazer.

#### BOUNDARIES
Do not touch: `docs/`
"""


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


class RestoreBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-restore-")
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "T")
        git(self.root, "config", "user.email", "t@example.com")
        self.write("src/a.txt", "a\n")
        self.write("src/b.txt", "b\n")
        self.write("src/c.txt", "c\n")
        self.write("notas.md", "notas\n")
        self.write(f".specs/features/{SLUG}/tasks.md", TASKS)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")

    def read(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = snapshot.main([*args, "--root", str(self.root)])
        return code, out.getvalue()

    def plan_then_yes(self, ticket="T1"):
        code, out = self.cli("restore", SLUG, ticket)
        self.assertEqual(code, 0, out)
        return self.cli("restore", SLUG, ticket, "--yes")

    def plan_file(self, ticket="T1"):
        return self.root / ".git" / "starcode" / f"restore-{SLUG}-{ticket}.json"

    def refs(self):
        return git(self.root, "for-each-ref", "refs/starcode").strip()

    def tree_state(self):
        files = {}
        for p in sorted(self.root.rglob("*")):
            if p.is_file() and ".git" not in p.relative_to(self.root).parts:
                files[p.relative_to(self.root).as_posix()] = p.read_bytes()
        return files


class RestoreTest(RestoreBase):
    def take_and_edit(self):
        self.assertEqual(self.cli("take", SLUG, "T1")[0], 0)
        self.write("src/a.txt", "a2\n")
        (self.root / "src" / "b.txt").unlink()
        self.write("src/novo.txt", "novo\n")
        self.write("notas.md", "editado\n")

    def test_restore_sem_yes_mostra_plano_e_nao_altera(self):
        self.take_and_edit()
        antes = self.tree_state()
        idx = (self.root / ".git" / "index").read_bytes()
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        self.assertIn("plano feat/T1 (May change: src/)", out)
        self.assertIn("  voltar   src/a.txt", out)
        self.assertIn("  voltar   src/b.txt", out)
        self.assertIn("  remover  src/novo.txt", out)
        self.assertIn("fora do ticket (não tocados):\n  notas.md", out)
        self.assertIn("nada foi alterado: rode de novo com --yes depois da confirmação do usuário", out)
        self.assertEqual(self.tree_state(), antes)
        self.assertEqual((self.root / ".git" / "index").read_bytes(), idx)

    def test_restore_yes_volta_e_remove_so_no_may_change(self):
        self.take_and_edit()
        idx = (self.root / ".git" / "index").read_bytes()
        code, out = self.plan_then_yes()
        self.assertEqual(code, 0)
        self.assertIn("restaurado feat/T1: 2 voltaram, 1 removidos", out)
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertEqual(self.read("src/b.txt"), "b\n")
        self.assertFalse((self.root / "src" / "novo.txt").exists())
        self.assertEqual(self.read("notas.md"), "editado\n")
        self.assertEqual((self.root / ".git" / "index").read_bytes(), idx)

    @unittest.skipIf(os.name == "nt", "bit executável não existe no Windows")
    def test_restore_yes_devolve_bit_executavel(self):
        self.write("src/run.sh", "#!/bin/sh\n")
        (self.root / "src" / "run.sh").chmod(0o755)
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "exec")
        self.cli("take", SLUG, "T1")
        (self.root / "src" / "run.sh").chmod(0o644)
        self.write("src/run.sh", "mudou\n")
        self.assertEqual(self.plan_then_yes()[0], 0)
        self.assertTrue(os.access(self.root / "src" / "run.sh", os.X_OK))

    def test_restore_lista_fora_do_ticket_com_limite(self):
        self.cli("take", SLUG, "T1")
        for i in range(53):
            self.write(f"fora/f{i:02d}.txt", "x\n")
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        linhas = out.split("fora do ticket (não tocados):\n", 1)[1].splitlines()
        self.assertEqual([ln for ln in linhas if ln.startswith("  fora/")].__len__(), 50)
        self.assertIn("e mais 3", linhas)
        code, out = self.plan_then_yes()
        self.assertIn("e mais 3", out)
        self.assertTrue((self.root / "fora" / "f52.txt").exists())

    def test_restore_recusa_head_mudado(self):
        self.take_and_edit()
        pai = git(self.root, "rev-parse", "HEAD").strip()
        git(self.root, "add", "notas.md")
        git(self.root, "commit", "-q", "-m", "outro")
        atual = git(self.root, "rev-parse", "HEAD").strip()
        self.assertNotEqual(pai, atual)
        antes = self.tree_state()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(out, f"HEAD mudou desde o snapshot ({pai[:7]} → {atual[:7]}): restauração recusada\n")
        self.assertEqual(self.tree_state(), antes)

    def test_restore_pasta_no_lugar_de_arquivo(self):
        self.assertEqual(self.cli("take", SLUG, "T1")[0], 0)
        (self.root / "src" / "a.txt").unlink()
        self.write("src/a.txt/dentro.txt", "x\n")
        code, out = self.plan_then_yes()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertFalse((self.root / "src" / "a.txt").is_dir())

    def test_restore_sem_snapshot_ou_ticket_sem_may_change(self):
        antes = self.tree_state()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(out, "sem snapshot de feat/T1: restauração recusada\n")
        motivos = (("T2", "ticket T2 sem May change"), ("T9", "ticket T9 não está no tasks.md de feat"))
        for ticket, motivo in motivos:
            self.cli("take", SLUG, ticket)
            code, out = self.cli("restore", SLUG, ticket, "--yes")
            self.assertEqual(code, 1)
            self.assertEqual(out, f"{motivo}: restauração recusada\n")
        self.assertEqual(self.tree_state(), antes)

    def test_restore_ignora_entrada_que_sai_da_raiz(self):
        self.write(f".specs/features/{SLUG}/tasks.md", TASKS.replace("May change: `src/`", "May change: `src/`, `../fora/`"))
        self.cli("take", SLUG, "T1")
        self.write("src/a.txt", "a2\n")
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        self.assertIn("aviso: May change ignorado", out)
        self.assertIn("voltar   src/a.txt", out)

    def test_restore_sem_tasks_usa_may_change_da_spec(self):
        (self.root / ".specs" / "features" / SLUG / "tasks.md").unlink()
        self.write(f".specs/features/{SLUG}/spec.md", "# Spec\n\n**May change**: `src/`\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "spec")
        self.cli("take", SLUG, "T1")
        self.write("src/a.txt", "a2\n")
        self.write("notas.md", "editado\n")
        code, out = self.plan_then_yes()
        self.assertEqual(code, 0)
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertEqual(self.read("notas.md"), "editado\n")

    def test_restore_falha_parcial_e_retomada(self):
        self.cli("take", SLUG, "T1")
        self.write("src/a.txt", "a2\n")
        self.write("src/c.txt", "c2\n")
        (self.root / "src" / "b.txt").unlink()
        real = snapshot._write_blob

        def falha_em_b(root, snap, path):
            if path == "src/b.txt":
                raise OSError("disco cheio")
            real(root, snap, path)

        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        with mock.patch.object(snapshot, "_write_blob", falha_em_b):  # gravar b.txt falha
            code, out = self.cli("restore", SLUG, "T1", "--yes")
        pre = git(self.root, "rev-parse", "refs/starcode/pre-restore/feat/T1").strip()
        self.assertEqual(code, 1)
        self.assertIn("restaurados (1):", out)
        self.assertIn("voltar   src/a.txt", out)
        self.assertIn("falhou: voltar src/b.txt", out)
        self.assertIn("faltaram (", out)
        self.assertIn("src/c.txt", out.split("faltaram (", 1)[1])
        self.assertEqual(self.read("src/c.txt"), "c2\n")
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("src/b.txt"), "b\n")
        self.assertEqual(self.read("src/c.txt"), "c\n")
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertNotIn("pre-restore", out)
        self.assertEqual(git(self.root, "rev-parse", "refs/starcode/pre-restore/feat/T1").strip(), pre)
        self.assertFalse(self.plan_file().exists())

    def test_restore_dry_run_apos_falha_parcial_regrava_pre_restore(self):
        self.cli("take", SLUG, "T1")
        self.write("src/a.txt", "a2\n")
        self.write("src/c.txt", "c2\n")
        (self.root / "src" / "b.txt").unlink()
        real = snapshot._write_blob

        def falha_em_b(root, snap, path):
            if path == "src/b.txt":
                raise OSError("disco cheio")
            real(root, snap, path)

        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        with mock.patch.object(snapshot, "_write_blob", falha_em_b):
            self.assertEqual(self.cli("restore", SLUG, "T1", "--yes")[0], 1)
        ref = "refs/starcode/pre-restore/feat/T1"
        primeiro = git(self.root, "rev-parse", ref).strip()
        self.write("src/novo.txt", "novo\n")
        self.write("src/b.txt", "b editado\n")
        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        self.assertFalse(json.loads(self.plan_file().read_text(encoding="utf-8"))["started"])
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        segundo = git(self.root, "rev-parse", ref).strip()
        self.assertIn("pre-restore " + segundo[:7], out)
        self.assertNotEqual(segundo, primeiro)
        self.assertEqual(git(self.root, "show", f"{ref}:src/novo.txt"), "novo\n")
        self.assertEqual(git(self.root, "show", f"{ref}:src/b.txt"), "b editado\n")
        parents = git(self.root, "rev-list", "--parents", "-n", "1", ref).split()
        self.assertEqual(parents[1], git(self.root, "rev-parse", "HEAD").strip())
        self.assertEqual(parents[2], primeiro)
        self.assertEqual(len(parents), 3)

    def test_restore_falha_ao_apagar_plano_avisa(self):
        self.take_and_edit()
        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        real = Path.unlink

        def unlink_falha(self_, *a, **k):
            if self_.name.startswith("restore-"):
                raise OSError("arquivo em uso")
            return real(self_, *a, **k)

        with mock.patch.object(Path, "unlink", unlink_falha):
            code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertIn("restaurado feat/T1, mas o plano não foi apagado: arquivo em uso; "
                      "rode restore --yes de novo para limpar\n", out)
        self.assertTrue(self.plan_file().exists())
        self.assertEqual(self.read("src/a.txt"), "a\n")
        pre = git(self.root, "rev-parse", "refs/starcode/pre-restore/feat/T1").strip()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        self.assertNotIn("pre-restore", out)
        self.assertFalse(self.plan_file().exists())
        self.assertEqual(git(self.root, "rev-parse", "refs/starcode/pre-restore/feat/T1").strip(), pre)

    def test_restore_dry_run_grava_plano(self):
        self.take_and_edit()
        idx = (self.root / ".git" / "index").read_bytes()
        status = git(self.root, "status", "--porcelain")
        refs = self.refs()
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        data = json.loads(self.plan_file().read_text(encoding="utf-8"))
        self.assertEqual(data["snapshot"], git(self.root, "rev-parse", "refs/starcode/snapshots/feat/T1").strip())
        self.assertEqual(sorted(map(tuple, data["lines"])),
                         [("remover", "src/novo.txt"), ("voltar", "src/a.txt"), ("voltar", "src/b.txt")])
        for acao, caminho in data["lines"]:
            self.assertIn(f"  {acao:<8} {caminho}", out)
        self.assertEqual((self.root / ".git" / "index").read_bytes(), idx)
        self.assertEqual(git(self.root, "status", "--porcelain"), status)
        self.assertEqual(self.refs(), refs)

    def test_restore_recusa_snapshot_ausente_fora_do_ticket(self):
        self.write("fora.txt", "fora\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "fora")
        self.cli("take", SLUG, "T1")
        (self.root / "fora.txt").rename(self.root / "src" / "fora.txt")
        refs = self.refs()
        for args in (("restore", SLUG, "T1"), ("restore", SLUG, "T1", "--yes")):
            code, out = self.cli(*args)
            self.assertEqual(code, 1)
            self.assertEqual(out, "restauração recusada: arquivos do snapshot ausentes fora do ticket:\n  fora.txt\n")
            self.assertTrue((self.root / "src" / "fora.txt").exists())
            self.assertFalse(self.plan_file().exists())
            self.assertEqual(self.refs(), refs)
            self.assertNotIn("pre-restore", self.refs())

    def test_restore_edicao_fora_do_ticket_nao_recusa(self):
        self.cli("take", SLUG, "T1")
        self.write("notas.md", "editado\n")
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        cab = "fora do ticket (não tocados):"
        listados = []
        for ln in out.split(cab + "\n", 1)[1].splitlines():
            if not ln.startswith("  "):
                break
            listados.append(ln[2:])
        self.assertEqual(listados, ["notas.md"])
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("notas.md"), "editado\n")

    def test_restore_yes_sem_plano_recusa(self):
        self.take_and_edit()
        antes = self.tree_state()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(out, "sem plano gravado de feat/T1: rode restore sem --yes primeiro\n")
        self.assertEqual(self.tree_state(), antes)
        self.assertNotIn("pre-restore", self.refs())

    def test_restore_yes_plano_mudou_recusa(self):
        self.take_and_edit()
        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        self.write("src/novo2.txt", "novo2\n")
        antes = self.tree_state()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(out, "plano mudou desde o dry-run: rode restore sem --yes de novo\n")
        self.assertEqual(self.tree_state(), antes)
        self.assertNotIn("pre-restore", self.refs())

    def test_restore_yes_snapshot_diferente_do_plano_recusa(self):
        self.take_and_edit()
        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        git(self.root, "update-ref", "-d", "refs/starcode/snapshots/feat/T1")
        self.cli("take", SLUG, "T1")
        antes = self.tree_state()
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual((code, out), (1, "plano mudou desde o dry-run: rode restore sem --yes de novo\n"))
        self.assertEqual(self.tree_state(), antes)

    def test_restore_grava_pre_restore_e_apaga_plano(self):
        self.take_and_edit()
        code, out = self.plan_then_yes()
        self.assertEqual(code, 0)
        pre_ref = "refs/starcode/pre-restore/feat/T1"
        curto = git(self.root, "rev-parse", "--short", pre_ref).strip()
        self.assertIn(f"pre-restore {curto}\n", out)
        self.assertLess(out.index("pre-restore"), out.index("restaurado feat/T1"))
        self.assertEqual(git(self.root, "show", f"{pre_ref}:src/a.txt"), "a2\n")
        self.assertEqual(git(self.root, "show", f"{pre_ref}:src/novo.txt"), "novo\n")
        self.assertEqual(git(self.root, "rev-parse", f"{pre_ref}^").strip(), git(self.root, "rev-parse", "HEAD").strip())
        self.assertFalse(self.plan_file().exists())

    def test_restore_pre_restore_falha_nao_toca_arquivos(self):
        self.take_and_edit()
        self.assertEqual(self.cli("restore", SLUG, "T1")[0], 0)
        antes = self.tree_state()

        def falha(*_a, **_k):
            raise snapshot.GitError("update-ref", "sem espaço")

        with mock.patch.object(snapshot, "_write_pre_restore", falha):
            code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 1)
        self.assertEqual(out, "restauração recusada: pre-restore falhou: sem espaço\n")
        self.assertEqual(self.tree_state(), antes)
        self.assertNotIn("pre-restore", self.refs())

    def test_drop_remove_pre_restore_e_planos_da_feature(self):
        for slug in ("feat", "outra", "feat-x"):
            if slug != "feat":
                shutil.copytree(self.root / ".specs" / "features" / "feat", self.root / ".specs" / "features" / slug)
            self.cli("take", slug, "T1")
            self.write("src/a.txt", f"a-{slug}\n")
            self.assertEqual(self.cli("restore", slug, "T1")[0], 0)
            self.assertEqual(self.cli("restore", slug, "T1", "--yes")[0], 0)
            self.write("src/a.txt", f"b-{slug}\n")
            self.assertEqual(self.cli("restore", slug, "T1")[0], 0)  # deixa um plano gravado
        pasta = self.root / ".git" / "starcode"
        self.assertEqual(len(list(pasta.glob("restore-*.json"))), 3)
        for nome in ("restore-feat-T1.json", "restore-feat-x-T1.json"):
            (pasta / nome).write_text("{ ilegível", encoding="utf-8")  # JSON ilegível: sem slug gravado
        code, out = self.cli("drop", "feat")
        self.assertEqual(code, 0)
        refs = git(self.root, "for-each-ref", "--format=%(refname)", "refs/starcode").split()
        self.assertEqual(sorted(refs), [
            "refs/starcode/pre-restore/feat-x/T1", "refs/starcode/pre-restore/outra/T1",
            "refs/starcode/snapshots/feat-x/T1", "refs/starcode/snapshots/outra/T1"])
        self.assertEqual(sorted(f.name for f in pasta.glob("restore-*.json")),
                         ["restore-feat-x-T1.json", "restore-outra-T1.json"])

    def test_decisions_snapshot_restauracao_segura(self):
        text = (Path(__file__).resolve().parents[1] / "DECISIONS.md").read_text(encoding="utf-8")
        entrada = text.split("### SC-174:", 1)[1].split("\n### ", 1)[0]
        for nome in ("**Problema:**", "**Decisão:**", "**Motivo:**", "**Por que não é bug:**", "F12-1", "F12-2", "pre-restore"):
            self.assertIn(nome, entrada)


class AcceptanceTest(RestoreBase):
    def test_cenario_aceite_disjuntor_modo_1(self):
        commits = git(self.root, "rev-list", "--count", "HEAD")
        self.assertEqual(self.cli("take", SLUG, "T1")[0], 0)
        self.write("src/a.txt", "alterado pelo ticket\n")
        self.write("src/criado.txt", "criado pelo ticket\n")
        self.write("notas.md", "edição do usuário\n")
        for _ in range(3):
            with contextlib.redirect_stdout(io.StringIO()):
                handoff.main(["set", SLUG, "--attempt", "gate-x=fail", "--root", str(self.root)])
        self.assertIn("**Breaker:** open", self.read(f".specs/features/{SLUG}/tasks.md"))
        code, out = self.cli("restore", SLUG, "T1")
        self.assertEqual(code, 0)
        self.assertIn("fora do ticket (não tocados):", out)
        self.assertIn("  notas.md", out.split("fora do ticket (não tocados):", 1)[1])
        antes = git(self.root, "rev-parse", "refs/starcode/snapshots/feat/T1")
        self.assertEqual(self.cli("take", SLUG, "T1")[0], 0)  # segundo take não muda o ref
        self.assertEqual(git(self.root, "rev-parse", "refs/starcode/snapshots/feat/T1"), antes)
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertEqual(self.read("src/b.txt"), "b\n")
        self.assertFalse((self.root / "src" / "criado.txt").exists())
        self.assertEqual(self.read("notas.md"), "edição do usuário\n")
        self.assertEqual(git(self.root, "rev-list", "--count", "HEAD"), commits)


if __name__ == "__main__":
    unittest.main()
