// Worker da Ponte do StarCode: acha o worktree em foco, roda o ponte.py e o Linear,
// publica o estado aos painéis e atualiza a barra de status. Só lê; nunca escreve estado.
import { execFile } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { OrcaWorkerApi } from 'orca/worker'
import type { PonteAgent, PonteIssue, PonteSnapshot, PonteState } from './protocol'

const DEBOUNCE_MS = 300
const TIMEOUT_MS = 10_000
const ISSUE_TTL_MS = 60_000
const LOG_MAX = 20
const LAUNCHABLE = ['claude', 'codex', 'antigravity', 'opencode']
const STATE_PT: Record<string, string> = {
  working: 'trabalhando', blocked: 'bloqueado', waiting: 'aguardando', done: 'concluído',
}

type ExecResult = { stdout: string }
type Exec = (cmd: string, args: string[], opts: { cwd?: string; timeout: number }) => Promise<ExecResult>

const realExec: Exec = (cmd, args, opts) =>
  new Promise((resolveExec, reject) => {
    execFile(
      cmd,
      args,
      { cwd: opts.cwd, timeout: opts.timeout, windowsHide: true, maxBuffer: 8 * 1024 * 1024, encoding: 'utf8' },
      (err, stdout, stderr) => {
        if (err) {
          const e = err as Error & { code?: unknown }
          const first = String(stderr || '').trim().split(/\r?\n/)[0]
          if (first && e.code !== 'ENOENT') e.message = first
          reject(e)
        } else resolveExec({ stdout: String(stdout) })
      },
    )
  })

// Só para testes: injeta um executor no lugar do processo filho.
function getExec(): Exec {
  return ((globalThis as { __ponteExec?: Exec }).__ponteExec ?? realExec) as Exec
}

function ponteScript(): string {
  let root = process.cwd()
  try {
    root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
  } catch {
    /* mantém o cwd */
  }
  const candidates = [resolve(root, 'scripts', 'ponte.py'), resolve(root, '..', '..', 'scripts', 'ponte.py')]
  return candidates.find((p) => existsSync(p)) ?? candidates[0]
}

function firstLine(err: unknown): string {
  const text = err instanceof Error ? err.message : String(err)
  return text.trim().split(/\r?\n/)[0] || 'erro desconhecido'
}

async function runSnapshot(path: string): Promise<PonteSnapshot> {
  const exec = getExec()
  const args = [ponteScript(), 'snapshot', '--path', path, '--json']
  let out: ExecResult | undefined
  let lastErr: unknown
  for (const py of ['python', 'python3']) {
    try {
      out = await exec(py, args, { timeout: TIMEOUT_MS })
      break
    } catch (err) {
      lastErr = err
      if ((err as { code?: unknown }).code !== 'ENOENT') throw err
    }
  }
  if (!out) throw lastErr ?? new Error('python não encontrado')
  let parsed: unknown
  try {
    parsed = JSON.parse(out.stdout)
  } catch {
    throw new Error('saída do ponte.py não é JSON')
  }
  const snap = parsed as PonteSnapshot & { error?: string }
  if (!snap || typeof snap !== 'object' || snap.error) throw new Error(snap?.error ?? 'snapshot inválido')
  return snap
}

type IssueResult = { issue: PonteIssue | null; note: string | null }

async function queryIssue(path: string): Promise<IssueResult> {
  try {
    const out = await getExec()('orca', ['linear', 'issue', '--current', '--json'], { cwd: path, timeout: TIMEOUT_MS })
    const json = JSON.parse(out.stdout)
    const issue = json?.result?.issue
    if (json?.ok && issue?.identifier) {
      return {
        issue: {
          id: String(issue.identifier),
          title: issue.title ?? null,
          state: issue.state?.name ?? null,
          url: issue.url ?? null,
        },
        note: null,
      }
    }
    return { issue: null, note: 'Sem issue vinculada' }
  } catch {
    return { issue: null, note: 'Linear indisponível' }
  }
}

function statusText(snap: PonteSnapshot): string {
  const mode = snap.gitMode ? ` · modo ${snap.gitMode.mode}` : ''
  if (snap.feature) return `🖖 ${snap.feature.slug} · ${snap.feature.phase}${mode}`
  return `🖖 StarCode${mode}`
}

