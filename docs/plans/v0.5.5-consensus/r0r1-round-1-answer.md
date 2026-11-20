**O conjunto ainda não está pronto para congelamento.** Os bloqueios centrais estão na interpretação estatística da D1-P e da D2-F, além do controle de execução. Os limiares solicitados estão transcritos corretamente nas funções comuns.

Fiz somente leitura local, sem rede, alterações ou execução de scripts/testes. Não acessei o diretório proibido. Os arquivos novos continuam não rastreados pelo Git, portanto os desenhos estão **especificados, ainda não congelados em commit**.

**Vereditos por item**

| Item | Veredito | Fundamentação |
|---|---|---|
| **1a** | **SURVIVED** | Reproduz os três preços decididos. A origem dos valores oferece argumento independente das necessidades de D1. Não altera metas nem resolve questões de desenho. Convém explicitar os limites de Wilson que continuam obrigatórios. |
| **1b** | **WEAKENED** | Preserva a decisão de sortear a estrela e usar sua incerteza. Acrescenta independência entre massa/raio e truncagem em 3σ, escolhas não explicitadas na decisão. “Calibrated by construction” excede o demonstrado, especialmente para a distribuição transformada `R/M^(1/3)`. |
| **1c** | **SURVIVED** | Escopo, limite populacional, três saídas, dois lados, conjuntos novos, amostragem da confirmação e revisões estão presentes. O argumento é independente dos resultados. Não autoriza escrever um registro de inviabilidade. |
| **1d** | **WEAKENED** | As sete salvaguardas estão presentes e as decisões ficam em R2. Entretanto, afirmar que qualquer aumento de sobreviventes espúrios necessariamente reprova as metas é falso: um aumento pode continuar abaixo do limite congelado. |
| **1e** | **SURVIVED** | Reproduz as nove mudanças, inclusive redimensionar a aceitação antes de pagá-la. São princípios independentes dos valores obtidos. A implementação operacional ainda não cumpre integralmente essas decisões. |
| **2** | **WEAKENED** | O `finally` restaura a função em execução serial, inclusive após exceções. O estado é local ao processo, mas global dentro dele e inseguro para chamadas concorrentes. O fluxo `[seed, 5505]` preserva os fluxos aleatórios anteriores. Mudam também profundidade e outras grandezas derivadas das durações. `forecast.planet_model` volta a usar a função original depois do contexto. |
| **3-D2F** | **REFUTED** | Fórmula da covariância cruzada, oito fases, 20.000 sorteios e verificações das marginais conferem para o modelo GLS declarado. Porém as categorias não demonstram um piso inevitável de **perdas de retenção**. A falha de um certificado de PASS não exclui um warning FAIL, que mantém o planeta. `RULE_3` também presume uma média da caixa não demonstrada para o trânsito trapezoidal. |
| **3-D1P** | **REFUTED** | Regras `route`/`closed` conferem, e o sentido do viés numérico para `route` está corretamente declarado. Mas a calibração planetária da leitura primária não foi estabelecida. O código avalia **três**, não quatro ajustes. O preço fatal transporta `3/178` entre baterias/populações diferentes sem medir a margem correspondente. |
| **3-T2aE** | **WEAKENED** | Implementa os limiares `0,8V`, `0,4V` e `UNK>20`, o placebo do próprio E4 e as paradas herdadas do passo 6. O fator χ² está algebricamente correto sob amostras normais independentes, condição ausente aqui. O piso branco vale para a combinação dos operadores declarados, não para qualquer estimador. A comparação numérica anunciada com o registro histórico de I1 está incompleta. |
| **3-T3b** | **WEAKENED** | **Adiar a execução é a aplicação conservadora correta de (e)**, dado o teste de valor de decisão declarado. Mas a justificativa factual continua restritiva demais: elegibilidade pode mudar sem nova tabela TOI. O script antigo tampouco aceita simplesmente uma tabela nova, pois exige os insumos congelados. |
| **3-comum** | **REFUTED** | Alocações e tetos aritméticos conferem. Há incompatibilidade `pause_at=None` com o driver, ausência de contador de retomadas, erro de interpretação do teto na retomada e identificação incompleta do código/insumos congelados. Os testes apresentados não cobrem esses caminhos. |
| **4** | **WEAKENED** | As correções reproduzem os pontos aceitos, e a cópia da conferência factual tem o mesmo SHA-256 da origem. Os dois registros históricos permanecem sem diff. O ROADMAP preserva a regra de avanço, mas acrescenta explicação corretiva dentro do parágrafo histórico e contradiz a declaração de que esse parágrafo mantém seus bytes. Também anuncia quatro execuções, embora T3b tenha sido adiada. |

**Correções concretas, em ordem de prioridade**

Todos os caminhos abaixo pertencem a `C:\Projetos\refute`. São recomendações, nenhuma foi aplicada.

