"""Perfis typescript e tauri renderizados com registro de fixture (R2, R3, R4, R9). Sem rede, npm ou cargo."""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT

import scaffold

PROFILES = ROOT / "profiles"
REGISTRY = {
    "npm": {
        "typescript": {"latest": "7.0.2", "versions": ["7.0.2"]},
        "@biomejs/biome": {"latest": "2.6.6", "versions": ["2.6.6"]},
        "vitest": {"latest": "5.1.0", "versions": ["5.1.0"]},
        "vite": {"latest": "8.3.6", "versions": ["8.3.6"]},
        "@tauri-apps/cli": {"latest": "2.12.4", "versions": ["3.0.0-alpha.6", "2.12.4", "2.11.0"]},
        "@tauri-apps/api": {"latest": "3.0.0-alpha.6", "versions": ["3.0.0-alpha.6", "2.12.4", "2.11.0"]},
    },
    "crates": {
        "tauri": {"max_stable_version": "2.12.4", "versions": ["3.0.0-alpha.6", "2.12.4", "2.11.0"]},
        "tauri-build": {"max_stable_version": "2.6.0", "versions": ["3.0.0-alpha.3", "2.6.0"]},
    },
}
TS_GATES = ["npx biome check .", "npx tsc --noEmit", "npx vitest run"]
RUST_GATES = ["cargo fmt --check", "cargo clippy --all-targets -- -D warnings", "cargo test"]
BUILD = "npm run tauri build -- --debug --no-bundle"


class ProfileCase(unittest.TestCase):
    registry = REGISTRY

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="starcode-ts-tauri-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.fixture = self.tmp / "registry.json"
        self.fixture.write_text(json.dumps(self.registry), encoding="utf-8")
        env = {"STARCODE_REGISTRY_FIXTURE": str(self.fixture), "STARCODE_PROFILES_DIR": str(PROFILES)}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)

    def new(self, profile: str, name: str) -> tuple[int, Path, str]:
        folder = self.tmp / name
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = scaffold.main(["new", str(folder), "--profile", profile, "--description", "Projeto de teste."])
        return code, folder, err.getvalue()

    def ok(self, profile: str, name: str) -> Path:
        code, folder, err = self.new(profile, name)
        self.assertEqual(code, 0, err)
        return folder

    def gates(self, profile: str) -> list[tuple[str, str | None]]:
        prof = scaffold.load_profiles()[profile]
        return [item for key in scaffold.GATE_ORDER for item in scaffold.gate_items(prof, key)]

    def no_markers(self, folder: Path) -> None:
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix not in (".png", ".ico"):
                self.assertNotIn("{{", path.read_text(encoding="utf-8"), str(path))


