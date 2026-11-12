**As correções avançaram, mas ainda há três bloqueios.** Conferidos por leitura e simulações em memória, sem alterar arquivos ou executar shards.

1. **Outra falha mecânica ainda permite nova tentativa.** A guarda verifica apenas cobranças abertas ([i4_rest.py:122](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:122)). O driver pode fechar a cobrança e depois lançar uma exceção ([driver.py:535](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:535), [driver.py:544](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:544)). Nesse caso, nenhum STOP persistente é registrado e outro `run` alcança `execute` novamente, reproduzido em memória. **Registrar duravelmente o início e o encerramento da execução; uma interrupção sem encerramento reconhecido deve exigir nova decisão.** O `summarize` também deve sinalizar essa interrupção, mesmo se todos os sidecars já existirem.

2. **`_alive` pode liberar um lock sem comprovar que seu proprietário morreu.** Se `GetExitCodeProcess` falhar, retorna `False`, permitindo o rename ([i4_rest.py:249](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:249)). Reproduzido com falha simulada da consulta. **Tratar falha de consulta como vivo/indeterminado e recusar a liberação.** Declarar também os tipos Win64 de `OpenProcess`, `GetExitCodeProcess` e `CloseHandle`, como faz o driver. O rename preserva corretamente o arquivo quando a verificação é conclusiva.

3. **Um STOP diferente no MAIN é ignorado depois de haver histórico de reconciliação.** A validação de `pending` fica dentro de `if not reconciled` ([i4_rest.py:107](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:107)). Com reconciliação anterior e um novo `unresolved_stop`, o caminho de execução continua, reproduzido em memória. **Validar o stop pendente independentemente do histórico**, incluindo o stop do driver MAIN.

**Demais correções conferidas:**

- `finish` preserva seu STOP; o estado intermediário esperado permite concluir a reconciliação ([i4_rest.py:135](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:135)).
- A transferência salva débito, crédito e histórico juntos. A simulação manteve **49,9 CPU-h** e um único registro de transferência ([i4_rest.py:71](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:71)).
- O leitor agora verifica stops e gates dos dois lados, unicidade, pertinência das chaves e cardinalidade completa ([i4_rest.py:180](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:180)).
- Permanecem o esvaziamento às 19h30, a reutilização do cálculo congelado, a exclusão divulgada de 3129 e o limiar 23.

**WEAKENED, corrigir os três bloqueios antes de rodar.**

