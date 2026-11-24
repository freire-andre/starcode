# LESSONS - mantido por scripts/lessons.py

> Gerado. Não edite à mão: o próximo `lessons.py` sobrescreve. O estado fica em `.specs/lessons.json`.
> promote_threshold=2 features distintas

## Confirmed

Vistas em features distintas. Entram nos briefs.

### L2 - Compare a linha exata e o valor esperado no teste, não só assertIn de um trecho ou um padrão genérico, porque C11 e C39 passariam com texto ou nível errados.
- signal: `weak_test` · features: 20
- features: fase-9-worf-guinan-diagnostico, guardas-add-commit-powershell, q-preserva-handoff, ponte-missao-ativa, fase-12-robustez, manutencao-retros-f11, ajustes-review-pr39, snapshot-restauracao-segura, impacto-seleciona-real, licoes-recorrencia-por-id, opencode-copia-instalada, verificacao-1-8-0, scanner-lote2, guard-lote2, pequena-minima, pr-review, roteamento-worf-mccoy, catalogo-e-orca, suite-e-execute, versao-1-9-0
- sources: tests/test_review_post.py:test_post_own_pr_falls_back_to_comment; tests/test_acceptance_doc_f9.py, verification.md achado 1 (C1, C3, C4, C6), verification.md achados 2-4 (C4, C5, C6), L18 (.specs/features/ponte-missao-ativa/verification.md (rodada 2, C5)), L21 (verification.md:C33), L24 (verification.md:C32), L26 (verification.md:C8 (tests/test_skills_exec.py:18)), L37 (verification.md:achado 3), L38 (verification.md:C7), .specs/features/licoes-recorrencia-por-id/verification.md: achado 5 (C6, prefixo da fonte), .specs/features/opencode-copia-instalada/verification.md: achado 1 (C1, caminhos e plugin), .specs/features/verificacao-1-8-0/verification.md:43, .specs/features/scanner-lote2/verification.md:26, .specs/features/scanner-lote2/verification.md:27, .specs/features/guard-lote2/verification.md:27, verification.md: achado 3 (C7 Worf sem PR), verification.md: achados 4 e 5 (asserções por trecho), .specs/features/roteamento-worf-mccoy/verification.md:achado 5, verification.md achado 4, .specs/features/suite-e-execute/verification.md:C6, .specs/features/versao-1-9-0/verification.md:achado 2
- updated: 2026-11-22T20:22:54Z

### L4 - Teste cada limite de leitura (tamanho, ilegível) em todas as fontes que o requisito cita, porque o Handoff acima de 1 MiB era ignorado em silêncio e o teste de fonte inválida só cobria os JSON.
- signal: `weak_test` · features: 2
- features: fase-10-ponte, guardas-add-commit-powershell
- sources: verification.md: achado R8 (scripts/ponte.py handoff_of), verification.md achado 2 (secret_scan.py:196)
- updated: 2026-11-14T23:53:01Z

### L10 - Cite na prova de um check o teste de cada afirmação dele, inclusive o caso positivo, porque a prova citava só o teste do erro.
- signal: `weak_test` · features: 10
- features: fase-11-telas, despacho-media-escopo, q-familia-revendedor, opencode-copia-instalada, verificacao-1-8-0, pequena-minima, pr-review, restauracao-e-telas, versao-e-retro, suite-e-execute
- sources: .specs/features/fase-11-telas/verification.md:achado 3, L29 (verification.md: achado ID em minúscula; spec.md Edge Cases), L31 (verification.md achado C7 (test_model_info.py:164)), .specs/features/opencode-copia-instalada/verification.md: achado 2 (dry-run de R3 sem check), .specs/features/verificacao-1-8-0/verification.md:40, verification.md: achado 2 (prova da C4 sem settle), verification.md: achado 2 (edge case sem check), verification.md achado 1, verification.md achado 3, .specs/features/suite-e-execute/verification.md:C8
- updated: 2026-11-22T15:05:53Z

### L13 - Confira exclusões de cópia em toda a árvore (rglob), não só na raiz do destino, porque o teste passaria com um filtro que ignorasse apenas o primeiro nível.
- signal: `weak_test` · features: 2
- features: fase-11-telas, opencode-copia-instalada
- sources: .specs/features/fase-11-telas/verification.md:achado 6, .specs/features/opencode-copia-instalada/verification.md: achado 3 (.pyc fora de __pycache__)
- updated: 2026-11-15T19:42:34Z

### L15 - Teste de 'nada foi escrito' compara bytes e a lista de arquivos antes e depois; mtime e tamanho não detectam uma escrita que os preserve.
- signal: `weak_test` · features: 3
- features: ponte-missao-ativa, licoes-recorrencia-por-id, verificacao-1-8-0
- sources: .specs/features/ponte-missao-ativa/verification.md (rodada 1, C4), .specs/features/licoes-recorrencia-por-id/verification.md: achado 3 (C4, LESSONS.md), .specs/features/verificacao-1-8-0/verification.md:34, .specs/features/verificacao-1-8-0/verification.md:35
- updated: 2026-11-16T17:20:28Z

