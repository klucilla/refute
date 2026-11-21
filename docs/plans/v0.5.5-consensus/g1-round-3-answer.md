## Parecer final, rodada 3

**O executor atual não recebe liberação para o completamento.** Restou uma falha concreta na prova de cobrança da recuperação. O estágio 2 também conserva uma divergência entre o teto usado para conferir a margem e o teto efetivamente aplicado.

**D2-F permanece sem execução**, pelo financiamento autorizado insuficiente e adaptador pendente, conforme o texto acordado.

Somente leitura local, sem rede, scripts ou testes. Não acessei o caminho proibido. `HEAD = 860f27d`; os dois arquivos continuam novos, sem commit. O pytest aprovado é informação apresentada por você, não execução reproduzida neste parecer.

## Vereditos finais por item

| Item | Veredito | Fundamentação |
|---|---|---|
| **1a. Teto protegido e efetivo** | **SURVIVED** | O chamador aplica `lv.hard_cap`; o executor usa o menor teto e impede elevação na retomada. Reservas e recusas estão implementadas. Sobrevive como proteção operacional declarada, sem garantia física absoluta do watchdog. |
| **1b. Identidade operacional** | **SURVIVED** | Executor, parâmetros e cronograma ficam vinculados antes do despacho; alterações são recusadas. A separação da identidade científica está explícita. |
| **1c. Parte nova e reserva** | **SURVIVED** | Alocação de 1,5 CPU-h, débito correspondente da reserva, pasta própria, somente ausentes e preservação do stop antigo. |
| **1d. Junção e publicação** | **REFUTED** | Cobertura, ordem, sidecars, conclusão contabilizada e escrita única estão protegidos. Porém, uma cobrança antiga pode ser aceita como prova da cobrança do resumo novo na recuperação. |
| **1e. Estágio 2** | **WEAKENED** | A revisão prospectiva da projeção é aceitável como planejamento. Entretanto, a margem é conferida contra o teto protegido, podendo o despacho aplicar teto efetivo menor. |
| **1f. Testes** | **WEAKENED** | Cobrem as correções declaradas, mas não a cobrança histórica confundida com a tentativa recuperada, nem a margem do estágio 2 diante de teto efetivo menor. O teste denominado “resume never raises” também não executa uma retomada. |
| **2-i. 0,114 como teto** | **REFUTED** | Continua sendo estimativa condicional, sem teto demonstrado para v2. |
| **2-ii. 14 em 178** | **SURVIVED** | Confere como contagem histórica derivada e registrada para v1, com as ressalvas Monte Carlo. Não vincula deterministicamente os futuros conjuntos v2. |
| **2-iii. Nove por conjunto** | **REFUTED** | Permanecem até 14 individualmente e até 18 no agregado, sujeitos aos limiares próprios mais estritos. |
| **2-iv. Não execução registrada** | **SURVIVED** | Sobrevive o **texto corrigido**: financiamento autorizado insuficiente e adaptador pendente, sem atribuição automática à regra (e)1 ou conclusão de inviabilidade. |

## Pendências que bloqueiam o completamento

### 1. Vincular a cobrança à tentativa e ao JSON recuperados

Arquivos: [r1_fixed_cap.py:436](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:436) e [ledger.json:33](C:/Projetos/refute/docs/validation/v0.5.5/ledger.json:33).

O ledger **já contém**:

` t2ae_summarize_1_20261120T235128Z `, cobrança de **0,0009461806 CPU-h**, anterior ao complemento.

Logo, este caminho é possível:

1. O resumo novo escreve `t2ae-1.json`.
2. O controlador cai antes de registrar sua cobrança.
3. A recuperação encontra exatamente uma cobrança com o prefixo, a antiga.
4. Identidade e campos decisórios conferem, permitindo publicação final sem demonstrar a cobrança da tentativa nova.

**Contar entradas pelo prefixo não estabelece proveniência.** Inversamente, após uma cobrança nova bem-sucedida, haverá duas entradas, causando recusa conservadora.

**Correção concreta:** persistir um comprovante de fechamento que vincule a tentativa, a cobrança específica, o SHA-256 do resumo e a identidade operacional. Recuperação sem esse vínculo deve parar para reconciliação do mantenedor. Não remover a cobrança histórica.

**Texto:**

