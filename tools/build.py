"""StarCode generator: writes one adapter folder per CLI into dist/ from the single source (D8, ADR-0001).

Python stdlib only. Nothing in dist/ is edited by hand.
  python tools/build.py           regenerate dist/ and the marketplace manifests
  python tools/build.py --check   build into a temp dir and fail (exit 1) if dist/ is out of date

Source: skills/, hooks/scripts/, scripts/, src/crew.yaml, src/context/STARCODE.md, src/briefs/, schemas/, evals/, VERSION.
Only crew members whose skill exists are emitted (crew.json "available"); plugin validation passes at
every phase. Hooks are registered only for Claude in Phase 1 (other CLIs: Phase 5).

Placeholders allowed in skills (anything else in {{...}} is an error):
  {{PLUGIN_ROOT}}           in SKILL.md: how to resolve the literal token <plugin-root> in that CLI
  {{VOICE_OPEN:<member>}}   catchphrases from crew.yaml
  {{VOICE_CLOSE:<member>}}
  {{CMD:<skill>}}           how to invoke a skill in that CLI (/starcode:<skill>, /sc-<skill>, or prose)
  {{CLI}}                   the CLI name
Capabilities: src/capabilities.yaml -> dist/<cli>/capabilities.json (unavailable extras need a fallback).
"""
from __future__ import annotations

import argparse
import filecmp
import json
import re
import shutil
import struct
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import miniyaml  # noqa: E402

NAME = "starcode"
DESC = ("StarCode: spec-driven development with a Star Trek crew (Picard, Spock, Troi, Data, LaForge, "
        "McCoy, Q) for Orca IDE and Linear.")
AUTHOR = {"name": "Andre Freire"}
CLIS = ("claude", "codex", "antigravity", "opencode")
PLUGIN_ROOT_DECL = {
    "claude": "`${CLAUDE_SKILL_DIR}/../..` (two directories above this skill's directory)",
    "codex": "the folder two directories above this skill's directory",
    "antigravity": "the folder two directories above this skill's directory",
    "opencode": "the folder two directories above this skill's directory",
}
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)(?::([a-z0-9-]+))?\}\}")
IGNORED_PARTS = {"__pycache__", "results", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


class BuildError(Exception):
    pass


# --- io helpers -----------------------------------------------------------------------------

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: object) -> None:
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def copy_tree(src: Path, dest: Path) -> None:
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src)
        if any(part in IGNORED_PARTS for part in rel.parts) or f.suffix in SKIP_SUFFIXES or not f.is_file():
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f.read_bytes())


def write_icon(path: Path, size: int = 512) -> None:
    """Square PNG (solid StarCode blue) written with the stdlib only."""
    raw = (bytes([0]) + bytes((0x1F, 0x4E, 0x9A)) * size) * size

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (bytes([137, 80, 78, 71, 13, 10, 26, 10])
           + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)


# --- source model ---------------------------------------------------------------------------

def load_source(root: Path) -> dict:
    crew_doc = miniyaml.loads((root / "src" / "crew.yaml").read_text(encoding="utf-8"))
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise BuildError(f"VERSION inválida: {version!r}")
    crew = crew_doc.get("crew") or {}
    extra = crew_doc.get("skills") or {}
    skill_owner: dict[str, tuple[str, dict]] = {}
    for key, m in crew.items():
        for field in ("name", "skill", "invocation", "release", "default", "voice"):
            if field not in m:
                raise BuildError(f"crew.yaml: {key} sem o campo {field!r}")
        if m["invocation"] not in ("user", "model", "both"):
            raise BuildError(f"crew.yaml: {key}.invocation inválido: {m['invocation']!r}")
        skill_owner[m["skill"]] = (key, m)
    for skill, s in extra.items():
        if s.get("owner") not in crew:
            raise BuildError(f"crew.yaml: skill {skill} com owner desconhecido {s.get('owner')!r}")
        skill_owner[skill] = (s["owner"], {"invocation": s.get("invocation", "both")})

    skills: dict[str, dict] = {}
    skills_dir = root / "skills"
    for d in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            raise BuildError(f"skills/{d.name}: falta SKILL.md")
        if d.name not in skill_owner:
            raise BuildError(f"skills/{d.name}: skill não declarada em src/crew.yaml (crew.*.skill ou skills.*)")
        text = skill_md.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not fm:
            raise BuildError(f"skills/{d.name}/SKILL.md: frontmatter ausente")
        meta = dict(re.findall(r"^([a-z-]+):\s*(.+)$", fm.group(1), re.M))
        if meta.get("name") != d.name:
            raise BuildError(f"skills/{d.name}/SKILL.md: name {meta.get('name')!r} difere da pasta")
        if not meta.get("description"):
            raise BuildError(f"skills/{d.name}/SKILL.md: description ausente")
        skills[d.name] = {"dir": d, "invocation": skill_owner[d.name][1]["invocation"]}
    available = [k for k, m in crew.items() if m["skill"] in skills]
    return {"crew_doc": crew_doc, "crew": crew, "skills": skills, "available": available, "version": version,
            "capabilities": load_capabilities(root)}


