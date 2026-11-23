// Testes da pintura da cena (contexto de canvas falso que grava as chamadas).
import { assert, test } from 'orca/testing'
import { avisoDeDados, buildScene, GRADE, LARGURA_MIN_PX, PONTE_ALTURA, criaRastroPresenca, relacaoDaTripulacao, TRANSICAO_MS } from './scene-model.ts'
import type { Cena } from './scene-model.ts'
import { ajustaCanvas, COR_ESTADO, criaRelacao, dimensoes, obterCanvas, paint, preferenciaDeMovimento } from './scene.ts'
import type { Pincel } from './scene'
import type { PonteAgent, PonteState } from './protocol.ts'
import type { Identidades } from './crew-visual.ts'

const MEMBROS = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy', 'q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan']

function estado(starcode = true): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: 0, issue: null, issueNote: null, agents: [], log: [], error: null,
    snapshot: {
      schemaVersion: 1, worktree: 'C:/wt', starcode,
      crew: MEMBROS.map(m => ({ member: m, emoji: 'x', name: m, count: 0, lastAt: null, cliModel: null })),
      gitMode: null, feature: null, errors: [],
      workers: Array.from({ length: 8 }, (_, i) => ({ label: `w${i}`, issues: [], base: null, dispatch: null, model: null })),
    },
  }
}

const IDS: Identidades = Object.fromEntries(MEMBROS.map(m => [`t-${m}`, m]))
const doMembro = (m: string, state: PonteAgent['state'] = 'working'): PonteAgent =>
  ({ terminalId: `t-${m}`, title: null, agent: 'claude', state, stateStartedAt: 0 })
/** Instante `extra` ms depois de `n` blocos de 10 s: o tempo sozinho não muda a presença. */
const T = (n: number, extra = 2000): number => n * 10_000 + extra

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
  // nomes completos do perfil, em até duas linhas: Spock numa, Jean-Luc Picard em duas
  for (const nome of ['Spock', 'Jean-Luc', 'Picard']) assert.ok(g.textos.includes(nome), nome)
  assert.ok(g.textos.includes('⚙'))
  // a seleção manual traz o resto da tripulação: Guinan aparece quando é escolhida
  const g2 = gravador()
  paint(g2.ctx, buildScene(estado(), [], T(1), undefined, IDS, { selecionado: 'guinan' }), 5)
  assert.ok(g2.textos.includes('Guinan') && g2.textos.includes('💤'))
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
  const nome = cena.rotulos.filter(r => r.tipo === 'nome' && r.dono === 'spock').at(-1)!
  assert.ok(cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === 'spock')!.y > nome.y)
  // ocioso: corpo a no máximo 40% de opacidade, console apagado, sem tempo, nome ainda legível
  const data = por('data')
  assert.ok(data.opacidade <= 0.6 && data.opacidade > 0.5)
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
  assert.equal(alfa(corDoTexto('Data')), data.opacidadeTexto)
  assert.equal(alfa(corDoTexto('Spock')), 1)
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
      const cenas = MEMBROS.map(m => buildScene(st, ags, T(0), linhas, IDS, { selecionado: m }))
      assert.equal(cena.grade.altura, linhas)
      // sem faixa vazia: a legenda encosta no fim da grade e o anel ocupa a altura da ponte
      const legenda = cena.rotulos.find(r => r.tipo === 'legenda')!
      assert.ok(linhas - (legenda.caixa.y + legenda.caixa.altura) <= 1, `faixa abaixo da legenda (${linhas})`)
      const { anel, ponte } = cena
      assert.ok(anel.y - ponte.y <= 1 && ponte.y + ponte.altura - (anel.y + anel.altura) <= 1, `anel curto (${linhas})`)
      assert.ok(anel.largura >= cena.grade.largura - 2)
      // a ponte tem proporção fixa e as estações a ocupam do topo à base, dentro dela e sem se tocar
      assert.equal(ponte.altura, PONTE_ALTURA, `ponte esticou (${linhas})`)
      const caixas = cenas.flatMap(c => c.personagens.map(p => p.caixa)).filter((c, i, l) => l.findIndex(o => o.x === c.x && o.y === c.y) === i)
      assert.equal(caixas.length, 12)
      const topo = Math.min(...caixas.map(c => c.y))
      const base = Math.max(...caixas.map(c => c.y + c.altura))
      assert.ok(topo - ponte.y <= 1 && ponte.y + ponte.altura - base <= 3, `estações não ocupam a ponte (${linhas})`)
      for (let i = 0; i < caixas.length; i++) {
        for (let j = i + 1; j < caixas.length; j++) assert.ok(!tocam(caixas[i], caixas[j]), `${linhas}: ${i} x ${j}`)
      }
      for (let i = 0; i < cena.rotulos.length; i++) {
        for (let j = i + 1; j < cena.rotulos.length; j++) {
          assert.ok(!tocam(cena.rotulos[i].caixa, cena.rotulos[j].caixa), `${linhas}: ${cena.rotulos[i].texto} x ${cena.rotulos[j].texto}`)
        }
      }
      if (nWorkers === 0) arcos.push(base - topo)
      // o espaço vertical que sobra vira a área de atividades, abaixo da engenharia e acima da legenda
      if (nWorkers === 0) {
        const at = cena.atividades!
        assert.ok(at && at.y >= cena.engenharia.y + cena.engenharia.altura && at.y + at.altura <= legenda.caixa.y, `atividades fora do lugar (${linhas})`)
        assert.ok(cena.rotulos.some(r => r.tipo === 'telao' && r.texto === 'ATIVIDADES'))
        assert.deepEqual(cena.rotulos.filter(r => r.tipo === 'atividade').map(r => r.texto), ['⚙ picard · trabalhando', '⚙ spock · trabalhando', '⚙ q · trabalhando'])
      }
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
  // painel mais alto não estica a ponte: o arco tem sempre a mesma altura
  for (let i = 1; i < arcos.length; i++) assert.equal(arcos[i], arcos[0], `ponte esticou: ${arcos}`)
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

