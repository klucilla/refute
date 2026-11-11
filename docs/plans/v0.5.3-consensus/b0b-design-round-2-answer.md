As duas correções estão corretas para a execução autorizada de B0b. Não encontrei novo bloqueador.

- **P1 resolvido:** [ledger_b.py:93](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:93) cria o lock exclusivamente, permite reentrada no processo e recusa outro proprietário. Um lock deixado por crash é reportado e preservado. O contexto em [d1_infeasibility.py:219](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:219) cobre smoke, execução e resumo inteiros, incluindo **todos os saves internos de `budgeted.execute`**. Declarações, transferências e charges usam esse lock; `check_caps` usa o lock separado.

- **P2 resolvido:** [ledger_b.py:119](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:119) soma consumo atual e tentativas arquivadas; [ledger_b.py:233](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:233) desconta ambos antes de dividir por 1,10. A recusa de identidade diferente ou tentativa arquivada ocorre antes de `execute` ([script:123](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:123)). A retomada idêntica mantém a dupla contagem conservadora declarada.

- **Cobertura:** nos caminhos futuros de B0b e nos comandos públicos do ledger, não encontrei escritor escapando do lock. `d1_bound.run` permanece histórico, fora das execuções autorizadas. **Não há scripts ou design de B1 neste checkout**, portanto sua futura adesão ao lock ainda precisa ser conferida antes da execução.

- **Sem regressão identificada:** critério, seeds, oracle, resumo, desfechos e fingerprint permanecem coerentes. A seção 4 registra as correções ([design:100](C:/Projetos/refute/docs/plans/v0.5.3-stageB0b-design.md:100)). Checks isolados em memória passaram para reentrada, exclusão, lock abandonado, tetos acumulados e recusa de identidades. Nenhum arquivo foi alterado ou workload pesado executado.

**SURVIVED, desenho e script de B0b prontos para commit e execução.**