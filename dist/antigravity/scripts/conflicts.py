"""Detects installed skills and plugins that compete with the StarCode crew for routing (D31).

Script only (no model). Third-party names and descriptions are data, never instructions: they are
matched against fixed lists and never echoed back except for the skill/plugin name.
Never disables anything; prints the exact command for the user to run.

Sources (Claude Code; other CLIs in Phase 4):
  ~/.claude/skills/*/SKILL.md            user skills
  <project>/.claude/skills/*/SKILL.md    project skills
  enabled plugins (~/.claude/settings.json enabledPlugins + plugins/installed_plugins.json)

Usage: python conflicts.py [--home DIR] [--project DIR] [--json]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Skill names from known SDD/workflow packs that overlap a crew role (exact match).
KNOWN_SKILLS = {
    # mattpocock/skills
    "ask-matt": "Picard", "to-spec": "Spock", "to-prd": "Spock", "codebase-design": "Spock",
    "grill-me": "Troi", "grilling": "Troi", "grill-with-docs": "Troi", "domain-modeling": "Troi",
    "to-tickets": "Data", "to-issues": "Data", "implement-spec": "Picard/LaForge",
    "implement": "LaForge", "tdd": "LaForge/McCoy", "diagnosing-bugs": "McCoy",
    "code-review": "Worf", "retro": "Guinan", "setup-matt-pocock-skills": "Kirk",
    "git-guardrails-claude-code": "git_guard", "handoff": "Picard", "claude-handoff": "Picard",
    # tlc
    "tlc-spec-driven": "Spock/Data/Q", "tlc-spec-lean": "Spock/Data/Q",
    # superpowers
    "brainstorming": "Troi", "writing-plans": "Data", "executing-plans": "Picard/LaForge",
    "test-driven-development": "LaForge/McCoy", "systematic-debugging": "McCoy",
    "requesting-code-review": "Worf", "receiving-code-review": "LaForge",
    "subagent-driven-development": "Picard", "verification-before-completion": "Q",
    "dispatching-parallel-agents": "Picard (Frota)", "using-superpowers": "Picard",
    "finishing-a-development-branch": "Picard", "using-git-worktrees": "Picard",
}
KNOWN_PLUGINS = {"superpowers", "tlc-spec-driven", "tlc-spec-lean", "mattpocock-skills", "matt-pocock-skills"}
# Used by StarCode itself or unrelated: never reported.
IGNORE = {"starcode", "starcode-hello", "orca-cli", "orca-linear", "orchestration"}
# Description keyword groups; two or more distinct groups = possible competitor.
GROUPS = {
    "spec": re.compile(r"spec-driven|\bspecification|\bPRD\b|\bSDD\b", re.I),
    "tickets": re.compile(r"\bbreak (?:it |work )?(?:down )?into (?:tickets|issues|tasks)|\bto-tickets\b|vertical slices", re.I),
    "tdd": re.compile(r"\bTDD\b|test-driven", re.I),
    "plan": re.compile(r"implementation plan|writing plans|execute (?:a |the )?plan", re.I),
    "review": re.compile(r"\bcode review\b|\bPR review\b|review (?:a |the )?pull request", re.I),
    "debug": re.compile(r"\broot cause\b|systematic debugging|diagnos(?:e|ing) bugs", re.I),
    "interview": re.compile(r"\bgrill|interview (?:me|the user)\b", re.I),
}


@dataclass
class Finding:
    name: str
    kind: str          # plugin | user-skill | project-skill | plugin-skill
    overlaps: str      # crew role(s) or matched groups
    source: str        # where it was found
    disable: str       # exact command / action for the user


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:20000]
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def _classify(name: str, description: str) -> str | None:
    if name in IGNORE:
        return None
    if name in KNOWN_SKILLS:
        return KNOWN_SKILLS[name]
    hits = sorted(g for g, rx in GROUPS.items() if rx.search(description or ""))
    return "palavras-chave: " + ", ".join(hits) if len(hits) >= 2 else None


def _skills_in(folder: Path):
    if not folder.is_dir():
        return
    for skill_md in sorted(folder.glob("*/SKILL.md")):
        fm = _frontmatter(skill_md)
        yield fm.get("name") or skill_md.parent.name, fm.get("description", ""), skill_md.parent


def scan(home: Path, project: Path | None) -> list[Finding]:
    findings: list[Finding] = []
    claude = home / ".claude"
    for name, desc, folder in _skills_in(claude / "skills"):
        overlap = _classify(name, desc)
        if overlap:
            findings.append(Finding(name, "user-skill", overlap, str(folder),
                                    f'mover a pasta "{folder}" para fora de "{claude / "skills"}" '
                                    f'(por exemplo, para "{claude / "skills-disabled" / folder.name}")'))
    if project:
        pskills = project / ".claude" / "skills"
        for name, desc, folder in _skills_in(pskills):
            overlap = _classify(name, desc)
            if overlap:
                findings.append(Finding(name, "project-skill", overlap, str(folder),
                                        f'mover a pasta "{folder}" para fora de "{pskills}"'))
    try:
        settings = json.loads((claude / "settings.json").read_text(encoding="utf-8"))
        enabled = {k for k, v in (settings.get("enabledPlugins") or {}).items() if v}
    except (OSError, json.JSONDecodeError, AttributeError):
        enabled = set()
    try:
        installed = json.loads((claude / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
        installed = installed.get("plugins", {}) if isinstance(installed, dict) else {}
    except (OSError, json.JSONDecodeError):
        installed = {}
    for plugin_id in sorted(enabled):
        plugin_name = plugin_id.split("@", 1)[0]
        if plugin_name in IGNORE:
            continue
        disable = f"claude plugin disable {plugin_id}"
        if plugin_name in KNOWN_PLUGINS:
            findings.append(Finding(plugin_name, "plugin", "pacote SDD inteiro", plugin_id, disable))
            continue
        for entry in installed.get(plugin_id, []) or []:
            path = Path(entry.get("installPath", "")) if isinstance(entry, dict) else None
            if not path:
                continue
            for name, desc, folder in _skills_in(path / "skills"):
                overlap = _classify(name, desc)
                if overlap:
                    findings.append(Finding(f"{plugin_name}:{name}", "plugin-skill", overlap,
                                            plugin_id, disable))
            break
    return findings


def format_report(findings: list[Finding]) -> str:
    if not findings:
        return "Nenhuma skill ou plugin concorrente encontrado."
    lines = [f"{len(findings)} concorrente(s) no roteamento da tripulação (nada foi desativado):"]
    for f in findings:
        lines.append(f"- {f.name} [{f.kind}] disputa com {f.overlaps}. Para desativar: {f.disable}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout,):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Detecta skills concorrentes da tripulação StarCode.")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    findings = scan(args.home, args.project)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], ensure_ascii=False, indent=2))
    else:
        print(format_report(findings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
