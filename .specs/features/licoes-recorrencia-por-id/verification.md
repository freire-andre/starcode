# licoes-recorrencia-por-id verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 15aaf96
**HEAD**: 856e012
**Verifier**: codex · requested padrão do CLI · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_lessons.py` `test_lessons_add_id_registra_recorrencia_e_promove` | no - `updated >= before["updated"]` também aceita manter o timestamp antigo, sem provar a hora atual exigida por R1. |
| C2 | `tests/test_lessons.py` `test_lessons_add_id_sem_caixa_e_text_ignorado` | yes |
| C3 | `tests/test_lessons.py` `test_lessons_add_id_invalido_ou_quarentena_sai_2` | yes |
| C4 | `tests/test_lessons.py` `test_lessons_add_sem_id_exige_text` | no - só verifica que `lessons.json` não existe; não verifica que `LESSONS.md` não foi criado ou alterado, como R7 exige. |
| C5 | `tests/test_guinan_skill.py` `test_guinan_lista_licoes_e_reusa_id` | no - a ordem é comparada com `add --feature`, não com `add --id`, e os termos não provam que a regra de recorrência exige mesma causa e mesma correção. |
| C6 | `tests/test_lessons.py` `test_licoes_reprocessadas_n1` | no - valida só o prefixo `<ID> (` da fonte, não a primeira fonte entre parênteses; para as repetidas, verifica apenas existência, não que seus dados continuem iguais. |
| C7 | `tests/test_lessons.py` `test_decisions_licoes_recorrencia_por_id` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| `--id ""` é tratado como ausência de `--id`; o comando cria uma lição nova em vez de rejeitar um ID inexistente como exige R4. | `python -c "import pathlib,tempfile,subprocess,sys; s=pathlib.Path('scripts/lessons.py').resolve(); d=tempfile.TemporaryDirectory(prefix='q-probe-'); root=pathlib.Path(d.name); base=[sys.executable,'-I',str(s),'--root',str(root)]; subprocess.run(base+['init'],capture_output=True,text=True); a=subprocess.run(base+['add','--feature','f1','--signal','weak_test','--source','a:1','--text','seed'],capture_output=True,text=True); p=subprocess.run(base+['add','--id','','--feature','f2','--signal','weak_test','--source','b:2','--text','new lesson'],capture_output=True,text=True); print('seed:',a.returncode,repr(a.stdout),repr(a.stderr)); print('probe:',p.returncode,repr(p.stdout),repr(p.stderr)); print('lessons:',(root/'.specs'/'lessons.json').read_text(encoding='utf-8'))` → `probe: 0 'adicionada L2 (status=candidate)\n' ''` | Diferenciar opção ausente de opção presente vazia; rejeitar o ID vazio sem gravar. | |
| O teste de C1 permite que `updated` permaneça igual ao valor antigo e, portanto, não prova a hora atual de R1. | `tests/test_lessons.py:99` | Verificar que o timestamp gravado corresponde ao instante atual, usando relógio controlado ou uma janela temporal explícita. | |
| O teste de C4 não comprova que a visão `LESSONS.md` permanece intocada em caso de entrada inválida. | `tests/test_lessons.py:148` | Comparar os bytes de `LESSONS.md` antes e depois, inclusive quando ainda não existe. | |
| O teste de C5 pode passar se a listagem vier depois do comando `add --id` ou se o texto não exigir mesma causa e mesma correção. | `tests/test_guinan_skill.py:55`, `tests/test_guinan_skill.py:61` | Asserir a ordem da listagem antes dos dois comandos de escrita e o critério completo de recorrência no passo correspondente. | |
| O teste de C6 aceita qualquer fonte que comece com `<ID> (` e aceita alterações nas lições repetidas, embora R10 fixe a primeira fonte e exija que as repetidas permaneçam como estavam. | `tests/test_lessons.py:167` | Comparar a fonte completa com `<ID> (<primeira fonte>)` e verificar os registros repetidos contra seus valores originais. | |

## Limits

- A suíte completa em HEAD passou: `python -m unittest discover -s tests -v 2>&1` — 921 testes, 0 falhas, 1 ignorado (`bit executável não existe no Windows`).
- O worktree já tinha uma alteração em `spec.md` (`**Dispatched**: Q · 856e012`); mantive-a intacta, então o status não pode conter somente este relatório.
