Duas correções no stop report, sem alterar o outcome C:

1. **Arredondamento incorreto:** [README.md:68](C:/Projetos/refute/docs/validation/v0.5.3/stageB/README.md:68) deve informar **0.217**, não 0.218, para EB1 folded. O valor é `0.21746588456109694`, confirmado pelos registros e por [d1-bound.json:41](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1-bound.json:41).

2. **Hipótese de seleção resumida incorretamente:** [README.md:44](C:/Projetos/refute/docs/validation/v0.5.3/stageB/README.md:44) deve preservar a condição de que **a seleção não altere o ruído na direção da diferença binária–planeta**. Dizer apenas que ela atua sobre o box SNR não basta. Explicitar também que o null estelar é a caixa completa de **±3σ**, conforme [design:102](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:102). São hipóteses não demonstradas.

O restante confere:

- **Números:** contagens, projeções, allowances, expectativas, probabilidades e distâncias coincidem nos arredondamentos apresentados. O ledger totaliza **2.463690104 CPU-h**, corretamente apresentado como 2.464 em [README.md:105](C:/Projetos/refute/docs/validation/v0.5.3/stageB/README.md:105).
- **Decisão:** C segue exatamente [d1_bound.py:285](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:285) e [design:143](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:143). A leitura em [README.md:78](C:/Projetos/refute/docs/validation/v0.5.3/stageB/README.md:78) é fiel: sem rota, sem draft de inviabilidade, sem solução alegada; INCONCLUSIVE permanece sem decisão.
- **Execução:** verificados 80 shards, 800 sementes exatas, sem duplicatas, hashes inconsistentes, ERROR ou distâncias não finitas. As cinco falhas de geração permanecem no denominador. Reproduzi o fingerprint `cc407aecdd294028`; seus arquivos coincidem com `b00a78d`. Os registros são compatíveis com desenvolvimento apenas, sem alterações em `src/` ou execução de confirmação.
- **Caps:** não atingidos nas etapas registradas. [README.md:106](C:/Projetos/refute/docs/validation/v0.5.3/stageB/README.md:106) ainda precisa receber o consumo desta revisão antes do encaminhamento final.

**WEAKENED, com as duas correções acima.**