class TypescriptProfileTests(ProfileCase):
    def test_gates_and_fields(self) -> None:
        prof = scaffold.load_profiles()["typescript"]
        self.assertEqual(sorted(c for c, _ in self.gates("typescript")), sorted(TS_GATES))
        self.assertTrue(all(cwd is None for _, cwd in self.gates("typescript")))
        self.assertEqual(prof["tools"], ["node", "npm"])
        self.assertEqual(prof["install"], ["npm install"])
        self.assertEqual(prof["kind"], "app")
        self.assertEqual(prof["combinesWith"], [])

    def test_renders_project_with_resolved_versions(self) -> None:
        folder = self.ok("typescript", "meu-ts")
        self.no_markers(folder)
        pkg = json.loads((folder / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(pkg["name"], "meu-ts")
        self.assertEqual(pkg["devDependencies"]["typescript"], "7.0.2")
        self.assertEqual(pkg["devDependencies"]["vitest"], "5.1.0")
        self.assertEqual(pkg["devDependencies"]["@biomejs/biome"], "2.6.6")
        self.assertTrue((folder / "tsconfig.json").is_file())
        self.assertIn("vitest", (folder / "src" / "index.test.ts").read_text(encoding="utf-8"))

    def test_readme_ci_gitignore(self) -> None:
        folder = self.ok("typescript", "meu-ts")
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("# meu-ts", readme)
        self.assertIn("Projeto de teste.", readme)
        ci = (folder / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        for gate in TS_GATES:
            self.assertIn(gate, readme)
            self.assertIn(gate, ci)
        self.assertIn("node_modules", (folder / ".gitignore").read_text(encoding="utf-8"))


class TauriProfileTests(ProfileCase):
    def test_gates_and_fields(self) -> None:
        prof = scaffold.load_profiles()["tauri"]
        gates = self.gates("tauri")
        self.assertEqual([c for c, cwd in gates if cwd is None], TS_GATES + [BUILD])
        self.assertEqual([c for c, cwd in gates if cwd == "src-tauri"], RUST_GATES)
        self.assertEqual(gates[-1], (BUILD, None))
        for tool in ("node", "npm", "cargo"):
            self.assertIn(tool, prof["tools"])
        self.assertEqual(prof["install"], ["npm install"])
        self.assertEqual(prof["alignMajor"], [{"from": "@tauri-apps/cli",
                                               "deps": ["tauri", "tauri-build", "@tauri-apps/api"]}])

    def test_aligns_major_of_tauri_cli(self) -> None:
        folder = self.ok("tauri", "meu-tauri")
        self.no_markers(folder)
        pkg = json.loads((folder / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(pkg["devDependencies"]["@tauri-apps/cli"], "2.12.4")
        self.assertEqual(pkg["dependencies"]["@tauri-apps/api"], "2.12.4")
        cargo = (folder / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
        self.assertIn('tauri = { version = "2.12.4"', cargo)
        self.assertIn('tauri-build = { version = "2.6.0"', cargo)
        stack = json.loads((folder / ".starcode" / "stack.json").read_text(encoding="utf-8"))
        self.assertEqual(stack["versions"]["@tauri-apps/api"]["version"], "2.12.4")

    def test_stops_without_stable_crate_in_cli_major(self) -> None:
        npm = {**REGISTRY["npm"],
               "@tauri-apps/cli": {"latest": "3.0.0", "versions": ["3.0.0", "2.12.4"]},
               "@tauri-apps/api": {"latest": "3.0.0", "versions": ["3.0.0"]}}
        self.fixture.write_text(json.dumps({**REGISTRY, "npm": npm}), encoding="utf-8")
        code, folder, err = self.new("tauri", "meu-tauri")
        self.assertNotEqual(code, 0)
        self.assertIn("tauri: crate sem versão estável no major 3", err)
        self.assertFalse(folder.exists())

    def test_renders_tauri_structure(self) -> None:
        folder = self.ok("tauri", "meu-tauri")
        tauri = folder / "src-tauri"
        conf = json.loads((tauri / "tauri.conf.json").read_text(encoding="utf-8"))
        self.assertEqual(conf["productName"], "meu-tauri")
        self.assertEqual(conf["build"]["frontendDist"], "../dist")
        self.assertEqual(conf["build"]["beforeBuildCommand"], "npm run build")
        lib = (tauri / "src" / "lib.rs").read_text(encoding="utf-8")
        self.assertIn("fn greet", lib)
        self.assertIn("generate_handler![greet]", lib)
        self.assertIn("#[test]", lib)
        self.assertIn("tauri_build::build()", (tauri / "build.rs").read_text(encoding="utf-8"))
        for icon in ("icon.png", "icon.ico"):
            self.assertGreater((tauri / "icons" / icon).stat().st_size, 0, icon)
        self.assertEqual((tauri / "icons" / "icon.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertTrue((tauri / "capabilities" / "default.json").is_file())
        self.assertIn("vitest", (folder / "src" / "greeting.test.ts").read_text(encoding="utf-8"))
        self.assertIn("invoke", (folder / "src" / "main.ts").read_text(encoding="utf-8"))
        self.assertTrue((folder / "index.html").is_file())
        self.assertTrue((folder / "vite.config.ts").is_file())

    def test_readme_ci_gitignore(self) -> None:
        folder = self.ok("tauri", "meu-tauri")
        readme = (folder / "README.md").read_text(encoding="utf-8")
        ci = (folder / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("# meu-tauri", readme)
        for gate in TS_GATES + RUST_GATES + [BUILD]:
            self.assertIn(gate, readme)
            self.assertIn(gate, ci)
        ignore = (folder / ".gitignore").read_text(encoding="utf-8")
        for entry in ("node_modules", "dist", "src-tauri/target"):
            self.assertIn(entry, ignore)


class BiomeExcludesSpecsTests(unittest.TestCase):
    def test_biome_excludes_specs_cache(self) -> None:
        for name in ("typescript", "tauri"):
            cfg = json.loads((PROFILES / name / "template" / "biome.json").read_text(encoding="utf-8"))
            self.assertIn("!.specs", cfg["files"]["includes"], name)


class NoHardcodedVersionTests(unittest.TestCase):
    def test_manifests_use_version_markers(self) -> None:
        for rel in ("typescript/template/package.json", "tauri/template/package.json",
                    "tauri/template/src-tauri/Cargo.toml"):
            text = (PROFILES / rel).read_text(encoding="utf-8")
            self.assertIn("{{version:", text, rel)


if __name__ == "__main__":
    unittest.main()
