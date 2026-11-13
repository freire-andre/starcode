"""gate_common.py: the one path-coverage rule shared by check_scope and the tasks gate (R1, R3).

`covers(path, entry)`: with the path normalized (backslash becomes `/`, `posixpath.normpath`), an entry ending in
`/` covers a path that starts with it; any other entry covers a path equal to it or matching it by
`fnmatch`. A path that leaves the project (`..`, `../x`, `/x`) is never covered, not even by `*`.
"""
from __future__ import annotations

import fnmatch
import posixpath


def normalize(path: str) -> str:
    return posixpath.normpath(path.strip().strip("`'\"").replace("\\", "/"))


def covers(path: str, entry: str) -> bool:
    p = normalize(path)
    if p == ".." or p.startswith("../") or p.startswith("/"):
        return False
    e = entry.strip().strip("`'\"").replace("\\", "/")
    while e.startswith("./"):
        e = e[2:]
    if e.endswith("/"):
        return p.startswith(e)
    return p == e or fnmatch.fnmatch(p, e)
