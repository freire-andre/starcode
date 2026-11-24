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

**Phase:** spec-approved
**Size:** SMALL
**Git mode:** 3
**Plugin:** none yet
**Next:** LaForge corrige o teste
**Linear:** SC-225
**Integration branch:** fix/teste-git-linux
**Last integrated:** none
**Dispatched:** none
**Settled:** none
**Attempts:** none
**Reports:** none
**Breaker:** closed
