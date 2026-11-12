"""Fixtures de aceite do StarCode (R39). Só stdlib.

  python tools/aceite.py listar
  python tools/aceite.py preparar <nome> [--destino <dir>]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "aceite"
SKIP = {"node_modules", "dist", ".git", "target"}


def _fixtures() -> list[str]:
    if not FIXTURES.is_dir():
        return []
    return sorted(p.name for p in FIXTURES.iterdir() if p.is_dir())


def _dentro(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                   stdin=subprocess.DEVNULL)


def _ignorar(_dir: str, names: list[str]) -> list[str]:
    return [n for n in names if n in SKIP]


def preparar(nome: str, destino: str | None) -> int:
    src = FIXTURES / nome
    if nome not in _fixtures():
        print(f"erro: fixture '{nome}' não existe. Disponíveis: {', '.join(_fixtures()) or '(nenhuma)'}",
              file=sys.stderr)
        return 2
    if destino:
        dest = Path(destino).expanduser().resolve()
    else:
        dest = Path(tempfile.mkdtemp(prefix=f"starcode-aceite-{nome}-"))
    if _dentro(dest, ROOT.resolve()):
        print(f"erro: o destino {dest} está dentro do repositório StarCode", file=sys.stderr)
        return 2
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        print(f"erro: o destino {dest} já existe e não está vazio", file=sys.stderr)
        return 2
    shutil.copytree(src, dest, ignore=_ignorar, dirs_exist_ok=True)
    try:
        _git(dest, "init", "-q")
        _git(dest, "config", "core.autocrlf", "false")
        _git(dest, "config", "user.email", "aceite@starcode.local")
        _git(dest, "config", "user.name", "StarCode Aceite")
        _git(dest, "config", "commit.gpgsign", "false")
        _git(dest, "add", "-A")
        _git(dest, "commit", "-q", "-m", f"chore: fixture de aceite {nome}")
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(f"erro: git falhou: {getattr(exc, 'stderr', exc)}", file=sys.stderr)
        return 1
    print(f"Fixture '{nome}' pronta em: {dest}")
    print("Próximos passos:")
    print(f"  1. cd {dest} && npm ci")
    print(f"  2. orca repo add {dest}")
    print("  3. Aviso: a .starcode/config.json da fixture aponta para o Linear do mantenedor "
          "(time PROJ). Rode o setup do StarCode (starcode:setup) nesta cópia para usar o seu Linear.")
    print("  Pré-requisitos: Node, Rust/Tauri e Orca.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aceite.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar", help="lista as fixtures")
    p = sub.add_parser("preparar", help="copia a fixture para uma cópia de trabalho com git")
    p.add_argument("nome")
    p.add_argument("--destino")
    args = ap.parse_args(argv)
    if args.cmd == "listar":
        for n in _fixtures():
            print(n)
        return 0
    return preparar(args.nome, args.destino)


if __name__ == "__main__":
    sys.exit(main())
