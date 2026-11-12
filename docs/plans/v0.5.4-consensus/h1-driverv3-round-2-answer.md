## Pontos da rodada 1

**Resolvidos no código e na cobertura apresentada:**

- `stop.json` é recusado antes da reconciliação. A marca v3 continua bloqueando partes antigas. [budgeted_v3.py:70](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:70), [budgeted_v3.py:112](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:112)
- A cobrança permanece no consumo, no total e no hard cap do chamador. Gates, archive, guard e finish permanecem estruturalmente iguais. [budgeted_v3.py:104](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:104), [budgeted_v3.py:123](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:123)
- Os testes agora verificam a retomada parcial, o motivo exato da parada antiga, equivalência sem interrupção, limites e workers registrados encerrados. A interrupção é injetada; o `finally` ainda encerra normalmente o pool, portanto não testa a morte abrupta do controlador. [test_v054_budgeted_v3.py:98](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:98), [test_v054_budgeted_v3.py:130](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:130), [test_v054_budgeted_v3.py:219](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:219)

Confirmei **19 testes, zero falhas, erros ou ignorados** no [JUnit:1](C:/Projetos/refute/.cache/v054/tests/junit-driverv3-r2.xml:1). Não os reexecutei.

## Duas questões restantes

**1. Projeção maior não significa todos os stops mais conservadores.**

O piso dos sidecars e o CPU anterior à queda não reduzem a projeção. Porém, uma projeção maior também aumenta seu cap de consumo, `1,5 × projeção + crash`. [budgeted_v3.py:63](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:63), [budgeted_v3.py:124](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:124)

Exemplo em segundos: checkpoint de 3/60, batch interrompido com 5 rastreados, 1 committed, crash de 42 e outros dois shards de 1 cada:

| Resultado | Rodada 1 | Rodada 2 |
|---|---:|---:|
| Projeção | 60 | 140 |
| Cap após checkpoint | 136 | 252 |

Ambas as projeções passam a alocação dos testes. Assim, **o stop por consumo pode ocorrer mais tarde**, embora o hard cap externo permaneça intacto. Antes do checkpoint, retirar o excedente rastreado do componente `crash` pode diminuir o cap.

**Correção:** documentar e testar esse comportamento explicitamente. A nova medição é defensável, mas sua conservatividade não é uniforme.

**2. A exclusividade do registro tem uma corrida.**

Dois lançadores com o mesmo `--log` podem passar juntos por `record_path.exists()`. Depois, cada um grava e libera seu filho; `os.replace` permite ao segundo sobrescrever a identidade do primeiro, deixando dois trabalhos com um único registro e logs compartilhados. [launch_detached.py:185](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:185), [launch_detached.py:161](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:161)

**Correção:** adquirir uma reserva exclusiva do prefixo antes de abrir logs ou criar o filho. Acrescentar teste de concorrência e testes das falhas de criação, registro e retomada. Os testes atuais verificam helpers, não essa sequência. [test_v054_launch_detached.py:38](C:/Projetos/refute/tests/test_v054_launch_detached.py:38)

## Sequência suspensa e sonda

**Para uma chamada isolada, a sequência está correta:** criação suspensa, criação válida, registro persistido, retomada com retorno anterior igual a 1 e encerramento pelo handle em falhas. Os protótipos estão completos. Isso corresponde à semântica de [ResumeThread](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-resumethread). [launch_detached.py:115](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:115), [launch_detached.py:199](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:199)

A sonda planejada deve também:

- Registrar os horários efetivos de fechamento e reabertura do app.
- Definir previamente a tolerância entre heartbeats UTC; sequência contínua sozinha não detecta uma pausa longa.
- Validar máscara `0xFFFFFF00` e prioridade esperada. Sem executar o driver, a sonda precisa aplicar BelowNormal explicitamente para verificar essa condição.

A sobrevivência ao reinício continua não demonstrada. Nenhum processo foi iniciado nesta revisão; o lançador oficial permanece inalterado.

**WEAKENED, corrigir a exclusividade do registro e documentar/testar o aumento possível do cap após o checkpoint.**