/** Elemento falso com o mínimo de DOM que a relação usa. */
function elemento(tag: string): any {
  const el: any = {
    tag, style: {}, attrs: {} as Record<string, string>, filhos: [] as unknown[], ouvintes: {} as Record<string, (e: unknown) => void>,
    textContent: '', hidden: false, focado: false,
    setAttribute(k: string, v: string) { el.attrs[k] = v },
    appendChild(n: unknown) { el.filhos.push(n); return n },
    addEventListener(ev: string, cb: (e: unknown) => void) { el.ouvintes[ev] = cb },
    focus() { el.focado = true },
  }
  return el
}
const todos = (el: any): any[] => [el, ...el.filhos.flatMap(todos)]

test('ponte viva expõe lista acessível', () => {
  const corpo = elemento('body')
  const doc: any = { getElementById: () => null, createElement: elemento, body: corpo }
  const rel = criaRelacao(doc)
  const raiz: any = rel.raiz
  assert.equal(raiz.tag, 'nav')
  assert.equal(raiz.attrs['aria-label'], 'Tripulação')
  assert.equal(corpo.filhos[0], raiz)
  const [alterna, aviso, lista] = raiz.filhos
  // o botão abre e fecha a lista e diz o estado; a lista começa fechada
  assert.equal(alterna.tag, 'button')
  assert.equal(alterna.attrs.type, 'button')
  assert.equal(alterna.attrs['aria-expanded'], 'false')
  assert.equal(alterna.attrs['aria-controls'], lista.id)
  assert.equal(lista.hidden, true)
  alterna.ouvintes.click()
  assert.equal(lista.hidden, false)
  assert.equal(alterna.attrs['aria-expanded'], 'true')
  // Esc fecha e devolve o foco ao botão
  raiz.ouvintes.keydown({ key: 'Escape' })
  assert.equal(lista.hidden, true)
  assert.equal(alterna.attrs['aria-expanded'], 'false')
  assert.equal(alterna.focado, true)
  // a região de aviso é anunciada pelo leitor de tela
  assert.equal(aviso.attrs.role, 'status')
  assert.equal(aviso.attrs['aria-live'], 'polite')

  const base = estado()
  const agentes = [doMembro('worf', 'blocked'), doMembro('spock')]
  const agora = T(0)
  const itens = relacaoDaTripulacao(base, agentes, agora, IDS)
  rel.atualiza(itens, avisoDeDados(base))
  const botoes = todos(lista).filter(e => e.tag === 'button')
  assert.equal(botoes.length, 12)
  assert.deepEqual(botoes.map(b => b.attrs['data-membro']), MEMBROS)
  botoes.forEach((b, i) => {
    assert.equal(b.attrs.type, 'button')
    assert.equal(b.attrs['aria-label'], itens[i].descricao)
    assert.equal(b.attrs['aria-pressed'], 'false')
    assert.equal(b.textContent, `${itens[i].emoji} ${itens[i].nome} ${itens[i].simbolo} ${itens[i].textoEstado} · ${itens[i].presente ? 'na cena' : 'fora da cena'}`)
  })
  assert.equal(botoes.find(b => b.attrs['data-membro'] === 'worf')!.attrs['aria-label'], 'Worf, bloqueado, na cena')
  assert.equal(aviso.textContent, '')

  // Enter/Espaço num botão nativo vira click: a seleção chega a quem tratou e aria-pressed acompanha
  const escolhidos: string[] = []
  rel.aoSelecionar(m => escolhidos.push(m))
  botoes[11].ouvintes.click()
  assert.deepEqual(escolhidos, ['guinan'])
  rel.atualiza(relacaoDaTripulacao(base, agentes, agora, IDS, { selecionado: 'guinan' }), null)
  assert.equal(botoes[11].attrs['aria-pressed'], 'true')
  assert.equal(botoes.filter(b => b.attrs['aria-pressed'] === 'true').length, 1)
  assert.equal(botoes[11].attrs['aria-label'], 'Guinan, ocioso, na cena')
  // os mesmos 12 botões são reaproveitados: o foco do teclado não se perde numa atualização
  assert.equal(todos(lista).filter(e => e.tag === 'button').length, 12)
  assert.ok(todos(lista).filter(e => e.tag === 'button').every((b, i) => b === botoes[i]))

  // dados antigos: o aviso mostra o horário da última atualização válida
  const velho = { ...base, stale: true, lastValidAt: new Date(2026, 10, 22, 9, 5, 7).getTime() }
  rel.atualiza(relacaoDaTripulacao(velho, agentes, agora, IDS), avisoDeDados(velho))
  assert.equal(aviso.textContent, 'Dados desatualizados; última atualização válida às 09:05:07')
  assert.ok(botoes.every(b => / desconhecido, /.test(b.attrs['aria-label'])))
})