CAPABILITY_EXTRAS = ("hooks", "banner_hook", "linear_mcp", "subagent_model", "orca_worker")


def load_capabilities(root: Path) -> dict:
    path = root / "src" / "capabilities.yaml"
    if not path.exists():
        raise BuildError("falta src/capabilities.yaml")
    doc = miniyaml.loads(path.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for cli in CLIS:
        extras = doc.get(cli)
        if not isinstance(extras, dict):
            raise BuildError(f"capabilities.yaml: CLI {cli!r} ausente")
        for name in CAPABILITY_EXTRAS:
            e = extras.get(name)
            if not isinstance(e, dict):
                raise BuildError(f"capabilities.yaml: {cli}.{name} ausente")
            if e.get("status") not in ("ok", "unavailable"):
                raise BuildError(f"capabilities.yaml: {cli}.{name}.status inválido: {e.get('status')!r}")
            if e["status"] == "unavailable" and not str(e.get("fallback") or "").strip():
                raise BuildError(f"capabilities.yaml: {cli}.{name} unavailable sem fallback")
        result[cli] = {name: dict(extras[name]) for name in CAPABILITY_EXTRAS}
    return result


def cmd_ref(cli: str, skill: str) -> str:
    if cli == "claude":
        return f"/starcode:{skill}"
    if cli == "opencode":
        return f"/sc-{skill}"
    return f"a skill `{skill}` do StarCode"


def render(text: str, cli: str, crew: dict, where: str, is_skill_md: bool) -> str:
    def sub(m: re.Match) -> str:
        name, arg = m.group(1), m.group(2)
        if name == "PLUGIN_ROOT" and arg is None:
            if not is_skill_md:
                raise BuildError(f"{where}: {{{{PLUGIN_ROOT}}}} só é permitido em SKILL.md; use <plugin-root>")
            return PLUGIN_ROOT_DECL[cli]
        if name in ("VOICE_OPEN", "VOICE_CLOSE") and arg:
            if arg not in crew:
                raise BuildError(f"{where}: tripulante desconhecido em {m.group(0)}")
            return crew[arg]["voice"]["open" if name == "VOICE_OPEN" else "close"]
        if name == "CMD" and arg:
            return cmd_ref(cli, arg)
        if name == "CLI" and arg is None:
            return cli
        raise BuildError(f"{where}: placeholder desconhecido {m.group(0)}")

    return PLACEHOLDER.sub(sub, text)


def emit_skills(src: dict, cli: str, out: Path) -> None:
    for name, info in src["skills"].items():
        for f in sorted(info["dir"].rglob("*")):
            rel = f.relative_to(info["dir"])
            if not f.is_file() or any(p in IGNORED_PARTS for p in rel.parts) or f.suffix in SKIP_SUFFIXES:
                continue
            target = out / "skills" / name / rel
            if f.suffix == ".md":
                text = render(f.read_text(encoding="utf-8"), cli, src["crew"], f"skills/{name}/{rel.as_posix()}",
                              rel.as_posix() == "SKILL.md")
                if rel.as_posix() == "SKILL.md" and cli == "claude":
                    text = claude_header_rule(text)
                    text = claude_frontmatter(text, info["invocation"])
                write(target, text)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(f.read_bytes())


HEADER_RULE_CLAUDE = ("In Claude Code the StarCode hook already showed your header and marks you as working: "
                      "do not run crew_live.py start/stop and do not repeat the header.")
HEADER_PARAGRAPHS = (
    re.compile(r"\*\*Header first \(F6-6\):\*\*.*?\n\n", re.S),  # troi, spock, data, laforge, mccoy, q
    re.compile(r"First run `python \"<plugin-root>/scripts/crew_live\.py\" start picard.*?stop picard`\.\n\n", re.S),
)


def claude_header_rule(text: str) -> str:
    """Claude only (F7-12): the hook shows the header and the status, so the F6-6 instruction becomes one line."""
    for pattern in HEADER_PARAGRAPHS:
        text = pattern.sub(lambda _m: HEADER_RULE_CLAUDE + "\n\n", text)
    return text


def claude_frontmatter(text: str, invocation: str) -> str:
    extra = {"user": "disable-model-invocation: true\n", "model": "user-invocable: false\n"}.get(invocation, "")
    if not extra:
        return text
    head, sep, body = text.partition("\n---\n")
    return head + "\n" + extra.rstrip("\n") + sep + body


def emit_common(src: dict, out: Path, root: Path, cli: str) -> None:
    """Runtime pieces every adapter needs: scripts, hook scripts, core context, crew data, schemas."""
    copy_tree(root / "scripts", out / "scripts")
    copy_tree(root / "hooks" / "scripts", out / "hooks" / "scripts")
    write(out / "context" / "STARCODE.md", (root / "src" / "context" / "STARCODE.md").read_text(encoding="utf-8"))
    copy_tree(root / "schemas", out / "schemas")
    if (root / "src" / "briefs").is_dir():  # worker briefs (q-verify.md), read by scripts/dispatch.py
        copy_tree(root / "src" / "briefs", out / "briefs")
    crew_json = {
        "schemaVersion": src["crew_doc"].get("schemaVersion", 1),
        "version": src["version"],
        "families": src["crew_doc"].get("families", {}),
        "costTiers": src["crew_doc"].get("costTiers", {}),
        "available": src["available"],
        "crew": src["crew"],
    }
    write_json(out / "crew.json", crew_json)
    write_json(out / "capabilities.json", {"schemaVersion": 1, "cli": cli, "extras": src["capabilities"][cli]})


def base_hooks() -> dict:
    root = "${CLAUDE_PLUGIN_ROOT}"
    return {"hooks": {
        "PreToolUse": [{"matcher": "Bash", "hooks": [
            {"type": "command", "command": f'python "{root}/hooks/scripts/git_guard.py"', "timeout": 15},
            {"type": "command", "command": f'python "{root}/hooks/scripts/secret_scan.py"', "timeout": 30},
        ]}],
        "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [
            {"type": "command", "command": f'python "{root}/hooks/scripts/banner.py"', "timeout": 30},
        ]}],
    }}


