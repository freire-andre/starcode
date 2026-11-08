"""Perfis rust e gpui renderizados com registro de fixture (R2, R3, R4, R45). Sem rede e sem cargo."""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT

import scaffold

PROFILES = ROOT / "profiles"
REGISTRY = {"crates": {"gpui": {"max_stable_version": "0.2.2", "versions": ["0.3.0-alpha.1", "0.2.2", "0.2.1"]}}}
RUST_GATES = ["cargo fmt --check", "cargo clippy --all-targets -- -D warnings", "cargo test"]


class ProfileRenderCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-rust-gpui-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        fixture = self.tmp / "registry.json"
        fixture.write_text(json.dumps(REGISTRY), encoding="utf-8")
        env = {"STARCODE_REGISTRY_FIXTURE": str(fixture), "STARCODE_PROFILES_DIR": str(PROFILES)}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def new(self, profile: str, name: str) -> Path:
        folder = self.tmp / name
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = scaffold.main(["new", str(folder), "--profile", profile, "--description", "Projeto de teste."])
        self.assertEqual(code, 0, err.getvalue())
        return folder

    def gates_of(self, profile: str) -> list[str]:
        prof = scaffold.load_profiles()[profile]
        return [cmd for key in scaffold.GATE_ORDER for cmd, _ in scaffold.gate_items(prof, key)]

    def assert_no_leftover_markers(self, folder: Path) -> None:
        for path in folder.rglob("*"):
            if path.is_file():
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"\{\{[^}]*\}\}", str(path))


class RustProfileTests(ProfileRenderCase):
    def test_rust_gates_are_exact(self) -> None:
        prof = scaffold.load_profiles()["rust"]
        self.assertEqual(self.gates_of("rust"), RUST_GATES)
        self.assertEqual(prof["tools"], ["cargo"])
        self.assertEqual(prof["kind"], "app")
        self.assertEqual(prof["combinesWith"], [])

    def test_rust_renders_lib_bin_and_test(self) -> None:
        folder = self.new("rust", "meu-rust")
        self.assert_no_leftover_markers(folder)
        cargo = (folder / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn('name = "meu-rust"', cargo)
        self.assertIn('name = "meu_rust"', cargo)
        self.assertIn("#[test]", (folder / "src" / "lib.rs").read_text(encoding="utf-8"))
        self.assertIn("meu_rust::greeting", (folder / "src" / "main.rs").read_text(encoding="utf-8"))
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("# meu-rust", readme)
        self.assertIn("Projeto de teste.", readme)
        self.assertIn("## Gates", readme)
        for gate in RUST_GATES:
            self.assertIn(gate, readme)

    def test_rust_has_ci_and_gitignore(self) -> None:
        folder = self.new("rust", "meu-rust")
        ci = (folder / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        for gate in RUST_GATES:
            self.assertIn(gate, ci)
        self.assertIn("/target", (folder / ".gitignore").read_text(encoding="utf-8"))


class GpuiProfileTests(ProfileRenderCase):
    def test_gpui_profile_fields(self) -> None:
        prof = scaffold.load_profiles()["gpui"]
        self.assertIs(prof["experimental"], True)
        self.assertEqual(prof["combinesWith"], [])
        self.assertEqual(prof["tools"], ["cargo"])
        self.assertEqual(self.gates_of("gpui"), RUST_GATES + ["cargo build"])
        dep = next(d for d in prof["deps"] if d["name"] == "gpui")
        self.assertEqual(dep["tested"], "0.2")
        self.assertTrue(dep["main"])
        self.assertTrue(dep["docs"]["id"].startswith("/"))
        self.assertRegex(str(dep["docs"]["at"]), r"^\d{4}-\d{2}-\d{2}$")

    def test_gpui_renders_with_resolved_version(self) -> None:
        folder = self.new("gpui", "meu-gpui")
        self.assert_no_leftover_markers(folder)
        cargo = (folder / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn('name = "meu-gpui"', cargo)
        self.assertIn('gpui = "0.2.2"', cargo)
        stack = json.loads((folder / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["versions"]["gpui"]["version"], "0.2.2")

    def test_gpui_counter_logic_is_tested_without_a_window(self) -> None:
        folder = self.new("gpui", "meu-gpui")
        logic = (folder / "src" / "counter.rs").read_text(encoding="utf-8")
        self.assertIn("#[test]", logic)
        self.assertNotIn("gpui", logic)
        main = (folder / "src" / "main.rs").read_text(encoding="utf-8")
        self.assertIn("open_window", main)
        self.assertIn("impl Render for CounterView", main)
        self.assertNotIn("#[test]", main)

    def test_gpui_has_readme_ci_and_gitignore(self) -> None:
        folder = self.new("gpui", "meu-gpui")
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("# meu-gpui", readme)
        self.assertIn("experimental", readme.lower())
        for gate in RUST_GATES + ["cargo build"]:
            self.assertIn(gate, readme)
        ci = (folder / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("cargo build", ci)
        self.assertIn("/target", (folder / ".gitignore").read_text(encoding="utf-8"))


class NoHardcodedVersionTests(unittest.TestCase):
    def test_templates_have_no_dependency_version_numbers(self) -> None:
        for profile in ("rust", "gpui"):
            text = (PROFILES / profile / "template" / "Cargo.toml").read_text(encoding="utf-8")
            deps = text.split("[dependencies]", 1)[1] if "[dependencies]" in text else ""
            self.assertNotRegex(deps, r'"\d', profile)
            self.assertIsNone(re.search(r"\[(dev-|build-)?dependencies\.", text))


if __name__ == "__main__":
    unittest.main()
