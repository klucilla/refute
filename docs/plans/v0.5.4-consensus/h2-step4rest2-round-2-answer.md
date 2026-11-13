**As correções resolvem boa parte da rodada 1, mas restam a contabilização da exceção e uma ressalva sobre a garantia absoluta do teto.** Revisão somente estática, sem rede ou alterações.

1. **Correções da rodada 1.** Um worker reduz corretamente a reserva de crash para **0,338889 CPU-h**. A projeção predefinida elimina o checkpoint; o stop anterior agora precisa coincidir exatamente nos dois registros. A exceção passa a bloquear a parte. [step4_rest2.py:69](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:69), [step4_rest2.py:92](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:92), [step4_rest2.py:129](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:129).

   **Ainda falta atualizar `spent_hours` na exceção.** `_record_exception()` grava somente `unresolved_stop`. Se `run.execute()` propagar uma exceção após consumir CPU, `budgeted_v3` não chega à contabilização final. O ledger conserva o valor anterior ao batch. Corrigir o handler para registrar também o consumo de `spent_seconds()`, incluindo eventual batch aberto, sem executar trabalho novamente. [step4_rest2.py:105](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:105), [budgeted_v3.py:171](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:171). O procedimento manual após morte externa também precisa registrar **consumo e stop**.

2. **Mesmo código, linhas e fingerprint: sim, para o cálculo científico.** O wrapper muda o paralelismo, mantendo `s4.shard`, argumentos, sementes, fingerprint e limite por shard. `workers` é metadado do sidecar e parâmetro de contabilização; `_done()` verifica fingerprint, argumento e conteúdo, sem exigir igualdade de workers. O resumo científico não usa esse campo. [step4_rest2.py:160](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:160), [driver.py:335](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:335), [driver.py:363](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:363).

3. **Conta do teto: conservadora sob uma latência limitada, sem prova de pior caso absoluto.**

   | Componente | CPU-h |
   |---|---:|
   | Cap do driver | 0,550926 |
   | Gatilho nominal, `cap × 1,10` | 0,606019 |
   | Uma cobrança por crash | 0,338889 |
   | Soma antes da latência adicional | **0,944907** |
   | Folga restante | **0,055093 = 198,33 CPU-s** |

   Portanto, cabe enquanto a contabilização adicional após o gatilho permanecer nessa folga. Entretanto, `wait(0.5)` não estabelece prazo máximo de reação; há consultas e escrita atômica antes do `kill()`, além da contabilização final após o encerramento. `MARGIN=1.2` fornece margem operacional, não demonstra esse limite temporal. [driver.py:485](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:485), [driver.py:529](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:529).

   **Correção:** explicitar essa premissa e conferir o consumo final contra `FIXED_CAP` após o run e antes do resumo. `check_caps()` não faz essa comparação. A CPU do resumo continua cobrada separadamente na reserva da fase. [step4_rest2.py:168](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:168), [step4_b0_errors.py:188](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:188).

4. **Mais um ajuste de ordem:** a recusa por `hard_cap` insuficiente ocorre depois da reconciliação, fechamento e transferência. Ela pode deixar uma parte criada, sem execução, que a próxima chamada recusará. Antecipar essa verificação à transição. [step4_rest2.py:145](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:145).

Confirmei os 62 sidecars: **4.683,656 CPU-s**, média **75,543**, intervalo **1,75–410,797**. Sustentam a estimativa de custo, sem estabelecer o pior caso.

WEAKENED (corrigir consumo nas exceções, conferir o teto final, explicitar a premissa de latência e antecipar a recusa por hard_cap)