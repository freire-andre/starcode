// Testes do modelo da cena da Ponte (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { avisoDeDados, buildScene, GRADE, horario, OPACIDADE_LIVRE, TAM_NOME, LEGENDA, PONTE_ALTURA, linhasDoPainel, pecasDoPerfil, relacaoDaTripulacao, criaRastroPresenca, selecionaPresentes, alternaSelecao, TRANSICAO_MS } from './scene-model'
import type { Cena } from './scene-model'
type Rastro = ReturnType<typeof criaRastroPresenca>
import { ESTADOS, PERFIS, estadosDaTripulacao } from './crew-visual'
import type { EstadoDoMembro, Identidades } from './crew-visual'
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
/** Vínculos confiáveis terminal -> integrante, como os que o despacho registra. */
const IDS: Identidades = Object.fromEntries(MEMBROS.map(m => [`t-${m}`, m]))
const doMembro = (m: string, state: PonteAgent['state'] = 'working'): PonteAgent =>
  ({ terminalId: `t-${m}`, title: null, agent: 'claude', state, stateStartedAt: 0 })
/** Instante `extra` ms depois de `n` blocos de 10 s: a passagem do tempo nunca decide quem está presente (R3). */
const T = (n: number, extra = 2000): number => n * 10_000 + extra
const membrosDe = (c: Cena): string[] => c.personagens.map(p => p.membro)
const NOMES_CREW = ['Picard', 'Spock', 'Troi', 'Data', 'LaForge', 'McCoy', 'Q', 'Uhura', 'Scotty', 'Kirk', 'Worf', 'Guinan']
const NOMES_COMPLETOS = ['Jean-Luc Picard', 'Spock', 'Deanna Troi', 'Data', 'Geordi La Forge', 'Leonard McCoy', 'Q', 'Nyota Uhura', 'Montgomery Scott', 'James T. Kirk', 'Worf', 'Guinan']
/** Nome do integrante na cena: as linhas do nome (até duas) na ordem em que aparecem. */
const nomeNaCena = (c: Cena, membro: string): string => c.rotulos.filter(r => r.tipo === 'nome' && r.dono === membro).map(r => r.texto).join(' ')
const tocam = (a: { x: number; y: number; largura: number; altura: number }, b: typeof a) =>
  a.x < b.x + b.largura && b.x < a.x + a.largura && a.y < b.y + b.altura && b.y < a.y + a.altura

test('cena tem uma estação por tripulante e a engenharia', () => {
  const cena = buildScene(estado(), [], T(0))
  assert.equal(cena.vazia, false)
  assert.equal(cena.grade.largura, 48)
  assert.equal(cena.grade.altura, GRADE.altura)
  assert.ok(cena.grade.altura > cena.grade.largura) // layout vertical
  assert.deepEqual(cena.estacoes.map(e => e.membro).sort(), [...MEMBROS].sort())
  assert.equal(new Set(cena.estacoes.map(e => `${e.x},${e.y}`)).size, 12)
  assert.ok(cena.telao.largura > 0 && cena.engenharia.largura > 0)
  // telão em cima, ponte no meio, engenharia embaixo; o acesso fica dentro da ponte
  assert.ok(cena.telao.y + cena.telao.altura <= cena.ponte.y)
  assert.ok(cena.ponte.y + cena.ponte.altura <= cena.engenharia.y)
  assert.ok(cena.porta.y > cena.ponte.y && cena.porta.y < cena.ponte.y + cena.ponte.altura)
  const comWorkers = estado({}, {}, Array.from({ length: 8 }, (_, i) => worker(`T${i}`)))
  for (const base of [estado(), comWorkers]) {
    const vistos = new Set<string>()
    for (let ciclo = 0; ciclo < 3; ciclo++) {
      const cs = buildScene(base, [], T(ciclo))
      for (const p of cs.personagens) {
        vistos.add(p.membro)
        // cada personagem mostra o emoji e o nome da tripulação (crew.yaml)
        assert.ok(cs.rotulos.some(r => r.tipo === 'emoji' && r.dono === p.membro && r.texto === p.emoji), `emoji ${p.membro}`)
        assert.equal(nomeNaCena(cs, p.membro), p.nome, `nome ${p.membro}`)
        // todas as estações (LaForge incluído) ficam na ponte, e as áreas delas não se tocam
        assert.ok(p.caixa.y >= cs.ponte.y && p.caixa.y + p.caixa.altura <= cs.ponte.y + cs.ponte.altura, `fora da ponte: ${p.membro}`)
        assert.ok(p.caixa.x >= 0 && p.caixa.x + p.caixa.largura <= cs.grade.largura, `fora da grade: ${p.membro}`)
      }
      for (let i = 0; i < cs.personagens.length; i++) {
        for (let j = i + 1; j < cs.personagens.length; j++) {
          assert.ok(!tocam(cs.personagens[i].caixa, cs.personagens[j].caixa), `${cs.personagens[i].membro} x ${cs.personagens[j].membro}`)
        }
      }
    }
    assert.equal(vistos.size, 6)
  }
})

test('cena senta tripulante ativo e anima a cada 250 ms', () => {
  const ags = [doMembro('spock')]
  const a = buildScene(estado(), ags, T(0), undefined, IDS).personagens
  const b = buildScene(estado(), ags, T(0, 2250), undefined, IDS).personagens
  const c = buildScene(estado(), ags, T(0, 2500), undefined, IDS).personagens
  const spock = (p: typeof a) => p.find(x => x.membro === 'spock')!
  assert.equal(spock(a).pose, 'sentado')
  assert.equal(spock(a).quadro, 0)
  assert.equal(spock(b).quadro, 1)
  assert.equal(spock(c).quadro, 0)
  const picard = a.find(x => x.membro === 'picard')!
  assert.equal(picard.pose, 'de-pe')
  assert.equal(picard.quadro, 0)
  assert.equal(spock(a).ativo, true)
  assert.equal(picard.ativo, false)
  // trabalhar não muda a estação: o Picard trabalhando fica no mesmo lugar de quando está ocioso
  const ativoPicard = buildScene(estado(), [doMembro('picard')], T(0), undefined, IDS).personagens.find(x => x.membro === 'picard')!
  assert.equal(`${ativoPicard.x},${ativoPicard.y}`, `${picard.x},${picard.y}`)
  assert.equal(buildScene(estado(), [doMembro('picard')], T(0, 2250), undefined, IDS).personagens.find(x => x.membro === 'picard')!.quadro, 1)
})

