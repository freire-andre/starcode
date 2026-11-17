# Backlog de CI: validação da Orca e suíte lenta no Windows

> **Para o agente que vai ler este arquivo:** este é um plano para ser **investigado e implementado depois**, não uma ordem para executar tudo de uma vez. Siga as fases na ordem, pare nos pontos marcados com **PARE** e só altere arquivos depois da aprovação explícita do usuário. Responda ao usuário em português (PT-BR).

Criado em 2026-11-16, logo depois do PR #62 (`ci: reduzir minutos de windows sem perder cobertura`).

---

## 1. Contexto

### 1.1 Por que isso existe
Em novembro de 2026 o repositório privado `freire-andre/starcode` (plano GitHub Free) estourou a franquia de GitHub Actions até o dia 16: 922 min de Windows e 274 min de Linux, com status `Usage blocked`. O custo vinha quase todo da etapa `unittest` no runner Windows: cerca de 8 min 48 s por execução, contra cerca de 1 min 27 s no Ubuntu.

O PR #62 já reduziu o problema mudando **quando** o CI roda:
- a matriz Windows roda só em `pull_request` e `workflow_dispatch`; push em `main` roda só Ubuntu;
- tags `v*` não rodam `checks`, só o `release-check`;
- PRs que mexem só em `.specs/` não disparam o CI, exceto quando mudam `.specs/lessons.json`;
- o job `checks` tem `timeout-minutes: 20`.

Ficaram dois pontos em aberto, descritos aqui:
- **Item A:** a etapa `orca plugin validate` nunca valida nada no CI.
- **Item B:** a suíte de testes é lenta no Windows.

### 1.2 Estado atual relevante
- Workflow: `.github/workflows/ci.yml`. Jobs: `checks` (matriz), `eval` (só manual), `release-check` (só tags).
- Testes estruturais do workflow: `tests/test_ci_workflow.py`. Eles **fixam** a estrutura do `ci.yml`. Toda mudança deliberada no workflow precisa atualizar esses testes **sem apagar garantias**.
- Suíte: `python -m unittest discover -s tests -v`. Em 2026-11-16 eram 960 testes, cerca de 467 s localmente no Windows do usuário.
- O projeto é **somente stdlib de propósito**: `tools/miniyaml.py` existe para não depender do PyYAML. Não adicione dependências externas (pytest, pytest-xdist etc.) sem aprovação explícita do usuário.
- `tools/release.py` (função `_preconditions`) só libera um release se houver uma execução do workflow `CI` **concluída com sucesso no SHA exato do HEAD de `main`**. Qualquer mudança que faça um push em `main` não gerar execução, ou gerar execução que nunca fica verde, **bloqueia o release**.
- Não há proteção de branch nem checks obrigatórios: a API devolve 403 no plano Free para repositório privado.
- O runner `windows-latest` de repositório privado tem **2 vCPUs**. Isso limita o ganho de qualquer paralelismo a cerca de 2x.
- Preços vigentes informados (conferir no painel): Windows US$ 0,010/min, Linux US$ 0,006/min. Cada job é arredondado para cima em minutos inteiros.
- O usuário desenvolve no **Windows**, no disco `F:`. Os gates locais do StarCode rodam a suíte no Windows antes do PR.
- O hook do StarCode bloqueia `gh pr merge` sem `python scripts/git_mode.py authorize-merge main` registrado **numa chamada separada**, depois de uma autorização explícita do usuário. Revogue com `revoke-merge` logo após o merge.
- Mensagens de commit em minúsculas, no padrão `tipo(escopo): descrição`.

---

## 2. Regras gerais (valem para os dois itens)

1. **Fase 1 é só leitura.** Não altere arquivos e não dispare workflows no GitHub para investigar. Rode tudo localmente.
2. **Não remova nem enfraqueça asserções de teste** para ganhar velocidade. Pode mudar *como* um teste prepara o cenário, mas não *o que* ele verifica.
3. **Não toque no código do produto**: `src/`, `skills/`, `dist/`, `scripts/` (exceto quando a otimização exigir, e aí precisa ser aprovado e justificado), `profiles/`. O `dist/` é gerado: se algo em `src/` mudar, rode `python tools/build.py` e confirme `--check`.
4. **Uma melhoria por PR.** Item A e Item B vão em PRs separados. Dentro do Item B, cada otimização relevante vai num commit próprio, para que o rollback seja trivial.
5. **Validação local mínima antes de qualquer PR:**
   - `python tools/build.py --check`
   - `python -m unittest discover -s tests` (suíte completa, no Windows)
   - `python scripts/check_decisions.py`
   - `python -m unittest discover -s tests -p "test_ci_workflow.py" -v`, se o workflow mudou
