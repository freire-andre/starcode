# Correções pontuais do lote 1: Spec

**Approved**: 2026-11-16 - user: "sim"

**Size**: MEDIUM
**Risk triggers**: Segurança (o scanner de segredos decide o que é escaneado)
**Status**: Approved
**Linear**: SC-188
**May change**: skills/guinan/SKILL.md, tools/build.py, scripts/gates/check_proofs.py, hooks/scripts/secret_scan.py, tests/test_build.py, tests/test_check_proofs.py, tests/test_secret_scan.py, tests/test_crew_hook.py, tests/test_crew_hook_agy_opencode.py, tests/test_piloto.py, DECISIONS.md, CHANGELOG.md, dist/

## Context
Itens 1.2, 1.3 e 1.4 da triagem v2. Discovery: `.specs/features/lote1-correcoes/context.md`.
- 1.2: a Guinan usa `**Header first:**` sem `(F6-6)`. Por isso o parágrafo chega aos 4 `dist/*/skills/guinan/SKILL.md` (`tools/build.py:222-225`).
- 1.3: `sees()` (`scripts/gates/check_proofs.py:78-84`) casa um nome dentro de outro maior e não reconhece o teste com docstring. Além disso, a prova roda sem tempo limite (`:71-75`).
- 1.4: o scanner pula o arquivo cujo diff contém "Binary files" em qualquer lugar (`hooks/scripts/secret_scan.py:166`). Também pula sem avisar quando o `git diff` do arquivo falha (`:156-157`).

## Scope
- Cabeçalho da Guinan na forma das outras skills, e um teste que cobre todas as skills do `dist/`.
- `sees()` com palavra inteira e com o caso da docstring; tempo limite fixo de 1800 s por comando de prova.
- O scanner reconhece binário só pelo cabeçalho do git e avisa quando pula um arquivo.

## Non-Goals
- 1.5, 1.6 e 1.7 (próximas missões).
- Helper único de `git` com tempo limite (N.6), e tempo limite nas outras chamadas de `subprocess`.
- Tornar o tempo limite configurável.

## Decisions
| Item | Options | User answer |
|---|---|---|
| Divisão do lote 1 | 1.2+1.3+1.4 agora / lote inteiro / um item por missão | approved - user: "1.2+1.3+1.4 agora (Recomendado)" |
| Tempo limite por prova | 30 min fixo / 30 min ajustável por variável / 10 min fixo | approved - user: "30 min fixo (Recomendado)" |

## Requirements
- **R1** - The system SHALL ter em `skills/guinan/SKILL.md` o parágrafo `**Header first (F6-6):**`. Nenhum `dist/<cli>/skills/<skill>/SKILL.md`, para os 4 CLIs e todas as skills, SHALL conter o texto `Header first`.
- **R2** - WHEN uma palavra esperada pela prova começa ou termina com caractere de palavra (`\w`) THEN `sees()` SHALL exigir que não haja caractere de palavra colado do lado correspondente na saída. `test_login PASSED` não casa com `test_login_extra PASSED`, e `test_login (m.C.test_login) ... ok` casa com a mesma linha.
- **R3** - WHEN uma linha da saída é exatamente `<nome> (<id pontuado>)` (forma do unittest verboso com docstring) THEN `sees()` SHALL aceitar o casamento sobre essa linha unida à seguinte por um espaço. `test_x (m.C.test_x)` seguido de `Docstring ... ok` casa com `test_x (m.C.test_x) ... ok`, e `test_x` seguido de `... ok` continua sem casar.
- **R4** - WHEN um comando de prova (`Run`, prova avulsa ou `Build`) passa de 1800 s THEN o `check_proofs` SHALL encerrá-lo e registrar no `proofs.md` o resultado `fail - tempo limite (1800 s)` em cada linha que depende dele, e o veredito SHALL ser falha.
- **R5** - WHEN o diff de um arquivo de texto contém a frase `Binary files` numa linha adicionada THEN o scanner SHALL escanear o arquivo. Ele SHALL pular como binário só o diff que tem uma linha que casa `^Binary files .* differ$`, ou que contém o byte nulo.
- **R6** - IF o `git diff` de um arquivo falha ou passa do tempo limite THEN o scanner SHALL escrever no stderr `StarCode hook: secret_scan pulou <arquivo> (<motivo>)` e SHALL seguir para os outros arquivos, sem bloquear por causa desse arquivo.
- **R7** - The system SHALL ter no `DECISIONS.md` a entrada da issue desta feature (`### SC-188:`) com **Problema**, **Decisão** (R1 a R6, com o limite de 1800 s e a forma `Binary files ... differ`), **Motivo** e **Por que não é bug** citando os testes. SHALL também ter uma linha em `CHANGELOG.md` `[Unreleased]`.

