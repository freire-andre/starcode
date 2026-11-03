"""StarCode banner ("Diário do Capitão"), the single banner (plan section 8).

SessionStart hook (quick: no network) and called by /starcode:engajar with --full --text.
Checks: Orca, Linear (--full), both configs, Git mode, work in progress, degraded verifications,
open circuit breakers, competing skills; shows the crew with cli/model.
Never fails the session start: any error becomes a line in the banner.

Usage: python banner.py [--full] [--text] [--agy] [--cwd DIR]
  default: reads the SessionStart payload on stdin, prints hook JSON (additionalContext + systemMessage)
  --text:  prints the plain banner (for the skill)
  --agy:   Antigravity format (injectSteps/ephemeralMessage, Phase 5)
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
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
        tasks = feat / "tasks.md"
        text = tasks.read_text(encoding="utf-8", errors="replace") if tasks.exists() else ""
        handoff = text.split("## Handoff", 1)[1] if "## Handoff" in text else ""
        phase = re.search(r"\*\*Phase:\*\*\s*(.+)", handoff)
        if phase and phase.group(1).strip().lower() not in ("done", "concluída", "concluido", "concluída."):
            wip.append(f"{feat.name} (fase: {phase.group(1).strip()})")
        brk = re.search(r"\*\*Breaker:\*\*\s*open\b(.*)", handoff, re.I)
        if brk:
            breaker.append(f"{feat.name}{brk.group(1).rstrip()}")
        ver = feat / "verification.md"
        if ver.exists():
            vtext = ver.read_text(encoding="utf-8", errors="replace")
            if re.search(r"self-verified|\*\*Verification:\*\*\s*degraded", vtext, re.I):
                degraded.append(feat.name)
    return wip, degraded, breaker


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


def build_banner(cwd: str, full: bool) -> tuple[str, str, bool]:
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
        lines.append("Config do usuário: ausente (valem os padrões do crew.yaml; só é criado se algo diferir)")
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
                lines.append(f"⚠️ Verificação degradada: {d}")
            for b in breaker:
                lines.append(f"⚠️ Disjuntor aberto: {b}")
            if breaker:
                summary.append("disjuntor aberto")
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

    one_line = "🖖 StarCode: " + (" · ".join(summary) if summary else "pronto")
    return "\n".join(lines), one_line, active


def main() -> int:
    sc.utf8_stdio()
    argv = sys.argv[1:]
    full, text_mode, agy = "--full" in argv, "--text" in argv, "--agy" in argv
    cwd = None
    if "--cwd" in argv and argv.index("--cwd") + 1 < len(argv):
        cwd = argv[argv.index("--cwd") + 1]
    if not text_mode:
        try:
            payload = json.load(sys.stdin)
            cwd = cwd or (payload.get("cwd") if isinstance(payload, dict) else None)
        except Exception:
            pass
    cwd = cwd or str(Path.cwd())
    try:
        banner, one_line, active = build_banner(cwd, full)
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