test('cena põe o balão no personagem do agente bloqueado', () => {
  const ws = [worker('T3', ['SC-117']), worker('T4', ['SC-118'])]
  // worker: casa pelo rótulo
  let cena = buildScene(estado({}, {}, ws), [agente('blocked', 'laforge T4 implementando')], T(0))
  assert.deepEqual(cena.workers.map(w => w.balao), [false, true])
  // worker: casa pela issue
  cena = buildScene(estado({}, {}, ws), [agente('waiting', 'trabalho em SC-117')], T(0))
  assert.deepEqual(cena.workers.map(w => w.balao), [true, false])
  // tripulante: só pelo vínculo confiável (terminalId), nunca por título nem por quem trabalhou por último
  const crew: Record<string, [number, string]> = { spock: [1, '2026-01-01T00:00:00Z'], data: [1, '2026-01-02T00:00:00Z'] }
  cena = buildScene(estado({}, crew), [doMembro('worf', 'blocked'), doMembro('q', 'waiting')], T(0), undefined, IDS)
  const por = (m: string) => cena.personagens.find(p => p.membro === m)!
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro), ['q', 'worf'])
  assert.equal(por('worf').estado, 'bloqueado')
  assert.equal(por('q').estado, 'aguardando')
  assert.ok(cena.rotulos.some(r => r.tipo === 'balao' && r.dono === 'worf' && r.texto === '!'))
  // agente bloqueado sem identidade confiável não escolhe um dono: ninguém recebe o balão
  cena = buildScene(estado({}, crew), [agente('blocked', 'spock bloqueado')], T(0))
  assert.equal(cena.personagens.some(p => p.balao), false)
  // working não gera balão
  cena = buildScene(estado(), [doMembro('spock')], T(0), undefined, IDS)
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
  const ws = Array.from({ length: 8 }, (_, i) => worker(i === 2 ? 'T12345678910' : `T${i + 1}`, [`SC-${i}`]))
  const agentes = [agente('done', 'laforge T1'), agente('blocked', 'laforge T12345678910'), agente('waiting', 'laforge T8')]
  const todos: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, '1970-01-01T00:00:00Z']]))
  const trabalhando = MEMBROS.map(m => doMembro(m))
  const mistos = [doMembro('spock'), doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('kirk', 'done')]
  const cenas: Cena[] = []
  for (let ciclo = 0; ciclo < 4; ciclo++) {
    cenas.push(
      buildScene(estado(), [], T(ciclo)),
      buildScene(estado({}, {}, ws), [...agentes, ...mistos], T(ciclo), undefined, IDS),
      buildScene(estado({}, todos, ws.slice(0, 3)), trabalhando, T(ciclo, 5000), undefined, IDS),
      buildScene(estado({}, todos, []), trabalhando, T(ciclo, 59 * 60_000 + 1000), undefined, IDS),
    )
  }
  cenas.push(
    buildScene(estado({}, todos, ws.slice(0, 4)), trabalhando, 30 * 3_600_000 + 2000, undefined, IDS),
    buildScene(estado({ status: 'erro', snapshot: null, error: 'um erro bem longo que precisa quebrar em várias linhas de texto' }), [], 0),
  )
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
        assert.ok(!tocam(a.caixa, b.caixa), `${a.texto} x ${b.texto}`)
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
  // a ponte não estica: tem sempre a mesma altura e a engenharia vem logo abaixo dela
  for (const c of [sem, dois, seis]) {
    assert.equal(c.ponte.altura, PONTE_ALTURA)
    assert.equal(c.engenharia.y, c.ponte.y + c.ponte.altura + 1)
  }
  const alturaArco = (c: Cena) => { const ys = c.estacoes.map(p => p.y); return Math.max(...ys) - Math.min(...ys) }
  assert.equal(alturaArco(sem), alturaArco(seis))
  // o espaço que a engenharia compacta libera vai para as atividades (placeholder claro sem atividade)
  assert.ok(sem.atividades && sem.atividades.y >= sem.engenharia.y + sem.engenharia.altura)
  assert.deepEqual(sem.rotulos.filter(r => r.tipo === 'atividade').map(r => r.texto), ['sem atividade registrada'])
  assert.equal(seis.atividades, null)
})