def claude_hooks() -> dict:
    """Claude also gets crew_hook.py (F7-12): header and live status without depending on the model."""
    hooks = base_hooks()
    crew = [{"type": "command", "command": 'python "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/crew_hook.py"', "timeout": 10}]
    events = hooks["hooks"]
    events["PreToolUse"].append({"matcher": "Skill", "hooks": crew})
    events["UserPromptExpansion"] = [{"matcher": "starcode:.*", "hooks": crew}]
    events["PostToolUse"] = [{"matcher": "*", "hooks": crew}]
    for name in ("Stop", "UserPromptSubmit", "SessionEnd"):
        events[name] = [{"hooks": crew}]
    return hooks


def codex_hooks() -> dict:
    hooks = base_hooks()
    root = "${CLAUDE_PLUGIN_ROOT}"
    hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"] = f'python "{root}/hooks/scripts/banner.py" --full --cli codex'
    return hooks


def antigravity_hooks() -> dict:
    root = "{{STARCODE_ROOT}}/hooks/scripts"  # sem aspas (o agy as passa literais ao python); install_local troca pelo caminho absoluto
    return {
        "starcode-guard": {"PreToolUse": [{"matcher": "run_command", "hooks": [
            {"type": "command", "command": f"python {root}/git_guard.py --agy", "timeout": 15},
            {"type": "command", "command": f"python {root}/secret_scan.py --agy", "timeout": 30},
        ]}]},
        "starcode-banner": {"SessionStart": [
            {"type": "command", "command": f"python {root}/banner.py --agy --full --cli antigravity", "timeout": 30},
        ]},
    }


def build_claude(src: dict, out: Path, root: Path) -> None:
    write_json(out / ".claude-plugin" / "plugin.json",
               {"name": NAME, "version": src["version"], "description": DESC, "author": AUTHOR})
    write_icon(out / ".claude-plugin" / "icon.png")
    emit_skills(src, "claude", out)
    emit_common(src, out, root, "claude")
    write_json(out / "hooks" / "hooks.json", claude_hooks())
    write(out / "context" / "CLAUDE.snippet.md",
          "## StarCode\n\nEste repositório usa o StarCode. Comece com `/starcode:engajar`; configure com "
          "`/starcode:setup`.\nRegras do núcleo: `context/STARCODE.md` do plugin. Persona só no chat; "
          "artefatos neutros.\n")
    if (root / "evals").is_dir():
        copy_tree(root / "evals", out / "evals")


def build_codex(src: dict, out: Path, root: Path) -> None:
    write_json(out / ".codex-plugin" / "plugin.json",
               {"name": NAME, "version": src["version"], "description": DESC, "author": AUTHOR,
                "interface": {"displayName": "StarCode", "shortDescription": "SDD com a tripulação"}})
    emit_skills(src, "codex", out)
    emit_common(src, out, root, "codex")
    write_json(out / "hooks" / "hooks.json", codex_hooks())
    write(out / "AGENTS.md", (root / "src" / "context" / "STARCODE.md").read_text(encoding="utf-8"))


