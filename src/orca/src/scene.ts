// Painel HTML "ponte-cena": desenha a cena da Ponte num canvas. Lê só o resultado de buildScene (R43)
// e só usa fillRect/fillText/strokeRect: nenhuma imagem nem arquivo de arte (R38).
import { identidadesDaSessao } from './crew-visual.ts'
import { avisoDeDados, buildScene, CORES, criaRastroPresenca, GRADE, linhasDoPainel, relacaoDaTripulacao } from './scene-model.ts'
import type { Boneco, Cena, ItemRelacao, OpcoesCena, Peca, Rotulo, TipoRotulo } from './scene-model.ts'
import type { EstadoVisual } from './crew-visual.ts'
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
  contorno: '#05070f',
  mesa: '#1c2750',
  mesaBorda: '#2f7a9c',
  faixa: '#18214a',
  perigo: '#d4a017',
  holo: '#1f6f8f',
  holoClaro: '#5fd3ff',
  capacete: '#f1c40f',
  caixote: '#6b5b4b',
  casco: '#1a2246',
  cascoLuz: '#4a5ca0',
  cascoMeio: '#26315f',
  janela: '#070b1c',
  estrela: '#e8ecff',
  planeta: '#2e5d8f',
  luz: '#e67e22',
  painel: '#101a30',
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
  estado: COR.texto,
  atividade: COR.texto,
  worker: COR.texto,
  marca: COR.ok,
  balao: COR.balaoTexto,
  legenda: COR.legenda,
  mensagem: COR.mensagem,
}

