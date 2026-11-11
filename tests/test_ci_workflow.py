"""Estrutura de .github/workflows/ci.yml (R1-R10, R14). Sem PyYAML: usa tools/miniyaml.py."""
from __future__ import annotations

import unittest

from helpers import ROOT  # noqa: F401  (sets sys.path)

import miniyaml

CI = ROOT / ".github" / "workflows" / "ci.yml"
PIN = "npm install -g @anthropic-ai/claude-code@2.1.319"


def _text() -> str:
    return CI.read_text(encoding="utf-8")


def _doc() -> dict:
    return miniyaml.loads(_text())


def _jobs() -> dict:
    return _doc()["jobs"]


def _steps(job: str) -> list:
    return _jobs()[job]["steps"]


def _runs(job: str) -> list[str]:
    return [str(s.get("run", "")) for s in _steps(job)]


def _job_texts() -> dict[str, str]:
    """Texto bruto de cada job (blocos de 2 espaços sob `jobs:`)."""
    out: dict[str, list[str]] = {}
    cur = None
    in_jobs = False
    for line in _text().splitlines():
        if line.startswith("jobs:"):
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if line.startswith("  ") and not line.startswith("   ") and line.strip().endswith(":"):
            cur = line.strip()[:-1]
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return {k: "\n".join(v) for k, v in out.items()}


class CiWorkflowTests(unittest.TestCase):
    def test_ci_triggers(self):
        doc = _doc()
        on = doc.get("on", doc.get(True))
        self.assertIsNotNone(on, "chave on: ausente")
        self.assertEqual(on["pull_request"]["branches"], ["main"])
        self.assertEqual(on["push"]["branches"], ["main"])
        self.assertEqual(on["push"]["tags"], ["v*"])
        self.assertIn("workflow_dispatch", on)

    def test_ci_checks_steps_and_commands(self):
        expected = {
            "build --check": "python tools/build.py --check",
            "unittest": "python -m unittest discover -s tests -v",
            "check_decisions": "python scripts/check_decisions.py",
            "plugin validate": "claude plugin validate dist/claude --strict",
        }
        got = {s.get("name"): s.get("run") for s in _steps("checks")}
        for name, cmd in expected.items():
            self.assertEqual(got.get(name), cmd, name)

    def test_ci_matrix_ubuntu_windows_python_312(self):
        job = _jobs()["checks"]
        self.assertEqual(job["strategy"]["matrix"]["os"], ["ubuntu-latest", "windows-latest"])
        self.assertEqual(job["runs-on"], "${{ matrix.os }}")
        setups = [s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/setup-python")]
        self.assertEqual(len(setups), 1)
        self.assertEqual(str(setups[0]["with"]["python-version"]), "3.12")
        self.assertTrue(any(str(s.get("uses", "")).startswith("actions/setup-node") for s in job["steps"]))

    def test_ci_plugin_validate_with_pinned_claude_code(self):
        runs = _runs("checks")
        self.assertIn(PIN, runs)
        self.assertLess(runs.index(PIN), runs.index("claude plugin validate dist/claude --strict"))

    def test_ci_has_no_continue_on_error(self):
        self.assertNotIn("continue-on-error", _text())

    def test_ci_concurrency_cancels_in_progress(self):
        c = _doc()["concurrency"]
        self.assertEqual(c["group"], "ci-${{ github.ref }}")
        self.assertIs(c["cancel-in-progress"], True)

    def test_ci_eval_job_only_on_dispatch(self):
        job = _jobs()["eval"]
        cond = str(job["if"])
        self.assertEqual(cond, "github.event_name == 'workflow_dispatch'")
        self.assertNotIn("refs/tags", cond)
        joined = "\n".join(_runs("eval"))
        for tag in ("risk-sizing", "routing"):
            self.assertIn(
                f"claude plugin eval dist/claude --tag {tag} --ablation none --trust-plugin --no-publish",
                joined,
            )

    def test_ci_secret_only_in_eval_job(self):
        texts = _job_texts()
        self.assertEqual(set(texts), {"checks", "eval", "release-check"})
        self.assertEqual(_jobs()["eval"]["env"]["ANTHROPIC_API_KEY"], "${{ secrets.ANTHROPIC_API_KEY }}")
        for name, body in texts.items():
            if name != "eval":
                self.assertNotIn("ANTHROPIC_API_KEY", body, name)
                self.assertNotIn("secrets.", body, name)
        head = _text().split("jobs:")[0]
        self.assertNotIn("ANTHROPIC_API_KEY", head)
        self.assertNotIn("secrets.", head)

    def test_ci_eval_fails_without_secret(self):
        run = str(_steps("eval")[0].get("run"))
        self.assertEqual(run, 'test -n "$ANTHROPIC_API_KEY" || { echo "ANTHROPIC_API_KEY ausente: configure o secret do repositório"; exit 1; }')

    def test_ci_eval_uploads_results_and_summary(self):
        steps = _steps("eval")
        ups = [s for s in steps if str(s.get("uses", "")).startswith("actions/upload-artifact")]
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0]["with"]["path"], "dist/claude/evals/results/")
        self.assertEqual(ups[0]["if"], "always()")
        self.assertGreaterEqual(_job_texts()["eval"].count("$GITHUB_STEP_SUMMARY"), 2)

    def test_ci_release_check_runs_release_py(self):
        job = _jobs()["release-check"]
        self.assertIn("refs/tags/v", str(job["if"]))
        self.assertIn('python tools/release.py check --tag "${{ github.ref_name }}"', _runs("release-check"))

    def test_ci_valida_plugin_orca_condicional(self):
        step = next((s for s in _steps("checks") if "orca plugin validate" in str(s.get("run", ""))), None)
        self.assertIsNotNone(step, "passo orca plugin validate ausente")
        run = str(step["run"])
        self.assertIn("orca plugin validate src/orca --json", run)
        self.assertIn("command -v orca", run)
        self.assertIn("orca ausente: validação do plugin pulada", run)
        self.assertEqual(step.get("shell"), "bash")
        self.assertNotIn("continue-on-error", str(step))


if __name__ == "__main__":
    unittest.main()