6. **Push e PR só com confirmação do usuário.** Merge só com autorização explícita, seguindo o procedimento do hook (seção 1.2).
7. **Não mexa** em faturamento, orçamento, secrets, nem no job `eval` (ele usa `ANTHROPIC_API_KEY` e tem custo de API).

---

## 3. Item A: validação da Orca no CI

### 3.1 Problema
Passo atual no job `checks`:

```yaml
- name: orca plugin validate
  shell: bash
  run: 'if command -v orca >/dev/null 2>&1; then orca plugin validate src/orca --json; else echo "orca ausente: validação do plugin pulada"; fi'
```

O runner não tem a CLI `orca`, então o passo **sempre** cai no `else` e termina verde. Na prática é um **falso verde**: quem lê o CI acredita que o plugin Orca foi validado, mas não foi. O teste `test_ci_valida_plugin_orca_condicional`, em `tests/test_ci_workflow.py`, fixa esse comportamento condicional.

Relacionados: `src/orca/` (plugin Orca, com `orca-plugin.json`, `src/` e `tsconfig.json`), `tools/install_local.py` (instala o plugin localmente com `orca plugin install ... --approve <fingerprint>`). Há um problema conhecido: `orca plugin test` falha quando rodado fora do disco `C:`, porque o harness não encontra o `orca-runtime.mjs`. O gate local roda em worktree no `C:`.

### 3.2 Fase 1: investigação (somente leitura)
Responda com evidência, sem supor:
1. **Como a CLI `orca` é distribuída?** Pacote npm, binário baixável, só junto do app desktop? Tem versão para Linux? Precisa de interface gráfica, login ou licença?
2. **`orca plugin validate` funciona sem o app aberto e sem conta?** Teste localmente.
3. **Quanto tempo leva** para instalar e rodar no Ubuntu? Estime sem disparar o CI.
4. **A versão pode ser fixada** (como `@anthropic-ai/claude-code@2.1.319`)? Uma versão flutuante pode quebrar o CI sem mudança no projeto.
5. **O que `orca plugin validate` verifica** que nenhum outro teste da suíte já cobre? Procure em `tests/` testes sobre `src/orca` e o manifesto `orca-plugin.json`.

**PARE** e apresente as respostas ao usuário com uma recomendação.

### 3.3 Opções e quando escolher cada uma

| Opção | Quando escolher | Mudança |
|---|---|---|
| **A1. Instalar a CLI e validar de verdade** | A CLI instala de forma não interativa, com versão fixa, em Linux, em poucos segundos, sem login | Passo de instalação com versão fixada **só no Ubuntu** (`if: runner.os == 'Linux'`), e o passo de validação passa a **falhar** se a CLI não existir |
| **A2. Remover o passo do CI** | A CLI não instala de forma estável e automática no runner | Remover o passo, registrar em `DECISIONS.md` (ou onde o projeto registra decisões) que a validação da Orca é feita no gate local, e garantir que esse gate local existe e roda |
| **A3. Manter, mas tornar visível** | Paliativo, se A1 e A2 tiverem de esperar | Trocar o `echo` por `echo "::warning::orca ausente: validação do plugin NÃO executada"`, para o pulo aparecer como aviso na interface do GitHub |

Recomendação inicial, a confirmar na investigação: **A2**, a menos que a Fase 1 mostre que A1 é simples e estável.

### 3.4 Implementação
**A1:**
- Instalar a CLI só no job Ubuntu, com versão fixada.
- Validação sem `if command -v`: se a CLI faltar, o passo falha.
- No Windows o passo **não roda** (`if: runner.os == 'Linux'`), para não dobrar o custo.
- Atualizar `test_ci_valida_plugin_orca_condicional` para fixar o novo comportamento: versão fixada, passo só no Linux, sem o ramo que pula.

**A2:**
- Remover o passo de `ci.yml`.
- Substituir `test_ci_valida_plugin_orca_condicional` por um teste que fixe a **ausência** do passo, com um comentário apontando para a decisão registrada. Não basta apagar o teste.
- Confirmar onde a validação da Orca roda localmente e documentar o comando.
- Se `DECISIONS.md` for alterado, rodar `python scripts/check_decisions.py`.

