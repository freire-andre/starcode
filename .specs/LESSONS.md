# LESSONS - mantido por scripts/lessons.py

> Gerado. Não edite à mão: o próximo `lessons.py` sobrescreve. O estado fica em `.specs/lessons.json`.
> promote_threshold=2 features distintas

## Confirmed

Vistas em features distintas. Entram nos briefs.

_nenhuma_

## Candidates

Vistas uma vez. Em observação, não entram nos briefs.

### L1 - Valide campos obrigatórios exigindo string não vazia após strip, não só None ou "", porque o gate aceitou attacker: [] e o teste só cobria campo ausente.
- signal: `weak_test` · features: 1 · scope: `scripts/review`
- features: fase-9-worf-guinan-diagnostico
- sources: scripts/review/review_gate.py:72
- updated: 2026-11-09T18:54:53Z

### L2 - Compare a linha exata e o valor esperado no teste, não só assertIn de um trecho ou um padrão genérico, porque C11 e C39 passariam com texto ou nível errados.
- signal: `weak_test` · features: 1
- features: fase-9-worf-guinan-diagnostico
- sources: tests/test_review_post.py:test_post_own_pr_falls_back_to_comment; tests/test_acceptance_doc_f9.py
- updated: 2026-11-09T18:54:53Z

### L3 - Registre a decisão no DECISIONS.md no mesmo ciclo de qualquer correção em scripts/, skills/ ou hooks/, porque o check_decisions deixa as provas vermelhas.
- signal: `gate_fail` · features: 1
- features: fase-9-worf-guinan-diagnostico
- sources: proofs.md: check_decisions após 9e7679a
- updated: 2026-11-09T18:54:53Z

### L4 - Teste cada limite de leitura (tamanho, ilegível) em todas as fontes que o requisito cita, porque o Handoff acima de 1 MiB era ignorado em silêncio e o teste de fonte inválida só cobria os JSON.
- signal: `weak_test` · features: 1
- features: fase-10-ponte
- sources: verification.md: achado R8 (scripts/ponte.py handoff_of)
- updated: 2026-11-10T14:38:54Z

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

### L10 - Cite na prova de um check o teste de cada afirmação dele, inclusive o caso positivo, porque a prova citava só o teste do erro.
- signal: `weak_test` · features: 1
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 3
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

### L13 - Confira exclusões de cópia em toda a árvore (rglob), não só na raiz do destino, porque o teste passaria com um filtro que ignorasse apenas o primeiro nível.
- signal: `weak_test` · features: 1
- features: fase-11-telas
- sources: .specs/features/fase-11-telas/verification.md:achado 6
- updated: 2026-11-12T13:24:05Z

## Quarantined

Confirmadas que falharam ao serem aplicadas. Ignorar.

_nenhuma_
