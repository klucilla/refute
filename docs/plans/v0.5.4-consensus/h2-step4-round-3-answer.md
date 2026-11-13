**As correções principais estão aplicadas. Resta uma fragilidade na unicidade da cobrança.** O HEAD atual é `d2e4da3`; as dependências revisadas não diferem de `f34bb39`.

- **Reserva e publicação:** os caps e os 0,03 CPU-h são verificados antes da leitura. `_summarize` retorna sem gravar; a cobrança ocorre no `finally`, antes de `_write`. Uma cobrança que falha impede a criação de um novo relatório ([script:176](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:176)).
- **Stops:** erros, controle de 5% e distâncias inválidas são verificados antes dos agregados. Havendo qualquer stop registrado, o retorno contém famílias vazias e todos os resultados `INCONCLUSIVE (a stop)` ([script:206](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:206), [script:226](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:226)).
- **Interpretação:** permanecem a ressalva sobre reamostragem e a restrição às hipóteses por planeta do B0, sem conclusão geral sobre D1 ([script:285](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:285)).

**Correção final, conservadora:** o timestamp tem resolução de um segundo, portanto não garante nome único por invocação ([script:182](C:/Projetos/refute/docs/validation/v0.5.4/step4_b0_errors.py:182)). Duas invocações iniciadas no mesmo segundo podem colidir; `budgeted.charge` recusa a segunda cobrança, deixando sua CPU sem contabilização ([budgeted:101](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:101)). **Acrescentar um UUID ao timestamp**, preservando a ordem atual de cobrança antes da gravação, resolve essa fragilidade sem alterar o cálculo científico.

Não identifiquei outra correção material nesta leitura. O oráculo, o fingerprint histórico, os critérios congelados e as proteções da execução principal permanecem preservados. O controle empírico de 5% continua pendente da execução autorizada.

WEAKENED (acrescentar UUID ao identificador de cada cobrança do resumo).