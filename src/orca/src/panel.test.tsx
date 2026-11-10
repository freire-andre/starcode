// Testes do painel da Ponte, com o worker simulado por `mockHost`.
import { assert, mockHost, mount, test } from 'orca/testing'
import * as panel from './panel'
import type { PonteSnapshot, PonteState } from './protocol'

const AT = 1_700_000_000_000

function snap(over: Partial<PonteSnapshot> = {}): PonteSnapshot {
  return {
    schemaVersion: 1,
    worktree: 'C:/wt/a',
    starcode: true,
    crew: [
      { member: 'picard', emoji: '🛸', name: 'Picard', count: 1, lastAt: null, cliModel: 'claude · opus' },
      { member: 'laforge', emoji: '🔧', name: 'LaForge', count: 2, lastAt: null, cliModel: 'claude · sonnet' },
      { member: 'data', emoji: '🤖', name: 'Data', count: 0, lastAt: null, cliModel: null },
    ],
    gitMode: { mode: 3, label: 'branch + PR', recordedAt: null },
    feature: {
      slug: 'fase-10-ponte', phase: 'build', size: 'GRANDE', done: false, linear: ['SC-117'],
      integrationBranch: null, progress: { done: 2, total: 4, percent: 50 }, breaker: 'closed',
      files: { context: null, spec: null, tasks: null, handoff: null },
    },
    workers: [{ label: 'T3', issues: ['SC-117'], base: null, dispatch: null, model: 'sonnet' }],
    errors: [],
    ...over,
  }
}

function estado(over: Partial<PonteState> = {}): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: AT, snapshot: snap(),
    issue: { id: 'SC-117', title: 'Painel Ponte', state: 'In Progress', url: null },
    issueNote: null,
    agents: [{ terminalId: 't1', title: 'T3 painel', agent: 'claude', state: 'working', stateStartedAt: AT }],
    log: [], error: null, ...over,
  }
}


function host(s: PonteState | (() => PonteState)) {
  return mockHost({ requests: { 'ponte.state': () => (typeof s === 'function' ? s() : s) } })
}
const text = (p: { tree(): unknown }) => JSON.stringify(p.tree())
const base = estado()
const dados = base.snapshot!

test('painel pede o estado ao abrir', async () => {
  const h = host(base)
  const p = await mount(panel, { host: h })
  const t = text(p)
  for (const s of ['Tripulação', 'Modo Git', 'Issue', 'Fase SDD', 'Workers da Frota', 'Atalhos']) {
    assert.ok(t.includes(s), s)
  }
  assert.ok(p.find({ type: 'RelativeTime' } as never))
})

test('painel redesenha com ponte.state', async () => {
  const p = await mount(panel, { host: host(base) })
  assert.ok(!text(p).includes('desatualizado'))
  p.post('ponte.state', estado({ stale: true }))
  await p.settled()
  assert.ok(text(p).includes('desatualizado'))
})

test('painel mostra só tripulantes ativos', async () => {
  const p = await mount(panel, { host: host(base) })
  const t = text(p)
  assert.ok(t.includes('LaForge ×2') && t.includes('claude · sonnet'))
  assert.ok(t.includes('Picard') && !t.includes('Data'))
  const q = await mount(panel, { host: host(estado({ snapshot: { ...dados, crew: [] } })) })
  assert.ok(text(q).includes('Tripulação em repouso'))
})

test('painel mostra fase e progresso', async () => {
  const f = dados.feature!
  const p = await mount(panel, { host: host(estado({ snapshot: { ...dados, feature: { ...f, breaker: 'open' } } })) })
  const t = text(p)
  for (const s of ['fase-10-ponte', 'build', 'GRANDE', '2/4 (50%)', 'Disjuntor aberto']) assert.ok(t.includes(s), s)
})

test('painel casa worker com agente', async () => {
  const p = await mount(panel, { host: host(base) })
  assert.ok(text(p).includes('working'))
  const q = await mount(panel, { host: host(estado({ agents: [] })) })
  assert.ok(!text(q).includes('working'))
  const r = await mount(panel, { host: host(estado({ snapshot: { ...dados, workers: [] } })) })
  assert.ok(text(r).includes('Nenhum worker despachado'))
})

test('painel sem StarCode', async () => {
  const p = await mount(panel, { host: host(estado({ snapshot: { ...dados, starcode: false } })) })
  const t = text(p)
  assert.ok(t.includes('StarCode não configurado neste worktree') && t.includes('Atualizar agora'))
  assert.ok(!t.includes('Tripulação'))
  const q = await mount(panel, { host: host(estado({ status: 'sem-worktree', snapshot: null })) })
  assert.ok(text(q).includes('Nenhum worktree em foco'))
})

test('painel com seção indisponível', async () => {
  const errors = [{ source: 'src/crew.yaml', message: 'tripulação ilegível (OSError)' }]
  const p = await mount(panel, { host: host(estado({ snapshot: { ...dados, errors } })) })
  const t = text(p)
  assert.ok(t.includes('indisponível') && t.includes('tripulação ilegível (OSError)'))
  assert.ok(t.includes('Fase SDD') && t.includes('Workers da Frota'))
})
