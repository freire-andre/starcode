#!/usr/bin/env python3
"""Banco efêmero local em Docker para o gate de integração (R20-R25).

Só stdlib e autossuficiente: o arquivo é copiado para os projetos gerados.

  ephemeral_db.py run <postgresql|mysql> [--image IMG] [--reuse-env] -- <comando...>
  ephemeral_db.py list [--json]
  ephemeral_db.py down <nome>

Exit: o do comando (run) | 2 uso/entrada recusada | 3 Docker indisponível | 4 banco não subiu.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

PREFIX = "starcode-eph-"
NAME_RE = re.compile(r"^starcode-eph-[a-z0-9_.-]+$")
ENGINES = {
    "postgresql": {"port": 5432, "scheme": "postgresql+psycopg"},
    "mysql": {"port": 3306, "scheme": "mysql+pymysql"},
}
READY_SECONDS = 60
RUN_ATTEMPTS = 3
PORT_BUSY = ("port is already allocated", "address already in use", "port is already in use")


def _docker() -> str | None:
    return shutil.which("docker")


def _call(args: list[str], timeout: float | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_docker() or "docker", *args], capture_output=True, text=True, timeout=timeout
    )


def _docker_unavailable_reason() -> str | None:
    """None se o daemon responde; senão o motivo."""
    if not _docker():
        return "docker não encontrado no PATH"
    try:
        r = _call(["info"], timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc) or exc.__class__.__name__
    if r.returncode != 0:
        lines = (r.stderr or r.stdout or "").strip().splitlines()
        return lines[-1].strip() if lines else f"docker info saiu com {r.returncode}"
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _is_local(url: str) -> bool:
    try:
        host = urlparse(url).hostname
    except ValueError:
        return False
    return host in ("127.0.0.1", "localhost")


def _image_from_stack(engine: str) -> str | None:
    try:
        with open(os.path.join(".starcode", "stack.json"), encoding="utf-8") as fh:
            image = json.load(fh).get("image", {})
    except (OSError, ValueError):
        return None
    value = image.get(engine) if isinstance(image, dict) else None
    return value if isinstance(value, str) and value else None


def _remove(name: str) -> None:
    try:
        _call(["rm", "-f", "-v", name], timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        pass


def _ready_probe(engine: str, name: str, user: str, password: str, db: str) -> list[str]:
    if engine == "postgresql":
        return ["exec", name, "pg_isready", "-h", "127.0.0.1", "-U", user, "-d", db]
    return ["exec", name, "mysqladmin", "ping", "-h", "127.0.0.1", "-u", user, f"-p{password}", "--silent"]


def _wait_ready(engine: str, name: str, user: str, password: str, db: str) -> bool:
    limit = float(os.environ.get("STARCODE_EPH_READY_SECONDS", READY_SECONDS))
    interval = float(os.environ.get("STARCODE_EPH_POLL_SECONDS", 1))
    deadline = time.monotonic() + limit
    while True:
        try:
            if _call(_ready_probe(engine, name, user, password, db), timeout=30).returncode == 0:
                return True
        except (OSError, subprocess.TimeoutExpired):
            pass
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)


def _start(engine: str, image: str, user: str, password: str, db: str) -> tuple[str, int] | None:
    """Sobe o container; devolve (nome, porta) ou None após esgotar as tentativas."""
    spec = ENGINES[engine]
    env = (
        [f"POSTGRES_USER={user}", f"POSTGRES_PASSWORD={password}", f"POSTGRES_DB={db}"]
        if engine == "postgresql"
        else [f"MYSQL_USER={user}", f"MYSQL_PASSWORD={password}",
              f"MYSQL_ROOT_PASSWORD={secrets.token_hex(12)}", f"MYSQL_DATABASE={db}"]
    )
    for _ in range(RUN_ATTEMPTS):
        name = f"{PREFIX}{engine}-{secrets.token_hex(4)}"
        port = _free_port()
        args = ["run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:{spec['port']}"]
        for item in env:
            args += ["-e", item]
        r = _call([*args, image], timeout=600)
        if r.returncode == 0:
            return name, port
        _remove(name)  # um run que falhou pode deixar o container criado
        err = (r.stderr + r.stdout).lower()
        if not any(p in err for p in PORT_BUSY):
            sys.stderr.write(f"docker run falhou: {(r.stderr or r.stdout).strip()}\n")
            return None
    return None


def cmd_run(args: argparse.Namespace) -> int:
    command = args.command
    if not command:
        sys.stderr.write("faltou o comando depois de `--`\n")
        return 2
    env = dict(os.environ)
    existing = env.get("DATABASE_URL")
    if args.reuse_env and existing:
        if not _is_local(existing):
            sys.stderr.write("--reuse-env recusado: DATABASE_URL não aponta para 127.0.0.1/localhost\n")
            return 2
        return _run_command(command, env)  # reaproveita o banco local já configurado
    image = args.image or _image_from_stack(args.engine)
    if not image:
        sys.stderr.write(f"imagem de {args.engine} não definida: use --image ou .starcode/stack.json\n")
        return 2
    reason = _docker_unavailable_reason()
    if reason:
        sys.stderr.write(f"gate de integração não executado: Docker indisponível ({reason})\n")
        return 3
    user, password, db = f"eph_{secrets.token_hex(4)}", secrets.token_hex(12), f"eph_{secrets.token_hex(4)}"
    started = None
    try:
        started = _start(args.engine, image, user, password, db)
        if started is None:
            sys.stderr.write("banco efêmero não subiu: porta ocupada ou erro do docker run\n")
            return 4
        name, port = started
        if not _wait_ready(args.engine, name, user, password, db):
            sys.stderr.write("banco efêmero não ficou pronto em 60 s\n")
            return 4
        env["DATABASE_URL"] = f"{ENGINES[args.engine]['scheme']}://{user}:{password}@127.0.0.1:{port}/{db}"
        return _run_command(command, env)
    except KeyboardInterrupt:
        return 130
    finally:
        if started:
            _remove(started[0])


def _run_command(command: list[str], env: dict[str, str]) -> int:
    try:
        return subprocess.call(command, env=env)
    except FileNotFoundError:
        sys.stderr.write(f"comando não encontrado: {command[0]}\n")
        return 127


def _age_minutes(created: str) -> int | None:
    parts = created.split()
    try:
        if len(parts) >= 3:
            when = datetime.strptime(" ".join(parts[:3]), "%Y-%m-%d %H:%M:%S %z")
        else:
            when = datetime.strptime(" ".join(parts[:2]), "%Y-%m-%d %H:%M:%S").astimezone()
    except ValueError:
        return None
    return max(0, int((datetime.now(timezone.utc) - when).total_seconds() // 60))


def cmd_list(args: argparse.Namespace) -> int:
    reason = _docker_unavailable_reason()
    if reason:
        sys.stderr.write(f"Docker indisponível ({reason})\n")
        return 3
    r = _call(["ps", "-a", "--filter", f"name={PREFIX}", "--format", "{{.Names}} {{.CreatedAt}}"], timeout=30)
    items = []
    for line in r.stdout.splitlines():
        name, _, created = line.strip().partition(" ")
        if name.startswith(PREFIX):
            items.append({"name": name, "age_minutes": _age_minutes(created)})
    if args.json:
        print(json.dumps(items, ensure_ascii=False))
    else:
        for it in items:
            age = it["age_minutes"]
            print(f"{it['name']}\t{'?' if age is None else age} min")
    return 0


def cmd_down(args: argparse.Namespace) -> int:
    if not NAME_RE.match(args.name):
        sys.stderr.write(f"recusado: só containers com o prefixo {PREFIX} podem ser removidos\n")
        return 2
    reason = _docker_unavailable_reason()
    if reason:
        sys.stderr.write(f"Docker indisponível ({reason})\n")
        return 3
    r = _call(["rm", "-f", "-v", args.name], timeout=60)
    if r.returncode != 0:
        sys.stderr.write((r.stderr or r.stdout).strip() + "\n")
        return 1
    print(f"removido: {args.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ephemeral_db.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("engine", choices=sorted(ENGINES))
    p.add_argument("--image")
    p.add_argument("--reuse-env", action="store_true")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("list")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)
    p = sub.add_parser("down")
    p.add_argument("name")
    p.set_defaults(fn=cmd_down)
    argv = list(sys.argv[1:] if argv is None else argv)
    command: list[str] = []
    if "--" in argv:
        i = argv.index("--")
        argv, command = argv[:i], argv[i + 1:]
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    args.command = command
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