test('cena desenha a ponte em arco com bonecos', () => {
  const ags = [doMembro('spock'), doMembro('worf')]
  const a = buildScene(estado(), ags, T(0), undefined, IDS)
  const b = buildScene(estado(), ags, T(0, 2250), undefined, IDS)
  const por = (c: Cena, m: string) => c.personagens.find(p => p.membro === m)!
  const picard = a.estacoes.find(e => e.membro === 'picard')!
  const outros = a.estacoes.filter(e => e.membro !== 'picard')
  // Picard maior, no centro da largura e cercado pelas estações
  assert.equal(picard.x, a.grade.largura / 2)
  for (const p of outros) assert.ok(picard.escala > p.escala, p.membro)
  assert.ok(por(a, 'picard').boneco.corpo.altura > por(a, 'data').boneco.corpo.altura)
  // arco agrupado ao redor do capitão: ponte de proporção fixa (a altura do painel não muda as estações) e
  // estações nos quatro lados dele, perto o bastante para formar um conjunto
  const alta = buildScene(estado(), ags, T(0), 220, IDS)
  assert.deepEqual(alta.estacoes, a.estacoes)
  for (const o of outros) assert.ok(Math.hypot(o.x - picard.x, o.y - picard.y) <= 38, `longe do capitão: ${o.membro}`)
  const lado = (f: (e: { x: number; y: number }) => boolean) => outros.filter(f).length
  assert.ok(lado(e => e.x < picard.x - 8) >= 4 && lado(e => e.x > picard.x + 8) >= 4)
  assert.ok(lado(e => e.y < picard.y - 8) >= 3 && lado(e => e.y > picard.y + 8) >= 2)
  // não é grade: as estações não se alinham em poucas linhas
  assert.ok(new Set(outros.map(p => p.y)).size >= 5)
  // boneco: o emoji é a insígnia no peito
  for (const p of a.personagens) {
    const insignia = a.rotulos.find(r => r.tipo === 'emoji' && r.dono === p.membro)!
    const c = p.boneco.corpo
    assert.ok(insignia.x > c.x && insignia.x < c.x + c.largura && insignia.y > c.y && insignia.y < c.y + c.altura, `insígnia fora do peito: ${p.membro}`)
  }
  // o uniforme é o do perfil visual: cada integrante tem a sua cor
  const cores = a.personagens.map(p => p.cor)
  assert.equal(new Set(cores).size, cores.length)
  assert.equal(por(a, 'spock').cor, PERFIS.find(p => p.membro === 'spock')!.cor)
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

test('ponte viva identifica os 12 integrantes', async () => {
  const vistos = new Map<string, Cena['personagens'][number]>()
  const rotulosNome: string[] = []
  // a seleção manual (R10) traz cada integrante à cena: os 12 podem ser vistos
  for (const m of MEMBROS) {
    const cena = buildScene(crewReal(), [], T(0), undefined, IDS, { selecionado: m })
    vistos.set(m, cena.personagens.find(p => p.membro === m)!)
    rotulosNome.push(nomeNaCena(cena, m))
  }
  assert.deepEqual([...vistos.keys()].sort(), [...MEMBROS].sort())
  // src/crew.yaml (lido do arquivo) tem os nomes curtos; a cena mostra o nome completo do perfil (R1), também com
  // snapshot real, cujo `name` é o curto (R1: Jean-Luc Picard, Geordi La Forge, Montgomery Scott...)
  const { readFileSync } = await import('node:fs')
  const { fileURLToPath } = await import('node:url')
  const yaml = readFileSync(fileURLToPath(new URL('../../crew.yaml', import.meta.url)), 'utf8')
  assert.deepEqual([...yaml.matchAll(/^\s+name:\s*(\S.*?)\s*$/gm)].map(m => m[1]), NOMES_CREW)
  assert.deepEqual(NOMES_COMPLETOS.slice().sort(), rotulosNome.slice().sort())
  const ordem = PERFIS.map(p => p.membro)
  // identidade visual própria: uniforme, cabeça, acessório e a assinatura das peças diferem entre os 12
  const lista = ordem.map(m => vistos.get(m)!)
  for (const campo of ['cor', 'pele', 'acessorio'] as const) {
    assert.equal(new Set(lista.map(p => p[campo])).size, 12, `${campo} repetido`)
  }
  assert.equal(new Set(lista.map(p => JSON.stringify(p.pecas.map(x => [x.cor, +(x.x - p.boneco.cabeca.x).toFixed(2), +(x.y - p.boneco.cabeca.y).toFixed(2), +x.largura.toFixed(2), +x.altura.toFixed(2)])))).size, 12)
  for (const p of lista) {
    assert.ok(p.pecas.length > 0, `sem peças: ${p.membro}`)
    assert.equal(p.cor, PERFIS.find(x => x.membro === p.membro)!.cor)
  }
  // o modelo é só dados: as peças vêm de pecasDoPerfil, sem pintura
  const q = lista[ordem.indexOf('q')]
  assert.deepEqual(pecasDoPerfil(q.acessorio, q.boneco, q.escala).pecas, q.pecas)
  assert.deepEqual(pecasDoPerfil('inexistente', q.boneco, 1).pecas, [])
})

function crewReal(): PonteState {
  const s = estado()
  s.snapshot!.crew = MEMBROS.map((m, i) => ({ member: m, emoji: 'x', name: NOMES_CREW[i], count: 0, lastAt: null, cliModel: null }))
  return s
}

/** Seis trabalhando (Q entre eles) e, depois, Q concluindo e Worf assumindo com identidade comprovada. */
const SEIS = ['picard', 'spock', 'troi', 'data', 'laforge']
const ANTES = [...SEIS, 'q'].map(m => doMembro(m))
const DEPOIS = [...SEIS.map(m => doMembro(m)), doMembro('q', 'done'), doMembro('worf')]
const noRastro = (rastro: Rastro, ags: PonteAgent[], t: number, extra: Record<string, unknown> = {}): Cena =>
  buildScene(estado(), ags, t, undefined, IDS, { rastro, ...extra })
const porMembro = (c: Cena, m: string) => c.personagens.find(p => p.membro === m)
const estadosDe = (ags: PonteAgent[]): EstadoDoMembro[] => estadosDaTripulacao({ ...estado(), agents: ags }, IDS)
const est = (alertas: number, trabalhando = 0): EstadoDoMembro[] => MEMBROS.map((membro, i) => ({
  membro, motivo: '', estado: i < alertas ? 'bloqueado' : i < alertas + trabalhando ? 'trabalhando' : 'ocioso',
}))

test('ponte viva limita a seis integrantes', () => {
  const todos = MEMBROS.map(m => doMembro(m))
  // os agentes que trabalham mudam de tempos em tempos: nunca passa de seis, nem durante as trocas
  const mudando = (t: number): PonteAgent[] => Array.from({ length: 5 }, (_, i) => doMembro(MEMBROS[(Math.floor(t / 1500) + i * 2) % 12], i % 2 ? 'blocked' : 'working'))
  for (const ags of [(): PonteAgent[] => [], (): PonteAgent[] => todos, mudando]) {
    const rastro = criaRastroPresenca()
    for (let t = 0; t < 30_000; t += 100) {
      const cena = buildScene(crewReal(), ags(t), t, undefined, IDS, { rastro })
      assert.ok(cena.personagens.length <= 6, `${cena.personagens.length} em ${t} ms`)
      const nomes = cena.rotulos.filter(r => r.tipo === 'nome')
      assert.ok(nomes.length <= 12) // até duas linhas por presente
      // cada presente tem o nome completo junto de si, legível, mesmo com o snapshot real (name curto)
      assert.deepEqual([...new Set(nomes.map(r => r.dono))].sort(), membrosDe(cena).sort())
      for (const p of cena.personagens) assert.equal(nomeNaCena(cena, p.membro), NOMES_COMPLETOS[MEMBROS.indexOf(p.membro)])
    }
  }
  assert.equal(buildScene(crewReal(), [], T(0), undefined, IDS).personagens.length, 6)
  assert.equal(buildScene(crewReal(), todos, T(0), undefined, IDS).personagens.length, 6)
})

test('ponte viva mantém presença sem rodízio', () => {
  // estados iguais: os mesmos integrantes em qualquer instante, sem transição e sem trocar de lugar (R3)
  for (const ags of [[], ANTES, MEMBROS.map(m => doMembro(m))]) {
    const rastro = criaRastroPresenca()
    const ref = noRastro(rastro, ags, 0)
    assert.equal(ref.personagens.length, 6)
    for (let t = 250; t <= 5 * 60_000; t += 4_750) {
      const cena = noRastro(rastro, ags, t)
      assert.deepEqual(membrosDe(cena), membrosDe(ref), `${t} ms`)
      assert.ok(cena.personagens.every(p => p.transicao === null), `${t} ms`)
      assert.deepEqual(cena.personagens.map(p => [p.x, p.y]), ref.personagens.map(p => [p.x, p.y]))
    }
  }
  // sem estado guardado (cena avulsa) a escolha também não depende do relógio
  const seis = ['picard', 'spock', 'troi', 'data', 'laforge', 'q']
  assert.deepEqual(membrosDe(buildScene(estado(), ANTES, 0, undefined, IDS)), seis)
  for (const n of [1, 2, 9, 1000]) assert.deepEqual(membrosDe(buildScene(estado(), ANTES, T(n), undefined, IDS)), seis)
  // a escolha devolvida, usada como presença anterior, se repete
  const e = estadosDe(ANTES)
  const um = selecionaPresentes(e, [])
  assert.deepEqual(um, seis)
  assert.deepEqual(selecionaPresentes(e, um), um)
})

test('ponte viva prioriza presença estável', () => {
  // sete alertas comprovados: seis vagas; os já presentes ficam em caso de mesma prioridade (R19)
  const sete = est(7)
  assert.deepEqual(selecionaPresentes(sete, []), ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
  assert.deepEqual(selecionaPresentes(sete, ['spock', 'troi', 'data', 'laforge', 'mccoy', 'q']), ['spock', 'troi', 'data', 'laforge', 'mccoy', 'q'])
  // alerta (bloqueado ou aguardando) antes de trabalhando, e trabalhando antes dos demais
  const mistos: EstadoDoMembro[] = MEMBROS.map((membro, i) => ({
    membro, motivo: '', estado: i === 10 ? 'bloqueado' : i === 11 ? 'aguardando' : i >= 2 && i < 9 ? 'trabalhando' : 'ocioso',
  }))
  assert.deepEqual(selecionaPresentes(mistos, []), ['troi', 'data', 'laforge', 'mccoy', 'worf', 'guinan'])
  // quem trabalha e já está presente permanece; o recém-chegado só entra se houver vaga ou prioridade maior
  assert.deepEqual(selecionaPresentes(mistos, ['q', 'uhura', 'scotty', 'kirk']), ['troi', 'q', 'uhura', 'scotty', 'worf', 'guinan'])
  // cabem todos: ociosos ocupam as vagas livres, e o ocioso presente é mantido contra outro ocioso
  assert.deepEqual(selecionaPresentes(est(1, 1), []), ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
  assert.deepEqual(selecionaPresentes(est(1, 1), ['guinan', 'worf', 'kirk', 'scotty']), ['picard', 'spock', 'scotty', 'kirk', 'worf', 'guinan'])
  // dados incertos: nada muda por causa deles, nem entrada nem saída
  const incertos = estadosDaTripulacao(estado({ stale: true }, { spock: [1, null] }), IDS)
  assert.ok(incertos.every(x => x.estado === 'desconhecido'))
  assert.deepEqual(selecionaPresentes(incertos, ['guinan', 'q', 'kirk', 'worf', 'scotty', 'uhura']), ['q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan'])
  // Q conclui e Worf assume com identidade comprovada: só Q sai e só Worf entra, os outros cinco ficam
  const rastro = criaRastroPresenca()
  const antes = noRastro(rastro, ANTES, 0)
  assert.deepEqual(membrosDe(antes), ['picard', 'spock', 'troi', 'data', 'laforge', 'q'])
  const ini = 20_000
  assert.deepEqual(membrosDe(noRastro(rastro, ANTES, ini - 1)), membrosDe(antes))
  noRastro(rastro, DEPOIS, ini) // a mudança real começa aqui
  const durante = noRastro(rastro, DEPOIS, ini + 300)
  assert.deepEqual(membrosDe(durante), ['picard', 'spock', 'troi', 'data', 'laforge', 'q'])
  for (const m of SEIS) assert.equal(porMembro(durante, m)!.transicao, null, m)
  assert.deepEqual(porMembro(durante, 'q')!.transicao, { fase: 'saindo', progresso: 0.5 })
  assert.deepEqual(membrosDe(noRastro(rastro, DEPOIS, ini + 5000)), ['picard', 'spock', 'troi', 'data', 'laforge', 'worf'])
  // sem identidade comprovada o Worf não assume: o agente não vinculado não muda a presença (R22)
  const solto = criaRastroPresenca()
  noRastro(solto, ANTES, 0)
  const semId = noRastro(solto, [...SEIS.map(m => doMembro(m)), doMembro('q'), { ...doMembro('worf'), terminalId: null }], 30_000)
  assert.deepEqual(membrosDe(semId), ['picard', 'spock', 'troi', 'data', 'laforge', 'q'])
  assert.ok(semId.personagens.every(p => p.transicao === null))
})

test('ponte viva mantém integrante já presente', () => {
  const rastro = criaRastroPresenca()
  const base = noRastro(rastro, ANTES, 0)
  const rel = (sel: string | null) => relacaoDaTripulacao(estado(), ANTES, 5000, IDS, { rastro, selecionado: sel })
  const sem = rel(null)
  // acionar quem já está presente: mesma composição, sem transição e com o mesmo estado (R20)
  for (const m of ['q', 'picard']) {
    const cena = noRastro(rastro, ANTES, 5000, { selecionado: m })
    assert.deepEqual(membrosDe(cena), membrosDe(base))
    assert.ok(cena.personagens.every(p => p.transicao === null))
    assert.equal(porMembro(cena, m)!.estado, 'trabalhando')
    assert.deepEqual(cena.personagens.map(p => p.estado), base.personagens.map(p => p.estado))
    const item = rel(m).find(i => i.membro === m)!
    assert.equal(item.selecionado, true)
    assert.equal(item.presente, true)
    assert.equal(item.estado, 'trabalhando')
    assert.deepEqual(rel(m).map(i => [i.membro, i.presente, i.estado]), sem.map(i => [i.membro, i.presente, i.estado]))
  }
  // soltar a seleção também não mexe em quem está presente
  assert.deepEqual(membrosDe(noRastro(rastro, ANTES, 9000)), membrosDe(base))
})

test('ponte viva anima sem alterar estado', () => {
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t
  const rastro = criaRastroPresenca()
  const inicial = noRastro(rastro, ANTES, 0)
  // a primeira cena já nasce povoada, sem ninguém andando
  assert.ok(inicial.personagens.every(p => p.transicao === null))
  const ini = 20_000
  noRastro(rastro, DEPOIS, ini) // a mudança real começa aqui
  // saída (primeira metade): só Q anda até o acesso; os outros cinco seguem parados
  const saindo = noRastro(rastro, DEPOIS, ini + TRANSICAO_MS / 4)
  const q = porMembro(saindo, 'q')!
  assert.deepEqual(q.transicao, { fase: 'saindo', progresso: 0.5 })
  assert.ok(Math.abs(q.x - lerp(q.estacao.x, saindo.porta.x, 0.5)) < 1e-9 && Math.abs(q.y - lerp(q.estacao.y, saindo.porta.y, 0.5)) < 1e-9)
  assert.ok(q.opacidade < 1)
  assert.equal(saindo.personagens.filter(p => p.transicao !== null).length, 1)
  assert.equal(porMembro(saindo, 'worf'), undefined)
  // entrada (segunda metade): Worf sai do acesso até a estação; Q já saiu
  const entrando = noRastro(rastro, DEPOIS, ini + (TRANSICAO_MS * 3) / 4)
  const w = porMembro(entrando, 'worf')!
  assert.deepEqual(w.transicao, { fase: 'entrando', progresso: 0.5 })
  assert.ok(Math.abs(w.x - lerp(entrando.porta.x, w.estacao.x, 0.5)) < 1e-9 && Math.abs(w.y - lerp(entrando.porta.y, w.estacao.y, 0.5)) < 1e-9)
  assert.equal(porMembro(entrando, 'q'), undefined)
  // o estado real não muda em nenhum ponto: Q concluído e Worf trabalhando, só a posição anda
  assert.equal(q.estado, 'concluido')
  assert.equal(w.estado, 'trabalhando')
  assert.equal(w.ativo, false)
  assert.equal(w.pose, 'de-pe')
  assert.equal(w.brilho, null)
  const chegou = porMembro(noRastro(rastro, DEPOIS, ini + TRANSICAO_MS), 'worf')!
  assert.equal(chegou.transicao, null)
  assert.equal(chegou.estado, 'trabalhando')
  assert.equal(chegou.ativo, true)
  assert.equal(chegou.pose, 'sentado')
  assert.deepEqual([chegou.x, chegou.y], [chegou.estacao.x, chegou.estacao.y])
  // não há mais de seis em nenhum quadro da troca, e uma troca simultânea de vários também respeita o limite
  const r2 = criaRastroPresenca()
  noRastro(r2, ANTES, 0)
  const todosAlerta = MEMBROS.slice(6).map(m => doMembro(m, 'blocked'))
  for (let t = ini; t <= ini + 4 * TRANSICAO_MS; t += 50) {
    const c = noRastro(r2, todosAlerta, t)
    assert.ok(c.personagens.length <= 6, `${c.personagens.length} em ${t - ini} ms`)
  }
  assert.deepEqual(membrosDe(noRastro(r2, todosAlerta, ini + 5 * TRANSICAO_MS)), ['q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan'])
})

test('ponte viva representa trabalho', () => {
  const ags = [doMembro('spock')]
  const a = buildScene(estado(), ags, T(0), undefined, IDS)
  const b = buildScene(estado(), ags, T(0, 2250), undefined, IDS)
  const spock = a.personagens.find(p => p.membro === 'spock')!
  assert.equal(spock.estado, 'trabalhando')
  assert.equal(spock.simbolo, ESTADOS.trabalhando.simbolo)
  assert.equal(spock.simbolo, '⚙')
  assert.equal(spock.textoEstado, 'trabalhando')
  assert.ok(a.rotulos.some(r => r.tipo === 'estado' && r.dono === 'spock' && r.texto === '⚙'))
  // operação do console: aceso com brilho, sentado, braços alternando
  assert.equal(spock.ativo, true)
  assert.equal(spock.pose, 'sentado')
  assert.ok(spock.brilho)
  assert.equal(spock.opacidade, 1)
  assert.notDeepEqual(spock.boneco.bracos, b.personagens.find(p => p.membro === 'spock')!.boneco.bracos)
  assert.equal(a.ativos, 1)
})

test('ponte viva representa ociosidade', () => {
  const ags = [doMembro('spock'), doMembro('kirk', 'done')]
  const a = buildScene(estado(), ags, T(0), undefined, IDS)
  const b = buildScene(estado(), ags, T(0, 2250), undefined, IDS)
  const data = a.personagens.find(p => p.membro === 'data')!
  assert.equal(data.estado, 'ocioso')
  assert.equal(data.simbolo, '💤')
  assert.equal(data.textoEstado, 'ocioso')
  assert.ok(a.rotulos.some(r => r.tipo === 'estado' && r.dono === 'data' && r.texto === '💤'))
  // sem animação de trabalho: de pé, console apagado, quadro e braços parados
  assert.equal(data.ativo, false)
  assert.equal(data.pose, 'de-pe')
  assert.equal(data.brilho, null)
  assert.equal(data.quadro, 0)
  assert.ok(data.opacidade <= OPACIDADE_LIVRE)
  assert.equal(data.tempo, null)
  assert.deepEqual(data.boneco, b.personagens.find(p => p.membro === 'data')!.boneco)
})

test('ponte viva distingue estados', () => {
  const ags = [doMembro('spock'), doMembro('data', 'waiting'), doMembro('worf', 'blocked'), doMembro('picard', 'done')]
  const cena = buildScene(estado(), ags, T(0), undefined, IDS)
  const por = (m: string) => cena.personagens.find(p => p.membro === m)!
  assert.equal(por('spock').estado, 'trabalhando')
  assert.equal(por('data').estado, 'aguardando')
  assert.equal(por('worf').estado, 'bloqueado')
  assert.equal(por('picard').estado, 'concluido')
  const simbolos = ['spock', 'data', 'worf', 'picard'].map(m => cena.rotulos.find(r => r.tipo === 'estado' && r.dono === m)!.texto)
  assert.deepEqual(simbolos, ['⚙', '⏳', '⛔', '✔'])
  assert.equal(new Set(simbolos).size, 4)
  assert.deepEqual(['spock', 'data', 'worf', 'picard'].map(m => por(m).textoEstado), ['trabalhando', 'aguardando', 'bloqueado', 'concluído'])
  // só espera e bloqueio levantam o balão de alerta; só quem trabalha acende o console
  assert.deepEqual(cena.personagens.filter(p => p.balao).map(p => p.membro).sort(), ['data', 'worf'])
  assert.deepEqual(cena.personagens.filter(p => p.ativo).map(p => p.membro), ['spock'])
})

test('ponte viva não inventa atividade', () => {
  const comCount: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [5, '2026-01-01T00:00:00Z']]))
  const semTrabalho = (c: Cena) => c.personagens.every(p => p.estado !== 'trabalhando' && !p.ativo && p.brilho === null && p.pose === 'de-pe')
  // agente trabalhando sem vínculo confiável, ou com título parecido, e sem count que o explique: tudo desconhecido
  for (const ags of [
    [{ ...doMembro('spock'), terminalId: null }],
    [{ ...doMembro('spock'), title: 'spock implementando' }],
    [doMembro('spock')], // vínculo fora de `ids`: o mapa vazio não conhece o terminal
  ]) {
    const cena = buildScene(estado(), ags, T(0))
    assert.ok(semTrabalho(cena))
    assert.ok(cena.personagens.every(p => p.estado === 'desconhecido' && p.simbolo === '?' && p.textoEstado === 'desconhecido'))
    assert.equal(cena.ativos, 0)
    assert.ok(cena.rotulos.some(r => r.tipo === 'telao' && r.texto === 'tripulação em repouso'))
    for (const p of cena.personagens) assert.ok(p.opacidade <= OPACIDADE_LIVRE)
  }
  // sem agente e sem count: ocioso, não trabalho
  assert.ok(buildScene(estado(), [], T(0)).personagens.every(p => p.estado === 'ocioso'))
  // dado antigo ou com erro: desconhecido mesmo com count > 0, e a cena segue mostrando o último estado bom
  for (const over of [{ stale: true }, { status: 'erro' as const, error: 'falhou' }]) {
    const cena = buildScene(estado(over, comCount), [doMembro('spock')], T(0), undefined, IDS)
    assert.equal(cena.vazia, false)
    assert.ok(semTrabalho(cena) && cena.personagens.every(p => p.estado === 'desconhecido'))
    assert.equal(cena.ativos, 0)
  }
})

test('ponte viva destaca quem trabalha no fluxo snapshot para cena', () => {
  // snapshot como o ponte.py entrega: count agrega as sessões do repositório; só agente vinculado prova trabalho no foco
  const lastAt = new Date(T(0) - 2 * 60_000).toISOString()
  const crew: Record<string, [number, string]> = { picard: [1, lastAt], laforge: [3, lastAt], spock: [1, lastAt] }
  // só o count: atividade do repositório sem prova neste worktree, ninguém se destaca como trabalhando
  const semVinculo = buildScene(estado({}, crew), [], T(0))
  assert.equal(semVinculo.ativos, 0)
  assert.ok(semVinculo.personagens.every(p => !p.ativo && p.estado !== 'trabalhando' && p.brilho === null))
  for (const m of ['picard', 'laforge', 'spock']) assert.equal(semVinculo.personagens.find(p => p.membro === m)!.estado, 'desconhecido')
  const agenteSemVinculo = agente('working', 'claude') // agente sem vínculo confiável
  for (const ags of [[], [agenteSemVinculo]]) {
    const cena = buildScene(estado({}, crew), [...ags, doMembro('picard'), doMembro('laforge'), doMembro('spock')], T(0), undefined, IDS)
    const ativos = cena.personagens.filter(p => p.ativo)
    // pelo menos um se destaca: sentado, console aceso, símbolo de trabalho e "há 2 min"
    assert.ok(ativos.length > 0, 'ninguém se destaca')
    assert.deepEqual(ativos.map(p => p.membro).sort(), ['laforge', 'picard', 'spock'])
    for (const p of ativos) {
      assert.equal(p.estado, 'trabalhando')
      assert.equal(p.pose, 'sentado')
      assert.ok(p.brilho)
      assert.equal(p.opacidade, 1)
      assert.ok(cena.rotulos.some(r => r.tipo === 'estado' && r.dono === p.membro && r.texto === '⚙'))
      assert.equal(cena.rotulos.find(r => r.tipo === 'tempo' && r.dono === p.membro)?.texto, 'há 2 min')
    }
    // quem não tem agente vinculado nem count positivo é ocioso; com agente sem vínculo ninguém é ocioso sem evidência
    const esperado = ags.length === 0 ? 'ocioso' : 'desconhecido'
    assert.ok(cena.personagens.filter(p => !p.ativo).every(p => p.estado === esperado && p.brilho === null))
    assert.equal(cena.ativos, 3)
    assert.ok(cena.rotulos.some(r => r.tipo === 'telao' && r.texto === '3 tripulantes ativos'))
  }
  // 12 agentes vinculados trabalhando: os mesmos seis ficam, em qualquer instante (R3)
  const todos: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, lastAt]]))
  for (const n of [0, 1, 7]) {
    const cena = buildScene(estado({}, todos), MEMBROS.map(m => doMembro(m)), T(n), undefined, IDS)
    assert.deepEqual(membrosDe(cena), ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
    assert.ok(cena.personagens.every(p => p.ativo))
  }
})

