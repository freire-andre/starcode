# Teste do run_git independente do sistema: Spec

**Size**: SMALL
**Linear**: SC-225
**May change**: tests/test_falhas_start_settle.py

## Scope
- `test_run_git_argumentos_invalidos` deixa de fixar a frase do TypeError do Python do Windows e calcula a mensagem esperada com o Python da máquina, mantendo a comparação da tupla inteira (código, stdout, stderr), para passar no Windows e no Linux do CI.

## Checks
**Build**: `python tools/build.py --check`
**C1** - Com `env={"BAD": 1}`, `run_git` devolve exatamente `(126, "", "argumentos inválidos para o git: " + <str do TypeError que o subprocess do Python da máquina levanta para esse env>)`, e a forma binária devolve o mesmo em bytes; a mensagem esperada não é mais uma frase fixa de um sistema.
Proof: `python -m unittest discover -s tests -p "test_falhas_start_settle.py" -k test_run_git_argumentos_invalidos`

## Handoff

**Phase:** pr-review
**Size:** SMALL
**Git mode:** 3
**Plugin:** 1.9.0
**Next:** merge do PR #86
**Linear:** SC-225
**Integration branch:** feature/teste-git-linux
**Last integrated:** 4ab0195
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** 2026-11-24: Worf r1: APPROVE, sem achados; publicado
**Breaker:** closed
