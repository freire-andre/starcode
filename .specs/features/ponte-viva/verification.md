# ponte-viva verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at efbe0e6
**HEAD**: 5fc6ae3
**Verifier**: codex · requested cli-default · effective gpt-6.1-terra

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `crew-visual.test.ts` e `scene-model.test.ts` `ponte viva identifica os 12 integrantes` | no - verifica nomes completos nos perfis, mas exige nomes abreviados na cena e não verifica a relação com snapshot real |
| C2 | `scene-model.test.ts` `ponte viva limita a seis integrantes` | yes |
| C3 | `scene-model.test.ts` `ponte viva alterna integrantes elegíveis` | no - não verifica acesso dos demais quando seis alertas ocupam todas as vagas |
| C4 | `scene-model.test.ts` `ponte viva anima sem alterar estado` | yes |
| C5 | `crew-visual.test.ts` e `scene-model.test.ts` `ponte viva representa trabalho` | yes |
| C6 | `crew-visual.test.ts` e `scene-model.test.ts` `ponte viva representa ociosidade` | yes |
| C7 | `crew-visual.test.ts` e `scene-model.test.ts` `ponte viva distingue estados` | yes |
| C8 | `crew-visual.test.ts` e `scene-model.test.ts` `ponte viva não inventa atividade` | no - exige ocioso para contagens inválidas, embora não comprovem ociosidade |
| C9 | `scene-model.test.ts` `ponte viva lista os 12 integrantes` | yes |
| C10 | `scene-model.test.ts` `ponte viva permite selecionar integrante` | yes |
| C11 | `worker.test.ts` `ponte viva atualiza por evento` | no - verifica caminho e agentes, não se a atividade exibida pertence ao worktree em foco |
| C12 | `worker.test.ts` `ponte viva reconcilia automaticamente` | yes |
| C13 | `worker.test.ts` e `scene-model.test.ts` `ponte viva informa dados desatualizados` | yes |
| C14 | `worker.test.ts` `ponte viva descarta resposta obsoleta` | yes |
| C15 | `scene-model.test.ts` e `scene.test.ts` `ponte viva mantém rótulos legíveis` | no - mede quadros estáveis e caixas estimadas, sem verificar colisões durante a transição ou legibilidade visual real |
| C16 | `scene.test.ts` `ponte viva expõe lista acessível` | yes |
| C17 | `scene-model.test.ts` e `scene.test.ts` `ponte viva respeita movimento reduzido` | yes |
| C18 | `scene-model.test.ts` e `worker.test.ts` `ponte viva preserva transição em atualização repetida` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| A atividade de outro worktree é apresentada como trabalho no foco: as contagens são agregadas no repositório e tratadas como estado do integrante na cena. | `scripts/ponte.py:94`, `scripts/ponte.py:97`, `src/orca/src/crew-visual.ts:110`, `src/orca/src/scene.ts:397` | Vincular a atividade ao worktree de foco com identidade comprovada ou exibir desconhecido; testar dois worktrees. | 7543e30 · C11 |
| Uma contagem inválida é apresentada como ociosidade, embora não comprove ausência de atividade. | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --input-type=module -e 'import {estadosDaTripulacao,PERFIS} from "./src/orca/src/crew-visual.ts"; const s={status:"ok",stale:false,agents:[],snapshot:{starcode:true,crew:PERFIS.map(p=>({member:p.membro,count:p.membro==="q"?null:0}))}}; console.log(JSON.stringify(estadosDaTripulacao(s,{}).find(x=>x.membro==="q")))'` → `{"membro":"q","estado":"ocioso","motivo":"sem sessão ativa no snapshot do repositório"}` | Tratar contagem ausente ou inválida como desconhecida e testar o valor exato. | 7543e30 · C8 |
| Seis alertas fixos impedem que os demais integrantes elegíveis apareçam em qualquer rodada. | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --input-type=module -e 'import {selecionaPresentes} from "./src/orca/src/scene-model.ts"; import {MEMBROS} from "./src/orca/src/crew-visual.ts"; const e=MEMBROS.map((m,i)=>({membro:m,estado:i<6?"bloqueado":"ocioso",motivo:""})); console.log(JSON.stringify([...new Set(Array.from({length:24},(_,i)=>selecionaPresentes(e,i)).flat())]))'` → `["picard","spock","troi","data","laforge","mccoy"]` | Garantir acesso periódico a todos os elegíveis preservando prioridade proporcional aos alertas. | a96b4e4 · C3 |
| Nomes completos dos perfis são substituídos pelos nomes curtos do snapshot na relação e na cena. | `src/orca/src/scene-model.ts:612`, `src/orca/src/scene-model.ts:735`, `src/crew.yaml:32` | Disponibilizar os nomes completos também com snapshot real e testar o caminho integrado. | 8afa2c2 · C1 |
| O teste de legibilidade não mede as transições, apesar de nomes e indicadores também serem exibidos nelas. | `src/orca/src/scene-model.test.ts:554` | Exercitar as fases de entrada e saída nos dois tamanhos e verificar as caixas e a pintura. | 7e83f4d · C15 |

## Limits

Regressão em HEAD: `python -m unittest discover -s tests -v` passou: 1108 testes, 1 ignorado por depender do bit executável no Windows; `orca plugin test src/orca` passou: 104 testes.
Build, verificação de decisões e validação estrita do plugin passaram em HEAD.
Aceite visual real na Orca, inclusive leitor de tela, não foi executado nesta verificação; provas registram captura real pendente.