def build_antigravity(src: dict, out: Path, root: Path) -> None:
    write_json(out / "plugin.json",
               {"name": NAME, "version": src["version"], "description": DESC, "author": AUTHOR["name"]})
    emit_skills(src, "antigravity", out)
    emit_common(src, out, root, "antigravity")
    write_json(out / "hooks.json", antigravity_hooks())
    # agy exige frontmatter com trigger válido; sem ele a regra nunca se aplica.
    write(out / "rules" / "starcode.md",
          "---\ntrigger: always_on\n---\n" + (root / "src" / "context" / "STARCODE.md").read_text(encoding="utf-8"))


def build_opencode(src: dict, out: Path, root: Path) -> None:
    emit_skills(src, "opencode", out)
    emit_common(src, out, root, "opencode")
    write(out / "plugins" / "starcode.js", (root / "hooks" / "opencode" / "starcode.js").read_text(encoding="utf-8"))
    for name in src["skills"]:
        write(out / "commands" / f"sc-{name}.md",
              f"---\ndescription: StarCode {name} (/sc-{name})\n---\n\n"
              f"Load and follow the StarCode skill `{name}`. Arguments: $ARGUMENTS\n")


BUILDERS = {"claude": build_claude, "codex": build_codex, "antigravity": build_antigravity,
            "opencode": build_opencode}


def build(root: Path, dest_root: Path) -> list[Path]:
    """Build everything under dest_root (mirrors the repo layout). Returns written top-level paths."""
    src = load_source(root)
    dist = dest_root / "dist"
    for cli in CLIS:
        BUILDERS[cli](src, dist / cli, root)
    write_json(dest_root / ".claude-plugin" / "marketplace.json", {
        "name": NAME,
        "description": "StarCode private marketplace.",
        "owner": AUTHOR,
        "plugins": [{"name": NAME, "source": "./dist/claude", "description": DESC, "version": src["version"]}],
    })
    write_json(dest_root / ".agents" / "plugins" / "marketplace.json", {
        "name": NAME,
        "interface": {"displayName": "StarCode"},
        "plugins": [{"name": NAME, "source": {"source": "local", "path": "./dist/codex"}}],
    })
    return [dist, dest_root / ".claude-plugin" / "marketplace.json", dest_root / ".agents" / "plugins" / "marketplace.json"]


def _files(base: Path) -> set[str]:
    if not base.exists():
        return set()
    if base.is_file():
        return {""}
    return {p.relative_to(base).as_posix() for p in base.rglob("*")
            if p.is_file() and not any(part in IGNORED_PARTS for part in p.relative_to(base).parts)
            and p.suffix not in SKIP_SUFFIXES}


def compare(expected_root: Path, actual_root: Path) -> list[str]:
    problems = []
    for rel in ("dist", ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        exp, act = expected_root / rel, actual_root / rel
        exp_files, act_files = _files(exp), _files(act)
        for f in sorted(exp_files - act_files):
            problems.append(f"faltando: {rel}/{f}".rstrip("/"))
        for f in sorted(act_files - exp_files):
            problems.append(f"sobrando (não gerado): {rel}/{f}".rstrip("/"))
        for f in sorted(exp_files & act_files):
            e, a = (exp / f if f else exp), (act / f if f else act)
            if not filecmp.cmp(e, a, shallow=False):
                problems.append(f"diferente: {rel}/{f}".rstrip("/"))
    return problems


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Gera dist/<cli>/ a partir da fonte única do StarCode.")
    parser.add_argument("--check", action="store_true", help="falha se dist/ estiver desatualizado")
    args = parser.parse_args(argv)
    try:
        if args.check:
            with tempfile.TemporaryDirectory(prefix="starcode-build-") as tmp:
                build(ROOT, Path(tmp))
                problems = compare(Path(tmp), ROOT)
            if problems:
                print("build --check: FALHOU, dist/ desatualizado (rode python tools/build.py):")
                for p in problems[:50]:
                    print(f"  - {p}")
                if len(problems) > 50:
                    print(f"  ... e mais {len(problems) - 50}")
                return 1
            print("build --check: OK, dist/ em dia")
            return 0
        dist = ROOT / "dist"
        if dist.exists():
            shutil.rmtree(dist, onexc=_force_remove)
        build(ROOT, ROOT)
    except BuildError as exc:
        print(f"build: ERRO: {exc}")
        return 2
    src = load_source(ROOT)
    print(f"build: OK, versão {src['version']}; skills: {', '.join(src['skills'])}; "
          f"tripulação ativa: {', '.join(src['available'])}")
    return 0


def _force_remove(func, path, exc):  # pragma: no cover - Windows read-only files
    import os
    import stat
    os.chmod(path, stat.S_IWRITE)
    func(path)


if __name__ == "__main__":
    sys.exit(main())
