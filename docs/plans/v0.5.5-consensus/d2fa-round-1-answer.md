**Rodada 1/3: NÃO LIBERADO.** Identifiquei um bloqueio no fechamento contábil do resumo.

Revisei `main`, HEAD `9f6ec54b354e7245f5f2bc457edce4cde5c80a96`, somente por leitura local. Não usei rede, executei scripts ou testes, alterei arquivos ou acessei o caminho proibido. Os **14 testes aprovados são informação sua**, não resultado reproduzido neste parecer.

**Vereditos por item**

1. **SURVIVED, repetição do executor e identidade operacional.**

   A solução é aceitável neste escopo. A guarda realmente ignora `__main__` e `__mp_main__`; `driver.py` integra a lista congelada da D2-F; o adaptador chama `lv.bind()` depois dos imports.

   A identidade operacional é persistida antes do despacho e comparada na retomada. No resumo, a identidade científica e o SHA do adaptador são conferidos. **A guarda passar não prova segurança geral nem fechamento completo das dependências**, limitação já declarada em `r1_common.py:65`. O `check` informado não foi reproduzido.

2. **REFUTED quanto à equivalência integral das proteções, por faltar uma barreira de publicação após a cobrança do wrapper.**

   As proteções seguintes **sobrevivem à leitura**:

   - **Teto protegido:** fórmula compatível com reserva de crash e margem nominal de polling, `d2f_fixed_cap.py:110`.
   - **Teto efetivo e margem:** calculados sob o lock, registrados e conferidos antes de `record_start`, linhas 354 a 358.
   - **`expected_cap`:** comparação anterior à criação do driver, linha 265.
   - **Conclusão contabilizada:** marcador posterior a `budgeted.finish`, linha 296.
   - **`check_completed`:** exige conclusão, identidades, cobranças fechadas e igualdade entre ledger e driver, linha 307.
   - **Recibo interno:** exige uma cobrança nova única e vincula tentativa, SHA do registro e identidade, linha 406.
   - **Wrapper:** cobrança em `finally`, sob o lock, descontando somente cobranças internas novas, linha 492.

   **O bloqueio está na sequência:** o recibo é salvo na linha 488, mas o wrapper só é cobrado na linha 503. Se essa cobrança falhar antes de persistir, ficam `d2f-A.json` e um recibo que **`check_receipt()` aceita**, porque essa função não verifica a cobrança do wrapper. Além disso, ela só é chamada pelos testes, não pelo fluxo operacional.

   Isso difere do executor aprovado, cuja publicação final ocorre depois do `finally`, em `r1_fixed_cap.py:663`.

   **Emitir recibo para um registro com STOP científico é correto**, preservando os fatos e propagando o STOP. Esse recibo precisa continuar distinguível de um fechamento operacional completo.

   Não identifiquei erro aritmético que autorize exceder **16,3 CPU-h no modelo nominal adotado**. Isso não demonstra um limite físico absoluto do watchdog.

3. **SURVIVED, exclusivamente como estimativa de planejamento.**

   A base de **10,4 CPU-h** está explicitamente identificada como não medida de forma auditável. A aritmética confere:

   - Margem exigida: **13,52 CPU-h**.
   - Teto protegido para 16,3, quatro workers e 1.200 s: **13,585354 CPU-h**.
   - Alocação mínima pelo mesmo cálculo: **16,228111 CPU-h**.

   É aceitável para a decisão autorizada. **Não comprova que os 200 planetas terminarão dentro do teto**, nem justifica aumentá-lo automaticamente.

