**Rodada 1/3 de g1r: as três pendências foram atendidas. Não identifiquei bloqueio adicional no executor revisado.**

Revisei `09e729b`, confirmado em `main`, por leitura local. Sem rede, execução de scripts, testes ou alterações. Não acessei o caminho proibido. Os **53/53 testes aprovados são informação sua**, não resultado reproduzido neste parecer.

**Vereditos por item**

1. **SURVIVED, comprovante de fechamento.**  
   [r1_fixed_cap.py:496](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:496) persiste a tentativa e os nomes anteriores antes do resumo. `_write_receipt` exige exatamente uma cobrança nova; `_check_receipt` verifica SHA do resumo, tentativa persistida, nome e horas da cobrança, exclusão da lista anterior, identidade operacional e SHA do executor.

   **Isso atende ao texto da rodada 3.** No fluxo revisado, com o ledger preservado e os escritores respeitando o lock compartilhado, não encontrei caminho para uma cobrança histórica ou de outra tentativa passar como prova. O prefixo seleciona cobranças candidatas; a proveniência depende também da tentativa, exclusão mútua e recibo.

   **Interrupção entre resumo e recibo deve causar STOP**, inclusive quando a cobrança interna já ocorreu. Recusar reconstrução é a opção conservadora correta.

2. **SURVIVED, cobrança do wrapper.**  
   Em [r1_fixed_cap.py:646](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:646), o `finally` permanece sob o lock, desconta somente cobranças novas desde a abertura da tentativa e aplica piso zero. Na recuperação, não desconta novamente a cobrança interna antiga. O contador torna o nome único no histórico preservado.

   Uma exceção propagada ou falha na cobrança impede alcançar a publicação final. **Medir `started` depois da aquisição é aceitável neste escopo:** `Exclusive` recusa concorrência, sem aguardar a execução alheia. A aquisição, recusas anteriores à entrada e o pequeno trabalho posterior à medição ficam fora dessa contabilização. Também não há garantia de execução de `finally` após término forçado do processo.

3. **SURVIVED, margem do estágio 2.**  
   [r1_fixed_cap.py:331](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:331) calcula o menor teto aplicável sob o lock, depois de `hard_cap`, registra a conferência e recusa margem insuficiente **antes de `record_start`**. `expected_cap` confere o teto recalculado antes de criar o driver.

   [r1_fixed_cap.py:686](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:686) usa a média dos custos dos sidecars completos do estágio 1 multiplicada pelo número de injeções do estágio 2. **A regra de parada de 1,5 vez a projeção não voltou.** Sobrevive como extrapolação de planejamento, sem garantia de custo futuro ou representatividade.

4. **SURVIVED, testes solicitados nos itens 4 a 6.**  
   A leitura confirma cobertura de cobrança histórica contra vinculada, ausência de recibo, exceção com cobrança do wrapper, retomada com reconciliação de batch aberto e margem insuficiente diante de teto efetivo menor.

   A retomada em [test_r1_fixed_cap.py:163](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:163) efetivamente faz duas chamadas, preserva o teto anterior e verifica a cobrança reconciliada. **São suficientes para as regressões pedidas**, com as melhorias opcionais abaixo. Não demonstram o comportamento físico do watchdog.

5. **SURVIVED, ausência de bloqueio adicional identificado.**  
   A identidade operacional é persistida antes do despacho em [r1_fixed_cap.py:199](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:199); retomada e resumo recusam mudança do executor. O diff contém apenas os dois arquivos informados. A cobrança histórica permanece no ledger, sem alteração nesse commit.

   **Preserve os bytes do executor após o primeiro despacho**, inclusive comentários e docstring. SHA-256 revisado:

   `7f125394cc5898941d508c5d1fcc3119e31ee1bf6aba02e10a1385756bd65769`

**Correções que bloqueiam o despacho**

**Nenhuma identificada nesta rodada.**

**Ressalvas e melhorias concretas, sem bloquear**

1. Em [test_r1_fixed_cap.py:392](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:392), fortalecer a reprodução exata da interrupção solicitada.  
   **Texto:** “Abrir e persistir a tentativa sob `lv.Exclusive` antes de escrever o JSON correto; interromper sem cobrança nova; verificar STOP, ausência de publicação e preservação da tentativa e da cobrança histórica.” O teste atual já protege contra a aceitação da cobrança histórica, mas omite a tentativa persistida desse cenário.

2. Em [test_r1_fixed_cap.py:512](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:512), verificar numericamente o desconto.  
   **Texto:** “Com relógio determinístico, conferir cobrança exata do wrapper para consumo interno menor que o total e cobrança exatamente zero quando maior; a cobrança histórica não entra no desconto.” A asserção atual `hours >= 0` verifica apenas o piso.

**Liberação registrada neste parecer**

- **Complemento: executor LIBERADO**, para `r1_t2ae_1c`, 14 injeções, alocação fixa de **1,5 CPU-h**, **3 workers**, sujeito às guardas existentes.
- **Estágio 2: executor LIBERADO**, para execução posterior do `r1_t2ae_2`, 51 injeções, alocação de **3,1 CPU-h**, **4 workers**, somente após publicação válida do estágio 1, ausência de futilidade e aprovação da margem efetiva com os 51 custos medidos.

Esta liberação encerra a revisão do código solicitado; não certifica antecipadamente as condições operacionais futuras nem autoriza ultrapassar qualquer STOP.