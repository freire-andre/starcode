"""SC-213: suíte rápida para o worker, regra de estado novo e execute.md dividido (R1 a R10)."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from helpers import ROOT, TempRepoCase, run_git
from test_support import execute_text

import dispatch
import starcode_common as sc
from test_dispatch import TASKS
from test_dispatch_screens import png
from test_versao_e_retro import SPEC, VERIFICATION, run_main

REFS = ROOT / "skills" / "engajar" / "references"
FILES = {
    "execute-despacho.md": ["## 2. Dispatch one ticket (sequential path)",
                            "## 2F. Fleet (v1.1): parallel tickets in one batch",
                            "## 3. Check and integrate the ticket"],
    "execute-provas-e-q.md": ["## 4. Proofs and the Q"],
    "execute-pos-q-e-review.md": ["## 5. Post-Q cycle (4.6) and the end", "## Review (Worf)",
                                  "## Text for the PR and the Linear comments (Uhura)"],
    "execute-retomada.md": ["## 6. Resume and the circuit breaker (D27)"],
    "execute-modo-1.md": ["## 7. Git mode 1 (degraded)"],
    "execute-media-pequena.md": ["## 8. MEDIUM and SMALL"],
}
INDEX_HEADERS = ["## 0. Preconditions", "## 1. Integration branch"]
SELECT = 'python "{plugin}/scripts/impact.py" select --diff <base>'
GATE = 'python "{plugin}/scripts/gates/run_gates.py" ticket {slug} {ticket} <base>..HEAD'

TESTES = ("os testes escolhidos por `python \"{plugin}/scripts/impact.py\" select --diff <base>` verdes "
          "(a suíte inteira só quando o veredito for `rodar tudo` ou a seleção falhar)")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines()]


def _entry(slug: str) -> str:
    text = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    start = text.index(f"### {slug}:")
    nxt = re.search(r"\n### ", text[start + 1:])
    return text[start:start + 1 + nxt.start()] if nxt else text[start:]


class SuiteEExecuteTests(TempRepoCase):
    def feature(self, tasks: bool = False) -> None:
        self.write_repo_config()
        fdir = self.repo / ".specs" / "features" / "demo"
        (fdir / "captures").mkdir(parents=True)
        (fdir / "captures" / "home@2x.png").write_bytes(png(1600, 1200))
        (fdir / "spec.md").write_text(SPEC, encoding="utf-8")
        (fdir / "verification.md").write_text(VERIFICATION, encoding="utf-8", newline="\n")
        if tasks:
            (fdir / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "specs")

    def gerar(self, *args: str) -> str:
        """Run `dispatch.py <args> --out <file>` through main() and return the file the brief was written to."""
        out = self.tmp / "brief.md"
        code, _, err = run_main(dispatch, [*args, "--out", str(out), "--root", str(self.repo)])
        self.assertEqual((code, err), (0, ""), args)
        return out.read_text(encoding="utf-8")

    def test_fix_brief_usa_selecao_do_impact(self):  # C1, R1
        self.feature()
        plugin = sc.PLUGIN_ROOT.as_posix()
        brief = self.gerar("fix-brief", "demo")
        want = f"""## Regras fixas da correção (StarCode)

- Um commit por achado, com `Refs: PROJ-9` no corpo, citando o achado.
- Nunca escreva em `.specs/`.
- Nunca rode `git push`, `git reset`, `git restore` nem `git stash`.
- Antes de terminar: os testes escolhidos por `python "{plugin}/scripts/impact.py" select --diff <base>` verdes (a suíte inteira só quando o veredito for `rodar tudo` ou a seleção falhar) e `python "{plugin}/scripts/gates/run_gates.py" ticket demo T1 <base>..HEAD` verde.
- Relatório final: o commit e o teste de cada achado corrigido.
"""
        self.assertTrue(brief.endswith(want), brief[-900:])
        self.assertNotIn("a suíte inteira verde", brief)

    def test_brief_do_ticket_usa_selecao_do_impact(self):  # C2, R2
        plugin = sc.PLUGIN_ROOT.as_posix()
        want = f"""## Regras fixas do worker (StarCode)

- Você é o LaForge, um worker com contexto limpo. Se a skill `laforge` estiver disponível, siga-a.
- Implemente só este ticket e altere só os arquivos de `May change`. Precisa de outro arquivo? Pare e
  diga qual e por quê.
