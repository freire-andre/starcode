// Modelo da cena da Ponte: só dados, sem DOM e sem host. A pintura (canvas) lê este resultado.
import type { PonteAgent, PonteState, PonteWorker } from './protocol'

export type Divisao = 'comando' | 'operacoes' | 'ciencias'
export type Pose = 'sentado' | 'de-pe'

export interface Celula { x: number; y: number }
export interface Retangulo { x: number; y: number; largura: number; altura: number }

export interface Estacao extends Celula { membro: string }

export interface Personagem extends Celula {
  membro: string
  nome: string
  emoji: string
  divisao: Divisao
  cor: string
  pose: Pose
  /** Quadro da animação "trabalhando" (0 ou 1); 0 quando de pé. */
  quadro: 0 | 1
  balao: boolean
}

export interface WorkerCena extends Celula {
  rotulo: string
  concluido: boolean
  balao: boolean
}

export interface Cena {
  grade: { largura: number; altura: number }
  estacoes: Estacao[]
  turbolift: Retangulo
  engenharia: Retangulo
  personagens: Personagem[]
  workers: WorkerCena[]
  /** Quantidade de workers além dos 6 desenhados. */
  maisN: number
  vazia: boolean
  mensagem: string | null
}

export const GRADE = { largura: 64, altura: 40 } as const
export const MAX_WORKERS = 6
export const FRAME_MS = 250

export const MSG_SEM_WORKTREE = 'Nenhum worktree em foco'
export const MSG_SEM_STARCODE = 'StarCode não configurado neste worktree'

const TURBOLIFT: Retangulo = { x: 2, y: 28, largura: 8, altura: 10 }
const ENGENHARIA: Retangulo = { x: 42, y: 2, largura: 20, altura: 30 }

const CORES: Record<Divisao, string> = {
  comando: '#c0392b',
  operacoes: '#d4a017',
  ciencias: '#2e86c1',
}

interface Membro { id: string; nome: string; emoji: string; divisao: Divisao; x: number; y: number }

// Uma estação fixa por tripulante: Picard na cadeira central, Data e Troi ao lado,
// LaForge na engenharia, os demais nas laterais.
const TRIPULACAO: Membro[] = [
  { id: 'picard', nome: 'Picard', emoji: '🖖', divisao: 'comando', x: 32, y: 20 },
  { id: 'data', nome: 'Data', emoji: '🤖', divisao: 'operacoes', x: 28, y: 23 },
  { id: 'troi', nome: 'Troi', emoji: '💜', divisao: 'ciencias', x: 36, y: 23 },
  { id: 'laforge', nome: 'LaForge', emoji: '🔧', divisao: 'operacoes', x: 52, y: 26 },
  { id: 'spock', nome: 'Spock', emoji: '🖖', divisao: 'ciencias', x: 20, y: 14 },
  { id: 'mccoy', nome: 'McCoy', emoji: '🧪', divisao: 'ciencias', x: 20, y: 20 },
  { id: 'q', nome: 'Q', emoji: '✨', divisao: 'ciencias', x: 12, y: 17 },
  { id: 'uhura', nome: 'Uhura', emoji: '📡', divisao: 'operacoes', x: 24, y: 28 },
  { id: 'scotty', nome: 'Scotty', emoji: '⚙️', divisao: 'operacoes', x: 38, y: 29 },
  { id: 'kirk', nome: 'Kirk', emoji: '🚀', divisao: 'comando', x: 44, y: 20 },
  { id: 'worf', nome: 'Worf', emoji: '🛡️', divisao: 'comando', x: 32, y: 8 },
  { id: 'guinan', nome: 'Guinan', emoji: '🍸', divisao: 'ciencias', x: 10, y: 24 },
]

function casaWorker(agente: PonteAgent, worker: PonteWorker): boolean {
  const titulo = (agente.title ?? '').toLowerCase()
  if (!titulo) return false
  const chaves = [worker.label, ...worker.issues].filter(Boolean).map(c => c.toLowerCase())
  return chaves.some(c => titulo.includes(c))
}

