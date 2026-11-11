// Testes do modelo da cena da Ponte (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { buildScene, LEGENDA } from './scene-model'
import type { Cena } from './scene-model'
import type { PonteAgent, PonteState, PonteWorker } from './protocol'

const MEMBROS = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy', 'q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan']

function estado(
  over: Partial<PonteState> = {},
  crew: Record<string, [number, string | null]> = {},
  workers: PonteWorker[] = [],
  starcode = true,
): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: 0, issue: null, issueNote: null, agents: [], log: [], error: null,
    snapshot: {
      schemaVersion: 1, worktree: 'C:/wt', starcode,
      crew: MEMBROS.map(m => ({ member: m, emoji: 'x', name: m, count: crew[m]?.[0] ?? 0, lastAt: crew[m]?.[1] ?? null, cliModel: null })),
      gitMode: null, feature: null, workers, errors: [],
    },
    ...over,
  }
}
const worker = (label: string, issues: string[] = []): PonteWorker => ({ label, issues, base: null, dispatch: null, model: null })
const agente = (state: PonteAgent['state'], title: string): PonteAgent => ({ terminalId: null, title, agent: 'claude', state, stateStartedAt: 0 })

test('cena tem uma estação por tripulante e a engenharia', () => {
  const cena = buildScene(estado(), [], 0)
  assert.equal(cena.vazia, false)
  assert.equal(cena.grade.largura, 48)
  assert.equal(cena.grade.altura, 92)
  assert.ok(cena.grade.altura > cena.grade.largura) // layout vertical
  assert.deepEqual(cena.estacoes.map(e => e.membro).sort(), [...MEMBROS].sort())
  assert.equal(cena.personagens.length, 12)
  assert.ok(cena.telao.largura > 0 && cena.engenharia.largura > 0)
  // telão em cima, ponte no meio, engenharia embaixo
  assert.ok(cena.telao.y + cena.telao.altura <= cena.ponte.y)
  assert.ok(cena.ponte.y + cena.ponte.altura <= cena.engenharia.y)
  // cada estação mostra o emoji e o nome do tripulante
  for (const p of cena.personagens) {
    assert.ok(cena.rotulos.some(r => r.tipo === 'emoji' && r.texto === p.emoji), `emoji ${p.membro}`)
    assert.ok(cena.rotulos.some(r => r.tipo === 'nome' && r.texto === p.nome), `nome ${p.membro}`)
  }
  assert.equal(new Set(cena.estacoes.map(e => `${e.x},${e.y}`)).size, 12)
  // todas as estações (LaForge incluído) ficam na ponte, e as áreas delas não se tocam
  const tocam = (a: Cena['personagens'][number]['caixa'], b: typeof a) =>
    a.x < b.x + b.largura && b.x < a.x + a.largura && a.y < b.y + b.altura && b.y < a.y + a.altura
  const comWorkers = buildScene(estado({}, {}, Array.from({ length: 8 }, (_, i) => worker(`T${i}`))), [], 0)
  for (const cs of [cena, comWorkers]) {
    const pt = cs.ponte
    for (const p of cs.personagens) {
      assert.ok(p.caixa.y >= pt.y && p.caixa.y + p.caixa.altura <= pt.y + pt.altura, `fora da ponte: ${p.membro}`)
      assert.ok(p.caixa.x >= 0 && p.caixa.x + p.caixa.largura <= cs.grade.largura, `fora da grade: ${p.membro}`)
    }
    for (let i = 0; i < 12; i++) {
      for (let j = i + 1; j < 12; j++) {
        assert.ok(!tocam(cs.personagens[i].caixa, cs.personagens[j].caixa), `${cs.personagens[i].membro} x ${cs.personagens[j].membro}`)
      }
    }
  }
})

