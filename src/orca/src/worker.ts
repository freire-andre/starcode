// Worker da Ponte do StarCode: acha o worktree em foco, roda o ponte.py e o Linear,
// publica o estado aos painéis e atualiza a barra de status. Só lê; nunca escreve estado.
import { execFile } from 'node:child_process'
import { existsSync, statSync } from 'node:fs'
import { homedir } from 'node:os'
import { delimiter, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { OrcaWorkerApi } from 'orca/worker'
import type { PonteAgent, PonteIssue, PonteSnapshot, PonteState } from './protocol'

const DEBOUNCE_MS = 300
const TIMEOUT_MS = 10_000
const ISSUE_TTL_MS = 60_000
// Reconciliação sem evento: o estado nunca fica mais de 30 s sem ser conferido.
const RECONCILE_MS = 30_000
const LOG_MAX = 20
const LAUNCHABLE = ['claude', 'codex', 'antigravity', 'opencode']
const STATE_PT: Record<string, string> = {
  working: 'trabalhando', blocked: 'bloqueado', waiting: 'aguardando', done: 'concluído',
}

type ExecResult = { stdout: string }
type ExecOpts = { cwd?: string; timeout: number; env?: Record<string, string | undefined> }
type Exec = (cmd: string, args: string[], opts: ExecOpts) => Promise<ExecResult>
type ExecError = Error & { code?: unknown; stdout?: string; stderr?: string }

const STDERR_LINES = 8
// Variáveis que o launcher nativo do orca.exe lê e que o worker do plugin herda do Electron.
const ORCA_ENV_DROP = [
  'NODE_OPTIONS', 'NODE_PATH', 'NODE_REPL_EXTERNAL_MODULE', 'ELECTRON_RUN_AS_NODE', 'ORCA_NODE_OPTIONS', 'ORCA_CLI_COMMAND',
]

const realExec: Exec = (cmd, args, opts) =>
  new Promise((resolveExec, reject) => {
    execFile(
      cmd,
      args,
      { cwd: opts.cwd, env: opts.env, timeout: opts.timeout, windowsHide: true, maxBuffer: 8 * 1024 * 1024, encoding: 'utf8' },
      (err, stdout, stderr) => {
        if (err) {
          const e = err as ExecError
          e.stdout = String(stdout ?? '')
          e.stderr = String(stderr ?? '')
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

/** Env do processo sem as variáveis que quebram o launcher do orca.exe. */
const BASE_ENV = ['APPDATA', 'LOCALAPPDATA', 'USERPROFILE', 'HOME', 'HOMEDRIVE', 'HOMEPATH', 'SYSTEMROOT', 'PATH']

/** Valor de uma variável sem diferenciar maiúsculas no nome (no Windows o env copiado não ignora a caixa). */
function envKey(env: Record<string, string | undefined>, name: string): string | undefined {
  return Object.keys(env).find((k) => k.toUpperCase() === name && env[k] !== undefined && env[k] !== '')
}

/**
 * Env do CLI: sem as variáveis que quebram o launcher do orca.exe e com as pastas do usuário que o
 * runtime da Orca exige (APPDATA etc.) preenchidas pelo homedir quando faltam. Nunca sobrescreve.
 */
function orcaEnv(): Record<string, string | undefined> {
  const env: Record<string, string | undefined> = { ...process.env }
  for (const k of Object.keys(env)) if (ORCA_ENV_DROP.includes(k.toUpperCase())) delete env[k]
  let home = ''
  try {
    home = homedir()
  } catch {
    /* sem home */
  }
  if (home) {
    const fill: Record<string, string> =
      process.platform === 'win32'
        ? { USERPROFILE: home, APPDATA: join(home, 'AppData', 'Roaming'), LOCALAPPDATA: join(home, 'AppData', 'Local') }
        : { HOME: home }
    for (const [k, v] of Object.entries(fill)) if (!envKey(env, k)) env[k] = v
  }
  return env
}

/** `code: message` de um stdout `{ok:false,error:{code,message}}` do CLI; null se não for isso. */
function cliFailure(stdout: unknown): string | null {
  if (typeof stdout !== 'string' || !stdout.trim()) return null
  try {
    const json = JSON.parse(stdout) as { ok?: unknown; error?: { code?: unknown; message?: unknown } }
    if (json?.ok !== false || !json.error) return null
    const parts = [json.error.code, json.error.message].filter((x) => typeof x === 'string' && x)
    return parts.length ? parts.join(': ') : null
  } catch {
    return null
  }
}

/** Diagnóstico para o orca.log: até 8 linhas do stderr e só os NOMES das variáveis NODE_/ELECTRON_/ORCA_. */
function diagnostics(err: unknown): string | null {
  const e = err as ExecError
  if (!e || typeof e !== 'object' || typeof e.stderr !== 'string') return null
  const lines = String(e.stderr ?? '').split(/\r?\n/).filter((l) => l.trim()).slice(0, STDERR_LINES)
  const names = Object.keys(process.env).filter((k) => /^(NODE_|ELECTRON_|ORCA_)/i.test(k)).sort()
  const env = process.env as Record<string, string | undefined>
  const base = BASE_ENV.filter((k) => envKey(env, k))
  return `stderr: ${lines.length ? lines.join(' | ') : '(vazio)'} · env: ${names.join(', ') || '(nenhuma)'} · base: ${base.join(', ') || '(nenhuma)'}`
}

// O ponte.py recusa o worktree com JSON `{error}` no stdout e exit 2; essa mensagem vale mais que o stderr.
function stdoutError(err: unknown): Error | null {
  const out = (err as { stdout?: unknown })?.stdout
  if (typeof out !== 'string' || !out.trim()) return null
  try {
    const msg = (JSON.parse(out) as { error?: unknown })?.error
    return typeof msg === 'string' && msg ? new Error(msg) : null
  } catch {
    return null
  }
}

async function runSnapshot(path: string): Promise<PonteSnapshot> {
  const exec = getExec()
  const args = ['-B', ponteScript(), 'snapshot', '--path', path, '--json']
  let out: ExecResult | undefined
  let lastErr: unknown
  for (const py of ['python', 'python3']) {
    try {
      out = await exec(py, args, { timeout: TIMEOUT_MS, env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } })
      break
    } catch (err) {
      lastErr = err
      if ((err as { code?: unknown }).code !== 'ENOENT') throw stdoutError(err) ?? err
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

const samePath = (a: string, b: string) => resolve(a).replace(/\\/g, '/').toLowerCase() === resolve(b).replace(/\\/g, '/').toLowerCase()

function isFile(p: string): boolean {
  try {
    return existsSync(p) && statSync(p).isFile()
  } catch {
    return false
  }
}

/**
 * Caminhos explícitos do CLI, em ordem: variáveis da Orca, `resources/bin` e `bin` ao lado do executável,
 * e o PATH procurado à mão. Nunca o nome solto `orca`: no Windows o CreateProcess olha primeiro a pasta
 * do executável e acharia o Orca.exe (o app). Nunca o próprio process.execPath.
 */
function orcaCandidates(): string[] {
  const exe = process.platform === 'win32' ? 'orca.exe' : 'orca'
  const raw: string[] = []
  for (const k of ['ORCA_CLI_PATH', 'ORCA_CLI', 'ORCA_BIN']) {
    const v = process.env[k]
    if (v) raw.push(v)
  }
  let self = ''
  try {
    self = process.execPath
    const dir = dirname(self)
    raw.push(join(dir, 'resources', 'bin', exe), join(dir, 'bin', exe))
  } catch {
    /* sem execPath */
  }
  for (const dir of (process.env.PATH ?? process.env.Path ?? '').split(delimiter)) {
    if (dir.trim()) raw.push(join(dir.trim().replace(/^"|"$/g, ''), exe))
  }
  const out: string[] = []
  for (const p of raw) {
    if (self && samePath(p, self)) continue
    if (out.some((o) => samePath(o, p))) continue
    if (isFile(p)) out.push(p)
  }
  return out
}

/** Roda o CLI do `orca` por caminho explícito e com env limpo; ENOENT passa ao próximo candidato. */
async function execOrca(args: string[]): Promise<ExecResult> {
  const exec = getExec()
  const opts: ExecOpts = { timeout: TIMEOUT_MS, env: orcaEnv() }
  let last: unknown = Object.assign(new Error('CLI do orca não encontrado'), { code: 'ENOENT' })
  for (const bin of orcaCandidates()) {
    let out: ExecResult
    try {
      out = await exec(bin, args, opts)
    } catch (e) {
      last = e
      if ((e as { code?: unknown }).code !== 'ENOENT') {
        const why = cliFailure((e as ExecError).stdout)
        if (why) (e as ExecError).message = why
        throw e
      }
      continue
    }
    const why = cliFailure(out.stdout)
    if (why) throw new Error(why)
    return out
  }
  throw last
}

/** Caminho do arquivo relativo à raiz do worktree, com `/`; null quando está fora dela. */
function relativeToWorktree(file: string, root: string): string | null {
  const norm = (p: string) => p.replace(/\\/g, '/').replace(/\/+$/, '').replace(/^([A-Za-z]):/, (_, d: string) => `${d.toLowerCase()}:`)
  const f = norm(file)
  const r = norm(root)
  const absolute = /^[a-z]:\//.test(f) || f.startsWith('/')
  let rel: string
  if (!absolute) rel = f.replace(/^\.\//, '')
  else if (f.toLowerCase().startsWith(`${r.toLowerCase()}/`)) rel = f.slice(r.length + 1)
  else return null
  return rel && !rel.split('/').includes('..') ? rel : null
}

/** Erro de tempo do execFile: processo morto, sinal ou ETIMEDOUT. */
function isTimeout(err: unknown): boolean {
  const e = err as { killed?: unknown; signal?: unknown; code?: unknown } | null
  return !!e && (e.killed === true || !!e.signal || e.code === 'ETIMEDOUT')
}

/** Modelo real do `cliModel` ("claude · opus"); vazio quando é o padrão do CLI. */
function realModel(cliModel: string | null | undefined): string | null {
  const m = (cliModel ?? '').split('·')[1]?.trim() ?? ''
  return m && !/^padr[aã]o/i.test(m) ? m : null
}

/** Handle/ID do terminal no JSON do `orca agent launch`; null quando não vier. */
function terminalOf(json: unknown): string | null {
  const r = (json as { result?: Record<string, any> } | null)?.result
  const cands = [r?.terminal?.handle, r?.terminalHandle, r?.terminalId, r?.handle, r?.terminal?.id]
  const hit = cands.find((x) => typeof x === 'string' && x)
  return typeof hit === 'string' ? hit : null
}

type IssueResult = { issue: PonteIssue | null; note: string | null }

const CLI_DOWN = 'Linear indisponível pelo CLI'

/** URL montada pelo urlKey da organização que o próprio worktree show devolve; é a única montagem permitida. */
function urlFromKey(key: unknown, id: string): string | null {
  if (typeof key !== 'string' || !/^[A-Za-z0-9_-]+$/.test(key) || !/^[A-Za-z0-9]+-\d+$/.test(id)) return null
  return `https://linear.app/${key}/issue/${id}`
}

async function queryIssue(
  path: string,
  snapId: string | null,
  fail: (action: string, err: unknown) => void,
  ok: (action: string) => void,
): Promise<IssueResult> {
  let action = 'orca worktree show'
  let id: string | null = null
  let urlKey: unknown = null
  try {
    // O worker não é o terminal do worktree: `--current` não serve. Lê o vínculo do worktree e consulta a issue pelo ID.
    const wt = await execOrca(['worktree', 'show', '--worktree', `path:${path}`, '--json'])
    const worktree = JSON.parse(wt.stdout)?.result?.worktree
    if (!worktree || typeof worktree !== 'object') throw new Error('resposta sem worktree')
    ok(action)
    urlKey = worktree.linkedLinearIssueOrganizationUrlKey
    const linked = typeof worktree.linkedLinearIssue === 'string' ? worktree.linkedLinearIssue.trim() : ''
    // Sem vínculo no worktree, a issue da feature (Handoff) também serve.
    id = linked || snapId
    if (!id) return { issue: null, note: 'Sem issue vinculada' }
    action = 'orca linear issue'
    const out = await execOrca(['linear', 'issue', id, '--json'])
    const json = JSON.parse(out.stdout)
    const issue = json?.result?.issue
    if (json?.ok && issue?.identifier) {
      ok(action)
      return {
        issue: {
          id: String(issue.identifier),
          title: issue.title ?? null,
          state: issue.state?.name ?? null,
          url: typeof issue.url === 'string' && issue.url.startsWith('https://linear.app/') ? issue.url : null,
        },
        note: null,
      }
    }
    throw new Error('resposta sem issue')
  } catch (err) {
    fail(action, err)
    const url = id ? urlFromKey(urlKey, id) : null
    return { issue: id && url ? { id, title: null, state: null, url } : null, note: CLI_DOWN }
  }
}

function statusText(snap: PonteSnapshot): string {
  const mode = snap.gitMode ? ` · modo ${snap.gitMode.mode}` : ''
  if (snap.elsewhere) return `🖖 ${snap.elsewhere.slug} · ${snap.elsewhere.phase} · outro worktree${mode}`
  if (snap.feature) return `🖖 ${snap.feature.slug} · ${snap.feature.phase}${mode}`
  return `🖖 StarCode${mode}`
}

type FocusCtx = { branch: string; displayName?: string | null }
type FocusWs = { id: string; kind: string; name?: string; path: string; branch: string | null }

const shortRef = (b: string | null | undefined) => (b ?? '').replace(/^refs\/heads\//, '')

// Resolve o worktree em foco: mesmo ramo; com vários no ramo, o de name igual ao displayName.
function pickFocus(ctx: FocusCtx, workspaces: FocusWs[]): { id: string; path: string } | null {
  const branch = shortRef(ctx.branch)
  const same = workspaces.filter((w) => w.kind === 'worktree' && shortRef(w.branch) === branch)
  const w = same.length === 1 ? same[0] : same.find((x) => x.name === ctx.displayName)
  return w ? { id: w.id, path: w.path } : null
}

let stopReconcile: (() => void) | null = null

/** Para a reconciliação periódica; o host chama antes de parar o worker. */
export function deactivate(): void {
  stopReconcile?.()
  stopReconcile = null
}

export default function activate(orca: OrcaWorkerApi): void {
  stopReconcile?.()
  const issueCache = new Map<string, { at: number; result: IssueResult }>()
  let seq = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  let lastGood: PonteState | null = null
  // Última consulta iniciada: uma resposta superada devolve esta, nunca o próprio resultado.
  let current: Promise<PonteState> | null = null
  let inflight = 0
  const log: { at: number; text: string }[] = []
  let launching = false
  // Última falha registrada no diário por ação: a mesma mensagem não se repete até mudar ou haver sucesso.
  const lastFail = new Map<string, string>()
  let seen: { path: string; name: string; phase: string | null; agents: Map<string, string> } | null = null

  const note = (text: string) => {
    log.push({ at: Date.now(), text })
    if (log.length > LOG_MAX) log.shift()
  }

  /** Falha de processo externo ou de chamada ao host: uma linha no diário (sem repetir) e o diagnóstico no orca.log. */
  const fail = (action: string, err: unknown) => {
    const msg = firstLine(err)
    const text = `${action} falhou: ${msg}`
    const diag = diagnostics(err)
    if (diag) orca.log(`${text} · ${diag}`)
    if (lastFail.get(action) === msg) return
    lastFail.set(action, msg)
    note(text)
    console.log(`[starcode-ponte] ${text}`)
  }
  const ok = (action: string) => {
    lastFail.delete(action)
  }

  /** Acrescenta ao diário o que mudou desde o último estado bom. */
  function track(path: string, snap: PonteSnapshot, agents: PonteAgent[]): void {
    const name = path.split(/[\\/]/).filter(Boolean).pop() ?? path
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
    const ctx = (await orca.host.call('workspace.readContext', {})) as FocusCtx | null
    if (!ctx) return null
    const list = (await orca.host.call('workspace.list', {})) as { workspaces: FocusWs[] }
    return pickFocus(ctx, list.workspaces)
  }

  /** Agentes do host; null quando a consulta falha (o estado anterior vale, em vez de esvaziar a cena). */
  async function listAgents(workspaceId: string): Promise<PonteAgent[] | { failed: string }> {
    try {
      // escopo explícito: só os agentes do worktree em foco provam que a sessão está nele (R21)
      const res = (await orca.host.call('agents.list', { workspaceId })) as { agents?: PonteAgent[] }
      return res?.agents ?? []
    } catch (err) {
      orca.log(`agents.list falhou: ${firstLine(err)}`)
      return { failed: firstLine(err) }
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
    const snapId = snap.feature?.linear?.[0] ?? null
    const key = `${path}|${snapId ?? ''}`
    let entry = issueCache.get(key)
    if (!entry || force || Date.now() - entry.at >= ISSUE_TTL_MS) {
      entry = { at: Date.now(), result: await queryIssue(path, snapId, (a, e) => fail(a, e), ok) }
      issueCache.set(key, entry)
    }
    const { issue, note: why } = entry.result
    if (issue) return { issue, note: issue.title ? null : why }
    return { issue: snapId ? { id: snapId, title: null, state: null, url: null } : null, note: why }
  }

  function refresh(force = false): Promise<PonteState> {
    inflight++
    const p = run(force).finally(() => {
      inflight--
    })
    current = p
    return p
  }

  async function run(force: boolean): Promise<PonteState> {
    const mine = ++seq
    const stale = () => mine !== seq
    const now = Date.now()
    const base = { updatedAt: now }
    // Último estado bom do worktree em foco; o de outro worktree nunca serve de reserva.
    const goodFor = (path: string | null) =>
      lastGood && (path === null || lastGood.snapshot?.worktree === path) ? lastGood : null
    let state: PonteState
    try {
      const where = await focus()
      const path = where?.path ?? null
      if (!path) {
        state = {
          status: 'sem-worktree', stale: false, snapshot: null, issue: null,
          issueNote: null, agents: [], error: null, log: [], lastValidAt: now, ...base,
        }
      } else {
        try {
          const snap = await runSnapshot(path)
          ok('snapshot')
          const [issueRes, listed] = await Promise.all([
            snap.starcode ? issueFor(path, snap, force) : Promise.resolve<IssueResult>({ issue: null, note: null }),
            listAgents(where!.id),
          ])
          const degraded = Array.isArray(listed) ? null : listed.failed
          const agents = Array.isArray(listed) ? listed : (goodFor(path)?.agents ?? [])
          state = {
            status: 'ok', stale: degraded !== null, snapshot: snap, issue: issueRes.issue,
            issueNote: issueRes.note, agents, error: degraded === null ? null : `agents.list: ${degraded}`,
            agentsWorktree: degraded === null ? path : (goodFor(path)?.agentsWorktree ?? null),
            log: [], lastValidAt: degraded === null ? now : (goodFor(path)?.lastValidAt ?? null), ...base,
          }
          if (!stale()) {
            track(path, snap, agents)
            if (degraded === null) lastGood = state
          }
        } catch (err) {
          const msg = firstLine(err)
          fail('snapshot', err)
          const good = goodFor(path)
          state = {
            status: 'erro', stale: true, snapshot: good?.snapshot ?? null,
            issue: good?.issue ?? null, issueNote: good?.issueNote ?? null,
            agents: good?.agents ?? [], agentsWorktree: good?.agentsWorktree ?? null, error: msg, log: [], lastValidAt: good?.updatedAt ?? null, ...base,
          }
        }
      }
    } catch (err) {
      const msg = firstLine(err)
      state = {
        status: 'erro', stale: true, snapshot: lastGood?.snapshot ?? null,
        issue: lastGood?.issue ?? null, issueNote: lastGood?.issueNote ?? null,
        agents: lastGood?.agents ?? [], agentsWorktree: lastGood?.agentsWorktree ?? null, error: msg, log: [], lastValidAt: lastGood?.updatedAt ?? null, ...base,
      }
    }
    state.log = [...log]
    if (stale()) return current ?? state
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

  // Rede de segurança contra evento perdido; não acumula: com consulta em andamento o tick não faz nada.
  const reconcile = setInterval(() => {
    if (inflight > 0) return
    void refresh().catch((err) => orca.log(`reconciliação falhou: ${firstLine(err)}`))
  }, RECONCILE_MS)
  reconcile.unref?.()
  stopReconcile = () => clearInterval(reconcile)

  orca.panels.handle('ponte.state', async (input) => refresh(!!input?.force))
  async function currentSnapshot(path: string): Promise<PonteSnapshot> {
    const cached = lastGood?.snapshot
    return cached && cached.worktree === path ? cached : runSnapshot(path)
  }

  orca.panels.handle('ponte.open', async (input) => {
    const where = await focus()
    if (!where) throw Object.assign(new Error('Nenhum worktree em foco'), { code: 'no_worktree' })
    const snap = await runSnapshot(where.path)
    const file = snap.feature?.files?.[input.file] ?? null
    const rel = file ? relativeToWorktree(file, where.path) : null
    if (!rel) throw Object.assign(new Error('file_missing'), { code: 'file_missing' })
    try {
      await orca.host.call('editor.open', { workspaceId: where.id, path: rel })
    } catch (err) {
      fail('editor.open', err)
      schedule()
      throw err
    }
    return { opened: true }
  })

  orca.panels.handle('ponte.focusElsewhere', async () => {
    const where = await focus()
    if (!where) throw Object.assign(new Error('Nenhum worktree em foco'), { code: 'no_worktree' })
    const target = (await currentSnapshot(where.path)).elsewhere?.worktree
    if (!target) throw Object.assign(new Error('Sem missão em outro worktree'), { code: 'no_elsewhere' })
    const list = (await orca.host.call('workspace.list', {})) as { workspaces: FocusWs[] }
    const ws = list.workspaces.find((w) => samePath(w.path, target))
    if (ws) {
      try {
        await orca.host.call('workspace.open', { workspaceId: ws.id })
      } catch (err) {
        fail('workspace.open', err)
        schedule()
        throw err
      }
      return { opened: true, message: null }
    }
    // sem capacidade notifications:show (manifesto): o painel mostra a mensagem junto do atalho
    return { opened: false, message: `worktree não aberto na Orca: ${target}` }
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
      const model = realModel(picard?.cliModel)
      const args = [
        'agent', 'launch', '--agent', agent, '--worktree', `path:${where.path}`, '--prompt', prompt,
        '--surface', 'terminal', '--focus', ...(model ? ['--model', model] : []), '--json',
      ]
      try {
        const out = await execOrca(args)
        let json: unknown = null
        try {
          json = JSON.parse(out.stdout)
        } catch {
          /* resposta sem JSON: segue sem terminal */
        }
        const terminalId = terminalOf(json)
        ok('orca agent launch')
        note('Picard iniciado numa aba visível')
        console.log(`[starcode-ponte] orca agent launch: terminal ${terminalId ?? '(sem id)'}`)
        schedule()
        return { terminalId, visible: true }
      } catch (err) {
        fail('orca agent launch', err)
        // Timeout: o CLI pode já ter aberto o Picard; voltar à API abriria um segundo.
        if (isTimeout(err)) {
          schedule()
          throw Object.assign(
            new Error('O CLI da Orca não respondeu a tempo; confira se o Picard abriu antes de tentar de novo'),
            { code: 'launch_timeout' },
          )
        }
      }
      let res: { terminalId: string }
      try {
        res = (await orca.host.call('agent.launch', { workspaceId: where.id, agent, prompt })) as { terminalId: string }
      } catch (err) {
        fail('agent.launch', err)
        schedule()
        throw err
      }
      note('Picard iniciado em segundo plano')
      console.log(`[starcode-ponte] agent.launch: terminalId ${res.terminalId}`)
      schedule()
      return { terminalId: res.terminalId ?? null, visible: false }
    } finally {
      launching = false
    }
  })

  orca.commands.register('starcode-ponte.refresh', async () => {
    await refresh(true)
    return 'Ponte atualizada'
  })
}
