Há **bloqueios corrigíveis antes da execução**, tanto estatísticos quanto operacionais. Fiz apenas leitura e checks leves em memória, sem gerar curvas, executar a medição, alterar arquivos ou acessar GitHub ou o caminho proibido.

**1. Inventário da seção 2**

A conclusão principal está correta: **dada a estrela catalogada, não identifiquei informação adicional de EB1/EB2 fora da curva de luz**. Os pixels reproduzem o fluxo já observado, acrescido de ruído, e os parâmetros estelares são iguais entre famílias. Evidências: [synthetic.py:390](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:390), [synthetic.py:295](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:295), [synthetic.py:203](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:203).

Há uma correção na tabela: **usar `solve_depth` não implica distribuições de profundidade idênticas**. EB2 usa período geométrico dobrado e divide pelo fator `(1+r)/2`: [c1.py:291](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:291). Portanto, “depth: no” é categórico demais em [design:39](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:39).

Falta explicitar a rota de **tamanho do candidato**, presente no [LEO-Vetter, IV.1](https://arxiv.org/html/2509.10619v1#S4.SS1). Ela usa profundidade e raio estelar, portanto permanece no canal já inventariado. Sua capacidade de separar este C1 precisa ser verificada, incluindo PG. Não encontrei outra modalidade independente que C1 forneça.

**2. Validade do oracle e direção das aproximações**

**A fórmula está correta para duas distribuições gaussianas fixas com covariância comum**:
\[
\beta_{\min}=\Phi(z_{1-\alpha}-d).
\]
Se o nível vale para **cada planeta do nulo**, qualquer planeta admissível fornece esse limite inferior para a probabilidade de não rejeição. Não é necessário encontrar o mínimo exato, embora encontrá-lo fortaleça o limite. Essa aplicação decorre do [lema de Neyman e Pearson](https://stat210a.berkeley.edu/fall-2024/reader/hypothesis-testing.html).

**O script, porém, ainda não estabelece um limite para D1 condicionado à seleção.** A elegibilidade e o período vêm da mesma curva ruidosa: [d1_bound.py:89](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:89). Condicionar à busca altera o experimento; a fórmula gaussiana incondicional não passa automaticamente a valer nesse subconjunto. O plano anterior reconhecia exatamente essa limitação: [v0.5.1-plan.md:141](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:141), [v0.5.1-plan.md:159](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:159).

Também **nem todas as aproximações têm a direção alegada**:

- Restringir período e perder o mínimo, inclusive ajustar em pesos brancos antes de pontuar pela covariância, enfraquece conservadoramente o limite, desde que o planeta resultante pertença ao nulo: [d1_routes.py:104](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/d1_routes.py:104).
- **Omitir a tendência não tem direção garantida.** C1 a aplica multiplicativamente; mesmo conhecida, ela modifica a diferença entre as médias. O residual correto inclui esse fator: [c1.py:375](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:375), [d1_bound.py:117](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:117).

**`star_known` é uma proteção adequada contra atribuir inviabilidade à largura do nulo estelar**, mas não corrige seleção, tendência ou incerteza amostral. Se o nulo declarado contém toda a caixa de 3σ, essa caixa não é uma exceção matemática; usar um prior gaussiano define outro problema.

**3. Nível 0,0027 e regra A/B/C**

**O nível tem precedente independente dos números divulgados**, verificável na aceitação anterior: [v0.5.1-plan.md:127](C:/Projetos/refute/docs/plans/v0.5.1-plan.md:127). A divulgação da exploração anterior é apropriada: [design:101](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:101).

Entretanto, quantis empíricos separados de P e PG **não demonstram controle uniforme para cada planeta e cada estrela do nulo**. Essa premissa precisa permanecer explicitamente uma exigência a justificar: [design:73](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:73), [design:117](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:117).

A/B/C está pré-especificada, mas precisa destas correções:

- **A:** expectativa acima do allowance não demonstra que nenhuma realização ou rota alcança a contagem. Falta tratar incerteza e justificar a ligação com o experimento condicionado.
- **B:** limite abaixo do allowance permite investigar uma rota, sem demonstrar alcançabilidade.
- **C:** não demonstra que parâmetros melhores sejam a única solução. Apenas registra que esses limites não resolvem a questão.
- Acrescentar parada sem conclusão para erros, dados insuficientes ou limites não válidos.

Referência: [design:109](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:109). Além disso, a projeção não verifica a segunda condição de D1, `s05 <= s04`: [c1.py:649](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:649).

**4. INCONCLUSIVE**

**Correto e sem decidir uma mudança:** D1 conta apenas SURVIVED; INCONCLUSIVE e WEAKENED permanecem fora desse numerador. Evidências: [c1.py:641](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:641), [design:96](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:96).

Convém chamar o resultado do oracle de **probabilidade de não rejeição**, reservando SURVIVED ao veredicto agregado. `excess_over_allowance_fraction` é uma quantidade esperada ilustrativa, não uma fração comprovadamente necessária de INCONCLUSIVE: [d1_bound.py:233](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:233).

**5. Código e contabilização**

**Checks positivos:** 800 seeds distintos; namespace separado dos anteriores; checkpoint com ambas as famílias; allowances 11 para 194 e 10 para 186. Referências: [d1_bound.py:68](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:68), [d1_bound.py:123](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:123).

Correções necessárias:

- **Bloqueio imediato do ledger:** alocações de 150 mais smoke de 0,0055 produzem projeção de **150,0055 CPU-h**. O guard para antes do primeiro shard. Ajustar reservas e a validação da soma, preservando a cobrança: [ledger_b.py:43](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:43), [ledger_b.py:83](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:83), [budgeted.py:247](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:247).
- **Falhas desaparecem da projeção:** o denominador usa somente `OK`. Quatro tentativas com duas falhas e duas elegíveis projetaram 200 elegíveis, em vez de 100 sobre tentativas. Erros também não impedem a interpretação. Zero elegíveis causa `ZeroDivisionError`: [d1_bound.py:199](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:199).
- **Elegibilidade:** reproduz o forecast, mas não a elegibilidade congelada de C1, que depende do gate após finalização: [d1_bound.py:93](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:93), [pipeline.py:247](C:/Projetos/refute/src/refute/packs/tess/pipeline.py:247).
- **Bootstrap:** implementação coerente como forecast de coortes reamostradas, mas mediana/p95 das CDFs não constituem prova de inviabilidade nem intervalo de confiança da expectativa. `n'` fica fixo: [d1_bound.py:220](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:220).
- **Tokens:** escolher o último `turn.completed` da última rodada da mesma conversa implementa a regra fornecida: [ledger_b.py:147](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:147). Porém, o stop usa `>` em vez de `>=`. Confirmei em memória que **1.200.000 tokens B0 são permitidos**, contrariando “ao atingir 80%”: [ledger_b.py:207](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:207).
- **Subcap CPU:** a reserva e a divisão por 1,10 são conservadoras. Na retomada, conferir o desconto do consumo atual, pois o driver recebe teto cumulativo: [ledger_b.py:137](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:137), [budgeted.py:285](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:285).

**6. Outros pré-requisitos**

O fingerprint cobre adequadamente o código computacional e o claim: [d1_bound.py:149](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:149). **Vincular também o desenho final e sua interpretação ao commit anterior à medição.**

`summarize` não verifica caps nem contabiliza seu próprio trabalho: [d1_bound.py:241](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:241). Corrigir isso e definir a checagem dos limites durante trabalhos longos.

O caminho mínimo é preservar este cálculo como **diagnóstico**, corrigir os bugs e impedir que A produza uma conclusão de inviabilidade antes da justificativa condicional.

WEAKENED (run after the listed corrections)