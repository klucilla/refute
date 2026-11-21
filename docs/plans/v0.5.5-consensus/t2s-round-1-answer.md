**Rodada 1/3: NÃO LIBERADO**, pela validação incompleta da repetição. A aplicação inicial parece correta no estado atual, mas a garantia de que uma repetição confere o ledger inteiro não está implementada.

Confirmei `0011f2c` em `main` e os hashes locais. Apenas leitura, sem rede, execução de scripts, testes ou alterações. Não acessei o caminho proibido.

1. **WEAKENED, passo e identidades.**

   A primeira aplicação mantém alocação, reserva e transferência no mesmo objeto, com um único salvamento atômico sob `lv.Exclusive`. As guardas de identidade, consumo, tentativas e início estão presentes.

   O [ledger.json:132](/C:/Projetos/refute/docs/validation/v0.5.5/ledger.json:132) contém somente alocação de 3,1 e a margem recusada nessa parte. Portanto, **a mudança não invalida identidade já persistida**: `budgeted._identity` e a identidade operacional serão formadas com 3,55 no primeiro início. O registro histórico de margem permanece válido como histórico.

   **A lacuna está na repetição**, em [r1_allocation_step.py:75](/C:/Projetos/refute/docs/validation/v0.5.5/r1_allocation_step.py:75): basta existir uma transferência com `step == name` e a alocação de destino ser 3,55. Não são conferidos conteúdo da transferência, reserva ou limites.

   Contraexemplo por leitura: após uma aplicação correta, devolver indevidamente 0,45 à reserva, mantendo destino e transferência, faz a repetição retornar sucesso mesmo com soma de alocações de **63,95**, superior à linha de 63,5.

2. **SURVIVED, cálculo e nova checagem de margem.**

   Os valores conferem:

   - Teto protegido: **2,6005050505 CPU-h**.
   - Margem exigida: **2,5833381076 CPU-h**.
   - Folga: **0,0171669429 CPU-h**.
   - Alocação mínima calculada: **3,5311163628 CPU-h**.

   Em [r1_fixed_cap.py:331](/C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:331), teto efetivo e margem são conferidos sob o lock, antes de `record_start`. `expected_cap` impede entregar ao driver um teto diferente do aprovado.

   A projeção é recalculada dos sidecars em `stage2_projection`, antes da aquisição desse lock. **A checagem da margem**, com essa projeção, ocorre sob o lock.

   Não identifiquei impedimento adicional causado pela nova alocação. Isso não certifica antecipadamente caps operacionais, guardas congeladas, arquivos ou consumo futuro.

3. **SURVIVED, ressalva sobre `lv.declare()`, no procedimento restrito.**

   A docstring é suficiente como restrição operacional neste escopo: o caminho restante do runner fixo não chama `lv.declare()`. **Ela não cria uma proteção automática** contra execução posterior de comandos antigos.

   A proibição deve também constar do procedimento exato publicado antes do despacho. O procedimento local anterior ainda descreve **3,1 e recusa esperada**, em [.cache/v055/issue-218-t2ae-2-procedure.md:7](/C:/Projetos/refute/.cache/v055/issue-218-t2ae-2-procedure.md:7).

4. **WEAKENED, testes sintéticos.**

   O [JUnit existente:1](/C:/Projetos/refute/.cache/v055/junit-step2.xml:1) registra nove testes sem falhas. **Não os executei** nem reproduzi esse resultado.

   A leitura confirma cobertura do caminho normal, salvamento único, margem recusada preservada, início anterior, identidade, consumo, alocação divergente, reserva insuficiente e linha excedida.

   Faltam as regressões da repetição inconsistente descrita no item 1. Também falta um caso explícito com `attempts`, guarda central declarada pelo passo.

5. **SURVIVED, observação sobre a D2-F, limitada ao primeiro despacho.**

   [d2f_fixed_cap.py:213](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_fixed_cap.py:213) exige exatamente **16,3** após o financiamento. Uma transferência adicional para essa parte seria recusada pelo adaptador atual. Usar uma alocação maior exige revisão do adaptador e de seu novo SHA.

   No primeiro despacho, sem teto anterior persistido, os parâmetros fixos dão **13,585354 contra 13,52**. Nesse cenário, a restrição da linha pode reduzir o teto efetivo e causar recusa de margem.

   **Aumentar a alocação não corrige uma restrição da linha**, pois ela depende do consumo acumulado. Em retomada, `cap_hours` também pode limitar o teto e nunca é elevado.

   Basta registrar essa limitação agora. A folga autorizada não torna sua aplicação executável pelo adaptador atual, nem permite superar esses STOPs.

**Correções que bloqueiam a aplicação do passo**

- [r1_allocation_step.py:75](/C:/Projetos/refute/docs/validation/v0.5.5/r1_allocation_step.py:75), complementando o registro da linha 95:

  **Texto:** “Na repetição, exigir um único registro com destino, origem, valor, alocações anterior e posterior, decisão e SHA correspondentes ao passo. Registrar também a reserva anterior e posterior. Conferir a reserva contra esse registro e eventuais transferências posteriores demonstráveis, além das duas linhas orçamentárias. Qualquer divergência ou reconciliação não demonstrável causa STOP, sem gravação.”

- [tests/v055/test_r1_allocation_step.py:131](/C:/Projetos/refute/tests/v055/test_r1_allocation_step.py:131):

  **Texto:** “Após aplicação normal, testar separadamente reserva indevidamente recomposta, registro adulterado, registro duplicado e linha excedida, mantendo o destino em 3,55. Exigir STOP e preservação dos bytes do ledger. Manter a repetição íntegra sem gravação. Acrescentar recusa com tentativa arquivada.”

**Ressalvas, sem bloquear a aplicação do ledger**

- [r1_allocation_step.py:18](/C:/Projetos/refute/docs/validation/v0.5.5/r1_allocation_step.py:18):

  **Texto:** “Repetir no procedimento operacional a proibição de `lv.declare()`, sua CLI e os scripts antigos que o chamam; divergência exige reconciliação pelo mantenedor.”

- [.cache/v055/issue-218-t2ae-2-procedure.md:7](/C:/Projetos/refute/.cache/v055/issue-218-t2ae-2-procedure.md:7), **antes do despacho**:

  **Texto:** “Substituir o procedimento anterior: alocação 3,55, débito de 0,45 da reserva, SHA do passo liberado e runner preservado; margem novamente conferida pelo runner. D2-F somente depois do estágio 2.”

- [.cache/v055/issue-218-decision-1000.md:7](/C:/Projetos/refute/.cache/v055/issue-218-decision-1000.md:7), como esclarecimento operacional:

  **Texto:** “A folga não contorna restrição da linha ou teto de retomada. Na D2-F, elevar 16,3 exige nova revisão do adaptador antes de qualquer aplicação.”

**Passo NÃO LIBERADO para aplicação ao ledger real nesta rodada.** A pendência conservadora fica registrada neste parecer.

SHA-256 revisado: `886a4a4ba37e1cd6cfb2cf61536ea51382eb9a2fc95a050af27f36dc619b9b57`.

