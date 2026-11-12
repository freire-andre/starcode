// Testes do worker da Ponte, com um executor falso no lugar dos processos filhos.
import { assert, hostError, mockHost, mountWorker, test } from 'orca/testing'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { homedir, tmpdir } from 'node:os'
import { join } from 'node:path'
import * as main from './worker'

const EXE = process.platform === 'win32' ? 'orca.exe' : 'orca'
const CLI_DIR = mkdtempSync(join(tmpdir(), 'ponte-cli-'))
const FAKE_CLI = join(CLI_DIR, EXE)
writeFileSync(FAKE_CLI, '')
const isOrca = (cmd: string) => /(^|[\\/])orca(\.exe)?$/i.test(cmd)

type Call = { cmd: string; args: string[]; cwd?: string; env?: Record<string, string | undefined> }
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
    linear: () => fake.calls.filter((c) => isOrca(c.cmd) && c.args[0] === 'linear'),
    worktrees: () => fake.calls.filter((c) => isOrca(c.cmd) && c.args[0] === 'worktree'),
    python: (path) => ({ stdout: JSON.stringify(snapshot(path)) }),
    orca: () => ({ stdout: LINEAR_OK }),
    worktree: () => ({ stdout: WORKTREE_OK }),
  }
  process.env.ORCA_CLI_PATH = FAKE_CLI
  ;(globalThis as any).__ponteExec = async (cmd: string, args: string[], opts: { cwd?: string; env?: Record<string, string | undefined> }) => {
    fake.calls.push({ cmd, args, cwd: opts?.cwd, env: opts?.env })
    const reply =
      isOrca(cmd)
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

test('worker roda o python sem gravar bytecode', async () => {
  const fake = install()
  const worker = await mount(hostFor(CTX_B))
  await worker.request('ponte.state', {})
  const call = fake.snaps()[0]
  assert.equal(call.args[0], '-B')
  assert.equal(call.env?.PYTHONDONTWRITEBYTECODE, '1')
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
  assert.equal(state.issueNote, 'Linear indisponível pelo CLI')
  await worker.request('ponte.state', {})
  assert.equal(fake.linear().length, 1)
  await worker.deactivate()

  const sem = install()
  sem.worktree = () => ({ stdout: WORKTREE_SEM })
  sem.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { feature: { ...(snapshot(p).feature as object), linear: [] } })) })
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.equal(s2.issue, null)
  assert.equal(s2.issueNote, 'Sem issue vinculada')
  assert.equal(sem.linear().length, 0)
  await w2.deactivate()

  const falha = install()
  falha.worktree = () => new Error('orca fora do ar')
  const w3 = await mount(hostFor(CTX_A))
  const s3: any = await w3.request('ponte.state', {})
  assert.equal(s3.issue.id, 'SC-17')
  assert.equal(s3.issueNote, 'Linear indisponível pelo CLI')
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

const cliDown = (f: Fake) => {
  f.orca = () => Object.assign(new Error('cli fora'), { code: 'EFAIL' })
}
const agentCalls = (f: Fake) => f.calls.filter((c) => isOrca(c.cmd) && c.args[0] === 'agent')

test('atalho inicia o Picard uma vez', async () => {
  const fake = install()
  cliDown(fake)
  fake.python = withFeature(FILES)
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.launchPicard', {}), { terminalId: 'term-1', visible: false })
  assert.deepEqual(host.callsOf('agent.launch'), [
    { workspaceId: 'ws-a', agent: 'claude', prompt: '/starcode:engajar' },
  ])
  const st: any = await worker.request('ponte.state', {})
  assert.match(st.log.map((e: any) => e.text).join('|'), /Picard iniciado em segundo plano/)
  await worker.deactivate()

  const codex = install()
  cliDown(codex)
  codex.python = withFeature(FILES, [{ ...PICARD, cliModel: 'codex · gpt' }])
  const h2 = launchHost()
  const w2 = await mount(h2)
  await w2.request('ponte.launchPicard', {})
  assert.equal((h2.callsOf('agent.launch')[0] as any).prompt, '$starcode:engajar')
  await w2.deactivate()

  const oc = install()
  cliDown(oc)
  oc.python = withFeature(FILES, [{ ...PICARD, cliModel: 'opencode · x' }])
  const h3 = launchHost()
  const w3 = await mount(h3)
  await w3.request('ponte.launchPicard', {})
  assert.deepEqual(h3.callsOf('agent.launch'), [{ workspaceId: 'ws-a', agent: 'opencode', prompt: 'engajar' }])
  await w3.deactivate()
})

