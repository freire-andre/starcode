import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT

import build


def copy_source(dest: Path) -> None:
    for name in ("skills", "hooks", "scripts", "src", "schemas", "tools", "profiles"):
        shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
    if (ROOT / "evals").is_dir():
        shutil.copytree(ROOT / "evals", dest / "evals", ignore=shutil.ignore_patterns("results"))
    shutil.copy(ROOT / "VERSION", dest / "VERSION")


class BuildTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.src = Path(self._tmp.name) / "src"
        self.out = Path(self._tmp.name) / "out"
        copy_source(self.src)

    def tearDown(self):
        self._tmp.cleanup()

    def test_build_gera_dist_orca(self):  # C33
        build.build(self.src, self.out)
        orca = self.out / "dist" / "orca"
        manifest = json.loads((orca / "orca-plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())
        self.assertTrue((orca / "src" / "panel.tsx").is_file())
        self.assertTrue((orca / "src" / "worker.ts").is_file())
        self.assertTrue((orca / "src" / "scene.ts").is_file())
        self.assertFalse((orca / "src" / "scene.html").exists())
        self.assertFalse((orca / ".orca").exists())
        self.assertEqual(list(orca.rglob("*.test.ts*")), [])
        scripts = {p.relative_to(orca / "scripts").as_posix() for p in (orca / "scripts").rglob("*.py")}
        self.assertTrue({"ponte.py", "crew_live.py", "handoff.py", "starcode_common.py",
                         "config/validate_config.py"} <= scripts, scripts)
        self.assertEqual((orca / "scripts" / "ponte.py").read_bytes(), (ROOT / "scripts" / "ponte.py").read_bytes())
        self.assertNotIn("orca", build.CLIS)
        self.assertFalse((self.out / "dist" / "claude" / "skills" / "orca").exists())

    def test_dist_orca_snapshot_le_a_tripulacao(self):
        build.build(self.src, self.out)
        orca = self.out / "dist" / "orca"
        self.assertTrue((orca / "crew.json").is_file())
        self.assertEqual(list(orca.rglob("__pycache__")), [])
        repo = Path(self._tmp.name) / "repo"
        (repo / ".starcode").mkdir(parents=True)
        (repo / ".specs").mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)  # ponte.py exige um worktree git
        (repo / ".starcode" / "config.json").write_text("{}", encoding="utf-8")
        res = subprocess.run([sys.executable, "-B", str(orca / "scripts" / "ponte.py"), "snapshot",
                              "--path", str(repo), "--json"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stderr)
        snap = json.loads(res.stdout)
        self.assertEqual(snap["errors"], [])
        self.assertEqual(len(snap["crew"]), 12)
        self.assertEqual(list(orca.rglob("__pycache__")), [])

    def test_build_check_cobre_dist_orca(self):  # C33
        build.build(self.src, self.out)
        self.assertEqual(build.compare(self.out, self.out), [])
        other = Path(self._tmp.name) / "other"
        build.build(self.src, other)
        (other / "dist" / "orca" / "src" / "panel.tsx").write_text("// editado à mão\n", encoding="utf-8")
        (other / "dist" / "orca" / "scripts" / "ponte.py").unlink()
        problems = build.compare(self.out, other)
        self.assertIn("diferente: dist/orca/src/panel.tsx", problems)
        self.assertIn("faltando: dist/orca/scripts/ponte.py", problems)

    def test_repo_dist_is_up_to_date(self):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), "--check"],
                             capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stdout)

    def test_build_copies_profiles_and_new_skills(self):
        build.build(self.src, self.out)
        names = sorted(p.name for p in (ROOT / "profiles").iterdir() if p.is_dir())
        self.assertEqual(len(names), 7, names)
        for cli in build.CLIS:
            base = self.out / "dist" / cli
            for name in names:
                self.assertTrue((base / "profiles" / name / "profile.yaml").is_file(), f"{cli}/{name}")
                self.assertTrue((base / "profiles" / name / "template").is_dir(), f"{cli}/{name}")
            for skill in ("uhura", "scotty", "nova-missao"):
                self.assertTrue((base / "skills" / skill / "SKILL.md").is_file(), f"{cli}/{skill}")

    def test_build_fase9_skills_and_scripts_in_all_clis(self):  # C35
        build.build(self.src, self.out)
        for cli in build.CLIS:
            base = self.out / "dist" / cli
            for skill in ("worf", "guinan", "diagnostico"):
                self.assertTrue((base / "skills" / skill / "SKILL.md").is_file(), f"{cli}/{skill}")
            for rel in ("scripts/review/review_gate.py", "scripts/review/post_review.py",
                        "scripts/review/scan_bypasses.py", "scripts/harness/track_a_correctness.py",
                        "scripts/harness/references/PROTOCOL.md", "scripts/lessons.py", "scripts/diagnostico.py"):
                self.assertTrue((base / rel).is_file(), f"{cli}/{rel}")

    def test_build_leva_telas_aos_4_clis(self):
        build.build(self.src, self.out)
        for cli in build.CLIS:
            base = self.out / "dist" / cli
            for rel in ("scripts/screens.py", "scripts/gates/images.py", "briefs/screens-verify.md"):
                self.assertTrue((base / rel).is_file(), f"{cli}/{rel}")
            for skill, termo in (("spock", "captures/"), ("laforge", "scripts/screens.py"), ("q", "screens-verify")):
                text = (base / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(termo, text, f"{cli}/{skill}")

    def test_check_flags_stale_profile(self):
        build.build(self.src, self.out)
        other = Path(self._tmp.name) / "other"
        build.build(self.src, other)
        (other / "dist" / "claude" / "profiles" / "rust" / "profile.yaml").write_text("name: rust\n", encoding="utf-8")
        problems = build.compare(self.out, other)
        self.assertTrue(any("dist/claude/profiles/rust/profile.yaml" in p for p in problems), problems[:5])

    def test_layout_per_cli(self):
        build.build(self.src, self.out)
        dist = self.out / "dist"
        self.assertTrue((dist / "claude" / ".claude-plugin" / "plugin.json").exists())
        self.assertTrue((dist / "claude" / "hooks" / "hooks.json").exists())
        self.assertTrue((dist / "codex" / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue((dist / "antigravity" / "plugin.json").exists())
        self.assertTrue((dist / "opencode" / "commands" / "sc-engajar.md").exists())
        # Fase 5: Codex e Antigravity têm hooks próprios; OpenCode não tem hooks.json.
        self.assertTrue((dist / "codex" / "hooks" / "hooks.json").exists())
        self.assertTrue((dist / "antigravity" / "hooks.json").exists())
        self.assertFalse((dist / "opencode" / "hooks.json").exists())
        self.assertFalse((dist / "claude" / "plugin.json").exists())
        self.assertFalse((dist / "antigravity" / ".claude-plugin").exists())

    def test_antigravity_rule_has_always_on_trigger(self):
        build.build(self.src, self.out)
        rule = (self.out / "dist" / "antigravity" / "rules" / "starcode.md").read_text(encoding="utf-8")
        self.assertTrue(rule.startswith("---\ntrigger: always_on\n---\n"), rule[:80])
        body = (self.src / "src" / "context" / "STARCODE.md").read_text(encoding="utf-8")
        self.assertTrue(rule.endswith(body))

    def test_placeholders_rendered_per_cli(self):
        build.build(self.src, self.out)
        claude = (self.out / "dist" / "claude" / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        codex = (self.out / "dist" / "codex" / "skills" / "engajar" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("${CLAUDE_SKILL_DIR}/../..", claude)
        self.assertNotIn("CLAUDE_SKILL_DIR", codex)
        self.assertIn("Número Um, relatório.", claude)
        for text in (claude, codex):
            self.assertNotIn("{{", text)

    def test_crew_json_lists_only_available(self):
        build.build(self.src, self.out)
        crew = json.loads((self.out / "dist" / "claude" / "crew.json").read_text(encoding="utf-8"))
        self.assertEqual(crew["available"][:4], ["picard", "spock", "troi", "data"])
        self.assertIn("q", crew["available"])  # Phase 3: skills/q exists
        self.assertIn("uhura", crew["available"])  # Phase 8: skills/uhura exists
        self.assertIn("worf", crew["available"])  # Phase 9: skills/worf exists
        self.assertEqual(crew["version"], (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_crew_json_carries_cost_tiers(self):
        build.build(self.src, self.out)
        crew = json.loads((self.out / "dist" / "claude" / "crew.json").read_text(encoding="utf-8"))
        self.assertEqual(crew["costTiers"]["claude-opus-5-5"], "$$$")
        self.assertEqual(crew["costTiers"]["claude-haiku-5-5"], "$")
        self.assertTrue(set(crew["costTiers"]) <= set(crew["families"]))

    def test_cost_tier_from_map_free_suffix_and_unknown(self):
        import starcode_common as sc

        tiers = {"claude-opus-5-5": "$$$", "x:free": "$"}
        self.assertEqual(sc.cost_tier("claude-opus-5-5", tiers), "$$$")
        self.assertEqual(sc.cost_tier("x:free", tiers), "$")  # the map wins
        self.assertEqual(sc.cost_tier("openrouter/nvidia/y:free", tiers), "grátis")
        self.assertEqual(sc.cost_tier("some-model-free", tiers), "grátis")
        self.assertEqual(sc.cost_tier("mystery", tiers), "?")
        self.assertEqual(sc.cost_tier("mystery", None), "?")

    def test_claude_hooks_use_plugin_root(self):
        build.build(self.src, self.out)
        hooks = json.loads((self.out / "dist" / "claude" / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        cmds = [h["command"] for e in hooks["hooks"]["PreToolUse"] for h in e["hooks"]]
        self.assertTrue(all("${CLAUDE_PLUGIN_ROOT}" in c for c in cmds))
        self.assertTrue(any("git_guard.py" in c for c in cmds) and any("secret_scan.py" in c for c in cmds))

    # --- Fase 5 T1: hooks.json do Codex e do Antigravity ---

    def _hooks_json(self, *parts):
        return json.loads(self.out.joinpath("dist", *parts).read_text(encoding="utf-8"))

    def test_codex_hooks_json_registers_guards_and_banner(self):  # C1
        build.build(self.src, self.out)
        hooks = self._hooks_json("codex", "hooks", "hooks.json")["hooks"]
        pre = hooks["PreToolUse"]
        self.assertEqual([e["matcher"] for e in pre], ["Bash", "Bash"])  # 2nd group: crew_hook (F7-14)
        cmds = [(h["command"], h["timeout"]) for h in pre[0]["hooks"]]
        self.assertEqual(cmds, [
            ('python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/git_guard.py"', 15),
            ('python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/secret_scan.py"', 30)])
        start = hooks["SessionStart"]
        self.assertEqual(start[0]["matcher"], "startup|resume|clear|compact")
        self.assertEqual([(h["command"], h["timeout"]) for h in start[0]["hooks"]],
                         [('python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/banner.py" --full --cli codex', 30)])

    def test_antigravity_hooks_json_native_format(self):  # C2
        build.build(self.src, self.out)
        data = self._hooks_json("antigravity", "hooks.json")
        root = "{{STARCODE_ROOT}}/hooks/scripts"
        guard = data["starcode-guard"]["PreToolUse"]
        self.assertEqual([e["matcher"] for e in guard], ["run_command"])
        self.assertEqual([h["command"] for h in guard[0]["hooks"]], [
            f"python {root}/git_guard.py --agy", f"python {root}/secret_scan.py --agy"])
        banner = data["starcode-banner"]["SessionStart"]
        self.assertEqual([h["command"] for h in banner], [f"python {root}/banner.py --agy --full --cli antigravity"])
        self.assertTrue(all(h["type"] == "command" for h in guard[0]["hooks"] + banner))

    def test_antigravity_hook_commands_without_quotes(self):  # C27
        build.build(self.src, self.out)
        text = (self.out / "dist" / "antigravity" / "hooks.json").read_text(encoding="utf-8")
        data = json.loads(text)
        cmds = [h["command"] for h in data["starcode-guard"]["PreToolUse"][0]["hooks"]]
        cmds += [h["command"] for h in data["starcode-banner"]["SessionStart"]]
        self.assertEqual(len(cmds), 3)
        for c in cmds:
            self.assertNotIn('"', c)
            self.assertTrue(c.startswith("python {{STARCODE_ROOT}}/hooks/scripts/"))

    def test_dist_has_no_machine_absolute_paths(self):  # C3
        build.build(self.src, self.out)
        bad = re.compile(r"(?<![\w\\])[A-Za-z]:[\\/]|/home/|/Users/")
        for path in (self.out / "dist").rglob("*"):
            if path.is_file() and path.suffix in {".json", ".md", ".py", ".yaml", ".yml", ".toml", ".js", ".txt"}:
                m = bad.search(path.read_text(encoding="utf-8", errors="ignore"))
                self.assertIsNone(m, f"{path.relative_to(self.out)}: {m and m.group(0)}")

    def test_session_start_banner_runs_in_hook_mode(self):  # C4
        build.build(self.src, self.out)
        codex = self._hooks_json("codex", "hooks", "hooks.json")["hooks"]["SessionStart"][0]["hooks"]
        agy = self._hooks_json("antigravity", "hooks.json")["starcode-banner"]["SessionStart"]
        for h in codex + agy:
            self.assertIn("banner.py", h["command"])
            self.assertIn("--full", h["command"])
            self.assertNotIn("--text", h["command"])

    def test_banner_hook_mode_matches_text_per_cli(self):  # C16 (R10: hook = --full --text)
        script = ROOT / "hooks" / "scripts" / "banner.py"
        def run(*args, payload="{}", cwd_args=("--cwd", str(ROOT)), cwd=None):
            r = subprocess.run([sys.executable, str(script), *args, *cwd_args], input=payload, cwd=cwd,
                               capture_output=True, text=True, encoding="utf-8", timeout=60)
            return json.loads(r.stdout) if "--text" not in args else r.stdout.strip()
        text = run("--full", "--text", "--cli", "codex")
        ctx = run("--full", "--cli", "codex")["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(ctx.strip(), text)
        text = run("--full", "--text", "--cli", "antigravity")
        msg = run("--agy", "--full", "--cli", "antigravity")["injectSteps"][0]["ephemeralMessage"]
        self.assertEqual(msg.strip(), text)
        # Antigravity sem cwd no payload: workspacePaths[0] é o repositório
        payload = json.dumps({"workspacePaths": [str(ROOT)]})
        msg = run("--agy", "--full", "--cli", "antigravity", payload=payload, cwd_args=(),
                  cwd=tempfile.gettempdir())["injectSteps"][0]["ephemeralMessage"]
        self.assertNotIn("fora de um repositório Git", msg)
        self.assertEqual(msg.strip(), text)

    def test_unknown_placeholder_fails(self):
        skill = self.src / "skills" / "setup" / "SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\n{{NOPE}}\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_plugin_root_placeholder_only_in_skill_md(self):
        ref = self.src / "skills" / "engajar" / "references" / "git-modes.md"
        ref.write_text(ref.read_text(encoding="utf-8") + "\n{{PLUGIN_ROOT}}\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    # --- Fase 4 T1: matriz de recursos e marcadores {{CMD}} / {{CLI}} ---

    EXTRAS = ("hooks", "banner_hook", "linear_mcp", "subagent_model", "orca_worker")

    def _caps(self, cli):
        return json.loads((self.out / "dist" / cli / "capabilities.json").read_text(encoding="utf-8"))

    def test_capabilities_json_per_cli(self):  # C1
        build.build(self.src, self.out)
        for cli in build.CLIS:
            data = self._caps(cli)
            self.assertEqual(set(data["extras"]), set(self.EXTRAS), cli)
            for name, e in data["extras"].items():
                self.assertIn(e["status"], ("ok", "unavailable"))
                if e["status"] == "unavailable":
                    self.assertTrue(e.get("fallback"), f"{cli}.{name}")
        claude = self._caps("claude")
        self.assertTrue(all(e["status"] == "ok" for e in claude["extras"].values()))
        codex = self._caps("codex")
        self.assertEqual(codex["extras"]["orca_worker"]["status"], "ok")
        self.assertEqual(codex["extras"]["hooks"]["status"], "ok")
        self.assertIn("sem evento", self._caps("opencode")["extras"]["banner_hook"]["fallback"])

    def test_unavailable_extra_without_fallback_fails(self):  # C2
        path = self.src / "src" / "capabilities.yaml"
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if "fallback:" not in ln]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_blank_fallback_fails(self):  # R1/R2: a whitespace-only fallback is no fallback
        path = self.src / "src" / "capabilities.yaml"
        lines = path.read_text(encoding="utf-8").splitlines()
        idx = next(i for i, ln in enumerate(lines) if ln.strip().startswith("fallback:"))
        indent = lines[idx][: len(lines[idx]) - len(lines[idx].lstrip())]
        lines[idx] = f'{indent}fallback: "   "'
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_cmd_and_cli_placeholders_per_cli(self):  # C3
        files = ("skills/setup/SKILL.md", "skills/engajar/references/git-modes.md")
        for rel in files:
            f = self.src / rel
            f.write_text(f.read_text(encoding="utf-8") + "\nX {{CMD:engajar}} Y {{CLI}}\n", encoding="utf-8")
        build.build(self.src, self.out)
        expected = {
            "claude": "X /starcode:engajar Y claude",
            "opencode": "X /sc-engajar Y opencode",
            "codex": "X a skill `engajar` do StarCode Y codex",
            "antigravity": "X a skill `engajar` do StarCode Y antigravity",
        }
        for cli, line in expected.items():
            for rel in files:
                got = (self.out / "dist" / cli / rel).read_text(encoding="utf-8")
                self.assertIn(line, got, f"{cli} {rel}")

    def test_undeclared_skill_fails(self):
        (self.src / "skills" / "rogue").mkdir()
        (self.src / "skills" / "rogue" / "SKILL.md").write_text("---\nname: rogue\ndescription: x\n---\n",
                                                                encoding="utf-8")
        with self.assertRaises(build.BuildError):
            build.build(self.src, self.out)

    def test_check_detects_hand_edit(self):
        build.build(self.src, self.out)
        target = self.out / "dist" / "claude" / "skills" / "setup" / "SKILL.md"
        target.write_text("edited by hand", encoding="utf-8")
        expected = Path(self._tmp.name) / "expected"
        build.build(self.src, expected)
        problems = build.compare(expected, self.out)
        self.assertEqual(problems, ["diferente: dist/claude/skills/setup/SKILL.md"])

    def test_user_invocation_adds_claude_frontmatter(self):
        text = build.claude_frontmatter("---\nname: x\ndescription: y\n---\n\nbody\n", "user")
        self.assertIn("disable-model-invocation: true\n---\n", text)
        self.assertEqual(build.claude_frontmatter("---\nname: x\n---\n", "both"), "---\nname: x\n---\n")

    def test_build_emits_execution_skills(self):
        build.build(self.src, self.out)
        claude = self.out / "dist" / "claude"
        for skill in ("laforge", "mccoy", "q"):
            text = (claude / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn(f"name: {skill}", text)
            self.assertNotIn("{{", text.split("---", 2)[2].replace("{{spec}}", ""))
        brief = (claude / "briefs" / "q-verify.md").read_text(encoding="utf-8")
        self.assertIn("{{output}}", brief)  # filled at dispatch time by scripts/dispatch.py
        self.assertTrue((claude / "scripts" / "dispatch.py").is_file())
        self.assertTrue((claude / "skills" / "engajar" / "references" / "execute.md").is_file())

    def test_routing_and_decisions_cover_phase3(self):
        routing = ROOT / "evals" / "routing"
        for skill, case in (("laforge", "pos-laforge-ticket"), ("mccoy", "pos-mccoy-bug"), ("q", "pos-q-verify")):
            text = (routing / case / "case.yaml").read_text(encoding="utf-8")
            self.assertIn(f'input_match: "starcode:{skill}"', text)
        decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("## Decisões da Fase 3", decisions)
        self.assertIn("### F3-1:", decisions)

    def test_version_is_1_2_0_in_all_manifests(self):  # C6
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "1.5.1")
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["plugins"][0]["version"], "1.5.1")
        for rel in ("dist/claude/.claude-plugin/plugin.json", "dist/codex/.codex-plugin/plugin.json",
                    "dist/antigravity/plugin.json"):
            data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
            self.assertEqual(data["version"], "1.5.1", rel)

    def test_check_fails_when_manifest_version_diverges(self):  # C7
        script = self.src / "tools" / "build.py"
        res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stdout)
        res = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(res.returncode, 0, res.stdout)
        for rel, edit in (
            (".claude-plugin/marketplace.json", lambda d: d["plugins"][0].update(version="9.9.9")),
            ("dist/claude/.claude-plugin/plugin.json", lambda d: d.update(version="9.9.9")),
            ("dist/codex/.codex-plugin/plugin.json", lambda d: d.update(version="9.9.9")),
            ("dist/antigravity/plugin.json", lambda d: d.update(version="9.9.9")),
        ):
            path = self.src / rel
            original = path.read_text(encoding="utf-8")
            data = json.loads(original)
            edit(data)
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            res = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True,
                                 encoding="utf-8")
            self.assertNotEqual(res.returncode, 0, rel)
            path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
