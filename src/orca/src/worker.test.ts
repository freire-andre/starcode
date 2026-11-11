// Testes do worker da Ponte, com um executor falso no lugar dos processos filhos.
import { assert, hostError, mockHost, mountWorker, test } from 'orca/testing'
import * as main from './worker'

type Call = { cmd: string; args: string[]; cwd?: string }
type Reply = { stdout: string } | Error

const WS_A = { id: 'ws-a', kind: 'worktree', name: 'a', path: 'C:/wt/a', branch: 'feat/a', hostId: null }
const WS_B = { id: 'ws-b', kind: 'worktree', name: 'b', path: 'C:/wt/b', branch: 'feat/b', hostId: null }
const CTX_A = { branch: 'feat/a', displayName: 'a', terminals: [] }
const CTX_B = { branch: 'feat/b', displayName: 'b', terminals: [] }

function snapshot(path: string, over: Record<string, unknown> = {}) {
  return {
    schemaVersion: 1,
    worktree: path,
    starcode: true,
    crew: [],
    gitMode: { mode: 3, label: 'branch + PR', recordedAt: null },
    feature: {
      slug: 'fase-10-ponte',
      phase: 'build',
      size: 'GRANDE',
      done: false,
      linear: ['SC-17', 'SC-18'],
      integrationBranch: null,
      progress: { done: 1, total: 4, percent: 25 },
      breaker: 'closed',
      files: { context: null, spec: null, tasks: null, handoff: null },
    },
    workers: [],
    errors: [],
    ...over,
  }
}

const WORKTREE_OK = JSON.stringify({ ok: true, result: { worktree: { linkedLinearIssue: 'SC-116' } } })
const WORKTREE_SEM = JSON.stringify({ ok: true, result: { worktree: { linkedLinearIssue: null } } })

const LINEAR_OK = JSON.stringify({
  ok: true,
  result: {
    issue: { identifier: 'SC-116', title: 'T2', state: { name: 'In Progress' }, url: 'https://linear.app/x/SC-116' },
  },
})

type Fake = {
  calls: Call[]
  snaps: () => Call[]
  linear: () => Call[]
  python: (path: string) => Reply | Promise<Reply>
  orca: () => Reply | Promise<Reply>
  worktree: () => Reply | Promise<Reply>
  worktrees: () => Call[]
}

function install(): Fake {
  const fake: Fake = {
    calls: [],
    snaps: () => fake.calls.filter((c) => c.args.includes('snapshot')),
    linear: () => fake.calls.filter((c) => c.cmd === 'orca' && c.args[0] === 'linear'),
    worktrees: () => fake.calls.filter((c) => c.cmd === 'orca' && c.args[0] === 'worktree'),
    python: (path) => ({ stdout: JSON.stringify(snapshot(path)) }),
    orca: () => ({ stdout: LINEAR_OK }),
    worktree: () => ({ stdout: WORKTREE_OK }),
  }
  ;(globalThis as any).__ponteExec = async (cmd: string, args: string[], opts: { cwd?: string }) => {
    fake.calls.push({ cmd, args, cwd: opts?.cwd })
    const reply =
      cmd === 'orca'
        ? args[0] === 'worktree' ? await fake.worktree() : await fake.orca()
        : await fake.python(args[args.indexOf('--path') + 1])
    if (reply instanceof Error) throw reply
    return reply
  }
  return fake
}

function hostFor(ctx: unknown, workspaces = [WS_A, WS_B], agents: unknown[] = []) {
  return mockHost({
    results: {
      'workspace.readContext': ctx,
      'workspace.list': { workspaces, truncated: false },
      'agents.list': { agents },
      'statusBar.update': { ok: true },
    },
  })
}

const EVENTS = ['workspace.changed', 'agent.status.changed']
const COMMANDS = ['starcode-ponte.refresh']

async function until(cond: () => boolean, ms = 3000) {
  const end = Date.now() + ms
  while (!cond()) {
    if (Date.now() > end) throw new Error('tempo esgotado esperando a condição')
    await new Promise((r) => setTimeout(r, 10))
  }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms))

const AGENT_EVT = { workspaceId: 'ws-a', paneKey: 'p1', state: 'working', receivedAt: 1 } as const
const mount = (host: ReturnType<typeof hostFor>) => mountWorker(main, { host, events: EVENTS, commands: COMMANDS })