const CLI_LAUNCH_OK = JSON.stringify({ ok: true, result: { terminal: { handle: 'term_abc' } } })

test('atalho abre o Picard numa aba visível pelo CLI', async () => {
  const fake = install()
  fake.python = withFeature(FILES, [{ ...PICARD, cliModel: 'claude · claude-opus-5-5' }])
  fake.orca = () => ({ stdout: CLI_LAUNCH_OK })
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.launchPicard', {}), { terminalId: 'term_abc', visible: true })
  const calls = agentCalls(fake)
  assert.equal(calls.length, 1)
  assert.deepEqual(calls[0].args, [
    'agent', 'launch', '--agent', 'claude', '--worktree', 'path:C:/wt/a',
    '--prompt', '/starcode:engajar', '--surface', 'terminal', '--focus', '--model', 'claude-opus-5-5', '--json',
  ])
  assert.equal(host.callsOf('agent.launch').length, 0)
  const st: any = await worker.request('ponte.state', {})
  assert.match(st.log.map((e: any) => e.text).join('|'), /Picard iniciado numa aba visível/)
  await worker.deactivate()
})

test('atalho sem modelo real não manda --model e aceita resposta sem terminal', async () => {
  const fake = install()
  fake.python = withFeature(FILES, [{ ...PICARD, cliModel: 'codex · padrão do CLI' }])
  fake.orca = () => ({ stdout: JSON.stringify({ ok: true, result: {} }) })
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.launchPicard', {}), { terminalId: null, visible: true })
  const args = agentCalls(fake)[0].args
  assert.ok(!args.includes('--model'))
  assert.equal(args[args.indexOf('--prompt') + 1], '$starcode:engajar')
  await worker.deactivate()
})

test('atalho não repete o Picard quando o CLI estoura o tempo', async () => {
  const fake = install()
  fake.python = withFeature(FILES)
  fake.orca = () => Object.assign(new Error('Command failed'), { killed: true, signal: 'SIGTERM' })
  const host = launchHost()
  const worker = await mount(host)
  await assert.rejects(worker.request('ponte.launchPicard', {}), /launch_timeout|não respondeu a tempo/)
  assert.equal(host.callsOf('agent.launch').length, 0)
  const st: any = await worker.request('ponte.state', {})
  assert.match(st.log.map((e: any) => e.text).join('|'), /orca agent launch falhou/)
  await worker.deactivate()
})

test('atalho cai no agent.launch quando o CLI falha', async () => {
  const fake = install()
  fake.python = withFeature(FILES)
  fake.orca = () => ({ stdout: JSON.stringify({ ok: false, error: { code: 'runtime_unavailable', message: 'sem runtime' } }) })
  const host = launchHost()
  const worker = await mount(host)
  assert.deepEqual(await worker.request('ponte.launchPicard', {}), { terminalId: 'term-1', visible: false })
  assert.equal(host.callsOf('agent.launch').length, 1)
  const st: any = await worker.request('ponte.state', {})
  const t = st.log.map((e: any) => e.text).join('|')
  assert.match(t, /orca agent launch falhou: runtime_unavailable/)
  assert.match(t, /Picard iniciado em segundo plano/)
  await worker.deactivate()
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
  assert.equal(s1.issueNote, 'Linear indisponível pelo CLI')
  assert.match(logs(s1), /orca worktree show.*orca fora do ar/)
  await w1.deactivate()

  // JSON inválido do CLI → "Linear indisponível" e log
  const f2 = install()
  f2.worktree = () => ({ stdout: 'não é json' })
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.equal(s2.issueNote, 'Linear indisponível pelo CLI')
  assert.match(logs(s2), /orca worktree show/)
  await w2.deactivate()

  // vínculo nulo não é falha: "Sem issue vinculada" e nada no log
  const f3 = install()
  f3.worktree = () => ({ stdout: WORKTREE_SEM })
  f3.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { feature: { ...(snapshot(p).feature as object), linear: [] } })) })
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
  assert.equal(s4.issueNote, 'Linear indisponível pelo CLI')
  assert.ok(f4.worktrees().length >= 1)
  await w4.deactivate()

  // editor.open e agent.launch falham → linha no log e erro devolvido ao painel
  const f5 = install()
  cliDown(f5)
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

