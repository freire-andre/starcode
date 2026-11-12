"""Tests for scripts/ponte.py (F10 T1): read-only snapshot of a worktree's StarCode state."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from helpers import FIXTURES, ROOT, TempRepoCase

import ponte

FX = FIXTURES / "ponte"
SCRIPT = ROOT / "scripts" / "ponte.py"
CONTRACT_KEYS = {"schemaVersion", "worktree", "starcode", "crew", "gitMode", "feature", "workers", "errors", "elsewhere"}
BIG = 1024 * 1024 + 1


def iso(delta_minutes: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=delta_minutes)).replace(microsecond=0).isoformat()


def run_cli(path: Path | str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), "snapshot", "--path", str(path), "--json"],
                          capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL)


class PonteCase(TempRepoCase):
    def feature(self, slug: str, fixture: str, artifact: str = "tasks.md", mtime: float | None = None) -> Path:
        d = self.repo / ".specs" / "features" / slug
        d.mkdir(parents=True, exist_ok=True)
        f = d / artifact
        f.write_text((FX / fixture).read_text(encoding="utf-8"), encoding="utf-8")
        if mtime is not None:
            os.utime(f, (mtime, mtime))
        return f

    def live(self, name: str, text: str) -> None:
        d = self.repo / ".starcode" / "live"
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text, encoding="utf-8")

    def snap(self) -> dict:
        return ponte.snapshot(self.repo)


class SnapshotTests(PonteCase):
    def test_snapshot_keys(self) -> None:
        self.write_repo_config()
        res = run_cli(self.repo)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(set(data), CONTRACT_KEYS)
        self.assertEqual(data["schemaVersion"], 1)
        self.assertTrue(data["starcode"])
        self.assertEqual(data["worktree"], self.repo.resolve().as_posix())
        self.assertEqual(len(data["crew"]), 12)
        self.assertEqual(data["errors"], [])

    def test_snapshot_crew_ttl(self) -> None:
        self.write_repo_config()
        entries = {
            "a": {"member": "spock", "active": True, "source": "hook", "at": iso(10)},
            "b": {"member": "troi", "active": True, "source": "hook", "at": iso(20)},
            "c": {"member": "uhura", "active": True, "source": "cli", "at": iso(50)},
            "d": {"member": "worf", "active": True, "source": "cli", "at": iso(70)},
            "e": {"member": "kirk", "active": True, "source": "hook", "at": "2999-01-01T00:00:00+00:00"},
            "f": {"member": "q", "active": True, "source": "other", "at": iso(1)},
            "g": {"member": "spock", "active": True, "source": "hook", "at": iso(3)},
        }
        self.live("sessions.json", json.dumps(entries))
        crew = {c["member"]: c for c in self.snap()["crew"]}
        self.assertEqual([crew[m]["count"] for m in ("spock", "troi", "uhura", "worf", "kirk", "q")],
                         [1, 0, 1, 0, 0, 0])
        self.assertEqual(crew["spock"]["lastAt"], entries["g"]["at"])  # newest valid session
        self.assertIsNone(crew["troi"]["lastAt"])
        self.assertIsNone(crew["kirk"]["lastAt"])
        self.assertEqual(crew["spock"]["name"], "Spock")
        self.assertTrue(crew["spock"]["emoji"])
        self.assertRegex(crew["picard"]["cliModel"], r"^\S+ · \S")
        # D17: the user config wins over crew.yaml
        home = Path(os.environ["STARCODE_HOME"])
        home.mkdir(parents=True, exist_ok=True)
        (home / "config.json").write_text(
            (FIXTURES / "config" / "valid" / "user-full.json").read_text(encoding="utf-8"), encoding="utf-8")
        crew = {c["member"]: c for c in self.snap()["crew"]}
        self.assertEqual(crew["laforge"]["cliModel"], "claude · claude-opus-5-5")
        self.assertEqual(crew["q"]["cliModel"], "opencode · provider/model-x")

    def test_snapshot_git_mode(self) -> None:
        self.write_repo_config()
        self.assertIsNone(self.snap()["gitMode"])
        self.set_mode(3)
        gm = self.snap()["gitMode"]
        self.assertEqual(gm["mode"], 3)
        self.assertEqual(gm["label"], "branch + PR")
        self.assertRegex(gm["recordedAt"], r"^\d{4}-\d\d-\d\dT")

    def test_snapshot_feature_choice(self) -> None:
        self.write_repo_config()
        self.feature("velha", "spec-pronta.md", "spec.md", mtime=1_000_000)
        self.feature("nova", "tasks-ativa.md", "tasks.md", mtime=2_000_000)
        self.feature("feita", "spec-done.md", "spec.md", mtime=3_000_000)  # newest, but done
        feat = self.snap()["feature"]
        self.assertEqual(feat["slug"], "nova")
        self.assertFalse(feat["done"])
        # all done -> the newest one, with done: true
        self.feature("velha", "spec-done.md", "spec.md", mtime=1_000_000)
        (self.repo / ".specs" / "features" / "nova" / "tasks.md").unlink()
        self.feature("nova", "spec-done.md", "spec.md", mtime=2_000_000)
        feat = self.snap()["feature"]
        self.assertEqual(feat["slug"], "feita")
        self.assertTrue(feat["done"])
        self.assertEqual(feat["phase"], "done")

    def test_snapshot_feature_fields(self) -> None:
        self.write_repo_config()
        f = self.feature("fase-x", "tasks-ativa.md", "tasks.md")
        (f.parent / "spec.md").write_text("# spec\n", encoding="utf-8")
        feat = self.snap()["feature"]
        self.assertEqual(feat["slug"], "fase-x")
        self.assertEqual(feat["phase"], "execute")
        self.assertEqual(feat["size"], "GRANDE")
        self.assertEqual(feat["linear"], ["SC-17", "SC-102..SC-113", "SC-9"])
        self.assertEqual(feat["integrationBranch"], "feature/fase-x")
        self.assertEqual(feat["breaker"], "open")
        self.assertEqual(feat["files"]["tasks"], f.resolve().as_posix())
        self.assertEqual(feat["files"]["handoff"], f.resolve().as_posix())
        self.assertEqual(feat["files"]["spec"], (f.parent / "spec.md").resolve().as_posix())
        self.assertIsNone(feat["files"]["context"])
        self.assertEqual(set(feat["progress"]), {"done", "total", "percent"})
        self.assertEqual(feat["progress"]["total"], 1)  # counted from tasks.md without progress.json
        self.live("progress.json", json.dumps({"fase-x": {"done": 2, "total": 5, "percent": 40}}))
        self.assertEqual(self.snap()["feature"]["progress"], {"done": 2, "total": 5, "percent": 40})
        # Handoff in an earlier artifact: files.handoff is the file that holds it
        g = self.feature("fase-y", "spec-pronta.md", "spec.md", mtime=9_999_999_999)
        feat = self.snap()["feature"]
        self.assertEqual(feat["slug"], "fase-y")
        self.assertEqual(feat["files"]["handoff"], g.resolve().as_posix())
        self.assertIsNone(feat["size"])
        self.assertIsNone(feat["integrationBranch"])
        self.assertEqual(feat["breaker"], "closed")

    def test_snapshot_workers(self) -> None:
        self.write_repo_config()
        self.feature("fase-x", "tasks-ativa.md", "tasks.md")
        self.assertEqual(self.snap()["workers"], [
            {"label": "T1", "issues": ["SC-120", "SC-121"], "base": "abc1234", "dispatch": "ctx_aaa111",
             "model": "claude-sonnet-5-5"},
            {"label": "T2", "issues": ["SC-122"], "base": "def5678", "dispatch": "ctx_bbb222",
             "model": "claude-opus-5-5"},
        ])
        self.feature("fase-y", "spec-pronta.md", "spec.md", mtime=9_999_999_999)
        self.assertEqual(self.snap()["workers"], [])  # Dispatched: none

    def test_snapshot_sem_starcode(self) -> None:
        res = run_cli(self.repo)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertFalse(data["starcode"])
        self.assertEqual((data["crew"], data["workers"], data["errors"]), ([], [], []))
        self.assertIsNone(data["gitMode"])
        self.assertIsNone(data["feature"])

    def test_snapshot_fonte_invalida(self) -> None:
        self.write_repo_config()
        self.feature("fase-x", "tasks-ativa.md", "tasks.md")
        self.set_mode(2)
        self.live("sessions.json", "{not json")
        self.live("progress.json", " " * BIG)
        git_dir = Path(subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=self.repo, check=True,
                                      capture_output=True, text=True).stdout.strip())
        (git_dir / "starcode" / "session.json").write_text("[1]", encoding="utf-8")
        data = self.snap()
        sources = {e["source"]: e["message"] for e in data["errors"]}
        self.assertIn("JSON inválido", sources[".starcode/live/sessions.json"])
        self.assertIn("1 MiB", sources[".starcode/live/progress.json"])
        self.assertIn("JSON inválido", sources["<git-dir>/starcode/session.json"])
        for e in data["errors"]:
            self.assertEqual(set(e), {"source", "message"})
            self.assertNotIn("\n", e["message"])
            self.assertNotIn("Traceback", e["message"])
        self.assertIsNone(data["gitMode"])
        self.assertTrue(all(c["count"] == 0 for c in data["crew"]))
        self.assertEqual(data["feature"]["slug"], "fase-x")  # other sections survive
        # repo config that is not JSON, and a feature without any artifact: errors, still exit 0
        (self.repo / ".starcode" / "config.json").write_text("{", encoding="utf-8")
        (self.repo / ".specs" / "features" / "fase-x" / "tasks.md").write_text("x" * BIG, encoding="utf-8")
        res = run_cli(self.repo)
        self.assertEqual(res.returncode, 0, res.stderr)
        out = json.loads(res.stdout)
        self.assertIn(".starcode/config.json", {e["source"] for e in out["errors"]})
        self.assertIn(".specs/features/fase-x/tasks.md", {e["source"] for e in out["errors"]})
        (self.repo / ".specs" / "features" / "fase-x" / "tasks.md").unlink()
        self.assertEqual(run_cli(self.repo).returncode, 0)
        # unreadable source (a directory where the file should be) and a Handoff above 1 MiB
        sessions = self.repo / ".starcode" / "live" / "sessions.json"
        sessions.unlink()
        sessions.mkdir()
        self.feature("fase-x", "tasks-ativa.md", "tasks.md")
        big = self.repo / ".specs" / "features" / "fase-x" / "tasks.md"
        big.write_text("x" * BIG, encoding="utf-8")
        out = ponte.snapshot(self.repo)
        sources = {e["source"]: e["message"] for e in out["errors"]}
        self.assertIn("ilegível", sources[".starcode/live/sessions.json"])
        self.assertIn("1 MiB", sources[".specs/features/fase-x/tasks.md"])
        self.assertTrue(out["starcode"])
        self.assertEqual(run_cli(self.repo).returncode, 0)

    def test_snapshot_handoff_grande_vira_erro(self) -> None:
        self.write_repo_config()
        self.feature("fase-x", "tasks-ativa.md", "tasks.md", mtime=2_000_000)
        old = self.feature("fase-y", "tasks-ativa.md", "tasks.md", mtime=1_000_000)
        old.write_text(old.read_text(encoding="utf-8") + "x" * BIG, encoding="utf-8")
        os.utime(old, (1_000_000, 1_000_000))
        data = self.snap()
        self.assertEqual(data["feature"]["slug"], "fase-x")
        errors = [e for e in data["errors"] if e["source"] == ".specs/features/fase-y/tasks.md"]
        self.assertEqual(len(errors), 1)
        self.assertIn("1 MiB", errors[0]["message"])
        # the chosen feature's oversized Handoff is reported once, not twice
        big = self.repo / ".specs" / "features" / "fase-x" / "tasks.md"
        big.write_text(big.read_text(encoding="utf-8") + "x" * BIG, encoding="utf-8")
        errors = [e for e in self.snap()["errors"] if e["source"] == ".specs/features/fase-x/tasks.md"]
        self.assertEqual(len(errors), 1)

    def test_linear_ids_sem_duplicatas(self) -> None:
        self.assertEqual(ponte.linear_ids("SC-17; SC-17; SC-18"), ["SC-17", "SC-18"])
        self.assertEqual(ponte.linear_ids("SC-9, SC-17, SC-9"), ["SC-9", "SC-17"])

    def test_snapshot_worktree_invalido(self) -> None:
        missing = self.tmp / "nao-existe"
        res = run_cli(missing)
        self.assertEqual(res.returncode, 2)
        self.assertEqual(json.loads(res.stdout),
                         {"schemaVersion": 1, "error": f"worktree inválido: {missing}"})
        outside = self.tmp / "fora"
        outside.mkdir()
        res = run_cli(outside)
        self.assertEqual(res.returncode, 2)
        self.assertEqual(json.loads(res.stdout)["error"], f"worktree inválido: {outside}")

    def test_snapshot_somente_leitura(self) -> None:
        self.write_repo_config()
        self.feature("fase-x", "tasks-ativa.md", "tasks.md")
        self.set_mode(3)
        self.live("sessions.json", json.dumps({"a": {"member": "spock", "active": True, "source": "hook",
                                                      "at": iso(1)}}))
        # a linked worktree with no live folder of its own: nothing may be created there either
        linked = self.tmp / "linked"
        subprocess.run(["git", "worktree", "add", "-q", "-b", "b2", str(linked)], cwd=self.repo, check=True,
                       stdin=subprocess.DEVNULL)

        def tree(base: Path) -> dict[str, tuple[int, int]]:
            out = {}
            for p in base.rglob("*"):
                rel = p.relative_to(base).as_posix()
                if rel == ".git" or rel.startswith(".git/"):
                    continue
                st = p.stat()
                out[rel] = (st.st_mtime_ns, st.st_size)
            return out

        def state_files() -> dict[str, int]:
            return {p.as_posix(): p.stat().st_mtime_ns
                    for p in sorted((self.repo / ".git").rglob("starcode/*")) if p.is_file()}

        before = (tree(self.repo), tree(linked), state_files())
        for target in (self.repo, linked):
            self.assertEqual(run_cli(target).returncode, 0)
        self.assertEqual((tree(self.repo), tree(linked), state_files()), before)
        self.assertFalse((linked / ".starcode").exists())


class ElsewhereTests(PonteCase):
    def linked(self, name: str) -> Path:
        path = self.tmp / name
        subprocess.run(["git", "worktree", "add", "-q", "-b", name, str(path)], cwd=self.repo, check=True,
                       stdin=subprocess.DEVNULL)
        return path

    def feature_in(self, root: Path, slug: str, fixture: str, artifact: str, mtime: float) -> None:
        d = root / ".specs" / "features" / slug
        d.mkdir(parents=True, exist_ok=True)
        f = d / artifact
        f.write_text((FX / fixture).read_text(encoding="utf-8"), encoding="utf-8")
        os.utime(f, (mtime, mtime))

    def test_elsewhere_picks_newest_active_worktree(self) -> None:
        self.write_repo_config()
        self.feature("feita", "spec-done.md", "spec.md", mtime=1_000_000)
        a, b = self.linked("wt-a"), self.linked("wt-b")
        self.feature_in(a, "missao-a", "tasks-ativa.md", "tasks.md", 2_000_000)
        self.feature_in(b, "missao-b", "tasks-ativa.md", "tasks.md", 3_000_000)
        snap = self.snap()
        self.assertEqual(snap["feature"]["slug"], "feita")
        el = snap["elsewhere"]
        self.assertEqual(el["slug"], "missao-b")
        self.assertEqual(el["worktree"], b.resolve().as_posix())
        self.assertEqual(el["branch"], "wt-b")
        self.assertEqual(el["others"], 1)
        self.assertFalse(el["done"])
        self.assertIn("progress", el)
        # sem feature local também procura
        (self.repo / ".specs" / "features" / "feita" / "spec.md").unlink()
        self.assertEqual(self.snap()["elsewhere"]["slug"], "missao-b")
        # empate de mtime: sai o maior slug (lexicográfico), mesmo em outro worktree
        c = self.linked("wt-c")
        self.feature_in(c, "missao-z", "tasks-ativa.md", "tasks.md", 3_000_000)
        el = self.snap()["elsewhere"]
        self.assertEqual(el["slug"], "missao-z")
        self.assertEqual(el["others"], 2)
        # o menor slug perde também quando o worktree vem antes na listagem
        d = self.linked("wt-d")
        self.feature_in(d, "missao-0", "tasks-ativa.md", "tasks.md", 3_000_000)
        el = self.snap()["elsewhere"]
        self.assertEqual((el["slug"], el["others"]), ("missao-z", 3))

    def test_elsewhere_ignores_done_and_focus_worktree(self) -> None:
        self.write_repo_config()
        self.feature("feita", "spec-done.md", "spec.md", mtime=1_000_000)
        a = self.linked("wt-a")
        self.feature_in(a, "velha", "spec-done.md", "spec.md", 2_000_000)
        self.assertIsNone(self.snap()["elsewhere"])
        # focus on the linked worktree (done): the main checkout is the "other" one
        self.feature("ativa", "tasks-ativa.md", "tasks.md", mtime=3_000_000)
        (self.repo / ".specs" / "features" / "feita" / "spec.md").unlink()
        el = ponte.snapshot(a)["elsewhere"]
        self.assertEqual(el["slug"], "ativa")
        self.assertEqual(el["worktree"], self.repo.resolve().as_posix())
        self.assertEqual(el["branch"], "main")

    def test_elsewhere_null_when_local_active(self) -> None:
        self.write_repo_config()
        self.feature("ativa", "tasks-ativa.md", "tasks.md", mtime=1_000_000)
        a = self.linked("wt-a")
        self.feature_in(a, "outra", "tasks-ativa.md", "tasks.md", 2_000_000)
        from unittest import mock

        with mock.patch.object(ponte, "list_worktrees", side_effect=AssertionError("git chamado")):
            snap = self.snap()
        self.assertIsNone(snap["elsewhere"])
        self.assertEqual(snap["feature"]["slug"], "ativa")

    def test_elsewhere_worktree_errors_do_not_break_snapshot(self) -> None:
        from unittest import mock

        self.write_repo_config()
        self.feature("feita", "spec-done.md", "spec.md", mtime=1_000_000)
        with mock.patch.object(ponte, "list_worktrees", side_effect=OSError("boom")):
            snap = self.snap()
        self.assertIsNone(snap["elsewhere"])
        self.assertEqual(snap["feature"]["slug"], "feita")
        self.assertIn("worktrees", [e["source"] for e in snap["errors"]])
        # worktree listado e removido do disco
        a = self.linked("wt-a")
        self.feature_in(a, "missao-a", "tasks-ativa.md", "tasks.md", 2_000_000)
        import shutil

        shutil.rmtree(a)
        snap = self.snap()
        self.assertIsNone(snap["elsewhere"])
        self.assertEqual(snap["feature"]["slug"], "feita")
        self.assertIn("worktrees", [e["source"] for e in snap["errors"]])
        self.assertEqual(run_cli(self.repo).returncode, 0)

    def test_elsewhere_erros_do_outro_worktree_usam_fonte_worktrees(self) -> None:
        self.write_repo_config()
        self.feature("feita", "spec-done.md", "spec.md", mtime=1_000_000)
        a = self.linked("wt-a")
        self.feature_in(a, "missao-a", "tasks-ativa.md", "tasks.md", 2_000_000)
        grande = a / ".specs" / "features" / "missao-a" / "spec.md"
        grande.write_text("x" * (ponte.MAX_BYTES + 1), encoding="utf-8")
        snap = self.snap()
        self.assertEqual(snap["elsewhere"]["slug"], "missao-a")
        erros = snap["errors"]
        self.assertTrue(erros)
        self.assertEqual({e["source"] for e in erros}, {"worktrees"})
        for e in erros:
            self.assertTrue(e["message"].startswith(a.resolve().as_posix() + ": "), e["message"])
        self.assertTrue(any("1 MiB" in e["message"] for e in erros))

    def test_elsewhere_snapshot_is_read_only(self) -> None:
        self.write_repo_config()
        self.feature("feita", "spec-done.md", "spec.md", mtime=1_000_000)
        a = self.linked("wt-a")
        self.feature_in(a, "missao-a", "tasks-ativa.md", "tasks.md", 2_000_000)

        def tree(base: Path) -> dict[str, object]:
            # lista de arquivos (chaves) + conteúdo em bytes (None para pastas) + mtime
            out: dict[str, object] = {}
            for p in base.rglob("*"):
                rel = p.relative_to(base).as_posix()
                if rel == ".git" or rel.startswith(".git/"):
                    continue
                out[rel] = (p.stat().st_mtime_ns, p.read_bytes() if p.is_file() else None)
            return out

        before = (tree(self.repo), tree(a))
        self.assertIn(".specs/features/missao-a/tasks.md", before[1])
        res = run_cli(self.repo)
        self.assertEqual(res.returncode, 0, res.stderr)
        data = json.loads(res.stdout)
        self.assertEqual(data["schemaVersion"], 1)
        self.assertEqual(data["elsewhere"]["slug"], "missao-a")
        self.assertEqual((tree(self.repo), tree(a)), before)

    def test_same_path_ignores_case_and_slashes(self) -> None:
        self.assertTrue(ponte.same_path("F:" + chr(92) + "x" + chr(92) + "Y", "f:/x/y"))
        self.assertFalse(ponte.same_path("F:/x", "F:/z"))

    def test_same_path_preserva_raiz_do_drive(self) -> None:
        bs = chr(92)
        self.assertFalse(ponte.same_path("C:/", "c:"))
        self.assertTrue(ponte.same_path("C:" + bs + "x" + bs, "c:/x"))
        self.assertTrue(ponte.same_path("C:/", "c:" + bs))


class DecisionsTests(unittest.TestCase):
    def test_decisions_records_p151_2_elsewhere(self) -> None:
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("### P151-2:", text)
        section = text.split("### P151-2:", 1)[1]
        for needle in ("elsewhere", "git worktree list --porcelain", "mtime", "workspace.open"):
            self.assertIn(needle, section)
