// Perfis visuais dos 12 integrantes e estado confiável da tripulação: só dados, sem DOM e sem host.
// A fonte dos integrantes é `src/crew.yaml`; o estado deriva do contrato `PonteState` (protocol.ts).
import type { PonteAgent, PonteState } from './protocol.ts'

export interface PerfilVisual {
  membro: string
  /** Nome completo, como o personagem aparece na cena. */
  nome: string
  emoji: string
  /** Cor do uniforme (#rrggbb). */
  cor: string
  /** Traço que distingue a silhueta, para o desenho não depender só da cor. */
  acessorio: string
}

/** Os 12 integrantes de `src/crew.yaml`, na ordem do arquivo; nome, emoji, cor e acessório são todos distintos. */
export const PERFIS: readonly PerfilVisual[] = [
  { membro: 'picard', nome: 'Jean-Luc Picard', emoji: '🛸', cor: '#b32d2e', acessorio: 'cabeca-calva' },
  { membro: 'spock', nome: 'Spock', emoji: '🖖', cor: '#2b6cb0', acessorio: 'orelhas-pontudas' },
  { membro: 'troi', nome: 'Deanna Troi', emoji: '💜', cor: '#7b4fa3', acessorio: 'cabelo-cacheado' },
  { membro: 'data', nome: 'Data', emoji: '🤖', cor: '#c9a227', acessorio: 'pele-palida' },
  { membro: 'laforge', nome: 'Geordi La Forge', emoji: '🔧', cor: '#d9822b', acessorio: 'visor' },
  { membro: 'mccoy', nome: 'Leonard McCoy', emoji: '🧪', cor: '#3b8f9e', acessorio: 'tricorder-medico' },
  { membro: 'q', nome: 'Q', emoji: '✨', cor: '#8c1d3d', acessorio: 'brilho' },
  { membro: 'uhura', nome: 'Nyota Uhura', emoji: '📡', cor: '#e0533d', acessorio: 'fone-de-ouvido' },
  { membro: 'scotty', nome: 'Montgomery Scott', emoji: '⚙️', cor: '#8a5a2b', acessorio: 'chave-inglesa' },
  { membro: 'kirk', nome: 'James T. Kirk', emoji: '🚀', cor: '#3f9d4a', acessorio: 'comunicador' },
  { membro: 'worf', nome: 'Worf', emoji: '🛡️', cor: '#4a4a5c', acessorio: 'testa-craniana' },
  { membro: 'guinan', nome: 'Guinan', emoji: '🍸', cor: '#a63f78', acessorio: 'chapeu-largo' },
]

export const MEMBROS: readonly string[] = PERFIS.map(p => p.membro)

export type EstadoVisual = 'trabalhando' | 'ocioso' | 'aguardando' | 'bloqueado' | 'concluido' | 'desconhecido'

export interface ApresentacaoEstado {
  estado: EstadoVisual
  /** Símbolo próprio de cada estado (R5 a R7). */
  simbolo: string
  texto: string
  /** Só o estado "trabalhando" opera o console (R5, R6). */
  animaConsole: boolean
}

export const ESTADOS: Readonly<Record<EstadoVisual, ApresentacaoEstado>> = {
  trabalhando: { estado: 'trabalhando', simbolo: '⚙', texto: 'trabalhando', animaConsole: true },
  ocioso: { estado: 'ocioso', simbolo: '💤', texto: 'ocioso', animaConsole: false },
  aguardando: { estado: 'aguardando', simbolo: '⏳', texto: 'aguardando', animaConsole: false },
  bloqueado: { estado: 'bloqueado', simbolo: '⛔', texto: 'bloqueado', animaConsole: false },
  concluido: { estado: 'concluido', simbolo: '✔', texto: 'concluído', animaConsole: false },
  desconhecido: { estado: 'desconhecido', simbolo: '?', texto: 'desconhecido', animaConsole: false },
}

/** Vínculos confiáveis `terminalId -> integrante` (por exemplo, o despacho que abriu o terminal). Título não vale. */
export type Identidades = Readonly<Record<string, string>>

