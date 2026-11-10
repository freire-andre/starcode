# Aceite da Fase 10 (SC-123): Ponte no painel da Orca

Executado em 2026-11-10 pelo LaForge (claude · claude-sonnet-5-5) no worktree `medaka` (Worktree A), com o plugin `local.starcode-ponte` 1.3.0 já instalado pelo usuário. Capturas com `orca plugin shot` (janela da Orca visível, tema claro, painel com 237 px de largura). Achados que pedem código ficam como pendência, sem correção neste ticket.

## Instalação

**Resultado**: aprovado

Captura: `docs/aceite/fase-10/worktree-a-status.png`

O usuário instalou e aprovou o plugin em 2026-11-10: `orca plugin install <IW>/dist/orca --json --approve ap1-cbf0017763ab268a83e1df5c2f30fbf1` → ok, chave `local.starcode-ponte`, versão 1.3.0, status `running`, contentHash `f17f2510…8d90`, 5 capabilities. Nada foi reinstalado nem aprovado neste ticket. `orca plugin list --json` confirma painéis `ponte` e `ponte-cena`, item de status `ponte` e comandos `starcode-ponte.toggle` e `starcode-ponte.refresh`. A captura da barra de status mostra o item `fase-10-ponte · published`.

## Worktree A

**Resultado**: aprovado

Capturas: `docs/aceite/fase-10/worktree-a-ponte.png` e `docs/aceite/fase-10/worktree-a-status.png`

Foco em `medaka` (`orca worktree activate`), `orca plugin open local.starcode-ponte --panel ponte`. O painel mostra tripulação LaForge (claude · claude-sonnet-5-5), modo Git "não definido", issue SC-17, feature `fase-10-ponte`, fase `published`, tamanho GRANDE, 8/9 (89%), "Nenhum worker despachado" e o diário "Worktree em foco: medaka". A barra de status mostra `fase-10-ponte · published`. `errors: []` e `settled: true` nas duas capturas.

Pendência (código): com 237 px os botões "Abrir tasks" e "Iniciar o Picard" ficam cortados e há rolagem horizontal.

## Worktree B

**Resultado**: aprovado

Capturas: `docs/aceite/fase-10/worktree-b-ponte.png` e `docs/aceite/fase-10/worktree-b-status.png`

Foco em `F:/Projetos/starcode-sandbox` (ramo `chore/starcode-specs`). Esse worktree tem StarCode configurado, então o painel não mostra "StarCode não configurado neste worktree": mostra "Tripulação em repouso", modo Git `2 · commit local`, issue PROJ-20, feature `tarefas-recorrentes`, fase `published`, tamanho LARGE, 5/5 (100%). A barra de status trocou para `tarefas-recorrentes · published · modo 2`, ou seja, o painel e o item seguem o worktree em foco. O estado sem StarCode não foi capturado (nenhum worktree sem StarCode foi usado). `errors: []` e `settled: true`.

## Evento de agente

**Resultado**: reprovado

Capturas: `docs/aceite/fase-10/evento-antes.png` e `docs/aceite/fase-10/evento-depois.png`

De volta ao Worktree A, duas capturas com 20 s de intervalo, enquanto este worker usava ferramentas. Só mudou o contador "Atualizado há 3 seg." → "há 24 seg." e a idade das linhas do diário; a tripulação continuou igual (LaForge) e nenhuma linha nova de evento de agente apareceu. A mudança vista é só o relógio, não uma atualização disparada por evento; por isso não conta como aprovado.

Pendência (investigar): confirmar se o evento de estado do agente chega ao worker do plugin e atualiza a tripulação sem clique em "Atualizar agora".

## Cena

**Resultado**: reprovado

Capturas: `docs/aceite/fase-10/cena-1.png`

`orca plugin shot local.starcode-ponte --panel ponte-cena`: a primeira captura saiu em branco (`cena-1.png`, sem nenhum elemento). As repetições, depois de `orca plugin open … --panel ponte-cena` e com `--width 400`, falharam com `The plugin panel the panel stopped responding.`; `orca plugin logs` não mostrou linhas. A segunda captura, após um evento de agente, não foi possível.

Pendência (código): o painel `ponte-cena` não desenha nem responde na Orca instalada; reproduzir com `orca plugin shot local.starcode-ponte --panel ponte-cena`.

## Atalhos

**Resultado**: reprovado

Captura: `docs/aceite/fase-10/worktree-a-ponte.png` (os botões visíveis, sem clique)

- Atualizar agora: não executado. `orca plugin shot --act` recusa agir com a janela da Orca visível ("shot --act needs Orca's window hidden or minimized, so it never clicks under the user"), e a CLI não tem outro jeito de pressionar o botão de um plugin instalado.
- Abrir spec: não executado, pelo mesmo motivo.
- Iniciar o Picard: não executado; o usuário não está junto e o atalho abriria um agente novo.

Os botões "Atualizar agora", "Abrir spec" e "Abrir tasks" aparecem no painel; "Abrir issue no Linear" aparece desabilitado (issue SC-17 sem título). Falta um aceite manual com o usuário para esses cliques.
