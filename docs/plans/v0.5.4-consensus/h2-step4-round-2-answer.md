As correções de stops e do controle de 5% estão aplicadas. **A proteção contábil do resumo ainda está incompleta.**

**Confirmado**

- `summarize` verifica os caps com `in_h1=False` antes de ler os resultados ([script:171](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:171)).
- Erros e falhas no controle de 5% produzem relatório sem agregados, com todos os resultados `INCONCLUSIVE (a stop)`, antes da saída ([script:190](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:190)).
- O controle exige ambas as distâncias finitas, positivas e dentro da tolerância relativa; inválidos entram em `differ_or_invalid` ([script:195](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:195), [script:279](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:279)).
- Distância não finita nos novos cenários força todos os resultados a `INCONCLUSIVE`. A ressalva sobre reamostragem também consta no JSON ([script:225](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:225), [script:253](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:253), [script:281](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:281)).

**Restam duas correções**

1. **Reservar CPU e concluir a cobrança antes de publicar um resultado favorável.** `check_caps` verifica tokens, dias e disco, mas não a disponibilidade da reserva de cobranças. O B0 verifica essa disponibilidade explicitamente ([B0:296](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:296)). Aqui, `_write` ocorre antes do `finally`; se a cobrança ultrapassar os 0,1 CPU-h disponíveis, o processo termina com STOP, mas pode deixar um JSON indicando margem ([script:265](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:265), [ledger_i:220](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:220)). **Verificar a reserva antes do bootstrap e publicar a conclusão somente após a cobrança bem-sucedida.**

2. **Identificar cada cobrança do resumo separadamente.** O nome fixo `h2_step4_summarize` colide na segunda invocação. Ela pode executar e sobrescrever o relatório antes de falhar com `already charged`, deixando sua CPU sem contabilização ([script:178](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:178), [budgeted:96](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:96)). Usar identificador único por invocação, como no B0.

Há ainda um **ajuste de redação**: o [plano:85](C:/Projetos/refute/docs/plans/v0.5.4-h2-step4-b0-errors.md:85) promete nenhum agregado sob qualquer stop, mas a detecção tardia de distância não finita permite agregados parciais. Prevalidar todas as distâncias ou explicitar essa exceção no plano. Os resultados finais já ficam inconclusivos nesse caso.

O oráculo, a leitura pelo fingerprint registrado e os limites das conclusões permanecem preservados. Nenhum cálculo foi executado nesta revisão.

WEAKENED (reservar CPU, cobrar antes da publicação, individualizar cobranças e alinhar a redação dos stops).