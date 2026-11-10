// Painel da Ponte: só componentes, sem hooks nem DOM; o estado fica em atoms com chave.
import {
  Badge, Box, Button, Callout, Heading, KeyValue, List, ListItem, Progress, RelativeTime,
  Row, Separator, Skeleton, Stack, Text, atom, plugin, read, set, update,
} from 'orca'
import type { PanelContext } from 'orca'
import type { PonteAgent, PonteState, PonteWorker } from './protocol'

const stateAtom = atom<PonteState | null>('ponte.state', null)
const loadingAtom = atom<boolean>('ponte.loading', true)
const failAtom = atom<string | null>('ponte.fail', null)

function request(force: boolean): void {
  update(loadingAtom, () => true)
  plugin
    .request('ponte.state', force ? { force: true } : {}, { timeoutMs: 15000 })
    .then((s) => {
      set(stateAtom, s)
      set(failAtom, null)
    })
    .catch((e: unknown) => set(failAtom, e instanceof Error ? e.message : String(e)))
    .finally(() => set(loadingAtom, false))
}

/** Ao abrir: assina o estado publicado pelo worker e pede o primeiro. */
export function setup(ctx: PanelContext) {
  ctx.subscriptions.push(
    plugin.on('ponte.state', (s) => {
      set(stateAtom, s)
      set(failAtom, null)
      set(loadingAtom, false)
    }),
  )
  request(false)
}

type Section = 'crew' | 'gitMode' | 'feature'

/** Seção de um erro do snapshot, pela origem. */
function sectionOf(source: string): Section {
  if (/crew|sessions/i.test(source)) return 'crew'
  if (/session\.json|git/i.test(source)) return 'gitMode'
  return 'feature'
}

function Unavailable(props: { message: string }) {
  return (
    <Text tone="warning" size="sm">
      {'indisponível: ' + props.message}
    </Text>
  )
}

function Section(props: { title: string; children?: unknown }) {
  return (
    <Stack gap="xs">
      <Heading level={3}>{props.title}</Heading>
      {props.children as never}
    </Stack>
  )
}

function agentFor(w: PonteWorker, agents: PonteAgent[]): PonteAgent | null {
  const keys = [w.label, ...w.issues].filter((k) => k)
  return agents.find((a) => a.title && keys.some((k) => a.title!.includes(k))) ?? null
}

function Refresh() {
  return (
    <Button icon="refresh" size="sm" onPress={() => request(true)}>
      Atualizar agora
    </Button>
  )
}

function Body(props: { s: PonteState }) {
  const { s } = props
  const snap = s.snapshot
  if (s.status === 'sem-worktree') return <Text muted>Nenhum worktree em foco</Text>
  if (!snap) return <Callout tone="danger" title="Ponte indisponível"><Text>{s.error ?? 'sem estado'}</Text></Callout>
  if (!snap.starcode) return <Text>StarCode não configurado neste worktree</Text>

  const errs = (sec: Section) => snap.errors.filter((e) => sectionOf(e.source) === sec)
  const active = snap.crew.filter((c) => c.count > 0)
  const f = snap.feature
  return (
    <Stack gap="md">
      {s.stale ? <Badge tone="warning">desatualizado</Badge> : null}
      <Section title="Tripulação">
        {errs('crew').map((e) => <Unavailable message={e.message} />)}
        {active.length === 0 ? (
          <Text muted>Tripulação em repouso</Text>
        ) : (
          <List label="Tripulação">
            {active.map((c) => (
              <ListItem
                title={`${c.emoji} ${c.name}${c.count > 1 ? ` ×${c.count}` : ''}`}
                description={c.cliModel ?? undefined}
              />
            ))}
          </List>
        )}
      </Section>
      <Section title="Modo Git">
        {errs('gitMode').map((e) => <Unavailable message={e.message} />)}
        <Text>{snap.gitMode ? `${snap.gitMode.mode} · ${snap.gitMode.label}` : 'não definido'}</Text>
      </Section>
      <Section title="Issue">
        {s.issue ? (
          <KeyValue
            items={[
              { label: 'ID', value: s.issue.id },
              { label: 'Título', value: s.issue.title ?? '—' },
              { label: 'Estado', value: s.issue.state ?? '—' },
            ]}
          />
        ) : (
          <Text muted>{s.issueNote ?? 'Sem issue'}</Text>
        )}
      </Section>
      <Section title="Fase SDD">
        {errs('feature').map((e) => <Unavailable message={e.message} />)}
        {f ? (
          <Stack gap="xs">
            <KeyValue
              items={[
                { label: 'Feature', value: f.slug },
                { label: 'Fase', value: f.phase },
                { label: 'Tamanho', value: f.size ?? '—' },
              ]}
            />
            <Progress
              label={`${f.progress.done}/${f.progress.total} (${f.progress.percent}%)`}
              value={f.progress.percent}
            />
            {f.breaker === 'open' ? <Callout tone="danger">Disjuntor aberto</Callout> : null}
          </Stack>
        ) : (
          <Text muted>Nenhuma feature em andamento</Text>
        )}
      </Section>
      <Section title="Workers da Frota">
        {snap.workers.length === 0 ? (
          <Text muted>Nenhum worker despachado</Text>
        ) : (
          <List label="Workers da Frota">
            {snap.workers.map((w) => {
              const a = agentFor(w, s.agents)
              const parts = [w.issues.join(', '), w.model, a ? a.state : null].filter((p) => p)
              return <ListItem title={w.label} description={parts.join(' · ')} />
            })}
          </List>
        )}
      </Section>
    </Stack>
  )
}

export default function Panel() {
  const s = read(stateAtom)
  const loading = read(loadingAtom)
  const fail = read(failAtom)
  
  return (
    <Box padding="md" direction="column" gap="md">
      {s ? <Body s={s} /> : loading ? <Stack gap="xs"><Text muted>Carregando…</Text><Skeleton lines={4} /></Stack> : null}
      {fail && !s ? <Callout tone="danger" title="Ponte indisponível"><Text>{fail}</Text></Callout> : null}
      <Separator />
      <Section title="Atalhos">
        <Row gap="sm" align="center">
          <Refresh />
          {s ? (
            <Text muted size="xs">
              {'Atualizado '}
              <RelativeTime at={s.updatedAt} />
            </Text>
          ) : null}
        </Row>
      </Section>
    </Box>
  )
}