**A3:**
- Trocar a mensagem do `echo` e ajustar a asserção de texto no teste.

### 3.5 Riscos de uma implementação ruim

| Risco | Como acontece | Consequência | Como evitar |
|---|---|---|---|
| CI quebra por motivo externo | CLI instalada sem versão fixa, ou de fonte instável | Todos os PRs ficam vermelhos sem mudança no projeto, e o release trava (o `release.py` exige CI verde em main) | Versão fixa e fonte oficial. Se a instalação for frágil, preferir A2 |
| Dobrar o custo | Instalar e validar a Orca também no Windows | Mais minutos de Windows, o oposto do objetivo | Restringir a `runner.os == 'Linux'` |
| Trocar um falso verde por outro | Validar sem checar o código de saída, ou com `|| true` | Continua sem validar nada | O passo precisa falhar quando a validação falha. Teste localmente com um manifesto inválido |
| Perder a validação sem perceber | Remover o passo (A2) sem garantir o gate local | O plugin Orca fica sem nenhuma validação | Antes de remover, apontar o comando local que valida e registrar a decisão |
| Apagar a garantia do teste | Excluir `test_ci_valida_plugin_orca_condicional` sem substituir | Alguém reintroduz o passo condicional sem perceber | Substituir por um teste que fixe o novo comportamento |
| Problema do disco `F:` | Rodar `orca plugin test` (não `validate`) localmente no `F:` | Falha que parece regressão, mas é ambiente | Usar worktree no `C:` para `orca plugin test` |
| Login ou licença no CI | A CLI exigir credencial | Tentação de criar secret novo | **Não criar secrets.** Se exigir credencial, escolher A2 |

### 3.6 Critérios de aceitação
- O CI **não** mostra verde para uma validação que não aconteceu (A1 ou A2), ou mostra um aviso explícito (A3).
- Nenhum minuto de Windows a mais.
- `tests/test_ci_workflow.py` fixa o novo comportamento.
- A suíte completa, o build `--check` e `check_decisions` passam localmente.

### 3.7 Rollback
Reverter o commit do PR (`git revert <sha>`). O passo antigo volta a pular silenciosamente, sem efeito no produto.

---

## 4. Item B: suíte lenta no Windows

### 4.1 Problema
A etapa `unittest` leva cerca de 8 min 48 s no Windows contra cerca de 1 min 27 s no Ubuntu. A hipótese principal, **a confirmar com medição**, é o custo de criar processos e de I/O no Windows: cerca de 39 arquivos de teste usam `subprocess`, e há testes que criam repositórios git temporários, rodam `git`, `bash`, `python` e `claude` como subprocessos, e usam `time.sleep`.

Depois do PR #62, o Windows roda só em PRs, então o ganho desta otimização é **menor do que era**. Ela só vale se a medição mostrar um ganho claro e de baixo risco.

### 4.2 Fase 1: medição (somente leitura, local)
1. **Tempo por arquivo de teste.** Rode cada módulo separadamente e registre a duração. Exemplo em Bash:
   ```bash
   cd tests
   for f in test_*.py; do
     s=$(date +%s.%N)
     python -m unittest "${f%.py}" >/dev/null 2>&1
     echo "$(echo "$(date +%s.%N) - $s" | bc) $f"
   done | sort -rn | head -25
   ```
   Ou escreva um script stdlib no scratchpad, fora do repositório, que use `unittest` com um `TestResult` cronometrando cada teste (`startTest`/`stopTest`) e liste os 30 testes mais lentos.
2. **Tempo por teste dentro dos 5 arquivos mais lentos.** Mesma técnica, no nível do teste.
3. **Para cada teste lento, classifique a causa:**
   - `time.sleep` fixo (espera por tempo, em vez de por condição);
   - repositório git temporário recriado em cada teste, quando poderia ser criado uma vez por classe (`setUpClass`);
   - subprocessos repetidos que poderiam ser chamados direto em Python (importar a função em vez de rodar `python script.py`);
   - chamadas ao `claude` ou a outra CLI externa;
   - timeouts altos sendo atingidos.
