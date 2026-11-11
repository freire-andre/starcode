// Painel HTML "ponte-cena": desenha a cena da Ponte num canvas. Lê só o resultado de buildScene (R43)
// e só usa fillRect/fillText/strokeRect: nenhuma imagem nem arquivo de arte (R38).
import { buildScene, GRADE } from './scene-model.ts'
import type { Cena, Rotulo, TipoRotulo } from './scene-model.ts'
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
  pisoAlt: '#161d38',
  telao: '#0f2238',
  telaoBorda: '#58a6c9',
  barraFundo: '#1d2a44',
  barra: '#2ecc71',
  estacao: '#232c4d',
  estacaoAtiva: '#34457a',
  borda: '#5b6aa0',
  bordaAtiva: '#ffd866',
  cadeira: '#3a4670',
  engenharia: '#2a2230',
  engenhariaBorda: '#c97a58',
  vaga: '#3a2a3e',
  vagaOk: '#1f4d36',
  pele: '#f1c9a0',
  texto: '#e8ecff',
  balao: '#ffffff',
  balaoTexto: '#c0392b',
  ok: '#2ecc71',
  mensagem: '#9aa7d8',
  legenda: '#9aa7d8',
  apagado: 'rgba(11,16,32,0.6)',
}

const COR_TEXTO: Record<TipoRotulo, string> = {
  telao: COR.texto,
  emoji: COR.texto,
  nome: COR.texto,
  worker: COR.texto,
  marca: COR.ok,
  balao: COR.balaoTexto,
  legenda: COR.legenda,
  mensagem: COR.mensagem,
}

type Caixa = { x: number; y: number; largura: number; altura: number }

function ret(p: Pincel, cor: string, x: number, y: number, w: number, h: number, e: number): void {
  p.fillStyle = cor
  p.fillRect(x * e, y * e, w * e, h * e)
}

function caixa(p: Pincel, cor: string, borda: string, r: Caixa, e: number): void {
  ret(p, cor, r.x, r.y, r.largura, r.altura, e)
  p.strokeStyle = borda
  p.lineWidth = Math.max(1, e / 2)
  p.strokeRect(r.x * e, r.y * e, r.largura * e, r.altura * e)
}

function texto(p: Pincel, r: Rotulo, e: number, dy = 0): void {
  p.fillStyle = COR_TEXTO[r.tipo]
  p.font = `${Math.max(6, Math.round(r.tam * e))}px system-ui, sans-serif`
  p.textAlign = 'center'
  p.textBaseline = 'middle'
  p.fillText(r.texto, r.x * e, (r.y + dy) * e)
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
  if (cena.vazia) {
    for (const r of cena.rotulos) texto(ctx, r, e)
    return
  }

  // telão: moldura e barra de progresso
  caixa(ctx, COR.telao, COR.telaoBorda, cena.telao, e)
  if (cena.progresso) {
    const b = cena.progresso.barra
    caixa(ctx, COR.barraFundo, COR.borda, b, e)
    ret(ctx, COR.barra, b.x, b.y, (b.largura * Math.min(100, Math.max(0, cena.progresso.percentual))) / 100, b.altura, e)
  }

  // faixa da engenharia e vagas de worker
  caixa(ctx, COR.engenharia, COR.engenhariaBorda, cena.engenharia, e)
  for (const v of cena.vagas) caixa(ctx, COR.estacao, COR.borda, v, e)
  for (const w of cena.workers) caixa(ctx, w.concluido ? COR.vagaOk : COR.vaga, COR.engenhariaBorda, w.caixa, e)

  // estações: ladrilho, cadeira do Picard, tronco na cor da divisão; inativo fica esmaecido e parado
  const rotulosDe = (c: { membro: string }) => cena.rotulos.filter(r => r.dono === c.membro)
  for (const c of cena.personagens) {
    const ladoAlto = c.caixa.altura > 4
    caixa(ctx, c.ativo ? COR.estacaoAtiva : COR.estacao, c.ativo ? COR.bordaAtiva : COR.borda, c.caixa, e)
    const balanco = c.ativo && c.quadro === 1 ? -0.3 : 0
    if (c.membro === 'picard') ret(ctx, COR.cadeira, c.x - 3.5, c.y + 1.2, 7, 1.2, e)
    if (ladoAlto) {
      // tronco (ombros e corpo) sob o emoji, que faz de rosto
      ret(ctx, c.cor, c.x - 1.5, c.y + 1.3 + balanco, 3, 1, e)
      ret(ctx, COR.pele, c.x - 0.4, c.y + 1.1 + balanco, 0.8, 0.4, e)
    }
    for (const r of rotulosDe(c)) {
      if (r.tipo === 'balao') ret(ctx, COR.balao, r.caixa.x, r.caixa.y, r.caixa.largura, r.caixa.altura, e)
      texto(ctx, r, e, r.tipo === 'emoji' ? balanco : 0)
    }
    if (!c.ativo) ret(ctx, COR.apagado, c.caixa.x, c.caixa.y, c.caixa.largura, c.caixa.altura, e)
  }

  // demais rótulos: telão, engenharia, workers, marcas, legenda
  for (const r of cena.rotulos) {
    if (r.dono) continue
    if (r.tipo === 'balao') {
      ret(ctx, COR.balao, r.caixa.x, r.caixa.y, r.caixa.largura, r.caixa.altura, e)
    }
    texto(ctx, r, e)
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
    escala = Math.max(5, Math.floor(largura / GRADE.largura)) // nunca abaixo de 240 px de largura
    canvas.width = GRADE.largura * escala
    canvas.height = GRADE.altura * escala
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