export interface EstadoDoMembro {
  membro: string
  estado: EstadoVisual
  /** Por que o estado foi escolhido; também diz por que ficou desconhecido. */
  motivo: string
}

const DO_AGENTE: Readonly<Record<string, EstadoVisual>> = {
  working: 'trabalhando',
  waiting: 'aguardando',
  blocked: 'bloqueado',
  done: 'concluido',
}

const tem = (obj: object, chave: string): boolean => Object.prototype.hasOwnProperty.call(obj, chave)

/** Contagem do snapshot que o `ponte.py` pode produzir: inteiro de 0 a 10 (`crew_live.count_members`). Outra coisa não prova nada. */
const contagemValida = (n: unknown): n is number => typeof n === 'number' && Number.isInteger(n) && n >= 0 && n <= 10

function vinculado(agente: PonteAgent, membro: string, ids: Identidades): boolean {
  return agente.terminalId !== null && tem(ids, agente.terminalId) && ids[agente.terminalId] === membro
}

function semVinculo(agente: PonteAgent, ids: Identidades): boolean {
  return agente.terminalId === null || !tem(ids, agente.terminalId) || !MEMBROS.includes(ids[agente.terminalId])
}

/**
 * Estado dos 12 integrantes, sempre na ordem de `PERFIS`. Só conta o que é comprovado no worktree em foco:
 * agente vinculado por `ids` (o estado dele vale, inclusive espera, bloqueio e conclusão). O `count` do snapshot
 * vem de `crew_live.count_members` sobre o `sessions.json` do worktree principal, que agrega as sessões de TODOS
 * os worktrees do repositório e não registra de qual veio cada uma: `count` > 0 prova atividade no repositório,
 * não neste worktree, então dá `desconhecido` (nunca `trabalhando`). `count` 0 prova que não há sessão ativa em
 * lugar nenhum, logo o integrante está livre aqui também (`ocioso`); `count` ausente, nulo ou inválido (fora de
 * 0 a 10, não inteiro, texto) não prova nada e dá `desconhecido`. Dado indisponível ou antigo (erro, `stale`,
 * sem worktree, sem snapshot, sem StarCode), integrante fora do snapshot, vínculos conflitantes e estado de
 * agente fora do contrato também dão `desconhecido`. Agente ativo sem identidade só impede afirmar ocioso.
 * Título nunca é identidade.
 */
export function estadosDaTripulacao(estado: PonteState, ids: Identidades): EstadoDoMembro[] {
  const snap = estado.snapshot
  const utilizavel = estado.status === 'ok' && !estado.stale && snap !== null && snap.starcode
  // agente ativo sem vínculo pode ser de qualquer integrante: não se afirma ocioso em ninguém
  const ativoSemIdentidade = utilizavel && estado.agents.some(a => a.state !== 'done' && semVinculo(a, ids))
  return MEMBROS.map((membro): EstadoDoMembro => {
    const desconhecido = (motivo: string): EstadoDoMembro => ({ membro, estado: 'desconhecido', motivo })
    if (!utilizavel) return desconhecido('dados indisponíveis ou antigos')
    if (!snap.crew.some(c => c.member === membro)) return desconhecido('integrante ausente do snapshot')
    const seus = estado.agents.filter(a => vinculado(a, membro, ids))
    if (seus.length > 0) {
      const estados = seus.map(a => DO_AGENTE[a.state])
      if (estados.some(e => e === undefined)) return desconhecido('estado de agente fora do contrato')
      if (new Set(estados).size > 1) return desconhecido('mais de um agente vinculado com estados diferentes')
      return { membro, estado: estados[0], motivo: `agente vinculado ${ESTADOS[estados[0]].texto}` }
    }
    const contagem: unknown = snap.crew.find(c => c.member === membro)?.count
    if (!contagemValida(contagem)) return desconhecido('contagem de sessões ausente ou inválida no snapshot')
    if (contagem > 0) return desconhecido('atividade no repositório, sem prova de que é deste worktree')
    if (ativoSemIdentidade) return desconhecido('agente ativo sem identidade confiável')
    return { membro, estado: 'ocioso', motivo: 'sem sessão ativa no snapshot do repositório' }
  })
}
