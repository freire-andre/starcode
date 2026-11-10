# fase-10-ponte proofs

**HEAD**: 29aff98
**Tree**: clean
**Shell**: C:\Program Files\Git\bin\bash.exe
**Result**: 54 pass, 0 fail

| Check | Proof | Result |
| --- | --- | --- |
| C1 | `run unit / test_snapshot_keys ... ok` | pass |
| C2 | `run unit / test_snapshot_crew_ttl ... ok` | pass |
| C3 | `run unit / test_snapshot_git_mode ... ok` | pass |
| C4 | `run unit / test_snapshot_feature_choice ... ok` | pass |
| C5 | `run unit / test_snapshot_feature_fields ... ok` | pass |
| C6 | `run unit / test_snapshot_workers ... ok` | pass |
| C7 | `run unit / test_snapshot_sem_starcode ... ok` | pass |
| C8 | `run unit / test_snapshot_fonte_invalida ... ok` | pass |
| C9 | `run unit / test_snapshot_worktree_invalido ... ok` | pass |
| C10 | `run unit / test_snapshot_somente_leitura ... ok` | pass |
| C11 | `run plugin / ✔ worker acha o worktree em foco pelo ramo` | pass |
| C12 | `run plugin / ✔ worker sem worktree em foco` | pass |
| C13 | `run plugin / ✔ worker publica o estado após agent.status.changed` | pass |
| C14 | `run plugin / ✔ worker agrupa eventos em 300 ms` | pass |
| C15 | `run plugin / ✔ worker descarta snapshot de foco antigo` | pass |
| C16 | `run plugin / ✔ worker consulta a issue vinculada e guarda em cache por 60 s` | pass |
| C17 | `run plugin / ✔ worker sem Linear mostra o ID do Handoff` | pass |
| C18 | `run plugin / ✔ worker com snapshot falho marca desatualizado` | pass |
| C19 | `run plugin / ✔ worker atualiza a barra de status` | pass |
| C20 | `run unit / test_manifest_toggle_da_barra ... ok` | pass |
| C21 | `run plugin / ✔ painel pede o estado ao abrir` | pass |
| C22 | `run plugin / ✔ painel redesenha com ponte.state` | pass |
| C23 | `run plugin / ✔ painel mostra só tripulantes ativos` | pass |
| C24 | `run plugin / ✔ painel mostra fase e progresso` | pass |
| C25 | `run plugin / ✔ painel casa worker com agente` | pass |
| C26 | `run plugin / ✔ painel sem StarCode` | pass |
| C27 | `run plugin / ✔ painel com seção indisponível` | pass |
| C28 | `run plugin / ✔ atalho abre spec tasks e handoff` | pass |
| C29 | `run plugin / ✔ atalho abre a issue no navegador` | pass |
| C30 | `run plugin / ✔ atalho inicia o Picard uma vez` | pass |
| C31 | `run plugin / ✔ atalho recusa agente que a Orca não lança` | pass |
| C32 | `run plugin / ✔ atualizar agora ignora o cache` | pass |
| C33 | `run unit / test_build_check_cobre_dist_orca ... ok` | pass |
| C34 | `run unit / test_install_orca_aprovacao_nunca_automatica ... ok` | pass |
| C35 | `run unit / test_manifest_capabilities_e_engines ... ok` | pass |
| C36 | `run unit / test_release_docs_f10 ... ok` | pass |
| C37 | `run unit / test_fase10_acceptance_sections ... ok` | pass |
| C38 | `run plugin / ✔ cena tem uma estação por tripulante e a engenharia` | pass |
| C39 | `run plugin / ✔ cena senta tripulante ativo e anima a cada 250 ms` | pass |
| C40 | `run plugin / ✔ cena põe o balão no personagem do agente bloqueado` | pass |
| C41 | `run plugin / ✔ cena desenha até 6 workers e +N` | pass |
| C42 | `run plugin / ✔ cena vazia mostra a frase do estado` | pass |
| C43 | `run plugin / ✔ pintura da cena só lê o modelo e não usa imagem` | pass |
| C44 | `run plugin / ✔ diário guarda 20 entradas e o painel mostra 10` | pass |
| C45 | `run plugin / ✔ cena cria o canvas e importa com caminho servido` | pass |
| C46 | `run plugin / ✔ painel mostra a nota da issue do Handoff` | pass |
| C47 | `run plugin / ✔ painel estreito quebra os atalhos` | pass |
| C48 | `run plugin / ✔ worker desempata ramo igual pelo nome` | pass |
| C49 | `run plugin / ✔ worker registra falhas no log` | pass |
| C50 | `run plugin / ✔ cena distribui os inativos no turbolift` | pass |
| C51 | `run unit / test_fase10_limitacoes_registradas ... ok` | pass |
| Build | `python tools/build.py --check` | pass |
| Build | `orca plugin validate src/orca --json` | pass |
| Build | `python scripts/check_decisions.py` | pass |

## Output

`Run unit` - exit 0

```
test_verification_fails_on_open_finding_or_missing_approval (test_validate_verification.ValidateVerificationTests.test_verification_fails_on_open_finding_or_missing_approval) ... ok
test_worf_review_standards_bypass_rule (test_worf_skill.WorfSkillTests.test_worf_review_standards_bypass_rule) ... ok
test_worf_skill_evidence_or_silence (test_worf_skill.WorfSkillTests.test_worf_skill_evidence_or_silence) ... ok
test_worf_skill_never_merges (test_worf_skill.WorfSkillTests.test_worf_skill_never_merges) ... ok
test_worf_skill_review_flow_order (test_worf_skill.WorfSkillTests.test_worf_skill_review_flow_order) ... ok
test_worf_skill_review_md_contract (test_worf_skill.WorfSkillTests.test_worf_skill_review_md_contract) ... ok
test_execute_stops_on_codex_hooks_review (test_worker_skills.WorkerSkillTests.test_execute_stops_on_codex_hooks_review) ... ok
test_laforge_calls_mccoy_on_second_failure (test_worker_skills.WorkerSkillTests.test_laforge_calls_mccoy_on_second_failure) ... ok
test_laforge_skill_scope_tdd_commit (test_worker_skills.WorkerSkillTests.test_laforge_skill_scope_tdd_commit) ... ok
test_mccoy_skill_regression_and_report (test_worker_skills.WorkerSkillTests.test_mccoy_skill_regression_and_report) ... ok

----------------------------------------------------------------------
Ran 599 tests in 326.270s

OK
```

`Run plugin` - exit 0

```
✔ atalho abre spec tasks e handoff (3.7541ms)
✔ atalho inicia o Picard uma vez (3.7932ms)
✔ atalho recusa agente que a Orca não lança (0.7894ms)
✔ diário guarda 20 entradas e o painel mostra 10 (10.9102ms)
✔ diário registra mudança de worktree e de fase (1.7868ms)
✔ worker registra falhas no log (5.4699ms)
ℹ tests 40
ℹ suites 0
ℹ pass 40
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1851.3506
4 test file(s) passed (node).
```
