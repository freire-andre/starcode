from __future__ import annotations

import sys
from pathlib import Path

from helpers import TempRepoCase, run_git

import check_proofs

PY = Path(sys.executable).as_posix()


class ProofsLfTests(TempRepoCase):
    def test_proofs_md_gravado_sem_cr(self):
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n\n**Size**: LARGE\n**Status**: Approved\n",
                                      encoding="utf-8", newline="\n")
        tasks = (f"# Demo: Tasks\n\n## Checks\n\n**Build**: none - sem build\n"
                 f"**Run unit**: `\"{PY}\" -c \"print('test_alpha ... ok')\"`\n\n"
                 "**C1** - alpha passa (R1)\nProof: run unit | test_alpha ... ok\n")
        (fdir / "tasks.md").write_text(tasks, encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "feature")
        check_proofs.evaluate("demo", self.repo)
        data = (fdir / "proofs.md").read_bytes()
        self.assertTrue(data)
        self.assertNotIn(b"\r", data)