test('worker acha o worktree em foco pelo ramo', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_B))
  const state: any = await worker.request('ponte.state', {})
  assert.equal(state.status, 'ok')
  assert.equal(fake.snaps().length, 1)
  const args = fake.snaps()[0].args
  assert.equal(args[args.indexOf('--path') + 1], 'C:/wt/b')
  assert.ok(args.includes('--json'))
  await worker.deactivate()
})

test('worker desempata ramo igual pelo nome', async () => {
  const fake = install()
  const mk = (n: string, p: string) => ({ id: `ws-${n}`, kind: 'worktree', name: n, path: p, branch: 'refs/heads/main', hostId: null })
  const ws = [mk('ApuraBolsa', 'F:/Projetos/ApuraBolsa'), mk('StarCode', 'F:/Projetos/StarCode'), mk('OuveAI', 'F:/Projetos/OuveAI')]
  const worker = await mount(hostFor({ branch: 'main', displayName: 'StarCode', terminals: [] }, ws))
  const state: any = await worker.request('ponte.state', {})
  assert.equal(state.status, 'ok')
  const args = fake.snaps()[0].args
  assert.equal(args[args.indexOf('--path') + 1], 'F:/Projetos/StarCode')
  await worker.deactivate()
})

test('worker sem worktree em foco', async () => {
  const fake = install()
  let worker = await mount(hostFor(null))
  let state: any = await worker.request('ponte.state', {})
  assert.equal(state.status, 'sem-worktree')
  assert.equal(state.snapshot, null)
  await worker.deactivate()
  worker = await mount(hostFor({ branch: 'outro', displayName: 'x', terminals: [] }))
  state = await worker.request('ponte.state', {})
  assert.equal(state.status, 'sem-worktree')
  assert.equal(fake.snaps().length, 0)
  await worker.deactivate()
  const mk = (n: string) => ({ id: `ws-${n}`, kind: 'worktree', name: n, path: `C:/wt/${n}`, branch: 'main', hostId: null })
  worker = await mount(hostFor({ branch: 'refs/heads/main', displayName: 'Outro', terminals: [] }, [mk('x'), mk('y')]))
  state = await worker.request('ponte.state', {})
  assert.equal(state.status, 'sem-worktree')
  assert.equal(fake.snaps().length, 0)
  await worker.deactivate()
})

test('worker publica o estado após agent.status.changed', async () => {
  install()
  const worker = await mount(hostFor(CTX_A))
  await worker.emit('agent.status.changed', { ...AGENT_EVT })
  await until(() => worker.posts.some((p) => p.event === 'ponte.state'))
  const post: any = worker.posts.find((p) => p.event === 'ponte.state')
  assert.equal(post.payload.status, 'ok')
  assert.equal(post.payload.snapshot.worktree, 'C:/wt/a')
  await worker.deactivate()
})

test('worker agrupa eventos em 300 ms', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_A))
  await worker.emit('agent.status.changed', { ...AGENT_EVT })
  await worker.emit('workspace.changed', { context: CTX_A })
  await worker.emit('agent.status.changed', { ...AGENT_EVT })
  assert.equal(fake.snaps().length, 0)
  await until(() => worker.posts.length >= 1)
  await sleep(500)
  assert.equal(fake.snaps().length, 1)
  assert.equal(worker.posts.filter((p) => p.event === 'ponte.state').length, 1)
  await worker.deactivate()
})

test('worker descarta snapshot de foco antigo', async () => {
  const fake = install()
  let release: () => void = () => {}
  const gate = new Promise<void>((r) => (release = r))
  fake.python = async (path) => {
    if (path === 'C:/wt/a') await gate
    return { stdout: JSON.stringify(snapshot(path)) }
  }
  const host = hostFor(CTX_A)
  const worker = await mount(host)
  const slow = worker.request('ponte.state', {})
  await until(() => fake.snaps().length === 1)
  host.respond('workspace.readContext', CTX_B)
  const fast: any = await worker.request('ponte.state', {})
  assert.equal(fast.snapshot.worktree, 'C:/wt/b')
  release()
  await slow
  const posted = worker.posts.filter((p) => p.event === 'ponte.state') as any[]
  assert.ok(posted.length >= 1)
  assert.ok(posted.every((p) => p.payload.snapshot.worktree === 'C:/wt/b'))
  await worker.deactivate()
})

