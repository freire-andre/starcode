// Testes do modelo da cena da Ponte (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { buildScene, LEGENDA } from './scene-model'
import type { Cena } from './scene-model'
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
  assert.equal(cena.grade.largura, 48)
  assert.equal(cena.grade.altura, 72)
  assert.ok(cena.grade.altura > cena.grade.largura) // layout vertical
  assert.deepEqual(cena.estacoes.map(e => e.membro).sort(), [...MEMBROS].sort())
  assert.equal(cena.personagens.length, 12)
  assert.ok(cena.telao.largura > 0 && cena.engenharia.largura > 0)
  assert.ok(cena.telao.y + cena.telao.altura <= cena.engenharia.y) // telão em cima, engenharia embaixo
  assert.equal(cena.vagas.length, 6)
  // cada estação mostra o emoji e o nome do tripulante
  for (const p of cena.personagens) {
    assert.ok(cena.rotulos.some(r => r.tipo === 'emoji' && r.texto === p.emoji), `emoji ${p.membro}`)
    assert.ok(cena.rotulos.some(r => r.tipo === 'nome' && r.texto === p.nome), `nome ${p.membro}`)
  }
  // Picard no centro, LaForge dentro da engenharia, o resto fora dela
  const por = (m: string) => cena.personagens.find(p => p.membro === m)!
  assert.equal(por('picard').x, cena.grade.largura / 2)
  const eng = cena.engenharia
  const dentro = (p: { x: number; y: number }) => p.y >= eng.y && p.y < eng.y + eng.altura
  assert.ok(dentro(por('laforge')))
  assert.equal(cena.personagens.filter(dentro).length, 1)
  assert.equal(new Set(cena.estacoes.map(e => `${e.x},${e.y}`)).size, 12)
  // os ladrilhos das estações não se tocam
  const tocam = (a: Cena['personagens'][number]['caixa'], b: typeof a) =>
    a.x < b.x + b.largura && b.x < a.x + a.largura && a.y < b.y + b.altura && b.y < a.y + a.altura
  for (let i = 0; i < 12; i++) {
    for (let j = i + 1; j < 12; j++) {
      assert.ok(!tocam(cena.personagens[i].caixa, cena.personagens[j].caixa), `${cena.personagens[i].membro} x ${cena.personagens[j].membro}`)
    }
  }
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
  // inativo fica na própria estação (mesma posição de quando está ativo), apagado e parado
  assert.equal(spock(a).ativo, true)
  assert.equal(picard.ativo, false)
  const ativoPicard = buildScene(estado({}, { picard: [1, null] }), [], 0).personagens.find(x => x.membro === 'picard')!
  assert.equal(`${ativoPicard.x},${ativoPicard.y}`, `${picard.x},${picard.y}`)
  assert.equal(buildScene(s, [], 250).personagens.find(x => x.membro === 'picard')!.quadro, 0)
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
  assert.equal(semWt.rotulos.map(r => r.texto).join(" "), "Nenhum worktree em foco")
  assert.equal(vazia(estado({}, {}, [], false)).mensagem, 'StarCode não configurado neste worktree')
  assert.equal(vazia(estado({ status: 'erro', snapshot: null, error: 'python não encontrado\ndetalhe' })).mensagem, 'python não encontrado')
  // erro com estado bom anterior continua desenhando
  const comBom = vazia(estado({ status: 'erro', stale: true, error: 'falhou' }))
  assert.equal(comBom.vazia, false)
  assert.equal(comBom.mensagem, null)
})

function sobrepoe(a: Cena['rotulos'][number], b: Cena['rotulos'][number]): boolean {
  const x = a.caixa, y = b.caixa
  return x.x < y.x + y.largura && y.x < x.x + x.largura && x.y < y.y + y.altura && y.y < x.y + x.altura
}

test('cena sem rótulos sobrepostos', () => {
  const crew: Record<string, [number, string]> = { spock: [1, '2026-01-01T00:00:00Z'], laforge: [1, '2026-01-02T00:00:00Z'] }
  const ws = Array.from({ length: 8 }, (_, i) => worker(`T${i + 1}`, [`SC-${i}`]))
  const agentes = [agente('done', 'laforge T1'), agente('blocked', 'laforge T3'), agente('waiting', 'laforge T8'), agente('blocked', 'outra')]
  const cenas = [
    buildScene(estado(), [], 0),
    buildScene(estado({}, crew, ws, true), agentes, 250),
    buildScene(estado({}, crew, ws.slice(0, 3)), agentes, 0),
    buildScene(estado({ status: 'erro', snapshot: null, error: 'um erro bem longo que precisa quebrar em várias linhas de texto' }), [], 0),
  ]
  for (const cena of cenas) {
    const { largura, altura } = cena.grade
    for (const r of cena.rotulos) {
      // a 240 px de largura a escala é 240 / 48 = 5 px por célula: a fonte tem de dar pelo menos 10 px
      assert.ok(r.tam * (240 / largura) >= 10, `fonte pequena: ${r.texto}`)
      assert.ok(r.caixa.x >= 0 && r.caixa.y >= 0 && r.caixa.x + r.caixa.largura <= largura && r.caixa.y + r.caixa.altura <= altura, `fora da grade: ${r.texto}`)
    }
    for (let i = 0; i < cena.rotulos.length; i++) {
      for (let j = i + 1; j < cena.rotulos.length; j++) {
        const a = cena.rotulos[i], b = cena.rotulos[j]
        assert.ok(!sobrepoe(a, b), `${a.texto} x ${b.texto}`)
      }
    }
  }
  // determinístico (função pura)
  assert.deepEqual(buildScene(estado(), [], 0), buildScene(estado(), [], 0))
})

test('cena mostra o telão com fase e progresso', () => {
  const base = estado()
  base.snapshot!.feature = {
    slug: 'fase-10-ponte', phase: 'review', size: null, done: false, linear: [], integrationBranch: null,
    progress: { done: 8, total: 9, percent: 89 }, breaker: 'closed',
    files: { context: null, spec: null, tasks: null, handoff: null },
  }
  const cena = buildScene(base, [], 0)
  const textos = cena.rotulos.map(r => r.texto)
  assert.ok(textos.includes('fase-10-ponte'))
  assert.ok(textos.includes('review'))
  assert.ok(textos.includes('8/9 · 89%'))
  assert.equal(cena.progresso?.percentual, 89)
  assert.equal(cena.progresso?.feitos, 8)
  assert.equal(cena.progresso?.total, 9)
  assert.ok(cena.rotulos.some(r => r.tipo === 'legenda' && r.texto === LEGENDA))
  assert.ok(LEGENDA.includes('aceso = trabalhando') && LEGENDA.includes('apagado = livre'))
  // a legenda fica embaixo, abaixo da engenharia
  const legenda = cena.rotulos.find(r => r.tipo === 'legenda')!
  assert.ok(legenda.y > cena.engenharia.y + cena.engenharia.altura)
  // sem feature: o telão avisa
  assert.ok(buildScene(estado(), [], 0).rotulos.some(r => r.texto === 'sem feature ativa'))
})
