"""Raio de impacto (fase 12): dos arquivos mudados, escolhe os testes que os alcançam pelo grafo de imports.

Usage:
  python impact.py select [--root DIR] [--json] <arquivo>...
  python impact.py select [--root DIR] [--json] --diff <base>[..<head>]

O grafo é por arquivo. Qualquer dúvida vira "rodar tudo" (nunca um conjunto vazio ou parcial).
Saída 0 (seleção ou rodar tudo), 1 (git falhou) e 2 (argumentos inválidos). Só stdlib.
"""
from __future__ import annotations

import argparse
import ast
import json
import posixpath
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

MAX_BYTES = 1024 * 1024  # R21: acima de 1 MiB o arquivo não entra no grafo
TS_JS_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts")


class ImpactError(Exception):
    def __init__(self, step: str, reason: str) -> None:
        super().__init__(f"{step}: {reason}")
        self.step = step
        self.reason = reason


class GraphError(Exception):
    """Arquivo do grafo ilegível, com erro de sintaxe ou grande demais."""


def run_git(root, *args: str) -> str:
    step = " ".join(args[:2])
    try:
        res = subprocess.run(["git", "-c", "core.quotepath=off", *args], cwd=str(root), capture_output=True,
                             text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL)
    except OSError as exc:
        raise ImpactError(step, str(exc)) from exc
    if res.returncode != 0:
        lines = (res.stderr or res.stdout).strip().splitlines()
        raise ImpactError(step, lines[-1] if lines else f"código {res.returncode}")
    return res.stdout


def split_z(out: str) -> list[str]:
    return [p for p in out.split("\0") if p]


def norm_path(p: str) -> str:
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return posixpath.normpath(p) if p else p


def repo_files(root) -> list[str]:
    """R14: arquivos do repositório (rastreados e não rastreados não ignorados), em posix."""
    out = run_git(root, "ls-files", "-z", "-co", "--exclude-standard")
    return sorted({norm_path(p) for p in split_z(out)})


def changed_from_diff(root, diff: str) -> list[str]:
    """R14: mudados do intervalo (ou da árvore de trabalho contra <base>) mais os não rastreados."""
    names = split_z(run_git(root, "diff", "-z", "--name-only", "--no-renames", diff))
    names += split_z(run_git(root, "ls-files", "-z", "-o", "--exclude-standard"))
    return sorted({norm_path(p) for p in names})


def is_test_file(path: str) -> bool:
    """Teste real: Python `test_*.py` ou `*_test.py` (SC-176 muda o F12 R15); o resto de tests/ é apoio. TS/JS como antes."""
    parts = path.split("/")
    name = parts[-1]
    if name.endswith(".py"):
        return name.startswith("test_") or name.endswith("_test.py")
    if name.endswith(TS_JS_EXTS):
        return re.search(r"\.(test|spec)\.[^.]+$", name) is not None or "__tests__" in parts[:-1]
    return False


# --- resolvedores por extensão: ext -> (prepare(files) -> estado, resolve(estado, path, text) -> {destinos}) ---

def py_prepare(files: set[str]) -> dict:
    index: dict[str, list[str]] = {}
    for f in sorted(files):
        if not f.endswith(".py"):
            continue
        parts = f[:-3].split("/")
        if parts[-1] == "__init__":
            parts = parts[:-1]
        for i in range(len(parts)):
            index.setdefault(".".join(parts[i:]), []).append(f)
    return {"files": files, "index": index}


def py_lookup(state: dict, dotted: str) -> set[str]:
    return set(state["index"].get(dotted, ()))


def py_relative(state: dict, path: str, level: int, module: str | None, names: list[str]) -> set[str]:
    base = posixpath.dirname(path)
    for _ in range(level - 1):
        if not base:
            return set()
        base = posixpath.dirname(base)
    files = state["files"]

    def join(*parts: str) -> str:
        return "/".join(p for p in parts if p)

    def module_files(prefix: str) -> set[str]:
        return {c for c in (prefix + ".py", join(prefix, "__init__.py")) if c in files}

    prefix = join(base, module.replace(".", "/")) if module else base
    deps = module_files(prefix) if module else ({join(base, "__init__.py")} & files)
    for name in names:
        deps |= module_files(join(prefix, name))
    return deps


def py_resolve(state: dict, path: str, text: str) -> set[str]:
    try:
        tree = ast.parse(text, filename=path)
    except (SyntaxError, ValueError) as exc:
        raise GraphError(str(exc).splitlines()[0] if str(exc) else type(exc).__name__) from exc
    deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                deps |= py_lookup(state, alias.name)
        elif isinstance(node, ast.ImportFrom):
            names = [a.name for a in node.names if a.name != "*"]
            if node.level:
                deps |= py_relative(state, path, node.level, node.module, names)
            elif node.module:
                deps |= py_lookup(state, node.module)
                for name in names:
                    deps |= py_lookup(state, f"{node.module}.{name}")
    deps.discard(path)
    return deps