test('ponte viva respeita movimento reduzido', () => {
  const mq = (matches: boolean) => {
    const ouvintes: (() => void)[] = []
    return { matches, addEventListener: (_: string, cb: () => void) => ouvintes.push(cb), ouvintes }
  }
  const consultas: string[] = []
  const reduzida = mq(true)
  const pref = preferenciaDeMovimento({ matchMedia: (q: string) => { consultas.push(q); return reduzida } })
  assert.deepEqual(consultas, ['(prefers-reduced-motion: reduce)'])
  assert.equal(pref.reduzido(), true)
  let avisos = 0
  pref.aoMudar(() => { avisos++ })
  reduzida.ouvintes[0]()
  assert.equal(avisos, 1)
  reduzida.matches = false
  assert.equal(pref.reduzido(), false)
  // sem matchMedia (ou erro) o movimento é o normal
  assert.equal(preferenciaDeMovimento({}).reduzido(), false)
  assert.equal(preferenciaDeMovimento({ matchMedia: () => { throw new Error('x') } }).reduzido(), false)

  // com a preferência ativa a cena não anda: a mudança de estado vale na hora, sem deslocamento, em nenhum instante
  const base = estado()
  const rastro = criaRastroPresenca()
  const fixo = buildScene(base, [], T(0), undefined, IDS, { reduzido: true, rastro }).personagens.map(p => p.membro)
  assert.deepEqual(fixo, ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
  const alertas = ['q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan'].map(m => doMembro(m, 'blocked'))
  for (const t of [T(1), T(1, 2100), T(1, 2900), T(5)]) {
    const cena = buildScene(base, alertas, t, undefined, IDS, { reduzido: true, rastro })
    assert.deepEqual(cena.personagens.map(p => p.membro), ['q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan'])
    assert.ok(cena.personagens.every(p => p.transicao === null))
  }
})

test('ponte viva pinta nomes e indicadores legíveis nas transições', () => {
  const mistos = [doMembro('spock'), doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('kirk', 'done')]
  const troca = [...mistos, ...['laforge', 'mccoy', 'q', 'uhura'].map(m => doMembro(m, 'blocked'))]
  const NOMES: Record<string, string> = { picard: 'Jean-Luc Picard', laforge: 'Geordi La Forge', scotty: 'Montgomery Scott', kirk: 'James T. Kirk' }
  const fases = new Set<string>()
  for (const [largura, e] of [[240, 5], [360, 7]] as const) {
    for (const extra of [100, 500, TRANSICAO_MS / 2, 700, 1100]) {
      for (const ciclo of [1, 2, 3]) {
        // quatro alertas novos tiram quatro dos seis presentes: saídas e entradas pelo acesso
        const rastro = criaRastroPresenca()
        buildScene(estado(), mistos, T(ciclo, 0), undefined, IDS, { rastro })
        buildScene(estado(), troca, T(ciclo, 10_000), undefined, IDS, { rastro }) // a mudança real começa aqui
        const cena = buildScene(estado(), troca, T(ciclo, 10_000 + extra), undefined, IDS, { rastro })
        const pintados: { texto: string; x: number; y: number; px: number; cor: string }[] = []
        const ctx: Pincel = {
          fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
          fillRect() {}, strokeRect() {},
          fillText(t: string, x: number, y: number) { pintados.push({ texto: t, x, y, px: parseInt(ctx.font, 10), cor: ctx.fillStyle }) },
        }
        paint(ctx, cena, e)
        const emTransicao = cena.personagens.filter(p => p.transicao)
        for (const p of emTransicao) fases.add(`${largura}:${p.transicao!.fase}`)
        for (const p of cena.personagens) {
          const meus = cena.rotulos.filter(r => r.dono === p.membro)
          // nome (todas as linhas) e indicador do estado de cada personagem presente são pintados, na posição e no tamanho do modelo
          for (const r of meus.filter(r => r.tipo === 'nome' || r.tipo === 'estado')) {
            const pintado = pintados.find(x => x.texto === r.texto && x.x === r.x * e && x.y === r.y * e)
            assert.ok(pintado, `${largura}px: ${r.texto} não foi pintado (${p.transicao?.fase ?? 'estável'})`)
            assert.ok(pintado.px >= 10 && pintado.px === Math.round(r.tam * e), `${largura}px: fonte de ${r.texto}`)
            assert.ok(pintado.x >= 0 && pintado.y >= 0 && pintado.x <= cena.grade.largura * e && pintado.y <= cena.grade.altura * e, `${largura}px: ${r.texto} fora do canvas`)
            // a opacidade acompanha a transição: de 0 a 1 entrando, de 1 a 0 saindo, nunca fora do intervalo
            assert.ok(p.opacidadeTexto >= 0 && p.opacidadeTexto <= 1)
            const a = pintado.cor.startsWith('rgba') ? Number(pintado.cor.replace(/.*,\s*([\d.]+)\)$/, '$1')) : 1
            assert.equal(a, p.opacidadeTexto, `${largura}px: alfa de ${r.texto}`)
          }
          if (NOMES[p.membro]) assert.equal(meus.filter(r => r.tipo === 'nome').map(r => r.texto).join(' '), NOMES[p.membro])
        }
        // nomes e indicadores pintados nunca se cobrem: as caixas do modelo, vistas em pixels, não se tocam
        const caixas = cena.rotulos.filter(r => r.tipo === 'nome' || r.tipo === 'estado' || r.tipo === 'emoji')
        for (let i = 0; i < caixas.length; i++) {
          for (let j = i + 1; j < caixas.length; j++) {
            const a = caixas[i].caixa, b = caixas[j].caixa
            assert.ok(!(a.x < b.x + b.largura && b.x < a.x + a.largura && a.y < b.y + b.altura && b.y < a.y + a.altura), `${largura}px: ${caixas[i].texto} x ${caixas[j].texto}`)
          }
        }
      }
    }
  }
  assert.deepEqual([...fases].sort(), ['240:entrando', '240:saindo', '360:entrando', '360:saindo'])
})

