"""Tests for scripts/ephemeral_db.py (R20-R25). Uses a fake `docker`, never the real one."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from helpers import ROOT

SCRIPT = ROOT / "scripts" / "ephemeral_db.py"

FAKE_DOCKER = r'''
import json, os, sys
d = os.environ["FAKE_DOCKER_DIR"]
args = sys.argv[1:]
with open(os.path.join(d, "calls.jsonl"), "a", encoding="utf-8") as fh:
    fh.write(json.dumps(args) + "\n")
state_file = os.path.join(d, "state.json")
state = json.load(open(state_file)) if os.path.exists(state_file) else {"containers": {}, "runs": 0}
mode = os.environ.get("FAKE_DOCKER_MODE", "")
cmd = args[0] if args else ""
if cmd == "info":
    if mode == "info_fail":
        sys.stderr.write("Cannot connect to the Docker daemon at npipe\n")
        sys.exit(1)
    sys.exit(0)
if cmd == "run":
    name = args[args.index("--name") + 1]
    port = int(args[args.index("-p") + 1].split(":")[1])
    state["runs"] += 1
    busy = state["runs"] <= int(os.environ.get("FAKE_DOCKER_BUSY_RUNS", "0"))
    if busy or port in [c["port"] for c in state["containers"].values()]:
        json.dump(state, open(state_file, "w"))
        sys.stderr.write("Bind for 127.0.0.1:%d failed: port is already allocated\n" % port)
        sys.exit(125)
    state["containers"][name] = {"port": port}
    json.dump(state, open(state_file, "w"))
    print("fakeid")
    sys.exit(0)
if cmd == "exec":
    sys.exit(1 if mode == "not_ready" else 0)
if cmd == "rm":
    state["containers"].pop(args[-1], None)
    json.dump(state, open(state_file, "w"))
    sys.exit(0)
if cmd == "ps":
    p = os.path.join(d, "ps.txt")
    if os.path.exists(p):
        sys.stdout.write(open(p, encoding="utf-8").read())
    sys.exit(0)
sys.exit(0)
'''

DUMP_ENV = "import os,sys; open(sys.argv[1],'w').write(os.environ.get('DATABASE_URL','<none>')); sys.exit(int(sys.argv[2]))"


class EphemeralDbTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-eph-test-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        self.state = self.tmp / "state"
        self.state.mkdir()
        (self.bin / "docker_fake.py").write_text(FAKE_DOCKER, encoding="utf-8")
        if os.name == "nt":
            (self.bin / "docker.cmd").write_text(
                f'@echo off\r\n"{sys.executable}" "{self.bin / "docker_fake.py"}" %*\r\n', encoding="utf-8")
        else:
            sh = self.bin / "docker"
            sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{self.bin / "docker_fake.py"}" "$@"\n', encoding="utf-8")
            sh.chmod(0o755)
        self.cwd = self.tmp / "proj"
        (self.cwd / ".starcode").mkdir(parents=True)
        (self.cwd / ".starcode" / "stack.json").write_text(
            json.dumps({"image": {"postgresql": "postgres:17", "mysql": "mysql:9"}}), encoding="utf-8")

    def env(self, **extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        env["PATH"] = str(self.bin) + os.pathsep + env.get("PATH", "")
        env["FAKE_DOCKER_DIR"] = str(self.state)
        env["STARCODE_EPH_POLL_SECONDS"] = "0.05"
        env["PYTHONIOENCODING"] = "utf-8"
        env.update(extra)
        return env

    def eph(self, *args: str, **extra: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.cwd, env=self.env(**extra),
                              capture_output=True, text=True, encoding="utf-8", timeout=60,
                              stdin=subprocess.DEVNULL)

    def calls(self) -> list[list[str]]:
        p = self.state / "calls.jsonl"
        return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []

    def test_ephemeral_run_lifecycle_with_fake_docker(self) -> None:
        out = self.tmp / "url.txt"
        for code in (0, 7):
            r = self.eph("run", "postgresql", "--", sys.executable, "-c", DUMP_ENV, str(out), str(code))
            self.assertEqual(r.returncode, code, r.stderr)
            url = out.read_text(encoding="utf-8")
            self.assertRegex(url, r"^postgresql\+psycopg://eph_[0-9a-f]{8}:[0-9a-f]{24}@127\.0\.0\.1:\d+/eph_[0-9a-f]{8}$")
        runs = [c for c in self.calls() if c[0] == "run"]
        self.assertEqual(len(runs), 2)
        run = runs[0]
        self.assertRegex(run[run.index("--name") + 1], r"^starcode-eph-postgresql-[0-9a-f]{8}$")
        self.assertRegex(run[run.index("-p") + 1], r"^127\.0\.0\.1:\d+:5432$")
        self.assertEqual(run[-1], "postgres:17")
        self.assertTrue(any(c[0] == "exec" and "pg_isready" in c for c in self.calls()))
        rms = [c for c in self.calls() if c[0] == "rm"]
        self.assertEqual(len(rms), 2)  # removido também quando o comando falha
        self.assertEqual(rms[0][:3], ["rm", "-f", "-v"])
        # mysql + --image
        r = self.eph("run", "mysql", "--image", "mysql:8", "--", sys.executable, "-c", DUMP_ENV, str(out), "0")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(out.read_text(encoding="utf-8").startswith("mysql+pymysql://"))
        mysql_run = [c for c in self.calls() if c[0] == "run"][-1]
        self.assertEqual(mysql_run[-1], "mysql:8")
        self.assertTrue(any(c[0] == "exec" and "mysqladmin" in c for c in self.calls()))

    def test_ephemeral_docker_unavailable_exit_3(self) -> None:
        out = self.tmp / "url.txt"
        r = self.eph("run", "postgresql", "--", sys.executable, "-c", DUMP_ENV, str(out), "0",
                     FAKE_DOCKER_MODE="info_fail")
        self.assertEqual(r.returncode, 3)
        self.assertIn("gate de integração não executado: Docker indisponível (", r.stderr)
        self.assertFalse(out.exists())
        # docker ausente do PATH
        env = self.env()
        env["PATH"] = str(self.tmp / "vazio")
        r = subprocess.run([sys.executable, str(SCRIPT), "run", "postgresql", "--", sys.executable, "-c", "pass"],
                           cwd=self.cwd, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(r.returncode, 3)
        self.assertIn("Docker indisponível", r.stderr)

    def test_ephemeral_not_ready_exit_4(self) -> None:
        out = self.tmp / "url.txt"
        r = self.eph("run", "postgresql", "--", sys.executable, "-c", DUMP_ENV, str(out), "0",
                     FAKE_DOCKER_MODE="not_ready", STARCODE_EPH_READY_SECONDS="0.5")
        self.assertEqual(r.returncode, 4)
        self.assertIn("banco efêmero não ficou pronto em 60 s", r.stderr)
        self.assertFalse(out.exists())
        self.assertEqual(len([c for c in self.calls() if c[0] == "rm"]), 1)
        # porta ocupada em todas as tentativas: 3 runs e exit 4
        (self.state / "calls.jsonl").unlink()
        r = self.eph("run", "postgresql", "--", sys.executable, "-c", "pass", FAKE_DOCKER_BUSY_RUNS="9")
        self.assertEqual(r.returncode, 4)
        self.assertEqual(len([c for c in self.calls() if c[0] == "run"]), 3)

    def test_ephemeral_reuse_env_rejects_remote_url(self) -> None:
        out = self.tmp / "url.txt"
        cmd = (sys.executable, "-c", DUMP_ENV, str(out), "0")
        remote = "postgresql://u:p@db.example.com:5432/prod"
        r = self.eph("run", "postgresql", "--reuse-env", "--", *cmd, DATABASE_URL=remote)
        self.assertEqual(r.returncode, 2)
        self.assertFalse(out.exists())
        self.assertEqual(self.calls(), [])
        # sem --reuse-env, a variável do ambiente é substituída
        r = self.eph("run", "postgresql", "--", *cmd, DATABASE_URL=remote)
        self.assertEqual(r.returncode, 0, r.stderr)
        url = out.read_text(encoding="utf-8")
        self.assertNotIn("example.com", url)
        self.assertIn("@127.0.0.1:", url)
        # --reuse-env com URL local é aceita
        local = "postgresql://u:p@localhost:5432/dev"
        r = self.eph("run", "postgresql", "--reuse-env", "--", *cmd, DATABASE_URL=local)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(out.read_text(encoding="utf-8"), local)

    def test_ephemeral_list_and_down(self) -> None:
        (self.state / "ps.txt").write_text(
            "starcode-eph-postgresql-aaaa1111 2020-01-01 10:00:00 +0000 UTC\n"
            "starcode-eph-mysql-bbbb2222 2020-01-01 10:00:00 +0000 UTC\n"
            "outro-starcode-eph-x 2020-01-01 10:00:00 +0000 UTC\n", encoding="utf-8")
        r = self.eph("list", "--json")
        self.assertEqual(r.returncode, 0, r.stderr)
        items = json.loads(r.stdout)
        self.assertEqual([i["name"] for i in items], ["starcode-eph-postgresql-aaaa1111", "starcode-eph-mysql-bbbb2222"])
        self.assertTrue(all(i["age_minutes"] > 60 for i in items))
        r = self.eph("list")
        self.assertIn("starcode-eph-mysql-bbbb2222", r.stdout)
        self.assertIn("min", r.stdout)
        r = self.eph("down", "starcode-eph-mysql-bbbb2222")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(["rm", "-f", "-v", "starcode-eph-mysql-bbbb2222"], self.calls())
        before = len(self.calls())
        r = self.eph("down", "meu-postgres-de-producao")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(len(self.calls()), before)  # nada foi removido

    def test_ephemeral_unique_names_and_ports(self) -> None:
        go = self.tmp / "go"
        wait_cmd = (sys.executable, "-c",
                    "import os,sys,time\nt=time.time()\n"
                    "while not os.path.exists(sys.argv[1]) and time.time()-t<30: time.sleep(0.05)\n"
                    "sys.exit(0 if os.path.exists(sys.argv[1]) else 9)", str(go))
        first = subprocess.Popen([sys.executable, str(SCRIPT), "run", "postgresql", "--", *wait_cmd],
                                 cwd=self.cwd, env=self.env(), stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        try:
            deadline = time.time() + 30
            while not any(c[0] == "exec" for c in self.calls()) and time.time() < deadline:
                time.sleep(0.05)
            second = self.eph("run", "postgresql", "--", sys.executable, "-c",
                              f"open(r'{go}','w').write('x')")
            self.assertEqual(second.returncode, 0, second.stderr)
            out, err = first.communicate(timeout=30)
            self.assertEqual(first.returncode, 0, err)
        finally:
            if first.poll() is None:
                first.kill()
        runs = [c for c in self.calls() if c[0] == "run"]
        names = [c[c.index("--name") + 1] for c in runs]
        ports = [c[c.index("-p") + 1].split(":")[1] for c in runs]
        self.assertGreaterEqual(len(runs), 2)
        self.assertEqual(len(set(names)), len(names))
        # a porta de um container vivo nunca é reaproveitada: as duas execuções simultâneas diferem
        self.assertNotEqual(ports[0], ports[-1])


if __name__ == "__main__":
    unittest.main()
