**A separação está correta, mas falta concluir o tratamento do overrun acima de 20 setores.**

1. **[P1] O overrun não produz o relatório previsto.** Em [b1_forecast.py:336](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:336), qualquer estado diferente de `complete` causa `SystemExit` antes de `validate_smoke`. Portanto, nessa situação não são escritos `b1-smoke-above20.json`, `c_above_20_runs=false` nem o resultado explícito de C como desconhecido.

   **O que fica registrado:** quando o shard termina acima do limite, o driver grava primeiro o resultado bruto, incluindo `wall_seconds`, e depois registra `shard_over_limit` com o tempo desde o despacho, além de `stop.json`, `state.json` e o stop no ledger. Isso aparece em [driver.py:523](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:523). O limite de 1.700 s é constatado após o retorno, não interrompe o shard exatamente nesse instante.

   **Correção conservadora:** criar uma saída diagnóstica específica para esse overrun, preservando o stop, registrando os dois tempos e mantendo C acima de 20 desconhecido. Não usar `budgeted.assembled`, que recusa partes paradas, nem reconciliar a parada para obter um PASS. B1.2 pode seguir como parte separada, conforme a decisão e seu procedimento registrado. Outros tipos de parada continuam sujeitos às regras próprias.

**Demais pontos conferidos:**

- [b1_forecast.py:164](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:164): `only_c=True` sempre entra no ramo que define `v5c`; B não é calculado. Confirmei com chamadas simuladas, incluindo restauração da constante e dos patches.
- Partes, alocações, fingerprints e identidades são distintos. O stop antigo de `b1_smoke` permanece intacto.
- [b1_forecast.py:305](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:305): seleção determinística por quantidade de arquivos, desempate pela chave e menor slot. Confirmei **TIC-229943561, 42 arquivos, slot 0**.
- O validador exige compatibilidade para `t2a_c`, verifica somente C e relata os seis contadores. O caminho completo grava corretamente a comparação com 1.200 s.
- **21 testes passaram novamente**, com sockets bloqueados. Falta teste do caminho de overrun descrito acima.
- O diff funcional permanece no escopo autorizado. `battery_b1.py` e os helpers antigos estão inalterados.

Nenhum arquivo foi modificado e nenhum smoke foi executado.

**WEAKENED (com a correção do relatório de overrun antes dos três smokes).**