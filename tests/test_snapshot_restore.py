"""Testes do restore de scripts/snapshot.py (fase 12, T2)."""
from __future__ import annotations

import contextlib
import io
import os
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
        code, out = self.cli("restore", SLUG, "T1", "--yes")
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
        self.assertEqual(self.cli("restore", SLUG, "T1", "--yes")[0], 0)
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
        code, out = self.cli("restore", SLUG, "T1", "--yes")
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
        code, out = self.cli("restore", SLUG, "T1", "--yes")
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
        code, out = self.cli("restore", SLUG, "T1", "--yes")
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

        with mock.patch.object(snapshot, "_write_blob", falha_em_b):  # gravar b.txt falha
            code, out = self.cli("restore", SLUG, "T1", "--yes")
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
        code, out = self.cli("restore", SLUG, "T1", "--yes")
        self.assertEqual(code, 0)
        self.assertEqual(self.read("src/a.txt"), "a\n")
        self.assertEqual(self.read("src/b.txt"), "b\n")
        self.assertFalse((self.root / "src" / "criado.txt").exists())
        self.assertEqual(self.read("notas.md"), "edição do usuário\n")
        self.assertEqual(git(self.root, "rev-list", "--count", "HEAD"), commits)


if __name__ == "__main__":
    unittest.main()
