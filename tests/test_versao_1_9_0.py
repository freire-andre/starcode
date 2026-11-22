"""SC-214: versão 1.9.0 em manifestos, CHANGELOG e README."""
from __future__ import annotations

import ast
import json
import re
import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from helpers import ROOT
from test_support import changelog_recent

import release

# Itens do [Unreleased] de 8b86df0:CHANGELOG.md, congelados aqui: a prova não depende do histórico do git.
ITENS_1_9_0 = [
    ("### Alterado",
     "- Suíte rápida, regra de estado e `execute.md` dividido (SC-213): o worker de ticket e a correção pós-Q rodam os testes escolhidos pelo `impact.py` (a suíte inteira só com `rodar tudo` ou seleção falha; ela segue no gate de done e no CI), o `AGENTS.md` ganha a regra de estado novo em JSON e o `execute.md` vira índice com seis arquivos `execute-*.md`; medição da suíte anotada no `DECISIONS.md`."),
    ("### Alterado",
     "- Versão do plugin no despacho e estado das ações de retro (SC-212): todo brief do `dispatch.py` traz `**Plugin:** StarCode <versão>` logo abaixo do título e o `start` grava a versão no campo `**Plugin:**` do Handoff (`handoff.py set --plugin`); no repositório do StarCode, versão diferente do `VERSION` gera aviso no stderr; a tabela da retro da Guinan ganha a coluna `Estado` (`aberto` nas linhas novas) e o novo `scripts/retros.py` lista as abertas (`abertas`) e muda o estado (`estado`)."),
    ("### Alterado",
     "- Catálogo conferido e adaptador único da Orca (SC-211): `model_info.download` só grava JSON com ao menos um provedor com `models` objeto; `name` e `description` do catálogo saem sem caracteres de controle e cortados em 80 e 200; o catálogo é interpretado uma vez por processo; novo `scripts/orca_cli.py` (`resolve`, `env`, `run`) usado por `screens.py`, pelo banner e pelo `dispatch.py`; `.specs/stack/orca.md` documenta o CLI da Orca 1.4.268."),
    ("### Alterado",
     "- Restauração pelo snapshot e telas restritas (SC-210): o `snapshot.py restore` lê o `May change` do `tasks.md` (ou do `spec.md`) gravado no commit do snapshot e sai com 2 se não houver nenhum; o `screens.py capture` só aceita host local (ou `--allow-host`) e `--out` em `captures/<nome>.running.png`; o veredito do `screens.md` casa pelo nome inteiro; PNG sem `IDAT`, com `IDAT` vazio ou com chunk truncado é recusado."),
    ("### Alterado",
     "- Regra `covers` igual em Windows e Linux (SC-209): `gates_common.covers` deixa o `fnmatch` e passa a ter regra própria que diferencia maiúsculas, com `*` e `?` sem atravessar `/`, `**` como segmento inteiro (zero ou mais segmentos) e `[`/`]` literais; pasta, igualdade e recusa de caminho absoluto ou com `..` não mudam."),
    ("### Alterado",
     "- Falhas do start e do settle (SC-208): o recibo do `worker-start` é lido a partir do primeiro `{` e, sem id de despacho, o `start` mantém a entrada, avisa `worker ativo sem id de despacho: ...` e sai com 3; o `settle` diferencia `conflito no merge de <T>` de `merge de <T> falhou: <erro do git>` e só aborta com merge em andamento; `handoff.py set` roda sob trava por feature (`.handoff.lock`, 5 s, `handoff ocupado: <pasta>`); novo `starcode_common.run_git` com tempo limite (124 e 127) adotado por `snapshot.py`, `impact.py` e `dispatch.py`."),
    ("### Alterado",
     "- Manutenção da Ponte (SC-207): `handoff.parse_dispatch_entry` é o único leitor da entrada do `**Dispatched:**` (usado por `ponte.py` e `dispatch.py`; a Ponte passa a mostrar o modelo `<cli>:<modelo>` do `start`); o plugin da Orca perde `storage:own`, só aceita `issue.url` de `https://linear.app/`, casa agente por token inteiro e acha o nome do worktree com `\\`; o passo do `orca` no CI avisa e registra no resumo quando pula."),
    ("### Alterado",
     "- Config local nos worktrees (SC-206): `local_config_path` cai para o `.starcode/config.local.json` do worktree principal quando o worktree ligado não tem o seu (o do worktree atual vence; `git` falhando mantém a leitura atual); a entrada local vale inteira (`cli` e `model` juntos, validador recusa a parcial e a vazia) e `effective_crew` não mistura mais o CLI do usuário com o modelo local; `model` recusa vazio, espaço, `-` inicial e caractere fora de `[A-Za-z0-9._:/+@-]` no `crew` do usuário, no `crew` local e em `fleet.workers`; `parse_model_arg` só separa `@<nível>` de custo conhecido e recusa o id que o validador recusa; o banner avisa quando o arquivo local está versionado ou fora do `.gitignore`; `suggest` mantém o membro já configurado com CLI disponível e lista `mantidos:`."),
    ("### Alterado",
     "- Lições no brief: `lessons_section` ordena por número de features, depois data e ID (limite 10) e abre com a frase do Q; no brief de worker a seção vem antes das regras fixas (no do Q segue no fim); novo `dispatch.py fix-brief <slug> [--out]` gera o brief da correção pós-Q com os achados abertos, o `May change`, as lições e as regras fixas, e o `execute.md` (seção 5) manda usá-lo (SC-205)."),
    ("### Alterado",
     "- Paridade declarada: o `README.md` troca \"com os 4 CLIs suportados\" por três níveis de suporte (Claude Code principal, Codex secundário completo, Antigravity CLI e OpenCode melhor esforço) e o `docs/compatibilidade.md` ganha `## Nível de suporte` com a tabela e as pendências do dono (aceite das Fases 8 e 9 no Codex) (SC-204)."),
    ("### Alterado",
     "- Roteamento do Worf e do McCoy fora do StarCode: descrições presas ao StarCode com \"Not for\" (review de PR e depuração genéricos) e 3 casos novos em `evals/routing/` (36 frases) (SC-203)."),
    ("### Alterado",
     "- Escrita concorrente dos arquivos de sessão: `locked` (trava do SO no `<arquivo>.lock`, 5 s) e `write_json_atomic` (temporário único) no `starcode_common.py`; `update_sessions`, `set_progress`, `write_session` e o `git_mode.py` (via novo `update_session`) leem, mudam e gravam sob a trava, sem `session.tmp`; trava esgotada deixa o hook em silêncio e faz `crew_live.py`/`git_mode.py` saírem com 2 e `trava ocupada: <arquivo> (tente de novo)` (SC-202)."),
    ("### Alterado",
     "- Frota travada só com workers atrasados: quando o `dispatch.py batch` sai vazio e toda entrada ativa do `Dispatched` está ` · blocked`, o JSON ganha `\"stalled\"` e o texto a linha `travado:`; o `execute.md` (2F) manda o Picard parar com duas opções, cancelar com confirmação ou seguir esperando (SC-200)."),
    ("### Alterado",
     "- Fechamento de achado do Q: `dispatch.py close-finding <slug> <n> --commit <sha> --cover <C<n>|test_nome>` grava `<sha> · <cobertura>` na célula `Closed` conferindo o commit e a cobertura; o gate `done` exige cobertura em cada achado e acusa linha de tabela com número errado de células (`verification.md:<linha>: ...`); o brief do Q manda escrever pipe de célula como `&#124;` (SC-199)."),
    ("### Alterado",
     "- Fase `pr-review` no Handoff (entre o PR aberto e o merge): `done` só depois do merge nos modos 3 e 4, `run_gates.py proofs` e `done` no novo HEAD depois de cada correção do Worf, Guinan em modo só lições depois da última rodada (só com achado `blocker` ou `should-fix`) e `piloto.py encerrar` na parada da autorização de merge; a F9-5 fica (SC-198)."),
    ("### Alterado",
     "- Caminho da PEQUENA (MÉDIA mínima): a spec `**Size**: SMALL` do Picard (só `## Scope`, `## Checks`, `**May change**:` e `**Linear**:`, no máximo 5 checks e 3 arquivos) passa no gate de spec e no `execute` sem aprovação, vai como `T1` pelo `dispatch.py start`/`settle`, e o novo `dispatch.py q-waive` grava `**Verification:** waived (PEQUENA)`, que o gate `done` aceita com o aviso `Q dispensado (PEQUENA)`; sem Guinan, com Worf no PR (SC-197)."),
    ("### Alterado",
     "- `git_guard.py`: bloqueia `git checkout -f`/`--force`, `git switch --discard-changes|-f|--force` e `git stash drop|clear` em qualquer repo; analisa o comando interno de `bash -lc`/`-ec` (flags curtas com `c`); no modo 1 bloqueia `cherry-pick`, `revert`, `am`, `pull` e `rebase` (exceto `--abort`, `--continue`, `--quit`, `--skip` e `-n`/`--no-commit`); ignora o corpo de heredoc que é só dado e continua analisando o que vai para um shell (SC-196)."),
    ("### Alterado",
     "- Scanner de segredos: escaneia o texto inteiro do comando que publica (inclusive heredoc), passa a cobrir `gh issue create|comment|edit` e `gh pr review`, e deixa de acusar string de conexão com placeholder ou host local, `AUTHOR_EMAIL` e URL sem credencial (SC-195)."),
    ("### Alterado",
     "- `review_gate.py` ganha `require_text` (no lugar do `blank`, com teste de tabela) e `argparse`: `--help` sai com 0 e sem argumento o exit é diferente de 0; um teste roda `--help` em cada script de `dist/claude/scripts/review/`; a retro da fase 9 ganha a coluna `Estado` (SC-190)."),
    ("### Alterado",
     "- Correções do lote 1 (SC-188): cabeçalho da Guinan na forma `(F6-6)` das outras skills (nenhuma do `dist/` tem `Header first`); `sees()` das provas exige palavra inteira e aceita a docstring do `unittest` verboso; comando de prova passa de 1800 s é encerrado e vira `fail - tempo limite (1800 s)`; o scanner de segredos só pula como binário o diff `Binary files ... differ` ou com byte nulo e avisa no stderr quando pula um arquivo."),
    ("### Alterado",
     "- Freios do piloto automático (SC-187): a aprovação `piloto:` vale com o piloto ativo ou encerrado (mandato confirmado pelo usuário e decisão citada registrada até o `**Encerrado:**`); `piloto.py registrar` recusa com exit 3 a 3ª decisão `⚠️ revisar` da feature (o freio fica) e grava \"devolvido ao usuário\" fora dele; `--categoria dependencia|esquema|arquitetura` exige um `M<n>` em `--basis`. A skill `piloto-automatico` descreve os três."),
    ("### Alterado",
     "- `dispatch.py q-cli` segue o `qStrategy` do config do usuário quando o campo existe: `orca-worker` é o percurso atual, `self-verified` para e devolve `self-verified`, `opencode-subagent` é pulado com aviso no stderr (ainda não implementado). Sem o campo, nada muda. A skill `config` deixa de oferecer `opencode-subagent`."),
    ("### Corrigido",
     "- Piloto e `model_info` (verificação retroativa da 1.8.0, SC-186): `piloto.py status` marca toda decisão `baixa` com `⚠️ revisar`, `model_info` avisa contexto `0` (menor que 200k) em `pesado` e `execucao` sem avisar quando o contexto não existe, e o banner lista só piloto ativo com mandato confirmado, a mesma regra do `ativo`."),
    ("### Corrigido",
     "- OpenCode: `install_local.py` copia o pacote para `~/.config/opencode/starcode` e aponta as skills e o plugin para essa cópia, em vez do `dist/` do clone. A troca da cópia é atômica o bastante para não deixar pasta incompleta: se a cópia falhar, a antiga fica intacta, o `opencode.json` não é gravado e o comando sai com 1 e `opencode: falha ao copiar <origem> para <destino>: <motivo>`. Caminhos de skill do StarCode que não existem mais saem do `opencode.json`."),
]