test('ponte viva mantém rótulos legíveis', () => {
  const mistos = [doMembro('spock'), doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('kirk', 'done'), doMembro('guinan')]
  // quatro alertas novos tiram quatro dos seis presentes: saídas e entradas simultâneas
  const troca = [...mistos, ...['laforge', 'mccoy', 'q', 'uhura'].map(m => doMembro(m, 'blocked'))]
  const lastAt = new Date(T(0) - 59 * 60_000).toISOString()
  const crew: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, lastAt]]))
  const fases = new Set<string>()
  for (const largura of [240, 360]) {
    const e = Math.max(5, Math.floor(largura / GRADE.largura)) // pixels por célula
    for (const altura of [500, 900, 1400]) {
      const linhas = linhasDoPainel(largura, altura)
      const instantes = [100, 500, TRANSICAO_MS / 2, 700, 1100, 1500, 2000, 5000] // em ordem: o relógio só avança
      for (const [antes, depois] of [[[], []], [mistos, troca], [MEMBROS.map(m => doMembro(m)), MEMBROS.map(m => doMembro(m, 'blocked'))]] as PonteAgent[][][]) {
        const rastro = criaRastroPresenca()
        buildScene(estado({}, crew, [worker('T1')]), antes, 0, linhas, IDS, { rastro })
        buildScene(estado({}, crew, [worker('T1')]), depois, 20_000, linhas, IDS, { rastro }) // a mudança real começa aqui
        for (const extra of instantes) {
          const cena = buildScene(estado({}, crew, [worker('T1')]), depois, 20_000 + extra, linhas, IDS, { rastro })
          for (const pe of cena.personagens) if (pe.transicao) fases.add(`${largura}:${pe.transicao.fase}`)
          assert.equal(cena.grade.altura, linhas)
          assert.ok(cena.personagens.length <= 6)
          if (extra >= 1500 || antes.length === 0) assert.equal(cena.personagens.length, 6)
          for (const r of cena.rotulos) {
            assert.ok(Math.round(r.tam * e) >= 10, `${largura}px: fonte pequena em ${r.texto}`)
            assert.ok(r.caixa.x >= 0 && r.caixa.y >= 0 && r.caixa.x + r.caixa.largura <= cena.grade.largura && r.caixa.y + r.caixa.altura <= cena.grade.altura, `${largura}px: ${r.texto} cortado`)
          }
          for (let i = 0; i < cena.rotulos.length; i++) {
            for (let j = i + 1; j < cena.rotulos.length; j++) {
              assert.ok(!tocam(cena.rotulos[i].caixa, cena.rotulos[j].caixa), `${largura}px: ${cena.rotulos[i].texto} x ${cena.rotulos[j].texto}`)
            }
          }
          // cada presente mostra nome e indicador de estado próprios
          for (const p of cena.personagens) {
            assert.equal(nomeNaCena(cena, p.membro), NOMES_COMPLETOS[MEMBROS.indexOf(p.membro)], `${largura}px: nome de ${p.membro}`)
            assert.ok(cena.rotulos.some(r => r.tipo === 'estado' && r.dono === p.membro && r.texto === p.simbolo))
          }
        }
      }
    }
  }
  // as fases de entrada e saída foram exercitadas nos dois tamanhos
  assert.deepEqual([...fases].sort(), ['240:entrando', '240:saindo', '360:entrando', '360:saindo'])
})

