// Testes da pintura da cena (contexto de canvas falso que grava as chamadas).
import { assert, test } from 'orca/testing'
import { buildScene, GRADE, LARGURA_MIN_PX, ROTACAO_MS } from './scene-model.ts'
import type { Cena } from './scene-model.ts'
import { ajustaCanvas, dimensoes, obterCanvas, paint } from './scene.ts'
import type { Pincel } from './scene'
import type { PonteAgent, PonteState } from './protocol.ts'
import type { Identidades } from './crew-visual.ts'

const MEMBROS = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy', 'q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan']

function estado(starcode = true): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: 0, issue: null, issueNote: null, agents: [], log: [], error: null,
    snapshot: {
      schemaVersion: 1, worktree: 'C:/wt', starcode,
      crew: MEMBROS.map(m => ({ member: m, emoji: 'x', name: m, count: m === 'spock' ? 1 : 0, lastAt: null, cliModel: null })),
      gitMode: null, feature: null, errors: [],
      workers: Array.from({ length: 8 }, (_, i) => ({ label: `w${i}`, issues: [], base: null, dispatch: null, model: null })),
    },
  }
}

const IDS: Identidades = Object.fromEntries(MEMBROS.map(m => [`t-${m}`, m]))
const doMembro = (m: string, state: PonteAgent['state'] = 'working'): PonteAgent =>
  ({ terminalId: `t-${m}`, title: null, agent: 'claude', state, stateStartedAt: 0 })
const T = (ciclo: number, extra = 2000): number => ciclo * ROTACAO_MS + extra

function gravador(): { ctx: Pincel; chamadas: string[]; textos: string[] } {
  const chamadas: string[] = []
  const textos: string[] = []
  const ctx: Pincel = {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
    fillRect: () => { chamadas.push('fillRect') },
    strokeRect: () => { chamadas.push('strokeRect') },
    fillText: (t: string) => { chamadas.push('fillText'); textos.push(t) },
  }
  return { ctx, chamadas, textos }
}

function congela<T>(o: T): T {
  if (o && typeof o === 'object') {
    Object.values(o as object).forEach(congela)
    Object.freeze(o)
  }
  return o
}

test('pintura da cena só lê o modelo e não usa imagem', () => {
  const cena = congela(buildScene(estado(), [doMembro('spock')], T(0), undefined, IDS))
  const g = gravador()
  // contexto sem drawImage: qualquer chamada quebraria
  assert.equal((g.ctx as unknown as Record<string, unknown>).drawImage, undefined)
  paint(g.ctx, cena, 5)
  assert.ok(g.chamadas.every(c => ['fillRect', 'strokeRect', 'fillText'].includes(c)))
  assert.ok(g.chamadas.includes('fillRect') && g.chamadas.includes('strokeRect'))
  for (const nome of ['spock', 'picard']) assert.ok(g.textos.includes(nome), nome)
  assert.ok(g.textos.includes('⚙'))
  // o rodízio traz o resto da tripulação: Guinan aparece numa rodada seguinte
  const g2 = gravador()
  paint(g2.ctx, buildScene(estado(), [], T(1)), 5)
  assert.ok(g2.textos.includes('guinan') && g2.textos.includes('💤'))
  assert.ok(g.textos.includes('+2'))
  assert.ok(g.textos.includes('w0'))
  assert.ok(g.textos.includes('aceso = trabalhando · apagado = livre'))
})

test('pintura da cena vazia mostra a mensagem central', () => {
  const cena = buildScene(estado(false), [], 0)
  const g = gravador()
  paint(g.ctx, cena, 5)
  assert.equal(g.textos.join(' '), 'StarCode não configurado neste worktree')
})

test('cena cria o canvas e importa com caminho servido', async () => {
  // 1) sem #cena na página, o script cria o canvas e o põe no corpo
  const filhos: unknown[] = []
  const criar = (tag: string) => {
    const el: any = { tag, style: {}, filhos: [] as unknown[], appendChild(n: unknown) { el.filhos.push(n); return n } }
    return el
  }
  const doc: any = { getElementById: () => null, createElement: criar, body: { appendChild: (n: unknown) => filhos.push(n) } }
  const canvas: any = obterCanvas(doc)
  assert.equal(canvas.tag, 'canvas')
  assert.equal(canvas.id, 'cena')
  assert.ok(filhos.length === 1)
  // com #cena existente, reaproveita
  const ja: any = { tag: 'canvas' }
  assert.equal(obterCanvas({ ...doc, getElementById: () => ja }), ja)
  // 2) nenhum import relativo do painel fica sem extensão
  const { readFileSync } = await import('node:fs')
  const { fileURLToPath } = await import('node:url')
  for (const arq of ['scene.ts', 'scene-model.ts', 'panel.tsx', 'worker.ts', 'protocol.ts']) {
    const src = readFileSync(fileURLToPath(new URL(`./${arq}`, import.meta.url)), 'utf8')
    for (const m of src.matchAll(/^\s*(?:import|export)\b(?!\s+type\b)[^'"\n]*from\s+['"](\.[^'"]*)['"]/gm)) {
      assert.ok(/\.(ts|tsx|js|json)$/.test(m[1]), `${arq}: import sem extensão ${m[1]}`)
    }
  }
})

function alfa(cor: string): number {
  const m = /^rgba\([^)]*,\s*([\d.]+)\)$/.exec(cor)
  return m ? Number(m[1]) : 1
}

