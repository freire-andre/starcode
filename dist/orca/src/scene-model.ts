// Modelo da cena da Ponte: só dados, sem DOM e sem host. A pintura (canvas) lê este resultado.
import type { PonteAgent, PonteState, PonteWorker } from './protocol.ts'

export type Divisao = 'comando' | 'operacoes' | 'ciencias'
export type Pose = 'sentado' | 'de-pe'

export interface Celula { x: number; y: number }
export interface Retangulo { x: number; y: number; largura: number; altura: number }

export interface Estacao extends Celula { membro: string }

export type TipoRotulo = 'telao' | 'emoji' | 'nome' | 'worker' | 'marca' | 'balao' | 'legenda' | 'mensagem'

/** Texto da cena com a caixa que ele ocupa (centro em x,y); o teste prova que nenhuma caixa se sobrepõe. */
export interface Rotulo {
  tipo: TipoRotulo
  texto: string
  x: number
  y: number
  /** Altura da fonte em células da grade. */
  tam: number
  caixa: Retangulo
  /** Tripulante dono do texto (emoji, nome ou balão da estação), quando houver. */
  dono?: string
}

export interface Personagem extends Celula {
  membro: string
  nome: string
  emoji: string
  divisao: Divisao
  cor: string
  pose: Pose
  /** Trabalhando (count > 0): sentado, cores vivas, animado. */
  ativo: boolean
  /** Quadro da animação "trabalhando" (0 ou 1); 0 quando parado. */
  quadro: 0 | 1
  balao: boolean
  /** Ladrilho da estação (fundo; esmaecido quando inativo). */
  caixa: Retangulo
}

export interface WorkerCena extends Celula {
  rotulo: string
  concluido: boolean
  balao: boolean
  caixa: Retangulo
}

export interface Telao {
  slug: string
  fase: string
  feitos: number
  total: number
  percentual: number
  barra: Retangulo
}

export interface Cena {
  grade: { largura: number; altura: number }
  telao: Retangulo
  /** Dados do telão; null quando não há feature ativa. */
  progresso: Telao | null
  estacoes: Estacao[]
  engenharia: Retangulo
  /** As 6 vagas de worker da engenharia (ocupadas ou vazias). */
  vagas: Retangulo[]
  personagens: Personagem[]
  workers: WorkerCena[]
  rotulos: Rotulo[]
  /** Quantidade de workers além dos 6 desenhados. */
  maisN: number
  vazia: boolean
  mensagem: string | null
}

export const GRADE = { largura: 48, altura: 72 } as const
export const MAX_WORKERS = 6
export const FRAME_MS = 250
/** Menor largura do painel, em px, e escala inteira mínima que decorre dela. */
export const LARGURA_MIN_PX = 240
export const TAM_MIN_PX = 10

export const MSG_SEM_WORKTREE = 'Nenhum worktree em foco'
export const MSG_SEM_STARCODE = 'StarCode não configurado neste worktree'
export const LEGENDA = 'aceso = trabalhando · apagado = livre'

const TELAO: Retangulo = { x: 1, y: 1, largura: 46, altura: 12 }
const BARRA: Retangulo = { x: 4, y: 9.4, largura: 26, altura: 1.6 }
const ENGENHARIA: Retangulo = { x: 1, y: 49, largura: 46, altura: 20 }
const PICARD_POS: Celula = { x: 24, y: 34 }

const CORES: Record<Divisao, string> = {
  comando: '#c0392b',
  operacoes: '#d4a017',
  ciencias: '#2e86c1',
}

interface Membro { id: string; nome: string; emoji: string; divisao: Divisao }