### L20 - Asserte a saída integral e cada condição ou ordem exigida pelo critério, não fragmentos da mensagem, porque fragmentos passavam mesmo com condição ou ordem erradas.
- signal: `weak_test` · features: 16
- features: fase-12-robustez, gate-d30-ci, despacho-media-escopo, piloto-decisao-citada, licoes-recorrencia-por-id, q-strategy, verificacao-1-8-0, retro-fase9, fecha-achado, licoes-no-brief, config-local-worktree, ponte-manutencao, falhas-start-settle, versao-e-retro, suite-e-execute, versao-1-9-0
- sources: verification.md:C11,C12,C28-C31, verification.md: achados 2 a 8 (C4-C10), verification.md: achados C5 e C13, verification.md achados 2 e 3 (test_piloto.py:204, :231), .specs/features/licoes-recorrencia-por-id/verification.md: achado 4 (C5, ordem e critério), .specs/features/q-strategy/verification.md:25, .specs/features/verificacao-1-8-0/verification.md:31, .specs/features/verificacao-1-8-0/verification.md:36, .specs/features/retro-fase9/verification.md:25, .specs/features/fecha-achado/verification.md:achado 4, .specs/features/licoes-no-brief/verification.md:achado 2, .specs/features/config-local-worktree/verification.md:achado 4, .specs/features/ponte-manutencao/verification.md achado 3, .specs/features/falhas-start-settle/verification.md achado 5, verification.md achado 1, .specs/features/suite-e-execute/verification.md:C3, .specs/features/versao-1-9-0/verification.md:achado 3, .specs/features/versao-1-9-0/verification.md:achado 5
- updated: 2026-11-22T20:22:55Z

### L25 - Teste de regra compartilhada deve exercitar cada gate que a usa, porque um teste que só cobre um chamador deixa o outro sem prova.
- signal: `weak_test` · features: 6
- features: ajustes-review-pr39, despacho-media-escopo, verificacao-1-8-0, fecha-achado, sessions-concorrente, config-local-worktree
- sources: verification.md:C2 (tests/test_coverage_rule.py:22), verification.md: achado C9, .specs/features/verificacao-1-8-0/verification.md:38, .specs/features/fecha-achado/verification.md:achado 3, .specs/features/sessions-concorrente/verification.md:achado 4, .specs/features/config-local-worktree/verification.md:achado 2
- updated: 2026-11-20T15:46:03Z

### L32 - No teste de uma entrada de decisão, asserte na seção Decisão os termos de cada requisito descrito, não só títulos e nomes de teste, porque a entrada podia omitir requisitos e o teste passava.
- signal: `weak_test` · features: 18
- features: q-familia-revendedor, setup-grava-config, impacto-seleciona-real, q-strategy, piloto-freios, lote1-correcoes, retro-fase9, scanner-lote2, guard-lote2, fecha-achado, sessions-concorrente, roteamento-worf-mccoy, licoes-no-brief, config-local-worktree, ponte-manutencao, falhas-start-settle, catalogo-e-orca, suite-e-execute
- sources: verification.md achado C9 (test_model_info.py:178), L34 (verification.md:C4), L39 (verification.md:C8), .specs/features/q-strategy/verification.md:27, .specs/features/piloto-freios/verification.md:31, .specs/features/lote1-correcoes/verification.md:26, .specs/features/retro-fase9/verification.md:27, .specs/features/scanner-lote2/verification.md:29, .specs/features/guard-lote2/verification.md:28, .specs/features/fecha-achado/verification.md:achado 5, .specs/features/sessions-concorrente/verification.md:achado 3, .specs/features/roteamento-worf-mccoy/verification.md:achado 4, .specs/features/licoes-no-brief/verification.md:achado 3, .specs/features/config-local-worktree/verification.md:achado 5, .specs/features/ponte-manutencao/verification.md achado 4, .specs/features/falhas-start-settle/verification.md achado 7, verification.md achado 5, .specs/features/suite-e-execute/verification.md:C10
- updated: 2026-11-22T15:05:53Z

### L41 - Diferencie opção ausente de opção presente com valor vazio (is None, não falsidade), porque --id "" caía no caminho sem --id e criava uma lição nova em vez de recusar o ID.
- signal: `weak_test` · features: 2
- features: licoes-recorrencia-por-id, verificacao-1-8-0
- sources: .specs/features/licoes-recorrencia-por-id/verification.md: achado 1 (--id vazio), .specs/features/verificacao-1-8-0/verification.md:32
- updated: 2026-11-16T17:20:27Z

### L93 - Ao procurar referências antigas, varra a árvore inteira sem excluir arquivos pelo nome e cubra cada forma de citação, porque a exclusão de execute* e uma regex estreita deixavam passar referência velha.
- signal: `weak_test` · features: 2
- features: suite-e-execute, versao-1-9-0
- sources: .specs/features/suite-e-execute/verification.md:C9, .specs/features/versao-1-9-0/verification.md:achado 4, .specs/features/versao-1-9-0/verification.md:achado 7
- updated: 2026-11-22T20:22:55Z

## Candidates

Vistas uma vez. Em observação, não entram nos briefs.

### L1 - Valide campos obrigatórios exigindo string não vazia após strip, não só None ou "", porque o gate aceitou attacker: [] e o teste só cobria campo ausente.
- signal: `weak_test` · features: 1 · scope: `scripts/review`
- features: fase-9-worf-guinan-diagnostico
- sources: scripts/review/review_gate.py:72
- updated: 2026-11-09T18:54:53Z

### L3 - Registre a decisão no DECISIONS.md no mesmo ciclo de qualquer correção em scripts/, skills/ ou hooks/, porque o check_decisions deixa as provas vermelhas.
- signal: `gate_fail` · features: 1
- features: fase-9-worf-guinan-diagnostico
- sources: proofs.md: check_decisions após 9e7679a
- updated: 2026-11-09T18:54:53Z