const DIRTY_ENV = {
  NODE_OPTIONS: '--segredo-node',
  NODE_PATH: 'C:/np',
  NODE_REPL_EXTERNAL_MODULE: 'x.js',
  ELECTRON_RUN_AS_NODE: '1',
  ORCA_NODE_OPTIONS: '--segredo-orca',
  ORCA_CLI_COMMAND: 'cmd',
  ORCA_USER_DATA_PATH: 'C:/ud',
}

async function withEnv<T>(vars: Record<string, string>, fn: () => Promise<T>): Promise<T> {
  const old: Record<string, string | undefined> = {}
  for (const k of Object.keys(vars)) {
    old[k] = process.env[k]
    process.env[k] = vars[k]
  }
  try {
    return await fn()
  } finally {
    for (const k of Object.keys(vars)) {
      if (old[k] === undefined) delete process.env[k]
      else process.env[k] = old[k]
    }
  }
}

test('falha de processo externo grava stderr e nomes de variáveis no orca.log', async () => {
  await withEnv(DIRTY_ENV, async () => {
    const fake = install()
    const stderr = Array.from({ length: 10 }, (_, i) => `linha ${i + 1}`).join('\n')
    fake.worktree = () => Object.assign(new Error('linha 1'), { code: 1, stderr })
    const worker = await mount(hostFor(CTX_A))
    const state: any = await worker.request('ponte.state', {})
    const logs = worker.logs.join('\n')
    assert.match(logs, /linha 1\b/)
    assert.match(logs, /linha 8\b/)
    assert.ok(!/linha 9\b/.test(logs))
    for (const k of Object.keys(DIRTY_ENV)) assert.ok(logs.includes(k), k)
    assert.ok(!logs.includes('--segredo-node'))
    assert.ok(!logs.includes('--segredo-orca'))
    const diary = state.log.map((e: any) => e.text).join('|')
    assert.ok(!diary.includes('linha 2'))
    assert.ok(!diary.includes('NODE_OPTIONS'))
    await worker.deactivate()
  })
})

test('orca roda com env limpo e python com o env herdado', async () => {
  await withEnv(DIRTY_ENV, async () => {
    const fake = install()
    const worker = await mount(hostFor(CTX_A))
    await worker.request('ponte.state', {})
    const orcaCalls = fake.calls.filter((c) => isOrca(c.cmd))
    assert.ok(orcaCalls.length >= 2)
    for (const c of orcaCalls) {
      assert.ok(c.env, 'env passado ao orca')
      for (const k of ['NODE_OPTIONS', 'NODE_PATH', 'NODE_REPL_EXTERNAL_MODULE', 'ELECTRON_RUN_AS_NODE', 'ORCA_NODE_OPTIONS', 'ORCA_CLI_COMMAND']) {
        assert.equal(c.env![k], undefined, k)
      }
      assert.equal(c.env!.ORCA_USER_DATA_PATH, 'C:/ud')
    }
    assert.equal(fake.snaps()[0].env?.NODE_OPTIONS, process.env.NODE_OPTIONS)
    assert.equal(fake.snaps()[0].env?.PYTHONDONTWRITEBYTECODE, '1')
    await worker.deactivate()
  })
})

test('diário não repete a mesma falha', async () => {
  const fake = install()
  let msg = 'orca fora do ar'
  fake.worktree = () => new Error(msg)
  const worker = await mount(hostFor(CTX_A))
  const count = (st: any) => st.log.filter((e: any) => /orca worktree show falhou/.test(e.text)).length
  let st: any
  for (let i = 0; i < 3; i++) st = await worker.request('ponte.state', { force: true })
  assert.equal(count(st), 1)
  msg = 'outra falha'
  st = await worker.request('ponte.state', { force: true })
  assert.equal(count(st), 2)
  fake.worktree = () => ({ stdout: WORKTREE_OK })
  st = await worker.request('ponte.state', { force: true })
  assert.equal(st.issue.id, 'SC-116')
  fake.worktree = () => new Error(msg)
  st = await worker.request('ponte.state', { force: true })
  assert.equal(count(st), 3)
  await worker.deactivate()
})