- Nunca escreva `.specs/STATE.md` nem a seção `## Handoff` de nenhum artefato: só o Picard escreve nelas.
- Testes: rode os testes escolhidos por `python "{plugin}/scripts/impact.py" select --diff <base>` e deixe-os verdes; a suíte inteira só quando o veredito for `rodar tudo` ou a seleção falhar.
- Antes de terminar: `python "{plugin}/scripts/gates/run_gates.py" ticket demo T1 <base>..HEAD` verde
  (base = commit de partida deste worktree).
- Falhas: identificador estável por erro; na 2ª falha do mesmo erro, use a skill `mccoy`; na 3ª, pare.
- Ticket com tela citada por captura (`captures/<nome>.png`): tire a foto do autor com
  `python "{plugin}/scripts/screens.py" capture` em `captures/<nome>.running.png` e commite-a, dentro do `May change`.
- Relatório final (até 5 linhas): o que mudou, a linha de veredito do `impact.py`, gates executados com resultado, commits, pendências,
  tentativas do disjuntor (`<id>=<n>` ou `none`).
- Nunca desligue a assinatura de commits (commit.gpgsign false, --no-gpg-sign) em código de produto; só repositórios Git temporários de teste podem fazê-lo.
"""
        self.feature()
        brief = self.gerar("brief", "demo", "T1")  # spec sem tasks.md (MEDIUM)
        self.assertTrue(brief.endswith(want), brief[-1500:])
        (self.repo / ".specs" / "features" / "demo" / "tasks.md").write_text(TASKS, encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-q", "-m", "tasks")
        brief = self.gerar("brief", "demo", "T1")  # ticket de tasks.md
        self.assertTrue(brief.endswith(want), brief[-1500:])

    def test_laforge_e_mccoy_rodam_a_selecao(self):  # C3, R3
        laforge = " ".join((ROOT / "skills/laforge/SKILL.md").read_text(encoding="utf-8").split())
        mccoy = " ".join((ROOT / "skills/mccoy/SKILL.md").read_text(encoding="utf-8").split())
        frases = {
            "laforge": (laforge, [
                "3. **Gates before each commit**: the ticket's `Gate` level from `## Gate Commands`, then the commit gate. "
                '**Tests (SC-213):** run the tests chosen by `python "<plugin-root>/scripts/impact.py" select --diff <base>`; '
                'the whole suite only when the verdict is `rodar tudo` or the selection fails. '
                'The whole suite runs at the done gate (`Run unit` of the spec) and in CI. '
                'Put the `impact.py` verdict line in the report.']),
            "mccoy": (mccoy, [
                '6. **Impact radius (R31).** After the regression test and the fix, run '
                '`python "<plugin-root>/scripts/impact.py" select --diff <base>` (base = `baseBranch` of the config). '
                'Run the tests it chooses (the whole suite only when the verdict is `rodar tudo` or the selection fails), '
                "before the ticket's gate, and put the verdict line in the report. "
                'The whole suite runs at the done gate (`Run unit` of the spec) and in CI.']),
        }
        for nome, (text, lista) in frases.items():
            for frase in lista:
                self.assertEqual(text.count(frase), 1, nome)
        self.assertNotIn("The gates still run the whole suite", mccoy)
        self.assertNotIn("The gates still run the whole suite", laforge)

    def test_decisions_registra_a_medicao(self):  # C4, R4
        entry = _entry("SC-213")
        decisao = entry[entry.index("- **Decisão**"):entry.index("- **Motivo**")]
        self.assertIn("python -m unittest discover -s tests --durations 20", decisao)
        self.assertIn("linha de base 1.083 testes em 1.519 s (2026-11-21, F:)", decisao)
        bruto = (ROOT / ".specs" / "features" / "suite-e-execute" / "medicao-durations.txt").read_text(encoding="utf-8")

        def ptbr(valor: str) -> str:  # "18.128" -> "18,128"; "731.326" -> "731,326"
            return valor.replace(".", ",")

        ran = re.search(r"^Ran (\d+) tests in (\d+\.\d+)s$", bruto, re.M)
        self.assertIsNotNone(ran, "a saída conservada não tem `Ran <n> tests in <t>s`")
        total = f"{int(ran.group(1)):,}".replace(",", ".")
        commit = re.search(r"commit (\w+), (\d{4}-\d\d-\d\d)", bruto)
        self.assertIsNotNone(commit)
        self.assertIn(f"Medição: {total} testes em {ptbr(ran.group(2))} s ({commit.group(2)}, C:, commit {commit.group(1)})", decisao)
        lentos_brutos = re.findall(r"^(\d+\.\d+)s\s+(test_\w+)", bruto, re.M)[:5]
        self.assertEqual(len(lentos_brutos), 5)
        registrados = re.findall(r"`(test_\w+)` (\d+,\d+) s", decisao)
        self.assertEqual(registrados, [(nome, ptbr(tempo)) for tempo, nome in lentos_brutos])

    def test_agents_tem_regra_de_estado(self):  # C5, R5
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        start = text.index("## Regras\n")
        sec = text[start:text.index("\n## ", start + 1)]
        want = ("- **Estado novo**: arquivo de estado novo é JSON escrito por script, e o markdown que alguém lê é "
                "gerado a partir dele. O Handoff (`## Handoff`) continua markdown escrito pelo `handoff.py`.")
        self.assertIn(want, _lines(sec))

    def test_execute_md_vira_indice(self):  # C6, R6, R7
        text = (REFS / "execute.md").read_text(encoding="utf-8")
        self.assertLessEqual(len(text.split()), 700)
        self.assertTrue(text.startswith("# Execute: sequential tickets, integration and verification"))
        heads = [ln for ln in text.splitlines() if ln.startswith("## ")]
        self.assertEqual(heads[:2], INDEX_HEADERS)
        self.assertEqual(len(heads), 3)
        self.assertIn("The Picard **only coordinates** (D23)", text)
        self.assertIn("Variables: `<slug>` the feature", text)
        self.assertIn("Do not load the other files.", text)
        rows = {ln.split("|")[2].strip(): ln.split("|")[1].strip() for ln in text.splitlines()
                if ln.startswith("| ") and "`execute-" in ln}
        self.assertEqual(len(rows), 6)
        quais = {"execute-despacho.md": "2, 2F, 3 (dispatch, fleet, integrate)",
                 "execute-provas-e-q.md": "4 (proofs and the Q)",
                 "execute-pos-q-e-review.md": "5, Review (Worf), Text for the PR",
                 "execute-retomada.md": "6 (resume, circuit breaker)",
                 "execute-modo-1.md": "7 (Git mode 1)",
                 "execute-media-pequena.md": "8 (MEDIUM and SMALL)"}
        self.assertEqual(rows, {f"`{nome}`": secoes for nome, secoes in quais.items()})
        for nome, secoes in quais.items():
            novo = (REFS / nome).read_text(encoding="utf-8").splitlines()
            self.assertTrue(novo[0].startswith("# Execute: "), nome)
            self.assertEqual(novo[1], "")
            self.assertEqual(novo[2], "Variables and preconditions: see `execute.md` (sections 0 and 1).", nome)

    def test_cabecalhos_no_arquivo_certo(self):  # C7, R7, R8
        antigos = INDEX_HEADERS + [h for hs in FILES.values() for h in hs]
        self.assertEqual(len(antigos), 12)
        conjunto = execute_text()
        todos = [ln for ln in conjunto.splitlines() if ln.startswith("## ")]
        for h in antigos:
            self.assertEqual(todos.count(h), 1, h)
        for nome, hs in FILES.items():
            achados = [ln for ln in (REFS / nome).read_text(encoding="utf-8").splitlines() if ln.startswith("## ")]
            self.assertEqual(achados, hs, nome)
        # o helper lê os sete arquivos: o índice primeiro, os outros em ordem alfabética
        ordem = [REFS / "execute.md"] + sorted(REFS.glob("execute-*.md"))
        self.assertEqual([p.name for p in ordem], ["execute.md"] + sorted(FILES))
        self.assertEqual(conjunto, "\n".join(p.read_text(encoding="utf-8") for p in ordem))

    def test_testes_leem_o_execute_por_execute_text(self):  # C8, R8
        """Nenhum teste lê `execute.md` direto (só o índice); quem confere o texto das seções usa `execute_text()`."""
        tests_dir = ROOT / "tests"
        diretos, usam_helper = [], set()
        for f in sorted(tests_dir.glob("*.py")):
            if f.name in ("test_support.py", Path(__file__).name):
                continue
            source = f.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                for filho in ast.iter_child_nodes(node):
                    filho.parent = node
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "execute_text":
                    usam_helper.add(f.name)
                if not (isinstance(node, ast.Constant) and isinstance(node.value, str)
                        and re.search(r"(^|/)execute\.md$", node.value)):
                    continue
                pai = node.parent  # só vale como leitura quando é parte de um caminho ou argumento de Path/open/join
                caminho = isinstance(pai, ast.BinOp) or (
                    isinstance(pai, ast.Call) and getattr(pai.func, "id", getattr(pai.func, "attr", "")) in
                    ("Path", "open", "join", "joinpath", "read_text", "read_bytes"))
                if not caminho:
                    continue
                stmt = node
                while not isinstance(stmt, ast.stmt):
                    stmt = stmt.parent
                trecho = ast.get_source_segment(source, stmt) or ""
                if ".is_file()" in trecho or ".exists()" in trecho:
                    continue  # só confere que o arquivo existe (test_build.py)
                diretos.append(f"{f.name}:{node.lineno}: {trecho.strip().splitlines()[0]}")
        self.assertEqual(diretos, [], "lê o execute.md direto em vez de execute_text()")
        afetados = {"test_brief_media_escopo.py", "test_crew_live.py", "test_dispatch.py", "test_dispatch_qcheck.py",
                    "test_execute_doc_start_settle.py", "test_fecha_achado.py", "test_flow_f12.py",
                    "test_flow_worf_guinan.py", "test_licoes_no_brief.py", "test_pr_review.py", "test_screens_flow.py",
                    "test_skills_exec.py", "test_uhura_skill.py", "test_worker_skills.py"}
        self.assertEqual(sorted(afetados - usam_helper), [], "teste afetado que não chama execute_text()")

    def test_referencias_apontam_o_arquivo_novo(self):  # C9, R9
        exts = {".md", ".py", ".ts", ".tsx", ".js", ".mjs", ".json", ".txt", ".yml", ".yaml", ".sh"}
        achadas: list[str] = []
        for base in ("skills", "src", "scripts", "hooks"):
            for f in sorted((ROOT / base).rglob("*")):
                if not f.is_file() or f.suffix not in exts or "node_modules" in f.parts:
                    continue
                rel = f.relative_to(ROOT).as_posix()
                for n, ln in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    # toda menção ao índice `execute.md` (não a um `execute-*.md`), em qualquer forma
                    if re.search(r"(?<![\w-])execute\.md", ln):
                        achadas.append(f"{rel}: {ln.strip()}")
                    # a seção citada ao lado de um `execute-*.md` existe nesse arquivo
                    for m in re.finditer(r"(execute-[\w-]+\.md)`\)?,? ?\(?(?:section|seção) (\d+)", ln):
                        alvo = REFS / m.group(1)
                        self.assertTrue(alvo.is_file(), f"{rel}:{n}: {m.group(1)} não existe")
                        titulos = [h for h in alvo.read_text(encoding="utf-8").splitlines()
                                   if h.startswith(f"## {m.group(2)}.")]
                        self.assertEqual(len(titulos), 1, f"{rel}:{n}: {m.group(1)} não tem a seção {m.group(2)}")
        permitidas = [
            ("skills/engajar/SKILL.md", "Follow `references/execute.md` (index; load only the file of the step in progress"),
            ("skills/engajar/references/state-format.md", "(`execute.md`, then `execute-despacho.md`)"),
            ("src/context/STARCODE.md", "`skills/engajar/references/execute.md` (index) and the `execute-*.md` files it lists."),
        ] + [(f"skills/engajar/references/{nome}", "Variables and preconditions: see `execute.md` (sections 0 and 1).")
             for nome in sorted(FILES)]
        self.assertEqual(len(achadas), len(permitidas), achadas)
        for rel, frase in permitidas:
            casam = [a for a in achadas if a.startswith(f"{rel}: ") and frase in a]
            self.assertEqual(len(casam), 1, (rel, frase, achadas))
        self.assertIn("(modo 1: siga o execute-modo-1.md, sem start)",
                      (ROOT / "scripts/dispatch.py").read_text(encoding="utf-8"))
        want = {
            "skills/engajar/references/state-format.md": ["`execute-media-pequena.md`, section 8",
                                                          "`execute-retomada.md`, section 6"],
            "skills/engajar/SKILL.md": ["`execute-media-pequena.md`, section 8", "`references/execute-modo-1.md` (section 7)",
                                        "`references/execute-retomada.md` (section 6)"],
            "skills/piloto-automatico/SKILL.md": ["`references/execute-media-pequena.md`, section 8"],
            "src/context/STARCODE.md": ["`execute-*.md` files"],
        }
        for rel, frases in want.items():
            text = (ROOT / rel).read_text(encoding="utf-8")
            for frase in frases:
                self.assertIn(frase, text, rel)

    def test_decisions_e_changelog(self):  # C10, R10
        entry = _entry("SC-213")
        self.assertRegex(entry.splitlines()[0], r"^### SC-213: \S")
        for parte in ("- **Problema**:", "- **Decisão**:", "- **Motivo**:", "- **Por que não é bug**:"):
            self.assertEqual(entry.count(parte), 1, parte)
        decisao = entry[entry.index("- **Decisão**: ") + len("- **Decisão**: "):entry.index("- **Motivo**")]
        pedacos = re.split(r"(?:^|(?<=\. ))(R\d+): ", decisao)
        partes = dict(zip(pedacos[1::2], pedacos[2::2]))  # {"R1": texto de R1, ...}
        self.assertEqual(list(partes), [f"R{i}" for i in range(1, 11)])
        # os termos de cada requisito têm de estar no trecho dele, não espalhados pela decisão
        exigidos = {
            "R1": ["`FIX_RULES`", "`dispatch.py`", "a suíte inteira verde", "`impact.py select --diff <base>`", "`rodar tudo`",
                   "a seleção falhar", "gate `ticket`"],
            "R2": ["`WORKER_RULES`", "`- Testes:`", "logo antes da linha do gate `ticket`", "linha de veredito do `impact.py`"],
            "R3": ["`laforge`", "`mccoy`", "`impact.py`", "`Run unit` da spec", "CI", "The gates still run the whole suite"],
            "R4": ["python -m unittest discover -s tests --durations 20", "Medição: 1.100 testes em 731,326 s", "C:",
                   "commit 844421b", "medicao-durations.txt", "linha de base 1.083 testes em 1.519 s", "Os 5 mais lentos",
                   "`test_check_fails_when_manifest_version_diverges` 18,128 s", "`test_diagnostico_failures` 9,795 s",
                   "Nada foi acelerado"],
            "R5": ["`AGENTS.md`", "JSON escrito por script", "markdown", "o Handoff continua markdown escrito pelo `handoff.py`"],
            "R6": ["`execute.md` vira índice", "seções 0 e 1", "a tabela dos seis arquivos", "carregar só o da etapa em curso",
                   "700 palavras"],
            "R7": ["`execute-*.md`", "`# Execute: <etapa>`", "`execute.md`", "cabeçalhos `## `", "uma única vez no conjunto"],
            "R8": ["só movido", "`execute_text()`", "`tests/test_support.py`"],
            "R9": ["`engajar`", "`state-format.md`", "`piloto-automatico`", "`STARCODE.md`", "`dispatch.py`",
                   "`siga o execute-modo-1.md, sem start`"],
            "R10": ["esta entrada", "`CHANGELOG.md`"],
        }
        for rotulo, termos in exigidos.items():
            for termo in termos:
                self.assertIn(termo, partes[rotulo], f"{rotulo}: {termo}")
        why = entry[entry.index("- **Por que não é bug**"):]
        for nome in ("test_fix_brief_usa_selecao_do_impact", "test_brief_do_ticket_usa_selecao_do_impact",
                     "test_laforge_e_mccoy_rodam_a_selecao", "test_decisions_registra_a_medicao",
                     "test_agents_tem_regra_de_estado", "test_execute_md_vira_indice",
                     "test_cabecalhos_no_arquivo_certo", "test_testes_leem_o_execute_por_execute_text",
                     "test_referencias_apontam_o_arquivo_novo", "test_decisions_e_changelog"):
            self.assertIn(f"`{nome}`", why)
        log = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        unreleased = log[log.index("## [Unreleased]"):]
        unreleased = unreleased[:unreleased.index("\n## [", 5)] if "\n## [" in unreleased[5:] else unreleased
        self.assertEqual(sum(1 for ln in unreleased.splitlines() if "(SC-213)" in ln), 1)


if __name__ == "__main__":
    unittest.main()