test('worker consulta a issue vinculada e guarda em cache por 60 s', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_A))
  const first: any = await worker.request('ponte.state', {})
  assert.deepEqual(first.issue, {
    id: 'SC-116',
    title: 'T2',
    state: 'In Progress',
    url: 'https://linear.app/x/SC-116',
  })
  assert.deepEqual(fake.worktrees()[0].args, ['worktree', 'show', '--worktree', 'path:C:/wt/a', '--json'])
  assert.deepEqual(fake.linear()[0].args, ['linear', 'issue', 'SC-116', '--json'])
  assert.ok(!fake.linear()[0].args.includes('--current'))
  await worker.request('ponte.state', {})
  assert.equal(fake.linear().length, 1)
  assert.equal(fake.worktrees().length, 1)
  await worker.deactivate()
})

test('worker sem Linear mostra o ID do Handoff', async () => {
  const fake = install()
  fake.orca = () => new Error('linear fora do ar')
  const worker = await mount(hostFor(CTX_A))
  const state: any = await worker.request('ponte.state', {})
  assert.equal(state.issue.id, 'SC-17')
  assert.equal(state.issueNote, 'Linear indisponível')
  await worker.request('ponte.state', {})
  assert.equal(fake.linear().length, 1)
  await worker.deactivate()

  const sem = install()
  sem.worktree = () => ({ stdout: WORKTREE_SEM })
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.equal(s2.issue.id, 'SC-17')
  assert.equal(s2.issueNote, 'Sem issue vinculada')
  assert.equal(sem.linear().length, 0)
  await w2.deactivate()

  const falha = install()
  falha.worktree = () => new Error('orca fora do ar')
  const w3 = await mount(hostFor(CTX_A))
  const s3: any = await w3.request('ponte.state', {})
  assert.equal(s3.issue.id, 'SC-17')
  assert.equal(s3.issueNote, 'Linear indisponível')
  await w3.deactivate()
})

test('worker com snapshot falho marca desatualizado', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_A))
  const good: any = await worker.request('ponte.state', {})
  assert.equal(good.status, 'ok')
  fake.python = () => new Error('boom\nsegunda linha')
  const bad: any = await worker.request('ponte.state', {})
  assert.equal(bad.status, 'erro')
  assert.equal(bad.stale, true)
  assert.equal(bad.error, 'boom')
  assert.equal(bad.snapshot.worktree, 'C:/wt/a')
  await worker.deactivate()
})

test('worker mostra o erro do ponte.py quando ele sai com 2', async () => {
  const fake = install()
  fake.python = () =>
    Object.assign(new Error('Command failed: python ponte.py snapshot'), {
      code: 2,
      stdout: JSON.stringify({ schemaVersion: 1, error: 'worktree inválido: X' }),
    })
  const worker = await mount(hostFor(CTX_A))
  const state: any = await worker.request('ponte.state', {})
  assert.equal(state.status, 'erro')
  assert.equal(state.error, 'worktree inválido: X')
  const posted = worker.posts.filter((p) => p.event === 'ponte.state') as any[]
  assert.equal(posted[posted.length - 1].payload.error, 'worktree inválido: X')
  await worker.deactivate()
})

test('worker atualiza a barra de status', async () => {
  const fake = install()
  const host = hostFor(CTX_A)
  const worker = await mount(host)
  const last = () => host.callsOf('statusBar.update').at(-1) as any
  await worker.request('ponte.state', {})
  assert.equal(last().id, 'ponte')
  assert.equal(last().text, '🖖 fase-10-ponte · build · modo 3')
  assert.equal(last().tone, 'neutral')
  assert.equal(last().visible, true)

  host.respond('agents.list', {
    agents: [{ terminalId: 't1', title: 'x', agent: 'claude', state: 'blocked', stateStartedAt: 1 }],
  })
  await worker.request('ponte.state', {})
  assert.equal(last().tone, 'warning')

  host.respond('agents.list', { agents: [] })
  fake.python = (p) => ({
    stdout: JSON.stringify(snapshot(p, { feature: { ...(snapshot(p).feature as object), breaker: 'open' } })),
  })
  await worker.request('ponte.state', {})
  assert.equal(last().tone, 'warning')

  fake.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { feature: null })) })
  await worker.request('ponte.state', {})
  assert.equal(last().text, '🖖 StarCode · modo 3')

  fake.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { starcode: false, feature: null, gitMode: null })) })
  await worker.request('ponte.state', {})
  assert.equal(last().visible, false)
  await worker.deactivate()
})

