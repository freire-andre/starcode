// Cenários de `orca plugin check` do painel da Ponte.
import { defineCheck } from 'orca/testing'
import type { PonteSnapshot, PonteState } from './protocol'

const AT = 1_700_000_000_000

function snap(over: Partial<PonteSnapshot> = {}): PonteSnapshot {
  return {
    schemaVersion: 1,
    worktree: 'C:/wt/a',
    starcode: true,
    crew: [
      { member: 'picard', emoji: '🛸', name: 'Picard', count: 1, lastAt: null, cliModel: 'claude · opus' },
      { member: 'laforge', emoji: '🔧', name: 'LaForge', count: 2, lastAt: null, cliModel: 'claude · sonnet' },
      { member: 'data', emoji: '🤖', name: 'Data', count: 0, lastAt: null, cliModel: null },
    ],
    gitMode: { mode: 3, label: 'branch + PR', recordedAt: null },
    feature: {
      slug: 'fase-10-ponte', phase: 'build', size: 'GRANDE', done: false, linear: ['SC-117'],
      integrationBranch: null, progress: { done: 2, total: 4, percent: 50 }, breaker: 'closed',
      files: { context: null, spec: null, tasks: null, handoff: null },
    },
    workers: [{ label: 'T3', issues: ['SC-117'], base: null, dispatch: null, model: 'sonnet' }],
    errors: [],
    ...over,
  }
}

export function estado(over: Partial<PonteState> = {}): PonteState {
  return {
    status: 'ok', stale: false, updatedAt: AT, snapshot: snap(),
    issue: { id: 'SC-117', title: 'Painel Ponte', state: 'In Progress', url: null },
    issueNote: null,
    agents: [{ terminalId: 't1', title: 'T3 painel', agent: 'claude', state: 'working', stateStartedAt: AT }],
    log: [], error: null, ...over,
  }
}

const reply = (s: PonteState) => ({ requests: { 'ponte.state': () => s } })

export default defineCheck({
  ok: reply(estado()),
  vazio: reply(estado({ snapshot: snap({ crew: [], workers: [], feature: null }), issue: null, agents: [] })),
  'sem-starcode': reply(estado({ snapshot: snap({ starcode: false }) })),
  'erro-secao': reply(
    estado({ snapshot: snap({ errors: [{ source: 'src/crew.yaml', message: 'tripulação ilegível (OSError)' }] }) }),
  ),
  // 240 px: todos os botões dos Atalhos ativos e a issue do Handoff com nota; as linhas quebram (R47)
  'estreito-240': reply(
    estado({
      snapshot: snap({
        feature: {
          ...snap().feature!,
          files: { context: 'c.md', spec: 'spec.md', tasks: 'tasks.md', handoff: 'handoff.md' },
        },
      }),
      issue: { id: 'SC-117', title: null, state: null, url: 'https://linear.app/x/SC-117' },
      issueNote: 'Sem issue vinculada',
    }),
  ),
  desatualizado: reply(estado({ stale: true, error: 'python não roda' })),
})
