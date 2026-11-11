**A correção atende ao solicitado. Não encontrei bloqueio para os smokes T2a e acima de 20 setores.**

- [b1_forecast.py:336](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:336): somente o overrun de shard da parte `above20` recebe o tratamento especial. As demais paradas continuam gerando `SystemExit`.
- [b1_forecast.py:351](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:351): o relatório lê diretamente os arquivos do driver, registra a parada, o tempo desde o despacho e os tempos próprios do registro. Mantém `c_above_20_runs=false` e C acima de 20 desconhecido.
- Esse caminho não chama `budgeted.assembled`, não reconcilia nem remove o stop do ledger. Permite encerrar o diagnóstico e seguir para B1.2 conforme a decisão registrada.

**Verificação:** passaram 21 testes via pytest e o novo teste de relatório, executado com arquivos simulados em memória. Também conferi seis cenários de encaminhamento, incluindo overrun, cap, pausa e conclusão normal.

Nenhum arquivo foi modificado, nenhum smoke foi executado e não houve interferência no D2.

**SURVIVED.**