1. **Distinguir certificado de PASS de retenção na D2-F.**  
   [d2f_floor.py:306](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:306), [desenhos:119](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:119).  
   A união atual conta `SIN_F`/`SIN_J` como perdas mesmo quando um warning FAIL pode manter o planeta. O próprio desenho anterior, `v0.5.4-h2-step7-sinusoid.md:67`, distingue essas situações e admite que sua contagem era condicional.

   **Texto:** “These counts diagnose certificate limitations and observed blockers. They are not demonstrated lower bounds on unavoidable retention losses.”

   Para conservar a saída `closed`, cada categoria da contagem estrita precisa demonstrar perda inevitável dentro de uma classe explicitamente definida. Até isso existir, resultados baseados nessa união devem permanecer `unresolved` quanto ao fechamento de D2.

2. **Corrigir a probabilidade de `RULE_3`.**  
   [d2f_floor.py:341](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:341).  
   `p_large = p_small` exige que a média do estimador da caixa sob o planeta seja exatamente `D`. O gerador produz um trânsito trapezoidal, enquanto a coluna ajustada é uma caixa.

   **Correção:** calcular a média do estimador GLS sob o sinal planetário verdadeiro,
   `mu_box = [G2^-1 X2' Sigma^-1 mu_planet][0]`, e usar
   `P_large = Φ((mu_box - 0.5 D)/sigma_box - 3)`. Registrar a média calculada e as hipóteses. Não reutilizar `p_small` por simetria sem provar `mu_box=D`.

3. **Retirar a calibração automática atribuída à D1-P.**  
   [desenhos:185](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:185), [d1p_price.py:89](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:89).  
   A penalização é centrada em `rho_B`, uma verdade latente, enquanto o catálogo entregue permanece centrado em 1. Isso pode integrar uma construção de oráculo com catálogo como observação aleatória, mas não equivale automaticamente ao experimento implementado, condicionado ao catálogo fixo.

   **Texto:** “This is an oracle surrogate under an explicitly specified catalog experiment. Planet-side calibration and the interpretation of `Φ(z_x-d)` have not been established.”

   Antes de lhe atribuir saídas decisivas, demonstrar a construção estatística, o tratamento dos parâmetros ajustados e da seleção pelos sobreviventes da bateria. Sortear a estrela, isoladamente, não fornece essa demonstração.

4. **Resolver a discrepância entre três e quatro ajustes.**  
   [d1p_price.py:141](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:141), [desenhos:190](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:190).  
   `fits` recebe somente `box`, `known` e `prior_fit`.

   **Texto, se esses forem os ajustes pretendidos:** “The smallest evaluated objective over three fits: prior-weighted, box-constrained and known-star.”

   A descrição atual também menciona “the three below”, mas lista dois. Se um quarto ajuste era necessário, especificá-lo antes do congelamento e rever seu custo. O caráter de limite superior da minimização aproximada, com viés para `route`, está corretamente explicado.

5. **Tornar o preço fatal explicitamente condicional à referência correta.**  
   [d1p_price.py:69](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:69), [desenhos:207](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:207).  
   `3/178` é uma observação da **version 5** no conjunto antigo. D1-P usa a bateria v0.5 de `paired_chain` e o gerador v2.

   **Texto:** “The value 0.05−3/178 is a historical reference scenario, not measured available room for this battery on generator v2.”

   A leitura decisiva deve usar margem medida em desenvolvimento para a bateria/população correspondente. `WEAKENED=0,10` coincide com o estatuto. `INCONCLUSIVE=0,05` deve continuar condicionado ao cumprimento integral de **D2 e D4**, não apenas à restauração nominal de D2.

6. **Explicitar todos os requisitos congelados do preço fatal.**  
   [estatuto:51](/C:/Projetos/refute/docs/plans/v0.5.5-charter.md:51).  
   Acrescentar:

   **Texto:** “The frozen Wilson upper limits also remain mandatory: 0.10 for P and 0.20 for PG, PV and PA. Subtracting observed fractions does not establish compliance with the joint battery rules.”

   Isso esclarece a decisão existente, sem criar novo orçamento.

7. **Qualificar a distribuição estelar e a truncagem.**  
   [estatuto:84](/C:/Projetos/refute/docs/plans/v0.5.5-charter.md:84), [generator_v2.py:38](/C:/Projetos/refute/docs/validation/v0.5.5/generator_v2.py:38).  
   A truncagem elimina aproximadamente **0,54% da massa conjunta** e reduz a dispersão marginal. Além disso, `R/M^(1/3)` não é exatamente gaussiano, e `effective_sigma()` é uma aproximação de primeira ordem.

   **Texto:** “Independent R and M errors and 3σ truncation are additional modelling conventions. The effective-radius Gaussian approximation is not the exact generator law.”

   Para fidelidade literal ao prior gaussiano de 5%, retirar a truncagem artificial, mantendo apenas domínio físico, ou registrar a distribuição truncada como escolha adicional e justificar sua compatibilidade. Substituir “calibrated by construction” por uma afirmação restrita à distribuição efetivamente sorteada.

