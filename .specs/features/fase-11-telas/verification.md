# fase-11-telas verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at e747017
**HEAD**: 8712cd2
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna (medium, lido no terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `tests/test_validate_spec_captures.py` `test_captura_sem_sources` | yes |
| C2 | `tests/test_validate_spec_captures.py` `test_captura_sem_linha_ou_non_binding_sem_citacao` | yes |
| C3 | `tests/test_validate_spec_captures.py` `test_captura_vinculante_sem_requisito` | yes |
| C4 | `tests/test_validate_spec_captures.py` `test_captura_sem_imagem_na_spec` | yes |
| C5 | `tests/test_validate_verification_screens.py` `test_feature_sem_telas_inalterada` | yes |
| C6 | `tests/test_validate_verification_screens.py` `test_telas_sem_screens_md` | yes |
| C7 | `tests/test_validate_verification_screens.py` `test_tela_diverges_reprova` | yes |
| C8 | `tests/test_validate_verification_screens.py` `test_screens_sem_round_ou_round_3` | yes |
| C9 | `tests/test_validate_verification_screens.py` `test_screens_sem_verifier` | yes |
| C10 | `tests/test_validate_verification_screens.py` `test_captura_sem_running` | yes |
| C11 | `tests/test_validate_verification_screens.py` `test_running_em_outro_tamanho` | no - testa apenas o tamanho divergente; o caso de foto 2x aprovada está em outro teste que não consta na prova do check (Finding 3). |
| C12 | `tests/test_validate_verification_screens.py` `test_imagem_ilegivel_vira_erro` | no - falha para bytes sem assinatura, mas não cobre PNG truncado que o parser aceita como imagem válida (Finding 1). |
| C13 | `tests/test_validate_verification_screens.py` `test_fotos_do_autor_degradada_e_strict` | yes |
| C14 | `tests/test_screens.py` `test_capture_chama_orca_na_ordem` | yes |
| C15 | `tests/test_screens.py` `test_capture_url_data_recusada` | no - cobre `data:`, mas não URL inválida com `http(s)://` fora do início, aceita pela validação (Finding 2). |
| C16 | `tests/test_screens.py` `test_capture_falha_fecha_aba` | yes |
| C17 | `tests/test_screens.py` `test_capture_sem_frame_tenta_de_novo` | yes |
| C18 | `tests/test_screens.py` `test_size_imprime_css` | yes |
| C19 | `tests/test_screens.py` `test_list_capturas_da_spec` | yes |
| C20 | `tests/test_screens.py` `test_capture_tamanho_errado_falha` | yes |
| C21 | `tests/test_dispatch_screens.py` `test_screens_brief_nao_leva_checks_nem_diff` | yes |
| C22 | `tests/test_dispatch_screens.py` `test_screens_brief_sem_captura_sai_2` | no - valida apenas a saída sem captura; não prova que o comando preenche o brief (Finding 4). |
| C23 | `tests/test_dispatch_screens.py` `test_screens_brief_preenche_campos` | yes |
| C24 | `tests/test_dispatch_screens.py` `test_screens_brief_regras_de_julgamento` | yes |
| C25 | `tests/test_dispatch_screens.py` `test_screens_brief_regras_de_julgamento` | yes |
| C26 | `tests/test_dispatch_screens.py` `test_screens_brief_regras_de_julgamento` | yes |
| C27 | `tests/test_dispatch_screens.py` `test_screens_brief_rodada_2` | yes |
| C28 | `tests/test_screens_flow.py` `test_execute_despacha_juiz_de_telas` | yes |
| C29 | `tests/test_screens_flow.py` `test_spock_regras_de_captura_sem_d25` | yes |
| C30 | `tests/test_screens_flow.py` `test_laforge_foto_do_autor` | yes |
| C31 | `tests/test_profile_screens.py` `test_template_tauri_mockipc_so_em_dev` | yes |
| C32 | `tests/test_profile_screens.py` `test_perfil_tauri_tem_screens` | yes |
| C33 | `tests/test_build.py` `test_build_leva_telas_aos_4_clis` | yes |
| C34 | `tests/test_release_docs_f11.py` `test_release_docs_f11` | yes |
| C35 | `tests/test_acceptance_doc_f11.py` `test_fase11_acceptance_sections` | no - valida marcadores e presença de arquivos, sem comprovar o app novo e a aprovação real do mockup (Finding 5). |
| C36 | `tests/test_acceptance_doc_f11.py` `test_fase11_acceptance_sections` | no - procura `matches`, `running` e `exit 0` no texto; não executa o fluxo nem o gate sobre a feature de aceite (Finding 5). |
| C37 | `tests/test_acceptance_doc_f11.py` `test_fase11_acceptance_sections` | no - procura `diverges`, `copy` e `same` no texto; não confere o conteúdo dos vereditos nem que a divergência foi corrigida entre as fotos (Finding 5). |
| C38 | `tests/test_acceptance_doc_f11.py` `test_fase11_acceptance_sections` | no - valida presença de seções e rótulos, não que o resultado aprovado decorra do aceite executado (Finding 5). |
| C39 | `tests/test_profile_gitattributes.py` `test_template_tauri_gitattributes_lf` | yes |
| C40 | `tests/test_aceite_tool.py` `test_aceite_preparar_materializa_fixture` | no - verifica ausência de `node_modules` apenas na raiz do destino, não em subpastas; a asserção é mais fraca que a exclusão recursiva pedida em R39 (Finding 6). |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| 1. Imagem PNG truncada passa como legível, contrariando R12. | `scripts/gates/images.py:56` — `_png` confere apenas o marcador IHDR e desempacota as dimensões; probe: PNG truncado contendo assinatura, IHDR e dimensões `7x9` retornou `(7, 9)`. | Validar comprimento e estrutura mínima do cabeçalho/chunk antes de aceitar a imagem; adicionar regressão com PNG truncado. | 98276ba |
| 2. R15 aceita URL que não começa com HTTP(S). | `scripts/screens.py:183` — o regex não está ancorado; probe com `junkhttps://example.com` aceitou a URL e chamou `tab create`, `exec`, `screenshot` e `tab close`. | Ancorar a validação no começo da string e cobrir prefixos inválidos. | cf601b4 |
| 3. C11 não demonstra que uma foto 2x de captura 1x passa, como afirma o check. | `tests/test_validate_verification_screens.py:74` — o teste citado cobre só a foto com tamanho incorreto; a aprovação 2x está em `test_running_2x_de_captura_1x_passa`, não citado na prova de C11. | Citar o teste positivo também ou dividir o check em dois. | 88d24fd |
| 4. O teste citado para C22 não cobre o caminho de sucesso prometido pelo check. | `tests/test_dispatch_screens.py:42` — `test_screens_brief_sem_captura_sai_2` só testa ausência de captura; o preenchimento é testado separadamente em C23. | Citar também `test_screens_brief_preenche_campos` em C22 ou separar o check de erro do check de preenchimento. | fc0cd73 |
| 5. O aceite real está provado apenas por asserções de texto, não pela execução e pelos artefatos do fluxo. As asserções são mais fracas que R35–R38. | `tests/test_acceptance_doc_f11.py:39` e `tests/test_acceptance_doc_f11.py:44` — verifica substrings como `PROJ-34`, `matches`, `running`, `exit 0`, `diverges` e `copy`; PNGs são verificados só pela assinatura de 8 bytes. | Executar e registrar o fluxo/gate no app de aceite, validar os vereditos e tamanhos nos artefatos e ligar a aprovação ao resultado observado. | 05a3a7d |
| 6. C40 não prova a ausência de `node_modules` em toda a árvore materializada. | `tests/test_aceite_tool.py:31` — `assertFalse((dest / "node_modules").exists())` só verifica a raiz. | Verificar com `rglob("node_modules")` que nenhuma subpasta foi copiada. | |

## Limits

Não verifiquei execução interativa dos workers Q/juiz nem o histórico do app Tauri externo; o aceite automatizado só inspeciona o registro e arquivos locais.
