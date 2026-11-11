## Correções necessárias

- **Arredondamentos:** em [b0b-record.md:31](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b0b-record.md:31), EB2 deve ser **12.9 e 0.077**, não 13.0 e 0.078. Os valores são 12.945299 e 0.077464 ([JSON:214](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1-infeasibility.json:214), linha 219).

- **Probabilidade pequena não é zero:** “with no cohort probability” em [b0b-record.md:45](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b0b-record.md:45) exagera. As medianas são **3.34×10⁻⁸ e 1.95×10⁻¹⁴** ([JSON:54](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1-infeasibility.json:54), linha 177). Escrever “medianas extremamente pequenas”; `0.000` nas tabelas é apenas arredondamento.

- **Leitura em 0.05:** [b0b-record.md:46](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b0b-record.md:46) atribui diretamente a um teste as contagens e probabilidades do oráculo. Identificar **12.0/13.1 como limites otimistas de contagens esperadas**, e **0.452/0.102 como medianas das probabilidades sob esse limite**, condicionadas às hipóteses. Não demonstram desempenho alcançável por uma rota ([desenho B0:83](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:83)).

- **Comparação com B0:** os números e a inversão estão corretos, mas “shows the size of the cohort variation” em [b0b-record.md:53](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b0b-record.md:53) extrapola duas amostras. Trocar por “illustrates sensitivity to the development seed set”, sem alegar quantificação dessa variação.

## Conferências aprovadas

- **Resultado (N):** ambas as famílias são válidas; em 0.05, nenhuma tem mediana abaixo de 0.05. Confere com [outcome:161](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:161) e [desenho:57](C:/Projetos/refute/docs/plans/v0.5.3-stageB0b-design.md:57). A abertura do registro preserva corretamente D1 pendente, nenhuma nova rota, nenhum draft e nenhuma declaração de inviabilidade, conforme a [decisão do mantenedor](https://github.com/klucilla/refute/issues/217#issuecomment-6804003610).

- **Demais números:** contagens, projeções, allowances, expectativas e probabilidades conferem, ressalvadas as correções acima. O denominador inclui as **400 tentativas por família**, inclusive a falha de geração ([d1_bound.py:223](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:223)). CPU e tokens conferem: execução **2.450981 CPU-h**, B0 total **4.922674 CPU-h**, revisão **109,572**, B0 **383,764** ([ledger:44](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger.json:44), [caps:262](C:/Projetos/refute/docs/validation/v0.5.3/stageB/caps.json:262)).

- **Procedimento:** recomputei o fingerprint **584a56d8f50283fe** com arquivos iguais aos de `98fa3c7`; validei os 80 shards/sidecars e as 800 sementes distintas, disjuntas de B0. Zero ERROR, distâncias finitas, execução completa, cobranças fechadas e caps respeitados. O cap efetivo após checkpoint foi **3.337630 CPU-h**, abaixo do teto inicial 5.45 ([state.json:1](C:/Projetos/refute/.cache/v053/stageB/d1-infeasibility/584a56d8f50283fe/state.json:1)). `ledger.lock` está ausente, consistente com sua liberação pelo [context manager:219](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:219).

**WEAKENED, com as quatro correções acima no registro de B0b.**