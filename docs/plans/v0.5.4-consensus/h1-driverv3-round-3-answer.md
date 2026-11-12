## Correções da rodada 2

**Resolvidas.**

- O aumento possível do cap está documentado e testado, incluindo os caps antes e depois do checkpoint. A cobrança continua no consumo, no hard cap externo e no total. [budgeted_v3.py:31](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:31), [test_v054_budgeted_v3.py:268](C:/Projetos/refute/tests/test_v054_budgeted_v3.py:268)
- A reserva com `O_EXCL`, anterior aos logs e ao processo, elimina a corrida identificada. Os testes cobrem concorrência, registro antes da retomada e encerramento nas falhas. [launch_detached.py:174](C:/Projetos/refute/docs/validation/v0.5.4/launch_detached.py:174), [test_v054_launch_detached.py:87](C:/Projetos/refute/tests/test_v054_launch_detached.py:87), [test_v054_launch_detached.py:136](C:/Projetos/refute/tests/test_v054_launch_detached.py:136)

Confirmei **28 testes, zero falhas, erros ou ignorados** no [JUnit:1](C:/Projetos/refute/.cache/v054/tests/junit-driverv3-r3.xml:1). Não reexecutei testes nem ruff.

**Precisão documental:** se “132 s” compara com a implementação da rodada 1, deve ser **136 s**: `1,5 × 60 + (49 − 3)`. Os 132 s correspondem à comparação mantendo apenas o crash puro de 42 s. Isso não altera o código atual.

## Pendências para decidir o reinício

**1. Criação não comprova que o processo está vivo.**

`state()` considera vivo qualquer PID cuja criação ainda possa ser consultada; uma falha de consulta vira “ended”. Um processo encerrado pode continuar tendo objeto consultável enquanto existirem handles abertos. [restart_check.py:31](C:/Projetos/refute/.cache/v054/tools/restart_check.py:31), [Microsoft](https://learn.microsoft.com/en-us/windows/win32/procthread/terminating-a-process)

**Opção conservadora:** verificar criação **e estado de término**, preferencialmente com espera de timeout zero no handle. Falhas de consulta devem produzir **desconhecido**, impedindo aprovação. Aplicar isso também à observação dos processos do app. [restart_probe.py:104](C:/Projetos/refute/.cache/v054/tools/restart_probe.py:104)

**2. O checker ainda não verifica todo o protocolo.**

Ele confere sequência e maior intervalo UTC, mas não duração de 60 minutos, reinício efetivo, reabertura ou observações persistidas antes/depois. `watch.json` ausente é aceito como observação vazia. [restart_probe.py:97](C:/Projetos/refute/.cache/v054/tools/restart_probe.py:97), [restart_check.py:37](C:/Projetos/refute/.cache/v054/tools/restart_check.py:37)

**Opção conservadora, sem outra rodada:** usar o checker como relatório parcial e exigir, no registro final em `.cache`:

- Critérios e watch persistidos antes do lançamento, com processos observados inicialmente vivos.
- Relatórios pré e pós com ambos os processos da sonda vivos, mesmas identidades.
- Saída do app e criação da nova instância dentro da janela observada.
- Duração e cadência previstas, intervalos positivos até 30 s, conferindo também `mono`, já coletado.
- Linha final e término confirmado dos dois processos.

BelowNormal explícito, afinidade e parentesco estão contemplados. **Driver e lançador passaram pelos pontos levantados; a sobrevivência real continua pendente do experimento.** Até sua aprovação, permanece `launch_affinity.ps1`.

**WEAKENED, corrigir a verificação de vida e completar a conferência registrada do protocolo de reinício.**