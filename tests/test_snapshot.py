"""Testes de scripts/snapshot.py (fase 12, T1)."""
from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401  (sys.path)
import snapshot


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


class SnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-snap-")
        self.root = Path(self._tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "T")
        git(self.root, "config", "user.email", "t@example.com")
        (self.root / "a.txt").write_text("a\n")
        (self.root / ".gitignore").write_text("ign.txt\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args, root=None):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = snapshot.main([*args, "--root", str(root or self.root)])
        return code, out.getvalue()

    def test_take_grava_ref_com_rastreados_e_novos(self):
        (self.root / "a.txt").write_text("mudou\n")
        (self.root / "novo.txt").write_text("novo\n")
        (self.root / "ign.txt").write_text("x\n")
        code, out = self.run_cli("take", "feat", "SC-1")
        self.assertEqual(code, 0)
        self.assertIn("snapshot feat/SC-1 ", out)
        ref = "refs/starcode/snapshots/feat/SC-1"
        files = git(self.root, "ls-tree", "-r", "--name-only", ref).split()
        self.assertEqual(sorted(files), [".gitignore", "a.txt", "novo.txt"])
        self.assertEqual(git(self.root, "show", f"{ref}:a.txt"), "mudou\n")
        self.assertEqual(git(self.root, "rev-parse", f"{ref}^").strip(), git(self.root, "rev-parse", "HEAD").strip())

    def test_take_nao_altera_indice_arvore_head(self):
        (self.root / "a.txt").write_text("mudou\n")
        (self.root / "novo.txt").write_text("novo\n")
        idx = self.root / ".git" / "index"

        def estado():
            return (idx.read_bytes(), git(self.root, "rev-parse", "HEAD"), git(self.root, "branch", "-a", "-v"),
                    git(self.root, "status", "--porcelain"), (self.root / "a.txt").read_bytes())

        before = estado()
        code, _ = self.run_cli("take", "feat", "SC-1")
        self.assertEqual(code, 0)
        self.assertEqual(before, estado())

    def test_take_substitui_snapshot_existente(self):
        _, first = self.run_cli("take", "feat", "SC-1")
        old = first.split()[2]
        (self.root / "novo.txt").write_text("novo\n")
        code, out = self.run_cli("take", "feat", "SC-1")
        self.assertEqual(code, 0)
        self.assertIn(f"(substituído {old})", out)
        self.assertIn("(3 arquivos)", out)

    def test_take_nome_invalido_sai_2(self):
        for slug, ticket in (("Feat", "SC-1"), ("feat", "_x"), ("feat", "a..b"), ("a/b", "SC-1"), ("feat", "x.lock")):
            code, out = self.run_cli("take", slug, ticket)
            self.assertEqual(code, 2, (slug, ticket))
            self.assertIn("nome inválido para o snapshot", out)
        self.assertEqual(git(self.root, "for-each-ref", "refs/starcode").strip(), "")

    def test_take_sem_head_ou_fora_do_git_sai_1(self):
        with tempfile.TemporaryDirectory(prefix="starcode-snap-") as d:
            code, out = self.run_cli("take", "feat", "SC-1", root=d)
            self.assertEqual(code, 1)
            self.assertIn("snapshot falhou:", out)
            git(d, "init", "-q")
            code, out = self.run_cli("take", "feat", "SC-1", root=d)
            self.assertEqual(code, 1)
            self.assertIn("snapshot falhou:", out)
            self.assertEqual(git(d, "for-each-ref", "refs/starcode").strip(), "")

    def test_list_texto_json_e_vazio(self):
        code, out = self.run_cli("list", "feat")
        self.assertEqual((code, out.strip()), (0, "nenhum snapshot de feat"))
        code, out = self.run_cli("list", "feat", "--json")
        self.assertEqual((code, json.loads(out)), (0, []))
        self.run_cli("take", "feat", "SC-1")
        code, out = self.run_cli("list", "feat")
        self.assertEqual(code, 0)
        self.assertIn("SC-1", out)
        code, out = self.run_cli("list", "feat", "--json")
        rows = json.loads(out)
        self.assertEqual(len(rows), 1)
        self.assertEqual(sorted(rows[0]), ["commit", "date", "files", "ticket"])
        self.assertEqual((rows[0]["ticket"], rows[0]["files"]), ("SC-1", 2))

    def test_drop_remove_refs_da_feature(self):
        self.run_cli("take", "feat", "SC-1")
        self.run_cli("take", "feat", "SC-2")
        self.run_cli("take", "outra", "SC-1")
        code, out = self.run_cli("drop", "feat")
        self.assertEqual((code, out.strip()), (0, "removidos 2 snapshots de feat"))
        refs = git(self.root, "for-each-ref", "--format=%(refname)", "refs/starcode").split()
        self.assertEqual(refs, ["refs/starcode/snapshots/outra/SC-1"])
        code, out = self.run_cli("drop", "feat")
        self.assertEqual((code, out.strip()), (0, "removidos 0 snapshots de feat"))


if __name__ == "__main__":
    unittest.main()