> “A recuperação exige comprovação de cobrança da tentativa que produziu este resumo, vinculada ao seu SHA-256 e à identidade operacional. Quantidade de cobranças com um prefixo não constitui essa comprovação. Vínculo ausente ou incerto causa STOP.”

Adicionar regressão com **uma cobrança antiga**, JSON novo correto e interrupção antes da cobrança nova. A publicação deve ser recusada.

### 2. Cobrar o wrapper também quando há exceção

Arquivos: [r1_fixed_cap.py:424](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:424), [r1_fixed_cap.py:469](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:469) e [t2ae_census.py:451](C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:451).

A cobrança do wrapper ocorre somente ao alcançar a linha 472. Recusas durante a recuperação e exceções de `te.summarize` deixam esse trabalho sem cobrança.

Além disso, `inner` desconta **toda a chamada** de `te.summarize`, enquanto sua cobrança interna mede apenas `_summarize`, excluindo verificações anteriores e a própria operação de cobrança.

**Correção concreta:** contabilizar o wrapper em `finally`, ainda sob o lock, descontando somente o consumo efetivamente cobrado pela chamada interna. Publicar o registro final apenas após término normal e cobrança bem-sucedida.

**Texto:**

> “O trabalho adicional do wrapper é contabilizado também em tentativas recusadas ou interrompidas por exceção. Desconta-se somente consumo comprovadamente cobrado pelo resumo interno. Qualquer STOP impede a publicação final.”

**Essas duas pendências bloqueiam o despacho inicial**, porque corrigir posteriormente o executor mudaria o hash exigido pelo próprio resumo.

## Pendência exclusiva do estágio 2

### 3. Conferir a margem contra o teto efetivo

Arquivos: [r1_fixed_cap.py:516](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:516), [r1_fixed_cap.py:535](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:535) e [r1_fixed_cap.py:165](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:165).

Com quatro workers, o teto protegido é **2,191414 CPU-h**, permitindo projeção máxima de **1,685703 CPU-h** pela margem de 1,3.

**A revisão proposta satisfaz conceitualmente o pedido de fundamentação prospectiva:** usar os 51 sidecars completos é uma estimativa de planejamento explicitamente definida antes do estágio 2. A média dos 37 atuais é apenas antecipação; a decisão deve usar todos os 51.

Entretanto, `fits` compara somente o teto protegido. Depois, o executor pode reduzi-lo pelo limite da linha ou pelo teto gravado numa tentativa anterior.

**Correção concreta:** conferir, sob o lock e antes de registrar o início, que:

`cap_effetivo >= 1,3 × projeção`

Usar exatamente o mesmo teto entregue ao driver. Persistir a projeção, sua base e o teto efetivo antes do despacho; o procedimento da #218 pode referenciar esse registro.

**Texto:**

> “A projeção é uma extrapolação de planejamento baseada no CPU dos 51 shards concluídos do estágio 1, sem garantia de representatividade ou de custo futuro. O despacho exige teto efetivo, após todas as restrições, de pelo menos 1,3 vez essa projeção.”

Essa projeção não inclui, por si, todo o overhead do driver nem trabalho descartado. As reservas continuam separadas. **Não reintroduz a regra de parada de 1,5 vez a projeção.**

## Ajustes de testes

4. Em [test_r1_fixed_cap.py:284](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:284), distinguir cobrança histórica de cobrança vinculada ao resumo recuperado. Cobrir também cobrança do wrapper após exceção.

5. Em [test_r1_fixed_cap.py:113](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:113), acrescentar uma retomada real, elegível pelas regras, ou retirar do nome a afirmação de que a retomada foi exercitada. A proteção existe no código, mas esse teste faz somente uma execução.

6. Acrescentar regressão do estágio 2 em que o teto protegido comporta a margem, mas o teto efetivo não. O despacho deve ser recusado.

## Registro conservador ao encerrar as rodadas

> “Encerradas as três rodadas. O executor atual do complemento T2a-E permanece sem liberação por pendências na comprovação e contabilização do resumo recuperado. O estágio 2 permanece parado também pela comparação da margem com teto diferente daquele efetivamente aplicado. Preservam-se o stop histórico e todos os consumos registrados. D2-F não executa por financiamento autorizado insuficiente e adaptador pendente, sem classificação demonstrada de route como implausível e sem conclusão de inviabilidade.”