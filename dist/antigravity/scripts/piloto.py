"""piloto.py: the autopilot mandate and decision log of a feature (.specs/features/<slug>/piloto.md).

The Picard in autopilot never edits piloto.md by hand: this script writes it in a fixed format, so the
decisions stay readable later (and by the Guinan in the retro).

    python piloto.py start <slug> [--root .]                  # creates piloto.md (status: ativo, mandato pendente)
    python piloto.py mandato <slug> --kind principio|limite|preferencia --text "..." --source Q3
    python piloto.py confirmar <slug> --words "<palavras exatas do usuário>"   # locks the mandate
    python piloto.py registrar <slug> --by data --question "..." --options "a | b" --decision "..." \
        --reason "..." [--basis M2,Q5] [--confidence alta|media|baixa] \
        [--categoria dependencia|esquema|arquitetura]
    python piloto.py status <slug>                            # one line per field + the decisions to review
    python piloto.py ativo <slug>                             # exit 0 when active with a confirmed mandate
    python piloto.py encerrar <slug> [--reason "..."]
    python piloto.py ativos [--root .]                        # active autopilots (banner)

Rules enforced here: the mandate changes only before `confirmar`; a decision is recorded only with a
confirmed mandate and an active autopilot; a decision without `--basis` is always `baixa` confidence, and
every `baixa` decision is marked `⚠️ revisar`. The 3rd `⚠️ revisar` decision of a feature (and every one after
it) is refused with exit 3 (brake: the question goes back to the user); `--decision "devolvido ao usuário"` is
the way back, recorded without the mark and never counted. `--categoria dependencia|esquema|arquitetura` needs
an `M<n>` in `--basis`, else exit 3. Exit codes: 0 ok, 1 feature/piloto not found or rule refused, 2 usage
error, 3 brake or category without a mandate item. Python stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "gates"))

import starcode_common as sc  # noqa: E402

FILE = "piloto.md"
KINDS = ("principio", "limite", "preferencia")
KIND_LABEL = {"principio": "princípio", "limite": "limite", "preferencia": "preferência"}
CATEGORIAS = ("dependencia", "esquema", "arquitetura")
BRAKE_AT = 2  # `⚠️ revisar` decisions already recorded when the next one is refused
RETURNED = "devolvido ao usuário"
CONFIDENCE = ("alta", "media", "baixa")
CONF_LABEL = {"alta": "alta", "media": "média", "baixa": "baixa"}
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(\S+)", re.M)
CONFIRMED_RE = re.compile(r"^\*\*Mandato confirmado:\*\*\s*(\d{4}-\d{2}-\d{2})", re.M)
USER_CONFIRMED_RE = re.compile(r"^\*\*Mandato confirmado:\*\*\s*\d{4}-\d{2}-\d{2}\s*-\s*user:", re.M)
MANDATE_RE = re.compile(r"^- \*\*M(\d+)\*\*", re.M)
DECISION_RE = re.compile(r"^### D(\d{1,6}) · ", re.M)
ENDED_RE = re.compile(r"^\*\*Encerrado:\*\*\s*(\S+)", re.M)
DECISION_STAMP_RE = re.compile(r"^### D(\d{1,6}) · (\S+) · ", re.M)
REVIEW_RE = re.compile(r"^### (D\d+) · .*⚠️ revisar", re.M)
QREF_RE = re.compile(r"^[MQD]\d+$")


class PilotoError(Exception):
    pass


class BrakeError(PilotoError):
    """The brake or a category without a mandate item: the question goes back to the user (exit 3)."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _one_line(text: str, field: str) -> str:
    value = " ".join((text or "").split())
    if not value:
        raise PilotoError(f"{field} vazio")
    return value


def feature_dir(slug: str, root: Path) -> Path:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise PilotoError(f"slug inválido: {slug!r} (minúsculas e hífen)")
    fdir = root / ".specs" / "features" / slug
    if not fdir.is_dir():
        raise PilotoError(f"feature não encontrada: {fdir}")
    return fdir


