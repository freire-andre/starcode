# ponte-viva verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at a22a9a7
**HEAD**: 9313368
**Verifier**: codex · requested cli-default · effective unconfirmed

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `crew-visual.test.ts`, `scene-model.test.ts` `ponte viva identifica os 12 integrantes` | yes |
| C2 | `scene-model.test.ts` `ponte viva limita a seis integrantes` | yes |
| C3 | `scene-model.test.ts` `ponte viva mantém presença sem rodízio` | yes |
| C4 | `scene-model.test.ts` `ponte viva anima sem alterar estado` | yes |
| C5 | `crew-visual.test.ts`, `scene-model.test.ts` `ponte viva representa trabalho` | yes |
| C6 | `crew-visual.test.ts`, `scene-model.test.ts` `ponte viva representa ociosidade` | yes |
| C7 | `crew-visual.test.ts`, `scene-model.test.ts` `ponte viva distingue estados` | yes |
| C8 | `crew-visual.test.ts`, `scene-model.test.ts` `ponte viva não inventa atividade` | no - não cobre estados inválidos que coincidem com propriedades herdadas |
| C9 | `scene-model.test.ts` `ponte viva lista os 12 integrantes` | yes |
| C10 | `scene-model.test.ts` `ponte viva permite selecionar integrante` | yes |
| C11 | `worker.test.ts` `ponte viva atualiza por evento` | yes |
| C12 | `worker.test.ts` `ponte viva reconcilia automaticamente` | yes |
| C13 | `worker.test.ts`, `scene-model.test.ts` `ponte viva informa dados desatualizados` | yes |
| C14 | `worker.test.ts` `ponte viva descarta resposta obsoleta` | yes |
| C15 | `scene-model.test.ts`, `scene.test.ts` `ponte viva mantém rótulos legíveis` | yes |
| C16 | `scene.test.ts` `ponte viva expõe lista acessível` | no - usa DOM simulado e chama clique diretamente, sem testar teclado ou leitor de tela |
| C17 | `scene-model.test.ts`, `scene.test.ts` `ponte viva respeita movimento reduzido` | yes |
| C18 | `scene-model.test.ts`, `worker.test.ts` `ponte viva preserva transição em atualização repetida` | yes |
| C19 | `scene-model.test.ts` `ponte viva prioriza presença estável` | yes |
| C20 | `scene-model.test.ts` `ponte viva mantém integrante já presente` | yes |
| C21 | `crew-visual.test.ts` `ponte viva vincula sessão ao worktree` | no - não recusa três caminhos vazios coincidentes |
| C22 | `crew-visual.test.ts` `ponte viva não infere troca sem vínculo` | no - não cobre vínculo com caminhos vazios |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| Um estado inválido com nome herdado provoca exceção em vez de desconhecido e interrompe a construção da cena. | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --input-type=module -e "import {estadosDaTripulacao} from './src/orca/src/crew-visual.ts'; let e={status:'ok',stale:false,agents:[{terminalId:'t',state:'toString'}],snapshot:{starcode:true,crew:[{member:'spock',count:1}]}}; try { console.log(JSON.stringify(estadosDaTripulacao(e,{t:'spock'}).find(x=>x.membro==='spock'))) } catch(err) { console.log(err.toString()) }"` → `TypeError: Cannot read properties of undefined (reading 'texto')` | Validar estados por propriedade própria ou mapa sem protótipo e testar valores herdados. | b36170d · C8 |
| Caminhos vazios coincidentes comprovam indevidamente um vínculo de sessão e worktree. | `node --disable-warning=MODULE_TYPELESS_PACKAGE_JSON --input-type=module -e "import {identidadesDaSessao} from './src/orca/src/crew-visual.ts'; let e={status:'ok',stale:false,agentsWorktree:'',agents:[{terminalId:'t',sessionId:'s'}],snapshot:{starcode:true,worktree:'',crew:[{member:'spock',sessions:[{id:'s',worktree:''}]}]}}; console.log(JSON.stringify(identidadesDaSessao(e)))"` → `{"t":"spock"}` | Recusar caminhos vazios em todas as três fontes e testar que não há vínculo nem troca. | 7bdf0ec · C21 |
| A prova de acessibilidade exercita ouvintes diretamente em elementos simulados, sem verificar navegação real por teclado nem anúncio por leitor de tela. | `src/orca/src/scene.test.ts:328` | Acrescentar prova de interação por teclado e de anúncio acessível em ambiente real. | a1e7cbb · C16 |

## Limits

Regressão do plugin em HEAD: `orca plugin test src/orca` passou, 114 testes.
Regressão em HEAD: `python -m unittest discover -s tests -v` passou, 1116 testes, 1 ignorado.
O aceite real de teclado, leitor de tela, vínculo de sessão e troca de presença não foi executado nesta verificação; a prova automatizada usa dados simulados.
