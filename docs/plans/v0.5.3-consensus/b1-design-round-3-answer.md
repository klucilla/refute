**Os quatro estimadores agora têm desenhos implementáveis.** Restam correções na triagem estatística e no controle de disco. Elas podem ser resolvidas pelas opções conservadoras abaixo, sem nova medição nem mudança de alvo.

Somente leitura. Fiz apenas conferências e contas pequenas. `B1:linha` refere-se ao [desenho revisado](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md).

### Correções que sobreviveram

| Ponto | Resultado |
|---|---|
| **E1** | A ordem v4 primeiro preserva seus resultados finitos. O alcance do limite completo e do limite condicionado às estimativas mantidas está corretamente separado. Definir explicitamente que termos ausentes recebem zero **somente na matriz usada para escolher o ramo PSD**. ([B1:101](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:101)) |
| **E2** | Cholesky, limites de condicionamento, solves triangulares e fallback resolvem o problema de inversão. A família de boxes permanece igual. ([B1:139](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:139)) |
| **E3** | Momentos, variância estacionária, propagação temporal, ausência de atualização nas máscaras e separação entre whitening e multiplicação por `Σ` estão coerentes. Usar QR/SVD no OLS whitened, evitando equações normais. ([B1:162](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:162)) |
| **E4** | QR escalado, fallback geométrico comum e erro branco próprio resolvem os pontos numéricos. A resposta unitária vale para a alternativa confinada e protegida pelo preprocessing. O teste deve comparar **com injeção menos sem injeção**, cobrindo também o fallback. ([B1:218](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:218)) |
| **D2/D4** | Regras congeladas, comparador v0.4 e intervalos apenas diagnósticos estão corretos. |
| **T2a** | Censo, `K_B/U_B`, conclusão sobre o limite superior de C e overrun como stop estão corrigidos. ([B1:373](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:373)) |
| **Stop e T3b** | Preço por disponibilidade/tamanho, certificações ainda devidas e recomendação condicionada à qualificação estão adequados. |

Para E3, completar a expressão usada pela implementação: inicializar `R₁=0` e acumular  
`uᵀKu = Σuᵢ² + 2ΣuᵢRᵢ`, separadamente por setor. Isso corresponde à recursão especificada em [B1:185](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:185).

### 1. A disponibilidade não pode apagar um FAIL

A regra “menos de 80% implica todos UNRESOLVED” pode neutralizar um desvio grave já observado ([B1:334](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:334)).

Ela também conflita com E1: seus contrastes existem deliberadamente apenas onde v4 recusa. Trinta recusas entre 450 curvas satisfazem o mínimo específico, mas nunca os 80% globais ([B1:288](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:288)).

**Opção conservadora:**

- Calcular disponibilidade sobre a população elegível ao ramo novo. Para E1, são as recusas relevantes de v4.
- Disponibilidade insuficiente impede PASS, mas **não sobrescreve FAIL** obtido com tamanho suficiente.
- Registrar separadamente tentativas, elegíveis, execuções novas, fallbacks e contrastes disponíveis.

### 2. Os intervalos não sustentam ainda a garantia simultânea declarada

O aumento para 450 resolveu a impossibilidade aritmética: com zero excedências, o limite Clopper–Pearson é **0,013626**. Isso depende do número **efetivamente disponível**; com 360, sobe para **0,017003**.

Entretanto, independência entre curvas não garante normalidade dos pulls. Erros estimados, seleção de ramo e misturas de regimes podem produzir distribuições não normais. O intervalo qui-quadrado para desvio padrão depende dessa hipótese e é sensível à sua violação. Bonferroni não corrige intervalos marginais sem cobertura adequada. ([B1:311](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:311); [NIST](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/sdconfli.htm))

**Opção conservadora:** manter t/qui-quadrado como diagnósticos condicionais ao modelo, sem alegar cobertura simultânea demonstrada. Resultados cuja cobertura não esteja sustentada ficam UNRESOLVED para conclusões inferenciais. Um veto exploratório conservador pode excluir um estimador, mas deve ser apresentado como tal, sem transformar ausência de veto em calibração.

Isso preserva a finalidade limitada de B1.3 já declarada em [B1:345](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:345).

### 3. E4 precisa de uma regra para bootstrap degenerado

A unidade host corrige a falsa independência das oito pseudo-efemérides. Porém, **16 hosts e bootstrap percentil não garantem os intervalos extremos pretendidos** ([B1:305](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:305)).

Há um caso concreto: se nenhum contraste exceder 3σ, todas as réplicas terão fração zero. O intervalo percentil será `[0,0]`, produzindo um PASS artificial para a cauda. Mesmo supondo 128 observações independentes, hipótese favorável demais, o limite exato seria aproximadamente **0,0471**, acima de 0,015.

**Opção conservadora:**

- Bootstrap degenerado, ausência de excedências ou suporte insuficiente para a cauda resultam em **UNRESOLVED**, nunca PASS inferencial.
- Os intervalos dos 16 hosts permanecem exploratórios; dependência instrumental entre hosts também não está excluída.
- Congelar ponderação por host e quantidade finita de propostas de pseudo-efemérides, sem reposições indefinidas.
- A composição continua uma decisão de desenvolvimento, sem permissão calibrada para T2a.

### 4. A reserva estimada não garante o teto de disco

Duas vezes o tamanho médio do checkpoint é uma projeção, não um limite superior. Além disso, o próprio checkpoint precisa escrever antes de fornecer essa estimativa ([B1:443](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:443)).

**Opção conservadora:** impor quota antes de cada escrita, incluindo checkpoint, temporários, sidecars e downloads. Recusar a escrita e parar antes de ultrapassar 5 GB. A projeção pode orientar reservas, mas não substituir esse controle.

As três partes de T2a também precisam receber alocações numéricas prospectivas, somando no máximo 60 CPU-h, antes de seus dispatches. A estimativa agregada continua **55,94 CPU-h**, ainda não medida.

### Ajustes editoriais

A tabela histórica da rodada 1 conserva “400 curvas” e “overruns recorded unknown”, contrariando o texto atual ([B1:507](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:507)). Marcar essas células como superadas. A razão 65× foi medida no background original e não demonstra, sozinha, a escala temporal do resíduo após detrending ([B1:206](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:206)).

**WEAKENED, pronto para código com as correções conservadoras acima incorporadas ao desenho antes da implementação.**