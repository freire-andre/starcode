"""model_info.py: what a model is, from the public models.dev catalog (the one OpenCode uses).

For each model ID it prints the price, the context window, tool calling, reasoning, the vendor family and
the cost tier, plus a fixed per-role fit (pesado, execução, repetitivo, Q). The /starcode:config skill uses it
to guide the user when they name a model StarCode does not know (Muse Spark, GLM, Kimi...).

    python model_info.py [--cli opencode] [--offline] [--json] <id> [<id> ...]
    python model_info.py refresh            # download the catalog again

IDs: `provider/model` as OpenCode lists them (`zai/glm-5.3`, `opencode/muse-spark-1.2`,
`openrouter/moonshotai/kimi-k3`), or a bare model (`claude-opus-5-5`; `--cli` picks the provider first).
The catalog is cached in <STARCODE_HOME>/cache/models-dev.json for 7 days; `STARCODE_MODELS_DEV_FILE` points to
a local copy instead (tests, offline machines). Without network and without cache: exit 3, nothing invented.

Cost tier from the output price per 1M tokens: grátis = 0 (or `:free`), `$` < 2, `$$` < 12, `$$$` >= 12.
Exit codes: 0 all found, 1 some ID not in the catalog, 2 usage error, 3 catalog unavailable. Python stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import starcode_common as sc  # noqa: E402

URL = "https://models.dev/api.json"
MAX_AGE_S = 7 * 24 * 3600
CLI_PROVIDERS = {"claude": "anthropic", "codex": "openai", "antigravity": "google"}
VENDOR_ALIASES = {"zhipuai": "zhipu", "z-ai": "zhipu", "zai": "zhipu", "moonshot": "moonshotai",
                  "meta-llama": "meta", "mistralai": "mistral", "x-ai": "xai", "google-vertex": "google",
                  "alibaba-cn": "alibaba", "minimax-cn": "minimax", "zai-coding-plan": "zhipu",
                  "zhipuai-coding-plan": "zhipu", "moonshotai-cn": "moonshotai"}
ROLE_GROUPS = {
    "pesado": ("picard", "spock", "mccoy", "worf"),
    "execucao": ("troi", "data", "laforge", "scotty", "kirk"),
    "repetitivo": ("uhura", "guinan"),
    "q": ("q",),
}
GROUP_LABEL = {"pesado": "Raciocínio pesado (Picard, Spock, McCoy, Worf)",
               "execucao": "Execução (Troi, Data, LaForge, Scotty, Kirk)",
               "repetitivo": "Repetitivo e rápido (Uhura, Guinan)",
               "q": "Q (verificador de outra família)"}
MIN_CONTEXT = 200_000
# Providers that are the vendor of their own models (the family is the provider); any other provider resells.
VENDOR_PROVIDERS = frozenset({"anthropic", "openai", "google", "deepseek", "zai", "zhipuai", "moonshotai",
                              "mistral", "xai", "meta", "alibaba", "alibaba-cn", "minimax", "minimax-cn",
                              "cohere", "ai21", "perplexity", "inception", "poolside", "sakana", "stepfun",
                              "upstage", "xiaomi", "zai-coding-plan", "zhipuai-coding-plan", "moonshotai-cn"})
# Model-name prefix -> family, for a reseller entry without canonical_model_id.
NAME_PREFIX_FAMILIES = (("claude", "anthropic"), ("gpt", "openai"), ("o1", "openai"), ("o3", "openai"),
                        ("o4", "openai"), ("codex", "openai"), ("gemini", "google"), ("deepseek", "deepseek"),
                        ("glm", "zhipu"), ("kimi", "moonshotai"), ("grok", "xai"), ("mistral", "mistral"),
                        ("codestral", "mistral"), ("devstral", "mistral"), ("llama", "meta"),
                        ("qwen", "alibaba"), ("minimax", "minimax"))


# --- catalog --------------------------------------------------------------------------------

def cache_path() -> Path:
    return sc.starcode_home() / "cache" / "models-dev.json"


def _read(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def download(dest: Path | None = None, timeout: int = 20) -> dict | None:
    dest = dest or cache_path()
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "starcode-model-info"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - fixed https URL
            raw = resp.read()
        data = json.loads(raw)
    except Exception:  # noqa: BLE001 - offline, DNS, bad JSON: the caller falls back
        return None
    if not isinstance(data, dict):
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".models-dev.", suffix=".tmp", dir=dest.parent)
    with os.fdopen(fd, "wb") as fh:
        fh.write(raw)
    os.replace(tmp, dest)
    return data


def load_catalog(fetch: bool = True) -> dict | None:
    """Local file override, else a fresh cache, else a download (fetch=True), else a stale cache."""
    override = os.environ.get("STARCODE_MODELS_DEV_FILE")
    if override:
        return _read(Path(override))
    path = cache_path()
    fresh = path.exists() and time.time() - path.stat().st_mtime < MAX_AGE_S
    if fresh:
        data = _read(path)
        if data is not None:
            return data
    if fetch:
        data = download(path)
        if data is not None:
            return data
    return _read(path) if path.exists() else None


# --- lookup and analysis --------------------------------------------------------------------

def lookup(catalog: dict, model_id: str, cli: str | None = None) -> tuple[str, dict] | None:
    """(provider, entry) for `provider/model` or a bare model; None when not in the catalog."""
    mid = model_id.strip()
    if "/" in mid:
        provider, _, rest = mid.partition("/")
        entry = (catalog.get(provider) or {}).get("models", {}).get(rest)
        if isinstance(entry, dict):
            return provider, entry
    order = [CLI_PROVIDERS[cli]] if cli in CLI_PROVIDERS else []
    order += [p for p in ("anthropic", "openai", "google") if p not in order]
    order += [p for p in catalog if p not in order]
    for provider in order:
        entry = (catalog.get(provider) or {}).get("models", {}).get(mid)
        if isinstance(entry, dict):
            return provider, entry
    return None


def vendor(provider: str, entry: dict, model_id: str = "") -> str:
    """Model family by vendor: canonical id prefix, else the openrouter vendor segment, else the provider."""
    canonical = entry.get("canonical_model_id") or ""
    if "/" in canonical:
        v = canonical.split("/", 1)[0]
    elif provider == "openrouter" and model_id.count("/") >= 2:
        v = model_id.split("/")[1]
    elif provider == "openrouter" and "/" in str(entry.get("id", "")):
        v = str(entry["id"]).lstrip("~").split("/", 1)[0]
    elif provider.lower() in VENDOR_PROVIDERS:
        v = provider
    else:
        return _reseller_family(model_id or str(entry.get("id", "")))
    v = v.lower()
    return VENDOR_ALIASES.get(v, v)


def _reseller_family(model_id: str) -> str:
    """Family of a reseller's model without canonical id: the first known vendor among the `.` segments
    before the last one (`anthropic.claude-...`, `global.anthropic.claude-...`), else the name prefix
    table on the last segment, then on the whole name; 'unknown' when none recognises it."""
    name = model_id.rsplit("/", 1)[-1].strip().lower()
    segments = name.split(".")
    for head in segments[:-1]:
        if head in VENDOR_PROVIDERS:
            return VENDOR_ALIASES.get(head, head)
    for candidate in dict.fromkeys((segments[-1], name)):
        for prefix, fam in NAME_PREFIX_FAMILIES:
            if candidate.startswith(prefix):
                return fam
    return "unknown"


def tier(entry: dict, model_id: str = "") -> str:
    if model_id.endswith((":free", "-free")):
        return "grátis"
    cost = entry.get("cost") or {}
    out = cost.get("output")
    if not isinstance(out, (int, float)):
        return "?"
    if out == 0:
        return "grátis"
    return "$" if out < 2 else ("$$" if out < 12 else "$$$")


def fit(entry: dict, model_tier: str) -> dict[str, str]:
    """Fixed per-role verdict: 'ok', 'aviso: <motivo>' or 'vetado: <motivo>'."""
    out: dict[str, str] = {}
    tools = entry.get("tool_call") is True
    reasoning = entry.get("reasoning") is True
    context = (entry.get("limit") or {}).get("context") or 0
    for group in ROLE_GROUPS:
        if not tools:
            out[group] = "vetado: não chama ferramentas (a tripulação lê e edita arquivos e roda comandos)"
            continue
        notes = []
        if group in ("pesado", "execucao") and context and context < MIN_CONTEXT:
            notes.append(f"contexto de {context // 1000}k, abaixo de {MIN_CONTEXT // 1000}k")
        if group in ("pesado", "q") and not reasoning:
            notes.append("sem modo de raciocínio")
        if group == "pesado" and model_tier in ("$", "grátis"):
            notes.append("modelo barato: pode faltar profundidade para spec, bug e review")
        if group == "repetitivo" and model_tier == "$$$":
            notes.append("caro para tarefa repetitiva")
        out[group] = "aviso: " + "; ".join(notes) if notes else "ok"
    return out


def info(catalog: dict, model_id: str, cli: str | None = None) -> dict:
    found = lookup(catalog, model_id, cli)
    if found is None:
        return {"id": model_id, "found": False}
    provider, entry = found
    t = tier(entry, model_id)
    cost = entry.get("cost") or {}
    return {
        "id": model_id, "found": True, "name": entry.get("name", model_id), "provider": provider,
        "family": vendor(provider, entry, model_id), "tier": t,
        "costInput": cost.get("input"), "costOutput": cost.get("output"),
        "context": (entry.get("limit") or {}).get("context"),
        "toolCall": entry.get("tool_call") is True, "reasoning": entry.get("reasoning") is True,
        "description": (entry.get("description") or "").strip(), "fit": fit(entry, t),
    }


def cached_family(model: str) -> str | None:
    """Vendor family from the cached catalog only (never downloads); None when unknown. Used by dispatch."""
    catalog = load_catalog(fetch=False)
    if not catalog or not model:
        return None
    found = lookup(catalog, model)
    return vendor(found[0], found[1], model) if found else None


def cached_tier(model: str) -> str | None:
    catalog = load_catalog(fetch=False)
    found = lookup(catalog, model) if catalog and model else None
    if not found:
        return None
    t = tier(found[1], model)
    return None if t == "?" else t


# --- output ---------------------------------------------------------------------------------

def _money(v) -> str:
    return "?" if not isinstance(v, (int, float)) else f"{v:.2f}".replace(".", ",")


def render(card: dict) -> str:
    if not card["found"]:
        return (f"❔ {card['id']}: não está no catálogo do models.dev. Confira o ID com `opencode models` e "
                "informe a faixa de custo à mão (grátis, $, $$ ou $$$).")
    ctx = f"{card['context'] // 1000}k" if card.get("context") else "?"
    lines = [f"🔎 {card['name']} ({card['id']})",
             f"   Família: {card['family']} · faixa {card['tier']} · US$ {_money(card['costInput'])} entrada / "
             f"{_money(card['costOutput'])} saída por 1M tokens · contexto {ctx} · ferramentas "
             f"{'sim' if card['toolCall'] else 'NÃO'} · raciocínio {'sim' if card['reasoning'] else 'não'}"]
    if card["description"]:
        lines.append(f"   {card['description'][:200]}")
    for group, verdict in card["fit"].items():
        mark = "✅" if verdict == "ok" else ("⛔" if verdict.startswith("vetado") else "⚠️")
        lines.append(f"   {mark} {GROUP_LABEL[group]}: {verdict}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    p = argparse.ArgumentParser(description="Ficha de modelos pelo catálogo models.dev.")
    p.add_argument("ids", nargs="*")
    p.add_argument("--cli", choices=("claude", "codex", "antigravity", "opencode"))
    p.add_argument("--offline", action="store_true", help="não baixa; usa só o cache")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.ids == ["refresh"]:
        ok = download() is not None
        print(f"catálogo atualizado em {cache_path()}" if ok else "ERRO: não foi possível baixar o catálogo")
        return 0 if ok else 3
    if not a.ids:
        p.error("informe ao menos um ID de modelo")
    catalog = load_catalog(fetch=not a.offline)
    if catalog is None:
        print("ERRO: catálogo do models.dev indisponível (sem rede e sem cache). Informe a faixa de custo à mão.")
        return 3
    cards = [info(catalog, mid, a.cli) for mid in a.ids]
    print(json.dumps(cards, ensure_ascii=False, indent=2) if a.json else "\n\n".join(render(c) for c in cards))
    return 0 if all(c["found"] for c in cards) else 1


if __name__ == "__main__":
    sys.exit(main())
