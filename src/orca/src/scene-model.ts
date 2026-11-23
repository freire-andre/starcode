// Modelo da cena da Ponte: só dados, sem DOM e sem host. A pintura (canvas) lê este resultado.
import type { PonteAgent, PonteState, PonteWorker } from './protocol.ts'
import { ESTADOS, PERFIS, estadosDaTripulacao } from './crew-visual.ts'
import type { EstadoDoMembro, EstadoVisual, Identidades } from './crew-visual.ts'

export type Divisao = 'comando' | 'operacoes' | 'ciencias'
export type Pose = 'sentado' | 'de-pe'

export interface Celula { x: number; y: number }
export interface Retangulo { x: number; y: number; largura: number; altura: number }

/** Estação fixa do arco: o console existe com ou sem personagem presente. */
export interface Estacao extends Celula { membro: string; escala: number; console: Retangulo }

/** Peça colorida do acessório ou do cabelo; o desenho só pinta o que o modelo entrega. */
export interface Peca extends Retangulo { cor: string }

/** Entrada ou saída pelo acesso da ponte; `progresso` (0 a 1) deriva só do relógio da cena (R4, R18). */
export interface Transicao { fase: 'entrando' | 'saindo'; progresso: number }

export type TipoRotulo = 'telao' | 'emoji' | 'nome' | 'tempo' | 'estado' | 'atividade' | 'worker' | 'marca' | 'balao' | 'legenda' | 'mensagem'

/** Texto da cena com a caixa que ele ocupa (centro em x,y); o teste prova que nenhuma caixa se sobrepõe. */
export interface Rotulo {
  tipo: TipoRotulo
  texto: string
  x: number
  y: number
  /** Altura da fonte em células da grade. */
  tam: number
  caixa: Retangulo
  /** Tripulante dono do texto (emoji, nome, tempo ou balão da estação), quando houver. */
  dono?: string
}

/** Boneco em pixel art: cabeça e corpo na cor da divisão; sentado não mostra as pernas (ficam sob o console). */
export interface Boneco {
  cabeca: Retangulo
  corpo: Retangulo
  bracos: Retangulo[]
  pernas: Retangulo[]
}

export interface Personagem extends Celula {
  membro: string
  nome: string
  emoji: string
  divisao: Divisao
  cor: string
  pose: Pose
  /** Estado confiável (R5 a R8): só `trabalhando` senta, digita e acende o console. */
  estado: EstadoVisual
  simbolo: string
  textoEstado: string
  /** Traço de silhueta do perfil visual e as peças que o desenham. */
  acessorio: string
  pele: string
  pecas: Peca[]
  /** Entrada ou saída em curso; null quando a presença é estável. */
  transicao: Transicao | null
  /** Estação de origem; x e y acompanham o personagem enquanto ele anda até ela ou até o acesso. */
  estacao: Celula
  /** Trabalhando e já na estação: sentado digitando, console aceso. */
  ativo: boolean
  /** Quadro da animação "trabalhando" (0 ou 1); 0 quando parado. */
  quadro: 0 | 1
  balao: boolean
  /** Tamanho do boneco (Picard é maior). */
  escala: number
  /** 1 quando ativo; no máximo 0,4 quando ocioso ou desconhecido (R52); multiplicada pela transição. */
  opacidade: number
  /** Opacidade dos textos do personagem: nome legível mesmo com o corpo apagado. */
  opacidadeTexto: number
  boneco: Boneco
  console: Retangulo
  /** Brilho do console aceso, na cor da divisão; null quando livre. */
  brilho: Retangulo | null
  /** "agora" ou "há N min" desde `lastAt`, só para o ativo. */
  tempo: string | null
  /** Área da estação (boneco, console e textos); as áreas não se tocam. */
  caixa: Retangulo
}

export interface WorkerCena extends Celula {
  rotulo: string
  concluido: boolean
  balao: boolean
  pose: Pose
  quadro: 0 | 1
  boneco: Boneco
  console: Retangulo
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
  /** Quantos tripulantes estão ativos (o telão mostra). */
  ativos: number
  /** Sala da ponte, de altura fixa (PONTE_ALTURA), logo abaixo do telão. */
  ponte: Retangulo
  /** Área de atividades e estados no espaço que sobra entre a engenharia e a legenda; null sem espaço. */
  atividades: Retangulo | null
  /** Caixa do anel do console (elipse): ocupa a largura e a altura da ponte. */
  anel: Retangulo
  estacoes: Estacao[]
  /** Acesso à ponte, de onde entram e saem os personagens. */
  porta: Celula
  engenharia: Retangulo
  /** Uma vaga por worker desenhado (até 6); sem worker, nenhuma. */
  vagas: Retangulo[]
  personagens: Personagem[]
  workers: WorkerCena[]
  rotulos: Rotulo[]
  /** Quantidade de workers além dos 6 desenhados. */
  maisN: number
  vazia: boolean
  mensagem: string | null
}

/** Largura fixa da grade e o mínimo de linhas; a altura real acompanha a proporção do painel (R54). */
export const GRADE = { largura: 48, altura: 128 } as const
/** Teto de linhas, para um painel muito alto não gerar uma grade absurda. */
export const LINHAS_MAX = 400
export const MAX_WORKERS = 6
/** Personagens presentes na ponte ao mesmo tempo (R2). */
export const MAX_PERSONAGENS = 6
/** Duração da troca de um integrante: metade para sair e metade para entrar, sem passar de seis (R4). */
export const TRANSICAO_MS = 1200
export const FRAME_MS = 250
/** Menor largura do painel, em px, e escala inteira mínima que decorre dela. */
export const LARGURA_MIN_PX = 240
export const TAM_MIN_PX = 10
/** Corpo de quem está ocioso ou desconhecido: apagado, mas ainda com silhueta e uniforme reconhecíveis a 240 px. */
export const OPACIDADE_LIVRE = 0.6