/** Cor do estado na placa do nome e no selo do símbolo, como os cartões de estado da referência (a cor reforça, não substitui, o símbolo). */
export const COR_ESTADO: Record<EstadoVisual, string> = {
  trabalhando: '#3ec9ff',
  aguardando: '#f1c40f',
  bloqueado: '#ff5a4d',
  concluido: '#2ecc71',
  ocioso: '#6b7699',
  desconhecido: '#8a94b8',
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

/** Boneco: pernas, corpo e braços no uniforme, cabeça na cor da pele, dois olhos e as peças do perfil. */
function desenhaBoneco(p: Pincel, b: Boneco, cor: string, op: number, e: number, pele = cor, pecas: Peca[] = []): void {
  for (const r of [...b.pernas, b.corpo, ...b.bracos, b.cabeca]) {
    bloco(p, alfa(COR.contorno, op), { x: r.x - 0.25, y: r.y - 0.25, largura: r.largura + 0.5, altura: r.altura + 0.5 }, e)
  }
  for (const r of b.pernas) bloco(p, alfa(COR.perna, op), r, e)
  bloco(p, alfa(cor, op), b.corpo, e)
  for (const r of b.bracos) bloco(p, alfa(cor, op), r, e)
  bloco(p, alfa(pele, op), b.cabeca, e)
  const c = b.cabeca
  const olho = c.largura / 4
  ret(p, alfa(COR.olho, op), c.x + olho * 0.6, c.y + c.altura * 0.4, olho, olho, e)
  ret(p, alfa(COR.olho, op), c.x + c.largura - olho * 1.6, c.y + c.altura * 0.4, olho, olho, e)
  for (const r of pecas) bloco(p, alfa(r.cor, op), r, e)
}

/** Console da estação: aceso (tela clara e brilho na cor da divisão) ou apagado. */
function desenhaConsole(p: Pincel, r: Caixa, cor: string, aceso: boolean, op: number, e: number): void {
  bloco(p, alfa(COR.console, op), r, e)
  if (aceso) {
    bloco(p, cor, { x: r.x + 0.4, y: r.y + 0.2, largura: r.largura - 0.8, altura: r.altura - 0.4 }, e)
    ret(p, COR.tela, r.x + r.largura / 2 - 0.6, r.y + 0.2, 1.2, r.altura - 0.4, e)
  }
}

/** Octógono (retângulo com os quatro cantos chanfrados) em degraus de 1 célula, só com fillRect. */
function octogono(p: Pincel, cor: string, r: Caixa, ch: number, e: number): void {
  for (let dy = 0; dy < r.altura; dy += 1) {
    const h = Math.min(1, r.altura - dy)
    const inset = Math.max(0, ch - Math.min(dy + 0.5, r.altura - dy - 0.5))
    ret(p, cor, r.x + inset, r.y + dy, r.largura - inset * 2, h, e)
  }
}

const dentro = (r: Caixa, d: number): Caixa => ({ x: r.x + d, y: r.y + d, largura: r.largura - d * 2, altura: r.altura - d * 2 })

/** Desenha a cena inteira; `escala` é o número de pixels do canvas por célula da grade. */
export function paint(ctx: Pincel, cena: Cena, escala: number): void {
  const e = escala
  const { largura, altura } = cena.grade
  ret(ctx, COR.fundo, 0, 0, largura, altura, e)
  if (cena.vazia) {
    for (const r of cena.rotulos) texto(ctx, r, e)
    return
  }

  // sala da ponte: casco em octógono com bordas em volume, piso em chapas, janela com estrelas e luzes
  const pt = cena.ponte
  octogono(ctx, COR.casco, pt, 9, e)
  octogono(ctx, COR.cascoLuz, dentro(pt, 0.5), 8.6, e)
  octogono(ctx, COR.cascoMeio, dentro(pt, 1.2), 8, e)
  octogono(ctx, COR.piso, dentro(pt, 2.2), 7.2, e)
  const pisoR = dentro(pt, 2.2)
  const largEm = (y: number): [number, number] => {
    const inset = Math.max(0, 7.2 - Math.min(y - pisoR.y, pisoR.y + pisoR.altura - y)) + 0.6
    return [pisoR.x + inset, pisoR.largura - inset * 2]
  }
  for (let y = pisoR.y + 9; y < pisoR.y + pisoR.altura - 1; y += 4) {
    const [x0, w] = largEm(y)
    ret(ctx, COR.pisoLinha, x0, y, w, 0.4, e)
  }
  for (let x = pisoR.x + 4; x < pisoR.x + pisoR.largura - 2; x += 6) {
    const topo = pisoR.y + 9
    const base = pisoR.y + pisoR.altura - 1
    const corte = (xx: number): number => Math.max(0, 7.2 - Math.min(xx - pisoR.x, pisoR.x + pisoR.largura - xx)) * 0.9
    ret(ctx, COR.pisoLinha, x, topo + corte(x), 0.4, base - topo - corte(x) * 2, e)
  }
  const janela = { x: pt.x + 9, y: pt.y + 2.6, largura: pt.largura - 18, altura: 5.2 }
  caixa(ctx, COR.janela, COR.telaoBorda, janela, e)
  for (let n = 0; n < 16; n++) {
    ret(ctx, n % 3 === 0 ? COR.tempo : COR.estrela, janela.x + 1 + ((n * 7) % 26), janela.y + 0.8 + ((n * 5) % 4), 0.4, 0.4, e)
  }
  elipse(ctx, COR.planeta, janela.x + janela.largura - 5, janela.y + janela.altura - 2.4, 3.2, 2, e)
  for (const y of [pt.y + 22, pt.y + 38, pt.y + 54]) {
    ret(ctx, COR.luz, pt.x + 1.5, y, 0.8, 3, e)
    ret(ctx, COR.luz, pt.x + pt.largura - 2.3, y, 0.8, 3, e)
  }
  const picard = cena.estacoes.find(c => c.membro === 'picard')
  if (picard && cena.estacoes.length > 1) {
    // centro: plataforma do capitão e corredor de faixas até o acesso, sem ficar vazio
    const cx = picard.x
    const faixaTopo = picard.y + 12
    const faixaBase = cena.porta.y
    if (faixaBase > faixaTopo) {
      ret(ctx, COR.faixa, cx - 1.6, faixaTopo, 3.2, faixaBase - faixaTopo, e)
      for (let y = faixaTopo; y < faixaBase - 1; y += 2) {
        const cor = ((y - faixaTopo) / 2) % 2 === 0 ? COR.perigo : COR.contorno
        ret(ctx, cor, cx - 1.6, y, 0.6, 1.6, e)
        ret(ctx, cor, cx + 1, y, 0.6, 1.6, e)
      }
    }
    elipse(ctx, COR.plataforma, picard.x, picard.y - 1, 9, 8, e)
    elipse(ctx, COR.cascoMeio, picard.x, picard.y - 1, 7, 6, e)
    elipse(ctx, COR.holo, picard.x, picard.y - 1, 5, 4.2, e)
    elipse(ctx, COR.plataforma, picard.x, picard.y - 1, 4, 3.3, e)
    ret(ctx, COR.holoClaro, picard.x - 5, picard.y - 1.2, 10, 0.4, e)
    ret(ctx, COR.holoClaro, picard.x - 0.2, picard.y - 5, 0.4, 8, e)
  }
  // acesso à ponte
  ret(ctx, COR.contorno, cena.porta.x - 3, cena.porta.y - 0.6, 6, 2.2, e)
  ret(ctx, COR.holoClaro, cena.porta.x - 3, cena.porta.y - 0.6, 6, 0.4, e)

  // mesas: cada estação é uma bancada integrada ao arco, com tampo iluminado e frente escura
  for (const est of cena.estacoes) {
    const c = est.console
    ret(ctx, COR.contorno, c.x - 1.5, c.y - 0.9, c.largura + 3, c.altura + 2.8, e)
    ret(ctx, COR.mesa, c.x - 1.2, c.y - 0.6, c.largura + 2.4, c.altura + 2.2, e)
    ret(ctx, COR.mesaBorda, c.x - 1.2, c.y - 0.6, c.largura + 2.4, 0.4, e)
    ret(ctx, COR.cascoMeio, c.x - 1.2, c.y + c.altura + 1, c.largura + 2.4, 0.6, e)
  }

  // estações sem ninguém presente: console apagado e cadeira do capitão (quem está presente desenha o seu)
  const presentes = new Set(cena.personagens.map(c => c.membro))
  for (const est of cena.estacoes) {
    if (presentes.has(est.membro)) continue
    if (est.membro === 'picard') ret(ctx, alfa(COR.cadeira, 0.5), est.x - 2.4 * est.escala, est.y - 3.4 * est.escala, 4.8 * est.escala, 4.2 * est.escala, e)
    desenhaConsole(ctx, est.console, COR.console, false, 0.5, e)
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
  if (cena.atividades) caixa(ctx, COR.painel, COR.telaoBorda, cena.atividades, e)
  if (cena.engenharia.altura > 0) {
    const g = cena.engenharia
    for (let x = g.x + 1; x < g.x + g.largura - 2; x += 2) ret(ctx, ((x - g.x) / 2) % 2 < 1 ? COR.perigo : COR.contorno, x, g.y + g.altura - 1.2, 1.2, 0.8, e)
    for (const dx of [1.2, g.largura - 5]) {
      ret(ctx, COR.caixote, g.x + dx, g.y + g.altura - 4.2, 3.6, 3, e)
      ret(ctx, COR.contorno, g.x + dx + 1.6, g.y + g.altura - 4.2, 0.4, 3, e)
    }
  }
  for (const w of cena.workers) {
    bloco(ctx, w.concluido ? COR.vagaOk : COR.vaga, w.caixa, e)
    if (w.pose === 'de-pe') desenhaConsole(ctx, w.console, CORES.operacoes, false, 1, e)
    desenhaBoneco(ctx, w.boneco, CORES.operacoes, 1, e, '#e0b48a', [
      { cor: COR.capacete, x: w.boneco.cabeca.x - 0.2, y: w.boneco.cabeca.y - 0.5, largura: w.boneco.cabeca.largura + 0.4, altura: 0.9 },
      { cor: COR.capacete, x: w.boneco.cabeca.x + 0.2, y: w.boneco.cabeca.y - 0.9, largura: w.boneco.cabeca.largura - 0.4, altura: 0.5 },
    ])
    if (w.pose === 'sentado') desenhaConsole(ctx, w.console, CORES.operacoes, true, 1, e)
  }

  // tripulantes: o ativo senta no console aceso; o livre fica de pé, a 40% da opacidade
  const rotulosDe = (c: { membro: string }) => cena.rotulos.filter(r => r.dono === c.membro)
  for (const c of cena.personagens) {
    const op = c.opacidade
    if (c.membro === 'picard') {
      const s = c.escala
      ret(ctx, alfa(COR.cadeira, op), c.estacao.x - 2.4 * s, c.estacao.y - 3.4 * s, 4.8 * s, 4.2 * s, e)
    }
    if (c.brilho) bloco(ctx, alfa(c.cor, 0.35), c.brilho, e)
    const consoleOp = c.transicao ? 1 : op
    if (c.pose === 'de-pe') desenhaConsole(ctx, c.console, c.cor, c.ativo, consoleOp, e)
    desenhaBoneco(ctx, c.boneco, c.cor, op, e, c.pele, c.pecas)
    if (c.pose === 'sentado') desenhaConsole(ctx, c.console, c.cor, c.ativo, consoleOp, e)
    const meus = rotulosDe(c)
    const nomes = meus.filter(r => r.tipo === 'nome')
    if (nomes.length > 0) {
      // placa escura atrás do nome: contraste garantido sobre qualquer fundo; a borda leva a cor do estado
      const x0 = Math.max(0, Math.min(...nomes.map(r => r.caixa.x)) - 0.3)
      const x1 = Math.min(cena.grade.largura, Math.max(...nomes.map(r => r.caixa.x + r.caixa.largura)) + 0.3)
      const y0 = Math.min(...nomes.map(r => r.caixa.y)) + 0.1
      const y1 = Math.max(...nomes.map(r => r.caixa.y + r.caixa.altura)) - 0.1
      const placa = { x: x0, y: y0, largura: x1 - x0, altura: y1 - y0 }
      bloco(ctx, alfa(COR.painel, 0.9 * c.opacidadeTexto), placa, e)
      ctx.strokeStyle = alfa(COR_ESTADO[c.estado], c.opacidadeTexto)
      ctx.lineWidth = Math.max(1, e / 2)
      ctx.strokeRect(placa.x * e, placa.y * e, placa.largura * e, placa.altura * e)
    }
    for (const r of meus) {
      if (r.tipo === 'estado') {
        // selo do símbolo de estado na cor do estado: legível mesmo com o boneco apagado
        const lado = Math.max(r.caixa.largura, r.caixa.altura) + 0.4
        const selo = { x: r.x - lado / 2, y: r.y - lado / 2, largura: lado, altura: lado }
        caixa(ctx, alfa(COR.painel, 0.95 * c.opacidadeTexto), alfa(COR_ESTADO[c.estado], c.opacidadeTexto), selo, e)
      }
      if (r.tipo === 'balao') bloco(ctx, alfa(COR.balao, c.opacidadeTexto), r.caixa, e)
      texto(ctx, r, e, c.opacidadeTexto)
    }
  }

  // demais rótulos: telão, engenharia, workers, marcas, legenda
  for (const r of cena.rotulos) {
    if (r.dono) continue
    if (r.tipo === 'balao') bloco(ctx, COR.balao, r.caixa, e)
    texto(ctx, r, e)
  }
}

export interface Dimensoes {
  /** Pixels do canvas por célula (escala inteira, no mínimo 5). */
  escala: number
  linhas: number
  /** Tamanho interno do canvas (linhas x escala). */
  largura: number
  altura: number
  /** Tamanho exibido, em px CSS: cabe no palco nas duas dimensões, arredondado para baixo. */
  cssLargura: number
  cssAltura: number
}

/**
 * Tamanho do canvas para um palco de `larguraPx` x `alturaPx`: escala inteira, linhas na proporção do palco
 * e um tamanho exibido que nunca passa do palco. Quando o palco é mais baixo que a proporção mínima da grade
 * (GRADE.altura linhas), a célula encolhe para caber na altura e o canvas fica centrado na largura.
 */
export function dimensoes(larguraPx: number, alturaPx: number): Dimensoes {
  const w = larguraPx > 0 ? larguraPx : GRADE.largura * 5
  const escala = Math.max(5, Math.floor(w / GRADE.largura))
  const linhas = linhasDoPainel(w, alturaPx)
  let celula = w / GRADE.largura
  if (alturaPx > 0 && linhas * celula > alturaPx) celula = alturaPx / linhas
  return {
    escala, linhas,
    largura: GRADE.largura * escala, altura: linhas * escala,
    cssLargura: Math.floor(GRADE.largura * celula), cssAltura: Math.floor(linhas * celula),
  }
}

/** Mede o palco e ajusta o canvas a ele: tamanho interno e tamanho exibido em px (sem `height: auto`). */
export function ajustaCanvas(
  canvas: { width: number; height: number; style: Record<string, string> },
  palco: { clientWidth: number; clientHeight: number } | null,
): Dimensoes {
  const g = globalThis as { innerWidth?: number; innerHeight?: number }
  const d = dimensoes(palco?.clientWidth || g.innerWidth || 0, palco?.clientHeight || g.innerHeight || 0)
  if (canvas.width !== d.largura) canvas.width = d.largura
  if (canvas.height !== d.altura) canvas.height = d.altura
  canvas.style.width = `${d.cssLargura}px`
  canvas.style.height = `${d.cssAltura}px`
  return d
}

// ---- ligação com o frame do painel (só roda dentro do Orca) ----

interface OrcaFrame {
  on(evento: string, cb: (dados: unknown) => void): unknown
  plugin: {
    request(nome: string, dados?: unknown, opcoes?: unknown): Promise<unknown>
    on(nome: string, cb: (dados: unknown) => void): unknown
  }
}

function iniciar(orca: OrcaFrame, canvas: HTMLCanvasElement, relacao: Relacao | null): void {
  const ctx = canvas.getContext('2d') as unknown as Pincel | null
  if (!ctx) return
  let estado: PonteState | null = null
  let agentes: PonteAgent[] = []
  let escala = 1
  let linhas: number = GRADE.altura
  let sujo = true
  let selecionado: string | null = null
  // a presença lembra quem está na ponte entre as atualizações: só mudança real de estado ou seleção troca alguém (R3, R18)
  const rastro = criaRastroPresenca()
  const preferencia = preferenciaDeMovimento()
  preferencia.aoMudar(() => { sujo = true })
  relacao?.aoSelecionar(membro => {
    selecionado = selecionado === membro ? null : membro
    sujo = true
  })

  // mede o palco (largura e altura do painel) e redesenha quando ele muda de tamanho (R54)
  const ajustar = (): void => {
    const d = ajustaCanvas(canvas as unknown as Parameters<typeof ajustaCanvas>[0], canvas.parentElement)
    escala = d.escala
    linhas = d.linhas
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
      const agora = Date.now()
      const atual = estado ?? vazio
      const opcoes: OpcoesCena = { reduzido: preferencia.reduzido(), selecionado, rastro }
      const ids = identidadesDaSessao(atual, agentes)
      paint(ctx, buildScene(atual, agentes, agora, linhas, ids, opcoes), escala)
      relacao?.atualiza(relacaoDaTripulacao(atual, agentes, agora, ids, opcoes), avisoDeDados(atual))
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
  documentElement?: unknown
}

type ComEstilo = { style?: Record<string, string> }

// ---- movimento reduzido (R17) ----

/** Preferência `prefers-reduced-motion` do sistema, lida de `matchMedia` (ausente: movimento normal). */
export function preferenciaDeMovimento(g: { matchMedia?: (q: string) => { matches: boolean; addEventListener?: (e: string, cb: () => void) => void } } = globalThis as never): {
  reduzido(): boolean
  aoMudar(cb: () => void): void
} {
  let mq: ReturnType<NonNullable<typeof g.matchMedia>> | null = null
  try { mq = g.matchMedia ? g.matchMedia('(prefers-reduced-motion: reduce)') : null } catch { mq = null }
  return {
    reduzido: () => mq?.matches === true,
    aoMudar: cb => { mq?.addEventListener?.('change', cb) },
  }
}

// ---- relação acessível da tripulação (R9, R10, R13, R16) ----

export interface Relacao {
  raiz: unknown
  /** Registra quem trata a seleção de um integrante (clique, Enter ou Espaço no botão). */
  aoSelecionar(cb: (membro: string) => void): void
  /** Atualiza os 12 itens e o aviso; só toca o DOM do que mudou, para o foco do teclado não se perder. */
  atualiza(itens: ItemRelacao[], aviso: string | null): void
}

/**
 * Cria a relação num `<nav>` com um botão que abre/fecha a lista dos 12 integrantes (um `<button>` por
 * integrante, `aria-pressed` = selecionado) e uma região `role="status"` com o aviso de dados antigos.
 * Tudo é elemento nativo: Tab percorre, Enter/Espaço seleciona, Esc fecha e devolve o foco ao botão.
 */
export function criaRelacao(doc: Pagina): Relacao {
  const raiz = doc.createElement('nav')
  raiz.id = 'relacao'
  raiz.setAttribute('aria-label', 'Tripulação')
  const alterna = doc.createElement('button')
  alterna.id = 'relacao-alterna'
  alterna.setAttribute('type', 'button')
  alterna.setAttribute('aria-expanded', 'false')
  alterna.setAttribute('aria-controls', 'relacao-lista')
  alterna.textContent = 'Tripulação'
  // botão compacto e escuro, no tom da cena: não cobre o telão a 240 px e continua legível sobre ele
  Object.assign(alterna.style, {
    font: '11px system-ui, sans-serif', padding: '1px 6px', color: COR.texto, background: COR.painel,
    border: `1px solid ${COR.telaoBorda}`, borderRadius: '3px', cursor: 'pointer',
  })
  const aviso = doc.createElement('p')
  aviso.id = 'relacao-aviso'
  aviso.setAttribute('role', 'status')
  aviso.setAttribute('aria-live', 'polite')
  Object.assign(aviso.style, { margin: '2px 0 0', font: '11px system-ui, sans-serif', color: COR.tempo, background: COR.painel, maxWidth: '200px' })
  const lista = doc.createElement('ul')
  lista.id = 'relacao-lista'
  lista.setAttribute('aria-label', 'Integrantes e estados')
  lista.hidden = true
  const botoes = new Map<string, any>()
  let tratar: (membro: string) => void = () => undefined
  const abre = (abrir: boolean): void => {
    lista.hidden = !abrir
    alterna.setAttribute('aria-expanded', String(abrir))
  }
  alterna.addEventListener('click', () => abre(lista.hidden))
  raiz.addEventListener('keydown', (ev: { key?: string }) => {
    if (ev.key === 'Escape' && !lista.hidden) { abre(false); alterna.focus?.() }
  })
  // colocada sobre o palco, no canto, sem ocupar espaço da cena
  raiz.style.position = 'fixed'
  raiz.style.top = '4px'
  raiz.style.left = '4px'
  raiz.style.zIndex = '2'
  raiz.style.maxHeight = '90%'
  raiz.style.overflow = 'auto'
  lista.style.listStyle = 'none'
  lista.style.margin = '4px 0 0'
  lista.style.padding = '0'
  raiz.appendChild(alterna)
  raiz.appendChild(aviso)
  raiz.appendChild(lista)
  doc.body.appendChild(raiz)
  return {
    raiz,
    aoSelecionar: cb => { tratar = cb },
    atualiza(itens, avisoTexto) {
      const texto = avisoTexto ?? ''
      if (aviso.textContent !== texto) aviso.textContent = texto
      for (const item of itens) {
        let botao = botoes.get(item.membro)
        if (!botao) {
          const li = doc.createElement('li')
          botao = doc.createElement('button')
          botao.setAttribute('type', 'button')
          botao.addEventListener('click', () => tratar(item.membro))
          li.appendChild(botao)
          lista.appendChild(li)
          botoes.set(item.membro, botao)
        }
        const rotulo = `${item.emoji} ${item.nome} ${item.simbolo} ${item.textoEstado} · ${item.presente ? 'na cena' : 'fora da cena'}`
        const chave = `${rotulo}|${item.selecionado}|${item.descricao}`
        if (botao.__chave === chave) continue
        botao.__chave = chave
        botao.textContent = rotulo
        botao.setAttribute('aria-label', item.descricao)
        botao.setAttribute('aria-pressed', String(item.selecionado))
        botao.setAttribute('data-membro', item.membro)
      }
    },
  }
}

/** Devolve o canvas `#cena` da página; quando a Orca gera a página em volta, cria o canvas no corpo (R45). */
export function obterCanvas(doc: Pagina): HTMLCanvasElement {
  const existente = doc.getElementById('cena')
  if (existente) return existente as HTMLCanvasElement
  // a página é só o palco: sem margem nem padding e sem barra de rolagem (a cena cabe na janela)
  for (const el of [doc.documentElement as ComEstilo | undefined, doc.body as ComEstilo]) {
    if (!el?.style) continue
    el.style.margin = '0'
    el.style.padding = '0'
    el.style.overflow = 'hidden'
  }
  // o palco é a área visível do painel: fixo nas quatro bordas, mede a largura e a altura (R54)
  const palco = doc.createElement('div')
  palco.id = 'palco'
  palco.style.position = 'fixed'
  palco.style.top = '0'
  palco.style.left = '0'
  palco.style.right = '0'
  palco.style.bottom = '0'
  palco.style.overflow = 'hidden'
  const canvas = doc.createElement('canvas')
  canvas.id = 'cena'
  canvas.width = GRADE.largura * 5
  canvas.height = GRADE.altura * 5
  // tamanho exibido em px, ajustado por ajustaCanvas para nunca passar do palco; centrado na largura
  canvas.style.display = 'block'
  canvas.style.margin = '0 auto'
  canvas.style.width = `${GRADE.largura * 5}px`
  canvas.style.height = `${GRADE.altura * 5}px`
  canvas.style.imageRendering = 'pixelated'
  palco.appendChild(canvas)
  doc.body.appendChild(palco)
  return canvas as HTMLCanvasElement
}

const frame = (globalThis as { orca?: OrcaFrame }).orca
if (frame && typeof document !== 'undefined') {
  const canvas = obterCanvas(document)
  iniciar(frame, canvas, criaRelacao(document as unknown as Pagina))
}
