Usei os limites congelados para distinguir uma melhora de cálculo de uma melhora com efeito demonstrado na meta. Os custos abaixo são referências de R1. O custo completo de desenvolver e validar cada mudança permanece sem estimativa específica nos registros. [Livro de pisos e margens](C:/Projetos/refute/docs/plans/v0.5.5-g1-report-3.md:53) · [Estatuto](C:/Projetos/refute/docs/plans/v0.5.5-charter.md:145) · [Emenda 1](C:/Projetos/refute/docs/plans/v0.5.5-charter-amendment-1.md:89)

### D2 | Probabilidade conjunta simulada (`SIN_J`)

| Critério | Avaliação |
|---|---|
| O que muda | Substitui o limite de Fréchet pela probabilidade conjunta simulada de detectar a senoide e obter resíduo pequeno. |
| Por que é método | Calcula o mesmo evento de sensibilidade, na mesma alternativa e com a exigência de **0,95**. Para sustentar a mesma afirmação do veredito, o modelo de dependência e a incerteza da simulação precisam justificar o certificado. A simulação registrada é no oráculo. |
| Evidência | Na ordem `current`, `variant_2_joint`, `variant_3_evidence`, `variant_4_combined`, as contagens estritas foram **10, 11, 10 e 11**. As superiores, que incluem os desconhecidos, foram **14 nas quatro**, ante o máximo de **13 em 182 elegíveis**. Com `SIN_J`, houve **3 desconhecidos**, ante **4** com Fréchet, e a contagem estrita subiu. As quatro leituras ficaram `unresolved`, com parada após A. O limite de 13 é do certificado de rota, que inclui a reserva para estimadores. [D2-F A](C:/Projetos/refute/docs/validation/v0.5.5/d2f-A.json:71) |
| Custo | Referência D2-F completa: **3,6369 CPU-h** observadas em A, projeção de **10,4 CPU-h por conjunto**, cerca de **300 mil tokens** e **1,5 dia-agente** para o desenho de R1. [Desenho R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:75) |
| Veredito | **SEM** |

### D2 | Melhor estimador de `odd_even`

| Critério | Avaliação |
|---|---|
| O que muda | Estima com mais precisão a diferença entre trânsitos pares e ímpares e sua incerteza, tratando a forma do trânsito como parâmetro auxiliar. |
| Por que é método | Preserva a diferença testada, a alternativa da bateria e a potência exigida de **0,95**. O ganho teria de vir de uma estimativa mais informativa com incerteza calibrada. |
| Evidência | A correção numérica do diagnóstico I4 já tornou válidos **22 de 22** limites antes inválidos por convergência. Mesmo com a correção, A registrou **3 casos `INFO` abaixo de 0,95**, **0 `INFO` desconhecidos** e contagem superior de **14** em todas as variantes. O ganho demonstrado foi na validade do cálculo diagnóstico. R2 retirou a troca do estimador da ordem de implementação por falta de fundamentação. [D2-F A](C:/Projetos/refute/docs/validation/v0.5.5/d2f-A.json:90) · [Argumentos R2](C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:195) |
| Custo | Referência I4: cerca de **0,024 CPU-h por planeta** para o limite. Para o diagnóstico D2-F, cerca de **300 mil tokens** e **1,5 dia-agente**. O estimador novo ficou sem preço próprio. [Desenho R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:75) |
| Veredito | **SEM** |

### T2a | Melhor estimativa do erro de fundo do E4