// Picard na cadeira central, LaForge na engenharia; os outros 10 em volta, de cima para baixo.
const PICARD: Membro = { id: 'picard', nome: 'Picard', emoji: '🖖', divisao: 'comando' }
const LAFORGE: Membro = { id: 'laforge', nome: 'LaForge', emoji: '🔧', divisao: 'operacoes' }
const ARCO_MEMBROS: Membro[] = [
  { id: 'spock', nome: 'Spock', emoji: '🖖', divisao: 'ciencias' },
  { id: 'mccoy', nome: 'McCoy', emoji: '🧪', divisao: 'ciencias' },
  { id: 'data', nome: 'Data', emoji: '🤖', divisao: 'operacoes' },
  { id: 'worf', nome: 'Worf', emoji: '🛡️', divisao: 'comando' },
  { id: 'troi', nome: 'Troi', emoji: '💜', divisao: 'ciencias' },
  { id: 'uhura', nome: 'Uhura', emoji: '📡', divisao: 'operacoes' },
  { id: 'scotty', nome: 'Scotty', emoji: '⚙️', divisao: 'operacoes' },
  { id: 'kirk', nome: 'Kirk', emoji: '🚀', divisao: 'comando' },
  { id: 'q', nome: 'Q', emoji: '✨', divisao: 'ciencias' },
  { id: 'guinan', nome: 'Guinan', emoji: '🍸', divisao: 'ciencias' },
]

/** Posição (centro do emoji) de cada estação em volta da cadeira do Picard: arco de 3 + 2 + 2 no alto e nas laterais, 3 embaixo. */
const POSICOES: Celula[] = [
  { x: 6, y: 26.5 }, { x: 15, y: 20 }, { x: 24, y: 20 }, { x: 33, y: 20 }, { x: 42, y: 26.5 },
  { x: 6, y: 34 }, { x: 42, y: 34 },
  { x: 12, y: 41.8 }, { x: 24, y: 41.8 }, { x: 36, y: 41.8 },
]

function larguraTexto(texto: string, tam: number, emoji: boolean): number {
  return emoji ? tam * 1.3 : [...texto].length * 0.6 * tam
}

function rotulo(tipo: TipoRotulo, texto: string, x: number, y: number, tam: number): Rotulo {
  const largura = larguraTexto(texto, tam, tipo === 'emoji')
  const altura = tam * 1.2
  return { tipo, texto, x, y, tam, caixa: { x: x - largura / 2, y: y - altura / 2, largura, altura } }
}

function corta(texto: string, max: number): string {
  const letras = [...texto]
  return letras.length <= max ? texto : `${letras.slice(0, max - 1).join('')}…`
}

/** Quebra a frase em linhas de até `max` letras, sem partir palavras (palavra longa fica inteira). */
function quebra(texto: string, max: number): string[] {
  const linhas: string[] = []
  let atual = ''
  for (const palavra of texto.split(/\s+/).filter(Boolean)) {
    if (atual && [...atual].length + 1 + [...palavra].length > max) {
      linhas.push(atual)
      atual = palavra
    } else {
      atual = atual ? `${atual} ${palavra}` : palavra
    }
  }
  if (atual) linhas.push(atual)
  return linhas.slice(0, 6).map(l => corta(l, max))
}

/** Vaga `i` (0 a 5) da engenharia: 3 colunas por 2 linhas. */
function vagaWorker(i: number): { centro: Celula; caixa: Retangulo } {
  const centro = { x: 9 + (i % 3) * 15, y: 57 + Math.floor(i / 3) * 6.8 }
  return { centro, caixa: { x: centro.x - 4, y: centro.y - 2, largura: 8, altura: 4 } }
}

function casaWorker(agente: PonteAgent, worker: PonteWorker): boolean {
  const titulo = (agente.title ?? '').toLowerCase()
  if (!titulo) return false
  const chaves = [worker.label, ...worker.issues].filter(Boolean).map(c => c.toLowerCase())
  return chaves.some(c => titulo.includes(c))
}

