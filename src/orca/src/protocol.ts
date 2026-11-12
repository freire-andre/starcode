// Contrato painel <-> worker da Ponte: o painel e o worker leem este arquivo.
export {}

/** Item da tripulação, como sai do `ponte.py snapshot`. */
export interface PonteCrew {
  member: string
  emoji: string
  name: string
  count: number
  lastAt: string | null
  cliModel: string | null
}

export interface PonteFeature {
  slug: string
  phase: string
  size: string | null
  done: boolean
  linear: string[]
  integrationBranch: string | null
  progress: { done: number; total: number; percent: number }
  breaker: 'open' | 'closed'
  files: {
    context: string | null
    spec: string | null
    tasks: string | null
    handoff: string | null
  }
}

/** Missão ativa de outro worktree do mesmo repositório (só quando a feature local está done ou ausente). */
export interface PonteElsewhere extends PonteFeature {
  worktree: string
  branch: string | null
  others: number
}

export interface PonteWorker {
  label: string
  issues: string[]
  base: string | null
  dispatch: string | null
  model: string | null
}

/** Saída de `ponte.py snapshot --json` (schemaVersion 1). */
export interface PonteSnapshot {
  schemaVersion: 1
  worktree: string
  starcode: boolean
  crew: PonteCrew[]
  gitMode: { mode: number; label: string; recordedAt: string | null } | null
  feature: PonteFeature | null
  workers: PonteWorker[]
  errors: { source: string; message: string }[]
  /** Opcional: ausente ou null quando não há missão ativa em outro worktree. */
  elsewhere?: PonteElsewhere | null
}

export interface PonteIssue {
  id: string
  title: string | null
  state: string | null
  url: string | null
}

export interface PonteAgent {
  terminalId: string | null
  title: string | null
  agent: string | null
  state: 'working' | 'blocked' | 'waiting' | 'done'
  stateStartedAt: number
}

/** Estado enviado ao painel. */
export interface PonteState {
  status: 'ok' | 'sem-worktree' | 'erro'
  stale: boolean
  updatedAt: number
  snapshot: PonteSnapshot | null
  issue: PonteIssue | null
  issueNote: string | null
  agents: PonteAgent[]
  log: { at: number; text: string }[]
  error: string | null
}

declare module 'orca' {
  interface PluginRequests {
    /** Estado atual; `force` ignora o cache do Linear. */
    'ponte.state': { input: { force?: boolean }; output: PonteState }
    /** Abre um arquivo da feature numa aba do editor (T4). */
    'ponte.open': { input: { file: 'spec' | 'tasks' | 'handoff' }; output: { opened: boolean } }
    /** Inicia o agente do Picard no worktree em foco; `visible` diz se abriu numa aba visível (F10-15). */
    /** Foca o worktree da missão ativa de outro worktree (`workspace.open`); `opened` false quando a Orca não o tem. */
    'ponte.focusElsewhere': { input: Record<string, never>; output: { opened: boolean; message: string | null } }
    'ponte.launchPicard': { input: Record<string, never>; output: { terminalId: string | null; visible: boolean } }
  }
  interface PluginPanelEvents {
    /** Estado completo, publicado a cada mudança. */
    'ponte.state': PonteState
  }
}
