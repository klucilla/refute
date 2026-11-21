**Rodada 2/3: bloqueio anterior resolvido. O passo está LIBERADO para aplicação ao ledger real nos bytes revisados.**

Confirmei `9f3dc54` em `main`. O diff altera somente o passo e seus testes. Revisão por leitura local, sem rede, execução de scripts, testes ou alterações. Não acessei o caminho proibido.

1. **SURVIVED, validação da repetição.**

   [_verify_on_file:88](/C:/Projetos/refute/docs/validation/v0.5.5/r1_allocation_step.py:88) atende à correção funcional pedida: exige registro único, compara os campos esperados, confere destino, reconcilia a reserva com os débitos posteriores registrados e verifica ambas as linhas. O retorno ocorre sem salvamento.

   O contraexemplo da rodada 1, recompor indevidamente a reserva mantendo destino e transferência, agora é recusado.

   **Limite da conclusão:** os débitos posteriores são lidos dos registros de transferência; essa função não valida integralmente cada transferência posterior contra todas as suas alocações. No fluxo autorizado, o `fund()` da D2-F grava essas mudanças e seu registro atomicamente.

2. **SURVIVED, testes das correções.**

   A leitura confirma os cenários solicitados, incluindo preservação dos bytes nas sete divergências parametrizadas, repetição íntegra, débito posterior da reserva e tentativa arquivada.

   O [JUnit existente:1](/C:/Projetos/refute/.cache/v055/junit-step4.xml:1) registra **18 testes, zero falhas e zero erros**. É evidência do executor, não uma execução reproduzida por mim.

   São suficientes para as regressões pedidas nesta revisão.

3. **SURVIVED, tratamento das ressalvas.**

   O procedimento descrito basta: substituir explicitamente o anterior, identificar **3,55 CPU-h**, débito de **0,45**, SHA liberado, runner preservado e nova checagem da margem, além da proibição de `lv.declare()` e seus chamadores antigos.

   O esclarecimento sobre a folga também está correto. **A publicação na #218 permanece uma etapa anterior ao despacho**, conforme sua instrução. Não verifiquei essa publicação, pois não usei rede.

4. **SURVIVED, ausência de bloqueio adicional identificado.**

   A aplicação inicial continua sob o mesmo lock, com uma única gravação atômica das duas alocações e do registro.

   O ledger lido ainda mostra reserva de **20,3**, destino em **3,1**, margem recusada e nenhum início dessa parte. O passo permanece não aplicado. Os hashes do runner e do adaptador continuam iguais aos anteriormente revisados.

**Correções bloqueantes**

Nenhuma identificada nesta rodada.

**Ressalvas e melhorias opcionais**

- [r1_allocation_step.py:88](/C:/Projetos/refute/docs/validation/v0.5.5/r1_allocation_step.py:88): a rejeição de campos extras vale para o nível superior do registro; campos adicionais dentro de `reserve_hours` são aceitos. Isso não reabre o bloqueio financeiro identificado.

  **Texto de precisão:** “Os campos do registro principal são exatos; a reconciliação posterior utiliza os débitos registrados pelos passos autorizados.”

- [test_r1_allocation_step.py:184](/C:/Projetos/refute/tests/v055/test_r1_allocation_step.py:184): tornar o cenário posterior mais fiel ao financiamento real.

  **Texto:** “Incluir as partes D1-P B e D2-F A na fixture; junto do débito de 2,1 da reserva, zerar a origem de 14,2 e atribuir 16,3 ao destino, preservando a soma das alocações.”

**Passo LIBERADO para ser aplicado ao ledger real**, exclusivamente para elevar `r1_t2ae_2` de **3,1 para 3,55 CPU-h**, retirando **0,45 da reserva**, sujeito às guardas existentes.

SHA-256 revisado:

`4dd68bdfac2cf6bdee600a776a2707b2a71455794aafdc8c63cf977584702d72`