test('ponte viva preserva transição em atualização repetida', () => {
  const ini = 20_000
  const mesmo = (): PonteState => JSON.parse(JSON.stringify(estado({ updatedAt: 99, log: [{ at: 1, text: 'x' }] })))
  const copia = (): PonteAgent[] => DEPOIS.map(x => ({ ...x }))
  const instante = (c: Cena) => c.personagens.map(p => [p.membro, p.transicao, p.x, p.y, p.opacidade])
  const rastro = criaRastroPresenca()
  noRastro(rastro, ANTES, 0)
  const vistos: number[] = []
  buildScene(mesmo(), copia(), ini, undefined, IDS, { rastro }) // a mudança real começa aqui
  for (const extra of [100, 300, 600, 700, 800, 900, 1000, 1100]) {
    const t = ini + extra
    // atualização repetida (cópia nova do estado, agentes recriados) no mesmo instante: a cena não muda, nem a transição
    const um = buildScene(mesmo(), copia(), t, undefined, IDS, { rastro })
    const dois = buildScene(mesmo(), copia(), t, undefined, IDS, { rastro })
    assert.deepEqual(instante(um), instante(dois), `${extra} ms`)
    const w = porMembro(um, 'worf')?.transicao
    if (w) vistos.push(w.progresso)
  }
  // a entrada segue o relógio e não reinicia: de 600 a 1100 ms o progresso só cresce, a partir de 0
  assert.equal(vistos.length, 6)
  assert.equal(vistos[0], 0)
  for (let i = 1; i < vistos.length; i++) assert.ok(vistos[i] > vistos[i - 1], `reiniciou: ${vistos}`)
  assert.ok(Math.abs(vistos[5] - 5 / 6) < 1e-9)
  assert.equal(porMembro(noRastro(rastro, DEPOIS, ini + 1200), 'worf')!.transicao, null)
  // repetir o estado depois de assentar não inicia transição alguma
  for (const extra of [1300, 4000, 9000]) assert.ok(noRastro(rastro, DEPOIS, ini + extra).personagens.every(p => p.transicao === null))
})