test('cena acende o ativo e conta os ativos no telão', () => {
  const agora = T(0)
  const s = estado()
  s.snapshot!.workers = []
  s.snapshot!.crew = s.snapshot!.crew.map(c =>
    c.member === 'spock' ? { ...c, lastAt: new Date(agora - 5 * 60_000).toISOString() } :
    c.member === 'worf' ? { ...c, lastAt: new Date(agora - 30_000).toISOString() } : c)
  const ags = [doMembro('spock'), doMembro('worf')]
  const cena = buildScene(s, ags, agora, undefined, IDS)
  const por = (m: string) => cena.personagens.find(p => p.membro === m)!
  const tempo = (m: string) => cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === m)?.texto
  // ativo: console aceso com brilho e "há N min" embaixo
  const spock = por('spock')
  assert.equal(spock.opacidade, 1)
  assert.ok(spock.brilho)
  assert.ok(spock.brilho!.largura > spock.console.largura)
  assert.equal(tempo('spock'), 'há 5 min')
  assert.equal(tempo('worf'), 'agora')
  const nome = cena.rotulos.find(r => r.tipo === 'nome' && r.dono === 'spock')!
  assert.ok(cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === 'spock')!.y > nome.y)
  // ocioso: corpo a no máximo 40% de opacidade, console apagado, sem tempo, nome ainda legível
  const data = por('data')
  assert.ok(data.opacidade <= 0.4)
  assert.ok(data.opacidadeTexto >= 0.7)
  assert.equal(data.brilho, null)
  assert.equal(tempo('data'), undefined)
  // telão conta os ativos (só quem trabalha com identidade confiável)
  const telao = (c: typeof cena) => c.rotulos.filter(r => r.tipo === 'telao').map(r => r.texto)
  assert.ok(telao(cena).includes('2 tripulantes ativos'))
  assert.ok(telao(buildScene(s, [doMembro('spock')], agora, undefined, IDS)).includes('1 tripulante ativo'))
  assert.ok(telao(buildScene(s, [], agora, undefined, IDS)).includes('tripulação em repouso'))
  // pintura: o brilho sai na cor do uniforme, o ocioso com texto de alfa menor que 1 e o ativo opaco
  const estilos: { op: string; cor: string; texto?: string }[] = []
  const ctx: Pincel = {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
    fillRect() { estilos.push({ op: 'fillRect', cor: ctx.fillStyle }) },
    strokeRect() { estilos.push({ op: 'strokeRect', cor: ctx.strokeStyle }) },
    fillText(t: string) { estilos.push({ op: 'fillText', cor: ctx.fillStyle, texto: t }) },
  }
  paint(ctx, cena, 5)
  const corDoTexto = (t: string) => estilos.find(e => e.op === 'fillText' && e.texto === t)!.cor
  assert.equal(alfa(corDoTexto('data')), data.opacidadeTexto)
  assert.equal(alfa(corDoTexto('spock')), 1)
  assert.equal(alfa(corDoTexto('há 5 min')), 1)
  const rgb = (hex: string) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)).join(',')
  assert.ok(estilos.some(e => e.op === 'fillRect' && e.cor.replace(/\s/g, '').includes(rgb(spock.cor))), 'brilho na cor do uniforme')
  // as peças do perfil também saem: o Spock pinta as orelhas na cor da pele
  assert.ok(spock.pecas.length > 0)
  assert.ok(estilos.some(e => e.op === 'fillRect' && e.cor === spock.pele))
})

test('ponte viva mantém rótulos legíveis', () => {
  // a 240 e a 360 px o canvas usa 5 e 7 px por célula: nenhuma fonte pintada fica abaixo de 10 px
  const ags = [doMembro('spock'), doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('kirk', 'done')]
  for (const [largura, e] of [[240, 5], [360, 7]]) {
    assert.equal(dimensoes(largura, 900).escala, e)
    const { linhas } = dimensoes(largura, 900)
    const fontes: number[] = []
    const ctx: Pincel = {
      fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
      fillRect() {}, strokeRect() {},
      fillText() { fontes.push(parseInt(ctx.font, 10)) },
    }
    paint(ctx, buildScene(estado(), ags, T(0), linhas, IDS), e)
    assert.ok(fontes.length > 10)
    assert.ok(fontes.every(f => f >= 10), `${largura}px: ${fontes}`)
  }
})