### L5 - Faça o teste afirmar a chamada e o valor exigidos (método, timeout) e a ausência do que a palavra 'só' exclui, porque os testes conferiam só a presença das seções e passariam com o requisito falso.
- signal: `weak_test` · features: 1
- features: fase-10-ponte
- sources: verification.md: achado C8/C21/C26
- updated: 2026-11-10T14:38:54Z

### L6 - Defina e teste a semântica de duplicatas ao extrair IDs de texto livre, porque linear_ids devolvia o mesmo ID repetido e o painel podia mostrá-lo duas vezes.
- signal: `ac_gap` · features: 1
- features: fase-10-ponte
- sources: verification.md: achado linear_ids
- updated: 2026-11-10T14:38:54Z

### L7 - Não use docstring em teste Python citado por uma check, porque o unittest -v imprime a docstring e separa o nome do '... ok' que a prova procura.
- signal: `gate_fail` · features: 1 · scope: `tests`
- features: fase-10-ponte
- sources: proofs.md r1: C51 (tests/test_acceptance_doc_f10.py)
- updated: 2026-11-10T14:38:54Z

### L8 - Valide o comprimento e a estrutura do cabeçalho de uma imagem antes de ler as dimensões, porque um PNG truncado passava como legível.
- signal: `weak_test` · features: 1 · scope: `imagens`
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 1
- updated: 2026-11-12T12:18:57Z

### L9 - Valide URLs contra a string inteira (fullmatch), não só o começo, porque a regex aceitava https:// vazio e URL com espaço.
- signal: `weak_test` · features: 1
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 2
- updated: 2026-11-12T12:18:57Z

### L11 - Separe em dois checks o caminho de erro e o de sucesso de um comando, porque um único teste de erro não prova que o comando produz a saída.
- signal: `weak_test` · features: 1
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 4
- updated: 2026-11-12T12:18:58Z

### L12 - Teste um registro de aceite pelos artefatos (tamanho das imagens, linhas do julgamento), não por palavras no texto, porque qualquer documento com os termos certos passava.
- signal: `weak_test` · features: 1 · scope: `aceite`
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 5
- updated: 2026-11-12T12:18:58Z

### L14 - Antes de exigir uma chamada de host da Orca num requisito, confirme no host-api a capacidade que ela pede e se o manifesto a tem; requisito que depende de capacidade ausente contradiz um Non-Goal de não pedir capacidades.
- signal: `spec_precision_gap` · features: 1 · scope: `src/orca`
- features: ponte-missao-ativa
- sources: .specs/features/ponte-missao-ativa/verification.md (rodada 1, R7)
- updated: 2026-11-12T16:46:42Z

### L16 - Critério 'o mais recente' precisa dizer o desempate quando a chave empata (ex.: mesmo mtime), com um caso de teste que o fixe.
- signal: `spec_precision_gap` · features: 1
- features: ponte-missao-ativa
- sources: .specs/features/ponte-missao-ativa/verification.md (rodada 1, R1)
- updated: 2026-11-12T16:46:42Z

### L17 - Normalização de caminho Windows não pode tirar a barra da raiz do drive: 'C:/' (raiz) e 'c:' (relativo ao drive) são diferentes; teste a raiz junto dos casos comuns.
- signal: `weak_test` · features: 1 · scope: `scripts`
- features: ponte-missao-ativa
- sources: .specs/features/ponte-missao-ativa/verification.md (rodada 2, same_path)
- updated: 2026-11-12T16:46:42Z

### L18 - Teste de texto composto exibido ao usuário compara a string inteira esperada, não substrings soltas que aceitam partes extras ou repetidas.
- signal: `weak_test` · features: 1 · scope: `src/orca`
- features: ponte-missao-ativa
- sources: .specs/features/ponte-missao-ativa/verification.md (rodada 2, C5)
- updated: 2026-11-12T16:46:42Z

### L19 - Declare em cada regra de análise a que tipos de arquivo ela vale e confira se outro requisito usa o mesmo token, porque a regra do marcador {{ foi lida para TS/JS e conflitou com a regra de templates.
- signal: `spec_precision_gap` · features: 1
- features: fase-12-robustez
- sources: verification.md:R21
- updated: 2026-11-12T20:27:14Z

### L21 - Compare o bloco completo da mensagem de erro com o motivo retornado, não só o prefixo, porque qualquer texto com o prefixo passava no teste.
- signal: `weak_test` · features: 1
- features: fase-12-robustez
- sources: verification.md:C33
- updated: 2026-11-12T20:27:15Z

### L22 - Valide a data com o calendário antes de preservar um prefixo ISO, porque 2026-99-99 era aceita como data válida.
- signal: `ac_gap` · features: 1
- features: manutencao-retros-f11
- sources: verification.md:R23
- updated: 2026-11-13T14:57:34Z

### L23 - Normalize o caminho citado e rejeite segmentos .. antes de conferir a pasta do May change, porque scripts/../../x passava como coberto.
- signal: `weak_test` · features: 1
- features: manutencao-retros-f11
- sources: verification.md:R20/R21
- updated: 2026-11-13T14:57:34Z

### L24 - Teste de idioma deve verificar o relato inteiro, não só palavras proibidas, porque a asserção deixava passar texto em português.
- signal: `weak_test` · features: 1
- features: manutencao-retros-f11
- sources: verification.md:C32
- updated: 2026-11-13T14:57:34Z

### L26 - Asserção sobre texto de contrato deve fixar o comando completo e o comportamento exigido, porque fragmentos aceitam textos que não cumprem o critério.
- signal: `weak_test` · features: 1
- features: ajustes-review-pr39
- sources: verification.md:C8 (tests/test_skills_exec.py:18)
- updated: 2026-11-13T16:43:22Z

