// Testes do painel da Ponte, com o worker simulado por `mockHost`.
import { assert, hostError, mockHost, mount, test } from 'orca/testing'
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

const ARQ = { context: null, spec: 'a/spec.md', tasks: null, handoff: 'a/handoff.md' }
const comArquivos = () =>
  estado({
    snapshot: { ...dados, feature: { ...dados.feature!, files: ARQ } },
    issue: { id: 'SC-118', title: 'T4', state: 'In Progress', url: 'https://linear.app/x/SC-118' },
  })

test('atalho abre spec tasks e handoff', async () => {
  const pedidos: unknown[] = []
  const h = mockHost({
    requests: {
      'ponte.state': comArquivos,
      'ponte.open': (i) => {
        pedidos.push(i)
        return { opened: true }
      },
    },
  })
  const p = await mount(panel, { host: h })
  assert.equal(p.find({ type: 'Button', text: 'Abrir spec' })!.disabled, false)
  assert.equal(p.find({ type: 'Button', text: 'Abrir tasks' })!.disabled, true)
  assert.equal(p.find({ type: 'Button', text: 'Abrir Handoff' })!.disabled, false)
  await p.press({ type: 'Button', text: 'Abrir spec' })
  await p.press({ type: 'Button', text: 'Abrir Handoff' })
  assert.deepEqual(pedidos, [{ file: 'spec' }, { file: 'handoff' }])
})

test('atalho abre a issue no navegador', async () => {
  const h = host(comArquivos)
  const p = await mount(panel, { host: h })
  await p.press({ type: 'Button', text: 'Abrir issue no Linear' })
  assert.deepEqual(h.callsOf('shell.openExternal'), [{ url: 'https://linear.app/x/SC-118' }])
  const q = await mount(panel, { host: host(base) })
  assert.equal(q.find({ type: 'Button', text: 'Abrir issue no Linear' })!.disabled, true)
})

test('atalho inicia o Picard uma vez', async () => {
  let n = 0
  let release: () => void = () => {}
  const gate = new Promise<void>((r) => (release = r))
  const h = mockHost({
    requests: {
      'ponte.state': comArquivos,
      'ponte.launchPicard': async () => {
        n++
        await gate
        return { terminalId: 't9' }
      },
    },
  })
  const p = await mount(panel, { host: h })
  const alvo = { type: 'Button', text: 'Iniciar Picard' }
  const primeiro = p.press(alvo)
  await new Promise((r) => setTimeout(r, 20))
  assert.equal(p.find(alvo)!.disabled, true)
  release()
  await primeiro
  await p.settled()
  assert.equal(n, 1)
  assert.equal(p.find(alvo)!.disabled, false)
  assert.ok(text(p).includes('Picard iniciado em segundo plano'))
  assert.ok(text(p).includes('O agente abre em segundo plano'))
})

test('atalho recusa agente que a Orca não lança', async () => {
  const h = mockHost({
    requests: {
      'ponte.state': comArquivos,
      'ponte.launchPicard': () => {
        throw hostError('not_launchable', 'Agente gemini não pode ser iniciado pela Orca')
      },
    },
  })
  const p = await mount(panel, { host: h })
  await p.press({ type: 'Button', text: 'Iniciar Picard' })
  assert.ok(text(p).includes('Agente gemini não pode ser iniciado pela Orca'))
})

test('diário guarda 20 entradas e o painel mostra 10', async () => {
  const log = Array.from({ length: 20 }, (_, i) => ({ at: AT + i, text: `evento ${i}.` }))
  const p = await mount(panel, { host: host(estado({ log })) })
  const t = text(p)
  assert.ok(t.includes('Diário de bordo'))
  for (let i = 10; i < 20; i++) assert.ok(t.includes(`evento ${i}.`), `evento ${i}`)
  for (let i = 0; i < 10; i++) assert.ok(!t.includes(`evento ${i}.`), `sem evento ${i}`)
  const vazio = await mount(panel, { host: host(base) })
  assert.ok(text(vazio).includes('Sem registros'))
})

test('painel mostra a nota da issue do Handoff', async () => {
  const doHandoff = { id: 'SC-17', title: null, state: null, url: null }
  const p = await mount(panel, { host: host(estado({ issue: doHandoff, issueNote: 'Sem issue vinculada' })) })
  const t = text(p)
  assert.ok(t.includes('SC-17') && t.includes('Sem issue vinculada'))
  const q = await mount(panel, { host: host(estado({ issue: doHandoff, issueNote: 'Linear indisponível' })) })
  assert.ok(text(q).includes('Linear indisponível'))
  // com título e estado, a nota não aparece
  assert.ok(!text(await mount(panel, { host: host(base) })).includes('Linear indisponível'))
})

test('painel estreito quebra os atalhos', async () => {
  const p = await mount(panel, { host: host(base) })
  const linhas = (JSON.stringify(p.tree()).match(/"wrap":true/g) ?? []).length
  assert.ok(linhas >= 2, 'as linhas de botões dos Atalhos devem quebrar')
})
