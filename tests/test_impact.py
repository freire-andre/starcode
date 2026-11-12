from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, run_git

import impact

SCRIPT = ROOT / "scripts" / "impact.py"


def write(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", stdin=subprocess.DEVNULL)


class ImpactCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="impact-test-")
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-q", "-b", "main")
        run_git(self.repo, "config", "user.email", "t@example.com")
        run_git(self.repo, "config", "user.name", "T")
        run_git(self.repo, "config", "commit.gpgsign", "false")
        self.addCleanup(self._tmp.cleanup)

    def commit(self, msg: str = "c") -> None:
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "-q", "-m", msg)

    def chain_repo(self) -> None:
        write(self.repo, {
            "pkg/__init__.py": "",
            "pkg/core.py": "X = 1\n",
            "pkg/mid.py": "from pkg import core\n",
            "tests/test_mid.py": "import pkg.mid\n",
            "tests/test_core.py": "from pkg.core import X\n",
            "tests/test_other.py": "import json\n",
            "README.md": "hi\n",
        })


class TestImpact(ImpactCase):
    def test_select_diff_inclui_nao_rastreados(self) -> None:
        write(self.repo, {"a.py": "A = 1\n", "test_a.py": "import a\n"})
        self.commit("base")
        write(self.repo, {"a.py": "A = 2\n", "b.py": "import a\n", "test_b.py": "import b\n"})
        files = impact.repo_files(self.repo)
        self.assertIn("b.py", files)
        res = impact.select(self.repo, diff="HEAD")
        self.assertEqual(res["changed"], ["a.py", "b.py", "test_b.py"])
        self.assertEqual(res["verdict"], "selected")
        self.assertEqual(res["tests"], ["test_a.py", "test_b.py"])
        self.commit("depois")
        write(self.repo, {"c.py": "import a\n"})
        res = impact.select(self.repo, diff="HEAD~1..HEAD")
        self.assertEqual(res["changed"], ["a.py", "b.py", "c.py", "test_b.py"])

    def test_identifica_testes_python_e_ts(self) -> None:
        for p in ("test_a.py", "a_test.py", "tests/helpers.py", "test/x/y.py", "src/foo.test.ts",
                  "src/foo.spec.js", "src/__tests__/foo.ts", "a/b.test.tsx"):
            self.assertTrue(impact.is_test_file(p), p)
        for p in ("a.py", "src/testing.py", "src/foo.ts", "latest.py", "README.md", "src/contest/x.ts"):
            self.assertFalse(impact.is_test_file(p), p)

    def test_python_imports_absolutos_relativos_e_ambiguos(self) -> None:
        write(self.repo, {
            "a/__init__.py": "",
            "a/b.py": "",
            "a/c.py": "from . import d\nfrom .b import X\n",
            "a/d.py": "",
            "a/sub/__init__.py": "",
            "a/sub/e.py": "from .. import d\nfrom ..b import Y\n",
            "m/util.py": "",
            "n/util.py": "",
            "x.py": "import a.b\nimport os\nimport requests\nfrom m import util\n",
            "y.py": "from a import c\nimport util\n",
        })
        files = impact.repo_files(self.repo)
        graph = impact.build_graph(self.repo, files)
        self.assertEqual(graph["x.py"], {"a/b.py", "m/util.py"})
        self.assertEqual(graph["a/c.py"], {"a/__init__.py", "a/d.py", "a/b.py"})
        self.assertEqual(graph["a/sub/e.py"], {"a/__init__.py", "a/d.py", "a/b.py"})
        self.assertEqual(graph["y.py"], {"a/c.py", "a/__init__.py", "m/util.py", "n/util.py"})

    def test_teste_mudado_entra_no_conjunto(self) -> None:
        self.chain_repo()
        res = impact.select(self.repo, changed=["tests/test_other.py"])
        self.assertEqual(res["verdict"], "selected")
        self.assertEqual(res["tests"], ["tests/test_other.py"])
        self.assertEqual(res["chains"], {"tests/test_other.py": ["tests/test_other.py"]})

    def test_dependentes_transitivos_e_ciclo(self) -> None:
        self.chain_repo()
        write(self.repo, {"pkg/core.py": "from pkg import mid\nX = 1\n"})
        res = impact.select(self.repo, changed=["pkg/core.py"])
        self.assertEqual(res["verdict"], "selected")
        self.assertEqual(res["tests"], ["tests/test_core.py", "tests/test_mid.py"])
        self.assertEqual(res["chains"]["tests/test_mid.py"], ["pkg/core.py", "pkg/mid.py", "tests/test_mid.py"])
        self.assertEqual(res["chains"]["tests/test_core.py"], ["pkg/core.py", "tests/test_core.py"])

    def test_fora_do_grafo_roda_tudo(self) -> None:
        self.chain_repo()
        self.commit()
        (self.repo / "pkg" / "mid.py").unlink()
        res = impact.select(self.repo, changed=["README.md", "pkg/mid.py", "nao_existe.py", "web/app.ts"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertEqual(res["reason"], "fora do grafo: README.md, nao_existe.py, pkg/mid.py, web/app.ts")
        self.assertEqual(res["tests"], [])

    def test_grafo_incompleto_roda_tudo(self) -> None:
        self.chain_repo()
        write(self.repo, {"broken.py": "def (:\n"})
        res = impact.select(self.repo, changed=["pkg/core.py"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertTrue(res["reason"].startswith("grafo incompleto: broken.py: "), res["reason"])
        (self.repo / "broken.py").write_text("x = 1\n", encoding="utf-8")
        (self.repo / "big.py").write_text("#" * (1024 * 1024 + 1), encoding="utf-8")
        res = impact.select(self.repo, changed=["pkg/core.py"])
        self.assertEqual(res["reason"], "grafo incompleto: big.py: arquivo acima de 1 MiB")

    def test_nenhum_teste_alcanca_roda_tudo(self) -> None:
        self.chain_repo()
        write(self.repo, {"lonely.py": "Z = 1\n"})
        res = impact.select(self.repo, changed=["lonely.py"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertEqual(res["reason"], "nenhum teste alcança lonely.py")
        self.assertEqual(res["tests"], [])

    def test_sem_mudanca_roda_tudo(self) -> None:
        self.chain_repo()
        self.commit()
        self.assertEqual(impact.select(self.repo, changed=[])["reason"], "nenhuma mudança informada")
        res = impact.select(self.repo, diff="HEAD")
        self.assertEqual(res["verdict"], "run-all")
        self.assertEqual(res["reason"], "nenhuma mudança informada")

    def test_saida_texto_selecao_e_rodar_tudo(self) -> None:
        self.chain_repo()
        out = cli("select", "--root", str(self.repo), "pkg/core.py")
        self.assertEqual(out.returncode, 0, out.stderr)
        lines = out.stdout.splitlines()
        self.assertEqual(lines[0], "selecionados 2 testes")
        self.assertIn("  pkg/core.py <- pkg/mid.py <- tests/test_mid.py", lines)
        out = cli("select", "--root", str(self.repo), "README.md")
        self.assertEqual(out.returncode, 0)
        self.assertEqual(out.stdout.strip(), "rodar tudo: fora do grafo: README.md")

    def test_saida_json_contrato(self) -> None:
        self.chain_repo()
        out = cli("select", "--root", str(self.repo), "--json", "pkg/core.py")
        data = json.loads(out.stdout)
        self.assertEqual(set(data), {"verdict", "tests", "chains", "reason", "changed"})
        self.assertEqual(data["verdict"], "selected")
        self.assertEqual(data["changed"], ["pkg/core.py"])
        self.assertEqual(data["chains"]["tests/test_core.py"], ["pkg/core.py", "tests/test_core.py"])
        out = cli("select", "--root", str(self.repo), "--json", "README.md")
        data = json.loads(out.stdout)
        self.assertEqual((data["verdict"], data["tests"], data["chains"]), ("run-all", [], {}))
        self.assertTrue(data["reason"])

    def test_erros_git_e_argumentos(self) -> None:
        self.chain_repo()
        self.commit()
        out = cli("select", "--root", str(self.repo), "--diff", "naoexiste..HEAD")
        self.assertEqual(out.returncode, 1)
        self.assertTrue(out.stderr.startswith("impact falhou: "), out.stderr)
        with tempfile.TemporaryDirectory(prefix="impact-nogit-") as d:
            out = cli("select", "--root", d, "a.py")
            self.assertEqual(out.returncode, 1)
            self.assertTrue(out.stderr.startswith("impact falhou: "), out.stderr)
        self.assertEqual(cli("select", "--root", str(self.repo)).returncode, 2)
        self.assertEqual(cli("select", "--root", str(self.repo), "--diff", "HEAD", "a.py").returncode, 2)

    def test_impact_no_repo_starcode(self) -> None:
        res = impact.select(ROOT, changed=["scripts/gates/gates_common.py"])
        self.assertEqual(res["verdict"], "selected", res["reason"])
        self.assertTrue(any(len(c) >= 3 for c in res["chains"].values()))
        res = impact.select(ROOT, changed=["README.md"])
        self.assertEqual(res["verdict"], "run-all")
        self.assertIn("fora do grafo", res["reason"])


if __name__ == "__main__":
    unittest.main()
