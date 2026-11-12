A revisão preserva o fechamento **não aprovado pelo item 2**, mas ainda precisa das correções abaixo. Conferi os anexos e o código somente em leitura. Nenhum arquivo foi alterado por mim e o caminho proibido não foi acessado.

**Correções necessárias no registro**

1. **Preencher a tabela do Codex.** [A seção correspondente](/C:/Projetos/refute/docs/validation/v0.5.3/closing-record.md:321) ainda contém `{CHECK_TABLE}`, embora anuncie respostas já registradas. Incorporar os nove resultados ao final desta resposta e identificar o registro de consenso correspondente.

2. **Precisar a faixa de E2.** Em `b1-screen.json`, há `error_ratios` nos 31 casos de perdas anteriores, dentro da amostra de 112. Os **28 valores finitos** de `v5_odd_even_over_bound` vão de **0,823048 a 2,120200**, com mediana **1,441337**. “Cerca de 1,1 a 2,1” resume os valores, mas não representa a faixa completa nem uma medição disponível nos 112 planetas. O desenho realmente ressalva que o bound usa o template verdadeiro.

3. **Limitar a conclusão sobre D2.** A [linha de inviabilidade](/C:/Projetos/refute/docs/validation/v0.5.3/closing-record.md:270) distingue corretamente 112 de 178, mas termina afirmando que “no information limit” foi mostrado nos 112. Substituir por: **o bound deixa espaço sob suas hipóteses nos 112, sem demonstrar atingibilidade; não foi recomputado nos 178**. Isso preserva a distinção explícita em `stageA/README.md:64–65`.

4. **Preservar a cronologia do teto.** Na [linha do item 3](/C:/Projetos/refute/docs/validation/v0.5.3/closing-record.md:56), retirar “so no cap was reached with the forecast not done”. O teto foi atingido com 181/200 registros. A conclusão posterior e autorizada torna **sem efeito a aplicação do item 3**, conforme a decisão do mantenedor, sem desfazer aquele acontecimento.

5. **Explicitar duas condições.** No ponto 3, trocar “With those kept” por **“If those five remain REFUTED”**, eliminando a ambiguidade entre preservar os FAILs e recuperar as perdas. No argumento de D1, esclarecer que um warning FAIL resulta em WEAKENED **quando nenhuma condição anterior da agregação determina REFUTED ou INCONCLUSIVE**.

6. **Corrigir a declaração de preservação.** [“Every record … is unchanged”, incluindo ledgers](/C:/Projetos/refute/docs/validation/v0.5.3/closing-record.md:340), contradiz a reconciliação documentada neste diff. Ressalvar expressamente essa alteração no ledger. As referências a tabela e seção “below”, na linha 370, também devem apontar para “above” ou usar links.

**Decisão do mantenedor e reconciliação**

A abertura, a marcação **item 3: no** e a nota dos caps implementam a decisão recebida, com a ressalva cronológica acima. A autoria está corretamente atribuída ao mantenedor. T2a exige 552 e mantém 331; D2 exige pelo menos 156 e mantém 141/178, sustentando o item 2.

Confirmei no ledger que `b1_smoke` passou de `unresolved_stop` para `reconciled`, preservando motivo, identidade e consumo. O arquivo `stop-reconciled-000.json` existe no caminho informado, mantém o estado original da parada e acrescenta o motivo da reconciliação. O `progress.jsonl` registra `stop_reconciled`, compatível com `driver.Run.reconcile`. O stop de D2/D4 também permanece registrado. O total recomposto é **53,273390625 CPU-h**, coerente com 53,273.

**Resposta e ordem propostas pela revisão**

A [nova seção](/C:/Projetos/refute/docs/validation/v0.5.3/closing-record.md:290) é fiel: conserva a ausência de base atual para inviabilidade, a atingibilidade indeterminada e os sete passos na ordem proposta. A autoria e a **não adoção** estão explícitas.

`closing-review.md` permanece idêntico ao de `f932cac`, confirmado pelo mesmo hash de blob. O registro identifica corretamente **`40aa485`** como o commit lido pela revisão independente.

Todos os nove pontos receberam atribuição à revisão, com referência à seção 5 e ao item correspondente, nos trechos pertinentes. As ressalvas abaixo distinguem a validade do ponto da precisão de sua aplicação.

| Ponto | Minha resposta | Motivo ou ressalva |
|---|---|---|
| 1. C e margem | **accepted** | C mantém 42/56 acima de 20: 552 − 42 = 510 necessários entre 559, permitindo 49 perdas; a margem de 28 depende do what-if de 207 recuperações. |
| 2. Bound de T2a | **accepted** | `t2a-bounds.json` conta recuperabilidade das 51 perdas anteriores, sob uma regra otimista; não estabelece um limite informacional. |
| 3. REFUTED e recuperações | **accepted with a caveat** | São 4 FAILs de `odd_even` e 1 de `period_alias`; preservados como REFUTED, o teto é 554, com recuperações INCONCLUSIVE de 72/124/207/223. Explicitar essa preservação. |
| 4. E2 e B1.2 | **accepted with a caveat** | O ganho 81→86 e sua ausência nos 178 novos, 142→141, conferem; precisar o subconjunto dos ratios e a faixa completa 0,823–2,120. |
| 5. Amostras de D2 | **accepted with a caveat** | O bound é sobre 112, com 111/108 contra 97; o FAIL é sobre 178. Remover a conclusão excessiva de ausência de limite informacional. |
| 6. Classes ausentes | **accepted** | Conferem 24/26 perdas de `odd_even` e 17/25 de `sinusoid` sem classe registrada; esses registros não demonstram causa de sensibilidade. |
| 7. T3b | **accepted** | A linha foi incluída corretamente: não medido na rodada, população “none as written”, sem base para inviabilidade informacional. |
| 8. D1 e severidade | **accepted with a caveat** | `secondary_eclipse` é WARNING; `c1.py:641–649` conta apenas SURVIVED e `:654` inclui WEAKENED em D2. Preservar também a condição de comparação com v0.4 e a precedência da agregação. |
| 9. Null de E4 | **accepted** | Conferem 2 elegíveis, 1 contraste e disponibilidade 0,0; “carried no information” substitui fielmente “empty”. |

**WEAKENED (com as correções indicadas acima).**