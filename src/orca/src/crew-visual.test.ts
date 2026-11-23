// Testes dos perfis visuais e do estado confiável da tripulação (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { ESTADOS, MEMBROS, PERFIS, estadosDaTripulacao } from './crew-visual'
import type { EstadoVisual, Identidades } from './crew-visual'
import type { PonteAgent, PonteState } from './protocol'

const ORDEM = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy', 'q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan']
const NOMES = [
  'Jean-Luc Picard', 'Spock', 'Deanna Troi', 'Data', 'Geordi La Forge', 'Leonard McCoy',
  'Q', 'Nyota Uhura', 'Montgomery Scott', 'James T. Kirk', 'Worf', 'Guinan',
]
const EMOJIS = ['🛸', '🖖', '💜', '🤖', '🔧', '🧪', '✨', '📡', '⚙️', '🚀', '🛡️', '🍸']

function estado(over: Partial<PonteState> = {}, agents: PonteAgent[] = []): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: 0, issue: null, issueNote: null, agents, log: [], error: null,
    snapshot: {
      schemaVersion: 1, worktree: 'C:/wt', starcode: true,
      crew: ORDEM.map(m => ({ member: m, emoji: 'x', name: m, count: 0, lastAt: null, cliModel: null })),
      gitMode: null, feature: null, workers: [], errors: [],
    },
    ...over,
  }
}
const agente = (terminalId: string | null, state: PonteAgent['state'], title = 'qualquer'): PonteAgent =>
  ({ terminalId, title, agent: 'claude', state, stateStartedAt: 0 })
type Res = ReturnType<typeof estadosDaTripulacao>
const de = (res: Res, membro: string) => res.find(r => r.membro === membro)!
const todos = (res: Res, e: EstadoVisual) => res.length === 12 && res.every(r => r.estado === e)