### L27 - Compare a saída de um comando git com o valor exato depois de remover só o fim de linha, não com strip(), e teste uma saída com espaços, porque ' false ' passava como clone completo.
- signal: `weak_test` · features: 1
- features: gate-d30-ci
- sources: verification.md: achado 1 (C3)
- updated: 2026-11-13T22:23:26Z

### L28 - Escreva a prova isolada só com o comando entre crases, sem '| linha esperada', porque o check_proofs roda a linha num shell e o pipe vira um comando inexistente (exit 127).
- signal: `gate_fail` · features: 1 · scope: `specs`
- features: gate-d30-ci
- sources: spec.md C11; Handoff attempt proofs-C11=fail
- updated: 2026-11-13T22:23:26Z

### L29 - Dê a cada item de Edge Cases da spec um check com teste próprio, porque a comparação sem diferença de maiúsculas estava listada e nenhum check a fixava.
- signal: `ac_gap` · features: 1 · scope: `specs`
- features: despacho-media-escopo
- sources: verification.md: achado ID em minúscula; spec.md Edge Cases
- updated: 2026-11-13T23:41:40Z

### L30 - Limite o tamanho de todo número extraído por regex antes do int(), porque um ID de 5000 dígitos passava a regex e derrubava o gate com traceback em vez de recusa.
- signal: `ac_gap` · features: 1
- features: piloto-decisao-citada
- sources: verification.md achado 1 (gates_common.py:200)
- updated: 2026-11-14T14:18:22Z

### L31 - Dê a cada valor de uma tabela fixada no requisito pelo menos uma linha no teste, porque a tabela de prefixos testava 13 de 15 e o1/o4 ficaram sem prova.
- signal: `weak_test` · features: 1
- features: q-familia-revendedor
- sources: verification.md achado C7 (test_model_info.py:164)
- updated: 2026-11-14T17:43:47Z

### L33 - Quando o teste extrai um valor de um título ou texto por regex, exija exatamente uma ocorrência e falhe com mensagem que nomeie o que faltou, porque a busca devolvia None (AttributeError) e aceitava duplicata.
- signal: `weak_test` · features: 1
- features: setup-grava-config
- sources: verification.md:C2
- updated: 2026-11-14T19:24:05Z

### L34 - No teste de uma entrada do DECISIONS.md, asserte os quatro campos (Problema, Decisão, Motivo, Por que não é bug) dentro da entrada, porque o teste conferia só o cabeçalho e um termo e passava sem os campos.
- signal: `weak_test` · features: 1
- features: setup-grava-config
- sources: verification.md:C4
- updated: 2026-11-14T19:24:05Z

### L35 - Ao limpar arquivos de estado por padrão de nome, decida também o destino do arquivo ilegível, porque a limpeza só apagava o que conseguia ler e deixava lixo da feature.
- signal: `ac_gap` · features: 1
- features: snapshot-restauracao-segura
- sources: verification.md:achado 1
- updated: 2026-11-14T20:27:54Z

### L36 - Nunca engula a falha de limpeza depois de uma operação destrutiva: saia com erro e diga como terminar, porque o comando anunciava sucesso e deixava estado iniciado para trás.
- signal: `ac_gap` · features: 1
- features: snapshot-restauracao-segura
- sources: verification.md:achado 2
- updated: 2026-11-14T20:27:54Z

### L37 - Para conferir uma lista impressa, compare a lista exata de linhas analisadas, porque assertIn de um trecho aceita caminho maior ou texto extra.
- signal: `weak_test` · features: 1
- features: snapshot-restauracao-segura
- sources: verification.md:achado 3
- updated: 2026-11-14T20:27:54Z

### L38 - Quando o requisito fixa uma mensagem ou motivo, compare o texto integral com assertEqual, porque assertIn de um trecho aceita caminho ou texto errado.
- signal: `weak_test` · features: 1
- features: impacto-seleciona-real
- sources: verification.md:C7
- updated: 2026-11-14T22:46:09Z

### L39 - No teste de uma entrada de registro, asserte cada termo que o requisito manda citar, porque o teste conferia só parte deles e passava se um sumisse.
- signal: `weak_test` · features: 1
- features: impacto-seleciona-real
- sources: verification.md:C8
- updated: 2026-11-14T22:46:09Z

### L40 - Ao ler git status --porcelain, trate as linhas R e C como dois caminhos (antigo e novo) e decida sobre os dois, porque a renomeação entre arquivos permitidos virava um caminho único e era recusada.
- signal: `ac_gap` · features: 1
- features: q-preserva-handoff
- sources: verification.md achado 1 (scripts/dispatch.py:507)
- updated: 2026-11-15T13:53:17Z

### L42 - Quando o requisito manda gravar a hora atual, asserte o carimbo dentro da janela entre antes e depois da chamada, porque updated >= anterior também passava com o valor antigo.
- signal: `weak_test` · features: 1
- features: licoes-recorrencia-por-id
- sources: .specs/features/licoes-recorrencia-por-id/verification.md: achado 2 (C1, updated)
- updated: 2026-11-15T17:19:52Z

### L43 - Quando o critério cita a saída e o exit code de um comando, exercite o próprio comando (main com o ambiente controlado), não só a função interna, porque o teste da função passava sem provar o que o comando imprime nem o código de saída.
- signal: `weak_test` · features: 1
- features: q-strategy
- sources: .specs/features/q-strategy/verification.md:26
- updated: 2026-11-16T12:25:30Z

