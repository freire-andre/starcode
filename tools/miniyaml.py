"""Minimal YAML subset parser (Python stdlib only) for StarCode source files such as src/crew.yaml.

Supported: nested block mappings (2-space indentation recommended), block lists of scalars or
mappings ("- item" / "- key: value"), flat flow lists ("[a, b]") and flat flow mappings
("{k: v, k2: v2}"), comments ("# ..."), plain/single-quoted/double-quoted scalars, int, float,
true/false, null/~.
Not supported (raises YamlError): anchors, aliases, multi-line strings (| >), nested flow
collections, tabs.
"""
from __future__ import annotations

import re
from typing import Any


class YamlError(ValueError):
    pass


_INT = re.compile(r"^[-+]?\d+$")
_FLOAT = re.compile(r"^[-+]?\d+\.\d+$")


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(text: str, lineno: int) -> Any:
    t = text.strip()
    if t == "":
        return None
    if t[0] in "'\"":
        if len(t) < 2 or t[-1] != t[0]:
            raise YamlError(f"line {lineno}: unterminated quoted string")
        body = t[1:-1]
        if t[0] == '"':
            body = re.sub(r'\\(["\\nt])', lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body)
        else:
            body = body.replace("''", "'")
        return body
    if t.startswith("[") :
        if not t.endswith("]"):
            raise YamlError(f"line {lineno}: unterminated flow list")
        inner = t[1:-1].strip()
        if not inner:
            return []
        return [_scalar(p, lineno) for p in _split_flow(inner, lineno)]
    if t.startswith("{"):
        if not t.endswith("}"):
            raise YamlError(f"line {lineno}: unterminated flow mapping")
        inner = t[1:-1].strip()
        out: dict[str, Any] = {}
        if not inner:
            return out
        for part in _split_flow(inner, lineno):
            kv = _split_key(part.strip(), lineno)
            if kv is None:
                raise YamlError(f"line {lineno}: expected 'key: value' inside flow mapping")
            if kv[0] in out:
                raise YamlError(f"line {lineno}: duplicate key {kv[0]!r}")
            out[kv[0]] = _scalar(kv[1], lineno)
        return out
    if t[0] in "&*|>!":
        raise YamlError(f"line {lineno}: unsupported YAML syntax {t[0]!r}")
    low = t.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if _INT.match(t):
        return int(t)
    if _FLOAT.match(t):
        return float(t)
    return t


def _split_flow(inner: str, lineno: int) -> list[str]:
    parts, cur, quote = [], [], None
    for ch in inner:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
        elif ch == ",":
            parts.append("".join(cur))
            cur = []
        elif ch in "[]{}":
            raise YamlError(f"line {lineno}: nested flow collections are not supported")
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _split_key(content: str, lineno: int) -> tuple[str, str] | None:
    """Return (key, rest) if content is 'key: rest' or 'key:'; None otherwise."""
    quote = None
    for i, ch in enumerate(content):
        if quote:
            if ch == quote:
                quote = None
            continue
        if ch in "'\"" and i == 0:
            quote = ch
            continue
        if ch == ":" and (i + 1 == len(content) or content[i + 1] == " "):
            key = content[:i].strip()
            if key[:1] in "'\"":
                key = _scalar(key, lineno)
            return str(key), content[i + 1:].strip()
    return None


def loads(text: str) -> Any:
    lines: list[tuple[int, int, str]] = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise YamlError(f"line {n}: tabs are not allowed for indentation")
        stripped = _strip_comment(raw)
        if not stripped.strip() or stripped.strip() == "---":
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((n, indent, stripped.strip()))
    if not lines:
        return None
    value, pos = _block(lines, 0, lines[0][1])
    if pos != len(lines):
        raise YamlError(f"line {lines[pos][0]}: unexpected indentation")
    return value


def _block(lines, pos: int, indent: int):
    if lines[pos][2].startswith("- ") or lines[pos][2] == "-":
        return _list(lines, pos, indent)
    return _map(lines, pos, indent)


def _map(lines, pos: int, indent: int):
    result: dict[str, Any] = {}
    while pos < len(lines):
        n, ind, content = lines[pos]
        if ind < indent:
            break
        if ind > indent:
            raise YamlError(f"line {n}: unexpected indentation")
        if content.startswith("- "):
            raise YamlError(f"line {n}: list item where a mapping key was expected")
        kv = _split_key(content, n)
        if kv is None:
            raise YamlError(f"line {n}: expected 'key: value'")
        key, rest = kv
        if key in result:
            raise YamlError(f"line {n}: duplicate key {key!r}")
        pos += 1
        if rest:
            result[key] = _scalar(rest, n)
        elif pos < len(lines) and (lines[pos][1] > indent or
                                   (lines[pos][1] == indent and lines[pos][2].startswith("- "))):
            result[key], pos = _block(lines, pos, lines[pos][1])
        else:
            result[key] = None
    return result, pos


def _list(lines, pos: int, indent: int):
    result: list[Any] = []
    while pos < len(lines):
        n, ind, content = lines[pos]
        if ind < indent or not (content.startswith("- ") or content == "-"):
            if ind > indent:
                raise YamlError(f"line {n}: unexpected indentation")
            break
        if ind > indent:
            raise YamlError(f"line {n}: unexpected indentation")
        item = content[1:].strip()
        pos += 1
        if not item:
            if pos < len(lines) and lines[pos][1] > indent:
                value, pos = _block(lines, pos, lines[pos][1])
            else:
                value = None
            result.append(value)
            continue
        kv = _split_key(item, n) if not item.startswith(("'", '"', "[")) else None
        if kv is None:
            result.append(_scalar(item, n))
            continue
        # "- key: value" starts an inline mapping whose further keys are indented past the dash.
        child_indent = ind + 2
        synthetic = [(n, child_indent, item)]
        j = pos
        while j < len(lines) and lines[j][1] >= child_indent:
            synthetic.append(lines[j])
            j += 1
        value, used = _map(synthetic, 0, child_indent)
        if used != len(synthetic):
            raise YamlError(f"line {synthetic[used][0]}: unexpected indentation")
        result.append(value)
        pos = j
    return result, pos