test('ponte viva identifica os 12 integrantes', () => {
  assert.deepEqual(MEMBROS, ORDEM)
  assert.deepEqual(PERFIS.map(p => p.membro), ORDEM)
  assert.deepEqual(PERFIS.map(p => p.nome), NOMES)
  assert.deepEqual(PERFIS.map(p => p.emoji), EMOJIS)
  // identidade visual própria: nenhum nome, emoji, cor de uniforme ou acessório se repete
  for (const campo of ['nome', 'emoji', 'cor', 'acessorio'] as const) {
    assert.equal(new Set(PERFIS.map(p => p[campo])).size, 12, `${campo} repetido`)
  }
  for (const p of PERFIS) {
    assert.match(p.cor, /^#[0-9a-f]{6}$/)
    assert.ok(p.acessorio.length > 0)
  }
  assert.equal(PERFIS.find(p => p.membro === 'picard')!.acessorio, 'cabeca-calva')
  assert.equal(PERFIS.find(p => p.membro === 'spock')!.acessorio, 'orelhas-pontudas')
})

test('ponte viva representa trabalho', () => {
  const ids: Identidades = { 'term-1': 'laforge' }
  const res = estadosDaTripulacao(estado({}, [agente('term-1', 'working')]), ids)
  assert.deepEqual(de(res, 'laforge'), { membro: 'laforge', estado: 'trabalhando', motivo: 'agente vinculado trabalhando' })
  assert.deepEqual(ESTADOS.trabalhando, { estado: 'trabalhando', simbolo: '⚙', texto: 'trabalhando', animaConsole: true })
  // só o estado "trabalhando" opera o console
  assert.deepEqual((Object.keys(ESTADOS) as EstadoVisual[]).filter(e => ESTADOS[e].animaConsole), ['trabalhando'])
})

test('ponte viva representa trabalho pelo count do snapshot', () => {
  // count do snapshot = sessões active válidas (crew_live.count_members, TTL): > 0 trabalha, 0 está livre
  const e = estado()
  for (const [m, n] of [['picard', 1], ['laforge', 3]] as const) e.snapshot!.crew.find(c => c.member === m)!.count = n
  const res = estadosDaTripulacao(e, {})
  assert.deepEqual(de(res, 'picard'), { membro: 'picard', estado: 'trabalhando', motivo: 'sessão ativa no snapshot (count > 0)' })
  assert.equal(de(res, 'laforge').estado, 'trabalhando')
  assert.equal(res.filter(r => r.estado === 'trabalhando').length, 2)
  assert.equal(res.filter(r => r.estado === 'ocioso').length, 10)
  // agente ativo sem vínculo: o count agregado de outro integrante não o explica; quem tem count segue
  // trabalhando e ninguém mais é rotulado ocioso sem evidência
  const comAgente = estadosDaTripulacao({ ...e, agents: [agente('t', 'working', 'claude')] }, {})
  assert.deepEqual(de(comAgente, 'picard'), { membro: 'picard', estado: 'trabalhando', motivo: 'sessão ativa no snapshot (count > 0)' })
  assert.equal(de(comAgente, 'laforge').estado, 'trabalhando')
  assert.deepEqual(de(comAgente, 'spock'), { membro: 'spock', estado: 'desconhecido', motivo: 'agente ativo sem identidade confiável' })
  assert.equal(comAgente.filter(r => r.estado === 'desconhecido').length, 10)
  assert.equal(comAgente.filter(r => r.estado === 'ocioso').length, 0)
  // agente sem vínculo já concluído não impede o ocioso; agente vinculado a outro continua sendo dele
  const concluidoSemVinculo = estadosDaTripulacao({ ...e, agents: [agente('t', 'done', 'claude')] }, {})
  assert.equal(de(concluidoSemVinculo, 'spock').estado, 'ocioso')
  const vinculado = estadosDaTripulacao({ ...e, agents: [agente('a', 'working')] }, { a: 'picard' })
  assert.equal(de(vinculado, 'spock').estado, 'ocioso')
  // o estado do agente vinculado vence o count (esperando fica esperando)
  const espera = estadosDaTripulacao({ ...e, agents: [agente('a', 'waiting')] }, { a: 'picard' })
  assert.equal(de(espera, 'picard').estado, 'aguardando')
})

test('ponte viva representa ociosidade', () => {
  const res = estadosDaTripulacao(estado(), {})
  assert.deepEqual(de(res, 'spock'), { membro: 'spock', estado: 'ocioso', motivo: 'sem sessão ativa no snapshot do repositório' })
  assert.deepEqual(ESTADOS.ocioso, { estado: 'ocioso', simbolo: '💤', texto: 'ocioso', animaConsole: false })
  // agente concluído não conta como atividade: os outros seguem ociosos
  const comConcluido = estadosDaTripulacao(estado({}, [agente('term-1', 'done')]), { 'term-1': 'data' })
  assert.equal(de(comConcluido, 'spock').estado, 'ocioso')
})

test('ponte viva distingue estados', () => {
  const ids: Identidades = { a: 'picard', b: 'spock', c: 'troi', d: 'data' }
  const res = estadosDaTripulacao(
    estado({}, [agente('a', 'working'), agente('b', 'waiting'), agente('c', 'blocked'), agente('d', 'done')]), ids,
  )
  assert.deepEqual(res.slice(0, 4).map(r => r.estado), ['trabalhando', 'aguardando', 'bloqueado', 'concluido'])
  assert.deepEqual(ESTADOS.aguardando, { estado: 'aguardando', simbolo: '⏳', texto: 'aguardando', animaConsole: false })
  assert.deepEqual(ESTADOS.bloqueado, { estado: 'bloqueado', simbolo: '⛔', texto: 'bloqueado', animaConsole: false })
  assert.deepEqual(ESTADOS.concluido, { estado: 'concluido', simbolo: '✔', texto: 'concluído', animaConsole: false })
  assert.deepEqual(ESTADOS.desconhecido, { estado: 'desconhecido', simbolo: '?', texto: 'desconhecido', animaConsole: false })
  const chaves = Object.keys(ESTADOS) as EstadoVisual[]
  assert.deepEqual(chaves, ['trabalhando', 'ocioso', 'aguardando', 'bloqueado', 'concluido', 'desconhecido'])
  for (const campo of ['simbolo', 'texto'] as const) {
    assert.equal(new Set(chaves.map(k => ESTADOS[k][campo])).size, 6, `${campo} repetido`)
  }
})

test('ponte viva não inventa atividade', () => {
  // título com o nome do integrante não é identidade
  const porTitulo = estadosDaTripulacao(estado({}, [agente('t', 'working', 'laforge SC-217 implementando')]), {})
  assert.deepEqual(de(porTitulo, 'laforge'), { membro: 'laforge', estado: 'desconhecido', motivo: 'agente ativo sem identidade confiável' })
  assert.equal(de(porTitulo, 'spock').estado, 'desconhecido')
  // agente sem terminalId nunca é vinculado, mesmo com mapa que tenha a chave "null"
  const semId = estadosDaTripulacao(estado({}, [agente(null, 'working')]), { null: 'kirk' })
  assert.equal(de(semId, 'kirk').estado, 'desconhecido')
  // dois agentes vinculados ao mesmo integrante com estados diferentes: ambíguo
  const dupla = estadosDaTripulacao(estado({}, [agente('a', 'working'), agente('b', 'done')]), { a: 'worf', b: 'worf' })
  assert.deepEqual(de(dupla, 'worf'), { membro: 'worf', estado: 'desconhecido', motivo: 'mais de um agente vinculado com estados diferentes' })
  // vínculo para quem não é da tripulação é ignorado
  const fora = estadosDaTripulacao(estado({}, [agente('x', 'working')]), { x: 'riker' })
  assert.equal(fora.length, 12)
  assert.equal(de(fora, 'picard').estado, 'desconhecido')
  // count > 0 só vale com dado atual: com dado antigo ou erro o mesmo count é desconhecido, nunca trabalho
  for (const over of [{ stale: true }, { status: 'erro' as const, error: 'x' }]) {
    const velho = estado(over)
    velho.snapshot!.crew.find(c => c.member === 'data')!.count = 7
    assert.equal(de(estadosDaTripulacao(velho, {}), 'data').estado, 'desconhecido')
  }
  // count inválido (negativo, NaN, texto) não é atividade
  for (const ruim of [-1, Number.NaN, '1' as unknown as number]) {
    const e = estado()
    e.snapshot!.crew.find(c => c.member === 'data')!.count = ruim
    assert.equal(de(estadosDaTripulacao(e, {}), 'data').estado, 'ocioso')
  }
  // dados antigos, erro, sem worktree, sem snapshot ou projeto sem StarCode: tudo desconhecido
  assert.ok(todos(estadosDaTripulacao(estado({ stale: true }), {}), 'desconhecido'))
  assert.ok(todos(estadosDaTripulacao(estado({ status: 'erro', error: 'x' }), {}), 'desconhecido'))
  assert.ok(todos(estadosDaTripulacao(estado({ status: 'sem-worktree' }), {}), 'desconhecido'))
  assert.ok(todos(estadosDaTripulacao(estado({ snapshot: null }), {}), 'desconhecido'))
  const semStarcode = estado()
  semStarcode.snapshot!.starcode = false
  assert.ok(todos(estadosDaTripulacao(semStarcode, {}), 'desconhecido'))
  // integrante ausente do snapshot: desconhecido, não ocioso
  const faltando = estado()
  faltando.snapshot!.crew = faltando.snapshot!.crew.filter(c => c.member !== 'guinan')
  assert.deepEqual(de(estadosDaTripulacao(faltando, {}), 'guinan'), { membro: 'guinan', estado: 'desconhecido', motivo: 'integrante ausente do snapshot' })
  // estado de agente fora do contrato vira desconhecido
  const estranho = estadosDaTripulacao(estado({}, [agente('a', 'dormindo' as PonteAgent['state'])]), { a: 'q' })
  assert.equal(de(estranho, 'q').estado, 'desconhecido')
})

test('ponte viva não afirma escopo de worktree nos dados agregados', () => {
  // sessions.json agrega a tripulação do repositório: nenhum motivo diz "worktree" nem inventa correspondência
  const e = estado()
  e.snapshot!.crew.find(c => c.member === 'spock')!.count = 1
  for (const agentes of [[], [agente('t', 'working', 'spock implementando')], [agente('a', 'blocked')]]) {
    const res = estadosDaTripulacao({ ...e, agents: agentes }, {})
    for (const r of res) assert.ok(!/worktree/i.test(r.motivo), r.motivo)
    // o count do Spock vale como trabalho, mas o agente sem vínculo não é atribuído a ele nem a ninguém
    assert.equal(de(res, 'spock').estado, 'trabalhando')
  }
  // agente vinculado ao Worf: o Worf segue o agente; sem count o agente não é atribuído ao Spock
  const comVinculo = estadosDaTripulacao({ ...e, agents: [agente('a', 'blocked')] }, { a: 'worf' })
  assert.equal(de(comVinculo, 'worf').estado, 'bloqueado')
  assert.equal(de(comVinculo, 'spock').estado, 'trabalhando')
  assert.equal(de(comVinculo, 'data').estado, 'ocioso')
})
