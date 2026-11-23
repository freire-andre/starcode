// Testes do modelo da cena da Ponte (módulo puro, sem host).
import { assert, test } from 'orca/testing'
import { avisoDeDados, buildScene, GRADE, horario, LEGENDA, PONTE_ALTURA, linhasDoPainel, pecasDoPerfil, relacaoDaTripulacao, ROTACAO_MS, selecionaPresentes, TRANSICAO_MS } from './scene-model'
import type { Cena } from './scene-model'
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
/** Instante estável (fora da troca) da rodada `ciclo`. */
const T = (ciclo: number, extra = 2000): number => ciclo * ROTACAO_MS + extra
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
    assert.equal(vistos.size, 12)
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
  for (let ciclo = 0; ciclo < 2; ciclo++) {
    const cena = buildScene(crewReal(), [], T(ciclo), undefined, IDS)
    for (const p of cena.personagens) vistos.set(p.membro, p)
    for (const p of cena.personagens) rotulosNome.push(nomeNaCena(cena, p.membro))
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

test('ponte viva limita a seis integrantes', () => {
  const todos = MEMBROS.map(m => doMembro(m))
  for (const ags of [[], todos]) {
    for (let t = 0; t < 3 * ROTACAO_MS; t += 100) {
      const cena = buildScene(crewReal(), ags, t, undefined, IDS)
      assert.ok(cena.personagens.length <= 6, `${cena.personagens.length} em ${t} ms`)
      const nomes = cena.rotulos.filter(r => r.tipo === 'nome')
      assert.ok(nomes.length <= 12) // até duas linhas por presente
      // cada presente tem o nome completo junto de si, legível, mesmo com o snapshot real (name curto)
      assert.deepEqual([...new Set(nomes.map(r => r.dono))].sort(), membrosDe(cena).sort())
      for (const p of cena.personagens) assert.equal(nomeNaCena(cena, p.membro), NOMES_COMPLETOS[MEMBROS.indexOf(p.membro)])
    }
    assert.equal(buildScene(crewReal(), ags, T(0), undefined, IDS).personagens.length, 6)
  }
})

test('ponte viva alterna integrantes elegíveis', () => {
  // sem prioridade: todos os 12 aparecem em duas rodadas, seis por vez
  const vistos = new Set<string>()
  for (let ciclo = 0; ciclo < 2; ciclo++) {
    const m = membrosDe(buildScene(estado(), [], T(ciclo)))
    assert.equal(m.length, 6)
    m.forEach(x => vistos.add(x))
  }
  assert.equal(vistos.size, 12)
  // alertas e trabalhando ficam sempre; a vaga que sobra gira entre todos os demais elegíveis
  const ags = [doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('q', 'blocked'), doMembro('spock'), doMembro('kirk')]
  const fixos = ['data', 'worf', 'q', 'spock', 'kirk']
  const sobra = new Set<string>()
  for (let ciclo = 0; ciclo < 7; ciclo++) {
    const m = membrosDe(buildScene(estado(), ags, T(ciclo), undefined, IDS))
    assert.equal(m.length, 6)
    for (const f of fixos) assert.ok(m.includes(f), `${f} sumiu na rodada ${ciclo}`)
    m.filter(x => !fixos.includes(x)).forEach(x => sobra.add(x))
  }
  assert.deepEqual([...sobra].sort(), MEMBROS.filter(m => !fixos.includes(m)).sort())
  // oito trabalhando: cada rodada tem cinco deles e um ocioso (acesso periódico); em oito rodadas todos aparecem
  const oito = MEMBROS.slice(0, 8)
  const alcance = new Set<string>()
  const ociososVistos = new Set<string>()
  for (let ciclo = 0; ciclo < 8; ciclo++) {
    const m = membrosDe(buildScene(estado(), oito.map(x => doMembro(x)), T(ciclo), undefined, IDS))
    assert.equal(m.length, 6)
    assert.equal(m.filter(x => oito.includes(x)).length, 5, `trabalhando na rodada ${ciclo}: ${m}`)
    m.forEach(x => (oito.includes(x) ? alcance : ociososVistos).add(x))
  }
  assert.equal(alcance.size, 8)
  assert.deepEqual([...ociososVistos].sort(), MEMBROS.slice(8).sort())
  // alerta ganha de trabalhando quando não cabem todos: ocupa quatro das seis vagas; o trabalhando e um ocioso ficam com uma cada
  const sete = MEMBROS.slice(0, 7).map(x => doMembro(x, 'blocked'))
  const m = membrosDe(buildScene(estado(), [...sete, doMembro('guinan')], T(0), undefined, IDS))
  assert.deepEqual(m, ['picard', 'spock', 'troi', 'data', 'uhura', 'guinan'])
  const est = (agentes: PonteAgent[]) => estadosDaTripulacao({ ...estado(), agents: agentes }, IDS)
  assert.deepEqual(selecionaPresentes(est([]), 0), ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
  assert.deepEqual(selecionaPresentes(est([]), 1), ['q', 'uhura', 'scotty', 'kirk', 'worf', 'guinan'])
})

test('ponte viva dá acesso periódico aos demais mesmo com seis alertas', () => {
  const est = (alertas: number, trabalhando = 0): EstadoDoMembro[] => MEMBROS.map((membro, i) => ({
    membro, motivo: '', estado: i < alertas ? 'bloqueado' : i < alertas + trabalhando ? 'trabalhando' : 'ocioso',
  }))
  // seis alertas e seis ociosos: cada rodada tem cinco alertas e um ocioso; em seis rodadas todos os ociosos aparecem
  const e6 = est(6)
  const alertas = MEMBROS.slice(0, 6)
  const ociosos = MEMBROS.slice(6)
  const rodadas = Array.from({ length: 6 }, (_, ciclo) => selecionaPresentes(e6, ciclo))
  for (const r of rodadas) {
    assert.equal(r.length, 6)
    assert.equal(r.filter(x => alertas.includes(x)).length, 5, `alertas na rodada: ${r}`)
    assert.equal(r.filter(x => ociosos.includes(x)).length, 1, `demais na rodada: ${r}`)
  }
  assert.deepEqual(rodadas.map(r => r.find(x => ociosos.includes(x))), ociosos)
  // os alertas também giram: nenhum fica de fora para sempre
  assert.deepEqual([...new Set(rodadas.flat().filter(x => alertas.includes(x)))].sort(), [...alertas].sort())
  assert.deepEqual([...new Set(Array.from({ length: 24 }, (_, c) => selecionaPresentes(e6, c)).flat())].sort(), [...MEMBROS].sort())
  // menos alertas, mais prioridade para eles: três alertas ficam sempre; trabalhando e ocioso dividem o resto
  const e3 = est(3, 6)
  const r3 = Array.from({ length: 12 }, (_, ciclo) => selecionaPresentes(e3, ciclo))
  for (const r of r3) assert.deepEqual(MEMBROS.slice(0, 3).filter(x => !r.includes(x)), [])
  assert.deepEqual([...new Set(r3.flat())].sort(), [...MEMBROS].sort())
  // movimento reduzido (rodada 0 fixa) segue só a prioridade: o rodízio continua sendo o único acesso aos demais
  const todosAlerta = est(12)
  assert.deepEqual(selecionaPresentes(todosAlerta, 0), ['picard', 'spock', 'troi', 'data', 'laforge', 'mccoy'])
})

test('ponte viva anima sem alterar estado', () => {
  const base = estado()
  const estaveis = estadosDaTripulacao(base, IDS)
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t
  const ini = ROTACAO_MS
  // saída (primeira metade da troca): os seis da rodada 0 andam até o acesso
  const saindo = buildScene(base, [], ini + TRANSICAO_MS / 4, undefined, IDS)
  assert.equal(saindo.personagens.length, 6)
  for (const p of saindo.personagens) {
    assert.deepEqual(p.transicao, { fase: 'saindo', progresso: 0.5 })
    assert.ok(Math.abs(p.x - lerp(p.estacao.x, saindo.porta.x, 0.5)) < 1e-9 && Math.abs(p.y - lerp(p.estacao.y, saindo.porta.y, 0.5)) < 1e-9)
    assert.ok(p.opacidade < OPAC_MAX)
  }
  // entrada (segunda metade): os seis da rodada 1 saem do acesso
  const entrando = buildScene(base, [], ini + (TRANSICAO_MS * 3) / 4, undefined, IDS)
  assert.equal(entrando.personagens.length, 6)
  for (const p of entrando.personagens) {
    assert.deepEqual(p.transicao, { fase: 'entrando', progresso: 0.5 })
    assert.ok(Math.abs(p.x - lerp(entrando.porta.x, p.estacao.x, 0.5)) < 1e-9)
  }
  assert.deepEqual(membrosDe(saindo), membrosDe(buildScene(base, [], T(0))))
  assert.deepEqual(membrosDe(entrando), membrosDe(buildScene(base, [], T(1))))
  // o estado real não muda em nenhum ponto da troca; depois dela a transição acaba
  for (const cena of [saindo, entrando, buildScene(base, [], ini + TRANSICAO_MS, undefined, IDS)]) {
    for (const p of cena.personagens) assert.equal(p.estado, estaveis.find(e => e.membro === p.membro)!.estado)
  }
  assert.ok(buildScene(base, [], ini + TRANSICAO_MS, undefined, IDS).personagens.every(p => p.transicao === null))
  // trabalhando que entra anda de pé, sem animar o console, e senta ao chegar; o estado segue trabalhando
  const oito = MEMBROS.slice(0, 8).map(m => doMembro(m))
  const chegando = buildScene(base, oito, ini + (TRANSICAO_MS * 3) / 4, undefined, IDS).personagens.find(p => p.transicao?.fase === 'entrando')!
  assert.equal(chegando.estado, 'trabalhando')
  assert.equal(chegando.ativo, false)
  assert.equal(chegando.pose, 'de-pe')
  assert.equal(chegando.brilho, null)
  const chegou = buildScene(base, oito, ini + TRANSICAO_MS, undefined, IDS).personagens.find(p => p.membro === chegando.membro)!
  assert.equal(chegou.estado, 'trabalhando')
  assert.equal(chegou.ativo, true)
  assert.equal(chegou.pose, 'sentado')
  // não há mais de seis em nenhum quadro da troca
  for (let t = ini; t <= ini + TRANSICAO_MS; t += 50) assert.ok(buildScene(base, [], t, undefined, IDS).personagens.length <= 6)
})
const OPAC_MAX = 0.4

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
  assert.ok(data.opacidade <= 0.4)
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
    for (const p of cena.personagens) assert.ok(p.opacidade <= 0.4)
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
  // 12 agentes vinculados trabalhando: seis aparecem por vez e o rodízio alcança todos
  const todos: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, lastAt]]))
  const vistos = new Set<string>()
  for (let ciclo = 0; ciclo < 2; ciclo++) {
    const cena = buildScene(estado({}, todos), MEMBROS.map(m => doMembro(m)), T(ciclo), undefined, IDS)
    assert.equal(cena.personagens.length, 6)
    assert.ok(cena.personagens.every(p => p.ativo))
    cena.personagens.forEach(p => vistos.add(p.membro))
  }
  assert.equal(vistos.size, 12)
})

