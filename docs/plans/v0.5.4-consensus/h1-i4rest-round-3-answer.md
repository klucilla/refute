**As três correções estão corretas. Não identifiquei novo bloqueio.** Conferência por leitura e simulações em memória, sem executar shards ou alterar arquivos.

- **Tentativas duráveis:** `start` é gravado com `flush` e `fsync` antes de `execute`; `end` só ocorre após retorno normal. Uma tentativa aberta bloqueia `run` antes das mutações operacionais e gera recusa em `summarize`, inclusive com 290 registros verificados. Confirmado em simulação ([i4_rest.py:97](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:97), [i4_rest.py:152](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:152), [i4_rest.py:191](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:191), [i4_rest.py:229](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:229)).

- **Consulta do PID:** tipos Win64 declarados corretamente. Erro 87 permite considerar o PID inexistente; acesso negado, outros erros de abertura e falha na consulta conservam o lock. Processo vivo também conserva; processo comprovadamente encerrado permite o rename. Casos confirmados em simulação ([i4_rest.py:286](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:286)).

- **Stops do MAIN:** agora são verificados independentemente do histórico. Somente o stop intermediário exato, ainda não reconciliado, pode prosseguir; um stop do driver também recusa a execução ([i4_rest.py:142](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:142)).

**Opção conservadora:** uma queda após `start`, mesmo antes do primeiro despacho, ou antes de persistir `end`, exige STOP e retorno ao mantenedor. Não completar o diário manualmente nem repetir a execução.

SHA-256 revisado: `b0f1388b9c9eb48cc865e94f57992e95baa17bfac52da57464d3181dbcc7f3c3`.

**SURVIVED**