export const MSG_SEM_WORKTREE = 'Nenhum worktree em foco'
export const MSG_SEM_STARCODE = 'StarCode não configurado neste worktree'
export const MSG_SEM_WORKERS = 'Nenhum worker na engenharia'
export const LEGENDA = 'aceso = trabalhando · apagado = livre'

const TELAO: Retangulo = { x: 1, y: 1, largura: 46, altura: 12 }
const BARRA: Retangulo = { x: 4, y: 8.2, largura: 26, altura: 1.6 }
const PONTE_Y = 14
/** Distância da base da engenharia ao fim da grade (a legenda fica nela). */
const ENG_MARGEM = 3
const ENG_LINHA = 11
/** Bonecos maiores (R54): fator sobre o desenho de escala 1. */
const BONECO = 1.7

export const CORES: Record<Divisao, string> = {
  comando: '#c0392b',
  operacoes: '#d4a017',
  ciencias: '#2e86c1',
}

interface Membro { id: string; nome: string; emoji: string; divisao: Divisao }

const PICARD: Membro = { id: 'picard', nome: 'Picard', emoji: '🖖', divisao: 'comando' }

/**
 * As 11 estações em arco ao redor da cadeira do Picard, agrupadas numa ponte de proporção fixa (PONTE_ALTURA):
 * 3 no alto, 2 em cada lado (2 fileiras), 2 embaixo e 2 nos cantos baixos. `y` é a distância a partir do topo da
 * ponte. Duas áreas nunca se tocam: ou ficam a 11,4 células ou mais na horizontal, ou a 18,5 ou mais na vertical
 * (o teste confere todas as estações).
 */
const ARCO: (Membro & { x: number; y: number })[] = [
  { id: 'spock', nome: 'Spock', emoji: '🖖', divisao: 'ciencias', x: 10, y: 12 },
  { id: 'data', nome: 'Data', emoji: '🤖', divisao: 'operacoes', x: 24, y: 8.5 },
  { id: 'worf', nome: 'Worf', emoji: '🛡️', divisao: 'comando', x: 38, y: 12 },
  { id: 'mccoy', nome: 'McCoy', emoji: '🧪', divisao: 'ciencias', x: 6.6, y: 30.5 },
  { id: 'troi', nome: 'Troi', emoji: '💜', divisao: 'ciencias', x: 41.2, y: 30.5 },
  { id: 'uhura', nome: 'Uhura', emoji: '📡', divisao: 'operacoes', x: 6.6, y: 49 },
  { id: 'scotty', nome: 'Scotty', emoji: '⚙️', divisao: 'operacoes', x: 41.2, y: 49 },
  { id: 'kirk', nome: 'Kirk', emoji: '🚀', divisao: 'comando', x: 6.6, y: 67.5 },
  { id: 'laforge', nome: 'LaForge', emoji: '🔧', divisao: 'operacoes', x: 41.2, y: 67.5 },
  { id: 'q', nome: 'Q', emoji: '✨', divisao: 'ciencias', x: 18.2, y: 57 },
  { id: 'guinan', nome: 'Guinan', emoji: '🍸', divisao: 'ciencias', x: 29.7, y: 57 },
]
const PICARD_Y = 35
const PICARD_ESCALA = 1.5
/** Altura fixa da ponte: ela não estica com o painel; o espaço que sobra vai para as atividades. */
export const PONTE_ALTURA = 80.5
/** Altura da área acima e abaixo do centro do boneco de escala `s` (cabeça e textos). */
const acimaDe = (s: number): number => 7.8 * s
/** Nome em até duas linhas e, abaixo dele, o tempo. */
const abaixoDe = (s: number): number => 2.72 * s + 7.92
/** Distância do centro do boneco ao centro do nome. */
const nomeDy = (s: number): number => 2.72 * s + 1.2
/** Fonte do nome (11 px a 240 px) e distância entre as linhas dele, em células: o nome é o que identifica o tripulante. */
export const TAM_NOME = 2.2
const NOME_LINHA = 2.7
/** Linha e margens da área de atividades. */
const ATIV_LINHA = 3
const ATIV_MAX = 12

function larguraTexto(texto: string, tam: number, emoji: boolean): number {
  return emoji ? tam * 1.3 : [...texto].length * 0.6 * tam
}