function cenaVazia(mensagem: string): Cena {
  return {
    grade: { ...GRADE },
    estacoes: [],
    turbolift: { ...TURBOLIFT },
    engenharia: { ...ENGENHARIA },
    personagens: [],
    workers: [],
    maisN: 0,
    vazia: true,
    mensagem,
  }
}

/** Primeira linha não vazia do erro, como em R18. */
function primeiraLinha(texto: string | null): string {
  const linha = (texto ?? '').split(/\r?\n/).map(l => l.trim()).find(l => l.length > 0)
  return linha ?? 'Erro ao ler o estado'
}

/** Mensagem da cena vazia, ou null quando há o que desenhar. */
function mensagemDoEstado(estado: PonteState): string | null {
  if (estado.status === 'sem-worktree') return MSG_SEM_WORKTREE
  if (estado.status === 'erro' && !estado.snapshot) return primeiraLinha(estado.error)
  if (!estado.snapshot) return MSG_SEM_WORKTREE
  if (!estado.snapshot.starcode) return MSG_SEM_STARCODE
  return null
}

export function buildScene(estado: PonteState, agentes: PonteAgent[], agoraMs: number): Cena {
  const mensagem = mensagemDoEstado(estado)
  if (mensagem !== null || !estado.snapshot) return cenaVazia(mensagem ?? MSG_SEM_WORKTREE)

  const snap = estado.snapshot
  const quadro = (Math.floor(agoraMs / FRAME_MS) % 2) as 0 | 1
  const porMembro = new Map(snap.crew.map(c => [c.member, c]))
  const turboliftX = TURBOLIFT.x + 2

  // Workers da engenharia: até 6, grade de 3 colunas.
  const visiveis = snap.workers.slice(0, MAX_WORKERS)
  const workers: WorkerCena[] = visiveis.map((w, i) => ({
    rotulo: w.label,
    x: ENGENHARIA.x + 4 + (i % 3) * 6,
    y: ENGENHARIA.y + 5 + Math.floor(i / 3) * 8,
    concluido: agentes.some(a => a.state === 'done' && casaWorker(a, w)),
    balao: false,
  }))

  const balaoMembros = new Set<string>()
  for (const agente of agentes) {
    if (agente.state !== 'blocked' && agente.state !== 'waiting') continue
    const i = visiveis.findIndex(w => casaWorker(agente, w))
    if (i >= 0) {
      workers[i].balao = true
      continue
    }
    if (snap.workers.some(w => casaWorker(agente, w))) {
      balaoMembros.add('laforge') // worker fora dos 6 desenhados: o balão vai ao LaForge
      continue
    }
    let alvo = 'picard'
    let maisRecente = -Infinity
    for (const c of snap.crew) {
      if (c.count <= 0 || !c.lastAt) continue
      const t = Date.parse(c.lastAt)
      if (Number.isFinite(t) && t > maisRecente) {
        maisRecente = t
        alvo = c.member
      }
    }
    balaoMembros.add(alvo)
  }

  const personagens: Personagem[] = TRIPULACAO.map(m => {
    const c = porMembro.get(m.id)
    const ativo = (c?.count ?? 0) > 0
    return {
      membro: m.id,
      nome: c?.name || m.nome,
      emoji: c?.emoji || m.emoji,
      divisao: m.divisao,
      cor: CORES[m.divisao],
      pose: ativo ? 'sentado' : 'de-pe',
      quadro: ativo ? quadro : 0,
      x: ativo ? m.x : turboliftX,
      y: ativo ? m.y : TURBOLIFT.y + 4,
      balao: balaoMembros.has(m.id),
    }
  })

  return {
    grade: { ...GRADE },
    estacoes: TRIPULACAO.map(m => ({ membro: m.id, x: m.x, y: m.y })),
    turbolift: { ...TURBOLIFT },
    engenharia: { ...ENGENHARIA },
    personagens,
    workers,
    maisN: Math.max(0, snap.workers.length - MAX_WORKERS),
    vazia: false,
    mensagem: null,
  }
}