test('cena mostra agora para atividade recente', () => {
  const agora = T(0)
  const s = estado()
  s.snapshot!.workers = []
  const em = (antes: number) => {
    const lastAt = new Date(agora - antes).toISOString()
    s.snapshot!.crew = s.snapshot!.crew.map(c => (c.member === 'spock' ? { ...c, lastAt } : c))
    return buildScene(s, [doMembro('spock')], agora, undefined, IDS).rotulos.find(r => r.tipo === 'tempo' && r.dono === 'spock')?.texto
  }
  assert.equal(em(0), 'agora')
  assert.equal(em(30_000), 'agora')
  assert.equal(em(59_999), 'agora')
  assert.equal(em(-20_000), 'agora') // relógio adiantado não vira tempo negativo
  assert.equal(em(60_000), 'há 1 min')
  assert.equal(em(59 * 60_000), 'há 59 min')
  assert.equal(em(60 * 60_000), 'há 1 h')
  assert.equal(em(2 * 24 * 3_600_000), 'há 2 d')
  assert.ok(!buildScene(s, [doMembro('spock')], agora, undefined, IDS).rotulos.some(r => r.texto.includes('há 0 min')))
})

test('cena estica o anel e aumenta os bonecos', () => {
  // o palco define a grade: largura fixa de 48 células e linhas na proporção do painel (mínimo GRADE.altura)
  assert.equal(dimensoes(LARGURA_MIN_PX, 300).linhas, GRADE.altura)
  assert.equal(dimensoes(480, 1600).linhas, Math.floor((48 * 1600) / 480))
  const d = dimensoes(240, 1000)
  assert.equal(d.escala, 5)
  assert.equal(d.largura, 240)
  assert.equal(d.altura, d.linhas * 5)
  assert.ok(d.altura <= 1000 && 1000 - d.altura < 5, `faixa vazia: ${1000 - d.altura}px`)
  const largo = dimensoes(600, 2000)
  assert.ok(2000 - largo.altura * (600 / largo.largura) < 600 / 48, 'o canvas esticado ocupa a altura do palco')
  const s = estado()
  s.snapshot!.crew = s.snapshot!.crew.map(c => ({ ...c, lastAt: new Date(T(0) - 59 * 60_000).toISOString() }))
  const ags = ['spock', 'q', 'picard'].map(m => doMembro(m))
  const tocam = (a: { x: number; y: number; largura: number; altura: number }, b: typeof a) =>
    a.x < b.x + b.largura && b.x < a.x + a.largura && a.y < b.y + b.altura && b.y < a.y + a.altura
  const arcos: number[] = []
  for (const painel of [[240, 400], [240, 700], [300, 1100], [240, 1300]]) {
    const { linhas } = dimensoes(painel[0], painel[1])
    for (const nWorkers of [0, 8]) {
      const st: typeof s = { ...s, snapshot: { ...s.snapshot!, workers: s.snapshot!.workers.slice(0, nWorkers) } }
      const cena: Cena = buildScene(st, ags, T(0), linhas, IDS)
      const cenas = [0, 1, 2].map(c => buildScene(st, ags, T(c), linhas, IDS))
      assert.equal(cena.grade.altura, linhas)
      // sem faixa vazia: a legenda encosta no fim da grade e o anel ocupa a altura da ponte
      const legenda = cena.rotulos.find(r => r.tipo === 'legenda')!
      assert.ok(linhas - (legenda.caixa.y + legenda.caixa.altura) <= 1, `faixa abaixo da legenda (${linhas})`)
      const { anel, ponte } = cena
      assert.ok(anel.y - ponte.y <= 1 && ponte.y + ponte.altura - (anel.y + anel.altura) <= 1, `anel curto (${linhas})`)
      assert.ok(anel.largura >= cena.grade.largura - 2)
      // as estações se espalham pelo anel: do topo à base da ponte, dentro dela e sem se tocar
      const caixas = cenas.flatMap(c => c.personagens.map(p => p.caixa)).filter((c, i, l) => l.findIndex(o => o.x === c.x && o.y === c.y) === i)
      assert.equal(caixas.length, 12)
      const topo = Math.min(...caixas.map(c => c.y))
      const base = Math.max(...caixas.map(c => c.y + c.altura))
      assert.ok(topo - ponte.y <= 1 && ponte.y + ponte.altura - base <= 1, `estações não ocupam a ponte (${linhas})`)
      for (let i = 0; i < caixas.length; i++) {
        for (let j = i + 1; j < caixas.length; j++) assert.ok(!tocam(caixas[i], caixas[j]), `${linhas}: ${i} x ${j}`)
      }
      for (let i = 0; i < cena.rotulos.length; i++) {
        for (let j = i + 1; j < cena.rotulos.length; j++) {
          assert.ok(!tocam(cena.rotulos[i].caixa, cena.rotulos[j].caixa), `${linhas}: ${cena.rotulos[i].texto} x ${cena.rotulos[j].texto}`)
        }
      }
      if (nWorkers === 0) arcos.push(base - topo)
      // bonecos: pelo menos 16 px de altura a 240 px (5 px por célula), sentado e de pé bem diferentes
      const px = LARGURA_MIN_PX / cena.grade.largura
      const altura = (b: Cena['personagens'][number]['boneco']) => {
        const partes = [b.cabeca, b.corpo, ...b.bracos, ...b.pernas]
        return Math.max(...partes.map(r => r.y + r.altura)) - Math.min(...partes.map(r => r.y))
      }
      for (const b of [...cenas.flatMap(c => c.personagens.map(p => p.boneco)), ...cena.workers.map(w => w.boneco)]) {
        assert.ok(altura(b) * px >= 16, `boneco pequeno: ${altura(b) * px}px`)
        assert.ok(b.corpo.largura * px >= 15, `corpo estreito: ${b.corpo.largura * px}px`)
      }
      const por = (m: string) => cena.personagens.find(p => p.membro === m)!
      const sentado = por('spock'), dePe = por('data')
      assert.equal(sentado.pose, 'sentado')
      assert.equal(dePe.pose, 'de-pe')
      assert.ok((altura(dePe.boneco) - altura(sentado.boneco)) * px >= 7, 'de pé fica bem mais alto que sentado')
      assert.ok(dePe.boneco.pernas.every(r => r.altura * px >= 5), 'pernas visíveis a 240 px')
      assert.equal(sentado.boneco.pernas.length, 0)
    }
  }
  // quanto mais alto o painel, mais alto o anel
  for (let i = 1; i < arcos.length; i++) assert.ok(arcos[i] > arcos[i - 1], `anel não estica: ${arcos}`)
  // a pintura acompanha a grade da cena e o anel ocupa a ponte
  const cena = buildScene(s, ags, 0, 200, IDS)
  const g = gravador()
  paint(g.ctx, cena, 5)
  assert.ok(g.chamadas.length > 0)
})

