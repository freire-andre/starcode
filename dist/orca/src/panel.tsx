// Painel da Ponte: só componentes, sem hooks nem DOM; o estado fica em atoms com chave.
import {
  Badge, Box, Button, Callout, Heading, KeyValue, List, ListItem, Progress, RelativeTime,
  Row, Separator, Skeleton, Stack, Text, atom, plugin, read, set, shell, update,
} from 'orca'
import type { PanelContext } from 'orca'
import type { PonteAgent, PonteState, PonteWorker } from './protocol'

const stateAtom = atom<PonteState | null>('ponte.state', null)
const loadingAtom = atom<boolean>('ponte.loading', true)
const failAtom = atom<string | null>('ponte.fail', null)
const OK_VISIBLE = 'Picard iniciado numa aba visível'
const OK_BACKGROUND = 'Picard iniciado em segundo plano'
const launchingAtom = atom<boolean>('ponte.launching', false)
const shortcutErrAtom = atom<string | null>('ponte.shortcutErr', null)
const shortcutOkAtom = atom<string | null>('ponte.shortcutOk', null)
const elsewhereMsgAtom = atom<string | null>('ponte.elsewhereMsg', null)

const msg = (e: unknown) => (e instanceof Error ? e.message : String(e))

function focusElsewhere(): void {
  set(shortcutErrAtom, null)
  set(elsewhereMsgAtom, null)
  plugin
    .request('ponte.focusElsewhere', {})
    .then((r) => {
      if (r && !r.opened && r.message) set(elsewhereMsgAtom, r.message)
    })
    .catch((e: unknown) => set(shortcutErrAtom, msg(e)))
}

function openFile(file: 'spec' | 'tasks' | 'handoff'): void {
  set(shortcutErrAtom, null)
  plugin.request('ponte.open', { file }).catch((e: unknown) => set(shortcutErrAtom, msg(e)))
}

function openIssue(url: string): void {
  set(shortcutErrAtom, null)
  shell.openExternal(url).catch((e: unknown) => set(shortcutErrAtom, msg(e)))
}

function launchPicard(): void {
  set(shortcutErrAtom, null)
  set(shortcutOkAtom, null)
  set(launchingAtom, true)
  plugin
    .request('ponte.launchPicard', {})
    .then((r) => set(shortcutOkAtom, r?.visible ? OK_VISIBLE : OK_BACKGROUND))
    .catch((e: unknown) => set(shortcutErrAtom, msg(e)))
    .finally(() => set(launchingAtom, false))
}

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
  const el = snap.elsewhere ?? null
  const elsewhereMsg = read(elsewhereMsgAtom)
  const f = el ?? snap.feature
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
              ...(s.issueNote && (!s.issue.title || !s.issue.state) ? [{ label: 'Nota', value: s.issueNote }] : []),
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
            {el ? (
              <Callout tone="warning" title="Missão ativa em outro worktree">
                <Text>{`${el.branch ?? el.worktree} · ${el.phase}${el.progress.total > 0 ? ` · ${el.progress.done}/${el.progress.total}` : ''}`}</Text>
                {el.others > 0 ? <Text muted size="sm">{`e mais ${el.others}`}</Text> : null}
                <Button size="sm" onPress={focusElsewhere}>Focar worktree</Button>
                {elsewhereMsg ? <Text tone="danger" size="sm">{elsewhereMsg}</Text> : null}
              </Callout>
            ) : null}
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

function Shortcuts(props: { s: PonteState | null }) {
  const { s } = props
  // com missão em outro worktree, os arquivos locais não são os da missão mostrada
  const files = s?.snapshot?.elsewhere ? undefined : s?.snapshot?.feature?.files
  const launching = read(launchingAtom)
  const err = read(shortcutErrAtom)
  const ok = read(shortcutOkAtom)
  const url = s?.issue?.url ?? null
  return (
    <Stack gap="xs">
      <Row gap="sm" align="center" wrap>
        <Button size="sm" disabled={!files?.spec} onPress={() => openFile('spec')}>Abrir spec</Button>
        <Button size="sm" disabled={!files?.tasks} onPress={() => openFile('tasks')}>Abrir tasks</Button>
        <Button size="sm" disabled={!files?.handoff} onPress={() => openFile('handoff')}>Abrir Handoff</Button>
      </Row>
      <Row gap="sm" align="center" wrap>
        <Button size="sm" disabled={!url} onPress={() => (url ? openIssue(url) : undefined)}>Abrir issue no Linear</Button>
        <Button size="sm" disabled={launching || !s?.snapshot?.starcode} onPress={launchPicard}>Iniciar Picard</Button>
      </Row>
      {ok === OK_BACKGROUND && !err ? (
        <Text muted size="sm">O agente abriu em segundo plano, sem aba visível e sem o prompt enviado.</Text>
      ) : null}
      {err ? <Text tone="danger" size="sm">{err}</Text> : null}
      {ok && !err ? <Text size="sm">{ok}</Text> : null}
    </Stack>
  )
}

function Journal(props: { log: { at: number; text: string }[] }) {
  const recent = props.log.slice(-10).reverse()
  return (
    <Section title="Diário de bordo">
      {recent.length === 0 ? (
        <Text muted>Sem registros</Text>
      ) : (
        <Stack gap="xs">
          {recent.map((e) => (
            <Row gap="sm" align="center">
              <Text size="xs" muted><RelativeTime at={e.at} /></Text>
              <Text size="sm">{e.text}</Text>
            </Row>
          ))}
        </Stack>
      )}
    </Section>
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
        <Shortcuts s={s} />
      </Section>
      <Journal log={s?.log ?? []} />
    </Box>
  )
}