4. **WEAKENED, financiamento correto no fluxo atual, com ressalvas de recuperação e documentação.**

   Sob o lock, `fund()` confere futilidade, ausência de execução/início, alocações iniciais, reserva e linha de 64 CPU-h. A transferência e a repetição normal estão corretas.

   Há duas ressalvas:

   - Alocações e registro da transferência são persistidos em **duas gravações**, linhas 218 e 230. Uma interrupção entre elas deixa estado parcial; a próxima chamada recusa continuar. É conservador, mas exige reconciliação.
   - A afirmação de que `lv.declare()` só é chamado por `guarded_run` é incorreta: também há chamadas diretas em `i4_diagnosis.py:150`, `pilot_costs.py:84`, `t2ae_geometry.py:97` e na entrada CLI de `ledger_v055.py:531`.

   **Não encontrei essas chamadas no caminho restante dos executores fixos revisados.**

5. **SURVIVED, futilidade e conjunto B.**

   O adaptador fixa `SET = "A"` e chama o resumo congelado. A regra permanece em `d2f_floor.py:681`. Se A não for fútil, a linha 509 interrompe com pedido estimado de **16,3 CPU-h adicionais**. Nenhum caminho do adaptador despacha B.

   Essa cifra continua sendo planejamento, sujeito à autorização posterior.

6. **WEAKENED, testes úteis, mas insuficientes para o bloqueio identificado.**

   Os 14 testes cobrem financiamento, margem efetiva, teto, retomada, mudança do adaptador, recibos, STOP após gravação e cobrança do wrapper após exceção.

   **Falta testar a falha da cobrança do wrapper depois de persistido o recibo**, verificando a recusa pela entrada operacional de aceitação do resultado. Os testes atuais chamam diretamente `check_receipt()` e não expõem essa lacuna.

**Correções que bloqueiam o despacho**

1. Em [d2f_fixed_cap.py:487](C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:487), abrangendo a cobrança da linha 503 e a validação da linha 431.

   **Texto proposto:** “Preservar `d2f-A.json` e o recibo interno como evidência. Persistir um fechamento operacional separado somente após a cobrança bem-sucedida do wrapper, vinculando SHA do registro, tentativa, identidade, recibo e cobrança do wrapper. Registrar explicitamente o estado do resumo. A aceitação operacional exige esse fechamento; sua ausência ou inconsistência causa STOP. Um STOP científico permanece registrado e propagado, sem publicação de sucesso.”

   Incorporar essa validação ao fluxo operacional, mantendo `d2f_floor.py` e os arquivos congelados intactos.

2. Em [test_d2f_fixed_cap.py:270](C:/Projetos/refute/tests/v055/test_d2f_fixed_cap.py:270), junto dos cenários das linhas 296 e 322.

   **Texto proposto:** “Após salvar registro, cobrança interna e recibo, provocar falha na cobrança do wrapper antes da persistência. Exigir STOP, ausência de fechamento operacional válido e recusa pela entrada operacional de validação. No caminho normal, exigir vínculo com a cobrança exata do wrapper. No STOP científico após gravação, preservar evidências e propagar o STOP, sem marcar sucesso.”

**Ressalvas e melhorias sem bloquear**

3. Em [d2f_fixed_cap.py:187](C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:187).

   **Texto proposto:** “Após o financiamento, não executar `lv.declare()`, sua CLI ou os scripts antigos que o chamam. Interrupção entre a atualização das alocações e o registro da transferência exige reconciliação documentada; não restaurar automaticamente a tabela antiga.”

4. Em [test_d2f_fixed_cap.py:226](C:/Projetos/refute/tests/v055/test_d2f_fixed_cap.py:226).

   **Texto proposto:** “Conferir explicitamente que o batch aberto foi fechado por reconciliação e recebeu exatamente a cobrança adicional de crash, preservando o consumo anterior.” O teste atual verifica retomada e teto, mas não essa cobrança numericamente.

**Conclusão da rodada:** o adaptador está **NÃO LIBERADO para o conjunto A** até resolver o fechamento operacional e sua regressão sintética. Este parecer registra a pendência; não houve alteração no repositório.

SHA-256 do arquivo revisado, conferido novamente ao fim:

`6d47e4d433f4034e8ec64af2a30c9ee59560092963b1341a10a7a901ff119715`