test('ponte viva lista os 12 integrantes', () => {
  const base = estado({}, { spock: [1, null] })
  const agentes = [doMembro('worf', 'blocked'), doMembro('kirk', 'done'), doMembro('spock')]
  const agora = T(0)
  const itens = relacaoDaTripulacao(base, agentes, agora, IDS)
  assert.deepEqual(itens.map(i => i.membro), MEMBROS)
  // com crew.name = id no snapshot, o nome exibido é o do snapshot; o texto de leitor de tela diz nome, estado e presença
  const cena = buildScene(base, agentes, agora, undefined, IDS)
  const naCena = new Set(membrosDe(cena))
  const estados = estadosDaTripulacao({ ...base, agents: agentes }, IDS)
  for (const i of itens) {
    const e = estados.find(x => x.membro === i.membro)!
    assert.equal(i.estado, e.estado)
    assert.equal(i.textoEstado, ESTADOS[e.estado].texto)
    assert.equal(i.simbolo, ESTADOS[e.estado].simbolo)
    assert.equal(i.presente, naCena.has(i.membro))
    assert.equal(i.descricao, `${i.nome}, ${ESTADOS[e.estado].texto}, ${i.presente ? 'na cena' : 'fora da cena'}`)
  }
  assert.equal(itens.find(i => i.membro === 'worf')!.descricao, 'Worf, bloqueado, na cena')
  assert.equal(itens.find(i => i.membro === 'spock')!.descricao, 'Spock, trabalhando, na cena')
  // com snapshot real (name curto) a relação mostra o nome completo do perfil
  const real = relacaoDaTripulacao(crewReal(), [doMembro('picard'), doMembro('laforge', 'blocked')], agora, IDS)
  assert.deepEqual(real.map(i => i.nome), NOMES_COMPLETOS)
  assert.equal(real.find(i => i.membro === 'picard')!.descricao, 'Jean-Luc Picard, trabalhando, na cena')
  assert.equal(real.find(i => i.membro === 'laforge')!.descricao, 'Geordi La Forge, bloqueado, na cena')
  assert.equal(itens.find(i => i.membro === 'kirk')!.estado, 'concluido')
  assert.ok(itens.some(i => !i.presente), 'há integrantes fora da cena e eles continuam na relação')
  assert.equal(itens.filter(i => i.presente).length, 6)
  // sem snapshot os 12 continuam listados, desconhecidos e fora da cena; nome vem dos perfis
  const sem = relacaoDaTripulacao({ ...base, status: 'sem-worktree', snapshot: null }, [], agora, IDS)
  assert.deepEqual(sem.map(i => i.nome), NOMES_COMPLETOS)
  assert.ok(sem.every(i => i.estado === 'desconhecido' && !i.presente && i.descricao === `${i.nome}, desconhecido, fora da cena`))
  // a relação não afirma escopo de worktree
  assert.ok(itens.every(i => !/worktree/i.test(i.descricao)))
})

