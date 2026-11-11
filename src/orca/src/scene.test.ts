// Testes da pintura da cena (contexto de canvas falso que grava as chamadas).
import { assert, test } from 'orca/testing'
import { buildScene } from './scene-model.ts'
import { obterCanvas, paint } from './scene.ts'
import type { Pincel } from './scene'
import type { PonteState } from './protocol.ts'

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
  const cena = congela(buildScene(estado(), [], 0))
  const g = gravador()
  // contexto sem drawImage: qualquer chamada quebraria
  assert.equal((g.ctx as unknown as Record<string, unknown>).drawImage, undefined)
  paint(g.ctx, cena, 5)
  assert.ok(g.chamadas.every(c => ['fillRect', 'strokeRect', 'fillText'].includes(c)))
  assert.ok(g.chamadas.includes('fillRect') && g.chamadas.includes('strokeRect'))
  for (const nome of ['spock', 'picard', 'guinan']) assert.ok(g.textos.includes(nome), nome)
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
  const agora = Date.parse('2026-01-01T00:10:00Z')
  const s = estado()
  s.snapshot!.workers = []
  s.snapshot!.crew = s.snapshot!.crew.map(c =>
    c.member === 'spock' ? { ...c, count: 1, lastAt: '2026-01-01T00:05:00Z' } :
    c.member === 'worf' ? { ...c, count: 3, lastAt: '2026-01-01T00:09:30Z' } : c)
  const cena = buildScene(s, [], agora)
  const por = (m: string) => cena.personagens.find(p => p.membro === m)!
  const tempo = (m: string) => cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === m)?.texto
  // ativo: console aceso com brilho na cor da divisão e "há N min" embaixo
  const spock = por('spock')
  assert.equal(spock.opacidade, 1)
  assert.ok(spock.brilho)
  assert.ok(spock.brilho!.largura > spock.console.largura)
  assert.equal(tempo('spock'), 'há 5 min')
  assert.equal(tempo('worf'), 'há 0 min')
  const nome = cena.rotulos.find(r => r.tipo === 'nome' && r.dono === 'spock')!
  assert.ok(cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === 'spock')!.y > nome.y)
  // livre: no máximo 40% de opacidade, console apagado, sem tempo
  const data = por('data')
  assert.ok(data.opacidade <= 0.4)
  assert.equal(data.brilho, null)
  assert.equal(tempo('data'), undefined)
  // telão conta os ativos
  const telao = (c: typeof cena) => c.rotulos.filter(r => r.tipo === 'telao').map(r => r.texto)
  assert.ok(telao(cena).includes('2 tripulantes ativos'))
  const um = estado()
  assert.ok(telao(buildScene(um, [], agora)).includes('1 tripulante ativo'))
  um.snapshot!.crew = um.snapshot!.crew.map(c => ({ ...c, count: 0 }))
  assert.ok(telao(buildScene(um, [], agora)).includes('tripulação em repouso'))
  // pintura: o brilho sai na cor da divisão, o livre sai com alfa <= 0.4 e o ativo opaco
  const estilos: { op: string; cor: string; texto?: string }[] = []
  const ctx: Pincel = {
    fillStyle: '', strokeStyle: '', lineWidth: 1, font: '', textAlign: '', textBaseline: '',
    fillRect() { estilos.push({ op: 'fillRect', cor: ctx.fillStyle }) },
    strokeRect() { estilos.push({ op: 'strokeRect', cor: ctx.strokeStyle }) },
    fillText(t: string) { estilos.push({ op: 'fillText', cor: ctx.fillStyle, texto: t }) },
  }
  paint(ctx, cena, 5)
  const corDoTexto = (t: string) => estilos.find(e => e.op === 'fillText' && e.texto === t)!.cor
  assert.ok(alfa(corDoTexto('data')) <= 0.4, corDoTexto('data'))
  assert.equal(alfa(corDoTexto('spock')), 1)
  assert.equal(alfa(corDoTexto('há 5 min')), 1)
  const rgb = (hex: string) => [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16)).join(',')
  assert.ok(estilos.some(e => e.op === 'fillRect' && e.cor.replace(/\s/g, '').includes(rgb(spock.cor))), 'brilho na cor da divisão')
})