export default function activate(orca: OrcaWorkerApi): void {
  const issueCache = new Map<string, { at: number; result: IssueResult }>()
  let seq = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  let lastGood: PonteState | null = null
  const log: { at: number; text: string }[] = []
  let launching = false
  let seen: { path: string; name: string; phase: string | null; agents: Map<string, string> } | null = null

  const note = (text: string) => {
    log.push({ at: Date.now(), text })
    if (log.length > LOG_MAX) log.shift()
  }

  /** Acrescenta ao diário o que mudou desde o último estado bom. */
  function track(path: string, snap: PonteSnapshot, agents: PonteAgent[]): void {
    const name = path.split(/[\/]/).filter(Boolean).pop() ?? path
    const phase = snap.feature?.phase ?? null
    const map = new Map<string, string>()
    agents.forEach((a, i) => map.set(a.terminalId ?? a.title ?? `#${i}`, a.state))
    if (seen) {
      if (seen.path !== path) note(`Worktree em foco: ${name}.`)
      else if (seen.phase !== phase && seen.phase && phase) note(`Fase: ${seen.phase} → ${phase}.`)
      if (seen.path === path) {
        agents.forEach((a, i) => {
          const key = a.terminalId ?? a.title ?? `#${i}`
          if (seen!.agents.get(key) !== a.state) {
            note(`Agente ${a.title ?? a.agent ?? key}: ${STATE_PT[a.state] ?? a.state}.`)
          }
        })
      }
    }
    seen = { path, name, phase, agents: map }
  }

  async function focus(): Promise<{ id: string; path: string } | null> {
    const ctx = (await orca.host.call('workspace.readContext', {})) as { branch: string } | null
    if (!ctx) return null
    const list = (await orca.host.call('workspace.list', {})) as {
      workspaces: { id: string; kind: string; path: string; branch: string | null }[]
    }
    const w = list.workspaces.find((x) => x.kind === 'worktree' && x.branch === ctx.branch)
    return w ? { id: w.id, path: w.path } : null
  }

  async function listAgents(): Promise<PonteAgent[]> {
    try {
      const res = (await orca.host.call('agents.list', {})) as { agents?: PonteAgent[] }
      return res?.agents ?? []
    } catch {
      return []
    }
  }

  async function updateBar(state: PonteState): Promise<void> {
    const snap = state.snapshot
    const visible = !!snap && snap.starcode && state.status !== 'sem-worktree'
    const params: Record<string, unknown> = { id: 'ponte', visible }
    if (snap && visible) {
      const blocked = state.agents.some((a) => a.state === 'blocked' || a.state === 'waiting')
      params.text = statusText(snap)
      params.tone = snap.feature?.breaker === 'open' || blocked ? 'warning' : 'neutral'
    }
    try {
      await orca.host.call('statusBar.update', params as never)
    } catch (err) {
      orca.log(`statusBar.update falhou: ${firstLine(err)}`)
    }
  }

  async function issueFor(path: string, snap: PonteSnapshot, force: boolean): Promise<IssueResult> {
    let entry = issueCache.get(path)
    if (!entry || force || Date.now() - entry.at >= ISSUE_TTL_MS) {
      entry = { at: Date.now(), result: await queryIssue(path) }
      issueCache.set(path, entry)
    }
    const { issue, note: why } = entry.result
    if (issue) return { issue, note: null }
    const id = snap.feature?.linear?.[0]
    return { issue: id ? { id, title: null, state: null, url: null } : null, note: why }
  }

  async function refresh(force = false): Promise<PonteState> {
    const mine = ++seq
    const stale = () => mine !== seq
    const now = Date.now()
    const base = { updatedAt: now }
    let state: PonteState
    try {
      const ctx = (await orca.host.call('workspace.readContext', {})) as { branch: string } | null
      let path: string | null = null
      if (ctx) {
        const list = (await orca.host.call('workspace.list', {})) as {
          workspaces: { kind: string; path: string; branch: string | null }[]
        }
        path = list.workspaces.find((w) => w.kind === 'worktree' && w.branch === ctx.branch)?.path ?? null
      }
      if (!path) {
        state = {
          status: 'sem-worktree', stale: false, snapshot: null, issue: null,
          issueNote: null, agents: [], error: null, log: [], ...base,
        }
      } else {
        try {
          const snap = await runSnapshot(path)
          const [issueRes, agents] = await Promise.all([
            snap.starcode ? issueFor(path, snap, force) : Promise.resolve<IssueResult>({ issue: null, note: null }),
            listAgents(),
          ])
          state = {
            status: 'ok', stale: false, snapshot: snap, issue: issueRes.issue,
            issueNote: issueRes.note, agents, error: null, log: [], ...base,
          }
          if (!stale()) track(path, snap, agents)
          lastGood = state
        } catch (err) {
          const msg = firstLine(err)
          note(`snapshot falhou: ${msg}`)
          state = {
            status: 'erro', stale: true, snapshot: lastGood?.snapshot ?? null,
            issue: lastGood?.issue ?? null, issueNote: lastGood?.issueNote ?? null,
            agents: lastGood?.agents ?? [], error: msg, log: [], ...base,
          }
        }
      }
    } catch (err) {
      const msg = firstLine(err)
      state = {
        status: 'erro', stale: true, snapshot: lastGood?.snapshot ?? null,
        issue: lastGood?.issue ?? null, issueNote: lastGood?.issueNote ?? null,
        agents: lastGood?.agents ?? [], error: msg, log: [], ...base,
      }
    }
    state.log = [...log]
    if (stale()) return state
    if (state.status === 'erro' && !state.snapshot) state.stale = false
    await updateBar(state.status === 'erro' && lastGood ? { ...lastGood, status: 'erro' } : state)
    if (!stale()) orca.panels.post('ponte.state', state)
    return state
  }

  function schedule(): void {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      void refresh().catch((err) => orca.log(`refresh falhou: ${firstLine(err)}`))
    }, DEBOUNCE_MS)
  }

  orca.events.on('workspace.changed', schedule)
  orca.events.on('agent.status.changed', schedule)

  orca.panels.handle('ponte.state', async (input) => refresh(!!input?.force))
  async function currentSnapshot(path: string): Promise<PonteSnapshot> {
    const cached = lastGood?.snapshot
    return cached && cached.worktree === path ? cached : runSnapshot(path)
  }

  orca.panels.handle('ponte.open', async (input) => {
    const where = await focus()
    if (!where) throw Object.assign(new Error('Nenhum worktree em foco'), { code: 'no_worktree' })
    const snap = await runSnapshot(where.path)
    const rel = snap.feature?.files?.[input.file] ?? null
    if (!rel) throw Object.assign(new Error('file_missing'), { code: 'file_missing' })
    await orca.host.call('editor.open', { workspaceId: where.id, path: rel })
    return { opened: true }
  })

  orca.panels.handle('ponte.launchPicard', async () => {
    if (launching) throw Object.assign(new Error('Picard já está sendo iniciado'), { code: 'busy' })
    launching = true
    try {
      const where = await focus()
      if (!where) throw Object.assign(new Error('Nenhum worktree em foco'), { code: 'no_worktree' })
      const snap = await currentSnapshot(where.path)
      const picard = snap.crew.find((c) => c.member === 'picard')
      const agent = (picard?.cliModel ?? 'claude').split('·')[0].trim().toLowerCase() || 'claude'
      if (!LAUNCHABLE.includes(agent)) {
        throw Object.assign(new Error(`Agente ${agent} não pode ser iniciado pela Orca`), { code: 'not_launchable' })
      }
      const prompt = agent === 'claude' ? '/starcode:engajar' : agent === 'codex' ? '$starcode:engajar' : 'engajar'
      const res = (await orca.host.call('agent.launch', { workspaceId: where.id, agent, prompt })) as {
        terminalId: string
      }
      return { terminalId: res.terminalId }
    } finally {
      launching = false
    }
  })

  orca.commands.register('starcode-ponte.refresh', async () => {
    await refresh(true)
    return 'Ponte atualizada'
  })
}