test('issue do snapshot sem CLI fica sem url', async () => {
  const fake = install()
  fake.worktree = () => new Error('orca fora do ar')
  const worker = await mount(hostFor(CTX_A))
  const st: any = await worker.request('ponte.state', {})
  assert.equal(st.issue.id, 'SC-17')
  assert.equal(st.issue.url, null)
  assert.equal(st.issueNote, 'Linear indisponível pelo CLI')
  await worker.deactivate()
})

async function withCliEnv<T>(vars: Record<string, string | undefined>, execPath: string, fn: () => Promise<T>): Promise<T> {
  const keys = ['ORCA_CLI_PATH', 'ORCA_CLI', 'ORCA_BIN', 'PATH', 'Path']
  const old: Record<string, string | undefined> = {}
  for (const k of keys) old[k] = process.env[k]
  const oldExec = process.execPath
  for (const k of keys) delete process.env[k]
  for (const [k, v] of Object.entries(vars)) if (v !== undefined) process.env[k] = v
  Object.defineProperty(process, 'execPath', { value: execPath, configurable: true, writable: true })
  try {
    return await fn()
  } finally {
    Object.defineProperty(process, 'execPath', { value: oldExec, configurable: true, writable: true })
    for (const k of keys) {
      if (old[k] === undefined) delete process.env[k]
      else process.env[k] = old[k]
    }
  }
}

function fakeApp(): { dir: string; app: string } {
  const dir = mkdtempSync(join(tmpdir(), 'ponte-app-'))
  const app = join(dir, process.platform === 'win32' ? 'Orca.exe' : 'orca')
  writeFileSync(app, '')
  return { dir, app }
}

test('orca é resolvido em resources/bin e nunca pelo nome solto nem pelo Orca.exe', async () => {
  const { dir, app } = fakeApp()
  mkdirSync(join(dir, 'resources', 'bin'), { recursive: true })
  const cli = join(dir, 'resources', 'bin', EXE)
  writeFileSync(cli, '')
  const fake = install()
  await withCliEnv({ PATH: dir }, app, async () => {
    const worker = await mount(hostFor(CTX_A))
    const state: any = await worker.request('ponte.state', {})
    assert.equal(state.issue.id, 'SC-116')
    const orcaCalls = fake.calls.filter((c) => c.args[0] === 'worktree' || c.args[0] === 'linear')
    assert.ok(orcaCalls.length >= 2)
    for (const c of orcaCalls) {
      assert.equal(c.cmd, cli)
      assert.notEqual(c.cmd, 'orca')
      assert.notEqual(c.cmd.toLowerCase(), app.toLowerCase())
    }
    await worker.deactivate()
  })
})

test('orca cai no PATH quando não há caminho explícito', async () => {
  const { app } = fakeApp()
  const pathDir = mkdtempSync(join(tmpdir(), 'ponte-path-'))
  const cli = join(pathDir, EXE)
  writeFileSync(cli, '')
  const vazio = mkdtempSync(join(tmpdir(), 'ponte-vazio-'))
  const fake = install()
  await withCliEnv({ PATH: [vazio, pathDir].join(process.platform === 'win32' ? ';' : ':') }, app, async () => {
    const worker = await mount(hostFor(CTX_A))
    const state: any = await worker.request('ponte.state', {})
    assert.equal(state.issue.id, 'SC-116')
    const wts = fake.worktrees()
    assert.ok(wts.length >= 1)
    assert.ok(wts.every((c) => c.cmd === cli))
    await worker.deactivate()
  })
})

test('orca nunca executa o próprio executável do processo', async () => {
  const { dir, app } = fakeApp()
  const fake = install()
  await withCliEnv({ ORCA_CLI_PATH: app.toUpperCase(), PATH: dir }, app, async () => {
    const worker = await mount(hostFor(CTX_A))
    const state: any = await worker.request('ponte.state', {})
    assert.equal(state.issueNote, 'Linear indisponível pelo CLI')
    assert.equal(fake.worktrees().length, 0)
    assert.ok(!fake.calls.some((c) => c.cmd === 'orca' || c.cmd.toLowerCase() === app.toLowerCase()))
    await worker.deactivate()
  })
})