| Critério | Avaliação |
|---|---|
| O que muda | Estima o erro do mesmo contraste de fundo a partir de fases placebo da própria estrela, considerando a dependência entre os deslocamentos. |
| Por que é método | Preserva o contraste, a alternativa de fundo, a região de rejeição e a potência exigida de **0,95**. A mudança está na estimativa da incerteza. |
| Evidência | T2a-E liberou **2 de 85 válidas**, com **17 desconhecidas em 102 replays**. A fração **0,024** ficou na faixa `empirically limited for this estimator class` (**≤ 0,40**), diante do limiar de **≥ 0,80** para justificar construir o modelo. A inflação placebo é heurística e sua cobertura de **95%** segue sem validação. A meta histórica de T2a exigia **552 de 559**, com déficit de **221**. A liberação do bloco mede potência nesse subteste. [T2a-E 1](C:/Projetos/refute/docs/validation/v0.5.5/t2ae-1.json:46) · [T2a-E 2](C:/Projetos/refute/docs/validation/v0.5.5/t2ae-2.json:46) · [Livro de pisos e margens](C:/Projetos/refute/docs/plans/v0.5.5-g1-report-3.md:53) |
| Custo | Referência T2a-E: projeção revisada de **2,1 CPU-h por etapa**, cerca de **200 mil tokens** e **1 dia-agente** para o diagnóstico. A calibração da dependência ficou sem preço próprio. [Revisão R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:172) · [Desenho R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:75) |
| Veredito | **SEM** |

### D1 | Melhor cálculo da separação entre planetas e binárias eclipsantes

| Critério | Avaliação |
|---|---|
| O que muda | Refina o ajuste e a calibração da compatibilidade com um trânsito planetário, incorporando a incerteza estelar declarada. |
| Por que é método | Cabe como método se refinar o cálculo do mesmo ataque, com a mesma interpretação das saídas e os mesmos limites de dano aos planetas. Um novo ataque, como o teste aventado em R2, exige desenho próprio. |
| Evidência | No conjunto A, com preço **0,05**, EB1 entre todos os elegíveis teve **8,25 SURVIVED esperados** ante o máximo de **9**, mas **p05 de 0,483** ante o mínimo de **0,5**. EB2 e a visão dos sobreviventes atingiram o critério. As duas saídas decisivas ficaram `unresolved`, com parada após A. A ponte leu `route` nas duas versões e nas duas visões no recorte de **200** tentativas, com **4** diferenças de elegibilidade e **17** de veredito. A ponte é comparativa, e o escore de oráculo segue sem calibração do lado dos planetas. `INCONCLUSIVE` ainda depende de D2 e D4 cumpridas, e `REFUTED` foi examinado apenas em cenários. [D1-P A](C:/Projetos/refute/docs/validation/v0.5.5/d1p-A.json:450) · [Ponte D1-P](C:/Projetos/refute/docs/validation/v0.5.5/d1p-bridge.json:3) · [Revisão R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:138) |
| Custo | Referência D1-P: projeção de **9,9 CPU-h por conjunto** e **4,9 CPU-h para a ponte**, cerca de **300 mil tokens** e **2 dias-agente** para o desenho de R1. A calibração de um teste realizável ficou sem preço próprio. [Revisão R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:172) · [Desenho R1](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:75) |
| Veredito | **SEM** |

### D2 | B3.3 (`RULE_3`), variante de regra

| Critério | Avaliação |
|---|---|
| O que muda | Abre um `PASS` por resíduo demonstrado grande no ramo ambíguo de `sinusoid`. |
| Classificação | Muda a condição que autoriza `PASS` onde a regra congelada emite `INCONCLUSIVE`. A segunda revisão cega manteve B3.3 apenas como variante. |
| Evidência | Houve **0** casos `RULE` e **0** `RULE_3` no conjunto A. A variante isolada repetiu **10 estritos e 14 superiores** da leitura atual. A combinada repetiu **11 estritos e 14 superiores** de `SIN_J`. [D2-F A](C:/Projetos/refute/docs/validation/v0.5.5/d2f-A.json:41) · [Segunda revisão cega](C:/Projetos/refute/docs/plans/v0.5.5-consensus/r2-blind-review-2.md:178) |
| Custo | A comparação já integra o custo de D2-F acima. CPU, tokens e dias-agente para validar B3.3 com os controles adversariais ficaram sem orçamento específico em R2. |
| Veredito | **SEM** |

**NENHUMA ROTA DE MÉTODO COM VALOR DE DECISÃO DEMONSTRADO**