4. **Compare com o Ubuntu**, se possível em WSL ou numa máquina Linux. Não dispare o CI só para isso.
5. **Verifique isolamento.** Liste os testes que usam `os.chdir`, alteram `os.environ` diretamente ou escrevem em caminhos fixos (fora de `tempfile`). Já foram vistos, entre outros: `tests/helpers.py`, `test_banner.py`, `test_config_skill.py`, `test_crew_hook_agy_opencode.py`, `test_diagnostico.py`, `test_dispatch.py`, `test_ephemeral_db.py`, `test_model_info.py`, `test_ponte.py`, `test_review_post.py`. Esses são os candidatos a quebrar com paralelismo.

**PARE** e apresente ao usuário a tabela dos testes mais lentos, a causa provável de cada um e a economia estimada por otimização.

### 4.3 Estratégias, da mais segura para a mais arriscada

**B1. Corrigir os gargalos pontuais (preferida)**
- Trocar `time.sleep` fixo por espera com condição e prazo, como um laço de verificação com timeout. O prazo máximo continua igual, mas o teste termina assim que a condição é satisfeita.
- Mover a preparação cara e **somente leitura** para `setUpClass`/`tearDownClass`. Só quando o cenário não é alterado pelos testes, senão um teste contamina o outro.
- Trocar `subprocess.run([sys.executable, "script.py", ...])` por chamada direta da função `main(argv)`, **somente** quando o teste não está validando justamente a interface de linha de comando (código de saída, stdout e stderr como processo real). Se estiver, mantenha o subprocesso.
- Reduzir repetições de cenário idêntico.

**B2. Paralelismo stdlib dentro do runner (só se B1 não bastar)**
- Executor próprio com `concurrent.futures`/`multiprocessing`, rodando **um módulo de teste por processo**, cada processo com seu diretório temporário e `cwd` próprio.
- Ganho máximo de cerca de 2x no runner Windows de 2 vCPUs.
- Exige isolamento comprovado (item 5 da Fase 1). Módulos não isolados rodam em série.
- O executor precisa propagar falhas (código de saída diferente de 0 se qualquer módulo falhar) e mostrar a saída de cada módulo que falhou.

**B3. Dividir em vários jobs (shards): não recomendado**
- Cada job paga a preparação (checkout, Python, Node, Claude Code) e o arredondamento por minuto. O total de minutos faturados **aumenta**. Só reduz o tempo de espera, que não é o problema aqui.

**B4. Adicionar `pytest` + `pytest-xdist`: só com aprovação explícita**
- Quebra o princípio "somente stdlib" do projeto e adiciona dependência externa ao CI. Apresente ao usuário como opção, com o custo de manutenção, e não implemente sem um "sim" claro.

### 4.4 Implementação
- Um commit por otimização (por arquivo de teste, ou por causa).
- Depois de cada commit:
  - rodar o arquivo alterado **várias vezes seguidas** (pelo menos 5), para detectar falha intermitente;
  - rodar a suíte completa;
  - registrar o tempo antes e depois.
- Se usar B2:
  - criar o executor em `tools/` (por exemplo `tools/run_tests.py`), stdlib apenas, com testes próprios em `tests/`;
  - trocar o comando do passo `unittest` no `ci.yml` **só depois** de a suíte rodar em paralelo localmente, pelo menos 5 vezes seguidas, sem nenhuma falha intermitente;
  - atualizar `test_ci_checks_steps_and_commands` em `tests/test_ci_workflow.py`, que hoje fixa `python -m unittest discover -s tests -v`;
  - manter `python -m unittest discover -s tests` funcionando localmente, porque os gates e outros fluxos podem depender dele (procure com `grep -rn "unittest discover"`).

### 4.5 Riscos de uma implementação ruim

