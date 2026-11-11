**Não encontrei bloqueio para o smoke previsto de dois shards.**

- [b1_forecast.py:326](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:326): o validador agora confere quantidade, ordem, identidade, status, compatibilidade e ativação completa. Contadores ausentes ou inválidos são rejeitados.
- [b1_forecast.py:355](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:355): a exigência de E2 respeita a recusa estrutural, exigindo zero quando recusado. O novo contador em [battery_b1.py:441](C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:441) comprova a entrada no wrapper de sinusoid mesmo quando o cálculo residual não é alcançado.
- [b1_forecast.py:374](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:374): a ativação esperada inclui configuração e hashes, com restauração de v4. As correções anteriores de bytes, fingerprint e disco permanecem presentes.

**Verificação:** os 20 testes passaram novamente, com sockets bloqueados. Mais sete casos de rejeição em memória passaram, incluindo ordem trocada, duplicação, slot incorreto, compatibilidade ausente e alterações isoladas de configuração ou hash. Também confirmei a restauração de v4, a ausência de mutação dos registros e o caso C=A até quatro setores.

Nenhum arquivo foi modificado e nenhum smoke foi executado. Não há correção pendente que exija desempate conservador para este smoke.

**SURVIVED.**