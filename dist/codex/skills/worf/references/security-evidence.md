# Portão de evidência de segurança (Worf)

Inspirado na security-audit-skill da Cloudflare (MIT), reescrito para o StarCode. Achado de segurança é
`category: security` no `review.json`. Sem prova, sem severidade.

## Campos obrigatórios
Todo achado de segurança responde, cada um em uma frase concreta:
- `attacker`: **quem ataca** (usuário anônimo, usuário autenticado, serviço vizinho...);
- `entry`: **por onde entra** (rota, argumento, arquivo lido, variável controlada pelo atacante);
- `control`: o **controle** que deveria barrar e o que ele faz hoje;
- `boundary`: a **fronteira** de confiança cruzada;
- `impact`: o **impacto** demonstrado (dado exposto, execução, escalada);
- `proof`: a **prova** (teste que falha, script no harness do repo, trecho `arquivo:linha` lido);
- `state`: `confirmed`, `needs-validation` ou `rejected`.

Campo vazio: o `review_gate.py` recusa com `security: campo <nome> ausente`.

## Estados
- `confirmed`: a prova mostra o ataque funcionando.
- `needs-validation`: falta um fato; escreva-o em `missing_fact`. Severidade máxima: `should-fix`.
- `rejected`: você investigou e o ataque não procede; escreva o motivo em `reason`. Nunca conta no veredito;
  fica no registro para a próxima rodada não repetir a dúvida.

## hardening
Faltou uma camada, mas outra já barra o ataque: marque `hardening: true`. Vai só para o resumo, fora da
contagem e do veredito.

## Severidade nunca acima do impacto demonstrado
A severidade segue o impacto que a prova mostra, não o impacto imaginável. Sem prova de exploração, no
máximo `should-fix` com `needs-validation`. Prova de um passo do ataque não vale o ataque inteiro.

## Fora do escopo
Negação de serviço, falta de endurecimento sem ataque, dependência desatualizada sem advisory para a versão
exata, achado em teste ou documentação, variável de ambiente e flag de CLI tratadas como confiáveis. Nunca
rode ataque de rede nem saia do checkout para provar.
