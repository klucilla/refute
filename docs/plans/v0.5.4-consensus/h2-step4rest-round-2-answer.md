**As três correções estão corretas. Não encontrei novos problemas no diff.**

- **Transferência e fechamento:** [step4_rest.py:83](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:83) faz débito, crédito, histórico e verificação da linha em um único save, sem `declare` ou arquivamento. A simulação confirmou transferência de **1.691705 CPU-h**, preservação da identidade e do consumo, projeção da origem igual ao consumo e ausência da dupla contagem anterior.

- **Fingerprint e verificações:** [step4_rest.py:102](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:102) vincula o fingerprint esperado ao `state.json` e à quantidade de shards, tanto em `run` quanto em `summarize`. Permanecem as recusas por parada diferente, workers ativos, batch aberto ou REST existente. O resumo agora recusa linha ausente, stop no ledger, stop no driver e gate bloqueante para ambas as partes ([linha 163](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:163)).

- **Resumo e patches:** [step4_rest.py:184](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:184) intercepta somente a leitura de step 4 com fingerprint e linhas esperados; B0 passa pelo leitor original. A união verifica sidecars via `_done`, recusa duplicatas e ausências e mantém a ordem dos 77 shards. O consumo soma ambas as partes. A restauração dos patches funciona no sucesso e nas exceções ([linha 196](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:196)).

- **Execução e limite da autorização:** código, schedule, fingerprint e units continuam os de step 4. Permanecem `budgeted_v3`, hard cap, drain e caps com `in_h1=False` ([linha 142](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest.py:142)). Outra parada retorna ao mantenedor; REST existente impede nova execução.

Verificação por leitura e simulações isoladas em memória, sem executar o trabalho operacional nem alterar arquivos. Os dois scripts de referência continuam iguais ao HEAD `50810db`. A postagem prévia na #217 permanece não verificada nesta revisão sem rede.

SURVIVED