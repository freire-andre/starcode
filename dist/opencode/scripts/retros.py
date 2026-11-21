"""retros.py: estado das ações propostas nas retros (SC-212). Só a biblioteca padrão.

    python retros.py abertas [--root DIR] [--json] [--todas]
    python retros.py estado <slug> <n> (--feito <commit> | --recusado <motivo> | --aberto [<issue>]) [--root DIR]

`abertas` lista as linhas cujo `Estado` começa com `aberto` em `.specs/features/*/retro.md`; `estado` reescreve só a
célula `Estado` da linha `<n>`, o resto do arquivo fica idêntico em bytes. A coluna é achada pelo nome do cabeçalho.
Saída 0 em sucesso, 2 em recusa (uma linha com o motivo) ou uso inválido.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

PIPE = "&#124;"


def _norm(cell: str) -> str:
    return unicodedata.normalize("NFC", cell).strip().casefold()


def _cells(line: str) -> list[str]:
    """Cells of a table row, without the outer pipes; an empty list when the line is not a row."""
    s = line.strip()
    if not s.startswith("|"):
        return []
    s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return s.split("|")


def _is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(c.strip() and set(c.strip()) <= set("-: ") for c in cells)


def tables(lines: list[str]) -> list[dict]:
    """Tables whose header has `Ação proposta`: columns by header name and rows with their line number."""
    found: list[dict] = []
    i = 0
    while i < len(lines):
        head = _cells(lines[i])
        if head and "ação proposta" in [_norm(c) for c in head] and i + 1 < len(lines) \
                and _is_separator(_cells(lines[i + 1])):
            names = [_norm(c) for c in head]
            table = {"cols": {n: k for k, n in reversed(list(enumerate(names)))}, "rows": []}
            j = i + 2
            while j < len(lines) and _cells(lines[j]):
                table["rows"].append((j, _cells(lines[j])))
                j += 1
            found.append(table)
            i = j
        else:
            i += 1
    return found


def _split(text: str) -> list[str]:
    return text.splitlines()


def _row_number(table: dict, pos: int, cells: list[str]) -> str:
    k = table["cols"].get("#")
    if k is not None and k < len(cells) and cells[k].strip():
        return cells[k].strip()
    return str(pos + 1)


def _cell(cells: list[str], k: int | None) -> str:
    return cells[k].strip() if k is not None and k < len(cells) else ""


def retro_paths(root: Path) -> list[Path]:
    return sorted((root / ".specs" / "features").glob("*/retro.md"))


def abertas(root: Path, todas: bool = False) -> tuple[list[dict], int]:
    """(rows, retros sem coluna Estado)."""
    rows: list[dict] = []
    sem_coluna = 0
    for path in retro_paths(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = False
        for table in tables(_split(text)):
            col_estado = table["cols"].get("estado")
            col_acao = table["cols"].get("ação proposta")
            if col_estado is None:
                missing = True
            for pos, (_line, cells) in enumerate(table["rows"]):
                estado = _cell(cells, col_estado) if col_estado is not None else "sem estado"
                if col_estado is not None and not _norm(estado).startswith("aberto"):
                    continue
                if col_estado is None and not todas:
                    continue
                rows.append({"slug": path.parent.name, "n": _row_number(table, pos, cells),
                             "estado": estado, "acao": _cell(cells, col_acao)})
        sem_coluna += missing
    return rows, sem_coluna


def clean(text: str) -> str:
    return " ".join(text.replace("|", PIPE).split())


def set_estado(slug: str, n: str, value: str, root: Path) -> str | None:
    """Rewrite only the Estado cell of row n; returns the refusal reason (file untouched) or None."""
    path = root / ".specs" / "features" / slug / "retro.md"
    if not path.is_file():
        return f"retro não encontrada: {slug}"
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return f"retro ilegível (não é UTF-8): {slug}"
    pieces = text.splitlines(keepends=True)
    lines = [p.rstrip("\r\n") for p in pieces]
    found = tables(lines)
    with_col = [t for t in found if t["cols"].get("estado") is not None]
    if not with_col:
        return f"retro sem coluna Estado: {slug}"
    for table in with_col:
        k = table["cols"]["estado"]
        for pos, (idx, cells) in enumerate(table["rows"]):
            if _row_number(table, pos, cells) != n:
                continue
            if k >= len(cells):
                return f"linha {n} da retro de {slug} não tem a célula Estado"
            s = lines[idx]
            bars = [m for m, ch in enumerate(s) if ch == "|"]
            start = bars[k] + 1
            end = bars[k + 1] if k + 1 < len(bars) else len(s.rstrip())
            pieces[idx] = s[:start] + f" {value} " + s[end:] + pieces[idx][len(s):]
            path.write_bytes("".join(pieces).encode("utf-8"))
            return None
    return f"linha {n} não existe na retro de {slug}"


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="retros.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("abertas")
    pa.add_argument("--root", default=".")
    pa.add_argument("--json", action="store_true")
    pa.add_argument("--todas", action="store_true")
    pe = sub.add_parser("estado")
    pe.add_argument("slug")
    pe.add_argument("n")
    pe.add_argument("--root", default=".")
    grp = pe.add_mutually_exclusive_group(required=True)
    grp.add_argument("--feito", metavar="COMMIT")
    grp.add_argument("--recusado", metavar="MOTIVO")
    grp.add_argument("--aberto", nargs="?", const="", default=None, metavar="ISSUE")
    try:
        a = p.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    root = Path(a.root)
    if a.cmd == "abertas":
        rows, sem_coluna = abertas(root, a.todas)
        if a.json:
            print(json.dumps({"retros": rows, "sem_coluna_estado": sem_coluna}, ensure_ascii=False))
        else:
            for r in rows:
                print(f"{r['slug']} #{r['n']} {r['estado']}: {r['acao']}")
            print(f"{sem_coluna} retro(s) sem coluna Estado")
        return 0
    if a.feito is not None:
        value = f"feito em {clean(a.feito)}" if clean(a.feito) else ""
    elif a.recusado is not None:
        value = f"recusado: {clean(a.recusado)}" if clean(a.recusado) else ""
    else:
        issue = clean(a.aberto)
        value = f"aberto: {issue}" if issue else "aberto"
    if not value:
        print("estado vazio: informe o commit ou o motivo", file=sys.stderr)
        return 2
    reason = set_estado(a.slug, a.n.strip(), value, root)
    if reason:
        print(reason, file=sys.stderr)
        return 2
    print(f"{a.slug} #{a.n.strip()}: {value}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