const RUNTIME_DOWN = JSON.stringify({
  ok: false,
  error: { code: 'runtime_unavailable', message: 'APPDATA is not set, so the Orca runtime metadata path cannot be resolved.' },
})

async function withoutEnv<T>(names: string[], fn: () => Promise<T>): Promise<T> {
  const old: Record<string, string | undefined> = {}
  for (const k of names) {
    old[k] = process.env[k]
    delete process.env[k]
  }
  try {
    return await fn()
  } finally {
    for (const k of names) if (old[k] !== undefined) process.env[k] = old[k]
  }
}

test('falha do CLI com JSON ok:false usa code e message', async () => {
  const fake = install()
  fake.worktree = () => Object.assign(new Error('Command failed: orca.exe worktree show'), { code: 1, stderr: '', stdout: RUNTIME_DOWN })
  const worker = await mount(hostFor(CTX_A))
  const st: any = await worker.request('ponte.state', {})
  const diary = st.log.map((e: any) => e.text).join('|')
  assert.match(diary, /orca worktree show falhou: runtime_unavailable: APPDATA is not set/)
  assert.ok(!diary.includes('Command failed'))
  const logs = worker.logs.join('\n')
  assert.match(logs, /runtime_unavailable: APPDATA is not set/)
  await worker.deactivate()

  const zero = install()
  zero.worktree = () => ({ stdout: RUNTIME_DOWN })
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.match(s2.log.map((e: any) => e.text).join('|'), /runtime_unavailable: APPDATA is not set/)
  await w2.deactivate()
})

test('orca.log lista quais variáveis de base estão definidas, sem valores', async () => {
  await withEnv({ APPDATA: 'C:/segredo-appdata', HOMEPATH: '\\segredo-home' }, async () => {
    await withoutEnv(['LOCALAPPDATA'], async () => {
      const fake = install()
      fake.worktree = () => Object.assign(new Error('falhou'), { code: 1, stderr: '' })
      const worker = await mount(hostFor(CTX_A))
      await worker.request('ponte.state', {})
      const logs = worker.logs.join('\n')
      const base = /base: ([^·]*)/.exec(logs)?.[1] ?? ''
      assert.match(base, /\bAPPDATA\b/)
      assert.match(base, /\bHOMEPATH\b/)
      assert.ok(!/\bLOCALAPPDATA\b/.test(base))
      assert.ok(!logs.includes('segredo-appdata'))
      assert.ok(!logs.includes('segredo-home'))
      await worker.deactivate()
    })
  })
})

test('env do CLI ganha as pastas do usuário quando faltam, sem sobrescrever', async () => {
  const win = process.platform === 'win32'
  const names = win ? ['APPDATA', 'LOCALAPPDATA', 'USERPROFILE'] : ['HOME']
  await withoutEnv(names, async () => {
    const home = homedir()
    const fake = install()
    const worker = await mount(hostFor(CTX_A))
    await worker.request('ponte.state', {})
    const env = fake.worktrees()[0].env!
    if (win) {
      assert.equal(env.USERPROFILE, home)
      assert.equal(env.APPDATA, join(home, 'AppData', 'Roaming'))
      assert.equal(env.LOCALAPPDATA, join(home, 'AppData', 'Local'))
    } else {
      assert.equal(env.HOME, home)
    }
    await worker.deactivate()
  })
  const custom = win ? { APPDATA: 'X:/meu-appdata' } : { HOME: '/meu-home' }
  await withEnv(custom, async () => {
    const fake = install()
    const worker = await mount(hostFor(CTX_A))
    await worker.request('ponte.state', {})
    const env = fake.worktrees()[0].env!
    for (const [k, v] of Object.entries(custom)) assert.equal(env[k], v)
    await worker.deactivate()
  })
})

test('worktree sem vínculo consulta a issue do snapshot', async () => {
  const fake = install()
  fake.worktree = () => ({ stdout: WORKTREE_SEM })
  fake.orca = () => ({
    stdout: JSON.stringify({
      ok: true,
      result: { issue: { identifier: 'SC-17', title: 'Fase 10', state: { name: 'In Progress' }, url: 'https://linear.app/ws/issue/SC-17/fase-10' } },
    }),
  })
  const worker = await mount(hostFor(CTX_A))
  const st: any = await worker.request('ponte.state', {})
  assert.equal(fake.linear().length, 1)
  assert.equal(fake.linear()[0].args[2], 'SC-17')
  assert.equal(st.issue.id, 'SC-17')
  assert.equal(st.issue.title, 'Fase 10')
  assert.equal(st.issue.state, 'In Progress')
  assert.equal(st.issue.url, 'https://linear.app/ws/issue/SC-17/fase-10')
  assert.equal(st.issueNote, null)
  await worker.deactivate()
})

