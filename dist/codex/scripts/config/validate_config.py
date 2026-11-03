"""StarCode config validator (D20). Python stdlib only.

Two levels, both with schemaVersion 1:
  user: ~/.starcode/config.json     (personal preferences, never versioned)
  repo: <repo>/.starcode/config.json (project settings, versioned)

Unknown key = error. A schemaVersion newer than this plugin blocks and asks for an update.
Field reference: schemas/config.md.

Usage:
  python validate_config.py --kind user|repo PATH
  python validate_config.py --kind user|repo --write DEST --from SRC   (SRC may be "-" for stdin)
      Validates SRC and writes it to DEST only if valid (atomic replace). Never writes partial data.
Exit codes: 0 valid / written, 1 invalid, 2 usage or I/O error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SUPPORTED_SCHEMA = 1
CLIS = ("claude", "codex", "antigravity", "opencode")
CREW = ("picard", "spock", "troi", "data", "laforge", "mccoy", "q",
        "uhura", "scotty", "kirk", "worf", "guinan")
Q_STRATEGIES = ("opencode-subagent", "orca-worker", "self-verified")
STACKS = ("python-flask", "rust", "tauri", "typescript", "postgresql", "mysql")
LANGUAGES = ("pt-BR", "en")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
GIT_REF = re.compile(r"^(?!/)(?!.*\.\.)(?!.*//)[A-Za-z0-9._/-]+(?<!/)(?<!\.lock)$")


# --- tiny schema language -------------------------------------------------------------------
# Each field spec: dict(type=..., required=bool, ...). Types: int, str, enum, list, obj, map,
# nullable_str, date.

def _obj(fields: dict, required: bool = False) -> dict:
    return {"type": "obj", "fields": fields, "required": required}


CREW_ENTRY = _obj({
    "cli": {"type": "enum", "values": CLIS},
    "model": {"type": "str"},
})

USER_SCHEMA = _obj({
    "schemaVersion": {"type": "schema", "required": True},
    "outputLanguage": {"type": "enum", "values": LANGUAGES},
    "crew": {"type": "map", "keys": CREW, "value": CREW_ENTRY, "min_entry_keys": 1},
    "qStrategy": {"type": "list", "item": {"type": "enum", "values": Q_STRATEGIES},
                  "unique": True, "min": 1},
    "fleet": _obj({
        "maxBatch": {"type": "int", "min": 1, "max": 10},
        "timeoutMinutes": {"type": "int", "min": 1, "max": 1440},
    }),
}, required=True)

REPO_SCHEMA = _obj({
    "schemaVersion": {"type": "schema", "required": True},
    "linear": _obj({
        "workspace": {"type": "str", "required": True},
        "team": {"type": "str", "required": True},
        "states": _obj({
            "unstarted": {"type": "str", "required": True},
            "started": {"type": "str", "required": True},
            "review": {"type": "nullable_str", "required": True},
            "completed": {"type": "str", "required": True},
            "blocked": {"type": "nullable_str", "required": True},
            "verifiedAt": {"type": "date", "required": True},
        }, required=True),
    }, required=True),
    "baseBranch": {"type": "gitref", "required": True},
    "stack": {"type": "list", "item": {"type": "enum", "values": STACKS}, "unique": True},
    "sensitiveFiles": {"type": "list", "item": {"type": "str"}, "unique": True},
}, required=True)

SCHEMAS = {"user": USER_SCHEMA, "repo": REPO_SCHEMA}


def _tname(v: Any) -> str:
    return {dict: "objeto", list: "lista", str: "texto", bool: "booleano", int: "inteiro",
            float: "número", type(None): "null"}.get(type(v), type(v).__name__)


def _check(spec: dict, value: Any, path: str, errors: list[str]) -> None:
    t = spec["type"]
    where = path or "(raiz)"
    if t == "schema":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{where}: deve ser um inteiro (use {SUPPORTED_SCHEMA})")
        elif value > SUPPORTED_SCHEMA:
            errors.append(f"{where}: versão {value} é mais nova que este StarCode (suporta "
                          f"{SUPPORTED_SCHEMA}). Atualize o plugin.")
        elif value < 1:
            errors.append(f"{where}: versão {value} inválida (use {SUPPORTED_SCHEMA})")
    elif t == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            errors.append(f"{where}: esperado inteiro, veio {_tname(value)}")
            return
        if "min" in spec and value < spec["min"]:
            errors.append(f"{where}: mínimo {spec['min']}, veio {value}")
        if "max" in spec and value > spec["max"]:
            errors.append(f"{where}: máximo {spec['max']}, veio {value}")
    elif t in ("str", "nullable_str", "date", "gitref"):
        if value is None and t == "nullable_str":
            return
        if not isinstance(value, str):
            errors.append(f"{where}: esperado texto{' ou null' if t == 'nullable_str' else ''}, "
                          f"veio {_tname(value)}")
            return
        if not value.strip():
            errors.append(f"{where}: não pode ser vazio")
        elif t == "date" and not DATE.match(value):
            errors.append(f"{where}: data no formato AAAA-MM-DD, veio {value!r}")
        elif t == "gitref" and not GIT_REF.match(value):
            errors.append(f"{where}: nome de ramo Git inválido: {value!r}")
    elif t == "enum":
        if value not in spec["values"]:
            errors.append(f"{where}: valor {value!r} não permitido (use: {', '.join(spec['values'])})")
    elif t == "list":
        if not isinstance(value, list):
            errors.append(f"{where}: esperado lista, veio {_tname(value)}")
            return
        if len(value) < spec.get("min", 0):
            errors.append(f"{where}: precisa de pelo menos {spec['min']} item(ns)")
        for i, item in enumerate(value):
            _check(spec["item"], item, f"{path}[{i}]", errors)
        if spec.get("unique"):
            seen = set()
            for item in value:
                key = json.dumps(item, sort_keys=True)
                if key in seen:
                    errors.append(f"{where}: item repetido {item!r}")
                seen.add(key)
    elif t == "map":
        if not isinstance(value, dict):
            errors.append(f"{where}: esperado objeto, veio {_tname(value)}")
            return
        for k, v in value.items():
            if k not in spec["keys"]:
                errors.append(f"{path}.{k}: tripulante desconhecido (use: {', '.join(spec['keys'])})")
                continue
            _check(spec["value"], v, f"{path}.{k}", errors)
            if isinstance(v, dict) and len(v) < spec.get("min_entry_keys", 0):
                errors.append(f"{path}.{k}: objeto vazio (remova a chave ou defina cli/model)")
    elif t == "obj":
        if not isinstance(value, dict):
            errors.append(f"{where}: esperado objeto, veio {_tname(value)}")
            return
        fields = spec["fields"]
        for k in value:
            if k not in fields:
                errors.append(f"{(path + '.') if path else ''}{k}: chave desconhecida")
        for k, sub in fields.items():
            sub_path = f"{path}.{k}" if path else k
            if k not in value:
                if sub.get("required"):
                    errors.append(f"{sub_path}: obrigatório")
                continue
            _check(sub, value[k], sub_path, errors)
    else:  # pragma: no cover - schema bug
        raise AssertionError(f"unknown spec type {t}")


def validate(kind: str, data: Any) -> list[str]:
    """Return a list of PT-BR error messages; empty list means valid."""
    if kind not in SCHEMAS:
        raise ValueError(f"kind must be one of {sorted(SCHEMAS)}")
    errors: list[str] = []
    _check(SCHEMAS[kind], data, "", errors)
    return errors


def load(kind: str, path: Path) -> tuple[Any, list[str]]:
    """Read and validate a config file. Returns (data or None, errors)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [f"{path}: arquivo não encontrado"]
    except OSError as exc:
        return None, [f"{path}: não foi possível ler ({exc})"]
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, [f"{path}: JSON inválido na linha {exc.lineno}, coluna {exc.colno} ({exc.msg})"]
    errors = validate(kind, data)
    return (None if errors else data), errors