def _path(slug: str, root: Path) -> Path:
    path = feature_dir(slug, root) / FILE
    if not path.exists():
        raise PilotoError(f"{path} não existe: rode `piloto.py start {slug}` primeiro")
    return path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _insert_before(text: str, heading: str, block: str) -> str:
    """Append `block` at the end of the section that ends right before `heading` (or at EOF)."""
    idx = text.find(heading) if heading else -1
    if idx < 0:
        return text.rstrip("\n") + "\n" + block
    head = text[:idx].rstrip("\n") + "\n"
    return head + block + "\n" + text[idx:]


def start(slug: str, root: Path) -> str:
    path = feature_dir(slug, root) / FILE
    if path.exists():
        st = STATUS_RE.search(_read(path))
        return f"piloto.md já existe ({st.group(1) if st else '?'}): {path}"
    _write(path, f"""# Piloto automático: {slug}

**Status:** ativo
**Iniciado:** {_now()}
**Mandato confirmado:** pendente
**Checkpoint humano:** aprovação da spec; push, PR, merge e deploy continuam com o usuário

## Mandato

## Decisões
""")
    return f"piloto.md criado: {path}"


def add_mandate(slug: str, root: Path, kind: str, text: str, source: str) -> str:
    path = _path(slug, root)
    doc = _read(path)
    if CONFIRMED_RE.search(doc):
        raise PilotoError("mandato já confirmado: mudanças só com uma nova entrevista (encerre e reinicie o piloto)")
    if kind not in KINDS:
        raise PilotoError(f"--kind deve ser um de {', '.join(KINDS)}")
    src = _one_line(source, "--source")
    n = max([int(x) for x in MANDATE_RE.findall(doc)] or [0]) + 1
    line = f"- **M{n}** · {KIND_LABEL[kind]} · {_one_line(text, '--text')} · origem: {src}\n"
    _write(path, _insert_before(doc, "## Decisões", line))
    return f"M{n} registrado"


def confirm(slug: str, root: Path, words: str) -> str:
    path = _path(slug, root)
    doc = _read(path)
    if CONFIRMED_RE.search(doc):
        return "mandato já estava confirmado"
    if not MANDATE_RE.search(doc):
        raise PilotoError("mandato vazio: registre ao menos um item antes de confirmar")
    quote = _one_line(words, "--words").replace('"', "'")
    doc = doc.replace("**Mandato confirmado:** pendente",
                      f'**Mandato confirmado:** {dt.date.today().isoformat()} - user: "{quote}"', 1)
    _write(path, doc)
    return "mandato confirmado"


def is_active(slug: str, root: Path) -> bool:
    try:
        doc = _read(_path(slug, root))
    except PilotoError:
        return False
    return _active_confirmed(doc)


def _active_confirmed(doc: str) -> bool:
    st = STATUS_RE.search(doc)
    return bool(st and st.group(1) == "ativo" and USER_CONFIRMED_RE.search(doc))


def active_confirmed_in(fdir: Path | None) -> bool:
    """Active autopilot whose mandate the user confirmed (a `- user:` quote), read from a feature folder."""
    path = (fdir / FILE) if fdir else None
    if not path or not path.exists():
        return False
    return _active_confirmed(_read(path))


def approval_valid_in(fdir: Path | None, cited: list[int]) -> bool:
    """A `piloto:` approval citing one of `cited` is valid when the mandate was confirmed by the user, the autopilot
    is active or finished, and a cited decision is registered (with a stamp not after `**Encerrado:**` once finished)."""
    path = (fdir / FILE) if fdir else None
    if not cited or not path or not path.exists():
        return False
    doc = _read(path)
    st = STATUS_RE.search(doc)
    if not st or st.group(1) not in ("ativo", "encerrado") or not USER_CONFIRMED_RE.search(doc):
        return False
    stamps = {int(n): stamp for n, stamp in DECISION_STAMP_RE.findall(doc)}
    if st.group(1) == "ativo":
        return any(n in stamps for n in cited)
    ended = ENDED_RE.search(doc)
    return bool(ended) and any(n in stamps and stamps[n] <= ended.group(1) for n in cited)