test('url da issue montada só pelo urlKey do worktree quando a consulta falha', async () => {
  const fake = install()
  fake.worktree = () => ({
    stdout: JSON.stringify({ ok: true, result: { worktree: { linkedLinearIssue: 'SC-116', linkedLinearIssueOrganizationUrlKey: 'minha-org' } } }),
  })
  fake.orca = () => new Error('linear fora do ar')
  const worker = await mount(hostFor(CTX_A))
  const st: any = await worker.request('ponte.state', {})
  assert.equal(st.issue.id, 'SC-116')
  assert.equal(st.issue.url, 'https://linear.app/minha-org/issue/SC-116')
  assert.equal(st.issueNote, 'Linear indisponível pelo CLI')
  await worker.deactivate()

  const sem = install()
  sem.orca = () => new Error('linear fora do ar')
  const w2 = await mount(hostFor(CTX_A))
  const s2: any = await w2.request('ponte.state', {})
  assert.equal(s2.issue.url, null)
  await w2.deactivate()
})

const ELSEWHERE_SNAP = {
  ...(snapshot('x').feature as object),
  slug: 'ponte-missao-ativa', phase: 'execute', worktree: 'c:/WT/b', branch: 'feat/b', others: 0,
}

test('barra de status indica missão em outro worktree', async () => {
  const fake = install()
  const host = hostFor(CTX_A)
  const worker = await mount(host)
  const last = () => host.callsOf('statusBar.update').at(-1) as any
  fake.python = (p) => ({
    stdout: JSON.stringify(snapshot(p, { feature: { ...(snapshot(p).feature as object), done: true, phase: 'done' }, elsewhere: ELSEWHERE_SNAP })),
  })
  await worker.request('ponte.state', {})
  assert.equal(last().text, '🖖 ponte-missao-ativa · execute · outro worktree · modo 3')
  await worker.deactivate()
})

test('atalho foca o worktree da missão ativa', async () => {
  const fake = install()
  fake.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { elsewhere: ELSEWHERE_SNAP })) })
  const host = mockHost({
    results: {
      'workspace.readContext': CTX_A,
      'workspace.list': { workspaces: [WS_A, WS_B], truncated: false },
      'agents.list': { agents: [] },
      'statusBar.update': { ok: true },
      'workspace.open': { opened: true },
      'notifications.show': { delivered: true },
    },
  })
  const worker = await mount(host)
  // caminho do elsewhere ('c:/WT/b') casa com WS_B ('C:/wt/b') sem caixa
  const res: any = await worker.request('ponte.focusElsewhere', {})
  assert.equal(res.opened, true)
  assert.deepEqual(host.callsOf('workspace.open'), [{ workspaceId: 'ws-b' }])
  assert.equal(host.callsOf('notifications.show').length, 0)
  // barras invertidas também casam
  fake.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { elsewhere: { ...ELSEWHERE_SNAP, worktree: 'C:' + String.fromCharCode(92) + 'wt' + String.fromCharCode(92) + 'b' } })) })
  await worker.request('ponte.state', { force: true })
  await worker.request('ponte.focusElsewhere', {})
  assert.equal(host.callsOf('workspace.open').length, 2)
  // sem workspace casando: mensagem na resposta, sem notificação, sem workspace.open novo e sem erro
  fake.python = (p) => ({ stdout: JSON.stringify(snapshot(p, { elsewhere: { ...ELSEWHERE_SNAP, worktree: 'C:/wt/fora' } })) })
  await worker.request('ponte.state', { force: true })
  const miss: any = await worker.request('ponte.focusElsewhere', {})
  assert.equal(miss.opened, false)
  assert.equal(miss.message, 'worktree não aberto na Orca: C:/wt/fora')
  assert.equal(host.callsOf('workspace.open').length, 2)
  assert.equal(host.callsOf('notifications.show').length, 0)
  await worker.deactivate()
})