ISSUES = ([186, 187, 188, 190] + list(range(195, 201)) + list(range(202, 214)))


def _itens(secao: str) -> list[tuple[str, str]]:
    """(seção `### ...`, linha do item `- ...`) na ordem do texto."""
    atual, itens = "", []
    for linha in secao.splitlines():
        if linha.startswith("### "):
            atual = linha
        elif linha.startswith("- "):
            itens.append((atual, linha))
    return itens


def _json(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

# Exceções da varredura C5, por (arquivo, função) e com o motivo: só testes que conferem o formato ou a
# existência da seção [Unreleased], ou que provam o próprio helper e a própria varredura.
EXCECOES: dict[tuple[str, str], str] = {
    ("test_support.py", "changelog_recent"): "define o helper que recorta o [Unreleased] e a versão mais recente",
    ("test_versao_1_9_0.py", "test_changelog_fecha_1_9_0"):
        "confere a existência e a ordem das seções [Unreleased] (vazia), 1.9.0 e 1.8.0",
    ("test_versao_1_9_0.py", "test_changelog_recent"):
        "prova o helper com um CHANGELOG de fixture em diretório temporário",
    ("test_release.py", "setUp"):
        "grava o CHANGELOG de fixture (formato da seção [Unreleased] do release.py) em diretório temporário",
    ("test_release_docs.py", "test_changelog_has_1_0_0_section"):
        "confere o formato do CHANGELOG (Keep a Changelog) e a existência da seção [Unreleased]",
}


def _e_changelog(texto: str) -> bool:
    """Literal que é o nome ou o caminho do arquivo (e não uma frase que o cita)."""
    return re.fullmatch(r"(.*[/\\])?CHANGELOG\.md", texto) is not None


def _tipos(no: ast.AST, portadores: dict[str, set[str]]) -> set[str]:
    """Tipos tocados por uma expressão: cl (CHANGELOG.md), un (Unreleased), is (SC-<n>)."""
    achou: set[str] = set()
    for n in ast.walk(no):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            if _e_changelog(n.value):
                achou.add("cl")
            if "Unreleased" in n.value:
                achou.add("un")
            if "SC-" in n.value:
                achou.add("is")
        elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            achou |= portadores.get(n.id, set())
        elif isinstance(n, ast.Attribute):
            achou |= portadores.get("." + n.attr, set())
    return achou


def _corpo_proprio(fn: ast.AST):
    """Nós do corpo da função, sem entrar nas funções aninhadas."""
    pilha = list(ast.iter_child_nodes(fn))
    while pilha:
        n = pilha.pop()
        yield n
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            pilha.extend(ast.iter_child_nodes(n))


def _violacoes(src: str, arquivo: str, excecoes: dict) -> list[str]:
    """`arquivo::função` de cada função que lê o CHANGELOG e busca Unreleased ou issue fora do helper."""
    arvore = ast.parse(src)
    funcoes = [n for n in ast.walk(arvore) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    locais = {id(x) for f in funcoes for x in _corpo_proprio(f)}
    portadores: dict[str, set[str]] = {}
    alvos = []
    for n in ast.walk(arvore):
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and n.value is not None:
            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                for x in ast.walk(t):
                    # Nome de módulo ou de classe, ou atributo (self.x, Classe.x); local de função já conta no corpo.
                    if isinstance(x, ast.Attribute):
                        alvos.append(("." + x.attr, n.value))
                    elif isinstance(x, ast.Name) and id(n) not in locais:
                        alvos += [(x.id, n.value), ("." + x.id, n.value)]

    def da_funcao(f):
        tipos: set[str] = set()
        for x in _corpo_proprio(f):
            if isinstance(x, (ast.Constant, ast.Name, ast.Attribute)):
                tipos |= _tipos(x, portadores)
        return tipos

    def usa_changelog(f) -> bool:
        """Lê o CHANGELOG de fato: literal fora de uma atribuição simples a nome local, carregamento desse
        nome local, ou carregamento de um portador de fora da função (constante, atributo, helper)."""
        corpo = list(_corpo_proprio(f))
        soltos: set[int] = set()  # literais que só ligam um nome local (usar o nome é que conta)
        locais_cl: set[str] = set()
        for x in corpo:
            if isinstance(x, ast.Assign) and all(isinstance(t, ast.Name) for t in x.targets):
                lit = [y for y in ast.walk(x.value)
                       if isinstance(y, ast.Constant) and isinstance(y.value, str) and _e_changelog(y.value)]
                if lit:
                    soltos |= {id(y) for y in lit}
                    locais_cl |= {t.id for t in x.targets}
        for x in corpo:
            if (isinstance(x, ast.Constant) and isinstance(x.value, str) and _e_changelog(x.value)
                    and id(x) not in soltos):
                return True
            if (isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)
                    and (x.id in locais_cl or "cl" in portadores.get(x.id, set()))):
                return True
            if isinstance(x, ast.Attribute) and "cl" in portadores.get("." + x.attr, set()):
                return True
        return False

    for _ in range(len(alvos) + len(funcoes) + 1):
        antes = {k: set(v) for k, v in portadores.items()}
        for nome, valor in alvos:
            portadores.setdefault(nome, set()).update(_tipos(valor, portadores))
        for f in funcoes:
            portadores.setdefault(f.name, set()).update(da_funcao(f))
        if portadores == antes:
            break
    achados = []
    for f in funcoes:
        tipos = da_funcao(f)
        if usa_changelog(f) and ("un" in tipos or "is" in tipos) and (arquivo, f.name) not in excecoes:
            achados.append(f"{arquivo}::{f.name}")
    return sorted(set(achados))


class Versao190Tests(unittest.TestCase):
    def test_versao_1_9_0_em_todos_os_manifestos(self):  # C2
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "1.9.0")
        self.assertEqual(_json("src/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json("dist/orca/orca-plugin.json")["version"], "1.9.0")
        self.assertEqual(_json(".claude-plugin/marketplace.json")["plugins"][0]["version"], "1.9.0")
        market = _json(".agents/plugins/marketplace.json")
        self.assertEqual(len(market["plugins"]), 1)
        plugin = market["plugins"][0]
        self.assertEqual(plugin["name"], "starcode")
        self.assertEqual(plugin["source"], {"source": "local", "path": "./dist/codex"})
        self.assertNotIn("version", plugin)
        self.assertEqual(_json("dist/codex/.codex-plugin/plugin.json")["version"], "1.9.0")
        for alvo in ("antigravity", "claude", "codex", "opencode", "orca"):
            path = ROOT / "dist" / alvo / "crew.json"
            self.assertTrue(path.is_file(), str(path))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["version"], "1.9.0", str(path))

    def test_changelog_fecha_1_9_0(self):  # C3
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        m = re.search(r"^## \[Unreleased\]\n(.*?)^## \[1\.9\.0\] - 2026-11-22\n(.*?)^## \[1\.8\.0\]",
                      text, re.M | re.S)
        self.assertIsNotNone(m, "ordem Unreleased, 1.9.0, 1.8.0 não encontrada")
        self.assertEqual(m.group(1).strip(), "")
        secao = m.group(2)
        self.assertEqual(sum(1 for l in secao.splitlines() if l.startswith("- ")), 24)
        self.assertEqual(sorted(set(re.findall(r"SC-\d+", secao))), sorted(f"SC-{n}" for n in ISSUES))
        self.assertEqual(len(ISSUES), 22)
        self.assertIn("### Alterado", secao)
        self.assertIn("### Corrigido", secao)
        self.assertEqual(len(ITENS_1_9_0), 24)
        self.assertEqual(_itens(secao), ITENS_1_9_0)
        # Seção integral extraída de forma independente: do cabeçalho até o próximo `## [`.
        linhas, dentro, corpo = text.splitlines(), False, []
        for linha in linhas:
            if linha.startswith("## ["):
                if dentro:
                    break
                dentro = linha == "## [1.9.0] - 2026-11-22"
                continue
            if dentro:
                corpo.append(linha)
        esperado = chr(10).join(corpo).strip(chr(10)) + chr(10)
        self.assertIn("SC-213", esperado)
        self.assertEqual(release._notes(ROOT, "1.9.0"), esperado)

    def test_changelog_recent(self):  # C5
        fake = """# Changelog

## [Unreleased]

- novo (SC-1)

## [3.0.0] - 2026-03-03

- do tres (SC-3)

## [2.0.0] - 2026-02-02

- do dois (SC-2)

## [1.0.0] - 2026-01-01

- do um (SC-4)
"""
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "CHANGELOG.md").write_text(fake, encoding="utf-8")
            got = changelog_recent(Path(tmp))
        esperado = """## [Unreleased]

- novo (SC-1)

## [3.0.0] - 2026-03-03

- do tres (SC-3)

"""
        self.assertEqual(got, esperado)
        for fora in ("SC-2", "SC-4", "2.0.0", "1.0.0"):
            self.assertNotIn(fora, got)

    def test_nenhum_teste_le_unreleased_nem_busca_issue_fora_do_helper(self):  # C5
        arquivos = sorted((ROOT / "tests").glob("*.py"))
        self.assertGreater(len(arquivos), 30)
        achados = []
        for path in arquivos:
            achados += _violacoes(path.read_text(encoding="utf-8"), path.name, {})
        # Toda função que lê o CHANGELOG e busca Unreleased/issue está na tabela de exceções, e só ela.
        self.assertEqual(sorted(achados), sorted(f"{a}::{f}" for a, f in EXCECOES))
        for motivo in EXCECOES.values():
            self.assertTrue(motivo.strip())

    def test_varredura_pega_cada_forma(self):  # C5
        cl = '(ROOT / "CHANGELOG.md").read_text()'
        casos = {
            "constante de módulo com o caminho": (
                'CL = ROOT / "CHANGELOG.md"\n'
                'class T:\n    def test_a(self):\n        self.assertIn("SC-9", CL.read_text())\n'),
            "atributo de classe com o caminho": (
                'class T:\n    P = ROOT / "CHANGELOG.md"\n'
                '    def test_a(self):\n        self.assertIn("SC-9", self.P.read_text())\n'),
            "atributo montado no setUp": (
                'class T:\n    def setUp(self):\n        self.p = ROOT / "CHANGELOG.md"\n'
                '    def test_a(self):\n        self.assertIn("SC-9", self.p.read_text())\n'),
            "helper local que lê o arquivo": (
                f'def _texto():\n    return {cl}\n'
                'def test_a():\n    assert "SC-9" in _texto()\n'),
            "helper aninhado que lê o arquivo": (
                'def test_a():\n    def ler():\n        return open("CHANGELOG.md").read()\n'
                '    assert "SC-9" in ler()\n'),
            "número de issue em constante de módulo": (
                f'N = "SC-9"\ndef test_a():\n    t = {cl}\n    assert N in t\n'),
            "número de issue em f-string": (
                f'def test_a():\n    t = {cl}\n    for n in (1, 2):\n        assert f"SC-{{n}}" in t\n'),
            "Unreleased em constante de módulo": (
                f'U = "## [Unreleased]"\ndef test_a():\n    t = {cl}\n    assert U in t\n'),
            "constante encadeada": (
                'A = "CHANGELOG.md"\nB = ROOT / A\n'
                'def test_a():\n    assert "Unreleased" in B.read_text()\n'),
            "helper chama helper": (
                'def _p():\n    return ROOT / "CHANGELOG.md"\n'
                'def _t():\n    return _p().read_text()\n'
                'def test_a():\n    assert "SC-9" in _t()\n'),
        }
        for nome, src in casos.items():
            with self.subTest(nome):
                self.assertTrue(_violacoes(src, "x.py", {}), nome)
        limpos = {
            "só o helper": 'def test_a():\n    assert "SC-9" in changelog_recent(ROOT)\n',
            "sem CHANGELOG": 'def test_a():\n    assert "SC-9" in texto\n',
            "CHANGELOG sem issue nem Unreleased": f'def test_a():\n    assert "1.9.0" in {cl}\n',
        }
        for nome, src in limpos.items():
            with self.subTest(nome):
                self.assertEqual(_violacoes(src, "x.py", {}), [], nome)
        # A exceção vale só para a função citada, não para o arquivo todo.
        dois = (f'def test_a():\n    assert "SC-9" in {cl}\n'
                f'def test_b():\n    assert "SC-8" in {cl}\n')
        self.assertEqual(_violacoes(dois, "x.py", {}), ["x.py::test_a", "x.py::test_b"])
        self.assertEqual(_violacoes(dois, "x.py", {("x.py", "test_a"): "motivo"}), ["x.py::test_b"])

    def test_readme_estado_1_9_0(self):  # C4
        linhas = [l for l in (ROOT / "README.md").read_text(encoding="utf-8").splitlines() if l.startswith("Estado:")]
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0], "Estado: **v1.9.0**, com suporte em três níveis:")
        self.assertNotIn("v1.8.0", linhas[0])


if __name__ == "__main__":
    unittest.main()