test('ponte viva permite selecionar integrante', () => {
  const base = estado({}, { spock: [1, null] })
  const agentes = [doMembro('worf', 'blocked')]
  const agora = T(0)
  const antes = relacaoDaTripulacao(base, agentes, agora, IDS)
  const fora = antes.find(i => !i.presente)!
  assert.equal(fora.estado, 'ocioso')
  const opcoes = { selecionado: fora.membro }
  const depois = relacaoDaTripulacao(base, agentes, agora, IDS, opcoes)
  const item = depois.find(i => i.membro === fora.membro)!
  assert.equal(item.presente, true)
  assert.equal(item.selecionado, true)
  assert.equal(item.estado, fora.estado) // estado real intacto
  assert.equal(depois.filter(i => i.selecionado).length, 1)
  const cena = buildScene(base, agentes, agora, undefined, IDS, opcoes)
  assert.equal(cena.personagens.length, 6)
  assert.ok(membrosDe(cena).includes(fora.membro))
  assert.equal(cena.personagens.find(p => p.membro === fora.membro)!.estado, 'ocioso')
  assert.ok(membrosDe(cena).includes('worf') && membrosDe(cena).includes('spock')) // alerta e quem trabalha seguem
  // selecionar quem já está na cena não muda nada; id desconhecido é ignorado
  assert.deepEqual(membrosDe(buildScene(base, agentes, agora, undefined, IDS, { selecionado: 'worf' })), membrosDe(buildScene(base, agentes, agora, undefined, IDS)))
  assert.deepEqual(membrosDe(buildScene(base, agentes, agora, undefined, IDS, { selecionado: 'nemo' })), membrosDe(buildScene(base, agentes, agora, undefined, IDS)))
  assert.deepEqual(selecionaPresentes(estadosDaTripulacao(base, IDS), [], 'guinan').includes('guinan'), true)
  // com a cena em andamento, o selecionado entra pelo acesso no lugar de quem tem a menor prioridade (R10)
  const rastro = criaRastroPresenca()
  const sem = buildScene(base, agentes, T(0), undefined, IDS, { rastro })
  assert.deepEqual(membrosDe(sem), ['picard', 'spock', 'troi', 'data', 'laforge', 'worf'])
  const agoraSel = 20_000
  const saindo = buildScene(base, agentes, agoraSel + 100, undefined, IDS, { rastro, selecionado: 'guinan' })
  assert.deepEqual(saindo.personagens.find(p => p.transicao)!.membro, 'laforge')
  assert.deepEqual(saindo.personagens.find(p => p.transicao)!.transicao!.fase, 'saindo')
  assert.equal(saindo.personagens.some(p => p.membro === 'guinan'), false)
  const entrando = buildScene(base, agentes, agoraSel + 900, undefined, IDS, { rastro, selecionado: 'guinan' })
  const g = entrando.personagens.find(p => p.membro === 'guinan')!
  assert.equal(g.transicao!.fase, 'entrando')
  assert.equal(g.estado, 'ocioso') // a animação não toca no estado real
  for (const n of [1, 5, 50]) {
    const cena = buildScene(base, agentes, agoraSel + 5000 * n, undefined, IDS, { rastro, selecionado: 'guinan' })
    assert.deepEqual(membrosDe(cena), ['picard', 'spock', 'troi', 'data', 'worf', 'guinan'])
    assert.ok(cena.personagens.every(p => p.transicao === null))
  }
})

test('ponte viva mantém a seleção ao acionar quem já está na cena', () => {
  // seis trabalhando; Q (ocioso, fora da cena) é trazido pela seleção e depois aciona-se o Picard, que já está presente
  const base = estado()
  const agentes = ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'].map(m => doMembro(m))
  const presentes = (sel: string | null): string[] =>
    relacaoDaTripulacao(base, agentes, 0, IDS, { selecionado: sel }).filter(i => i.presente).map(i => i.membro)
  let sel: string | null = null
  sel = alternaSelecao(sel, 'q', presentes(sel))
  assert.equal(sel, 'q')
  assert.ok(presentes(sel).includes('q'))
  sel = alternaSelecao(sel, 'picard', presentes(sel))
  assert.equal(sel, 'q') // acionar quem já está presente não troca a seleção
  assert.ok(presentes(sel).includes('q') && presentes(sel).includes('picard'))
  // a mesma seleção desmarca; outro integrante fora da cena substitui
  assert.equal(alternaSelecao('q', 'q', presentes('q')), null)
  assert.equal(alternaSelecao('q', 'guinan', presentes('q')), 'guinan')
  assert.equal(alternaSelecao(null, 'picard', presentes(null)), null)
})

