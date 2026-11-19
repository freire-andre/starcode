"""Tests for SC-202: lock + atomic write of the session/progress files under concurrent writers."""
from __future__ import annotations

import contextlib
import io
import json
import multiprocessing
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from helpers import ROOT, TempRepoCase
import crew_live
import git_mode
import starcode_common as sc

HOOK = ROOT / "hooks" / "scripts" / "crew_hook.py"
PROCS, PER_PROC = 16, 4  # 64 writes in total

HOLDER = """
import sys
sys.path.insert(0, sys.argv[2])
import starcode_common as sc
with sc.locked(sys.argv[1], 10):
    print("ready", flush=True)
    sys.stdin.readline()
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _w_sessions(d: str, names: list[str], mine: list[str]) -> None:
    for name in mine:
        def mutate(sessions: dict, name=name) -> None:
            sessions[name] = {"member": name, "active": True, "source": "cli", "at": _now()}
        crew_live.update_sessions(Path(d), names, mutate)


def _w_progress(d: str, mine: list[str]) -> None:
    for slug in mine:
        crew_live.set_progress(Path(d), slug, 1, 2, "execute")


def _w_session(cwd: str, mine: list[str]) -> None:
    for key in mine:
        sc.update_session(cwd, lambda data, key=key: data.__setitem__(key, 1))


def _run_parallel(target, make_args) -> list[int]:
    ctx = multiprocessing.get_context("spawn")
    procs = [ctx.Process(target=target, args=make_args([f"k{p}-{i}" for i in range(PER_PROC)])) for p in range(PROCS)]
    for p in procs:
        p.start()
    for p in procs:
        p.join(120)
    return [p.exitcode for p in procs]


class SessionsConcorrenteTests(TempRepoCase):
    def live(self) -> Path:
        d = crew_live.live_dir(self.repo)
        assert d is not None
        return d

    @contextlib.contextmanager
    def held(self, path: Path):
        proc = subprocess.Popen([sys.executable, "-c", HOLDER, str(path), str(ROOT / "scripts")],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(proc.stdout.readline().strip(), "ready")
            yield
        finally:
            proc.stdin.write("\n")
            proc.stdin.flush()
            proc.wait(10)
            proc.stdin.close()
            proc.stdout.close()

    def cli(self, main, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(sc, "LOCK_TIMEOUT", 0.3):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    # R1 ------------------------------------------------------------------------------------

    def test_locked_e_escrita_atomica(self):
        target = self.tmp / "estado.json"
        # positive: free lock is taken and released on exit (and on error)
        with sc.locked(target, 1):
            pass
        with self.assertRaises(RuntimeError), sc.locked(target, 1):
            raise RuntimeError("x")
        with sc.locked(target, 1):
            pass
        # negative: another process holds it -> TimeoutError after ~timeout, then free again after release
        with self.held(target):
            t0 = time.monotonic()
            with self.assertRaises(TimeoutError) as ctx, sc.locked(target, 0.3):
                self.fail("não devia obter a trava")
            self.assertEqual(str(ctx.exception), str(target))
            self.assertGreaterEqual(time.monotonic() - t0, 0.25)
        with sc.locked(target, 2):
            pass
        self.assertTrue((self.tmp / "estado.json.lock").exists())
        # atomic write: unique temp per call, none left behind
        names: list[str] = []
        real = sc.tempfile.mkstemp

        def spy(*a, **k):
            fd, name = real(*a, **k)
            names.append(name)
            return fd, name

        with mock.patch.object(sc.tempfile, "mkstemp", spy):
            sc.write_json_atomic(target, {"a": 1})
            sc.write_json_atomic(target, {"a": 2})
        self.assertEqual(len(set(names)), 2)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 2})
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name != "repo"),
                         ["estado.json", "estado.json.lock"])
        # failure: nothing left and the old content is intact
        before = target.read_bytes()
        with self.assertRaises(TypeError):
            sc.write_json_atomic(target, {"a": object()})
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name != "repo"),
                         ["estado.json", "estado.json.lock"])
        # replace retried on PermissionError
        calls = []
        real_replace = os.replace

        def flaky(a, b):
            calls.append(1)
            if len(calls) < 3:
                raise PermissionError("busy")
            real_replace(a, b)

        with mock.patch.object(sc.os, "replace", flaky), mock.patch.object(sc.time, "sleep"):
            sc.write_json_atomic(target, {"a": 3})
        self.assertEqual(len(calls), 3)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 3})
        # up to 5 new attempts: success on the 6th call writes the new content
        calls.clear()

        def busy_until(n):
            def fake(a, b):
                calls.append(1)
                if len(calls) < n:
                    raise PermissionError("busy")
                real_replace(a, b)
            return fake

        with mock.patch.object(sc.os, "replace", busy_until(6)), mock.patch.object(sc.time, "sleep"):
            sc.write_json_atomic(target, {"a": 4})
        self.assertEqual(len(calls), 6)
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"a": 4})
        # failure on the 6th call raises, old bytes intact, no temp left
        calls.clear()
        before = target.read_bytes()
        with mock.patch.object(sc.os, "replace", busy_until(7)), mock.patch.object(sc.time, "sleep"),                 self.assertRaises(PermissionError):
            sc.write_json_atomic(target, {"a": 5})
        self.assertEqual(len(calls), 6)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir() if p.name != "repo"),
                         ["estado.json", "estado.json.lock"])

    # R2 / R3 / R4 --------------------------------------------------------------------------

    def test_update_sessions_paralelo(self):
        d = self.live()
        names = [f"k{p}-{i}" for p in range(PROCS) for i in range(PER_PROC)]
        codes = _run_parallel(_w_sessions, lambda mine: (str(d), names, mine))
        self.assertEqual(codes, [0] * PROCS)
        sessions = json.loads((d / "sessions.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(sessions), sorted(names))
        self.assertEqual(len(sessions), 64)
        crew = json.loads((d / "crew.json").read_text(encoding="utf-8"))
        self.assertEqual(crew, {n: 1 for n in names})
        self.assertEqual(sum(crew.values()), 64)

    def test_set_progress_paralelo(self):
        d = self.live()
        codes = _run_parallel(_w_progress, lambda mine: (str(d), mine))
        self.assertEqual(codes, [0] * PROCS)
        data = json.loads((d / "progress.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(data), sorted(f"k{p}-{i}" for p in range(PROCS) for i in range(PER_PROC)))
        self.assertEqual(len(data), 64)

    def test_update_session_paralelo(self):
        gd = sc.git_dir(self.repo)
        expected = sorted(f"k{p}-{i}" for p in range(PROCS) for i in range(PER_PROC))
        codes = _run_parallel(_w_session, lambda mine: (str(self.repo), mine))
        self.assertEqual(codes, [0] * PROCS)
        self.assertEqual(sorted(sc.read_session(self.repo)), expected)
        self.assertEqual(list(gd.rglob("session.tmp")), [])
        self.assertEqual([p.name for p in (gd / "starcode").iterdir() if p.suffix == ".tmp"], [])
        # write_session keeps its signature and never writes a fixed-name temp
        path = sc.write_session(self.repo, {"gitMode": 2})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"gitMode": 2})
        self.assertEqual(list(gd.rglob("session.tmp")), [])
        # write_session replaces the whole file with exactly `data`
        sc.update_session(self.repo, lambda data: data.update({"extra": 1}))
        sc.write_session(self.repo, {"only": 2})
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"only": 2})
        self.assertEqual(list(gd.rglob("session.tmp")), [])
        # production code under scripts/ and hooks/ never calls write_session outside starcode_common.py
        callers = [str(p.relative_to(ROOT)) for folder in ("scripts", "hooks") for p in (ROOT / folder).rglob("*.py")
                   if p.name != "starcode_common.py" and "write_session(" in p.read_text(encoding="utf-8")]
        self.assertEqual(callers, [])
        # git_mode.py writes through update_session, never through a bare write
        src = (ROOT / "scripts" / "git_mode.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("sc.update_session("), 3)
        self.assertNotIn("write_session", src)

    # R5 ------------------------------------------------------------------------------------

    def test_trava_esgotada(self):
        d = self.live()
        spath = d / "sessions.json"
        ppath = d / "progress.json"
        gpath = sc.session_path(self.repo)
        # hook: silent, exit 0, nothing written (bytes and file list)
        before = sorted(p.name for p in d.iterdir())  # the .lock neighbour is the only allowed newcomer
        with self.held(spath):
            res = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True, encoding="utf-8",
                                 input=json.dumps({"hook_event_name": "PreToolUse", "session_id": "s1",
                                                   "cwd": str(self.repo), "tool_name": "Skill",
                                                   "tool_input": {"skill": "starcode:spock", "args": ""}}))
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertEqual(sorted(p.name for p in d.iterdir() if not p.name.endswith(".lock")), before)
        self.assertFalse(spath.exists())
        self.assertFalse((d / "crew.json").exists())
        # crew_live set/start/stop/progress: exit 2 and the exact message
        for args in (("set", "spock", "1"), ("start", "spock"), ("stop", "spock")):
            with self.held(spath):
                code, out, err = self.cli(crew_live.main, "--cwd", str(self.repo), *args)
            self.assertEqual((code, out, err), (2, "", f"trava ocupada: {spath} (tente de novo)\n"), args)
        with self.held(ppath):
            code, out, err = self.cli(crew_live.main, "--cwd", str(self.repo), "progress", "feat-x",
                                      "--done", "1", "--total", "2")
        self.assertEqual((code, out, err), (2, "", f"trava ocupada: {ppath} (tente de novo)\n"))
        self.assertFalse(spath.exists())
        self.assertFalse(ppath.exists())
        # git_mode set: exit 2 and the exact message; the file is untouched
        sc.write_session(self.repo, {"gitMode": 1})
        raw = gpath.read_bytes()
        with self.held(gpath):
            code, out, err = self.cli(git_mode.main, "--cwd", str(self.repo), "set", "3")
        self.assertEqual((code, out, err), (2, "", f"trava ocupada: {gpath} (tente de novo)\n"))
        self.assertEqual(gpath.read_bytes(), raw)
        for args in (("authorize-merge", "feature/x"), ("revoke-merge",)):
            raw = gpath.read_bytes()
            with self.held(gpath):
                code, out, err = self.cli(git_mode.main, "--cwd", str(self.repo), *args)
            self.assertEqual((code, out, err), (2, "", f"trava ocupada: {gpath} (tente de novo)\n"), args)
            self.assertEqual(gpath.read_bytes(), raw, args)
        # positive: with the lock free the same commands work
        code, out, err = self.cli(git_mode.main, "--cwd", str(self.repo), "set", "3")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(sc.git_mode(self.repo), 3)
        code, _, err = self.cli(crew_live.main, "--cwd", str(self.repo), "set", "spock", "1")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads((d / "crew.json").read_text(encoding="utf-8"))["spock"], 1)

    # R6 ------------------------------------------------------------------------------------

    def test_decisions_sessions_concorrente(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        parts = text.split("\n### ")
        entry = next((p for p in parts if p.startswith("SC-") and "concorrente" in p.splitlines()[0].lower()), None)
        self.assertIsNotNone(entry, "falta a entrada ### SC-<n> de sessions-concorrente")
        for field in ("**Problema**", "**Decisão**", "**Motivo**", "**Por que não é bug**"):
            self.assertEqual(entry.count(field), 1, field)
        problema = entry.split("**Problema**")[1].split("**Decisão**")[0]
        self.assertIn("64", problema)
        self.assertIn("16 processos", problema)
        for phrase in ("`sessions.json` terminou com 9, 11 e 13 das 64 entradas",
                       "`write_session` teve 10, 6 e 11 das 64 escritas falhando com `PermissionError`"):
            self.assertIn(phrase, problema, phrase)
        decisao = entry.split("**Decisão**")[1].split("**Motivo**")[0]
        for term in ("`locked(path, timeout=5.0)`", "`write_json_atomic(path, data)`", "`update_session(cwd, mutate)`", "5 s", "hook", "silencios",
                     "saída 2", "trava ocupada: <arquivo> (tente de novo)"):
            self.assertIn(term, decisao, term)
        nao_bug = entry.split("**Por que não é bug**")[1]
        for name in ("test_locked_e_escrita_atomica", "test_update_sessions_paralelo", "test_set_progress_paralelo",
                     "test_update_session_paralelo", "test_trava_esgotada"):
            self.assertIn(name, nao_bug, name)
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = changelog.split("## [Unreleased]")[1].split("\n## [")[0]
        self.assertTrue(any("`locked`" in ln and "SC-202" in ln for ln in unreleased.splitlines()))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    import unittest
    unittest.main()
