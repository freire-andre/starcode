#!/usr/bin/env python3
# Origem: adaptado de the-judge/scripts/scan_bypasses.py (the-judge 1.4.0, Felipe Rodrigues,
# licença CC-BY-4.0). Mudanças: leitura via --diff ou stdin em UTF-8 explícito, contagem de linhas
# do hunk para não confundir conteúdo adicionado com cabeçalho, só stdlib.
"""Varredura de bypass em um diff unificado (Worf, R1, R2). Só stdlib.

  scan_bypasses.py [--diff ARQUIVO]      (sem --diff, lê o diff do stdin)

Imprime `<arquivo>:<linha>\t<categoria>\t<conteúdo>` por linha adicionada com marcador.
Os acertos são candidatos, nunca achados. Sai sempre com 0: um detector não bloqueia a revisão.
"""
from __future__ import annotations

import argparse
import re
import sys

MARKERS = [
    ("suppression", re.compile(r"eslint-disable")),
    ("suppression", re.compile(r"@ts-(ignore|expect-error|nocheck)")),
    ("suppression", re.compile(r"#\s*noqa")),
    ("suppression", re.compile(r"#\s*type:\s*ignore")),
    ("suppression", re.compile(r"pylint:\s*disable")),
    ("suppression", re.compile(r"rubocop:\s*disable")),
    ("suppression", re.compile(r"@SuppressWarnings")),
    ("suppression", re.compile(r"//\s*nolint|\bnolint:")),
    ("suppression", re.compile(r"biome-ignore")),
    ("suppression", re.compile(r"#pragma\s+warning\s*\(?\s*disable", re.I)),
    ("test-dodge", re.compile(r"\.(only|skip)\s*\(")),
    ("test-dodge", re.compile(r"\b(xit|xdescribe|xtest)\s*\(")),
    ("test-dodge", re.compile(r"@pytest\.mark\.skip|@unittest\.skip")),
    ("test-dodge", re.compile(r"\bt\.Skip\s*\(")),
    ("hook-bypass", re.compile(r"--no-verify\b")),
    ("tls-bypass", re.compile(r"rejectUnauthorized\s*:\s*false|verify\s*=\s*False|InsecureSkipVerify|NODE_TLS_REJECT_UNAUTHORIZED")),
    ("type-bypass", re.compile(r"\bas\s+any\b|\bas\s+unknown\s+as\b")),
    ("error-swallow", re.compile(r"except(\s+\w+)?\s*:\s*pass\b|catch\s*(\([^)]*\))?\s*\{\s*\}")),
    ("unsafe-html", re.compile(r"dangerouslySetInnerHTML|bypassSecurityTrust")),
    ("sync-hack", re.compile(r"\btime\.sleep\s*\(|\bThread\.sleep\s*\(")),
]

FILE_RE = re.compile(r"^\+\+\+ (?:b/)?(.+?)\s*$")
HUNK_RE = re.compile(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def scan(lines) -> tuple[list[str], int]:
    out: list[str] = []
    path = None
    new_line = 0
    old_left = new_left = 0  # linhas que ainda faltam no hunk atual
    for raw in lines:
        line = raw.rstrip("\r\n")
        in_hunk = old_left > 0 or new_left > 0
        if not in_hunk:
            m = FILE_RE.match(line)
            if m:
                path = None if m.group(1) == "/dev/null" else m.group(1)
                continue
            m = HUNK_RE.match(line)
            if m:
                old_left = int(m.group(1)) if m.group(1) is not None else 1
                new_line = int(m.group(2))
                new_left = int(m.group(3)) if m.group(3) is not None else 1
            continue
        if line.startswith("\\"):
            continue
        if line.startswith("+"):
            new_left -= 1
            content = line[1:]
            if path is not None:
                for category, rx in MARKERS:
                    if rx.search(content):
                        out.append(f"{path}:{new_line}\t{category}\t{content.strip()[:160]}")
                        break
            new_line += 1
        elif line.startswith("-"):
            old_left -= 1
        else:
            old_left -= 1
            new_left -= 1
            new_line += 1
    return out, len(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--diff")
    try:
        args, _ = parser.parse_known_args(argv)
    except SystemExit:
        args = argparse.Namespace(diff=None)
    try:
        if args.diff:
            with open(args.diff, "rb") as fh:
                data = fh.read()
        else:
            data = sys.stdin.buffer.read()
        text = data.decode("utf-8", errors="replace")
        rows, hits = scan(text.splitlines())
    except Exception:  # um detector nunca bloqueia a revisão
        rows, hits = [], 0
    sys.stdout.buffer.write("".join(r + "\n" for r in rows).encode("utf-8"))
    sys.stdout.flush()
    sys.stderr.buffer.write(f"scan: {hits} candidate(s)\n".encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