test('cena senta tripulante ativo e anima a cada 250 ms', () => {
  const s = estado({}, { spock: [2, '2026-01-01T00:00:00Z'] })
  const a = buildScene(s, [], 0).personagens
  const b = buildScene(s, [], 250).personagens
  const c = buildScene(s, [], 500).personagens
  const spock = (p: typeof a) => p.find(x => x.membro === 'spock')!
  assert.equal(spock(a).pose, 'sentado')
  assert.equal(spock(a).quadro, 0)
  assert.equal(spock(b).quadro, 1)
  assert.equal(spock(c).quadro, 0)
  const picard = a.find(x => x.membro === 'picard')!
  assert.equal(picard.pose, 'de-pe')
  assert.equal(picard.quadro, 0)
  // inativo fica na própria estação (mesma posição de quando está ativo), apagado e parado
  assert.equal(spock(a).ativo, true)
  assert.equal(picard.ativo, false)
  const ativoPicard = buildScene(estado({}, { picard: [1, null] }), [], 0).personagens.find(x => x.membro === 'picard')!
  assert.equal(`${ativoPicard.x},${ativoPicard.y}`, `${picard.x},${picard.y}`)
  assert.equal(buildScene(s, [], 250).personagens.find(x => x.membro === 'picard')!.quadro, 0)
})

test('cena põe o balão no personagem do agente bloqueado', () => {
  const ws = [worker('T3', ['SC-117']), worker('T4', ['SC-118'])]
  // casa pelo rótulo do worker
  let cena = buildScene(estado({}, {}, ws), [agente('blocked', 'laforge T4 implementando')], 0)
  assert.deepEqual(cena.workers.map(w => w.balao), [false, true])
  // casa pela issue
  cena = buildScene(estado({}, {}, ws), [agente('waiting', 'trabalho em SC-117')], 0)
  assert.deepEqual(cena.workers.map(w => w.balao), [true, false])
  // sem casamento: tripulante ativo de lastAt mais recente
  const crew: Record<string, [number, string]> = { spock: [1, '2026-01-01T00:00:00Z'], data: [1, '2026-01-02T00:00:00Z'] }
  cena = buildScene(estado({}, crew, ws), [agente('blocked', 'outra coisa')], 0)
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro), ['data'])
  // ninguém ativo: Picard
  cena = buildScene(estado(), [agente('waiting', 'x')], 0)
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro), ['picard'])
  // working não gera balão
  cena = buildScene(estado(), [agente('working', 'x')], 0)
  assert.equal(cena.personagens.some(p => p.balao), false)
})

test('cena desenha até 6 workers e +N', () => {
  const ws = Array.from({ length: 8 }, (_, i) => worker(`T${i + 1}`))
  const cena = buildScene(estado({}, {}, ws), [agente('done', 'laforge T2')], 0)
  assert.equal(cena.workers.length, 6)
  assert.deepEqual(cena.workers.map(w => w.rotulo), ['T1', 'T2', 'T3', 'T4', 'T5', 'T6'])
  assert.equal(cena.maisN, 2)
  assert.deepEqual(cena.workers.map(w => w.concluido), [false, true, false, false, false, false])
  assert.equal(buildScene(estado({}, {}, ws.slice(0, 6)), [], 0).maisN, 0)
})

test('cena vazia mostra a frase do estado', () => {
  const vazia = (s: PonteState) => buildScene(s, [], 0)
  const semWt = vazia(estado({ status: 'sem-worktree', snapshot: null }))
  assert.equal(semWt.vazia, true)
  assert.equal(semWt.mensagem, 'Nenhum worktree em foco')
  assert.equal(semWt.personagens.length, 0)
  assert.equal(semWt.rotulos.map(r => r.texto).join(" "), "Nenhum worktree em foco")
  assert.equal(vazia(estado({}, {}, [], false)).mensagem, 'StarCode não configurado neste worktree')
  assert.equal(vazia(estado({ status: 'erro', snapshot: null, error: 'python não encontrado\ndetalhe' })).mensagem, 'python não encontrado')
  // erro com estado bom anterior continua desenhando
  const comBom = vazia(estado({ status: 'erro', stale: true, error: 'falhou' }))
  assert.equal(comBom.vazia, false)
  assert.equal(comBom.mensagem, null)
})

function sobrepoe(a: Cena['rotulos'][number], b: Cena['rotulos'][number]): boolean {
  const x = a.caixa, y = b.caixa
  return x.x < y.x + y.largura && y.x < x.x + x.largura && x.y < y.y + y.altura && y.y < x.y + x.altura
}