def write_validated(kind: str, data: Any, dest: Path) -> list[str]:
    errors = validate(kind, data)
    if errors:
        return errors
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".config.", suffix=".tmp", dir=dest.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, dest)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return []


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Valida configs do StarCode (schemaVersion 1).")
    parser.add_argument("--kind", choices=sorted(SCHEMAS), required=True)
    parser.add_argument("path", nargs="?", help="arquivo a validar")
    parser.add_argument("--write", metavar="DEST", help="grava DEST só se o conteúdo de --from for válido")
    parser.add_argument("--from", dest="src", metavar="SRC", help="origem para --write ('-' = stdin)")
    args = parser.parse_args(argv)

    if args.write:
        if not args.src:
            parser.error("--write exige --from")
        try:
            raw = sys.stdin.read() if args.src == "-" else Path(args.src).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERRO: não foi possível ler {args.src}: {exc}")
            return 2
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"INVÁLIDO: JSON inválido na linha {exc.lineno}, coluna {exc.colno} ({exc.msg}). Nada foi gravado.")
            return 1
        errors = write_validated(args.kind, data, Path(args.write))
        if errors:
            print(f"INVÁLIDO ({args.kind}): nada foi gravado em {args.write}")
            for e in errors:
                print(f"  - {e}")
            return 1
        print(f"OK ({args.kind}): gravado em {args.write}")
        return 0

    if not args.path:
        parser.error("informe o caminho do arquivo ou use --write")
    _, errors = load(args.kind, Path(args.path))
    if errors:
        print(f"INVÁLIDO ({args.kind}): {args.path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"OK ({args.kind}): {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