## Edge Cases
- Palavra esperada só com pontuação (`...`): não tem borda de palavra, casa como hoje (R2, C2).
- Nome com docstring na última linha da saída, sem linha seguinte: não casa (R3, C3).
- Arquivo de texto com a frase "Binary files" numa linha de contexto ou removida: não muda nada, porque só as linhas `+` são escaneadas (R5).

## Open Questions
None.

## Checks

**Build**: `python tools/build.py --check`; `claude plugin validate dist/claude --strict`; `python scripts/check_decisions.py`
**Run unit**: `python -m unittest discover -s tests -v 2>&1`

**C1** - Cabeçalho da Guinan em `(F6-6)` e nenhum `Header first` em `dist/*/skills/*/SKILL.md` (R1)
Proof: run unit | test_nenhuma_skill_do_dist_tem_header_first (test_build.BuildTests.test_nenhuma_skill_do_dist_tem_header_first) ... ok

**C2** - Tabela de `sees()`: `test_login` vs `test_login_extra`, borda antes e depois, `...` sem borda (R2)
Proof: run unit | test_sees_palavra_inteira (test_check_proofs.CheckProofsTests.test_sees_palavra_inteira) ... ok

**C3** - Docstring entre o nome e o `... ok` casa; `test_x\n... ok` e o nome na última linha não casam (R3)
Proof: run unit | test_sees_docstring_do_unittest (test_check_proofs.CheckProofsTests.test_sees_docstring_do_unittest) ... ok

**C4** - Prova que passa do tempo limite (limite reduzido no teste) vira `fail - tempo limite (1800 s)` no `proofs.md`, com veredito de falha (R4)
Proof: run unit | test_prova_com_tempo_limite (test_check_proofs.CheckProofsTests.test_prova_com_tempo_limite) ... ok

**C5** - Arquivo de texto com `Binary files` numa linha adicionada e um segredo é bloqueado; binário de verdade é pulado (R5)
Proof: run unit | test_frase_binary_files_em_texto_e_escaneada (test_secret_scan.CommitTests.test_frase_binary_files_em_texto_e_escaneada) ... ok

**C6** - Falha do `git diff` de um arquivo gera a linha exata no stderr e não bloqueia (R6)
Proof: run unit | test_arquivo_pulado_avisa (test_secret_scan.CommitTests.test_arquivo_pulado_avisa) ... ok

**C7** - Entrada do `DECISIONS.md` com os quatro campos, os termos de R1 a R6 na Decisão, testes citados e linha no CHANGELOG (R7)
Proof: run unit | test_decisions_lote1_correcoes (test_build.BuildTests.test_decisions_lote1_correcoes) ... ok

## Handoff

**Phase:** done
**Size:** MÉDIA
**Git mode:** 3
**Next:** 1.5 + 1.7 (docs)
**Linear:** SC-188
**Integration branch:** feature/lote1-correcoes
**Last integrated:** 9d9be01
**Dispatched:** none
**Settled:** 2026-11-16: spec + issue: "sim"; 2026-11-16: May change ampliado com tests/test_piloto.py (Picard: test_decisions_piloto_freios depende da SC-187 ser a última entrada); 2026-11-16: push + PR: "sim"; 2026-11-16: PR aberto: https://github.com/freire-andre/starcode/pull/61; 2026-11-16: review publicado; W1 aceito como está; merge + Done: "Sim, merge e Done"
**Attempts:** none
**Reports:** 2026-11-16: T1: R1–R7 em 31fa777; 956 OK; ticket gate verde; SC-188 ficou antes da SC-187 no DECISIONS porque test_decisions_piloto_freios lê a SC-187 até o fim do arquivo; 2026-11-16: provas verdes; 2026-11-16: Q: codex · effective unconfirmed · FAIL, 4 achados (byte nulo depois de 8000 caracteres; C4 sem conferir o encerramento; C7 com termos soltos; R6 sem o caso de tempo limite); 956 OK; q-check 0; 2026-11-16: T1-fix: 5c33211, 2d5c921, 8183cfe (4 achados + ordem do DECISIONS); 958 OK; ticket gate verde; 2026-11-16: provas e done verdes (958 OK); 2026-11-16: Guinan: L51, L52, L53 novas, L32 (--id); retro com 4 sugestões; test_lessons OK; 2026-11-16: Worf r1: APPROVE, 1 nit (W1: mensagem do tempo limite literal); 2026-11-16: PR #61 merge; SC-188 Done
**Breaker:** closed
