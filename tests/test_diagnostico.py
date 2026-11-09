"""Testes de scripts/diagnostico.py (R26-R28, R35) com um npx falso no PATH."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROOT

SCRIPT = ROOT / "scripts" / "diagnostico.py"
SAMPLE = FIXTURES / "diagnostico" / "harness-score-sample.json"
DATE = "2026-11-09"

FAKE_PY = """import os, sys, time
mode = os.environ.get("FAKE_NPX_MODE", "ok")
with open(os.environ["FAKE_NPX_LOG"], "a", encoding="utf-8") as fh:
    fh.write(" ".join(sys.argv[1:]) + "\\n")
if mode == "ok":
    sys.stdout.buffer.write(open(os.environ["FAKE_NPX_SAMPLE"], "rb").read())
elif mode == "garbage":
    print("isto não é json")
elif mode == "fail":
    print("boom", file=sys.stderr)
    sys.exit(3)
elif mode == "slow":
    time.sleep(8)
"""


class DiagnosticoTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="diag-test-")
        tmp = Path(self._tmp.name)
        self.repo = tmp / "repo"
        self.repo.mkdir()
        (self.repo / "AGENTS.md").write_text(
            "# Agentes\n\nVeja `docs/guia.md` e `scripts/inexistente.py` antes de agir.\n", encoding="utf-8")
        self.bin = tmp / "bin"
        self.bin.mkdir()
        self.log = tmp / "npx.log"
        (self.bin / "fake_npx.py").write_text(FAKE_PY, encoding="utf-8")
        if os.name == "nt":
            (self.bin / "npx.cmd").write_text(f'@"{sys.executable}" "%~dp0fake_npx.py" %*\r\n', encoding="utf-8")
        else:
            sh = self.bin / "npx"
            sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{self.bin / "fake_npx.py"}" "$@"\n', encoding="utf-8")
            sh.chmod(0o755)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_diag(self, mode: str = "ok", path_dirs: list[Path] | None = None, extra_env: dict | None = None,
                 date: str = DATE):
        dirs = [self.bin] if path_dirs is None else path_dirs
        env = {**os.environ, "PATH": os.pathsep.join(str(d) for d in dirs), "FAKE_NPX_MODE": mode,
               "FAKE_NPX_LOG": str(self.log), "FAKE_NPX_SAMPLE": str(SAMPLE), **(extra_env or {})}
        res = subprocess.run([sys.executable, "-I", str(SCRIPT), "run", "--root", str(self.repo), "--date", date],
                             capture_output=True, stdin=subprocess.DEVNULL, env=env, timeout=120)
        return res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")

    def report(self, date: str = DATE) -> str:
        return (self.repo / "docs" / "diagnostico" / f"{date}.md").read_text(encoding="utf-8")

    def test_diagnostico_runs_harness_score_and_track_a(self) -> None:
        code, out, err = self.run_diag()
        self.assertEqual(code, 0, out + err)
        calls = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].startswith("--yes harness-score@1.8.4 --json "), calls[0])
        self.assertIn(str(self.repo.resolve()), calls[0])
        run_dir = self.repo / ".harness-eval" / "runs" / f"{DATE}-diag"
        self.assertTrue((run_dir / "inventory.json").is_file())
        self.assertTrue((run_dir / "04-correctness.json").is_file())

    def test_diagnostico_report_contract(self) -> None:
        sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
        code, out, err = self.run_diag()
        self.assertEqual(code, 0, out + err)
        text = self.report()
        lvl = sample["level"]
        self.assertIn(f"**Level**: L{lvl['index']} · {lvl['name']}", text)
        self.assertIn(f"**Score**: {sample['score']['earned']}/{sample['score']['max']}", text)
        self.assertIn("| Dimensão | % |", text)
        for d in sample["dimensions"]:
            self.assertIn(f"| {d['title']} | {d['percent']}% |", text)
        self.assertIn(f"Próximo degrau: To reach L{lvl['index'] + 1}: " + "; ".join(lvl["nextLevelGaps"]), text)
        self.assertRegex(text, r"\*\*Track A\*\*: [1-9]\d* quebrados")
        self.assertIn("- `AGENTS.md`: ", text)
        self.assertIn("**Tracks B/C**: não executados (sem aprovação de custo)", text)
        # mesma data sobrescreve
        (self.repo / "docs" / "diagnostico" / f"{DATE}.md").write_text("VELHO\n", encoding="utf-8")
        self.assertEqual(self.run_diag()[0], 0)
        self.assertNotIn("VELHO", self.report())
        self.assertEqual(len(list((self.repo / "docs" / "diagnostico").glob("*.md"))), 1)

    def test_diagnostico_failures(self) -> None:
        empty = Path(self._tmp.name) / "vazio"
        empty.mkdir()
        cases = [
            ("npx ausente", dict(path_dirs=[empty]), "npx não encontrado"),
            ("exit != 0", dict(mode="fail"), "código 3"),
            ("json inválido", dict(mode="garbage"), "JSON inválido"),
            ("timeout", dict(mode="slow", extra_env={"STARCODE_DIAGNOSTICO_NPX_TIMEOUT": "1"}), "timeout"),
        ]
        for name, kwargs, motivo in cases:
            with self.subTest(name):
                code, out, err = self.run_diag(**kwargs)
                self.assertEqual(code, 0, out + err)
                text = self.report()
                self.assertIn("**Level**: não executado - ", text)
                self.assertIn(motivo, text)
                self.assertRegex(text, r"\*\*Track A\*\*: \d+ quebrados")
        with self.subTest("track A falhou"):
            # um arquivo no lugar de .harness-eval impede o Track A de gravar
            blocker = self.repo / ".harness-eval"
            for child in sorted(blocker.rglob("*"), reverse=True):
                child.rmdir() if child.is_dir() else child.unlink()
            blocker.rmdir()
            blocker.write_text("arquivo no lugar da pasta", encoding="utf-8")
            code, out, err = self.run_diag()
            self.assertEqual(code, 2, out + err)
            self.assertIn("track A falhou:", err)

    def test_diagnostico_gitignore_warning(self) -> None:
        code, out, err = self.run_diag()
        self.assertEqual(code, 0, out + err)
        warn = [ln for ln in out.splitlines() if ln.startswith("aviso:")]
        self.assertEqual(warn, [f"aviso: .harness-eval/ não está no .gitignore de {self.repo.resolve()}"])
        (self.repo / ".gitignore").write_text("node_modules/\n.harness-eval/\n", encoding="utf-8")
        code, out, err = self.run_diag(date="2026-11-10")
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("aviso:", out)
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".harness-eval/", [ln.strip() for ln in gi])


if __name__ == "__main__":
    unittest.main()
