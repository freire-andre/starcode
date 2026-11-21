"""SC-212: versão do plugin no despacho e estado das ações de retro."""
from __future__ import annotations

import contextlib
import io
import json
import re
import unittest
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git

import dispatch
import handoff
import retros
import starcode_common as sc
from test_dispatch import TASKS, make_tasks
from test_dispatch_screens import png
from test_dispatch_start import HANDOFF, FakeOrca

SPEC = ("# Demo: Spec\n\n**Linear**: PROJ-9\n**May change**: `app/a.py`, `tests/test_a.py`\n\n"
        "## Scope\nAlgo.\n\n## Requirements\n\n- **R1** - WHEN abre THEN the system SHALL mostrar `captures/home@2x.png`.\n\n"
        "## Checks\n\n**Build**: none - sem build\n**Run unit**: `python -m unittest -v 2>&1`\n\n"
        "**C1** - a (R1)\nProof: run unit | test_a ... ok\n\n"
        "## Sources\n\n- ![home](captures/home@2x.png) - binding - tela inicial\n")
VERIFICATION = ("# Demo - verification\n\n**Verdict**: PASS\n\n## Checks\n\n| Check | Test | Holds |\n| --- | --- | --- |\n"
                "| C1 | `tests/t.py` `test_a` | yes |\n\n## Findings\n\n"
                "| Finding | Evidence | Fix | Closed |\n| --- | --- | --- | --- |\n| C1 frouxa | prova | troque |  |\n")
AVISO = "aviso: plugin StarCode {run} difere do VERSION {repo} do repositório: o brief segue as regras do plugin instalado"

ESPERADO = {
    "R1": ("`dispatch.py` põe a linha `**Plugin:** StarCode <versão>` logo abaixo do título de todo brief que gera "
           "(`brief`, `q-brief`, `screens-brief` e `fix-brief`); a `<versão>` é a do plugin que roda o script, lida como no "
           "banner (`.claude-plugin/plugin.json`, depois `crew.json`, depois `VERSION` da raiz do plugin), ou `desconhecida`."),
    "R2": ("`dispatch.py start` grava a mesma versão no campo `**Plugin:**` do Handoff (campo novo do `handoff.py`, "
           "opção `--plugin`, padrão `none yet`)."),
    "R3": ("num repositório que tem `VERSION` e `dist/claude/.claude-plugin/plugin.json`, quando a versão do plugin "
           "difere do `VERSION`, o `dispatch.py` (nos quatro briefs e no `start`) imprime no stderr `aviso: plugin StarCode "
           "<versão> difere do VERSION <repo> do repositório: o brief segue as regras do plugin instalado`, sem mudar o "
           "código de saída; fora desse repositório, ou com versões iguais, não imprime o aviso."),
    "R4": ("o `skills/guinan/references/retro.md` tem a tabela com a última coluna `Estado` e a regra de que a Guinan "
           "escreve `aberto` em cada linha nova; os valores válidos são `aberto`, `aberto: <issue>`, `feito em <commit>` e "
           "`recusado: <motivo>`."),
    "R5": ("`python scripts/retros.py abertas [--root DIR] [--json] [--todas]` lista, de todos os "
           "`.specs/features/*/retro.md`, as linhas cujo `Estado` começa com `aberto`, uma por linha "
           "(`<slug> #<n> <estado>: <ação proposta>`), e termina com `<N> retro(s) sem coluna Estado`; com `--todas` lista "
           "também as linhas das retros sem a coluna, com o estado `sem estado`; a coluna é achada pelo nome do cabeçalho "
           "(`Estado`, `Ação proposta`), não pela posição; sai com 0."),
    "R6": ("`python scripts/retros.py estado <slug> <n> (--feito <commit> | --recusado <motivo> | --aberto [<issue>])` "
           "reescreve só a célula `Estado` da linha `<n>` e mantém o resto do arquivo idêntico em bytes; retro inexistente, "
           "sem a coluna `Estado` ou sem a linha `<n>` sai com 2 e uma linha com o motivo, sem mudar o arquivo; um `|` no "
           "texto vira `&#124;`."),
    "R7": "esta entrada e a linha no `CHANGELOG.md`.",
}