function rotulo(tipo: TipoRotulo, texto: string, x: number, y: number, tam: number): Rotulo {
  const largura = larguraTexto(texto, tam, tipo === 'emoji' || tipo === 'estado')
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

/** Boneco em pixel art com centro do corpo em (x, y): sentado digita (braços alternam), de pé fica parado. */
function fazBoneco(x: number, y: number, s: number, sentado: boolean, quadro: 0 | 1): Boneco {
  const k = s * BONECO
  const r = (dx: number, dy: number, w: number, h: number): Retangulo => ({ x: x + dx * k, y: y + dy * k, largura: w * k, altura: h * k })
  if (sentado) {
    const esq = quadro === 0 ? 0.4 : 0
    const dir = quadro === 1 ? 0.4 : 0
    return {
      cabeca: r(-0.8, -3.6, 1.6, 1.6),
      corpo: r(-1.3, -2.0, 2.6, 2.6),
      bracos: [r(-1.9, -1.6 + esq, 0.6, 1.6), r(1.3, -1.6 + dir, 0.6, 1.6)],
      pernas: [],
    }
  }
  return {
    cabeca: r(-0.8, -4.2, 1.6, 1.6),
    corpo: r(-1.3, -2.6, 2.6, 3.2),
    bracos: [r(-1.9, -2.4, 0.6, 2.4), r(1.3, -2.4, 0.6, 2.4)],
    pernas: [r(-1.0, 0.6, 0.8, 1.0), r(0.2, 0.6, 0.8, 1.0)],
  }
}

function fazConsole(x: number, y: number, s: number): Retangulo {
  const k = s * BONECO
  return { x: x - 2.6 * k, y: y + 0.4 * k, largura: 5.2 * k, altura: 0.8 * k }
}

/** Opções de apresentação: movimento reduzido (R17), integrante escolhido na relação (R10) e a memória da presença. */
export interface OpcoesCena { reduzido?: boolean; selecionado?: string | null; rastro?: RastroPresenca }

const ALERTAS: readonly EstadoVisual[] = ['bloqueado', 'aguardando']

/** Prioridade do estado comprovado: alertas (0), depois quem trabalha (1), depois os demais (2) (R19). */
function prioridade(estado: EstadoVisual): number {
  return ALERTAS.includes(estado) ? 0 : estado === 'trabalhando' ? 1 : 2
}

/**
 * Quem fica na ponte (no máximo MAX_PERSONAGENS), na ordem dos perfis (R2, R19). A prioridade é alertas, depois
 * trabalhando, depois os demais; em caso de mesma prioridade ficam os `anteriores` (já presentes) e só então vale a
 * ordem dos perfis. Não depende do tempo (R3): os mesmos estados e a mesma presença anterior dão a mesma escolha.
 * `selecionado` (R10) é trazido à cena no lugar do último da escolha; o estado dele não muda, e quem já está presente
 * não altera a composição (R20).
 */
export function selecionaPresentes(estados: readonly EstadoDoMembro[], anteriores: readonly string[] = [], selecionado: string | null = null): string[] {
  const ordem = PERFIS.map(p => p.membro)
  const ranque = [...estados]
    .filter(e => ordem.includes(e.membro))
    .sort((a, b) =>
      prioridade(a.estado) - prioridade(b.estado)
      || Number(!anteriores.includes(a.membro)) - Number(!anteriores.includes(b.membro))
      || ordem.indexOf(a.membro) - ordem.indexOf(b.membro))
    .map(e => e.membro)
  const fica = ranque.slice(0, MAX_PERSONAGENS)
  if (selecionado !== null && ordem.includes(selecionado) && !fica.includes(selecionado)) {
    if (fica.length >= MAX_PERSONAGENS) fica.pop()
    fica.push(selecionado)
  }
  return ordem.filter(m => fica.includes(m))
}

export interface Presenca { membro: string; transicao: Transicao | null }

/** Memória da presença entre atualizações: quem está, quem sai e quem entra, com o instante em que cada troca começou. */
export interface RastroPresenca {
  /** Presença no instante `agoraMs`; chamar de novo com os mesmos estados e o mesmo instante dá o mesmo resultado (R18). */
  atualiza(estados: readonly EstadoDoMembro[], agoraMs: number, opcoes?: { reduzido?: boolean; selecionado?: string | null }): Presenca[]
}

/**
 * Cria o rastro de uma ponte. A primeira atualização povoa a cena sem animar; depois só mudanças reais de estado ou
 * de seleção geram saída (andando até o acesso, na primeira metade) e entrada (andando até a estação, depois que quem
 * sai terminou), então nunca há mais de seis. O progresso vem do instante em que a troca começou, não de quando a
 * atualização chegou, e estado repetido não reinicia nada (R4, R18). Com movimento reduzido não há deslocamento (R17).
 */
export function criaRastroPresenca(): RastroPresenca {
  const ordem = PERFIS.map(p => p.membro)
  const metade = TRANSICAO_MS / 2
  let alvo: string[] | null = null
  const saindo = new Map<string, number>()
  const entrando = new Map<string, number>()
  return {
    atualiza(estados, agoraMs, opcoes = {}) {
      const agora = Math.max(0, Number.isFinite(agoraMs) ? agoraMs : 0)
      const desejada = selecionaPresentes(estados, alvo ?? [], opcoes.selecionado ?? null)
      if (alvo === null || opcoes.reduzido) {
        alvo = desejada
        saindo.clear()
        entrando.clear()
      } else {
        for (const [m, ini] of saindo) if (agora - ini >= metade) saindo.delete(m)
        for (const [m, ini] of entrando) if (agora - ini >= metade) entrando.delete(m)
        for (const m of alvo.filter(x => !desejada.includes(x))) {
          // quem ainda nem começou a entrar simplesmente deixa de ser esperado
          if (entrando.has(m) && entrando.get(m)! > agora) entrando.delete(m)
          else { entrando.delete(m); saindo.set(m, agora) }
        }
        for (const m of desejada.filter(x => !alvo!.includes(x))) {
          if (saindo.has(m)) saindo.delete(m)
          else entrando.set(m, agora)
        }
        // entradas só começam quando todas as saídas terminaram: nunca passa de seis
        const fim = Math.max(agora, ...[...saindo.values()].map(i => i + metade))
        for (const [m, ini] of entrando) if (ini >= agora) entrando.set(m, Math.max(ini, fim))
        alvo = desejada
      }
      const visiveis = new Set<string>([...alvo.filter(m => (entrando.get(m) ?? 0) <= agora), ...saindo.keys()])
      return ordem.filter(m => visiveis.has(m)).map(membro => {
        if (saindo.has(membro)) return { membro, transicao: { fase: 'saindo' as const, progresso: Math.min(1, (agora - saindo.get(membro)!) / metade) } }
        if (entrando.has(membro)) return { membro, transicao: { fase: 'entrando' as const, progresso: Math.min(1, (agora - entrando.get(membro)!) / metade) } }
        return { membro, transicao: null }
      })
    },
  }
}

/** Presenças no instante `agoraMs`; sem `rastro` (cena avulsa) a escolha é só a prioridade, sem transição. */
export function presencas(estados: readonly EstadoDoMembro[], agoraMs: number, opcoes: OpcoesCena = {}): Presenca[] {
  return (opcoes.rastro ?? criaRastroPresenca()).atualiza(estados, agoraMs, opcoes)
}

const PELE_PADRAO = '#e0b48a'

interface Estilo { pele: string; pecas: (c: Retangulo, b: Retangulo, k: number) => Peca[] }
const peca = (cor: string, x: number, y: number, largura: number, altura: number): Peca => ({ cor, x, y, largura, altura })

/**
 * Silhueta própria de cada perfil, em pixel art gerada por código: o modelo só diz onde ficam as peças (cabelo,
 * orelhas, visor, chapéu...) e a pintura as desenha. `c` é a cabeça, `b` o corpo e `k` a célula do boneco.
 */
const ESTILOS: Record<string, Estilo> = {
  'cabeca-calva': { pele: '#e8c4a0', pecas: c => [peca('#fff4e0', c.x + c.largura * 0.2, c.y + c.altura * 0.05, c.largura * 0.3, c.altura * 0.12)] },
  'orelhas-pontudas': {
    pele: '#d9c27a',
    pecas: c => [
      peca('#1a1a1a', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.28),
      peca('#d9c27a', c.x - c.largura * 0.15, c.y + c.altura * 0.2, c.largura * 0.15, c.altura * 0.45),
      peca('#d9c27a', c.x + c.largura, c.y + c.altura * 0.2, c.largura * 0.15, c.altura * 0.45),
      peca('#1a1a1a', c.x + c.largura * 0.15, c.y + c.altura * 0.28, c.largura * 0.7, c.altura * 0.08),
    ],
  },
  'cabelo-cacheado': {
    pele: '#d9a679',
    pecas: c => [
      peca('#3a2416', c.x - c.largura * 0.2, c.y - c.altura * 0.2, c.largura * 1.4, c.altura * 0.45),
      peca('#3a2416', c.x - c.largura * 0.2, c.y + c.altura * 0.25, c.largura * 0.25, c.altura * 0.7),
      peca('#3a2416', c.x + c.largura * 0.95, c.y + c.altura * 0.25, c.largura * 0.25, c.altura * 0.7),
    ],
  },
  'pele-palida': {
    pele: '#eceed8',
    pecas: c => [
      peca('#1a1a1a', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.22),
      peca('#e8c030', c.x + c.largura * 0.2, c.y + c.altura * 0.4, c.largura * 0.2, c.altura * 0.2),
      peca('#e8c030', c.x + c.largura * 0.6, c.y + c.altura * 0.4, c.largura * 0.2, c.altura * 0.2),
    ],
  },
  visor: {
    pele: '#8a5a3c',
    pecas: c => [
      peca('#c8ccd8', c.x - c.largura * 0.1, c.y + c.altura * 0.35, c.largura * 1.2, c.altura * 0.3),
      peca('#ff3b30', c.x + c.largura * 0.2, c.y + c.altura * 0.4, c.largura * 0.6, c.altura * 0.2),
    ],
  },
  'tricorder-medico': {
    pele: '#e0b48a',
    pecas: (c, b) => [
      peca('#3a2a1a', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.25),
      peca('#d6f3f6', b.x + b.largura * 0.62, b.y + b.altura * 0.5, b.largura * 0.36, b.altura * 0.34),
      peca('#1f6f7a', b.x + b.largura * 0.7, b.y + b.altura * 0.58, b.largura * 0.14, b.altura * 0.12),
    ],
  },
  brilho: {
    pele: '#f6e3cf',
    pecas: (c, b) => [
      peca('#d4a017', b.x, b.y, b.largura, b.altura * 0.14),
      peca('#d4a017', b.x + b.largura * 0.44, b.y, b.largura * 0.12, b.altura),
      peca('#fff7a8', c.x - c.largura * 0.5, c.y - c.altura * 0.45, c.largura * 0.22, c.altura * 0.22),
      peca('#ffffff', c.x + c.largura * 0.4, c.y - c.altura * 0.6, c.largura * 0.2, c.altura * 0.2),
      peca('#fff7a8', c.x + c.largura * 1.25, c.y - c.altura * 0.3, c.largura * 0.22, c.altura * 0.22),
      peca('#ffffff', c.x - c.largura * 0.4, c.y + c.altura * 0.7, c.largura * 0.18, c.altura * 0.18),
      peca('#fff7a8', c.x + c.largura * 1.2, c.y + c.altura * 0.75, c.largura * 0.18, c.altura * 0.18),
    ],
  },
  'fone-de-ouvido': {
    pele: '#9a6a48',
    pecas: c => [
      peca('#14100e', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.28),
      peca('#14100e', c.x + c.largura * 0.3, c.y - c.altura * 0.3, c.largura * 0.4, c.altura * 0.25),
      peca('#f2f2f2', c.x - c.largura * 0.2, c.y + c.altura * 0.35, c.largura * 0.25, c.altura * 0.35),
      peca('#f2f2f2', c.x - c.largura * 0.05, c.y + c.altura * 0.62, c.largura * 0.3, c.altura * 0.1),
    ],
  },
  'chave-inglesa': {
    pele: '#e3b894',
    pecas: (c, b, k) => [
      peca('#b4501e', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.25),
      peca('#c9ced6', b.x + b.largura + 0.7 * k, b.y + 0.2 * k, 0.3 * k, 2.2 * k),
      peca('#c9ced6', b.x + b.largura + 0.45 * k, b.y, 0.8 * k, 0.5 * k),
    ],
  },
  comunicador: {
    pele: '#e5b98f',
    pecas: (c, b, k) => [
      peca('#6b4a2a', c.x, c.y - c.altura * 0.05, c.largura, c.altura * 0.28),
      peca('#202020', b.x, b.y + b.altura * 0.78, b.largura, 0.25 * k),
      peca('#d8d8d8', b.x + b.largura * 0.62, b.y + b.altura * 0.62, 0.8 * k, 0.55 * k),
    ],
  },
  'testa-craniana': {
    pele: '#8f6a54',
    pecas: (c, b) => [
      peca('#c9ced6', b.x + b.largura * 0.1, b.y + b.altura * 0.08, b.largura * 0.8, b.altura * 0.2),
      peca('#0e0e12', c.x - c.largura * 0.1, c.y - c.altura * 0.1, c.largura * 1.2, c.altura * 0.3),
      peca('#0e0e12', c.x - c.largura * 0.1, c.y + c.altura * 0.2, c.largura * 0.2, c.altura * 0.8),
      peca('#0e0e12', c.x + c.largura * 0.9, c.y + c.altura * 0.2, c.largura * 0.2, c.altura * 0.8),
      peca('#5a3c2c', c.x + c.largura * 0.25, c.y + c.altura * 0.2, c.largura * 0.14, c.altura * 0.2),
      peca('#5a3c2c', c.x + c.largura * 0.45, c.y + c.altura * 0.2, c.largura * 0.14, c.altura * 0.2),
      peca('#5a3c2c', c.x + c.largura * 0.65, c.y + c.altura * 0.2, c.largura * 0.14, c.altura * 0.2),
    ],
  },
  'chapeu-largo': {
    pele: '#6e4a36',
    pecas: c => [
      peca('#7a2f66', c.x - c.largura * 0.6, c.y - c.altura * 0.1, c.largura * 2.2, c.altura * 0.22),
      peca('#7a2f66', c.x + c.largura * 0.15, c.y - c.altura * 0.55, c.largura * 0.7, c.altura * 0.5),
    ],
  },
}

const SEM_DISTINTIVO = ['brilho', 'cabelo-cacheado', 'chapeu-largo']

/** Peças do perfil para um boneco; o acessório vem de `PERFIS` e cada um tem o próprio desenho. */
export function pecasDoPerfil(acessorio: string, boneco: Boneco, escala: number): { pele: string; pecas: Peca[] } {
  const estilo = ESTILOS[acessorio]
  if (!estilo) return { pele: PELE_PADRAO, pecas: [] }
  const b = boneco.corpo
  // distintivo de comunicação dourado no peito dos oficiais da Frota; Q, Troi e Guinan não vestem o uniforme
  const distintivo = SEM_DISTINTIVO.includes(acessorio) ? [] : [peca('#ffd24a', b.x + b.largura * 0.14, b.y + b.altura * 0.16, b.largura * 0.2, b.altura * 0.18)]
  return { pele: estilo.pele, pecas: [...estilo.pecas(boneco.cabeca, b, escala * BONECO), ...distintivo] }
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t
}

/** Linhas da grade para um palco de `largura` x `altura` px: mesma proporção, entre GRADE.altura e LINHAS_MAX. */
export function linhasDoPainel(largura: number, altura: number): number {
  if (!(largura > 0) || !(altura > 0)) return GRADE.altura
  return normalizaLinhas((GRADE.largura * altura) / largura)
}

/** Linhas válidas: inteiras, entre GRADE.altura e LINHAS_MAX. */
function normalizaLinhas(linhas: number | undefined): number {
  if (linhas === undefined || !Number.isFinite(linhas)) return GRADE.altura
  return Math.min(LINHAS_MAX, Math.max(GRADE.altura, Math.floor(linhas)))
}

/**
 * "agora" com menos de 1 minuto (R54), depois "há N min" desde `lastAt` (horas e dias quando passa disso,
 * para o texto caber); null sem data válida.
 */
export function haQuanto(lastAt: string | null | undefined, agoraMs: number): string | null {
  const t = lastAt ? Date.parse(lastAt) : NaN
  if (!Number.isFinite(t)) return null
  const min = Math.max(0, Math.floor((agoraMs - t) / 60_000))
  if (min < 1) return 'agora'
  if (min < 60) return `há ${min} min`
  if (min < 24 * 60) return `há ${Math.floor(min / 60)} h`
  return `há ${Math.min(99, Math.floor(min / (24 * 60)))} d`
}

function textoAtivos(n: number): string {
  if (n === 0) return 'tripulação em repouso'
  return n === 1 ? '1 tripulante ativo' : `${n} tripulantes ativos`
}

function casaWorker(agente: PonteAgent, worker: PonteWorker): boolean {
  const titulo = (agente.title ?? '').toLowerCase()
  if (!titulo) return false
  const chaves = [worker.label, ...worker.issues].filter(Boolean).map(c => c.toLowerCase())
  return chaves.some(c => titulo.includes(c))
}

function anelDa(ponte: Retangulo): Retangulo {
  return { x: ponte.x + 0.5, y: ponte.y, largura: ponte.largura - 1, altura: ponte.altura }
}

function cenaVazia(mensagem: string, alturaGrade: number): Cena {
  const linhas = quebra(mensagem, 30)
  const meio = alturaGrade / 2
  const fundo = alturaGrade - ENG_MARGEM
  const rotulos = linhas.map((l, i) => rotulo('mensagem', l, GRADE.largura / 2, meio + (i - (linhas.length - 1) / 2) * 3, 2))
  const ponte: Retangulo = { x: 0, y: PONTE_Y, largura: GRADE.largura, altura: fundo - PONTE_Y }
  return {
    grade: { largura: GRADE.largura, altura: alturaGrade },
    telao: { ...TELAO },
    progresso: null,
    ativos: 0,
    ponte,
    atividades: null,
    anel: anelDa(ponte),
    estacoes: [],
    porta: { x: GRADE.largura / 2, y: fundo - 1.5 },
    engenharia: { x: 1, y: fundo, largura: 46, altura: 0 },
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

/**
 * Monta a cena (função pura). `linhas` é a altura da grade em células, tirada da proporção do palco
 * (`linhasDoPainel`); a largura é sempre GRADE.largura e a ponte, com o anel, ocupa a altura que sobra.
 */
export function buildScene(estado: PonteState, agentes: PonteAgent[], agoraMs: number, linhas?: number, ids: Identidades = {}, opcoes: OpcoesCena = {}): Cena {
  const alturaGrade = normalizaLinhas(linhas)
  const mensagem = mensagemDoEstado(estado)
  if (mensagem !== null || !estado.snapshot) return cenaVazia(mensagem ?? MSG_SEM_WORKTREE, alturaGrade)

  const snap = estado.snapshot
  const quadro = (opcoes.reduzido ? 0 : Math.floor(agoraMs / FRAME_MS) % 2) as 0 | 1
  const porMembro = new Map(snap.crew.map(c => [c.member, c]))
  const estados = estadosDaTripulacao({ ...estado, agents: agentes }, ids)
  const porEstado = new Map(estados.map(e => [e.membro, e.estado]))
  const ativos = estados.filter(e => e.estado === 'trabalhando').length
  const rotulos: Rotulo[] = []

  // Telão: slug, fase, progresso da feature e quantos tripulantes estão ativos.
  let progresso: Telao | null = null
  const feature = snap.feature
  if (feature) {
    const { done, total, percent } = feature.progress
    progresso = { slug: feature.slug, fase: feature.phase, feitos: done, total, percentual: percent, barra: { ...BARRA } }
    rotulos.push(rotulo('telao', corta(feature.slug, 28), 24, 3.4, 2.4))
    rotulos.push(rotulo('telao', corta(feature.phase, 28), 24, 6.1, 2))
    rotulos.push(rotulo('telao', `${done}/${total} · ${percent}%`, 38.5, BARRA.y + BARRA.altura / 2, 2))
    rotulos.push(rotulo('telao', textoAtivos(ativos), 24, 11.6, 2))
  } else {
    rotulos.push(rotulo('telao', 'sem feature ativa', 24, 5, 2.4))
    rotulos.push(rotulo('telao', textoAtivos(ativos), 24, 9.5, 2))
  }

  // Engenharia: só os workers reais (até 6, 3 por linha); sem worker, uma linha só.
  const visiveis = snap.workers.slice(0, MAX_WORKERS)
  const linhasEng = Math.ceil(visiveis.length / 3)
  const engAltura = linhasEng === 0 ? 4 : 4 + linhasEng * ENG_LINHA
  const ponte: Retangulo = { x: 0, y: PONTE_Y, largura: GRADE.largura, altura: PONTE_ALTURA }
  const engenharia: Retangulo = { x: 1, y: ponte.y + ponte.altura + 1, largura: 46, altura: engAltura }
  const workers: WorkerCena[] = visiveis.map((w, i) => {
    const x = 9 + (i % 3) * 15
    const y = engenharia.y + 9.2 + Math.floor(i / 3) * ENG_LINHA
    const concluido = agentes.some(a => a.state === 'done' && casaWorker(a, w))
    const q: 0 | 1 = concluido ? 0 : quadro
    return {
      rotulo: corta(w.label, 8), x, y, concluido, balao: false,
      pose: concluido ? 'de-pe' : 'sentado', quadro: q,
      boneco: fazBoneco(x, y, 1, !concluido, q),
      console: fazConsole(x, y, 1),
      caixa: { x: x - 5, y: y - 5.8, largura: 10, altura: 10.6 },
    }
  })

  // Balão dos workers: só quando o agente casa com o worker (a identidade dos tripulantes vem de `ids`).
  for (const agente of agentes) {
    if (agente.state !== 'blocked' && agente.state !== 'waiting') continue
    const i = visiveis.findIndex(w => casaWorker(agente, w))
    if (i >= 0) workers[i].balao = true
  }

  // Ponte: proporção fixa (R54 trocou o esticamento por uma área de atividades abaixo da engenharia).
  const topo = ponte.y

  const lugares: { m: Membro; x: number; y: number; s: number }[] = [
    { m: PICARD, x: GRADE.largura / 2, y: topo + PICARD_Y, s: PICARD_ESCALA },
    ...ARCO.map(m => ({ m, x: m.x, y: topo + m.y, s: 1 })),
  ]
  const porta: Celula = { x: GRADE.largura / 2, y: ponte.y + ponte.altura - 1.5 }
  const lugarDe = new Map(lugares.map(l => [l.m.id, l]))
  const perfilDe = new Map(PERFIS.map(p => [p.membro, p]))
  const personagens: Personagem[] = presencas(estados, agoraMs, opcoes).map(({ membro, transicao }) => {
    const { m, x: ex, y: ey, s } = lugarDe.get(membro)!
    const perfil = perfilDe.get(membro)!
    const c = porMembro.get(membro)
    const visual = porEstado.get(membro) ?? 'desconhecido'
    const apres = ESTADOS[visual]
    const andando = transicao !== null
    // andando até a estação (entrando) ou até o acesso (saindo): só a posição muda, nunca o estado
    const t = transicao ? (transicao.fase === 'entrando' ? transicao.progresso : 1 - transicao.progresso) : 1
    const x = lerp(porta.x, ex, t)
    const y = lerp(porta.y, ey, t)
    const ativo = apres.animaConsole && !andando
    const alerta = ALERTAS.includes(visual)
    // nome completo do perfil (R1), em até duas linhas para caber ao lado dos vizinhos; o `name` do snapshot é curto
    const nome = perfil.nome
    const linhasNome = quebra(nome, 10)
    const emoji = c?.emoji || m.emoji
    const tempo = ativo ? haQuanto(c?.lastAt, agoraMs) : null
    const q: 0 | 1 = ativo ? quadro : 0
    // os textos ficam na estação (e surgem ou somem com a opacidade) enquanto o corpo anda: assim nunca cruzam os dos
    // vizinhos, que é o que garante a legibilidade também nas fases de entrada e saída
    const yNome = ey + nomeDy(s)
    const meus = [
      rotulo('emoji', emoji, ex, ey - 1.2 * s, s > 1 ? 2.6 : 2),
      ...linhasNome.map((l, i) => rotulo('nome', l, ex, yNome + i * NOME_LINHA, TAM_NOME)),
      rotulo('estado', apres.simbolo, ex + 4.2 * s, ey - 6.6 * s, 2),
    ]
    if (tempo) meus.push(rotulo('tempo', tempo, ex, yNome + NOME_LINHA * linhasNome.length, 2)) // folga contra o arredondamento
    if (alerta) meus.push(rotulo('balao', '!', ex - 4.2 * s, ey - 6.6 * s, 2))
    for (const r of meus) rotulos.push({ ...r, dono: m.id })
    const consoleR = fazConsole(ex, ey, s)
    const acima = acimaDe(s)
    const abaixo = abaixoDe(s)
    const meia = 5.7 + (s - 1) * 4
    const boneco = fazBoneco(x, y, s, ativo, q)
    const mult = transicao ? (transicao.fase === 'entrando' ? transicao.progresso : 1 - transicao.progresso) : 1
    const base = visual === 'ocioso' || visual === 'desconhecido' ? OPACIDADE_LIVRE : 1
    const estilo = pecasDoPerfil(perfil.acessorio, boneco, s)
    return {
      membro: m.id, nome, emoji, divisao: m.divisao, cor: perfil.cor,
      estado: visual, simbolo: apres.simbolo, textoEstado: apres.texto,
      acessorio: perfil.acessorio, pele: estilo.pele, pecas: estilo.pecas,
      transicao, estacao: { x: ex, y: ey },
      pose: ativo ? 'sentado' : 'de-pe', ativo, quadro: q, x, y, balao: alerta,
      escala: s,
      opacidade: base * mult,
      opacidadeTexto: (base === 1 ? 1 : 0.85) * mult,
      boneco,
      console: consoleR,
      brilho: ativo ? { x: consoleR.x - 0.6, y: consoleR.y - 0.6, largura: consoleR.largura + 1.2, altura: consoleR.altura + 1.2 } : null,
      tempo,
      caixa: { x: ex - meia, y: ey - acima, largura: meia * 2, altura: acima + abaixo },
    }
  })

  const maisN = Math.max(0, snap.workers.length - MAX_WORKERS)
  if (workers.length === 0) {
    rotulos.push(rotulo('worker', MSG_SEM_WORKERS, 24, engenharia.y + engenharia.altura / 2, 2))
  } else {
    rotulos.push(rotulo('telao', 'ENGENHARIA', 24, engenharia.y + 1.9, 2))
    if (maisN > 0) rotulos.push(rotulo('marca', `+${maisN}`, 43, engenharia.y + 1.9, 2))
  }
  for (const w of workers) {
    rotulos.push(rotulo('emoji', '🔧', w.x, w.y - 1, 2))
    rotulos.push(rotulo('worker', w.rotulo, w.x, w.y + 3.4, 2))
    if (w.concluido) rotulos.push(rotulo('marca', '✓', w.x - 2.6, w.y - 1, 2))
    if (w.balao) rotulos.push(rotulo('balao', '!', w.x + 2.6, w.y - 1, 2))
  }
  // Atividades: o espaço vertical que sobra vira uma lista dos estados reais (nada de dado inventado).
  const topoAtiv = engenharia.y + engenharia.altura + 1
  const espaco = alturaGrade - 3.5 - topoAtiv
  let atividades: Retangulo | null = null
  if (espaco >= ATIV_LINHA * 2 + 3.5) {
    // só quem tem estado comprovado e relevante ganha linha própria; os sem prova entram numa linha de resumo
    const itens = estados
      .filter(e => e.estado !== 'ocioso' && e.estado !== 'desconhecido')
      .map(e => `${ESTADOS[e.estado].simbolo} ${corta(porMembro.get(e.membro)?.name || e.membro, 8)} · ${ESTADOS[e.estado].texto}`)
    const incertos = estados.filter(e => e.estado === 'desconhecido').length
    const resumo = incertos > 0 ? `${ESTADOS.desconhecido.simbolo} ${incertos} ${incertos === 1 ? 'desconhecido' : 'desconhecidos'}` : null
    const cabem = Math.min(ATIV_MAX, Math.floor((espaco - 3.5) / ATIV_LINHA)) - (resumo ? 1 : 0)
    const lista = itens.length > cabem ? [...itens.slice(0, cabem - 1), `+${itens.length - cabem + 1}`] : itens
    const mostrados = resumo ? [...lista, resumo] : lista.length === 0 ? ['sem atividade registrada'] : lista
    atividades = { x: 1, y: topoAtiv, largura: 46, altura: 3.5 + mostrados.length * ATIV_LINHA }
    rotulos.push(rotulo('telao', 'ATIVIDADES', 24, topoAtiv + 1.9, 2))
    mostrados.forEach((t, i) => rotulos.push(rotulo('atividade', t, 24, topoAtiv + 3.5 + (i + 0.5) * ATIV_LINHA, 2)))
  }
  rotulos.push(rotulo('legenda', LEGENDA, 24, alturaGrade - 1.4, 2))

  return {
    grade: { largura: GRADE.largura, altura: alturaGrade },
    telao: { ...TELAO },
    progresso,
    ativos,
    ponte,
    atividades,
    anel: anelDa(ponte),
    estacoes: lugares.map(l => ({ membro: l.m.id, x: l.x, y: l.y, escala: l.s, console: fazConsole(l.x, l.y, l.s) })),
    porta,
    engenharia,
    vagas: workers.map(w => ({ ...w.caixa })),
    personagens,
    workers,
    rotulos,
    maisN,
    vazia: false,
    mensagem: null,
  }
}

/** Um integrante na relação acessível: nome, estado e presença na cena (R9, R16). */
export interface ItemRelacao {
  membro: string
  nome: string
  emoji: string
  estado: EstadoVisual
  simbolo: string
  textoEstado: string
  presente: boolean
  selecionado: boolean
  /** Texto para leitor de tela: nome, estado e presença. */
  descricao: string
}

/** Horário local HH:MM:SS de um instante em ms. */
export function horario(ms: number): string {
  const d = new Date(ms)
  return [d.getHours(), d.getMinutes(), d.getSeconds()].map(n => String(n).padStart(2, '0')).join(':')
}

/**
 * Relação dos 12 integrantes, sempre na ordem dos perfis e mesmo sem cena (sem worktree, erro). O estado vem
 * de `estadosDaTripulacao`, o mesmo que a cena usa; só diz o que a fonte garante, sem escopo de worktree.
 */
export function relacaoDaTripulacao(
  estado: PonteState, agentes: PonteAgent[], agoraMs: number, ids: Identidades = {}, opcoes: OpcoesCena = {},
): ItemRelacao[] {
  const estados = estadosDaTripulacao({ ...estado, agents: agentes }, ids)
  const naCena = new Set(mensagemDoEstado(estado) === null ? presencas(estados, agoraMs, opcoes).map(p => p.membro) : [])
  const sel = opcoes.selecionado ?? null
  return PERFIS.map(perfil => {
    const visual = estados.find(e => e.membro === perfil.membro)?.estado ?? 'desconhecido'
    const apres = ESTADOS[visual]
    const c = estado.snapshot?.crew.find(x => x.member === perfil.membro)
    const nome = perfil.nome // nome completo do perfil, também com snapshot real (o `name` dele é curto)
    const presente = naCena.has(perfil.membro)
    return {
      membro: perfil.membro, nome, emoji: c?.emoji || perfil.emoji, estado: visual, simbolo: apres.simbolo,
      textoEstado: apres.texto, presente, selecionado: sel === perfil.membro,
      descricao: `${nome}, ${apres.texto}, ${presente ? 'na cena' : 'fora da cena'}`,
    }
  })
}

/** Aviso de falha ou de dados antigos com o horário da última atualização válida (R13); null quando está tudo em dia. */
export function avisoDeDados(estado: PonteState): string | null {
  const ultima = estado.lastValidAt != null
    ? `última atualização válida às ${horario(estado.lastValidAt)}`
    : 'ainda sem atualização válida'
  if (estado.status === 'erro') return `Dados indisponíveis (${primeiraLinha(estado.error)}); ${ultima}`
  if (estado.status === 'ok' && estado.stale) return `Dados desatualizados; ${ultima}`
  return null
}
