// Testes do modelo da cena da Ponte (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { buildScene } from './scene-model'
import type { PonteAgent, PonteState, PonteWorker } from './protocol'

const MEMBROS = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy', 'q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan']

function estado(
  over: Partial<PonteState> = {},
  crew: Record<string, [number, string | null]> = {},
  workers: PonteWorker[] = [],
  starcode = true,
): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: 0, issue: null, issueNote: null, agents: [], log: [], error: null,
    snapshot: {
      schemaVersion: 1, worktree: 'C:/wt', starcode,
      crew: MEMBROS.map(m => ({ member: m, emoji: 'x', name: m, count: crew[m]?.[0] ?? 0, lastAt: crew[m]?.[1] ?? null, cliModel: null })),
      gitMode: null, feature: null, workers, errors: [],
    },
    ...over,
  }
}
const worker = (label: string, issues: string[] = []): PonteWorker => ({ label, issues, base: null, dispatch: null, model: null })
const agente = (state: PonteAgent['state'], title: string): PonteAgent => ({ terminalId: null, title, agent: 'claude', state, stateStartedAt: 0 })

test('cena tem uma estação por tripulante e a engenharia', () => {
  const cena = buildScene(estado(), [], 0)
  assert.equal(cena.vazia, false)
  assert.equal(cena.grade.largura, 64)
  assert.equal(cena.grade.altura, 40)
  assert.deepEqual(cena.estacoes.map(e => e.membro).sort(), [...MEMBROS].sort())
  assert.equal(cena.personagens.length, 12)
  assert.ok(cena.turbolift.largura > 0 && cena.engenharia.largura > 0)
})

test('cena senta tripulante ativo e anima a cada 250 ms', () => {
  const s = estado({}, { spock: [2, '2026-01-01T00:00:00Z'] })
  const a = buildScene(s, [], 0).personagens
  const b = buildScene(s, [], 250).personagens
  const c = buildScene(s, [], 500).personagens
  const spock = (p: typeof a) => p.find(x => x.membro === 'spock')!
  assert.equal(spock(a).pose, 'sentado')
  assert.equal(spock(a).quadro, 0)
  assert.equal(spock(b).quadro, 1)
  assert.equal(spock(c).quadro, 0)
  const picard = a.find(x => x.membro === 'picard')!
  assert.equal(picard.pose, 'de-pe')
  assert.equal(picard.quadro, 0)
  const lift = buildScene(s, [], 0).turbolift
  assert.ok(picard.x >= lift.x && picard.x < lift.x + lift.largura && picard.y >= lift.y && picard.y < lift.y + lift.altura)
})

test('cena põe o balão no personagem do agente bloqueado', () => {
  const ws = [worker('T3', ['SC-117']), worker('T4', ['SC-118'])]
  // casa pelo rótulo do worker
  let cena = buildScene(estado({}, {}, ws), [agente('blocked', 'laforge T4 implementando')], 0)
  assert.deepEqual(cena.workers.map(w => w.balao), [false, true])
  // casa pela issue
  cena = buildScene(estado({}, {}, ws), [agente('waiting', 'trabalho em SC-117')], 0)
  assert.deepEqual(cena.workers.map(w => w.balao), [true, false])
  // sem casamento: tripulante ativo de lastAt mais recente
  const crew: Record<string, [number, string]> = { spock: [1, '2026-01-01T00:00:00Z'], data: [1, '2026-01-02T00:00:00Z'] }
  cena = buildScene(estado({}, crew, ws), [agente('blocked', 'outra coisa')], 0)
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro), ['data'])
  // ninguém ativo: Picard
  cena = buildScene(estado(), [agente('waiting', 'x')], 0)
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro), ['picard'])
  // working não gera balão
  cena = buildScene(estado(), [agente('working', 'x')], 0)
  assert.equal(cena.personagens.some(p => p.balao), false)
})

test('cena desenha até 6 workers e +N', () => {
  const ws = Array.from({ length: 8 }, (_, i) => worker(`T${i + 1}`))
  const cena = buildScene(estado({}, {}, ws), [agente('done', 'laforge T2')], 0)
  assert.equal(cena.workers.length, 6)
  assert.deepEqual(cena.workers.map(w => w.rotulo), ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'])
  assert.equal(cena.maisN, 2)
  assert.deepEqual(cena.workers.map(w => w.concluido), [false, true, false, false, false, false])
  assert.equal(buildScene(estado({}, {}, ws.slice(0, 6)), [], 0).maisN, 0)
})

test('cena vazia mostra a frase do estado', () => {
  const vazia = (s: PonteState) => buildScene(s, [], 0)
  const semWt = vazia(estado({ status: 'sem-worktree', snapshot: null }))
  assert.equal(semWt.vazia, true)
  assert.equal(semWt.mensagem, 'Nenhum worktree em foco')
  assert.equal(semWt.personagens.length, 0)
  assert.equal(vazia(estado({}, {}, [], false)).mensagem, 'StarCode não configurado neste worktree')
  assert.equal(vazia(estado({ status: 'erro', snapshot: null, error: 'python não encontrado\ndetalhe' })).mensagem, 'python não encontrado')
  // erro com estado bom anterior continua desenhando
  const comBom = vazia(estado({ status: 'erro', stale: true, error: 'falhou' }))
  assert.equal(comBom.vazia, false)
  assert.equal(comBom.mensagem, null)
})

test('cena distribui os inativos no turbolift', () => {
  const cena = buildScene(estado(), [], 0)
  const lift = cena.turbolift
  const inativos = cena.personagens.filter(p => p.pose === 'de-pe')
  assert.equal(inativos.length, 12)
  const pontos = new Set(inativos.map(p => `${p.x},${p.y}`))
  assert.equal(pontos.size, inativos.length)
  for (const p of inativos) {
    assert.ok(p.x >= lift.x && p.x < lift.x + lift.largura && p.y >= lift.y && p.y < lift.y + lift.altura, p.membro)
  }
  // sem rótulo sobreposto: rótulo com fonte de 1,3 célula: ~0,72 célula por letra, 1,5 de altura
  for (let i = 0; i < inativos.length; i++) {
    for (let j = i + 1; j < inativos.length; j++) {
      const a = inativos[i], b = inativos[j]
      const meia = (0.72 * (a.nome.length + b.nome.length)) / 2
      const sobrepoe = Math.abs(a.x - b.x) < meia && Math.abs(a.y - b.y) < 1.5
      assert.ok(!sobrepoe, `${a.membro} x ${b.membro}`)
    }
  }
  // determinístico (função pura)
  assert.deepEqual(buildScene(estado(), [], 0).personagens, cena.personagens)
})
