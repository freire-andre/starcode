// Testes da pintura da cena (contexto de canvas falso que grava as chamadas).
import { assert, test } from 'orca/testing'
import { buildScene } from './scene-model'
import { paint } from './scene'
import type { Pincel } from './scene'
import type { PonteState } from './protocol'

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