def mandate_confirmed_in(fdir: Path | None) -> bool:
    """The feature's piloto.md has a mandate confirmed by the user (a `- user:` quote), active or finished."""
    path = (fdir / FILE) if fdir else None
    if not path or not path.exists():
        return False
    return bool(USER_CONFIRMED_RE.search(_read(path)))


def registered_decisions_in(fdir: Path | None) -> set[int]:
    """Numbers of the `### D<n> · ` decisions registered in the feature folder's piloto.md."""
    path = (fdir / FILE) if fdir else None
    if not path or not path.exists():
        return set()
    return {int(x) for x in DECISION_RE.findall(_read(path))}


def record(slug: str, root: Path, by: str, question: str, options: str, decision: str, reason: str,
           basis: str = "", confidence: str = "", categoria: str | None = None) -> str:
    path = _path(slug, root)
    doc = _read(path)
    st = STATUS_RE.search(doc)
    if not st or st.group(1) != "ativo":
        raise PilotoError("piloto encerrado: a decisão é do usuário")
    if not USER_CONFIRMED_RE.search(doc):
        raise PilotoError("mandato não confirmado: o piloto ainda não decide nada")
    refs = [r.strip().upper() for r in (basis or "").split(",") if r.strip()]
    bad = [r for r in refs if not QREF_RE.match(r)]
    if bad:
        raise PilotoError(f"--basis aceita M<n>, Q<n> ou D<n>: {', '.join(bad)}")
    known_m = {f"M{x}" for x in MANDATE_RE.findall(doc)}
    missing = [r for r in refs if r.startswith("M") and r not in known_m]
    if missing:
        raise PilotoError(f"item de mandato inexistente: {', '.join(missing)}")
    returned = " ".join((decision or "").split()).casefold() == RETURNED.casefold()
    if categoria is not None and categoria not in CATEGORIAS:
        raise PilotoError(f"--categoria deve ser um de {', '.join(CATEGORIAS)}")
    if categoria and not returned and not any(r.startswith("M") for r in refs):
        raise BrakeError(f"categoria {categoria} exige item de mandato (--basis M<n>); "
                         "devolva a pergunta ao usuário")
    conf = (confidence or ("alta" if refs else "baixa")).lower().replace("é", "e")
    if conf not in CONFIDENCE:
        raise PilotoError(f"--confidence deve ser um de {', '.join(CONFIDENCE)}")
    if not refs:
        conf = "baixa"  # no basis in the interview: never more than low confidence
    n = max([int(x) for x in DECISION_RE.findall(doc)] or [0]) + 1
    flag = " · ⚠️ revisar" if conf == "baixa" and not returned else ""
    if flag and len(REVIEW_RE.findall(doc)) >= BRAKE_AT:
        raise BrakeError("freio: 3ª decisão ⚠️ revisar nesta feature; devolva a pergunta ao usuário")
    cat = f" · categoria {categoria}" if categoria else ""
    entry = (f"\n### D{n} · {_now()} · {_one_line(by, '--by')} · confiança {CONF_LABEL[conf]}{cat}{flag}\n"
             f"- **Pergunta:** {_one_line(question, '--question')}\n"
             f"- **Opções:** {_one_line(options, '--options')}\n"
             f"- **Decisão:** {_one_line(decision, '--decision')}\n"
             f"- **Motivo:** {_one_line(reason, '--reason')}\n"
             f"- **Base:** {', '.join(refs) if refs else 'nenhuma na entrevista (opção mais segura e reversível)'}\n")
    _write(path, doc.rstrip("\n") + "\n" + entry)
    return f"D{n} registrada (confiança {CONF_LABEL[conf]}{', revisar' if flag else ''})"