test('atualizar agora ignora o cache', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_A))
  await worker.request('ponte.state', {})
  await worker.request('ponte.state', {})
  assert.equal(fake.linear().length, 1)
  await worker.request('ponte.state', { force: true })
  assert.equal(fake.linear().length, 2)
  await worker.command('starcode-ponte.refresh')
  assert.equal(fake.linear().length, 3)
  assert.equal(fake.snaps().length, 4)
  await worker.deactivate()
})

const FILES = { context: null, spec: 'C:/wt/a/specs/spec.md', tasks: 'c:\\wt\\a\\specs\\tasks.md', handoff: null }
const PICARD = { member: 'picard', emoji: '🛸', name: 'Picard', count: 1, lastAt: null, cliModel: 'claude · claude-opus-5-5' }

function withFeature(files: Record<string, string | null>, crew: unknown[] = [PICARD]) {
  return (p: string) => ({
    stdout: JSON.stringify(
      snapshot(p, { crew, feature: { ...(snapshot(p).feature as object), files } }),
    ),
  })
}

function launchHost() {
  return mockHost({
    results: {
      'workspace.readContext': CTX_A,
      'workspace.list': { workspaces: [WS_A, WS_B], truncated: false },
      'agents.list': { agents: [] },
      'statusBar.update': { ok: true },
      'editor.open': { opened: true },
      'agent.launch': { terminalId: 'term-1' },
    },
  })
}

test('atalho abre spec tasks e handoff', async () => {
  const fake = install()
  fake.python = withFeature(FILES)
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.open', { file: 'spec' }), { opened: true })
  await worker.request('ponte.open', { file: 'tasks' })
  assert.deepEqual(host.callsOf('editor.open'), [
    { workspaceId: 'ws-a', path: 'specs/spec.md' },
    { workspaceId: 'ws-a', path: 'specs/tasks.md' },
  ])
  await assert.rejects(worker.request('ponte.open', { file: 'handoff' }), /file_missing/)
  assert.equal(host.callsOf('editor.open').length, 2)
  // caminho fora do worktree em foco → file_missing, sem chamar o editor
  fake.python = withFeature({ ...FILES, handoff: 'C:/outro/handoff.md' })
  await worker.request('ponte.state', { force: true })
  await assert.rejects(worker.request('ponte.open', { file: 'handoff' }), /file_missing/)
  assert.equal(host.callsOf('editor.open').length, 2)
  await worker.deactivate()
})

test('atalho inicia o Picard uma vez', async () => {
  const fake = install()
  fake.python = withFeature(FILES)
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.launchPicard', {}), { terminalId: 'term-1' })
  assert.deepEqual(host.callsOf('agent.launch'), [
    { workspaceId: 'ws-a', agent: 'claude', prompt: '/starcode:engajar' },
  ])
  const st: any = await worker.request('ponte.state', {})
  assert.match(st.log.map((e: any) => e.text).join('|'), /Picard iniciado.*term-1/)
  await worker.deactivate()

  const codex = install()
  codex.python = withFeature(FILES, [{ ...PICARD, cliModel: 'codex · gpt' }])
  const h2 = launchHost()
  const w2 = await mount(h2)
  await w2.request('ponte.launchPicard', {})
  assert.equal((h2.callsOf('agent.launch')[0] as any).prompt, '$starcode:engajar')
  await w2.deactivate()

  const oc = install()
  oc.python = withFeature(FILES, [{ ...PICARD, cliModel: 'opencode · x' }])
  const h3 = launchHost()
  const w3 = await mount(h3)
  await w3.request('ponte.launchPicard', {})
  assert.deepEqual(h3.callsOf('agent.launch'), [{ workspaceId: 'ws-a', agent: 'opencode', prompt: 'engajar' }])
  await w3.deactivate()
})

test('atalho recusa agente que a Orca não lança', async () => {
  const fake = install()
  fake.python = withFeature(FILES, [{ ...PICARD, cliModel: 'gemini · pro' }])
  const host = launchHost()
  const worker = await mount(host)
  await assert.rejects(
    worker.request('ponte.launchPicard', {}),
    /Agente gemini não pode ser iniciado pela Orca/,
  )
  assert.equal(host.callsOf('agent.launch').length, 0)
  await worker.deactivate()
})