test('cena sem rótulos sobrepostos', () => {
  const crew: Record<string, [number, string]> = { spock: [1, '2026-01-01T00:00:00Z'], laforge: [1, '2026-01-02T00:00:00Z'] }
  const ws = Array.from({ length: 8 }, (_, i) => worker(i === 2 ? 'T12345678910' : `T${i + 1}`, [`SC-${i}`]))
  const agentes = [agente('done', 'laforge T1'), agente('blocked', 'laforge T12345678910'), agente('waiting', 'laforge T8'), agente('blocked', 'outra')]
  // todos ativos há 59 min (o rótulo de tempo mais largo), com balão
  const todos: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, '1970-01-01T00:00:00Z']]))
  const cenas = [
    buildScene(estado(), [], 0),
    buildScene(estado({}, crew, ws, true), agentes, 250),
    buildScene(estado({}, crew, ws.slice(0, 3)), agentes, 0),
    buildScene(estado({}, todos, ws), [...agentes, agente('waiting', 'nada')], 59 * 60_000 + 1000),
    buildScene(estado({}, todos, []), [agente('blocked', 'nada')], 59 * 60_000 + 1000),
    buildScene(estado({}, todos, ws.slice(0, 4)), [agente('blocked', 'nada')], 30 * 3_600_000),
    buildScene(estado({ status: 'erro', snapshot: null, error: 'um erro bem longo que precisa quebrar em várias linhas de texto' }), [], 0),
  ]
  for (const cena of cenas) {
    const { largura, altura } = cena.grade
    for (const r of cena.rotulos) {
      // a 240 px de largura a escala é 240 / 48 = 5 px por célula: a fonte tem de dar pelo menos 10 px
      assert.ok(r.tam * (240 / largura) >= 10, `fonte pequena: ${r.texto}`)
      assert.ok(r.caixa.x >= 0 && r.caixa.y >= 0 && r.caixa.x + r.caixa.largura <= largura && r.caixa.y + r.caixa.altura <= altura, `fora da grade: ${r.texto}`)
    }
    for (let i = 0; i < cena.rotulos.length; i++) {
      for (let j = i + 1; j < cena.rotulos.length; j++) {
        const a = cena.rotulos[i], b = cena.rotulos[j]
        assert.ok(!sobrepoe(a, b), `${a.texto} x ${b.texto}`)
      }
    }
  }
  // determinístico (função pura)
  assert.deepEqual(buildScene(estado(), [], 0), buildScene(estado(), [], 0))
})

test('cena mostra o telão com fase e progresso', () => {
  const base = estado()
  base.snapshot!.feature = {
    slug: 'fase-10-ponte', phase: 'review', size: null, done: false, linear: [], integrationBranch: null,
    progress: { done: 8, total: 9, percent: 89 }, breaker: 'closed',
    files: { context: null, spec: null, tasks: null, handoff: null },
  }
  const cena = buildScene(base, [], 0)
  const textos = cena.rotulos.map(r => r.texto)
  assert.ok(textos.includes('fase-10-ponte'))
  assert.ok(textos.includes('review'))
  assert.ok(textos.includes('8/9 · 89%'))
  assert.equal(cena.progresso?.percentual, 89)
  assert.equal(cena.progresso?.feitos, 8)
  assert.equal(cena.progresso?.total, 9)
  assert.ok(cena.rotulos.some(r => r.tipo === 'legenda' && r.texto === LEGENDA))
  assert.ok(LEGENDA.includes('aceso = trabalhando') && LEGENDA.includes('apagado = livre'))
  // a legenda fica embaixo, abaixo da engenharia
  const legenda = cena.rotulos.find(r => r.tipo === 'legenda')!
  assert.ok(legenda.y > cena.engenharia.y + cena.engenharia.altura)
  // sem feature: o telão avisa
  assert.ok(buildScene(estado(), [], 0).rotulos.some(r => r.texto === 'sem feature ativa'))
})