8. **Restringir a garantia de segurança do patch ao uso serial.**  
   [generator_v2.py:59](/C:/Projetos/refute/docs/validation/v0.5.5/generator_v2.py:59), [test_generator_v2.py:39](/C:/Projetos/refute/tests/v055/test_generator_v2.py:39).  
   O `finally` é adequado, mas outra chamada no mesmo processo pode observar a substituição ou interferir na restauração.

   **Texto:** “This context mutates process-global module state and requires exclusive, serial use within each worker process.”

   Acrescentar regressões para exceção dentro de `generate` e para `forecast.planet_model` antes/depois da chamada. Corrigir “changes only the durations” para incluir profundidade e demais valores derivados pelo ponto fixo de `solve_depth`.

9. **Corrigir a promessa de cobertura de 95% do placebo.**  
   [t2ae_census.py:111](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:111), [desenhos:272](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:272).  
   O fator `sqrt((K−1)/χ²_0.05(K−1))` pressupõe observações normais independentes. Os deslocamentos compartilham o hospedeiro, podem compartilhar cadências e passam por processamento dependente da fase. A ressalva posterior reconhece dependência, mas não resolve a alegação anterior.

   **Texto:** “The χ² multiplier is a heuristic inflation here; 95% coverage has not been established for these dependent placebo estimates.”

   Manter a interpretação exploratória ou especificar previamente um procedimento que trate a dependência e cuja cobertura possa ser validada.

10. **Limitar corretamente o alcance do piso branco.**  
    [t2ae_census.py:121](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:121), [desenhos:274](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:274).  
    A fórmula combina por variância inversa os operadores E4 de janelas disjuntas sob escala branca comum. Não demonstra o melhor desempenho de qualquer estimador, nem incorpora automaticamente a transformação do ruído pelo detrending.

    **Texto:** “This is the minimum-variance combination of the declared E4 window contrasts under the stated white-noise approximation.”

    Validar `sigma_w>0` e variâncias finitas positivas **antes** das divisões da linha 144, retornando `UNK` quando inválidas.

11. **Comparar o replay com os números históricos de I1.**  
    [t2ae_census.py:159](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:159).  
    As paradas do passo 6 foram preservadas mecanicamente. Contudo, `recorded` e `recorded_power` vêm do próprio replay recém-calculado. A população vem de I1, enquanto `mismatch` verifica referências de B1. Isso não compara os dois números com seus valores históricos de I1.

    **Correção:** carregar a referência histórica por `key/slot`, conferir sua proveniência e comparar classe, erro e potência com ela nas tolerâncias declaradas. Divergência deve levantar a parada antes do placebo.

12. **Corrigir `pause_at=None` nos três executores.**  
    [r1_common.py:66](/C:/Projetos/refute/docs/validation/v0.5.5/r1_common.py:66).  
    Em horário comercial, essa função retorna `None`. O driver herdado faz `moment >= self.pause_at` e `self.clock() >= self.pause_at`, sem tratamento para `None`, nas linhas 575 e 509 de `driver.py`.

    **Correção:** fornecer sempre um `datetime` com fuso compatível, usando um instante sentinela futuro quando não houver pausa, ou criar um adaptador v0.5.5 que trate ausência de pausa. Acrescentar regressão de integração com relógio simulado. O teste atual verifica justamente o retorno incompatível, sem alcançar o driver.

13. **Distinguir parar despachos de cumprir o limite às 08h.**  
    [desenhos:36](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:36).  
    Parar novos despachos às 08h permite que até 22 trabalhos já iniciados continuem em horário comercial. Para garantir no máximo dez trabalhadores nesse intervalo, encerrar despachos antecipadamente e drenar o excedente antes das 08h.

    **Texto:** “The transition must account for in-flight shards; stopping dispatch at 08:00 alone does not establish the ten-worker limit.”

    Também qualificar os 1.200 segundos como limite declarado: o driver detecta excesso após a conclusão, não impõe esse prazo como timeout rígido.

14. **Implementar uma única retomada e corrigir seu teto.**  
    [ledger_v055.py:136](/C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:136), [ledger_v055.py:182](/C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:182).  
    Não existe contador persistente de retomadas. A mesma identidade pode ser retomada repetidamente após pausas. Além disso, `hard_cap()` calcula saldo restante, mas o driver compara seu argumento com consumo **cumulativo** da execução, causando parada prematura na retomada.

    **Correção:** persistir `resume_count`, permitir apenas a retomada pré-aprovada e converter o saldo para o teto cumulativo esperado pelo driver, contando o consumo anterior uma única vez. Fazer validação e reserva sob o mesmo bloqueio exclusivo.