### L44 - Em percurso ordenado com efeito colateral por item (aviso, log), teste um item com efeito depois de um que já resolve e asserte que o efeito não acontece, porque uma avaliação antecipada avisaria fora da ordem sem nenhum teste falhar.
- signal: `ac_gap` · features: 1
- features: q-strategy
- sources: .specs/features/q-strategy/verification.md:28
- updated: 2026-11-16T12:25:30Z

### L45 - Faça a listagem e a checagem unitária de um estado usarem a mesma função de regra, porque a listagem do banner incluía piloto com mandato pendente que a checagem unitária recusava.
- signal: `ac_gap` · features: 1
- features: verificacao-1-8-0
- sources: .specs/features/verificacao-1-8-0/verification.md:33
- updated: 2026-11-16T17:20:27Z

### L46 - Teste cada código de saída documentado de um comando (uso inválido, recurso ausente, regra recusada, sucesso) via CLI, porque o teste cobria só parte dos códigos e um exit trocado passava.
- signal: `weak_test` · features: 1
- features: verificacao-1-8-0
- sources: .specs/features/verificacao-1-8-0/verification.md:37, .specs/features/verificacao-1-8-0/verification.md:41
- updated: 2026-11-16T17:20:28Z

### L47 - Teste os valores exatos de cada limiar fixado no requisito e um logo abaixo dele (ex.: 0, 2, 12; 7 dias), porque o teste usava valores folgados e um < trocado por <= passava.
- signal: `weak_test` · features: 1
- features: verificacao-1-8-0
- sources: .specs/features/verificacao-1-8-0/verification.md:39
- updated: 2026-11-16T17:20:28Z

### L48 - Quando o requisito fixa uma precedência entre fontes, asserte o valor efetivo resultante (CLI e modelo) em cada origem, não só o rótulo da origem, porque o rótulo certo passava com o valor herdado errado.
- signal: `weak_test` · features: 1
- features: verificacao-1-8-0
- sources: .specs/features/verificacao-1-8-0/verification.md:42
- updated: 2026-11-16T17:20:28Z

### L49 - Ao isentar um caso de uma regra, limite a isenção à regra que o requisito nomeia e teste o caso isento contra as outras regras, porque a isenção do freio para 'devolvido ao usuário' vazou para a exigência de mandato da categoria.
- signal: `ac_gap` · features: 1
- features: piloto-freios
- sources: .specs/features/piloto-freios/verification.md:28
- updated: 2026-11-16T18:32:50Z

### L50 - Depois de um comando que grava, asserte a entrada persistida no arquivo (título, campos, marcas), não só a mensagem de sucesso impressa, porque o teste passava com o comando anunciando a gravação sem gravar.
- signal: `weak_test` · features: 1
- features: piloto-freios
- sources: .specs/features/piloto-freios/verification.md:29, .specs/features/piloto-freios/verification.md:30
- updated: 2026-11-16T18:32:50Z

### L51 - Ao detectar binário ou marcador num conteúdo, examine o conteúdo inteiro ou documente o recorte no requisito, porque olhar só os primeiros 8000 caracteres deixava passar um byte nulo mais adiante.
- signal: `spec_deviation` · features: 1
- features: lote1-correcoes
- sources: .specs/features/lote1-correcoes/verification.md:24
- updated: 2026-11-16T20:40:03Z

### L52 - Num teste de tempo limite, confira que o processo expirado deixou de existir (PID gravado pela prova), não só a mensagem de falha escrita, porque o resultado podia ser registrado com o processo ainda vivo.
- signal: `weak_test` · features: 1
- features: lote1-correcoes
- sources: .specs/features/lote1-correcoes/verification.md:25
- updated: 2026-11-16T20:40:03Z

### L53 - Quando o requisito cobre falha e tempo limite de uma chamada externa, teste os dois caminhos e a continuação para o próximo item, porque só o retorno não zero tinha teste.
- signal: `ac_gap` · features: 1
- features: lote1-correcoes
- sources: .specs/features/lote1-correcoes/verification.md:27
- updated: 2026-11-16T20:40:03Z

### L54 - Ao trocar a leitura manual de argv por argparse, preserve os casos que o argparse interpreta diferente (argumento iniciado por hífen, posição) e teste-os, porque um caminho '-review.json' passou a ser tratado como opção.
- signal: `spec_deviation` · features: 1
- features: retro-fase9
- sources: .specs/features/retro-fase9/verification.md:23
- updated: 2026-11-17T23:38:49Z

### L55 - Ao trocar um helper usado em vários campos, teste cada campo que o usa, inclusive os condicionais, com valor inválido e válido, porque o teste cobria só os campos fixos.
- signal: `weak_test` · features: 1
- features: retro-fase9
- sources: .specs/features/retro-fase9/verification.md:24
- updated: 2026-11-17T23:38:49Z

### L56 - Quando um artefato cita um commit da feature, o teste confere que o hash existe e tocou o arquivo esperado, não só o formato hexadecimal, porque qualquer hash passava.
- signal: `weak_test` · features: 1
- features: retro-fase9
- sources: .specs/features/retro-fase9/verification.md:26
- updated: 2026-11-17T23:38:49Z

### L57 - Toda isenção de segurança por host (local, confiável) extrai o host como o parser de URL faz (último @ da autoridade) e exige igualdade exata, com teste de contorno (@localhost:5432@evil.com, localhost.evil.com); na dúvida, acuse.
- signal: `ac_gap` · features: 1
- features: scanner-lote2
- sources: .specs/features/scanner-lote2/verification.md:24
- updated: 2026-11-18T22:56:47Z

