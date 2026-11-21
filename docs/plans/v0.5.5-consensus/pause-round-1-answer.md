A pausa da v0.5 está registrada corretamente no ROADMAP. O registro adotado tem **dois bloqueios documentais**. A decisão de pausa do mantenedor permanece válida.

## Bloqueios

1. **A seção 7 foi reescrita além das três correções autorizadas.** O novo parágrafo acrescenta decisões reservadas ao mantenedor e faz `2026-12-05` parecer prazo para o registro de disponibilidade de T3b. Na seção 5, essa é a data-limite para a resposta do NExScI. Em `docs/plans/v0.5.5-v05-line-pause-record.md:110`, use o título `## 7. What the draft asked the maintainer to decide` e restaure o parágrafo do rascunho: “Whether to pause the v0.5 line (and change its status in the ROADMAP, a non-delegated stop), which trigger to watch, and the T3b record by 2026-12-05.” O título situa o parágrafo como histórico.

2. **O gatilho D1 herdou uma contradição do rascunho.** O texto exige oito células `route` em um único conjunto novo. O desenho congelado exige duas visões × duas famílias × dois conjuntos. Em `docs/plans/v0.5.5-v05-line-pause-record.md:79`, submeta ao mantenedor esta correção textual: “whose D1-P price reads ‘route’ in all eight cells across two new seed sets for a decisive exit”. Isso reproduz o critério existente. [Desenho R1, revisão 1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:146)

## O que conferiu

- **Resultados.** D1-P, a preço `0,05`, registra `8,25` esperados ante o máximo de `9` e `p05 = 0,483` ante o mínimo de `0,5`. As duas saídas decisivas ficaram `unresolved`. D2-F tem `182` elegíveis, contagem superior `14` nas quatro variantes ante o limite próprio `13`, e contagens estritas `10` e `11`. Os `PASS` de D4 (`0,057` e `0,122`) são de desenvolvimento. T2a-E tem `102` replays, `85` válidos, `17` desconhecidos e `2` liberados (`0,024`). Na configuração B, `331` ante `552` de `559` dá a falta de `221`. T3b tem `2` elegíveis nas duas leituras, faltando `9` de `11`. A decisão local das 18h30 sustenta o relato de envio ao contato geral em `2026-11-21`, ainda sem resposta naquele registro, com prazo em `2026-12-05`.
- **CPU e tokens.** O ledger fecha em `64 = 63,5 + 0,5` CPU-h, com `14,854 = 14,578 + 0,276` gastos e `49,146 = 17,75 + 31,172 + 0,224` disponíveis. A única alteração no ledger é `cap_exceptions`, com até `150.000` tokens acima do ponto de parada de `2.400.000`, restritos à revisão final. O subtotal de `1.303.962` confere para a linha sem R2. [Ledger](C:/Projetos/refute/docs/validation/v0.5.5/ledger.json:2)
- **Escopo e invariantes.** O rascunho está byte a byte igual ao de `bd35900`. O diff do ROADMAP se limita a `Current phase` e ao aviso da v0.5.5, com o ponteiro para o registro e os critérios de saída intactos. O cabeçalho registra a adoção às 18h30 e `method_status: not_validated`. A regra de avanço, as metas, os locks históricos e os vereditos estão preservados. A v0.5 segue `WEAKENED` e T3b segue `INCONCLUSIVE`. [ROADMAP](C:/Projetos/refute/ROADMAP.md:43)

## Ressalvas

- `docs/plans/v0.5.5-v05-line-pause-record.md:104` — os seis saldos individuais, arredondados, somam `31,173`. O saldo calculado antes do arredondamento é `31,172057…`. Acrescente “Individual balances are rounded independently to 0.001 CPU-h.”
- `docs/plans/v0.5.5-v05-line-pause-record.md:77` — explicite a condição herdada da pausa v0.5.4 para o modelo de ruído: “or a noise model of the background series, in a new design frozen before its data, under which at least 82 of the 102 class-(i) injections are valid by all of step 6’s requirements.”
- `docs/plans/v0.5.5-v05-line-pause-record.md:8` — a frase sobre fontes commitadas é ampla demais para a data de adoção e o acompanhamento de T3b. Use “Measurements and balances are traced to the cited records. The adoption and NExScI follow-up are recorded in the maintainer’s decision of 2026-11-21 (18:30), item 1 (#218).”

**Veredito da revisão documental: WEAKENED.**

