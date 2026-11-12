# tela-saudacao verification

**Verdict**: FAIL
**Proofs**: `proofs.md` at 8b1d62f
**HEAD**: 9c378ae
**Verifier**: codex · requested padrão do CLI · effective gpt-6-luna (medium, lido no terminal)

## Checks

| Check | Test | Holds |
| --- | --- | --- |
| C1 | `src/ui.test.ts` `traz os textos do mockup` | no - `toContain` não prova que os textos estejam copiados caractere por caractere nem que não haja texto divergente. |
| C2 | `src/ui.test.ts` `mostra a saudação com o nome` | yes |
| C3 | `src/ui.test.ts` `mostra a saudação ao mundo com o campo vazio` | yes |

## Findings

| Finding | Evidence | Fix | Closed |
| --- | --- | --- | --- |
| C1 aceita conteúdo diferente do mockup: cada valor é verificado apenas como substring. | `src/ui.test.ts:47` | Comparar o conjunto/estrutura e os textos integrais definidos por R1, rejeitando conteúdo extra ou substituído. | 712c30c |
| O CSS transforma “Saudar” em “SAUDAR”, divergindo do texto visível do mockup; nenhuma checagem prova a aparência renderizada. | `src/style.css:107`; `.specs/features/tela-saudacao/captures/saudacao.running.png` mostra “SAUDAR”, enquanto `saudacao.png` mostra “Saudar”. | Remover a transformação para caixa alta e validar a captura renderizada contra o mockup. | cf05251 |

## Limits

Não foi possível validar equivalência visual completa em uma sessão de navegador; os proofs registram testes unitários e verificações de build.