### L58 - Ao isentar URL sem credencial, trate usuário sem senha como sem credencial e teste esse caso, porque https://alice@host era acusado contra o requisito.
- signal: `spec_deviation` · features: 1
- features: scanner-lote2
- sources: .specs/features/scanner-lote2/verification.md:25
- updated: 2026-11-18T22:56:47Z

### L59 - Quando o requisito manda incluir exemplos numa lista de fixtures, o teste exige a presença de cada exemplo na lista, não só que a lista inteira passe, porque removê-los não quebrava nada.
- signal: `weak_test` · features: 1
- features: scanner-lote2
- sources: .specs/features/scanner-lote2/verification.md:28
- updated: 2026-11-18T22:56:47Z

### L60 - Quando um parser ignora parte do texto (corpo de heredoc, comentário, string), teste o marcador que abre a parte ignorada dentro de comentário e de aspas, porque '# <<EOF' escondia o comando real da linha seguinte.
- signal: `ac_gap` · features: 1
- features: guard-lote2
- sources: .specs/features/guard-lote2/verification.md:25
- updated: 2026-11-19T00:58:27Z

### L61 - Ao interpretar sintaxe de shell, associe cada construção ao seu comando ou pipeline e respeite '--', porque o heredoc de um segmento era tratado como entrada do shell de outro, e um arquivo chamado -f virava flag.
- signal: `spec_deviation` · features: 1
- features: guard-lote2
- sources: .specs/features/guard-lote2/verification.md:26
- updated: 2026-11-19T00:58:27Z

### L62 - Ao casar um marcador de estado por regex, delimite o valor (palavra inteira até o fim da linha) e teste um valor que só começa igual, porque 'waivedness' dispensava o Q e o gate passava sem tabelas.
- signal: `weak_test` · features: 1
- features: pequena-minima
- sources: verification.md: achado 1 (waivedness)
- updated: 2026-11-19T11:59:04Z

### L63 - Ao acrescentar um passo a uma seção de fluxo, releia as paradas já existentes nela e teste a frase condicional inteira do passo novo, porque o pedido de merge incondicional contradizia a parada da rodada 3 e o teste não via.
- signal: `weak_test` · features: 1
- features: pr-review
- sources: verification.md: achado 1 (merge após r3 aberta)
- updated: 2026-11-19T14:18:00Z

### L64 - Ao criar um modo ou exceção que remete a uma regra geral, cite a regra que a exceção contraria e escreva a exceção explícita, porque o modo só lições remetia à seção 1, que excluía achados corrigidos.
- signal: `ac_gap` · features: 1
- features: pr-review
- sources: verification.md: achado 3 (Guinan exclui corrigidos)
- updated: 2026-11-19T14:18:01Z

### L65 - Quando um passo do fluxo grava arquivos depois do PR aberto (review, lições), a instrução manda commitar e fazer o push antes do merge, porque senão o merge entra sem eles e a árvore da feature fica suja.
- signal: `review_finding` · features: 1
- features: pr-review
- sources: review.md: W1 (r1)
- updated: 2026-11-19T14:44:11Z

### L66 - Para saber se um nome é definido em código, analise a sintaxe (ast) em vez de buscar texto, porque uma definição aparente dentro de string ou comentário passava como função real.
- signal: `weak_test` · features: 1
- features: fecha-achado
- sources: .specs/features/fecha-achado/verification.md:achado 1
- updated: 2026-11-19T16:29:48Z

### L67 - Ao ler tabelas Markdown, trate como linha da tabela também a linha com pipe que segue outra linha da tabela sem pipe inicial, porque ela escapava da contagem de células.
- signal: `weak_test` · features: 1
- features: fecha-achado
- sources: .specs/features/fecha-achado/verification.md:achado 2
- updated: 2026-11-19T16:29:48Z

### L68 - Teste de escrita concorrente deve passar pelo mesmo caminho de ler-mudar-gravar que a produção usa; uma função que substitui o arquivo inteiro perde as chaves das outras escritas mesmo sob trava.
- signal: `weak_test` · features: 1
- features: sessions-concorrente
- sources: .specs/features/sessions-concorrente/verification.md:achado 1
- updated: 2026-11-19T18:51:34Z

### L69 - Prove novas tentativas e limpeza com a falha simulada até o limite: sucesso na última tentativa permitida e falha depois dela, com o arquivo anterior intacto e sem temporário sobrando.
- signal: `weak_test` · features: 1
- features: sessions-concorrente
- sources: .specs/features/sessions-concorrente/verification.md:achado 2
- updated: 2026-11-19T18:51:34Z

### L70 - Teste de descrição de skill extrai todos os gatilhos entre aspas e confere cada um contra a regra; procurar só as frases esperadas deixa passar um gatilho genérico novo.
- signal: `weak_test` · features: 1
- features: roteamento-worf-mccoy
- sources: .specs/features/roteamento-worf-mccoy/verification.md:achado 1
- updated: 2026-11-19T21:20:12Z

### L71 - Teste de arquivo estruturado (YAML, JSON) analisa o arquivo e compara a estrutura inteira; linhas soltas passam com o campo na seção errada ou com o documento malformado.
- signal: `weak_test` · features: 1
- features: roteamento-worf-mccoy
- sources: .specs/features/roteamento-worf-mccoy/verification.md:achado 2
- updated: 2026-11-19T21:20:13Z

### L72 - Ao descrever o que um caso negativo de eval garante, use o alcance do grader (uma skill ou qualquer skill), porque o README prometia nenhuma skill e o grader só barrava uma.
- signal: `spec_precision_gap` · features: 1
- features: roteamento-worf-mccoy
- sources: .specs/features/roteamento-worf-mccoy/verification.md:achado 6
- updated: 2026-11-19T21:20:14Z

