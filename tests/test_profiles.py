"""F8 T12: os 7 perfis de stack (R1, R2, R3, R6, R39, R42), lidos com o leitor do scripts/scaffold.py."""
from __future__ import annotations

import json
import re
import tomllib
import unittest

from helpers import ROOT

import scaffold

PROFILES_DIR = ROOT / "profiles"
APPS = {"python-flask", "rust", "tauri", "typescript", "gpui"}
DBS = {"postgresql", "mysql"}
MARKER = re.compile(r"^\{\{(name|description|module|version:[^}]+)\}\}$")
GATE_KEYS = ("lint", "typecheck", "unit", "build", "integration")


def load() -> dict[str, dict]:
    profiles = {}
    for d in sorted(PROFILES_DIR.iterdir()):
        if d.is_dir():
            doc = scaffold.loads((d / "profile.yaml").read_text(encoding="utf-8"))
            doc["_dir"] = d
            profiles[d.name] = doc
    return profiles


def commands(items) -> list[tuple[str, str | None]]:
    """Entrada de gate: texto ou {run, cwd}; devolve (comando, cwd)."""
    return [(i, None) if isinstance(i, str) else (i["run"], i.get("cwd")) for i in items or []]


def all_gates(profile: dict) -> list[tuple[str, str | None]]:
    return [c for key in GATE_KEYS for c in commands(profile["gates"].get(key))]


def dependency_specs(template) -> list[tuple[str, str]]:
    """(onde, especificação) de cada dependência declarada nos manifestos do template."""
    specs: list[tuple[str, str]] = []
    for f in template.rglob("*"):
        if f.name == "package.json":
            data = json.loads(f.read_text(encoding="utf-8"))
            for sec in ("dependencies", "devDependencies", "peerDependencies"):
                specs += [(f"{f.name}:{k}", v) for k, v in (data.get(sec) or {}).items()]
        elif f.name == "Cargo.toml":
            data = tomllib.loads(f.read_text(encoding="utf-8").replace("{{", "<<").replace("}}", ">>"))
            for sec in ("dependencies", "dev-dependencies", "build-dependencies"):
                for k, v in (data.get(sec) or {}).items():
                    specs.append((f"{f.name}:{k}", v if isinstance(v, str) else v.get("version", "")))
        elif f.name == "pyproject.toml":
            text = f.read_text(encoding="utf-8")
            specs += [(f"{f.name}:{m}", m) for m in re.findall(r'^\s*"([^"]+)",?\s*$', text, re.M)]
    return specs


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.profiles = load()

    def test_profiles_all_seven_with_required_fields(self):
        self.assertEqual(set(self.profiles), APPS | DBS)
        for name, p in self.profiles.items():
            for field in ("name", "kind", "tools", "gates", "deps"):
                self.assertIn(field, p, f"{name}.{field}")
            self.assertEqual(p["name"], name)
            self.assertEqual(p["kind"], "app" if name in APPS else "db", name)
            if name in APPS:
                self.assertIn("combinesWith", p, name)
            self.assertTrue((p["_dir"] / "template").is_dir(), name)
        self.assertIs(self.profiles["gpui"].get("experimental"), True)
        self.assertEqual(self.profiles["python-flask"]["combinesWith"], ["postgresql", "mysql"])

    def test_profiles_gate_commands_exact(self):
        rust = [("cargo fmt --check", None), ("cargo clippy --all-targets -- -D warnings", None),
                ("cargo test", None)]
        ts = [("npx tsc --noEmit", None), ("npx biome check .", None), ("npx vitest run", None)]
        expected = {
            "python-flask": [(c, None) for c in ("uv run ruff check .", "uv run ruff format --check .",
                                                 "uv run mypy src", "uv run pytest -v")],
            "rust": rust,
            "typescript": ts,
            "tauri": ts + [(c, "src-tauri") for c, _ in rust]
                     + [("npm run tauri build -- --debug --no-bundle", None)],
            "gpui": rust + [("cargo build", None)],
        }
        for engine in DBS:
            expected[engine] = [(f"python scripts/ephemeral_db.py run {engine} -- uv run pytest -v -m integration",
                                 None)]
        for name, want in expected.items():
            self.assertEqual(sorted(all_gates(self.profiles[name]), key=str), sorted(want, key=str), name)

    def test_templates_have_no_hardcoded_versions(self):
        for name, p in self.profiles.items():
            template = p["_dir"] / "template"
            specs = dependency_specs(template)
            for where, spec in specs:
                if where.startswith("pyproject.toml"):  # linhas de dependência: nome==versão
                    if "==" in spec:
                        self.assertRegex(spec, r"==\{\{version:[^}]+\}\}", f"{name}/{where}")
                    continue
                version = spec.replace("<<", "{{").replace(">>", "}}")
                self.assertRegex(version, r"^\{\{version:[^}]+\}\}$", f"{name}/{where}")
            # o inject dos perfis de banco também só usa marcadores
            for item in p.get("inject") or []:
                for line in item["lines"]:
                    if "==" in line:
                        self.assertRegex(line, r"==\{\{version:[^}]+\}\}", f"{name}: {line}")
        # nenhuma dependência `main` fica sem marcador no template (apps) ou no inject (bancos)
        for name, p in self.profiles.items():
            template = p["_dir"] / "template"
            text = "".join(f.read_text(encoding="utf-8") for f in template.rglob("*")
                           if f.is_file() and f.suffix not in (".png", ".ico", ".icns"))
            text += " ".join(line for item in p.get("inject") or [] for line in item["lines"])
            for dep in p["deps"]:
                if dep.get("main"):
                    self.assertIn("{{version:" + dep["name"] + "}}", text, f"{name}: {dep['name']}")

    def test_app_templates_have_ci_and_gitignore(self):
        for name in sorted(APPS):
            template = self.profiles[name]["_dir"] / "template"
            self.assertTrue((template / ".gitignore").is_file(), name)
            ci = template / ".github" / "workflows" / "ci.yml"
            self.assertTrue(ci.is_file(), name)
            text = ci.read_text(encoding="utf-8")
            for cmd, _ in all_gates(self.profiles[name]):
                self.assertIn(cmd, text, f"{name}: ci.yml sem o gate {cmd!r}")
        for name in sorted(DBS):  # banco: o CI de integração vai num arquivo separado (T9)
            self.assertTrue((self.profiles[name]["_dir"] / "template" / ".github" / "workflows"
                             / "ci-db.yml").is_file(), name)

    def test_profiles_main_deps_have_tested_series(self):
        for name, p in self.profiles.items():
            for dep in p["deps"]:
                if dep.get("main"):
                    tested = str(dep.get("tested", ""))
                    where = f"{name}.{dep['name']}"
                    self.assertRegex(tested, r"^\d+(\.\d+)?$", where)
                    if tested.startswith("0."):
                        self.assertRegex(tested, r"^0\.\d+$", where)
                    else:
                        self.assertNotIn(".", tested, f"{where}: >= 1 pede só o major")

    def test_profiles_main_deps_have_docs_id(self):
        for name, p in self.profiles.items():
            for dep in p["deps"]:
                if dep.get("main"):
                    docs = dep.get("docs")
                    where = f"{name}.{dep['name']}"
                    self.assertIsInstance(docs, dict, where)
                    self.assertRegex(str(docs.get("id", "")), r"^/[\w.-]+/[\w.-]+", where)
                    self.assertRegex(str(docs.get("at", "")), r"^\d{4}-\d{2}-\d{2}$", where)


if __name__ == "__main__":
    unittest.main()