test('diário guarda 20 entradas e o painel mostra 10', async () => {
  install()
  const host = launchHost()
  const worker = await mount(host)
  await worker.request('ponte.state', {})
  const estados = ['working', 'blocked', 'waiting', 'done']
  let last: any
  for (let i = 0; i < 30; i++) {
    host.respond('agents.list', {
      agents: [{ terminalId: 't1', title: 'T3', agent: 'claude', state: estados[i % 4], stateStartedAt: i }],
    })
    last = await worker.request('ponte.state', {})
  }
  assert.equal(last.log.length, 20)
  assert.ok(last.log.every((e: any) => typeof e.at === 'number' && typeof e.text === 'string'))
  assert.match(last.log[19].text, /T3/)
  await worker.deactivate()
})

test('diário registra mudança de worktree e de fase', async () => {
  const fake = install()
  const host = launchHost()
  const worker = await mount(host)
  await worker.request('ponte.state', {})
  host.respond('workspace.readContext', CTX_B)
  await worker.request('ponte.state', {})
  fake.python = (p) => ({
    stdout: JSON.stringify(snapshot(p, { feature: { ...(snapshot(p).feature as object), phase: 'verify' } })),
  })
  const s: any = await worker.request('ponte.state', {})
  const texts = s.log.map((e: any) => e.text).join('|')
  assert.match(texts, /Worktree em foco: b/)
  assert.match(texts, /Fase: build → verify/)
  await worker.deactivate()
})

test('worker registra falhas no log', async () => {
  const logs = (st: any) => st.log.map((e: any) => e.text).join('|')

  // processo externo (worktree show) falha → linha com a ação e a mensagem
  const fake = install()
  fake.worktree = () => new Error('orca fora do ar')
  const w1 = await mount(hostFor(CTX_A))
  const s1: any = await w1.request('ponte.state', { force: true })
  assert.equal(s1.issueNote, 'Linear indisponível')
  assert.match(logs(s1), /orca worktree show.*orca fora do ar/)
  await w1.deactivate()

  // JSON inválido do CLI → "Linear indisponível" e log
  const f2 = install()
  f2.worktree = () => ({ stdout: 'não é json' })
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.equal(s2.issueNote, 'Linear indisponível')
  assert.match(logs(s2), /orca worktree show/)
  await w2.deactivate()

  // vínculo nulo não é falha: "Sem issue vinculada" e nada no log
  const f3 = install()
  f3.worktree = () => ({ stdout: WORKTREE_SEM })
  const w3 = await mount(hostFor(CTX_A))
  const s3: any = await w3.request('ponte.state', {})
  assert.equal(s3.issueNote, 'Sem issue vinculada')
  assert.ok(!/orca worktree show/.test(logs(s3)))
  await w3.deactivate()

  // orca fora do PATH (ENOENT): tenta o binário ao lado do executável antes de desistir
  const f4 = install()
  const enoent = Object.assign(new Error('spawn orca ENOENT'), { code: 'ENOENT' })
  f4.worktree = () => enoent
  const w4 = await mount(hostFor(CTX_A))
  const s4: any = await w4.request('ponte.state', {})
  assert.equal(s4.issueNote, 'Linear indisponível')
  assert.ok(f4.calls.filter((c) => c.cmd !== 'orca' && c.cmd !== 'python' && c.args[0] === 'worktree').length >= 1)
  await w4.deactivate()

  // editor.open e agent.launch falham → linha no log e erro devolvido ao painel
  const f5 = install()
  f5.python = withFeature(FILES)
  const h5 = mockHost({
    results: {
      'workspace.readContext': CTX_A,
      'workspace.list': { workspaces: [WS_A, WS_B], truncated: false },
      'agents.list': { agents: [] },
      'statusBar.update': { ok: true },
      'editor.open': () => { throw hostError('internal', 'sem permissão') },
      'agent.launch': () => { throw hostError('internal', 'agente indisponível') },
    },
  })
  const w5 = await mount(h5)
  await assert.rejects(w5.request('ponte.open', { file: 'spec' }), /sem permissão/)
  await assert.rejects(w5.request('ponte.launchPicard', {}), /agente indisponível/)
  const s5: any = await w5.request('ponte.state', {})
  assert.match(logs(s5), /editor\.open.*sem permissão/)
  assert.match(logs(s5), /agent\.launch.*agente indisponível/)
  await w5.deactivate()
})
