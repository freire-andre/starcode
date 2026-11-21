"""orca_cli.py: o único adaptador do CLI `orca` (resolução, ambiente, tempo limite e leitura do JSON).

    import orca_cli
    res = orca_cli.run(["status", "--json"], timeout=6)   # code, stdout, stderr, data, error

`run` nunca levanta exceção: 127 sem executável, 124 com tempo esgotado, 126 com `OSError`.
Usado por `screens.py`, pelo banner e pelo `dispatch.py`. Só stdlib.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess

DROP_KEYS = ("ELECTRON_RUN_AS_NODE", "ORCA_NODE_OPTIONS", "ORCA_CLI_COMMAND")


def resolve() -> str | None:
    """Caminho do `orca` pelo PATH (`shutil.which` acha o `orca.cmd` no Windows), ou None."""
    return shutil.which("orca")


def env() -> dict[str, str]:
    """Cópia do ambiente sem as chaves que fazem o CLI da Orca rodar como Node/Electron."""
    out = {k: v for k, v in os.environ.items() if not k.startswith("NODE_") and k not in DROP_KEYS}
    if os.name == "nt":
        home = out.get("USERPROFILE") or os.path.expanduser("~")
        out.setdefault("USERPROFILE", home)
        out.setdefault("APPDATA", os.path.join(home, "AppData", "Roaming"))
        out.setdefault("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    return out


def _error(code: int, data, stdout: str, stderr: str) -> str | None:
    failed = code != 0 or (isinstance(data, dict) and data.get("ok") is False)
    if not failed:
        return None
    candidates = []
    if isinstance(data, dict):
        err = data.get("error")
        candidates.append(err.get("message") if isinstance(err, dict) else err)
    candidates += [stderr, stdout]
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return f"saiu com {code}"


def run(args: list[str], timeout: float, cwd: str | None = None) -> dict:
    exe = resolve()
    if not exe:
        return {"code": 127, "stdout": "", "stderr": "", "data": None,
                "error": "o CLI `orca` não está no PATH"}
    try:
        res = subprocess.run([exe, *args], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout, cwd=cwd, env=env())
    except subprocess.TimeoutExpired:
        return {"code": 124, "stdout": "", "stderr": "", "data": None, "error": f"tempo esgotado ({timeout} s)"}
    except (OSError, ValueError) as exc:
        reason = getattr(exc, "strerror", None) or str(exc)
        return {"code": 126, "stdout": "", "stderr": "", "data": None, "error": reason}
    stdout, stderr = res.stdout or "", res.stderr or ""
    try:
        data = json.loads(stdout)
    except ValueError:
        data = None
    if not isinstance(data, dict):
        data = None
    return {"code": res.returncode, "stdout": stdout, "stderr": stderr, "data": data,
            "error": _error(res.returncode, data, stdout, stderr)}
