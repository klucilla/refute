**Rodada 2/3: as correções atendem ao parecer anterior. Não identifiquei bloqueio remanescente.**

Confirmei `ab5e7e7` em `main` e o SHA informado. O commit intermediário `549c198` contém apenas os quatro registros da T2a-E, sem tocar o adaptador. Revisão somente por leitura local, sem rede, execução de scripts, testes ou alterações. Não acessei o caminho proibido. Os **16 testes aprovados são informação sua**, não resultado reproduzido neste parecer.

**Vereditos por item**

1. **SURVIVED, fechamento operacional.**

   Em [d2f_fixed_cap.py:523](C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:523), a cobrança do wrapper precisa retornar sem erro antes de alcançar a criação exclusiva do fechamento, na linha 548. Uma falha nessa cobrança impede o fechamento, mesmo com registro científico e recibo interno já persistidos.

   [check_closed:559](C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:559) exige os vínculos com registro, recibo validado, tentativa, identidade, adaptador e cobrança do wrapper. Exige também estado `final`. O comando `accept` passa por essa validação.

   **O STOP científico permanece distinto:** gera fechamento `stopped`, é propagado e não passa como sucesso. O STOP financeiro para B ocorre depois do fechamento válido de A, sem autorizar B. Isso atende ao texto da rodada 1.

2. **SURVIVED, testes dos bloqueios anteriores.**

   A leitura confirma cobertura suficiente para as regressões solicitadas:

   - Caminho normal, vínculo com nome e horas da cobrança do wrapper e passagem por `accept`, [test_d2f_fixed_cap.py:286](C:/Projetos/refute/tests/v055/test_d2f_fixed_cap.py:286).
   - Falha do wrapper após o recibo, ausência de fechamento, recusa por `check_closed` e `accept`, e ausência de reparo automático, linha 312.
   - Cobrança inconsistente no fechamento, linha 339.
   - STOP científico preservado e recusado como sucesso, linha 359.

   São verificações sintéticas do fluxo e da contabilidade. Não demonstram um limite físico absoluto do watchdog.

3. **SURVIVED, financiamento atômico e ressalva documentada.**

   Em [d2f_fixed_cap.py:233](C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:233), as três alocações são atualizadas no mesmo objeto que recebe o registro da transferência. Há uma única chamada a `budgeted.save`, na linha 245, vinculada à gravação atômica de `ledger_v055`.

   As verificações anteriores permanecem, incluindo o limite de `budgeted.declare`. Não há arquivamento indevido de SOURCE ou PART, pois ambas precisam satisfazer `_never_ran`. A reserva permanece uma parte não despachável pelo desenho.

   A docstring agora identifica corretamente as chamadas antigas a `lv.declare()` e a reconciliação pelo mantenedor.

4. **SURVIVED, cobrança de crash na retomada.**

   Em [test_d2f_fixed_cap.py:252](C:/Projetos/refute/tests/v055/test_d2f_fixed_cap.py:252), o teste exige batch fechado, marcador de reconciliação e cobrança de **44 segundos**: os 2 segundos anteriores mais `2 × (1 + 20)`. Isso atende à ressalva anterior.

5. **SURVIVED, ausência de bloqueio adicional identificado.**

   O diff preserva as proteções de teto, margem efetiva, identidade, retomada e conclusão já examinadas. Não altera o desenho congelado nem acrescenta despacho de B.

**Correções que bloqueiam o despacho**

**Nenhuma identificada nesta rodada.**

**Ressalva opcional, sem bloquear**

1. Em [test_d2f_fixed_cap.py:312](C:/Projetos/refute/tests/v055/test_d2f_fixed_cap.py:312), acrescentar o segundo modo de falha de `lv.charge`.

   **Texto proposto:** “Simular cobrança do wrapper persistida seguida de STOP por ultrapassar a sala das cobranças; exigir ausência de fechamento e recusa por `accept`.” O código já impede alcançar o fechamento nesse caminho; falta apenas essa regressão explícita.

**Adaptador LIBERADO para o conjunto A**, nos bytes revisados, com alocação de **16,3 CPU-h**, **4 workers**, limite de **1.200 s por shard** e sujeito às guardas existentes.

**A parada na G1 permanece: a D2-F não será despachada nesta sessão.** A liberação do código fica disponível para a decisão posterior do mantenedor. Preserve os bytes do adaptador após o primeiro despacho.

SHA-256 revisado:

`7b980a25685df9f4b0e632b61786a598db061acda289d4f653670cbd342cd374`