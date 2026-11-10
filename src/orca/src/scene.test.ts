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
})

test('pintura da cena vazia mostra a mensagem central', () => {
  const cena = buildScene(estado(false), [], 0)
  const g = gravador()
  paint(g.ctx, cena, 5)
  assert.ok(g.textos.includes('StarCode não configurado neste worktree'))
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