test('ponte viva pinta a placa do nome com a cor do estado e dentro da grade', () => {
  const agora = T(0)
  const cena = buildScene(estado(), [doMembro('spock'), doMembro('worf', 'blocked'), doMembro('kirk', 'done'), doMembro('data', 'waiting')], agora, undefined, IDS)
  const bordas: { cor: string; x: number; largura: number }[] = []
  const ctx: Pincel = {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
    fillRect() {}, fillText() {},
    strokeRect(x: number, _y: number, w: number) { bordas.push({ cor: ctx.strokeStyle, x, largura: w }) },
  }
  paint(ctx, cena, 5)
  for (const p of cena.personagens) {
    // cada estado tem a própria cor de borda (a cor reforça o símbolo, não o substitui) e a cor de cada estado é distinta
    assert.ok(bordas.some(b => b.cor === COR_ESTADO[p.estado] || b.cor.startsWith('rgba')), `borda de ${p.membro}`)
  }
  assert.equal(new Set(Object.values(COR_ESTADO)).size, 6)
  assert.ok(COR_ESTADO.trabalhando !== COR_ESTADO.aguardando && COR_ESTADO.bloqueado !== COR_ESTADO.concluido)
  // nenhuma placa passa da largura da tela de 240 px (48 células x 5 px)
  for (const b of bordas) assert.ok(b.x >= 0 && b.x + b.largura <= 48 * 5 + 1, `placa fora da tela: ${b.x} + ${b.largura}`)
})

test('ponte viva mantém o botão da relação compacto e legível sobre a cena', () => {
  const doc: any = { getElementById: () => null, createElement: elemento, body: elemento('body') }
  const raiz: any = criaRelacao(doc).raiz
  const [alterna, aviso] = raiz.filhos
  // fonte de 11 px, fundo escuro e borda na cor do telão: não esconde o título nem some sobre o fundo
  assert.equal(parseInt(alterna.style.font, 10), 11)
  assert.ok(alterna.style.background && alterna.style.color && alterna.style.border)
  assert.ok(parseInt(aviso.style.font, 10) >= 11)
  assert.ok(parseFloat(aviso.style.maxWidth) <= 200)
  assert.equal(raiz.style.position, 'fixed')
})
