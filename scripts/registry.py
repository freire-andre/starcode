#!/usr/bin/env python3
"""Reads the latest stable version of a package from npm, PyPI, crates.io or Docker Hub (stdlib only).

Usage: python registry.py <registry> <package> [--series S] [--json]
With STARCODE_REGISTRY_FIXTURE=<file.json> no network is used and source() is "fixture".
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

TIMEOUT = 15
REGISTRIES = ("npm", "pypi", "crates", "dockerhub")
_PRE = re.compile(r"-|(?<=\d)(?:a|b|c|rc|alpha|beta|pre|dev)\d*|\.?dev", re.IGNORECASE)


class RegistryError(Exception):
    pass


def source() -> str:
    return "fixture" if os.environ.get("STARCODE_REGISTRY_FIXTURE") else "registry"


def is_prerelease(version: str) -> bool:
    return bool(_PRE.search(version.split("+", 1)[0]))


def _key(version: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", version.split("+", 1)[0].split("-", 1)[0])
    return tuple(int(n) for n in nums)


def in_series(version: str, series: str) -> bool:
    parts = [int(p) for p in series.split(".")]
    return list(_key(version)[: len(parts)]) == parts


def _fail(registry: str, package: str, reason: object) -> RegistryError:
    return RegistryError(f"registro {registry} indisponível para {package}: {reason}")


def _fetch(registry: str, package: str, url: str, headers: dict[str, str] | None = None) -> object:
    req = urllib.request.Request(url, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise _fail(registry, package, f"JSON inválido ({exc})") from exc
    except UnicodeDecodeError as exc:
        raise _fail(registry, package, f"resposta ilegível ({exc})") from exc
    except OSError as exc:  # HTTPError, URLError and timeouts are OSErrors
        raise _fail(registry, package, exc) from exc


def _fixture(registry: str, package: str) -> object:
    path = os.environ["STARCODE_REGISTRY_FIXTURE"]
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise _fail(registry, package, f"fixture ilegível ({exc})") from exc
    try:
        return data[registry][package]
    except (KeyError, TypeError) as exc:
        raise _fail(registry, package, "pacote inexistente na fixture") from exc


def _best(versions: list[str], series: str | None) -> str | None:
    ok = [v for v in versions if isinstance(v, str) and _key(v) and not is_prerelease(v)
          and (series is None or in_series(v, series))]
    return max(ok, key=_key) if ok else None


def _versions(registry: str, package: str) -> tuple[list[str], str | None]:
    """Returns (stable-candidate versions, shortcut latest or None) for the registry."""
    fixture = bool(os.environ.get("STARCODE_REGISTRY_FIXTURE"))
    q = urllib.parse.quote(package, safe="@")
    if registry == "npm":
        data = _fixture(registry, package) if fixture else _fetch(
            registry, package, f"https://registry.npmjs.org/{q.replace('/', '%2F')}")
        if not isinstance(data, dict):
            raise _fail(registry, package, "resposta inesperada")
        latest = data.get("latest") if fixture else (data.get("dist-tags") or {}).get("latest")
        versions = data.get("versions", [])
        return list(versions) if isinstance(versions, (list, dict)) else [], latest
    if registry == "pypi":
        data = _fixture(registry, package) if fixture else _fetch(
            registry, package, f"https://pypi.org/pypi/{q}/json")
        if fixture and isinstance(data, list):
            return list(data), None
        releases = data.get("releases") if isinstance(data, dict) else None
        if not isinstance(releases, dict):
            raise _fail(registry, package, "resposta inesperada")
        return [v for v, files in releases.items()
                if files and not any(f.get("yanked") for f in files)], None
    if registry == "crates":
        data = _fixture(registry, package) if fixture else _fetch(
            registry, package, f"https://crates.io/api/v1/crates/{q}", {"User-Agent": "starcode-registry"})
        if not isinstance(data, dict):
            raise _fail(registry, package, "resposta inesperada")
        if fixture:
            return list(data.get("versions", [])), data.get("max_stable_version")
        crate = data.get("crate") or {}
        versions = [v.get("num") for v in data.get("versions", []) if not v.get("yanked")]
        return versions, crate.get("max_stable_version") or data.get("max_stable_version")
    if registry == "dockerhub":
        data = _fixture(registry, package) if fixture else _fetch(
            registry, package, f"https://hub.docker.com/v2/repositories/library/{q}/tags?page_size=100")
        if isinstance(data, dict):
            data = [t.get("name") for t in data.get("results", [])]
        if not isinstance(data, list):
            raise _fail(registry, package, "resposta inesperada")
        return data, None
    raise RegistryError(f"registro {registry} desconhecido: use {', '.join(REGISTRIES)}")


def latest_stable(registry: str, package: str, *, series: str | None = None) -> str:
    versions, shortcut = _versions(registry, package)
    if registry == "dockerhub":  # only pure-numeric major tags ("17", "9")
        majors = [v for v in versions if isinstance(v, str) and v.isdigit()]
        best = _best(majors, series)
    elif series is None and shortcut and not is_prerelease(shortcut):
        best = shortcut
    else:
        best = _best(versions, series)
    if best is None:
        what = f"série {series}" if series else "versão estável"
        raise _fail(registry, package, f"sem {what}")
    return best


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="registry.py", description=__doc__.splitlines()[0])
    ap.add_argument("registry", choices=REGISTRIES)
    ap.add_argument("package")
    ap.add_argument("--series")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        version = latest_stable(args.registry, args.package, series=args.series)
    except RegistryError as exc:
        print(exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"registry": args.registry, "package": args.package, "version": version,
                          "source": source()}, ensure_ascii=False))
    else:
        print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