test('ponte viva mantém rótulos legíveis', () => {
  const mistos = [doMembro('spock'), doMembro('data', 'blocked'), doMembro('worf', 'waiting'), doMembro('kirk', 'done'), doMembro('guinan')]
  const todos = MEMBROS.map(m => doMembro(m))
  const lastAt = new Date(T(0) - 59 * 60_000).toISOString()
  const crew: Record<string, [number, string]> = Object.fromEntries(MEMBROS.map(m => [m, [1, lastAt]]))
  const fases = new Set<string>()
  for (const largura of [240, 360]) {
    const e = Math.max(5, Math.floor(largura / GRADE.largura)) // pixels por célula
    for (const altura of [500, 900, 1400]) {
      const linhas = linhasDoPainel(largura, altura)
      // estável (2000 ms) e as fases da troca: saindo (100 e 500 ms), meio (TRANSICAO_MS / 2) e entrando (700 e 1100 ms)
      const instantes = [0, 1, 2, 3, 4].flatMap(ciclo => [2000, 100, 500, TRANSICAO_MS / 2, 700, 1100].map(extra => T(ciclo, extra)))
      for (const agora of instantes) {
        for (const ags of [[], mistos, todos]) {
          const cena = buildScene(estado({}, crew, [worker('T1')]), ags, agora, linhas, IDS)
          for (const pe of cena.personagens) if (pe.transicao) fases.add(`${largura}:${pe.transicao.fase}`)
          assert.equal(cena.grade.altura, linhas)
          assert.equal(cena.personagens.length, 6)
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
  const ags = MEMBROS.slice(0, 8).map(m => doMembro(m))
  const a = estado({}, {}, [worker('T1')])
  const mesmo = (): PonteState => JSON.parse(JSON.stringify(estado({ updatedAt: 99, log: [{ at: 1, text: 'x' }] }, {}, [worker('T1')])))
  for (const t of [ROTACAO_MS + 100, ROTACAO_MS + TRANSICAO_MS * 0.75, ROTACAO_MS + 1100, 2 * ROTACAO_MS + 800]) {
    const um = buildScene(a, ags, t, undefined, IDS)
    // atualização repetida (cópia nova, mesmos agentes recriados): a cena não muda, nem a transição
    const dois = buildScene(mesmo(), ags.map(x => ({ ...x })), t, undefined, IDS)
    assert.deepEqual(um.personagens.map(p => [p.membro, p.transicao, p.x, p.y, p.opacidade]), dois.personagens.map(p => [p.membro, p.transicao, p.x, p.y, p.opacidade]))
  }
  // a transição segue o relógio: o progresso só cresce enquanto o estado se repete (não volta a 0)
  const prog = (t: number) => buildScene(mesmo(), ags, t, undefined, IDS).personagens.find(p => p.transicao?.fase === 'entrando')!.transicao!.progresso
  const seq = [ROTACAO_MS + 700, ROTACAO_MS + 800, ROTACAO_MS + 900, ROTACAO_MS + 1000, ROTACAO_MS + 1100]
  const ps = seq.map(prog)
  for (let i = 1; i < ps.length; i++) assert.ok(ps[i] > ps[i - 1], `reiniciou: ${ps}`)
  // quem fica não sai nem volta durante a troca
  const antes = new Set(membrosDe(buildScene(a, ags, ROTACAO_MS - 100, undefined, IDS)))
  const durante = buildScene(a, ags, ROTACAO_MS + 100, undefined, IDS).personagens
  for (const p of durante) if (p.transicao === null) assert.ok(antes.has(p.membro))
  assert.ok(durante.every(p => p.transicao === null || p.transicao.fase === 'saindo'))
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
  assert.deepEqual(selecionaPresentes(estadosDaTripulacao(base, IDS), 0, 'guinan').includes('guinan'), true)
  // a seleção continua valendo no rodízio, durante a troca incluída
  for (const t of [T(1), T(2), ROTACAO_MS + TRANSICAO_MS / 4, ROTACAO_MS + (TRANSICAO_MS * 3) / 4]) {
    assert.ok(membrosDe(buildScene(base, agentes, t, undefined, IDS, opcoes)).includes(fora.membro), String(t))
  }
})

test('ponte viva informa dados desatualizados', () => {
  const lv = new Date(2026, 10, 22, 9, 5, 7).getTime()
  assert.equal(horario(lv), '09:05:07')
  assert.equal(avisoDeDados(estado()), null)
  assert.equal(avisoDeDados(estado({ status: 'sem-worktree', snapshot: null })), null)
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
  const base = estado()
  const agentes = [doMembro('worf', 'blocked')]
  const r = { reduzido: true }
  const fixo = membrosDe(buildScene(base, agentes, T(0), undefined, IDS, r))
  // sem rodízio: o conjunto é o mesmo em qualquer rodada, e sem deslocamento: nenhuma transição em lugar nenhum
  for (let t = 0; t <= ROTACAO_MS * 4; t += 250) {
    const cena = buildScene(base, agentes, t, undefined, IDS, r)
    assert.deepEqual(membrosDe(cena), fixo, String(t))
    assert.ok(cena.personagens.every(p => p.transicao === null), String(t))
    assert.ok(cena.personagens.every(p => p.quadro === 0), String(t))
  }
  // o rodízio normal, no mesmo instante, mudaria a cena e anima a troca
  assert.notDeepEqual(membrosDe(buildScene(base, agentes, T(1), undefined, IDS)), fixo)
  assert.ok(buildScene(base, agentes, ROTACAO_MS + TRANSICAO_MS / 4, undefined, IDS).personagens.some(p => p.transicao !== null))
  // acesso manual preservado: a seleção traz o integrante mesmo com movimento reduzido
  const fora = MEMBROS.find(m => !fixo.includes(m))!
  const cena = buildScene(base, agentes, T(3), undefined, IDS, { ...r, selecionado: fora })
  assert.ok(membrosDe(cena).includes(fora))
  assert.ok(cena.personagens.every(p => p.transicao === null))
  const item = relacaoDaTripulacao(base, agentes, T(3), IDS, { ...r, selecionado: fora }).find(i => i.membro === fora)!
  assert.equal(item.presente, true)
})
