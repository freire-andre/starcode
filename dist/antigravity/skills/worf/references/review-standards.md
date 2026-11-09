# Padrões do review (Worf)

Adaptado de the-judge 1.4.0 (Felipe Rodrigues, CC-BY-4.0). A geração busca recall; a verificação busca
precisão: aponte à vontade nos passes, mate na verificação o que não tem evidência.

## Passes
- **A. Correção e lógica:** invariante quebrada, caminho de falha que perde dado, limite errado, ordem
  assíncrona. Só o que tem entrada ou estado concreto que dispara a falha.
- **B. Segurança:** só falha introduzida pelo PR e com exploração demonstrável. Siga
  `security-evidence.md`; o que já existia antes vira `pre-existing`.
- **C. Estrutura:** complexidade que some com outro enquadramento, ramo ad-hoc em fluxo alheio, arquivo que
  passa de 1000 linhas por causa do PR, abstração que só repassa.
- **D. Lixo de IA:** comentário que repete o código, comentário de changelog, código comentado, try/catch
  defensivo em caminho confiável.
- **E. Afirmações da descrição do PR:** "corrige X" sem teste ou repro vira pergunta, nunca afirmação de
  que é falso.
- **F. Bypass, duplicação e gambiarra:** semeado pelo `scan_bypasses.py`; todo candidato é julgado aqui.

## Severidades e emojis
| Severidade | Emoji | Quando | Veredito |
|---|---|---|---|
| blocker | 🔴 | muda se o PR deve entrar: perda de dado, falha explorável, auth quebrada | `REQUEST_CHANGES` |
| should-fix | 🟠 | defeito real, sem risco de merge | `COMMENT` |
| nit | 🟡 | menor; no máximo 5 | sem efeito |
| pre-existing | 🟣 | bug que o PR não introduziu; só no resumo | sem efeito |

Sem `blocker` e sem `should-fix`: `APPROVE`. Baixo risco não é falso positivo: coisa pequena e real é `nit`,
não descarte. Descarte por falta de evidência; rebaixe por falta de impacto.

## Bypasses (R3)
Cada linha do `scan_bypasses.py` é **candidata**, nunca achado. Julgue:
- supressão com **justificativa e link de issue** na mesma linha ou na anterior: **aceita**, listada só no
  resumo, sem achado;
- sem isso: achado `should-fix`;
- `tls-bypass` e `hook-bypass` sem isso: `blocker`;
- bypass que esconde defeito real herda a severidade do defeito.

## Arquivos mecânicos
`dist/`, lockfiles, snapshots, código gerado e vendorizado ficam fora do review. Liste-os no resumo.
Código movido (3+ linhas iguais removidas num lugar e adicionadas em outro) não é código novo.

## Convergência
A rodada 1 levanta tudo, de uma vez. A rodada 2 e a 3 só verificam a resolução dos achados anteriores e
aceitam **blockers novos**; nada de `should-fix`, `nit` ou `pre-existing` novos. IDs `W<n>` ficam estáveis
entre rodadas. Autor que recusa com motivo: se o motivo se sustenta, registre e abandone o achado; senão
argumente uma vez, com evidência nova. Na rodada 3 todo achado aberto está corrigido, virou issue de
acompanhamento ou sobe ao usuário. Nunca há rodada 4 (convergência em até 3 rodadas).

## Barra de aprovação
Aprove quando o PR melhora a saúde do código, mesmo imperfeito. `nit` aberto nunca impede `APPROVE`.
