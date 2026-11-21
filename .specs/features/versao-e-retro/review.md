**Round**: 1
**Verdict**: APPROVE
**Reviewer**: claude · claude-opus-5-5

## TL;DR
APPROVE. Sem achados que bloqueiem o merge, só um nit.

- **Briefs:** os quatro passam a ter o título na primeira linha e o `**Plugin:**` logo abaixo. No q-brief e no screens-brief, a linha `Repositório:` vem depois do Plugin.
- **Handoff:** o `start` grava a versão no campo novo `**Plugin:**`.
- **Aviso de versão:** o `version_warning` só dispara no repositório do StarCode quando a versão difere, e vai para o stderr.
- **`retros.py`:** acha as colunas pelo nome do cabeçalho. No `estado`, troca só o intervalo entre os delimitadores da célula e preserva o fim de linha original.
- **Nit W1:** o `sc.plugin_version` duplica o `plugin_version` do banner.

## Achados

| ID | Severity | Where | Finding | Evidence | State |
|---|---|---|---|---|---|
| W1 | nit | `scripts/starcode_common.py:29` | O `sc.plugin_version` repete a leitura de `hooks/scripts/banner.py:128` (manifesto, `crew.json`, `VERSION`), mas devolve `desconhecida` em vez de `None`. O banner já importa o `starcode_common` e pode usar a mesma função, para as duas leituras não divergirem. | `hooks/scripts/banner.py:128` | aberto |

## Escada determinística
- CI local em c717f8b (evidência do PR): `build --check`, `check_decisions`, `claude plugin validate --strict` e a suíte inteira (1091 testes, 1 pulado), todos verdes.
- Módulos tocados, todos OK: `test_versao_e_retro` 8, `test_dispatch` 56, `test_licoes_no_brief` 5, `test_handoff` 13, `test_dispatch_start` 17 e `test_banner` 24.
- `retros.py abertas` no repositório real, só leitura: 5 linhas abertas (4 da retro desta feature e 1 de fase-9) e `34 retro(s) sem coluna Estado`.
- `scan_bypasses.py`: 0 candidatos.

## Pesquisa
Nenhuma superfície externa: só a biblioteca padrão.