TS_IMPORT_RES = (
    re.compile(r"""\bfrom\s*(['"])([^'"\r\n]+)\1"""),  # import ... from / export ... from (inclusive multilinha e import type)
    re.compile(r"""\bimport\s*(['"])([^'"\r\n]+)\1"""),  # import '<esp>'
    re.compile(r"""\bimport\s*\(\s*(['"])([^'"\r\n]+)\1"""),  # import('<esp>')
    re.compile(r"""\brequire\s*\(\s*(['"])([^'"\r\n]+)\1"""),  # require('<esp>')
)
TS_ALIAS_RE = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*)(['"])(?:@|~)/""")
TS_ALIAS_REASON = "aliases do TypeScript não resolvidos"


def ts_prepare(files: set[str]) -> dict:
    return {"files": files}


def ts_specifiers(text: str) -> set[str]:
    return {m.group(2) for rx in TS_IMPORT_RES for m in rx.finditer(text)}


TS_PAIRS = {")": "(", "]": "[", "}": "{"}


def ts_balanced(text: str) -> bool:
    """Verificação barata de análise: (), [] e {} balanceados fora de strings, template literals e comentários."""
    stack: list[str] = []
    i, n, prev = 0, len(text), ";"
    while i < n:
        c = text[i]
        if i and not text[i - 1].isspace():
            prev = text[i - 1]
        elif i and text[i - 1] == "\n":
            prev = "\n"
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c in "'\"":  # string de uma linha; aspa sem fechar (texto de JSX) termina na quebra de linha
            i += 1
            while i < n and text[i] not in (c, "\n"):
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif c == "/" and prev in "(,=:[!&|?{;" + "\n":  # literal de regex: pula até a barra de fechamento
            i += 1
            in_class = False
            while i < n and text[i] != "\n" and (in_class or text[i] != "/"):
                if text[i] == "\\":
                    i += 1
                elif text[i] == "[":
                    in_class = True
                elif text[i] == "]":
                    in_class = False
                i += 1
            i += 1
        elif c == "`" or (c == "}" and stack and stack[-1] == "${"):  # template literal, com ${...} aninhado
            if c == "}":
                stack.pop()
            i += 1
            while i < n and text[i] != "`" and not text.startswith("${", i):
                i += 2 if text[i] == "\\" else 1
            if text.startswith("${", i):
                stack.append("${")
            i += 2 if i < n and text[i] == "$" else 1
        else:
            if c in "([{":
                stack.append(c)
            elif c in TS_PAIRS and (not stack or stack.pop() != TS_PAIRS[c]):
                return False
            i += 1
    return not stack


def ts_resolve(state: dict, path: str, text: str) -> set[str]:
    """R17: só './' e '../' viram arestas; testa o caminho exato, cada extensão e <esp>/index.<ext>."""
    if not ts_balanced(text):
        raise GraphError("chaves ou parênteses desbalanceados")
    files = state["files"]
    base = posixpath.dirname(path)
    deps: set[str] = set()
    for spec in ts_specifiers(text):
        if not (spec.startswith("./") or spec.startswith("../") or spec in (".", "..")):
            continue
        target = posixpath.normpath(posixpath.join(base, spec))
        if target == ".." or target.startswith("../"):
            continue
        cands = [target] + [target + ext for ext in TS_JS_EXTS] + [f"{target}/index{ext}" for ext in TS_JS_EXTS]
        deps |= {c for c in cands if c in files}
    deps.discard(path)
    return deps


def loose_json(text: str):
    """R22: JSON de tsconfig com comentários // e /* */ e vírgula final."""
    out: list[str] = []
    i, n, in_str = 0, len(text), False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        else:
            out.append(c)
        i += 1
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", "".join(out)))


def ts_aliases_present(root, files: list[str]) -> bool:
    """R22: tsconfig/jsconfig com paths ou baseUrl (ou ilegível), ou algum import '@/' ou '~/'."""
    root = Path(root)
    for f in files:
        name = posixpath.basename(f)
        if name in ("tsconfig.json", "jsconfig.json") or (name.startswith("tsconfig.") and name.endswith(".json")):
            try:
                opts = loose_json((root / f).read_text(encoding="utf-8-sig")).get("compilerOptions") or {}
            except (OSError, ValueError, UnicodeDecodeError, AttributeError):
                return True
            if isinstance(opts, dict) and ("paths" in opts or "baseUrl" in opts):
                return True
        elif f.endswith(TS_JS_EXTS):
            try:
                if (root / f).stat().st_size <= MAX_BYTES and TS_ALIAS_RE.search((root / f).read_text(encoding="utf-8")):
                    return True
            except (OSError, UnicodeDecodeError):
                continue
    return False


RESOLVERS = {".py": (py_prepare, py_resolve), **{ext: (ts_prepare, ts_resolve) for ext in TS_JS_EXTS}}


def build_graph(root, files: list[str]) -> dict[str, set[str]]:
    """Arestas arquivo -> arquivos de que ele depende. Levanta GraphError('<arquivo>: <erro>')."""
    fileset = set(files)
    states = {ext: prep(fileset) for ext, (prep, _) in RESOLVERS.items()}
    graph: dict[str, set[str]] = {}
    for f in files:
        ext = posixpath.splitext(f)[1]
        if ext not in RESOLVERS:
            continue
        full = Path(root) / f
        try:
            if full.stat().st_size > MAX_BYTES:
                raise GraphError(f"{f}: arquivo acima de 1 MiB")
            text = full.read_text(encoding="utf-8")
        except GraphError:
            raise
        except (OSError, UnicodeDecodeError) as exc:
            raise GraphError(f"{f}: {exc}") from exc
        try:
            graph[f] = RESOLVERS[ext][1](states[ext], f, text)
        except GraphError as exc:
            if ext == ".py" and "{{" in text:  # modelo com marcador ({{module}}), não é Python de verdade: fora do grafo (R21: só .py)
                continue
            raise GraphError(f"{f}: {exc}") from exc
    return graph


def run_all(reason: str, changed: list[str]) -> dict:
    return {"verdict": "run-all", "tests": [], "chains": {}, "reason": reason, "changed": changed}


def _relative(root: Path, p: str) -> str:
    q = p.replace("\\", "/")
    if re.match(r"^([A-Za-z]:)?/", q):
        try:
            return Path(p).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return norm_path(q)
    return norm_path(q)


def select(root, changed=None, diff=None) -> dict:
    """Seleciona os testes que alcançam `changed` (ou o `diff`). Levanta ImpactError se o git falhar."""
    if changed and diff:
        raise ValueError("changed e diff são exclusivos")
    root = Path(root)
    files = repo_files(root)
    if diff:
        changed_list = changed_from_diff(root, diff)
    else:
        changed_list = sorted({_relative(root, p) for p in (changed or [])})
    if not changed_list:
        return run_all("nenhuma mudança informada", [])
    changed_list = [c for c in changed_list if c != ".specs" and not c.startswith(".specs/")]
    if not changed_list:
        return run_all("nenhuma mudança fora de .specs/", [])
    conftests = [c for c in changed_list if posixpath.basename(c) == "conftest.py"]
    if conftests:  # o pytest carrega as fixtures sem import: o grafo não as vê
        return run_all("conftest.py muda fixtures sem import: " + ", ".join(conftests), changed_list)
    fileset = set(files)
    outside =[c for c in changed_list
               if c not in fileset or posixpath.splitext(c)[1] not in RESOLVERS or not (root / c).is_file()]
    if outside:
        return run_all("fora do grafo: " + ", ".join(outside), changed_list)
    if any(c.endswith(TS_JS_EXTS) for c in changed_list) and ts_aliases_present(root, files):
        return run_all(TS_ALIAS_REASON, changed_list)
    try:
        graph = build_graph(root, files)
    except GraphError as exc:
        return run_all(f"grafo incompleto: {exc}", changed_list)
    reverse: dict[str, list[str]] = {}
    for src in sorted(graph):
        for dst in sorted(graph[src]):
            reverse.setdefault(dst, []).append(src)
    # SC-176 R5: teste real que cita o basename de um mudado também o alcança, sem import
    real_tests = [f for f in files if is_test_file(f) and posixpath.splitext(f)[1] in RESOLVERS]
    for t in real_tests:
        try:
            text = (root / t).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for c in changed_list:
            if c != t and posixpath.basename(c) in text:
                reverse.setdefault(c, []).append(t)

    def reach(starts: list[str]) -> dict[str, str | None]:
        seen: dict[str, str | None] = {c: None for c in starts}
        queue = deque(starts)
        while queue:
            cur = queue.popleft()
            for dep in reverse.get(cur, ()):
                if dep not in seen:
                    seen[dep] = cur
                    queue.append(dep)
        return seen

    lonely = [c for c in changed_list if not any(is_test_file(f) for f in reach([c]))]
    if lonely:  # R6: um mudado sem teste real basta para rodar tudo
        return run_all("nenhum teste alcança " + ", ".join(lonely), changed_list)
    parent = reach(changed_list)
    tests = sorted(f for f in parent if is_test_file(f))
    chains = {}
    for t in tests:
        chain, cur = [], t
        while cur is not None:
            chain.append(cur)
            cur = parent[cur]
        chains[t] = chain[::-1]  # do arquivo mudado até o teste
    return {"verdict": "selected", "tests": tests, "chains": chains, "reason": "", "changed": changed_list}


def format_text(result: dict) -> str:
    if result["verdict"] == "run-all":
        return f"rodar tudo: {result['reason']}"
    lines = [f"selecionados {len(result['tests'])} testes"]
    for t in result["tests"]:
        lines.append("  " + " <- ".join(result["chains"][t]))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="impact.py", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select", help="seleciona os testes alcançados pelas mudanças")
    s.add_argument("--root", default=".")
    s.add_argument("--json", action="store_true")
    s.add_argument("--diff", metavar="BASE[..HEAD]")
    s.add_argument("files", nargs="*", metavar="arquivo")
    return p


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.files and args.diff:
        parser.error("informe arquivos ou --diff, não os dois")
    if not args.files and not args.diff:
        parser.error("informe arquivos ou --diff")
    try:
        result = select(args.root, changed=args.files, diff=args.diff)
    except ImpactError as exc:
        print(f"impact falhou: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else format_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