test('ponte viva informa dados desatualizados', () => {
  const lv = new Date(2026, 10, 22, 9, 5, 7).getTime()
  assert.equal(horario(lv), '09:05:07')
  assert.equal(avisoDeDados(estado()), null)
  assert.equal(avisoDeDados(estado({ status: 'sem-worktree', snapshot: null })), null)
  // sessions.json ilegível: contagem nula avisa e nunca vira ocioso (SC-216, W2)
  const ilegivel = estado()
  ilegivel.snapshot!.crew = ilegivel.snapshot!.crew.map(c => ({ ...c, count: null, sessions: [] }))
  assert.equal(avisoDeDados(ilegivel), 'Sessões da tripulação ilegíveis; estados desconhecidos')
  assert.ok(estadosDaTripulacao(ilegivel, IDS).every(e => e.estado === 'desconhecido'))
  assert.equal(
    avisoDeDados(estado({ status: 'erro', stale: true, error: 'boom' + String.fromCharCode(10) + 'segunda', lastValidAt: lv })),
    'Dados indisponíveis (boom); última atualização válida às 09:05:07',
  )
  assert.equal(
    avisoDeDados(estado({ stale: true, lastValidAt: lv })),
    'Dados desatualizados; última atualização válida às 09:05:07',
  )
  assert.equal(
    avisoDeDados(estado({ status: 'erro', stale: false, error: 'x', snapshot: null, lastValidAt: null })),
    'Dados indisponíveis (x); ainda sem atualização válida',
  )
  // com dados antigos nenhum integrante afirma trabalho: todos desconhecidos, ainda listados
  const itens = relacaoDaTripulacao(estado({ stale: true, lastValidAt: lv }, { spock: [1, null] }), [], T(0), IDS)
  assert.equal(itens.length, 12)
  assert.ok(itens.every(i => i.estado === 'desconhecido'))
})

test('ponte viva respeita movimento reduzido', () => {
  const r = { reduzido: true }
  const ini = 20_000
  const rastro = criaRastroPresenca()
  noRastro(rastro, ANTES, 0, r)
  // sem deslocamento: Q conclui e Worf assume já na primeira atualização, sem ninguém andando (R17)
  for (const extra of [0, 100, 300, 600, 900, 1100, 1300]) {
    const cena = noRastro(rastro, DEPOIS, ini + extra, r)
    assert.deepEqual(membrosDe(cena), ['picard', 'spock', 'troi', 'data', 'laforge', 'worf'], String(extra))
    assert.ok(cena.personagens.every(p => p.transicao === null && p.opacidade >= 0.6), String(extra))
    assert.ok(cena.personagens.every(p => p.quadro === 0), String(extra))
    for (const p of cena.personagens) assert.deepEqual([p.x, p.y], [p.estacao.x, p.estacao.y])
    assert.equal(porMembro(cena, 'worf')!.estado, 'trabalhando')
  }
  // a mesma troca com movimento normal anima
  const normal = criaRastroPresenca()
  noRastro(normal, ANTES, 0)
  assert.ok(noRastro(normal, DEPOIS, ini + TRANSICAO_MS / 4).personagens.some(p => p.transicao !== null))
  // acesso manual preservado: a seleção traz o integrante na hora, sem transição, com o estado dele intacto
  const fora = 'guinan'
  const cena = noRastro(rastro, DEPOIS, ini + 5000, { ...r, selecionado: fora })
  assert.ok(membrosDe(cena).includes(fora))
  assert.equal(cena.personagens.length, 6)
  assert.ok(cena.personagens.every(p => p.transicao === null))
  assert.equal(porMembro(cena, fora)!.estado, 'ocioso')
  const item = relacaoDaTripulacao(estado(), DEPOIS, ini + 5000, IDS, { ...r, rastro, selecionado: fora }).find(i => i.membro === fora)!
  assert.equal(item.presente, true)
  assert.equal(item.selecionado, true)
})

test('ponte viva legibilidade: corpo apagado continua visível e o nome é maior que 10 px a 240 px', () => {
  // ocioso ou desconhecido fica apagado, mas acima de 50%: na captura real a 40% o uniforme sumia no fundo
  assert.ok(OPACIDADE_LIVRE > 0.5 && OPACIDADE_LIVRE < 1)
  const cena = buildScene(estado(), [], T(0), undefined, IDS)
  for (const p of cena.personagens) assert.ok(p.opacidade >= 0.5, `${p.membro} apagado demais`)
  const nomes = cena.rotulos.filter(r => r.tipo === 'nome')
  assert.ok(nomes.length > 6)
  for (const n of nomes) {
    assert.equal(n.tam, TAM_NOME)
    assert.ok(Math.round(n.tam * 5) >= 11, `nome a 240 px: ${Math.round(n.tam * 5)} px`)
  }
  // as linhas de um mesmo nome não se tocam (a fonte maior pede mais espaço entre elas)
  for (const p of cena.personagens) {
    const linhas = nomes.filter(r => r.dono === p.membro)
    for (let i = 1; i < linhas.length; i++) assert.ok(linhas[i].caixa.y >= linhas[i - 1].caixa.y + linhas[i - 1].caixa.altura)
  }
})

test('ponte viva resume os sem prova em uma linha em vez de repetir desconhecido 12 vezes', () => {
  const indisponivel = estado({ status: 'erro', stale: true, error: 'x' })
  const atividades = (c: Cena) => c.rotulos.filter(r => r.tipo === 'atividade').map(r => r.texto)
  // todos desconhecidos (dados antigos): uma linha só, com a contagem
  const todos = buildScene(indisponivel, [], T(0), undefined, IDS)
  assert.deepEqual(atividades(todos), ['? 12 desconhecidos'])
  // um comprovado e os demais sem prova: a linha dele e o resumo dos outros, sem "+N" que esconda o resumo
  const s = estado({}, Object.fromEntries(MEMBROS.map(m => [m, [1, '1970-01-01T00:00:00Z']])))
  const misto = buildScene(s, [doMembro('spock')], T(0), undefined, IDS)
  const linhas = atividades(misto)
  assert.equal(linhas.length, 2)
  assert.equal(linhas[0], '⚙ spock · trabalhando')
  assert.equal(linhas[1], '? 11 desconhecidos')
  // singular quando só um não tem prova
  const um = estado({}, { ...Object.fromEntries(MEMBROS.map(m => [m, [0, null]])), q: [1, '1970-01-01T00:00:00Z'] })
  assert.deepEqual(atividades(buildScene(um, [], T(0), undefined, IDS)), ['? 1 desconhecido'])
})

test('ponte viva dá a cada integrante um distintivo ou traje próprio', () => {
  // só seis aparecem por vez: a seleção manual traz cada integrante à cena
  const achar = (m: string) => buildScene(estado(), [], T(0), undefined, IDS, { selecionado: m }).personagens.find(x => x.membro === m)!
  const dourado = (p: ReturnType<typeof achar>) => p.pecas.some(x => x.cor === '#ffd24a')
  for (const m of MEMBROS) {
    // oficiais da Frota levam o distintivo no peito; Q, Troi e Guinan vestem trajes próprios
    assert.equal(dourado(achar(m)), !['q', 'troi', 'guinan'].includes(m), `distintivo de ${m}`)
  }
  // Q usa manto carmim com debrum dourado e Worf a faixa prateada: silhuetas que não dependem só da cabeça
  assert.notEqual(PERFIS.find(p => p.membro === 'q')!.cor, '#f2f2f2')
  assert.ok(pecasDoPerfil('brilho', achar('q').boneco, 1).pecas.some(x => x.cor === '#d4a017'))
  assert.ok(pecasDoPerfil('testa-craniana', achar('worf').boneco, 1).pecas.some(x => x.cor === '#c9ced6'))
})