### L73 - Um gerador que substitui um passo manual da referência cobre todas as entradas que a referência manda juntar, ou a referência passa a dizer o que ele não cobre; o fix-brief ignorava as linhas differs de telas.
- signal: `spec_precision_gap` · features: 1
- features: licoes-no-brief
- sources: .specs/features/licoes-no-brief/verification.md:achado 1
- updated: 2026-11-20T13:12:09Z

### L74 - Quando um requisito fixa a mensagem de recusa, toda forma de entrada inválida coberta por ele (vazia, parcial) sai com essa mensagem; uma validação anterior com texto próprio passava na frente.
- signal: `ac_gap` · features: 1
- features: config-local-worktree
- sources: .specs/features/config-local-worktree/verification.md:achado 1
- updated: 2026-11-20T15:46:03Z

### L75 - Antes de escrever que uma regra vale em todas as configs, confira no schema quais têm o campo; a config do repositório não tem modelo e a lista de fleet.workers tinha modelo sem validação.
- signal: `spec_precision_gap` · features: 1
- features: config-local-worktree
- sources: .specs/features/config-local-worktree/verification.md:achado 3
- updated: 2026-11-20T15:46:04Z

### L76 - Ao trocar um leitor próprio por um compartilhado, compare a saída antiga e a nova de cada chamador campo a campo, porque o leitor comum pode normalizar um valor que o chamador imprimia como estava.
- signal: `spec_deviation` · features: 1
- features: ponte-manutencao
- sources: .specs/features/ponte-manutencao/verification.md achado 1
- updated: 2026-11-21T00:46:37Z

### L77 - Delimitador de token inteiro deve tratar letras e números Unicode como parte do token (\p{L}\p{N} com a flag u), não só [A-Za-z0-9], e o teste deve cobrir acento nos dois limites.
- signal: `spec_deviation` · features: 1
- features: ponte-manutencao
- sources: .specs/features/ponte-manutencao/verification.md achado 2
- updated: 2026-11-21T00:46:37Z

### L78 - Teste que executa bash no Windows não deve usar shutil.which('bash'), que pode achar o bash do WSL sem acesso aos caminhos do Windows; use o bash do Git ou pule o teste com motivo.
- signal: `gate_fail` · features: 1 · scope: `testes no Windows`
- features: ponte-manutencao
- sources: .specs/features/ponte-manutencao/verification.md achado 5
- updated: 2026-11-21T00:46:38Z

### L79 - Ao ler o código de saída de um comando que usa 0 e 1 como resposta (git diff --quiet), trate qualquer outro código como erro, porque um tempo esgotado ou falha virava resposta válida.
- signal: `spec_deviation` · features: 1
- features: falhas-start-settle
- sources: .specs/features/falhas-start-settle/verification.md achado 1
- updated: 2026-11-21T13:55:54Z

### L80 - Função que promete nunca levantar exceção deve capturar também os erros de argumento e ambiente (TypeError, ValueError), não só OSError e tempo esgotado, e o teste deve cobrir esses casos.
- signal: `spec_deviation` · features: 1
- features: falhas-start-settle
- sources: .specs/features/falhas-start-settle/verification.md achado 2
- updated: 2026-11-21T13:55:54Z

### L81 - Wrapper que devolve só bool ou só stdout não pode engolir um tempo esgotado: propague o erro com o stderr pelo caminho de erro do chamador.
- signal: `spec_deviation` · features: 1
- features: falhas-start-settle
- sources: .specs/features/falhas-start-settle/verification.md achado 3
- updated: 2026-11-21T13:55:54Z

### L82 - Teste de um modo de saída (--json) deve exercitar o fluxo inteiro com o runner falso, não injetar o resultado pronto da função interna, porque a integração errada passaria.
- signal: `weak_test` · features: 1
- features: falhas-start-settle
- sources: .specs/features/falhas-start-settle/verification.md achado 4
- updated: 2026-11-21T13:55:54Z

### L83 - Teste de concorrência deve forçar a disputa com sincronização explícita (sinais por arquivo ou evento) e provar que falha sem a proteção, porque processos soltos podem serializar e passar sem a trava.
- signal: `weak_test` · features: 1
- features: falhas-start-settle
- sources: .specs/features/falhas-start-settle/verification.md achado 6
- updated: 2026-11-21T13:55:54Z

### L84 - Ao ler formato binário por chunks, confira o comprimento declarado contra o tamanho do arquivo antes de aceitar o chunk; teste chunk truncado no cabeçalho, nos dados e no CRC, e chunk de comprimento zero.
- signal: `weak_test` · features: 1 · scope: `leitores de formato binário`
- features: restauracao-e-telas
- sources: verification.md achado 2
- updated: 2026-11-21T17:36:00Z

### L85 - Ao memorizar o resultado de uma leitura, guarde também o resultado ausente ou inválido, e teste com espião que a segunda chamada para um arquivo inválido não relê.
- signal: `weak_test` · features: 1 · scope: `memoização`
- features: catalogo-e-orca
- sources: verification.md achado 1
- updated: 2026-11-21T20:17:26Z

### L86 - Um adaptador de processo não deve sinalizar falha de execução só com códigos de saída que o processo também pode devolver (127, 124, 126); use um campo próprio e teste o processo saindo com esses códigos.
- signal: `spec_precision_gap` · features: 1 · scope: `adaptadores de processo`
- features: catalogo-e-orca
- sources: verification.md achado 2
- updated: 2026-11-21T20:17:26Z

