"""StarCode banner ("Diário do Capitão"), the single banner (plan section 8).

SessionStart hook (quick: no network) and called by /starcode:engajar with --full --text.
Checks: Orca, Linear (--full), both configs, Git mode, work in progress, degraded verifications,
open circuit breakers, competing skills; shows the crew with cli/model.
Never fails the session start: any error becomes a line in the banner.

Usage: python banner.py [--full] [--text] [--agy] [--cwd DIR] [--cli CLI]
  default: reads the SessionStart payload on stdin, prints hook JSON (additionalContext + systemMessage)
  --text:  prints the plain banner (for the skill)
  --agy:   Antigravity format (injectSteps/ephemeralMessage, Phase 5)
  --cli:   adds `CLI: <cli>` and the extras unavailable in that CLI (default claude when given without value;
           without the flag the Phase 3 output is unchanged)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import conflicts  # noqa: E402
import starcode_common as sc  # noqa: E402

ORCA_TIMEOUT = 6
LINEAR_TIMEOUT = 20


def _run(cmd: list[str], timeout: int, cwd: str | None = None) -> tuple[int, str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return 127, ""
    try:
        res = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL,
                             errors="replace", timeout=timeout, cwd=cwd)
    except subprocess.TimeoutExpired:
        return 124, ""
    except OSError:
        return 126, ""
    return res.returncode, res.stdout


def check_orca() -> str:
    code, out = _run(["orca", "status", "--json"], ORCA_TIMEOUT)
    if code == 127:
        return "Orca: ❌ comando `orca` não encontrado no PATH"
    if code == 124:
        return "Orca: ⚠️ `orca status` não respondeu a tempo"
    if code != 0:
        return "Orca: ⚠️ `orca status` falhou (a Orca está aberta?)"
    return "Orca: ✅ disponível"


def check_linear(repo_cfg: dict | None) -> list[str]:
    code, out = _run(["orca", "linear", "team", "list", "--json"], LINEAR_TIMEOUT)
    if code != 0:
        return ["Linear: ❌ `orca linear team list` falhou (Linear conectado na Orca?)"]
    lines = ["Linear: ✅ `orca linear` responde"]
    if repo_cfg:
        team = repo_cfg["linear"]["team"]
        ws = repo_cfg["linear"]["workspace"]
        code, out = _run(["orca", "linear", "team", "states", "--team", team, "--workspace", ws, "--json"],
                         LINEAR_TIMEOUT)
        if code != 0:
            lines.append(f"Linear: ❌ estados do time {team} não puderam ser lidos")
        else:
            try:
                doc = json.loads(out)
                result = doc.get("result", doc)
                names = {s.get("name") for s in result.get("states", []) if isinstance(s, dict)}
            except (json.JSONDecodeError, AttributeError):
                names = set()
            mapped = {k: v for k, v in repo_cfg["linear"]["states"].items() if k != "verifiedAt" and v}
            missing = [f"{k}={v}" for k, v in mapped.items() if v not in names]
            if missing:
                lines.append(f"Linear: ⚠️ estados mapeados que não existem mais no time {team}: "
                             + ", ".join(missing) + " (rode /starcode:setup)")
            else:
                lines.append(f"Linear: ✅ time {team}, {len(mapped)} estados mapeados conferidos")
    return lines


def work_in_progress(root: Path) -> tuple[list[str], list[str], list[str]]:
    """(in progress, degraded, breaker open) from .specs/features/*."""
    wip, degraded, breaker = [], [], []
    features = root / ".specs" / "features"
    if not features.is_dir():
        return wip, degraded, breaker
    for feat in sorted(p for p in features.iterdir() if p.is_dir()):
        # The Handoff lives in the most advanced artifact (tasks.md > spec.md > context.md, F2-3).
        handoff = ""
        for name in ("tasks.md", "spec.md", "context.md"):
            art = feat / name
            text = art.read_text(encoding="utf-8", errors="replace") if art.exists() else ""
            # Only the real heading counts: prose may quote `## Handoff` and its markers.
            head = re.search(r"^## Handoff[ \t]*$", text, re.M)
            if head:
                handoff = re.split(r"^## ", text[head.end():], maxsplit=1, flags=re.M)[0]
                break
        phase = re.search(r"\*\*Phase:\*\*\s*(.+)", handoff)
        if phase and phase.group(1).strip().lower() not in ("done", "concluída", "concluido", "concluída."):
            wip.append(f"{feat.name} (fase: {phase.group(1).strip()})")
        brk = re.search(r"\*\*Breaker:\*\*\s*open\b\s*\(?\s*([^,)\s]*)", handoff, re.I)
        if brk:
            breaker.append(f"{feat.name} ({brk.group(1)})" if brk.group(1) else feat.name)
        ver = feat / "verification.md"
        if ver.exists():
            vtext = ver.read_text(encoding="utf-8", errors="replace")
            # Only a line that STARTS with the marker counts; a table row may merely cite `self-verified`.
            if re.search(r"^\*\*Verification:\*\*[ 	]*(degraded|self-verified)", vtext, re.I | re.M):
                degraded.append(feat.name)
    return wip, degraded, breaker


def unavailable_extras(cli: str) -> list[str]:
    """`Indisponível neste CLI: <extra> → <fallback>` lines: capabilities.json beside the plugin
    (dist), else that CLI's section of src/capabilities.yaml (source tree)."""
    generated = sc.PLUGIN_ROOT / "capabilities.json"
    try:
        if generated.exists():
            extras = json.loads(generated.read_text(encoding="utf-8")).get("extras", {})
        else:
            sys.path.insert(0, str(sc.PLUGIN_ROOT / "tools"))
            import miniyaml  # noqa: PLC0415
            doc = miniyaml.loads((sc.PLUGIN_ROOT / "src" / "capabilities.yaml").read_text(encoding="utf-8"))
            extras = doc.get(cli) or {}
    except Exception as exc:  # noqa: BLE001
        return [f"Capacidades: ⚠️ não foi possível ler a matriz ({exc})"]
    return [f"Indisponível neste CLI: {name} → {info.get('fallback', '')}"
            for name, info in extras.items() if isinstance(info, dict) and info.get("status") == "unavailable"]


def codex_trust_warning() -> list[str]:
    """Warn when the StarCode hooks are not trusted in Codex (R16): no `[hooks.state."starcode@starcode:..."]`
    key with `trusted_hash`, or any of them with `enabled = false`. Missing/unreadable file counts as no trust.
    Home: STARCODE_HOME (tests) or the user's home."""
    warning = ["Hooks do Codex sem trust: aprove em /hooks"]
    home = Path(os.environ.get("STARCODE_HOME") or Path.home())
    try:
        with open(home / ".codex" / "config.toml", "rb") as fh:
            doc = tomllib.load(fh)
        state = doc.get("hooks", {}).get("state", {})
        mine = [v for k, v in state.items()
                if k.startswith("starcode@starcode:hooks/hooks.json:") and isinstance(v, dict)]
    except Exception:  # noqa: BLE001 - never break the banner
        return warning
    if not any(v.get("trusted_hash") for v in mine) or any(v.get("enabled") is False for v in mine):
        return warning
    return []


def crew_lines(user_cfg: dict | None) -> list[str]:
    try:
        doc = sc.load_crew()
    except Exception as exc:  # noqa: BLE001
        return [f"Tripulação: ⚠️ não foi possível ler a tripulação ({exc})"]
    crew = sc.effective_crew(doc, user_cfg)
    available = set(doc["available"]) if "available" in doc else None
    parts = []
    for key, m in crew.items():
        if available is not None and key not in available:
            continue
        model = "padrão do CLI" if m["model"] in (None, "cli-default") else m["model"]
        mark = " (config do usuário)" if m["overridden"] else ""
        parts.append(f"{m.get('emoji', '')} {m['name']}: {m['cli']} · {model}{mark}")
    return ["Tripulação ativa: " + ("; ".join(parts) if parts else "nenhuma")]


def build_banner(cwd: str, full: bool, cli: str | None = None) -> tuple[str, str, bool]:
    """Return (banner text, one-line summary, starcode_active)."""
    root = sc.repo_root(cwd)
    user_cfg, user_err = sc.load_user_config()
    repo_cfg, repo_err = sc.load_repo_config(root)
    has_repo_cfg = bool(root and sc.repo_config_path(root).exists())
    has_specs = bool(root and (root / ".specs").is_dir())
    active = has_repo_cfg or has_specs or full
    lines = ["🖖 StarCode · Diário do Capitão"]
    summary: list[str] = []

    if root is None:
        lines.append("Repositório: fora de um repositório Git")
    else:
        branch = sc.current_branch(cwd) or "(HEAD destacado)"
        mode = sc.git_mode(cwd)
        session = sc.read_session(cwd)
        mode_txt = (f"{mode} ({sc.MODES[mode]}, gravado em {session.get('setAt', '?')}; o Picard pergunta de "
                    "novo nesta sessão)") if mode else "não definido (o Picard pergunta ao engajar)"
        lines.append(f"Repositório: {root.name} · ramo {branch} · modo Git: {mode_txt}")
        summary.append(f"modo Git {mode}" if mode else "modo Git não definido")

    if not sc.user_config_path().exists():
        lines.append("Config do usuário: ausente (valem os padrões do crew.yaml; rode /starcode:setup para criar)")
    elif user_err:
        lines.append("Config do usuário: ❌ INVÁLIDO, não aplicado: " + "; ".join(user_err))
        summary.append("config do usuário inválido")
    else:
        lines.append("Config do usuário: ✅ válido")
    if root is not None:
        if not has_repo_cfg:
            lines.append("Config do repositório: ausente (rode /starcode:setup)")
        elif repo_err:
            lines.append("Config do repositório: ❌ INVÁLIDO, fluxo parado até corrigir: " + "; ".join(repo_err))
            summary.append("config do repositório inválido")
        else:
            lines.append(f"Config do repositório: ✅ válido (time {repo_cfg['linear']['team']}, "
                         f"ramo base {repo_cfg['baseBranch']})")

    if active:
        lines.append(check_orca())
        if full:
            lines.extend(check_linear(repo_cfg))
        if root is not None:
            wip, degraded, breaker = work_in_progress(root)
            if wip:
                lines.append("Trabalho em andamento: " + "; ".join(wip) + " (o Picard propõe retomar)")
                summary.append(f"{len(wip)} feature(s) em andamento")
            for d in degraded:
                lines.append(f"⚠️ Verificação: degradada ({d})")
            for b in breaker:
                lines.append(f"⚠️ Disjuntor aberto: {b}")
            if breaker:
                summary.append("disjuntor aberto")
            if degraded:
                summary.append("verificação degradada")
        try:
            found = conflicts.scan(Path.home(), root)
        except Exception as exc:  # noqa: BLE001
            found = []
            lines.append(f"Concorrentes: ⚠️ verificação falhou ({exc})")
        if found:
            lines.append("⚠️ " + conflicts.format_report(found))
            summary.append(f"{len(found)} skill(s) concorrente(s)")
        lines.extend(crew_lines(user_cfg))
    else:
        lines.append("Este repositório ainda não usa o StarCode. /starcode:setup configura; /starcode:engajar inicia.")

    if cli:
        lines.append(f"CLI: {cli}")
        lines.extend(unavailable_extras(cli))
        if cli == "codex":
            lines.extend(codex_trust_warning())

    one_line = "🖖 StarCode: " + (" · ".join(summary) if summary else "pronto")
    return "\n".join(lines), one_line, active


def _payload_cwd(payload) -> str | None:
    """cwd of the SessionStart payload; Antigravity may omit it and send workspacePaths (as git_guard.extract)."""
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("cwd"), str) and payload["cwd"]:
        return payload["cwd"]
    paths = payload.get("workspacePaths")
    if isinstance(paths, list):
        return next((p for p in paths if isinstance(p, str) and p), None)
    return None


def main() -> int:
    sc.utf8_stdio()
    argv = sys.argv[1:]
    full, text_mode, agy = "--full" in argv, "--text" in argv, "--agy" in argv
    cwd = None
    cli = None
    if "--cli" in argv:
        i = argv.index("--cli") + 1
        cli = argv[i] if i < len(argv) and not argv[i].startswith("--") else "claude"
    if "--cwd" in argv and argv.index("--cwd") + 1 < len(argv):
        cwd = argv[argv.index("--cwd") + 1]
    if not text_mode:
        try:
            payload = json.load(sys.stdin)
            cwd = cwd or _payload_cwd(payload)
        except Exception:
            pass
    cwd = cwd or str(Path.cwd())
    try:
        banner, one_line, active = build_banner(cwd, full, cli)
    except Exception as exc:  # noqa: BLE001 - never break the session start
        banner, one_line, active = f"🖖 StarCode: banner indisponível ({exc})", "", False
    if text_mode:
        print(banner)
    elif agy:
        print(json.dumps({"injectSteps": [{"ephemeralMessage": banner}]}, ensure_ascii=False))
    else:
        out: dict = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": banner}}
        if active and one_line:
            out["systemMessage"] = one_line
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
