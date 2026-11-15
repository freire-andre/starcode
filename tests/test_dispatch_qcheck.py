"""Tests for `dispatch.py q-check` and its wiring (SC-181)."""
from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git

import dispatch

FEAT = ".specs/features/demo"
OK_MSG = "q-check: só arquivos permitidos alterados\n"


def write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def run_qcheck(repo) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(["q-check", "demo", "--root", str(repo)])
    return code, out.getvalue(), err.getvalue()


def snapshot(repo: Path) -> dict:
    return {p: p.read_bytes() for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts}


class QCheckCase(TempRepoCase):
    def setUp(self) -> None:
        super().setUp()
        for rel in (f"{FEAT}/spec.md", f"{FEAT}/tasks.md", f"{FEAT}/verification.md", f"{FEAT}/captures/x.png"):
            write(self.repo, rel, "base\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feature")

    def test_q_check_so_permitidos_sai_0(self):
        self.assertEqual(run_qcheck(self.repo), (0, OK_MSG, ""))
        write(self.repo, f"{FEAT}/verification.md", "mudou\n")
        write(self.repo, f"{FEAT}/screens.md", "novo\n")
        write(self.repo, f"{FEAT}/captures/x.running.png", "png\n")
        self.assertEqual(run_qcheck(self.repo), (0, OK_MSG, ""))

    def test_q_check_fora_da_lista_sai_1_sem_tocar(self):
        write(self.repo, f"{FEAT}/verification.md", "mudou\n")
        write(self.repo, f"{FEAT}/tasks.md", "mudou\n")
        (self.repo / FEAT / "spec.md").unlink()
        write(self.repo, "notas.txt", "n\n")
        write(self.repo, f"{FEAT}/captures/x.png", "mudou\n")
        write(self.repo, ".specs/features/outra/verification.md", "v\n")
        before = run_git(self.repo, "status", "--porcelain", "--untracked-files=all")
        files = snapshot(self.repo)
        code, out, err = run_qcheck(self.repo)
        expected = (
            f"fora da lista:  M {FEAT}/captures/x.png\n"
            f"fora da lista:  D {FEAT}/spec.md\n"
            f"fora da lista:  M {FEAT}/tasks.md\n"
            f"fora da lista: ?? .specs/features/outra/verification.md\n"
            f"fora da lista: ?? notas.txt\n"
            "q-check: 5 arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)\n"
        )
        self.assertEqual((code, out, err), (1, expected, ""))
        self.assertEqual(run_git(self.repo, "status", "--porcelain", "--untracked-files=all"), before)
        self.assertEqual(snapshot(self.repo), files)

    def test_q_check_indice_conta_como_fora(self):
        write(self.repo, f"{FEAT}/tasks.md", "mudou\n")
        run_git(self.repo, "add", f"{FEAT}/tasks.md")
        self.assertEqual(run_qcheck(self.repo), (
            1, f"fora da lista: M  {FEAT}/tasks.md\n"
               "q-check: 1 arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)\n", ""))

    def test_q_check_renomeacao(self):
        run_git(self.repo, "mv", f"{FEAT}/verification.md", f"{FEAT}/screens.md")
        self.assertEqual(run_qcheck(self.repo), (0, OK_MSG, ""))
        run_git(self.repo, "commit", "-q", "-m", "renomeia")
        run_git(self.repo, "mv", f"{FEAT}/tasks.md", f"{FEAT}/verification.md")
        self.assertEqual(run_qcheck(self.repo), (
            1, f"fora da lista: R  {FEAT}/tasks.md -> {FEAT}/verification.md\n"
               "q-check: 1 arquivo(s) fora da lista; desfaça com git restore (rastreados) ou apague (novos)\n", ""))

    def test_q_check_fora_de_repositorio_sai_2(self):
        with tempfile.TemporaryDirectory(prefix="starcode-nogit-") as d:
            res = subprocess.run(["git", "status", "--porcelain"], cwd=d, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
            why = res.stderr.strip().splitlines()[0]
            code, out, err = run_qcheck(d)
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(err, f"ERRO: git status falhou em {Path(d).resolve()}: {why}\n")


class WiringCase(unittest.TestCase):
    def test_execute_commita_handoff_antes_do_q(self):
        text = (ROOT / "skills" / "engajar" / "references" / "execute.md").read_text(encoding="utf-8")
        sec = text[text.index("## 4. Proofs and the Q"):text.index("## 5. Post-Q cycle")]
        lines = sec.splitlines()
        phase = next(i for i, l in enumerate(lines) if 'python "P/scripts/handoff.py" set <slug> --phase review' in l)
        self.assertEqual(lines[phase].strip(),
                         '`python "P/scripts/handoff.py" set <slug> --phase review` and **commit the Handoff** '
                         "(`docs(specs): handoff antes do Q (<slug>)` + `Refs`)")
        self.assertEqual(lines[phase - 1].strip(), "2. Green → commit `proofs.md` (`docs(specs): provas (<slug>)` + `Refs`), then")
        start = next(i for i, l in enumerate(lines) if l.strip().startswith("orca orchestration worker-start --agent codex"))
        self.assertLess(phase, start)
        check = 'python "P/scripts/dispatch.py" q-check <slug>'
        self.assertEqual(sec.count(check), 1)
        step = next(i for i, l in enumerate(lines) if l.startswith("7. Right after the Q's `worker_done`, run"))
        self.assertLess(start, step)
        self.assertEqual(lines[step + 1].strip(), f"`{check}` (it only reports; the Q writes only `verification.md`): exit 0 means only the allowed files")
        self.assertEqual([i for i, l in enumerate(lines) if check in l], [step + 1])

    def test_decisions_q_preserva_handoff(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        entry = text[text.index("### SC-181:"):]
        nxt = entry.find("\n### ", 4)
        entry = entry if nxt == -1 else entry[:nxt]
        fields = {}
        for line in entry.splitlines():
            for name in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
                if line.startswith(f"- **{name}**: "):
                    fields[name] = line
        self.assertEqual(sorted(fields), sorted(("Problema", "Decisão", "Motivo", "Por que não é bug")))
        decisao = fields["Decisão"]
        self.assertIn("`q-check` é exceção registrada ao congelamento D-i (novos subcomandos e opções)", decisao)
        self.assertIn("manda o Picard rodar `handoff.py set <slug> --phase review`, commitar o Handoff antes do `worker-start` do Q", decisao)
        self.assertIn("e rodar `python \"P/scripts/dispatch.py\" q-check <slug>` logo após o `worker_done`", decisao)
        self.assertIn("com o Handoff commitado a árvore do Q está limpa", fields["Motivo"])


if __name__ == "__main__":
    unittest.main()
