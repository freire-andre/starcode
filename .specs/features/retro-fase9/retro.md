# Retro: retro-fase9

| # | Severidade | Categoria | Evidência | Ação proposta |
|---|---|---|---|---|
| 1 | alta | automatic checks | Escalação do T1: `scan_bypasses.py --help` lia o stdin e ficou 40 min parado na suíte (corrigido em 897934b) | Todo teste que roda subprocesso usa `stdin=DEVNULL` e `timeout`. Um check no build (ou no `scan_bypasses`) aponta `subprocess.run` sem `timeout` em `tests/` (liga-se ao N.6). |
| 2 | alta | instructions without effect | L32 voltou pela 7ª feature e L20 pela 8ª (achados C3 e C6, linhas 25 e 27) | Mesma proposta das retros de piloto-freios e lote1-correcoes: o brief do LaForge já traz o esqueleto de `test_decisions_<slug>` com uma asserção por requisito, e a regra "saída integral" no bloco RULES. |
| 3 | média | tool economy | Escalação do T1: o `check_scope` do worktree leu o May change antigo, porque a ampliação do Picard entrou no ramo depois da base | Ao ampliar o May change durante um despacho, o Picard reenvia a spec ao worker (ou o `check_scope` lê a spec do ramo de integração), para o gate do worker não ficar vermelho à toa. |
| 4 | baixa | information access | Q: `docs/fluxograma-starcode.svg` apareceu não rastreado durante a verificação, e o `q-check` saiu 1 | O `q-check` lista à parte arquivos não rastreados criados fora da worktree do Q, para distinguir arquivo do usuário de sobra do verificador. |
