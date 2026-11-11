// Painel HTML "ponte-cena": desenha a cena da Ponte num canvas. Lê só o resultado de buildScene (R43)
// e só usa fillRect/fillText/strokeRect: nenhuma imagem nem arquivo de arte (R38).
import { buildScene, CORES, GRADE, linhasDoPainel } from './scene-model.ts'
import type { Boneco, Cena, Rotulo, TipoRotulo } from './scene-model.ts'
import type { PonteAgent, PonteState } from './protocol.ts'

/** Contexto mínimo do canvas que a pintura usa (permite um contexto falso nos testes). */
export interface Pincel {
  fillStyle: string
  strokeStyle: string
  lineWidth: number
  font: string
  textAlign: string
  textBaseline: string
  fillRect(x: number, y: number, w: number, h: number): void
  strokeRect(x: number, y: number, w: number, h: number): void
  fillText(texto: string, x: number, y: number): void
}

const COR = {
  fundo: '#0b1020',
  piso: '#121830',
  pisoLinha: '#171f3c',
  anel: '#1b2448',
  anelBorda: '#2c3a6e',
  plataforma: '#222c55',
  telao: '#0f2238',
  telaoBorda: '#58a6c9',
  barraFundo: '#1d2a44',
  barra: '#2ecc71',
  borda: '#5b6aa0',
  cadeira: '#4a557f',
  console: '#3a4466',
  tela: '#9fe8ff',
  engenharia: '#2a2230',
  engenhariaBorda: '#c97a58',
  vaga: '#3a2a3e',
  vagaOk: '#1f4d36',
  olho: '#0b1020',
  perna: '#2b3148',
  texto: '#e8ecff',
  tempo: '#ffd866',
  balao: '#ffffff',
  balaoTexto: '#c0392b',
  ok: '#2ecc71',
  mensagem: '#9aa7d8',
  legenda: '#c8d0f0',
}

const COR_TEXTO: Record<TipoRotulo, string> = {
  telao: COR.texto,
  emoji: COR.texto,
  nome: COR.texto,
  tempo: COR.tempo,
  worker: COR.texto,
  marca: COR.ok,
  balao: COR.balaoTexto,
  legenda: COR.legenda,
  mensagem: COR.mensagem,
}

type Caixa = { x: number; y: number; largura: number; altura: number }

/** Cor com opacidade: a própria cor quando opaca, `rgba(...)` quando não (o canvas não precisa de globalAlpha). */
function alfa(hex: string, a: number): string {
  if (a >= 1) return hex
  const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16))
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

function ret(p: Pincel, cor: string, x: number, y: number, w: number, h: number, e: number): void {
  p.fillStyle = cor
  p.fillRect(x * e, y * e, w * e, h * e)
}

function bloco(p: Pincel, cor: string, r: Caixa, e: number): void {
  ret(p, cor, r.x, r.y, r.largura, r.altura, e)
}

function caixa(p: Pincel, cor: string, borda: string, r: Caixa, e: number): void {
  bloco(p, cor, r, e)
  p.strokeStyle = borda
  p.lineWidth = Math.max(1, e / 2)
  p.strokeRect(r.x * e, r.y * e, r.largura * e, r.altura * e)
}

function texto(p: Pincel, r: Rotulo, e: number, opacidade = 1): void {
  p.fillStyle = alfa(COR_TEXTO[r.tipo], opacidade)
  p.font = `${Math.max(6, Math.round(r.tam * e))}px system-ui, sans-serif`
  p.textAlign = 'center'
  p.textBaseline = 'middle'
  p.fillText(r.texto, r.x * e, r.y * e)
}

/** Elipse em degraus de 1 célula (pixel art), só com fillRect. */
function elipse(p: Pincel, cor: string, cx: number, cy: number, rx: number, ry: number, e: number): void {
  for (let dy = -ry; dy < ry; dy += 1) {
    const meio = dy + 0.5
    const meia = rx * Math.sqrt(Math.max(0, 1 - (meio / ry) ** 2))
    if (meia > 0) ret(p, cor, cx - meia, cy + dy, meia * 2, 1, e)
  }
}

/** Boneco: pernas, corpo, braços e cabeça na cor da divisão, com dois olhos. */
function desenhaBoneco(p: Pincel, b: Boneco, cor: string, op: number, e: number): void {
  for (const r of b.pernas) bloco(p, alfa(COR.perna, op), r, e)
  bloco(p, alfa(cor, op), b.corpo, e)
  for (const r of b.bracos) bloco(p, alfa(cor, op), r, e)
  bloco(p, alfa(cor, op), b.cabeca, e)
  const c = b.cabeca
  const olho = c.largura / 4
  ret(p, alfa(COR.olho, op), c.x + olho * 0.6, c.y + c.altura * 0.4, olho, olho, e)
  ret(p, alfa(COR.olho, op), c.x + c.largura - olho * 1.6, c.y + c.altura * 0.4, olho, olho, e)
}