test('cena compacta a engenharia sem workers', () => {
  const sem = buildScene(estado(), [], 0)
  assert.equal(sem.workers.length, 0)
  assert.equal(sem.vagas.length, 0)
  // uma única linha dentro da engenharia
  const dentro = (c: Cena) => c.rotulos.filter(r => r.y >= c.engenharia.y && r.y <= c.engenharia.y + c.engenharia.altura)
  assert.deepEqual(dentro(sem).map(r => r.texto), ['Nenhum worker na engenharia'])
  assert.ok(sem.engenharia.altura <= 5, `engenharia alta: ${sem.engenharia.altura}`)
  // com workers: só os reais, sem vagas vazias
  const dois = buildScene(estado({}, {}, [worker('T1'), worker('T2')]), [], 0)
  assert.equal(dois.workers.length, 2)
  assert.equal(dois.vagas.length, 2)
  assert.ok(!dois.rotulos.some(r => r.texto === 'Nenhum worker na engenharia'))
  const seis = buildScene(estado({}, {}, Array.from({ length: 9 }, (_, i) => worker(`T${i}`))), [], 0)
  assert.equal(seis.vagas.length, 6)
  assert.ok(seis.rotulos.some(r => r.texto === '+3'))
  assert.ok(dois.engenharia.altura < seis.engenharia.altura)
  // a altura liberada vai para a ponte: ela cresce e as estações se espalham
  assert.ok(sem.ponte.altura > dois.ponte.altura && dois.ponte.altura > seis.ponte.altura)
  assert.equal(sem.engenharia.y + sem.engenharia.altura, seis.engenharia.y + seis.engenharia.altura)
  const alturaArco = (c: Cena) => { const ys = c.personagens.map(p => p.y); return Math.max(...ys) - Math.min(...ys) }
  assert.ok(alturaArco(sem) > alturaArco(seis))
})

test('cena desenha a ponte em arco com bonecos', () => {
  const s = estado({}, { spock: [1, '2026-01-01T00:00:00Z'], worf: [2, null] })
  const a = buildScene(s, [], 0)
  const b = buildScene(s, [], 250)
  const por = (c: Cena, m: string) => c.personagens.find(p => p.membro === m)!
  const picard = por(a, 'picard')
  // Picard maior, no centro da largura e cercado pelas estações
  assert.equal(picard.x, a.grade.largura / 2)
  const outros = a.personagens.filter(p => p.membro !== 'picard')
  for (const p of outros) assert.ok(picard.escala > p.escala, p.membro)
  assert.ok(picard.boneco.corpo.altura > por(a, 'data').boneco.corpo.altura)
  // arco: as estações ficam a uma distância parecida do Picard e em volta dele (sem buraco maior que 90 graus)
  const dist = outros.map(p => Math.hypot(p.x - picard.x, p.y - picard.y))
  const media = dist.reduce((x, y) => x + y, 0) / dist.length
  for (const d of dist) assert.ok(d > media * 0.75 && d < media * 1.25, `fora do arco: ${d} (média ${media})`)
  const ang = outros.map(p => Math.atan2(p.y - picard.y, p.x - picard.x)).sort((x, y) => x - y)
  const buracos = ang.map((g, i) => g - (i === 0 ? ang[ang.length - 1] - 2 * Math.PI : ang[i - 1]))
  assert.ok(Math.max(...buracos) <= Math.PI / 2, `buraco no arco: ${Math.max(...buracos)}`)
  // não é grade: as estações não se alinham em poucas linhas
  assert.ok(new Set(outros.map(p => p.y)).size >= 5)
  // boneco: o emoji é a insígnia no peito
  for (const p of a.personagens) {
    const insignia = a.rotulos.find(r => r.tipo === 'emoji' && r.dono === p.membro)!
    const c = p.boneco.corpo
    assert.ok(insignia.x > c.x && insignia.x < c.x + c.largura && insignia.y > c.y && insignia.y < c.y + c.altura, `insígnia fora do peito: ${p.membro}`)
  }
  assert.equal(por(a, 'spock').cor, por(a, 'troi').cor) // mesma divisão (ciências)
  assert.notEqual(por(a, 'spock').cor, por(a, 'worf').cor)
  // ativo sentado digitando (braços trocam a cada 250 ms); livre de pé, parado, com pernas
  const spock = por(a, 'spock'), data = por(a, 'data')
  assert.equal(spock.pose, 'sentado')
  assert.equal(spock.boneco.pernas.length, 0)
  assert.equal(data.pose, 'de-pe')
  assert.equal(data.boneco.pernas.length, 2)
  assert.ok(spock.boneco.cabeca.y - spock.y > data.boneco.cabeca.y - data.y, 'sentado fica mais baixo')
  assert.notDeepEqual(spock.boneco.bracos, por(b, 'spock').boneco.bracos)
  assert.deepEqual(data.boneco, por(b, 'data').boneco)
  // worker da engenharia também é boneco: trabalhando sentado, concluído de pé
  const w = buildScene(estado({}, {}, [worker('T1'), worker('T2')]), [agente('done', 'laforge T2')], 0).workers
  assert.equal(w[0].pose, 'sentado')
  assert.equal(w[1].pose, 'de-pe')
  assert.equal(w[1].boneco.pernas.length, 2)
})