test('cena cabe no palco sem rolagem', () => {
  // painéis reais, inclusive o da captura da T16 (465 x 930, mais baixo que a proporção mínima da grade)
  const paineis = [[465, 930], [240, 400], [240, 1000], [300, 500], [600, 700], [480, 1600], [252, 2000], [1000, 600]]
  for (const [w, h] of paineis) {
    const canvas: any = { width: 0, height: 0, style: {} }
    const palco = { clientWidth: w, clientHeight: h }
    const d = ajustaCanvas(canvas, palco)
    const css = { largura: parseFloat(canvas.style.width), altura: parseFloat(canvas.style.height) }
    // a altura desenhada nunca passa da altura do palco (nem a largura da largura)
    assert.ok(css.altura <= h, `${w}x${h}: canvas com ${css.altura}px de altura`)
    assert.ok(css.largura <= w, `${w}x${h}: canvas com ${css.largura}px de largura`)
    // e ocupa o palco numa das dimensões (sem faixa vazia grande)
    assert.ok(h - css.altura < w / 48 + 1 || w - css.largura <= 1, `${w}x${h}: sobra ${h - css.altura}px`)
    // o canvas mantém a proporção da grade e a legenda fica dentro da área visível
    assert.equal(canvas.width, d.largura)
    assert.equal(canvas.height, d.altura)
    assert.ok(Math.abs(css.largura / css.altura - d.largura / d.altura) < 0.02, `${w}x${h}: proporção`)
    const cena = buildScene(estado(), [], 0, d.linhas)
    const legenda = cena.rotulos.find(r => r.tipo === 'legenda')!
    assert.ok((legenda.caixa.y + legenda.caixa.altura) * (css.altura / cena.grade.altura) <= css.altura)
  }
  // o palco é a janela inteira, sem margem do corpo e sem barra de rolagem
  const criar = (tag: string) => {
    const el: any = { tag, style: {}, appendChild(n: unknown) { return n } }
    return el
  }
  const corpo: any = { style: {}, appendChild: () => undefined }
  const raiz: any = { style: {} }
  const canvas: any = obterCanvas({ getElementById: () => null, createElement: criar, body: corpo, documentElement: raiz } as any)
  assert.equal(corpo.style.margin, '0')
  assert.equal(corpo.style.overflow, 'hidden')
  assert.equal(raiz.style.overflow, 'hidden')
  assert.equal(canvas.style.display, 'block')
  assert.ok(canvas.style.height !== 'auto')
})