### L87 - Para provar que nenhum módulo chama algo diretamente, inspecione chamadas efetivas (AST ou espião do adaptador) e não um padrão textual, que perde variações de espaço e aceita comentários ou código inativo.
- signal: `weak_test` · features: 1
- features: catalogo-e-orca
- sources: verification.md achado 3
- updated: 2026-11-21T20:17:26Z

### L88 - Antes de inserir uma linha relativa ao título de um texto gerado, confira em cada gerador qual é de fato a primeira linha; um prefixo como 'Repositório:' desloca o título e a regra falha em parte dos geradores.
- signal: `spec_deviation` · features: 1
- features: versao-e-retro
- sources: verification.md achado 2
- updated: 2026-11-21T22:56:22Z

### L89 - Ao reescrever uma célula de tabela markdown, troque só o intervalo de caracteres dela; reconstruir a linha pelas células perde espaços finais e o CRLF. Teste com espaços depois do último | e com CRLF.
- signal: `weak_test` · features: 1 · scope: `edição de markdown`
- features: versao-e-retro
- sources: verification.md achado 4
- updated: 2026-11-21T22:56:23Z

### L90 - Quando um comando classifica arquivos pela estrutura (ex.: 'sem coluna X'), trate o arquivo sem a estrutura nenhuma (sem tabela, vazio) como um caso da classificação e teste-o.
- signal: `ac_gap` · features: 1
- features: versao-e-retro
- sources: verification.md achado 5
- updated: 2026-11-21T22:56:23Z

### L91 - Teste o texto gerado pela interface real (o brief montado), não a constante que entra nele, porque o teste passaria se a montagem deixasse a constante de fora.
- signal: `weak_test` · features: 1
- features: suite-e-execute
- sources: .specs/features/suite-e-execute/verification.md:C1,C2
- updated: 2026-11-22T15:05:53Z

### L92 - Confira um valor medido contra a saída bruta guardada da medição, não só o formato, porque contagem e tempos inventados no formato certo passavam.
- signal: `weak_test` · features: 1
- features: suite-e-execute
- sources: .specs/features/suite-e-execute/verification.md:C4
- updated: 2026-11-22T15:05:53Z

### L94 - Antes de exigir um campo num arquivo gerado, confira no gerador se o formato tem esse campo, porque o requisito pediu version no marketplace do Codex, que não tem a chave, e o teste trocava a ausência pelo valor esperado.
- signal: `spec_precision_gap` · features: 1
- features: versao-1-9-0
- sources: .specs/features/versao-1-9-0/verification.md:achado 1
- updated: 2026-11-22T20:22:54Z

### L95 - Não faça a prova depender do histórico do git com skipTest quando o commit falta; congele a referência no próprio teste, porque num clone raso a comparação era pulada e nada era provado.
- signal: `weak_test` · features: 1
- features: versao-1-9-0
- sources: .specs/features/versao-1-9-0/verification.md:achado 6
- updated: 2026-11-22T20:22:55Z

### L96 - Teste de estado vindo de texto externo deve incluir nomes herdados do protótipo (toString, constructor) e exigir propriedade própria ou mapa sem protótipo, porque 'toString' lançava exceção e interrompia a cena.
- signal: `weak_test` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: verification.md:C8
- updated: 2026-11-23T15:00:07Z

### L97 - Ao provar vínculo de sessão e worktree por caminho, recuse caminho vazio em todas as fontes e teste o caso de caminhos vazios coincidentes, porque três vazios iguais comprovavam vínculo indevido.
- signal: `weak_test` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: verification.md:C21
- updated: 2026-11-23T15:00:07Z

### L98 - Prova de acessibilidade que só aciona ouvintes em DOM simulado não prova teclado nem leitor de tela; rode a navegação real ou declare a prova como lógica, porque o teste passava sem Tab ou anúncio.
- signal: `weak_test` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: verification.md:C16
- updated: 2026-11-23T15:00:07Z

### L99 - Ao tratar clique em item já presente, use a mesma função de alternância de seleção e teste que a seleção se mantém, porque o clique trocava a seleção de quem já estava na cena.
- signal: `review_finding` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: review.md:W1
- updated: 2026-11-23T16:56:34Z

### L100 - Trate arquivo de estado presente mas ilegível ou inválido como desconhecido, nunca como contagem zero, e teste os três casos (ausente, válido, inválido), porque o JSON inválido virava integrante ocioso.
- signal: `review_finding` · features: 1 · scope: `scripts`
- features: ponte-viva
- sources: review.md:W2
- updated: 2026-11-23T16:56:34Z

### L101 - Ignore a caixa ao comparar caminhos só quando houver letra de unidade ou UNC; em POSIX compare exato e teste os dois sentidos com nomes que diferem só na caixa, porque /repo/Foo vinculava a /repo/foo.
- signal: `review_finding` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: review.md:W3
- updated: 2026-11-23T16:56:34Z

### L102 - Remova conversões de tipo desnecessárias quando o valor já satisfaz a interface esperada, porque a conversão dupla de document para Pagina escondia a compatibilidade real.
- signal: `review_finding` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: review.md:W4
- updated: 2026-11-23T16:56:34Z

### L103 - Não suprima tipo em dublê de teste sem justificativa: tipe o dublê com a forma real ou mantenha a conversão com a justificativa e a issue na linha anterior, porque dublês contornavam tipos sem registro.
- signal: `review_finding` · features: 1 · scope: `src/orca`
- features: ponte-viva
- sources: review.md:W5
- updated: 2026-11-23T16:56:34Z

## Quarantined

Confirmadas que falharam ao serem aplicadas. Ignorar.

_nenhuma_
