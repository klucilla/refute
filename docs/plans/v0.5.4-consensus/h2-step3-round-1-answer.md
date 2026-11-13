Revisei o estado em `d5cfbee`, somente por leitura local, sem rede e sem executar o experimento. **A correção conceitual sobrevive, mas há correções necessárias antes de aceitar uma rota.**

### 1. Passo 2: incremento

**Está bem definido e é conservador.** Os custos próprios `r_f` e `i_f` não herdam a retenção já insuficiente da versão 5. Contar todas as rejeições, inclusive sobrepostas às perdas da referência, superestima o custo incremental, de forma conservadora. Os orçamentos estritos e os dois resultados, rota ou `INCONCLUSIVE`, estão congelados. [step2:47](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:47), [step2:61](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:61).

**A hipótese binária é honesta:** exigir que o novo teste rejeite sozinho é suficiente para investigar uma rota, mas seu insucesso não demonstra inviabilidade da bateria. A ausência da cláusula comparativa com v0.4 também está declarada. [step2:36](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:36).

Há duas inconsistências a corrigir: o passo 2 ainda promete sensibilidade própria e bandas simultâneas em todos os limiares, enquanto o passo 3 não modela sensibilidade e avalia somente `τ*`. [step2:77](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:77), [step2:98](C:/Projetos/refute/docs/plans/v0.5.4-h2-step2-i3-increment.md:98).

### 2. Passo 3: estatística e inferência

- **Estatística defensável como razão de verossimilhanças aproximada:** ambas as famílias usam as mesmas cadências em cada meio período, pesos comuns e um offset livre em cada ajuste. Os aliases binários `P` e `2P`, limites e partidas estão implementados. A caixa estelar corresponde à convenção de B0, uma restrição dura sobre `R/M^(1/3)`, sem penalidade gaussiana. Não demonstra máximo global nem validade sob ruído correlacionado. [script:85](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:85), [script:118](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:118).

- **Ajustar a descrição numérica:** o desenho omite o offset e chama as partidas de profundidade de “B0”, mas o script usa `depth0` e `1.5·depth0`. Além disso, normaliza o fluxo por `level` sem normalizar `sigma` pelo mesmo fator. Para interpretar o resultado como χ² com esses erros, normalizar ambos. [script:100](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:100), [script:122](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:122).

- **Calibração separada está correta:** `τ*` depende somente de calibração; avaliação usa sementes distintas. Examinar os valores ordenados de Λ implementa os pontos de mudança do limiar contínuo. Isso permite inferência no `τ*` escolhido, mas não uma banda sobre todos os limiares. [script:356](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:356).

- **O Bonferroni não estabelece a banda conjunta anunciada.** Existem oito limites: três em P, três em PG/PV/PA e dois binários. Dividir α por seis famílias não controla automaticamente vários limites dentro de P. Corrigir para oito limites ou demonstrar uma construção simultânea por família. [desenho:69](C:/Projetos/refute/docs/plans/v0.5.4-h2-step3-i3-population.md:69), [script:285](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:285).

- **D1 usa corretamente o Wilson na projeção, mas testa uma média.** Sem perdas novas, recupera `n′=190/186`, com tolerância de dez. Entretanto, `U(p)·n′≤k` não demonstra probabilidade conjunta de aprovação ≥0,95, exigida na auditoria. Por exemplo, em `p=10/190`, a probabilidade binomial de até dez sobreviventes é aproximadamente **0,583**. Calcular o limite da probabilidade conjunta ou restringir explicitamente a conclusão à fração média projetada. [script:366](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:366), [audit-check:56](C:/Projetos/refute/docs/plans/v0.5.4-audit-check.md:56).

### 3. Erros, execução e orçamento

**Há descarte potencialmente otimista:** erros até 5% são tolerados, mas desaparecem dos denominadores por não terem `eligible`. Binárias que deixam de reproduzir a elegibilidade também podem desaparecer e reduzir a projeção. Preservar a população congelada, tratar desconhecidos conservadoramente ou parar. [script:184](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:184), [script:271](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:271), [script:331](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:331).

As duas partes, uma curva por shard, checkpoints de 60/38 curvas, afinidade e drain de **18/11 às 19:30** estão implementados. O resumo cobra CPU com identificador único antes de escrever o resultado, inclusive quando o cálculo falha. [script:194](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:194), [script:232](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:232), [script:302](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:302).

Duas correções orçamentárias:

- `1,4 × 1.200 × 16,4 s` resulta em **7,653 CPU-h**, não 7,5.
- A barreira de **80% da CPU da fase**, prometida no desenho, não aparece no caminho executado: `hard_cap` protege 50 CPU-h; `check_caps` aplica 80% aos tokens. Falta conferir e reservar CPU para ambas as partes e o restante do plano sob a barreira anunciada. [desenho:101](C:/Projetos/refute/docs/plans/v0.5.4-h2-step3-i3-population.md:101), [ledger:230](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:230), [ledger:342](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:342).

### 4. Limites das conclusões

Os três resultados por curva estão explícitos. **Sem sensibilidade, PASS significa apenas não rejeição.** O desenho reconhece que isso subestima `i_f`; portanto, uma rota continua condicionada a essa limitação e não satisfaz integralmente a condição anterior de sensibilidade. [desenho:38](C:/Projetos/refute/docs/plans/v0.5.4-h2-step3-i3-population.md:38).

A proibição de resultado negativo está correta. Porém, o resumo não produz os orçamentos completos nem as curvas de separação prometidos como relatórios auxiliares. [desenho:85](C:/Projetos/refute/docs/plans/v0.5.4-h2-step3-i3-population.md:85), [script:378](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:378).

**WEAKENED (corrigir banda conjunta, alcance de D1, desconhecidos e denominadores, coerência numérica e documental, e reserva de CPU).**