| Risco | Como acontece | Consequência | Como evitar |
|---|---|---|---|
| **Testes intermitentes** | Paralelizar testes que dividem `cwd`, `os.environ`, arquivos temporários com nome fixo ou o próprio repositório | CI falha aleatoriamente, PRs precisam de re-execução (que **gasta mais minutos**), e a confiança no CI cai | Verificar isolamento antes. Rodar em paralelo 5 vezes ou mais sem falha antes de adotar. Na dúvida, serial |
| **Enfraquecer o teste** | Trocar subprocesso por chamada direta em teste que valida a CLI, reduzir asserções, aumentar tolerâncias, pular testes no Windows (`skipIf`) | Regressões passam despercebidas, principalmente as de Windows (`.cmd`, Git Bash, caminhos, arquivos somente leitura), que eram o motivo de manter o Windows | Regra 2 da seção 2. Nunca adicionar `skip` para ganhar tempo. Revisar o diff procurando asserções removidas |
| **Contaminação entre testes** | `setUpClass` compartilhando estado que algum teste altera | Resultado depende da ordem: passa sozinho e falha na suíte, ou o contrário | Só compartilhar cenário somente leitura. Rodar o arquivo isolado e na suíte completa |
| **Falha mascarada no executor** | Executor paralelo que não propaga o código de saída, ou engole exceções do processo filho | **CI verde com teste falhando**, o pior cenário | Teste do executor com um módulo que falha de propósito: o executor precisa sair com código diferente de 0 e mostrar a falha |
| **Teste sumir da execução** | Executor próprio descobre menos testes que o `unittest discover` (padrão de nome, subpastas, `helpers`) | Testes deixam de rodar em silêncio | Comparar a contagem: o executor tem de reportar o mesmo número de testes (hoje 960, sendo 1 skip) |
| **Espera por condição sem prazo** | Trocar `sleep` por laço sem timeout | Job trava até o `timeout-minutes: 20` e gasta 20 min de Windows | Todo laço de espera precisa de prazo máximo explícito |
| **Prazo curto demais** | Reduzir timeouts ou esperas para acelerar | Falhas intermitentes no runner do GitHub, mais lento que a máquina local | Manter os prazos máximos. Otimizar terminando cedo, não esperando menos |
| **Mais minutos em vez de menos** | Shards (B3), cache que não compensa, passos extras de instalação | O consumo sobe | Medir antes e depois. Comparar minutos faturados, não só o tempo de espera |
| **Dependência externa** | Adicionar pytest/xdist sem aprovação | Contraria o princípio stdlib, e mais uma coisa pode quebrar o CI | B4 só com "sim" explícito do usuário |
| **Quebrar o release** | Mudar o comando de testes de um jeito que falha em main | Sem CI verde no SHA de main, o `release.py` recusa o release | Validar a suíte completa localmente antes do merge. O push em main roda no Ubuntu: confirme que o executor funciona lá também |
| **Divergência entre Linux e Windows** | Otimização que só funciona no Windows (caminhos com `\`, `.exe`) ou só no Linux | Uma das plataformas quebra | Testar no Windows (máquina do usuário) e garantir que o PR roda a matriz completa |
| **Mexer no produto sem querer** | Ajustar um script de `scripts/` para facilitar o teste | Mudança de comportamento do StarCode | Regra 3 da seção 2. Se precisar, justificar e pedir aprovação |

### 4.6 Critérios de aceitação
- Mesmo número de testes executados (hoje 960, sendo 1 skip). Nenhuma asserção removida ou enfraquecida, nenhum `skip` novo.
- Redução **medida** do tempo da suíte no Windows, com números antes e depois na descrição do PR.
- Zero falhas intermitentes em pelo menos 5 execuções completas seguidas.
- `build --check`, `check_decisions` e `test_ci_workflow` passam.
- O PR roda a matriz completa (Ubuntu e Windows) verde antes do merge, se a cota de Actions permitir. Se não permitir, o usuário decide se faz o merge só com a validação local.

### 4.7 Rollback
Cada otimização num commit próprio: `git revert <sha>` do commit problemático. Se o executor paralelo (B2) causar instabilidade, a reversão mínima é voltar o passo do `ci.yml` para `python -m unittest discover -s tests -v` e manter o executor só para uso local.

---

## 5. Ordem sugerida
1. Item A, Fase 1 (investigação da Orca). É rápida e decide entre A1, A2 e A3.
2. Item A, implementação, em PR próprio.
3. Item B, Fase 1 (medição). Pode levar alguns minutos de execução local.
4. Item B, B1 (gargalos pontuais), um PR com commits separados.
5. Medir de novo. Só considerar B2 se o ganho de B1 for insuficiente e o isolamento estiver comprovado.

## 6. Prompt sugerido para o agente
> Leia `.specs/backlog/ci-orca-e-suite-windows.md` e execute a Fase 1 do Item A (somente leitura). Pare e me apresente o resultado antes de alterar qualquer arquivo.

Depois de aprovado o Item A:
> Siga o mesmo arquivo e execute a Fase 1 do Item B (medição local). Pare e me apresente a tabela dos testes mais lentos antes de otimizar.
