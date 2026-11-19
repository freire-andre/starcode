# LESSONS - mantido por scripts/lessons.py

> Gerado. Não edite à mão: o próximo `lessons.py` sobrescreve. O estado fica em `.specs/lessons.json`.
> promote_threshold=2 features distintas

## Confirmed

Vistas em features distintas. Entram nos briefs.

### L2 - Compare a linha exata e o valor esperado no teste, não só assertIn de um trecho ou um padrão genérico, porque C11 e C39 passariam com texto ou nível errados.
- signal: `weak_test` · features: 16
- features: fase-9-worf-guinan-diagnostico, guardas-add-commit-powershell, q-preserva-handoff, ponte-missao-ativa, fase-12-robustez, manutencao-retros-f11, ajustes-review-pr39, snapshot-restauracao-segura, impacto-seleciona-real, licoes-recorrencia-por-id, opencode-copia-instalada, verificacao-1-8-0, scanner-lote2, guard-lote2, pequena-minima, pr-review
- sources: tests/test_review_post.py:test_post_own_pr_falls_back_to_comment; tests/test_acceptance_doc_f9.py, verification.md achado 1 (C1, C3, C4, C6), verification.md achados 2-4 (C4, C5, C6), L18 (.specs/features/ponte-missao-ativa/verification.md (rodada 2, C5)), L21 (verification.md:C33), L24 (verification.md:C32), L26 (verification.md:C8 (tests/test_skills_exec.py:18)), L37 (verification.md:achado 3), L38 (verification.md:C7), .specs/features/licoes-recorrencia-por-id/verification.md: achado 5 (C6, prefixo da fonte), .specs/features/opencode-copia-instalada/verification.md: achado 1 (C1, caminhos e plugin), .specs/features/verificacao-1-8-0/verification.md:43, .specs/features/scanner-lote2/verification.md:26, .specs/features/scanner-lote2/verification.md:27, .specs/features/guard-lote2/verification.md:27, verification.md: achado 3 (C7 Worf sem PR), verification.md: achados 4 e 5 (asserções por trecho)
- updated: 2026-11-19T14:18:01Z

### L4 - Teste cada limite de leitura (tamanho, ilegível) em todas as fontes que o requisito cita, porque o Handoff acima de 1 MiB era ignorado em silêncio e o teste de fonte inválida só cobria os JSON.
- signal: `weak_test` · features: 2
- features: fase-10-ponte, guardas-add-commit-powershell
- sources: verification.md: achado R8 (scripts/ponte.py handoff_of), verification.md achado 2 (secret_scan.py:196)
- updated: 2026-11-14T23:53:01Z

### L10 - Cite na prova de um check o teste de cada afirmação dele, inclusive o caso positivo, porque a prova citava só o teste do erro.
- signal: `weak_test` · features: 7
- features: fase-11-telas, despacho-media-escopo, q-familia-revendedor, opencode-copia-instalada, verificacao-1-8-0, pequena-minima, pr-review
- sources: .specs/features/fase-11-telas/verification.md:achado 3, L29 (verification.md: achado ID em minúscula; spec.md Edge Cases), L31 (verification.md achado C7 (test_model_info.py:164)), .specs/features/opencode-copia-instalada/verification.md: achado 2 (dry-run de R3 sem check), .specs/features/verificacao-1-8-0/verification.md:40, verification.md: achado 2 (prova da C4 sem settle), verification.md: achado 2 (edge case sem check)
- updated: 2026-11-19T14:18:00Z

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
- signal: `weak_test` · features: 8
- features: fase-12-robustez, gate-d30-ci, despacho-media-escopo, piloto-decisao-citada, licoes-recorrencia-por-id, q-strategy, verificacao-1-8-0, retro-fase9
- sources: verification.md:C11,C12,C28-C31, verification.md: achados 2 a 8 (C4-C10), verification.md: achados C5 e C13, verification.md achados 2 e 3 (test_piloto.py:204, :231), .specs/features/licoes-recorrencia-por-id/verification.md: achado 4 (C5, ordem e critério), .specs/features/q-strategy/verification.md:25, .specs/features/verificacao-1-8-0/verification.md:31, .specs/features/verificacao-1-8-0/verification.md:36, .specs/features/retro-fase9/verification.md:25
- updated: 2026-11-17T23:38:49Z

### L25 - Teste de regra compartilhada deve exercitar cada gate que a usa, porque um teste que só cobre um chamador deixa o outro sem prova.
- signal: `weak_test` · features: 3
- features: ajustes-review-pr39, despacho-media-escopo, verificacao-1-8-0
- sources: verification.md:C2 (tests/test_coverage_rule.py:22), verification.md: achado C9, .specs/features/verificacao-1-8-0/verification.md:38
- updated: 2026-11-16T17:20:28Z

### L32 - No teste de uma entrada de decisão, asserte na seção Decisão os termos de cada requisito descrito, não só títulos e nomes de teste, porque a entrada podia omitir requisitos e o teste passava.
- signal: `weak_test` · features: 9
- features: q-familia-revendedor, setup-grava-config, impacto-seleciona-real, q-strategy, piloto-freios, lote1-correcoes, retro-fase9, scanner-lote2, guard-lote2
- sources: verification.md achado C9 (test_model_info.py:178), L34 (verification.md:C4), L39 (verification.md:C8), .specs/features/q-strategy/verification.md:27, .specs/features/piloto-freios/verification.md:31, .specs/features/lote1-correcoes/verification.md:26, .specs/features/retro-fase9/verification.md:27, .specs/features/scanner-lote2/verification.md:29, .specs/features/guard-lote2/verification.md:28
- updated: 2026-11-19T00:58:27Z

### L41 - Diferencie opção ausente de opção presente com valor vazio (is None, não falsidade), porque --id "" caía no caminho sem --id e criava uma lição nova em vez de recusar o ID.
- signal: `weak_test` · features: 2
- features: licoes-recorrencia-por-id, verificacao-1-8-0
- sources: .specs/features/licoes-recorrencia-por-id/verification.md: achado 1 (--id vazio), .specs/features/verificacao-1-8-0/verification.md:32
- updated: 2026-11-16T17:20:27Z

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

## Quarantined

Confirmadas que falharam ao serem aplicadas. Ignorar.

_nenhuma_