function cenaVazia(mensagem: string): Cena {
  const linhas = quebra(mensagem, 30)
  const rotulos = linhas.map((l, i) => rotulo('mensagem', l, GRADE.largura / 2, 36 + (i - (linhas.length - 1) / 2) * 3, 2))
  return {
    grade: { ...GRADE },
    telao: { ...TELAO },
    progresso: null,
    estacoes: [],
    engenharia: { ...ENGENHARIA },
    vagas: [],
    personagens: [],
    workers: [],
    rotulos,
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
  const rotulos: Rotulo[] = []

  // Telão: slug, fase e progresso da feature.
  let progresso: Telao | null = null
  const feature = snap.feature
  if (feature) {
    const { done, total, percent } = feature.progress
    progresso = { slug: feature.slug, fase: feature.phase, feitos: done, total, percentual: percent, barra: { ...BARRA } }
    rotulos.push(rotulo('telao', corta(feature.slug, 28), 24, 3.6, 2.4))
    rotulos.push(rotulo('telao', corta(feature.phase, 28), 24, 6.8, 2))
    rotulos.push(rotulo('telao', `${done}/${total} · ${percent}%`, 38.5, BARRA.y + BARRA.altura / 2, 2))
  } else {
    rotulos.push(rotulo('telao', 'sem feature ativa', 24, 7, 2.4))
  }

  // Workers da engenharia: até 6 vagas em 3 colunas.
  const visiveis = snap.workers.slice(0, MAX_WORKERS)
  const workers: WorkerCena[] = visiveis.map((w, i) => {
    const { centro, caixa } = vagaWorker(i)
    return {
      rotulo: corta(w.label, 8),
      x: centro.x,
      y: centro.y,
      caixa,
      concluido: agentes.some(a => a.state === 'done' && casaWorker(a, w)),
      balao: false,
    }
  })

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

  const lugares: { m: Membro; x: number; y: number; caixa: Retangulo }[] = [
    { m: PICARD, ...PICARD_POS, caixa: { x: PICARD_POS.x - 5, y: PICARD_POS.y - 3, largura: 10, altura: 8.2 } },
    { m: LAFORGE, x: 6.5, y: 52, caixa: { x: 3, y: 50.4, largura: 17, altura: 3.2 } },
    ...ARCO_MEMBROS.map((m, i) => {
      const { x, y } = POSICOES[i]
      return { m, x, y, caixa: { x: x - 4, y: y - 2.2, largura: 8, altura: 7.4 } }
    }),
  ]
  const personagens: Personagem[] = lugares.map(({ m, x, y, caixa }) => {
    const c = porMembro.get(m.id)
    const ativo = (c?.count ?? 0) > 0
    const nome = c?.name || m.nome
    const emoji = c?.emoji || m.emoji
    const balao = balaoMembros.has(m.id)
    const meus = [rotulo('emoji', emoji, x, y, m === PICARD ? 3 : 2.6)]
    // LaForge: o nome fica ao lado do emoji, no cabeçalho da engenharia.
    meus.push(m === LAFORGE ? rotulo('nome', nome, 15, y, 2) : rotulo('nome', nome, x, y + 3.4, 2))
    if (balao) meus.push(rotulo('balao', '!', x + 3.2, y - 1.9, 2))
    for (const r of meus) rotulos.push({ ...r, dono: m.id })
    return {
      membro: m.id, nome, emoji, divisao: m.divisao, cor: CORES[m.divisao],
      pose: ativo ? 'sentado' : 'de-pe', ativo, quadro: ativo ? quadro : 0, x, y, balao, caixa,
    }
  })

  rotulos.push(rotulo('telao', 'ENGENHARIA', 30, 52, 2))
  for (const w of workers) {
    rotulos.push(rotulo('emoji', '🔧', w.x, w.y, 2.4))
    rotulos.push(rotulo('worker', w.rotulo, w.x, w.y + 3.6, 2))
    if (w.concluido) rotulos.push(rotulo('marca', '✓', w.x - 3.2, w.y - 1.3, 2))
    if (w.balao) rotulos.push(rotulo('balao', '!', w.x + 3.2, w.y - 1.3, 2))
  }
  const maisN = Math.max(0, snap.workers.length - MAX_WORKERS)
  if (maisN > 0) rotulos.push(rotulo('marca', `+${maisN}`, 43, 52, 2))
  rotulos.push(rotulo('legenda', LEGENDA, 24, 70.8, 2))

  return {
    grade: { ...GRADE },
    telao: { ...TELAO },
    progresso,
    estacoes: lugares.map(l => ({ membro: l.m.id, x: l.x, y: l.y })),
    engenharia: { ...ENGENHARIA },
    vagas: Array.from({ length: MAX_WORKERS }, (_, i) => vagaWorker(i).caixa),
    personagens,
    workers,
    rotulos,
    maisN,
    vazia: false,
    mensagem: null,
  }
}