/** Console da estação: aceso (tela clara e brilho na cor da divisão) ou apagado. */
function desenhaConsole(p: Pincel, r: Caixa, cor: string, aceso: boolean, op: number, e: number): void {
  bloco(p, alfa(COR.console, op), r, e)
  if (aceso) {
    bloco(p, cor, { x: r.x + 0.4, y: r.y + 0.2, largura: r.largura - 0.8, altura: r.altura - 0.4 }, e)
    ret(p, COR.tela, r.x + r.largura / 2 - 0.6, r.y + 0.2, 1.2, r.altura - 0.4, e)
  }
}

/** Desenha a cena inteira; `escala` é o número de pixels do canvas por célula da grade. */
export function paint(ctx: Pincel, cena: Cena, escala: number): void {
  const e = escala
  const { largura, altura } = cena.grade
  ret(ctx, COR.fundo, 0, 0, largura, altura, e)
  if (cena.vazia) {
    for (const r of cena.rotulos) texto(ctx, r, e)
    return
  }

  // piso da ponte: chapas, anel do console em volta da cadeira e plataforma central
  const pt = cena.ponte
  bloco(ctx, COR.piso, pt, e)
  for (let y = pt.y + 2; y < pt.y + pt.altura; y += 4) ret(ctx, COR.pisoLinha, pt.x, y, pt.largura, 0.4, e)
  const picard = cena.personagens.find(c => c.membro === 'picard')
  if (picard && cena.personagens.length > 1) {
    // o anel ocupa a caixa `anel` do modelo (toda a altura da ponte) e estica com ela
    const a = cena.anel
    const rx = a.largura / 2
    const ry = a.altura / 2
    const cx = a.x + rx
    const cy = a.y + ry
    elipse(ctx, COR.anelBorda, cx, cy, rx, ry, e)
    elipse(ctx, COR.anel, cx, cy, rx - 0.5, ry - 0.6, e)
    elipse(ctx, COR.piso, cx, cy, rx - 10, Math.max(4, ry - 11), e)
    elipse(ctx, COR.plataforma, picard.x, picard.y, 7, 7, e)
  }

  // telão: moldura e barra de progresso
  caixa(ctx, COR.telao, COR.telaoBorda, cena.telao, e)
  if (cena.progresso) {
    const b = cena.progresso.barra
    caixa(ctx, COR.barraFundo, COR.borda, b, e)
    ret(ctx, COR.barra, b.x, b.y, (b.largura * Math.min(100, Math.max(0, cena.progresso.percentual))) / 100, b.altura, e)
  }

  // engenharia: só os workers reais, cada um um boneco no seu console
  if (cena.engenharia.altura > 0) caixa(ctx, COR.engenharia, COR.engenhariaBorda, cena.engenharia, e)
  for (const w of cena.workers) {
    bloco(ctx, w.concluido ? COR.vagaOk : COR.vaga, w.caixa, e)
    if (w.pose === 'de-pe') desenhaConsole(ctx, w.console, CORES.operacoes, false, 1, e)
    desenhaBoneco(ctx, w.boneco, CORES.operacoes, 1, e)
    if (w.pose === 'sentado') desenhaConsole(ctx, w.console, CORES.operacoes, true, 1, e)
  }

  // tripulantes: o ativo senta no console aceso; o livre fica de pé, a 40% da opacidade
  const rotulosDe = (c: { membro: string }) => cena.rotulos.filter(r => r.dono === c.membro)
  for (const c of cena.personagens) {
    const op = c.opacidade
    if (c.membro === 'picard') {
      const s = c.escala
      ret(ctx, alfa(COR.cadeira, op), c.x - 2.4 * s, c.y - 3.4 * s, 4.8 * s, 4.2 * s, e)
    }
    if (c.brilho) bloco(ctx, alfa(c.cor, 0.35), c.brilho, e)
    if (c.pose === 'de-pe') desenhaConsole(ctx, c.console, c.cor, c.ativo, op, e)
    desenhaBoneco(ctx, c.boneco, c.cor, op, e)
    if (c.pose === 'sentado') desenhaConsole(ctx, c.console, c.cor, c.ativo, op, e)
    for (const r of rotulosDe(c)) {
      if (r.tipo === 'balao') bloco(ctx, COR.balao, r.caixa, e)
      texto(ctx, r, e, r.tipo === 'balao' ? 1 : op)
    }
  }

  // demais rótulos: telão, engenharia, workers, marcas, legenda
  for (const r of cena.rotulos) {
    if (r.dono) continue
    if (r.tipo === 'balao') bloco(ctx, COR.balao, r.caixa, e)
    texto(ctx, r, e)
  }
}