15. **Completar a identidade congelada e validar a primeira etapa ao combiná-la.**  
    [d1p_price.py:241](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:241), [d2f_floor.py:401](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:401), [t2ae_census.py:227](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:227).  
    O hash de `src/` não cobre dependências em `docs/validation/`. Faltam, entre outras, `driver.py`, `budgeted.py` e, na D2-F, **`b1-composition.json`**, que `config()` lê.

    **Correção:** congelar um manifesto completo das dependências executadas, configurações e insumos. Cada resumo deve registrar essa identidade comum; B/etapa 2 deve verificar a identidade e o hash do resumo anterior antes de usar sua futilidade ou combinar contagens.

16. **Preservar os elementos necessários ao diagnóstico por caso.**  
    [t2ae_census.py:104](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:104), [d1p_price.py:185](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:185), [d2f_floor.py:256](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:256).  
    T2a-E guarda contagens dos placebos, mas não cada fase, valor e recusa; reduz o replay a poucos campos. D1-P omite parâmetros completos dos ajustes. D2-F omite partes da verdade e do candidato final.

    **Texto:** “Each case retains the replay record, complete fit parameters, per-placebo phase/value/status, and references with hashes to the preserved inputs.”

    Isso é necessário para cumprir a mudança de processo 9 sem refazer a execução para recuperar detalhes.

17. **Corrigir o alcance das salvaguardas prospectivas.**  
    [estatuto:142](/C:/Projetos/refute/docs/plans/v0.5.5-charter.md:142).  
    Substituir a conclusão categórica sobre qualquer aumento de espúrios por:

    **Texto:** “The frozen spurious-family targets remain mandatory adversarial checks. Passing them does not by itself prove that no relaxation occurred elsewhere.”

    Preservar as demais salvaguardas e a reserva das decisões para R2.

18. **Manter T3b adiada, corrigindo sua justificativa e procedimento futuro.**  
    [desenhos:325](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:325).  
    **Texto:** “Availability may change through domain-eligibility metadata without a new TOI table. A recount of the frozen frame and construction of an updated frame are distinct operations.”

    O método antigo exige quadro `63/41/11`, 22 restantes e os hashes congelados. Uma tabela posterior exige novo desenho de proveniência e autorização correspondente. Preservar “does not run in R1”; o adiamento não deve virar uma constatação atual de indisponibilidade.

19. **Corrigir a precisão das estimativas e do saldo orçamentário.**  
    [desenhos:55](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:55).  
    A fonte mede três baterias em curvas D2 e declara D1 não medido. Portanto `0,039 CPU-h` não é limite superior demonstrado para cada binária. O preço dos ajustes novos e dos placebos também é extrapolação.

    **Texto:** “These are workload-dependent extrapolations, not measured upper bounds for the new checks. Review-token and agent-time figures are planning estimates.”

    A soma **32 + 22 + 5 + 4,5 + 0,5 = 64 CPU-h** confere. Os demais pontos de parada são **2,4 M tokens, 7,2 dias-agente e 4 GB**. “2,4 M left” deve virar “2,4 M stop threshold, less consumption already recorded”. Só a revisão factual registrada já consumiu 168.755 tokens, deixando 2.231.245 antes desta rodada. Os guardas devem ser descritos como verificações nas fronteiras das etapas, sem alegar monitoramento contínuo dos quatro recursos.

20. **Qualificar “nenhuma execução” e ajustar o ROADMAP apenas com ponteiros.**  
    [desenhos:10](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:10), [ROADMAP.md:71](/C:/Projetos/refute/ROADMAP.md:71), [correções:10](/C:/Projetos/refute/docs/validation/v0.5.4/pause-record-corrections.md:10).

    Existe um artefato anterior, `.cache/v055/junit-v055.xml:1`, relatando **14 testes unitários**, inclusive geração sintética. Não os executei nem isso valida os executores R1.

    **Texto:** “No R1 experimental check has run. Earlier unit-test activity is recorded separately.”

    No ROADMAP, preservar a frase histórica e acrescentar somente o link ao registro corretivo, retirando a explicação numérica inserida nas linhas 73 a 75. Na linha 52, usar: “The pause ends; its record remains historical, subject to the linked corrections.” Na descrição de R1, usar: “designs for four checks; T3b execution deferred by the decision-value test”.

**Limites da constatação:** o diff consultado não mostra mudanças em `src/`, `pause-record.md` ou `h2-stop-report.md`. Não encontrei artefatos de execução experimental R1 nem seleção nova de alvos reais no material revisado. Isso sustenta uma conclusão local sobre os arquivos observados, não uma prova absoluta de ausência de atividade anterior.