def finish(slug: str, root: Path, reason: str = "") -> str:
    path = _path(slug, root)
    doc = _read(path)
    if not STATUS_RE.search(doc):
        raise PilotoError("piloto.md sem a linha **Status:**")
    doc = STATUS_RE.sub("**Status:** encerrado", doc, count=1)
    note = f"\n**Encerrado:** {_now()}" + (f" · {' '.join(reason.split())}" if reason.strip() else "") + "\n"
    doc = doc.replace("\n## Mandato", note + "\n## Mandato", 1)
    _write(path, doc)
    return "piloto encerrado"


def status(slug: str, root: Path) -> list[str]:
    doc = _read(_path(slug, root))
    st = STATUS_RE.search(doc)
    conf = CONFIRMED_RE.search(doc)
    review = REVIEW_RE.findall(doc)
    return [f"Status: {st.group(1) if st else '?'}",
            f"Mandato: {len(MANDATE_RE.findall(doc))} item(ns), " + (f"confirmado em {conf.group(1)}" if conf else "pendente"),
            f"Decisões: {len(DECISION_RE.findall(doc))}",
            "Revisar: " + (", ".join(f"{d} ⚠️ revisar" for d in review) if review else "nenhuma")]


def actives(root: Path) -> list[tuple[str, int, int]]:
    """(slug, decisions, to review) of every active autopilot with a confirmed mandate."""
    out = []
    base = root / ".specs" / "features"
    for path in sorted(base.glob(f"*/{FILE}")) if base.is_dir() else []:
        doc = _read(path)
        if _active_confirmed(doc):
            out.append((path.parent.name, len(DECISION_RE.findall(doc)), len(REVIEW_RE.findall(doc))))
    return out


def main(argv: list[str] | None = None) -> int:
    sc.utf8_stdio()
    p = argparse.ArgumentParser(description="Mandato e registro de decisões do piloto automático.")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("start", "status", "ativo"):
        s = sub.add_parser(name)
        s.add_argument("slug")
    m = sub.add_parser("mandato")
    m.add_argument("slug")
    m.add_argument("--kind", required=True, choices=KINDS)
    m.add_argument("--text", required=True)
    m.add_argument("--source", required=True)
    c = sub.add_parser("confirmar")
    c.add_argument("slug")
    c.add_argument("--words", required=True)
    r = sub.add_parser("registrar")
    r.add_argument("slug")
    for opt in ("--by", "--question", "--options", "--decision", "--reason"):
        r.add_argument(opt, required=True)
    r.add_argument("--basis", default="")
    r.add_argument("--confidence", default="")
    r.add_argument("--categoria", default=None, choices=CATEGORIAS)
    e = sub.add_parser("encerrar")
    e.add_argument("slug")
    e.add_argument("--reason", default="")
    sub.add_parser("ativos")
    for s in sub.choices.values():
        s.add_argument("--root", default=".")
    a = p.parse_args(argv)
    root = Path(a.root)
    try:
        if a.cmd == "start":
            print(start(a.slug, root))
        elif a.cmd == "mandato":
            print(add_mandate(a.slug, root, a.kind, a.text, a.source))
        elif a.cmd == "confirmar":
            print(confirm(a.slug, root, a.words))
        elif a.cmd == "registrar":
            print(record(a.slug, root, a.by, a.question, a.options, a.decision, a.reason, a.basis, a.confidence,
                         a.categoria))
        elif a.cmd == "status":
            print("\n".join(status(a.slug, root)))
        elif a.cmd == "ativo":
            ok = is_active(a.slug, root)
            print("ativo" if ok else "inativo")
            return 0 if ok else 1
        elif a.cmd == "encerrar":
            print(finish(a.slug, root, a.reason))
        elif a.cmd == "ativos":
            found = actives(root)
            for slug, n, rev in found:
                print(f"{slug}: {n} decisão(ões), {rev} para revisar")
            if not found:
                print("nenhum piloto ativo")
    except BrakeError as exc:
        print(exc, file=sys.stderr)
        return 3
    except PilotoError as exc:
        print(f"ERRO: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
