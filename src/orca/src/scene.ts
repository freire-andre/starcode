// Painel HTML "ponte-cena": desenha a cena da Ponte num canvas. Lê só o resultado de buildScene (R43)
// e só usa fillRect/fillText/strokeRect: nenhuma imagem nem arquivo de arte (R38).
import { buildScene } from './scene-model.ts'
import type { Cena } from './scene-model.ts'
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
  piso: '#151c33',
  pisoAlt: '#1a2240',
  console: '#2b3558',
  consoleTopo: '#3a4670',
  estacao: '#232c4d',
  borda: '#5b6aa0',
  turbolift: '#243a4a',
  turboliftBorda: '#58a6c9',
  engenharia: '#2e2430',
  engenhariaBorda: '#c97a58',
  pele: '#f1c9a0',
  texto: '#e8ecff',
  balao: '#ffffff',
  balaoTexto: '#c0392b',
  ok: '#2ecc71',
  mensagem: '#9aa7d8',
}

function ret(p: Pincel, cor: string, x: number, y: number, w: number, h: number, e: number): void {
  p.fillStyle = cor
  p.fillRect(x * e, y * e, w * e, h * e)
}

function texto(p: Pincel, t: string, cor: string, x: number, y: number, tam: number, e: number): void {
  p.fillStyle = cor
  p.font = `${Math.max(6, Math.round(tam * e))}px system-ui, sans-serif`
  p.textAlign = 'center'
  p.textBaseline = 'middle'
  p.fillText(t, x * e, y * e)
}

function caixa(p: Pincel, cor: string, borda: string, r: { x: number; y: number; largura: number; altura: number }, e: number): void {
  ret(p, cor, r.x, r.y, r.largura, r.altura, e)
  p.strokeStyle = borda
  p.lineWidth = Math.max(1, e / 2)
  p.strokeRect(r.x * e, r.y * e, r.largura * e, r.altura * e)
}

/** Desenha a cena inteira; `escala` é o número de pixels do canvas por célula da grade. */
export function paint(ctx: Pincel, cena: Cena, escala: number): void {
  const e = escala
  const { largura, altura } = cena.grade
  ret(ctx, COR.fundo, 0, 0, largura, altura, e)
  // piso xadrez
  for (let y = 0; y < altura; y += 4) {
    for (let x = 0; x < largura; x += 4) {
      ret(ctx, ((x + y) / 4) % 2 === 0 ? COR.piso : COR.pisoAlt, x, y, 4, 4, e)
    }
  }
  caixa(ctx, COR.turbolift, COR.turboliftBorda, cena.turbolift, e)
  texto(ctx, 'TURBOLIFT', COR.texto, cena.turbolift.x + cena.turbolift.largura / 2, cena.turbolift.y + 1.2, 1.6, e)
  caixa(ctx, COR.engenharia, COR.engenhariaBorda, cena.engenharia, e)
  texto(ctx, 'ENGENHARIA', COR.texto, cena.engenharia.x + cena.engenharia.largura / 2, cena.engenharia.y + 1.5, 1.8, e)

  // consoles (ponte central) e estações
  caixa(ctx, COR.console, COR.borda, { x: 26, y: 17, largura: 12, altura: 3 }, e)
  ret(ctx, COR.consoleTopo, 27, 17.5, 10, 1, e)
  for (const s of cena.estacoes) {
    caixa(ctx, COR.estacao, COR.borda, { x: s.x - 2, y: s.y - 1, largura: 4, altura: 3 }, e)
  }

  for (const w of cena.workers) {
    caixa(ctx, w.concluido ? '#1f4d36' : '#3a2a3e', COR.engenhariaBorda, { x: w.x - 2, y: w.y - 1.5, largura: 4, altura: 3 }, e)
    texto(ctx, w.rotulo.slice(0, 7), COR.texto, w.x, w.y + 2.8, 1.3, e)
    if (w.concluido) texto(ctx, '✓', COR.ok, w.x, w.y, 2.4, e)
    if (w.balao) texto(ctx, '!', COR.balaoTexto, w.x + 2, w.y - 2, 2.6, e)
  }

  for (const c of cena.personagens) {
    const sentado = c.pose === 'sentado'
    const balanco = sentado && c.quadro === 1 ? -0.5 : 0
    const alturaCorpo = sentado ? 2 : 3
    // corpo em retângulos de pixel: cabeça, tronco, pernas
    ret(ctx, COR.pele, c.x - 0.5, c.y - 2.5 + balanco, 1, 1, e)
    ret(ctx, c.cor, c.x - 1, c.y - 1.5 + balanco, 2, alturaCorpo - 1, e)
    if (!sentado) ret(ctx, '#222', c.x - 1, c.y + 0.5, 2, 1, e)
    texto(ctx, c.emoji, COR.texto, c.x, c.y - 4 + balanco, 2.2, e)
    texto(ctx, c.nome, COR.texto, c.x, c.y + 2.2, 1.3, e)
    if (c.balao) {
      ret(ctx, COR.balao, c.x + 1, c.y - 5.5, 1.6, 2, e)
      texto(ctx, '!', COR.balaoTexto, c.x + 1.8, c.y - 4.5, 2, e)
    }
  }

  if (cena.maisN > 0) {
    texto(ctx, `+${cena.maisN}`, COR.engenhariaBorda, cena.engenharia.x + cena.engenharia.largura - 3, cena.engenharia.y + cena.engenharia.altura - 2, 2.2, e)
  }
  if (cena.mensagem) {
    texto(ctx, cena.mensagem, COR.mensagem, largura / 2, altura / 2, 2.4, e)
  }
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
  let sujo = true

  const ajustar = (): void => {
    const largura = canvas.parentElement?.clientWidth || 360
    escala = Math.max(1, Math.floor(largura / 64))
    canvas.width = 64 * escala
    canvas.height = 40 * escala
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
      paint(ctx, buildScene(estado ?? vazio, agentes, Date.now()), escala)
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
  const palco = doc.createElement('div')
  palco.id = 'palco'
  palco.style.width = '100%'
  const canvas = doc.createElement('canvas')
  canvas.id = 'cena'
  canvas.width = 64
  canvas.height = 40
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