def fake_plugin(parent: Path, name: str, manifest: str | None = None, crew: str | None = None,
                version: str | None = None) -> Path:
    root = parent / name
    root.mkdir()
    if manifest is not None:
        (root / ".claude-plugin").mkdir()
        (root / ".claude-plugin" / "plugin.json").write_text(json.dumps({"version": manifest}), encoding="utf-8")
    if crew is not None:
        (root / "crew.json").write_text(json.dumps({"version": crew}), encoding="utf-8")
    if version is not None:
        (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    return root


class Plugin:
    """Points the running plugin's version to a fake plugin folder."""

    def __init__(self, root: Path):
        self.root, self.old = root, sc.VERSION_ROOT

    def __enter__(self):
        sc.VERSION_ROOT = self.root

    def __exit__(self, *exc):
        sc.VERSION_ROOT = self.old


def run_main(mod, argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = mod.main(argv)
    return code, out.getvalue(), err.getvalue()


def tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class VersaoERetroTests(TempRepoCase):
    def feature(self) -> Path:
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        (fdir / "captures").mkdir(parents=True)
        (fdir / "captures" / "home@2x.png").write_bytes(png(1600, 1200))
        (fdir / "spec.md").write_text(SPEC, encoding="utf-8")
        (fdir / "verification.md").write_text(VERIFICATION, encoding="utf-8", newline="\n")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        return fdir

    def briefs(self) -> dict[str, str]:
        return {
            "brief": dispatch.worker_brief("demo", "T1", self.repo),
            "q-brief": dispatch.q_brief("demo", self.repo, "main", "abc1234"),
            "screens-brief": dispatch.screens_brief("demo", self.repo, "http://localhost:5173"),
            "fix-brief": dispatch.fix_brief("demo", self.repo),
        }

    def assert_plugin_line(self, name: str, text: str, version: str) -> None:
        lines = text.splitlines()
        self.assertTrue(lines[0].startswith("# "), (name, lines[0]))  # título na primeira linha
        self.assertEqual(lines[1:3], ["", f"**Plugin:** StarCode {version}"], name)
        self.assertEqual(text.count("**Plugin:**"), 1, name)
        if name.endswith(("q-brief", "screens-brief")):
            self.assertEqual(lines[3:5], ["", f"Repositório: {self.repo.as_posix()}"], name)
        else:
            self.assertNotIn("Repositório:", "\n".join(lines[:6]), name)

    def test_brief_traz_versao_do_plugin(self):
        fdir = self.feature()
        fakes = [("manifesto", dict(manifest="2.0.0", crew="3.0.0", version="4.0.0"), "2.0.0"),
                 ("crew", dict(crew="3.0.0", version="4.0.0"), "3.0.0"),
                 ("version", dict(version="4.0.0"), "4.0.0"),
                 ("nenhum", dict(), "desconhecida")]
        for name, files, want in fakes:
            with self.subTest(name), Plugin(fake_plugin(self.tmp, name, **files)):
                for cmd, text in self.briefs().items():
                    self.assert_plugin_line(f"{name}/{cmd}", text, want)
        # com tasks.md o brief do ticket sai do outro caminho e ganha a mesma linha
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "tasks")
        with Plugin(fake_plugin(self.tmp, "com-tasks", manifest="5.1.0")):
            text = dispatch.worker_brief("demo", "T2", self.repo)
        self.assertTrue(text.startswith("# Ticket T2: "), text[:40])
        self.assertEqual(text.splitlines()[1:3], ["", "**Plugin:** StarCode 5.1.0"])
        self.assertEqual(text.count("**Plugin:**"), 1)

    def test_start_grava_plugin_no_handoff(self):
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        fdir.mkdir(parents=True)
        (fdir / "spec.md").write_text("# Demo: Spec\n", encoding="utf-8")
        (fdir / "tasks.md").write_text(make_tasks([{"tid": "T1"}]) + HANDOFF.format(d="none"), encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")
        run_git(self.repo, "branch", "-f", "feature/demo")
        fake = FakeOrca()
        out: list[str] = []
        with Plugin(fake_plugin(self.tmp, "p", manifest="7.7.7")):
            code, _ = dispatch.start("demo", "T1", "claude", "claude-sonnet-5-5", self.repo, runner=fake, emit=out.append)
        self.assertEqual(code, 0, out)
        writes = [c for c in fake.calls if c[0] != "orca" and "handoff.py" in c[1]]
        self.assertEqual(len(writes), 2)
        for c in writes:
            self.assertEqual(c[c.index("--plugin") + 1], "7.7.7")
        lines = (fdir / "tasks.md").read_text(encoding="utf-8").splitlines()
        self.assertEqual(handoff.read_fields(lines, handoff.section_bounds(lines))["plugin"], "7.7.7")
        self.assertIn("**Plugin:** 7.7.7", lines)
        # o handoff.py set --plugin funciona sozinho; sem a opção o padrão é `none yet`
        (self.repo / ".specs" / "features" / "solo").mkdir()
        solo = self.repo / ".specs" / "features" / "solo" / "spec.md"
        solo.write_text("# Solo\n", encoding="utf-8")
        code, _, err = run_main(handoff, ["set", "solo", "--root", str(self.repo)])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("**Plugin:** none yet", solo.read_text(encoding="utf-8").splitlines())
        code, _, err = run_main(handoff, ["set", "solo", "--root", str(self.repo), "--plugin", "1.2.3"])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("**Plugin:** 1.2.3", solo.read_text(encoding="utf-8").splitlines())

    def test_aviso_de_versao_diferente(self):
        fdir = self.feature()
        (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "tasks")
        outdir = self.tmp / "out"
        outdir.mkdir()
        root = ["--root", str(self.repo)]
        cmds = {
            "brief": ["brief", "demo", "T1", "--out", str(outdir / "b.md"), *root],
            "q-brief": ["q-brief", "demo", "--base", "main", "--head", "abc1234", "--out", str(outdir / "q.md"), *root],
            "screens-brief": ["screens-brief", "demo", "--url", "http://localhost:5173", "--out", str(outdir / "s.md"), *root],
            "fix-brief": ["fix-brief", "demo", "--out", str(outdir / "f.md"), *root],
            "start": ["start", "demo", "T99", "--cli", "claude", "--model", "m", *root],  # recusado antes de chamar a Orca
        }
        with Plugin(fake_plugin(self.tmp, "p", manifest="0.9.0")):
            base = {k: run_main(dispatch, a) for k, a in cmds.items()}  # fora do repositório do StarCode
            (self.repo / "VERSION").write_text("1.0.0\n", encoding="utf-8")
            plug = self.repo / "dist" / "claude" / ".claude-plugin"
            plug.mkdir(parents=True)
            (plug / "plugin.json").write_text("{}", encoding="utf-8")
            for k, a in cmds.items():
                code, out, err = run_main(dispatch, a)
                self.assertEqual(err, AVISO.format(run="0.9.0", repo="1.0.0") + "\n", k)
                self.assertEqual((code, out), (base[k][0], base[k][1]), k)  # mesmo código e mesma saída
            self.assertEqual({k: v[0] for k, v in base.items()},
                             {"brief": 0, "q-brief": 0, "screens-brief": 0, "fix-brief": 0, "start": 2})
            for k, v in base.items():
                self.assertEqual(v[2], "", k)
        with Plugin(fake_plugin(self.tmp, "igual", manifest="1.0.0")):  # versões iguais
            for k, a in cmds.items():
                self.assertEqual(run_main(dispatch, a)[2], "", k)
        (plug / "plugin.json").unlink()
        with Plugin(fake_plugin(self.tmp, "dif", manifest="0.9.0")):  # sem dist/claude/.../plugin.json
            for k, a in cmds.items():
                self.assertEqual(run_main(dispatch, a)[2], "", k)
        (plug / "plugin.json").write_text("{}", encoding="utf-8")
        (self.repo / "VERSION").unlink()
        with Plugin(fake_plugin(self.tmp, "dif2", manifest="0.9.0")):  # sem VERSION
            for k, a in cmds.items():
                self.assertEqual(run_main(dispatch, a)[2], "", k)

    def test_retro_da_guinan_tem_estado(self):
        text = (ROOT / "skills" / "guinan" / "references" / "retro.md").read_text(encoding="utf-8")
        flat = " ".join(text.split())
        self.assertIn("| # | Severidade | Categoria | Evidência | Ação proposta | Estado |\n|---|---|---|---|---|---|\n"
                      "| 1 | alta | <category> | <commit, Handoff line or finding ID> | <action, not applied> | aberto |", text)
        self.assertIn("The last column is `Estado`: Guinan writes `aberto` in every new row.", flat)
        self.assertIn("Valid values: `aberto`, `aberto: <issue>`, `feito em <commit>` and `recusado: <motivo>`.", flat)
        self.assertIn("(--feito <commit> | --recusado <motivo> | --aberto [<issue>])", flat)
        skill = (ROOT / "skills" / "guinan" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("- **estado**: last column of the table, `aberto` in every new row", skill)

    def retros_tree(self) -> Path:
        root = self.tmp / "arvore"
        feats = root / ".specs" / "features"
        for slug, body in {
            "a": ("# Retro: a\n\n| Estado | # | Severidade | Ação proposta |\n|---|---|---|---|\n"
                  "| aberto | 1 | alta | faz &#124; isso |\n| feito em abc1234 | 2 | média | já foi |\n"
                  "| aberto: SC-9 | 3 | baixa | depois |\n| recusado: não vale | 4 | baixa | nunca |\n"),
            "b": ("# Retro: b\n\n| # | Severidade | Categoria | Evidência | Ação proposta |\n|---|---|---|---|---|\n"
                  "| 1 | alta | spec | e | sem estado aqui |\n"),
            "c": "# Retro: c\n\n| # | Ação proposta | Estado |\n|---|---|---|\n| 1 | tudo feito | feito em 1234567 |\n",
        }.items():
            (feats / slug).mkdir(parents=True)
            (feats / slug / "retro.md").write_text(body, encoding="utf-8", newline="\n")
        return root

    def test_retros_abertas(self):
        root = self.retros_tree()
        code, out, err = run_main(retros, ["abertas", "--root", str(root)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "a #1 aberto: faz &#124; isso\na #3 aberto: SC-9: depois\n1 retro(s) sem coluna Estado\n")
        code, out, err = run_main(retros, ["abertas", "--root", str(root), "--todas"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "a #1 aberto: faz &#124; isso\na #3 aberto: SC-9: depois\n"
                              "b #1 sem estado: sem estado aqui\n1 retro(s) sem coluna Estado\n")
        code, out, err = run_main(retros, ["abertas", "--root", str(root), "--json"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), {"retros": [
            {"slug": "a", "n": "1", "estado": "aberto", "acao": "faz &#124; isso"},
            {"slug": "a", "n": "3", "estado": "aberto: SC-9", "acao": "depois"}], "sem_coluna_estado": 1})
        code, out, _ = run_main(retros, ["abertas", "--root", str(self.tmp / "vazio")])
        self.assertEqual((code, out), (0, "0 retro(s) sem coluna Estado\n"))

    def test_retros_estado(self):
        root = self.retros_tree()
        path = root / ".specs" / "features" / "a" / "retro.md"
        original = path.read_bytes()
        cases = [(["--feito", "abc1234"], "feito em abc1234"),
                 (["--recusado", "não vale | agora"], "recusado: não vale &#124; agora"),
                 (["--aberto", "SC-9"], "aberto: SC-9"), (["--aberto"], "aberto"), (["--aberto", ""], "aberto")]
        for extra, cell in cases:
            path.write_bytes(original)
            code, out, err = run_main(retros, ["estado", "a", "2", "--root", str(root), *extra])
            self.assertEqual((code, err, out), (0, "", f"a #2: {cell}\n"), extra)
            want = original.replace("| feito em abc1234 | 2 |".encode(), f"| {cell} | 2 |".encode())
            self.assertEqual(path.read_bytes(), want, extra)
        # CRLF, sem newline final e Estado no meio: o resto fica idêntico em bytes
        crlf = root / ".specs" / "features" / "d"
        crlf.mkdir()
        body = ("# Retro: d\r\n\r\n| # | Estado | Ação proposta |\r\n|---|---|---|\r\n| 1 | aberto | x |\r\n"
                "| 2 | aberto | y |\r\n\r\nrodapé").encode()
        (crlf / "retro.md").write_bytes(body)
        code, _, err = run_main(retros, ["estado", "d", "1", "--root", str(root), "--feito", "c0ffee1"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual((crlf / "retro.md").read_bytes(),
                         body.replace(b"| 1 | aberto | x |", b"| 1 | feito em c0ffee1 | x |"))
        # recusas: código 2, a linha exata e nada mudado (bytes e lista de arquivos)
        path.write_bytes(original)
        before = tree(root)
        refusals = [(["estado", "nada", "1", "--feito", "x"], "retro não encontrada: nada\n"),
                    (["estado", "b", "1", "--feito", "x"], "retro sem coluna Estado: b\n"),
                    (["estado", "a", "9", "--feito", "x"], "linha 9 não existe na retro de a\n"),
                    (["estado", "a", "1", "--feito", ""], "estado vazio: informe o commit ou o motivo\n"),
                    (["estado", "a", "1", "--recusado", ""], "estado vazio: informe o commit ou o motivo\n")]
        for argv, line in refusals:
            code, out, err = run_main(retros, [*argv, "--root", str(root)])
            self.assertEqual((code, out, err), (2, "", line), argv)
            self.assertEqual(tree(root), before, argv)
        code, _, _ = run_main(retros, ["estado", "a", "1", "--root", str(root)])  # sem o estado novo
        self.assertEqual(code, 2)
        self.assertEqual(tree(root), before)

    def test_decisions_e_changelog(self):
        text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
        m = re.search(r"^### SC-212:.*?(?=^### SC-|\Z)", text, re.M | re.S)
        self.assertIsNotNone(m)
        entry = m.group(0)
        parts = {}
        for label in ("Problema", "Decisão", "Motivo", "Por que não é bug"):
            pm = re.search(rf"^- \*\*{label}\*\*: (.*)$", entry, re.M)
            self.assertIsNotNone(pm, label)
            parts[label] = pm.group(1)
        achados = {k: v.rstrip(" ") for k, v in re.findall(r"(R\d): (.*?)(?= R\d: |$)", parts["Decisão"])}
        self.assertEqual(sorted(achados), sorted(ESPERADO))
        for chave, frase in ESPERADO.items():
            self.assertEqual(achados[chave], frase, chave)
        tests = ("test_brief_traz_versao_do_plugin", "test_start_grava_plugin_no_handoff", "test_aviso_de_versao_diferente",
                 "test_retro_da_guinan_tem_estado", "test_retros_abertas", "test_retros_estado", "test_decisions_e_changelog")
        for name in tests:
            self.assertIn(f"`{name}`", parts["Por que não é bug"], name)
            self.assertTrue(hasattr(type(self), name), name)
        self.assertIn("`test_versao_e_retro.VersaoERetroTests`", parts["Por que não é bug"])
        change = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", change, re.M | re.S).group(1)
        self.assertEqual(len([ln for ln in unreleased.splitlines() if "(SC-212)" in ln]), 1)


if __name__ == "__main__":
    unittest.main()
