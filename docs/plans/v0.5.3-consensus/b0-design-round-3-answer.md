**Os quatro ajustes estão aplicados e corretos.**

1. **Cobranças:** `charge` registra o consumo antes do STOP; `charges_left()` calcula o saldo corretamente. Confirmado em memória: [ledger_b.py:143](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:143).

2. **Sumarização:** verifica caps e reserva de 0,03 CPU-h antes de começar; cobra no `finally`, inclusive quando `_summarize` falha. Ambos os caminhos foram verificados sem executar a sumarização real: [d1_bound.py:296](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:296).

3. **Transferências:** `declare` preserva as alocações persistidas quando existe transferência registrada. O caso que antes restaurava 4 manteve 5 CPU-h no check em memória: [ledger_b.py:94](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:94).

4. **Desenho:** a ressalva sobre SNR e profundidade foi corrigida; as regras de cobrança correspondem ao código: [design:52](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:52), [design:175](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:175).

**Nenhum bloqueio restante identificado para executar o diagnóstico**, preservadas as limitações estatísticas declaradas e o compromisso prévio do desenho e scripts: [design:198](C:/Projetos/refute/docs/plans/v0.5.3-stageB0-design.md:198). Nenhum arquivo foi alterado e nenhuma medição foi executada nesta revisão.

SURVIVED (run as is)