/** Tamanho do canvas para um palco de `larguraPx` x `alturaPx`: escala inteira e linhas na proporção do palco. */
export function dimensoes(larguraPx: number, alturaPx: number): { escala: number; linhas: number; largura: number; altura: number } {
  const escala = Math.max(5, Math.floor((larguraPx || 0) / GRADE.largura)) // nunca abaixo de 240 px de largura
  const linhas = linhasDoPainel(larguraPx, alturaPx)
  return { escala, linhas, largura: GRADE.largura * escala, altura: linhas * escala }
}

// ---- ligação com o frame do painel (só roda dentro do Orca) ----

interface OrcaFrame {
  on(evento: string, cb: (dados: unknown) => void): unknown
  plugin: {
    request(nome: string, dados?: unknown, opcoes?: unknown): Promise<unknown>
    on(nome: string, cb: (dados: unknown) => void): unknown
  }
}

function iniciar(orca: OrcaFrame, canvas: HTMLCanvasElement): void {
  const ctx = canvas.getContext('2d') as unknown as Pincel | null
  if (!ctx) return
  let estado: PonteState | null = null
  let agentes: PonteAgent[] = []
  let escala = 1
  let linhas: number = GRADE.altura
  let sujo = true

  // mede o palco (largura e altura do painel) e redesenha quando ele muda de tamanho (R54)
  const ajustar = (): void => {
    const palco = canvas.parentElement
    const g = globalThis as { innerWidth?: number; innerHeight?: number }
    const d = dimensoes(palco?.clientWidth || g.innerWidth || 360, palco?.clientHeight || g.innerHeight || 0)
    escala = d.escala
    linhas = d.linhas
    if (canvas.width !== d.largura) canvas.width = d.largura
    if (canvas.height !== d.altura) canvas.height = d.altura
    sujo = true
  }
  const receber = (s: unknown): void => {
    estado = s as PonteState
    agentes = estado.agents ?? agentes
    sujo = true
  }

  orca.plugin.on('ponte.state', receber)
  orca.on('agent.status.changed', () => { sujo = true })
  void orca.plugin.request('ponte.state', {}, { timeoutMs: 15000 }).then(receber, () => { sujo = true })
  new ResizeObserver(ajustar).observe(canvas.parentElement ?? canvas)
  ajustar()

  let ultimoQuadro = -1
  const laco = (agora: number): void => {
    const quadro = Math.floor(agora / 250)
    if (sujo || quadro !== ultimoQuadro) {
      sujo = false
      ultimoQuadro = quadro
      const vazio: PonteState = {
        status: 'sem-worktree', stale: false, updatedAt: 0, issue: null, issueNote: null,
        agents: [], log: [], error: null, snapshot: null,
      }
      paint(ctx, buildScene(estado ?? vazio, agentes, Date.now(), linhas), escala)
    }
    requestAnimationFrame(laco)
  }
  requestAnimationFrame(laco)
}

/** O mínimo do documento que a ligação usa (permite um documento falso nos testes). */
export interface Pagina {
  getElementById(id: string): unknown
  createElement(tag: string): any
  body: { appendChild(n: unknown): unknown }
}

/** Devolve o canvas `#cena` da página; quando a Orca gera a página em volta, cria o canvas no corpo (R45). */
export function obterCanvas(doc: Pagina): HTMLCanvasElement {
  const existente = doc.getElementById('cena')
  if (existente) return existente as HTMLCanvasElement
  const corpo = doc.body as { style?: Record<string, string> }
  if (corpo.style) corpo.style.margin = '0' // o palco mede o painel inteiro, sem a margem padrão
  const palco = doc.createElement('div')
  palco.id = 'palco'
  palco.style.width = '100%'
  palco.style.height = '100vh' // a altura do painel define as linhas da grade (R54)
  palco.style.overflow = 'auto' // painel mais baixo que o mínimo de linhas rola em vez de cortar
  const canvas = doc.createElement('canvas')
  canvas.id = 'cena'
  canvas.width = GRADE.largura * 5
  canvas.height = GRADE.altura * 5
  canvas.style.minWidth = '240px'
  canvas.style.display = 'block'
  canvas.style.width = '100%'
  canvas.style.height = 'auto'
  canvas.style.imageRendering = 'pixelated'
  palco.appendChild(canvas)
  doc.body.appendChild(palco)
  return canvas as HTMLCanvasElement
}

const frame = (globalThis as { orca?: OrcaFrame }).orca
if (frame && typeof document !== 'undefined') iniciar(frame, obterCanvas(document))
