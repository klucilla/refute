## Parecer da rodada 1

**O complemento T2a-E ainda tem bloqueios. A justificativa apresentada para cancelar a D2-F está REFUTED.** Minha posição de mérito é executar D2-F A, com futilidade, teto fixo corrigido e financiamento registrado para eventual B.

Fiz somente leitura local, sem rede, testes ou execução dos scripts de checagem. Não acessei o caminho proibido. `HEAD = 860f27d`, precedido por `356f105`. O `git diff` está vazio porque as únicas alterações são os dois arquivos novos, ainda não rastreados, que li integralmente.

## 1. Complemento T2a-E

| Item | Veredito | Fundamentação |
|---|---|---|
| **1a. `execute_fixed`** | **REFUTED** | Elimina corretamente checkpoint e projeção, mantém a guarda e a contabilização normal. Porém, **não garante consumo contabilizado dentro da alocação**, especialmente após crash. O watchdog também não fornece um limite físico exato. |
| **1b. Código e fingerprint** | **WEAKENED** | Preservar o fingerprint dos módulos científicos é defensável como exceção operacional expressamente registrada. Entretanto, o executor altera execução e leitura dos resultados. Seu hash gravado somente no resumo não vincula os bytes efetivamente usados no início e na retomada. |
| **1c. Parte nova e reserva** | **SURVIVED** | No ledger atual, a reserva comporta a transferência: **21,8 → 20,3 CPU-h**, com nova alocação de 1,5. `declare_fixed` preserva as demais alocações; o stop antigo permanece. A seleção usa somente os identificadores ausentes. |
| **1d. Junção e resumo** | **WEAKENED** | Sidecars, argumentos, bytes, cobertura única e ordem são conferidos. A substituição temporária de `_records`, restaurada por `finally`, é aceitável sob uso serial explícito. Falta exigir conclusão e contabilidade final persistidas antes de aceitar os shards. |
| **1e. Estágio 2** | **WEAKENED** | A futilidade e a identidade científica são verificadas. Porém, o código exige apenas `t2ae-1.json`, sem exigir o registro de complemento finalizado e conferir seu vínculo com aquele resumo. |
| **1f. Testes sintéticos** | **WEAKENED** | Cobrem casos úteis, mas substituem `_batch`, retirando justamente watchdog, contabilidade viva e fechamento de crash. Também não cobrem interrupções entre shards completos, contabilidade final e publicação dos dois registros. **Não os executei.** |

### Correções que bloqueiam o complemento

1. **Corrigir a promessa e a proteção da alocação.**

   Arquivos: [r1_fixed_cap.py:98](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:98), [r1_fixed_cap.py:162](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:162), [driver.py:375](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:375) e [driver.py:489](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:489).

   Há dois contraexemplos concretos:

   - A função aceita `cap_hours == allocation_hours`; o watchdog só dispara acima de `1,10 × cap`. O chamador normal divide por 1,10, mas a própria função não exige essa proteção.
   - Uma cobrança de crash com dez workers e limite de shard de 1.200 segundos acrescenta **10 × (1.200 + 20)/3.600 = 3,388889 CPU-h**. Isso, sozinho, supera a alocação de **1,5 CPU-h**. A retomada pode parar sem despachar trabalho adicional, mas a contabilidade já ultrapassou a alocação.

   Além disso, dividir por 1,10 coloca o **limiar de acionamento** na alocação. O polling de 0,5 segundo e o encerramento posterior ainda permitem ultrapassagem física.

   **Correção concreta:** no executor novo, validar o teto protegido, reservar espaço para uma cobrança de crash adicional e para a ultrapassagem operacional, mantendo as cobranças originais. Recusar despacho se essa reserva não couber. Com dez workers, a reserva de crash já inviabiliza o complemento sob uma alocação contabilística estrita de 1,5 CPU-h.

   **Texto obrigatório:**

   > “O fator 1,10 define o limiar do watchdog, não um limite físico exato. Todas as cobranças de crash entram na alocação. O despacho é recusado quando não cabe a reserva necessária.”

   Se a intenção for apenas um teto operacional com possíveis cobranças acima dele, isso precisa ser explicitamente distinguido da garantia atualmente anunciada. **Não certifico ausência de caminhos acima da alocação no código apresentado.**

2. **Vincular o executor antes do primeiro despacho.**

   Arquivos: [r1_fixed_cap.py:160](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:160) e [r1_fixed_cap.py:288](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:288).

   Hoje, o executor pode mudar entre execução, retomada e resumo sem alterar o fingerprint científico. `own_sha256()` no resumo identificaria somente a versão que resumiu.

   **Correção concreta:** persistir, sob o lock e antes do despacho, a identidade operacional contendo SHA-256 do executor, fingerprint científico, parte, alocação e cronograma do complemento. Exigir igualdade na retomada e no resumo.

   **Texto:**

   > “O fingerprint científico permanece inalterado. O executor possui identidade operacional separada, congelada antes do despacho e conferida na retomada e no resumo. Esta exceção não constitui fechamento integral das dependências pela guarda FROZEN.”

   A exclusão de `__main__` não basta, por si, como justificativa da exceção.

3. **Exigir fechamento e contabilidade final antes da montagem.**

   Arquivos: [r1_fixed_cap.py:120](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:120) e [r1_fixed_cap.py:232](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:232).

   **Caminho problemático:** os últimos shards são persistidos; o controlador cai antes de concluir a contabilidade. A linha já contém `driver = fixed-cap`, não tem necessariamente `unresolved_stop`, e `assemble()` pode aceitar todos os shards. O resumo então publica consumo zero ou antigo obtido do ledger.

   `assemble()` **não exige `state.json = complete` nem fechamento das cobranças**.

   **Correção concreta:**

   - Persistir um marcador de conclusão somente após `budgeted.finish` terminar sem stop.
   - Na montagem, exigir esse marcador, identidade correspondente, `comp.completed()`, cobranças fechadas e consumo reconciliado com o ledger.
   - Reaplicar `_open_gates` para a parte de complemento.
   - Manter montagem e resumo sob `lv.Exclusive`, incluindo a restauração do leitor.

   **Texto:**

   > “Cobertura completa de shards não equivale a execução contabilmente concluída. Sem fechamento das cobranças, conclusão persistida e identidade correspondente no ledger, o resumo é recusado.”

   O stop da parte antiga continua sendo a exceção deliberada. Isso não justifica ignorar gates ou conclusão da parte nova.

4. **Acrescentar os testes das proteções anteriores.**

   Arquivo: [test_r1_fixed_cap.py:88](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:88).

   **Casos necessários:** cobrança de crash que excederia a alocação; teto sem proteção contra overshoot; executor alterado numa retomada; todos os shards presentes com contabilidade incompleta; gate posterior; complemento com stop; e interrupção entre os dois registros do resumo.

   **Texto do alcance:**

   > “Os testes determinísticos de `_batch` verificam o fluxo sintético; não validam o watchdog real nem demonstram um limite físico estrito.”

### Correção que bloqueia o estágio 2

5. **Exigir o registro final do complemento.**

   Arquivos: [r1_fixed_cap.py:278](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:278) e [r1_fixed_cap.py:302](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:302).

   `te.summarize("1")` escreve `t2ae-1.json` antes de o wrapper escrever `t2ae-1-completion.json`. Uma interrupção nessa janela deixa um resumo que `_first_stage()` aceita.

   **Correção concreta:** tratar o registro de complemento finalizado como marcador de publicação. Antes do estágio 2, conferir sua existência, estado final, hash de `t2ae-1.json` e identidade operacional. Prever recuperação dessa janela sem sobrescrever silenciosamente o resumo existente.

   **Texto:**

   > “O estágio 2 exige resumo e registro de complemento finalizados e vinculados por SHA-256, além da identidade científica e da regra de futilidade.”

### Ressalvas não bloqueantes

6. **Precisar a descrição do código preservado e do consumo.**

   Arquivos: [r1_fixed_cap.py:11](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:11) e [r1_fixed_cap.py:289](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:289).

   **Texto substituto:**

   > “Os módulos científicos e seus arquivos congelados permanecem inalterados. O executor operacional é novo e possui identidade separada. O resumo utiliza o leitor combinado declarado.”

   Acrescentar ao registro de complemento `total_stage_1_cpu_hours`, somando ambas as partes. A nota sobre `t2ae-1.json` está correta, mas um total explícito reduz o risco de leitura equivocada.

   O estado antigo registra **51 shards, 37 concluídos, fingerprint `20c9aefffa4007f4` e 1,533919 CPU-h**; existem 37 sidecars. Não executei o cálculo de fingerprint nem `_done`.

## 2. D2-F

| Item | Veredito | Fundamentação |
|---|---|---|
| **2-i. 0,114 como teto** | **REFUTED** | É **estimativa preditiva condicional**, aproximadamente 0,113865. Não foi demonstrado limite superior para o gerador v2. Isso já está expressamente retificado no código, na revisão e nas duas rodadas night. |
| **2-ii. 14 em 178** | **SURVIVED** | É o número registrado para a contagem superior histórica derivada da variante 4, no gerador v1: nove SIN, incluindo os dois INFO, mais dois DATA e três da faixa, totalizando 14. **Não constitui limite determinístico da futura classificação Monte Carlo nem dos novos conjuntos v2.** |
| **2-iii. Máximo de nove por conjunto** | **REFUTED** | No cenário fixo de 178 elegíveis por conjunto, são **até 14 individualmente e até 18 somados**, sujeitos ao limiar próprio eventualmente mais estrito. Nove é a média quando ambos somam 18, não um teto individual. |
| **2-iv. Cancelamento por (e)1** | **REFUTED** | A justificativa depende de um teto probabilístico não demonstrado e de uma restrição individual incorreta. O estatuto não classifica automaticamente cerca de 11,4% como implausível. **Sustento executar A**, após resolver as condições técnicas e registrar o financiamento. |

7. **Retificar a fundamentação da decisão, preservando o registro original.**

   Referências: [decisão:4](C:/Projetos/refute/.cache/v055/issue-218-decision-2100.md:4), [revisão:104](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:104), [d2f_decision_value.py:25](C:/Projetos/refute/docs/validation/v0.5.5/d2f_decision_value.py:25) e [estatuto:176](C:/Projetos/refute/docs/plans/v0.5.5-charter.md:176).

   **Texto para uma retificação separada:**

   > “O valor 0,113865 é uma estimativa preditiva condicionada ao modelo Beta compartilhado, às classificações históricas utilizadas e a dois conjuntos de exatamente 178 elegíveis. Não é teto demonstrado para o gerador v2. O registro histórico deriva 14/178 na contagem superior da variante 4, com as ressalvas Monte Carlo documentadas. No cenário fixo, route admite até 14 por conjunto e até 18 no agregado, sujeitos aos limiares próprios mais estritos. Esses números não demonstram implausibilidade pela regra (e)1.”

   **Contraexemplo à restrição de nove:** a dupla **(14, 4)** satisfaz os limites fixos. O Wilson superior de 18/356 é aproximadamente **0,0785005**, abaixo de 14/178, aproximadamente **0,0786517**. Já 19/356 produz aproximadamente **0,0818470**, acima.

8. **Registrar o financiamento e implementar o caminho fixo da D2-F antes de A.**

   Referências: [ledger.json:51](C:/Projetos/refute/docs/validation/v0.5.5/ledger.json:51), [d1p-A.json:1033](C:/Projetos/refute/docs/validation/v0.5.5/d1p-A.json:1033) e [d2f_floor.py:539](C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:539).

   A futilidade de D1-P A está registrada. Após reservar 1,5 para o complemento:

   **21,8 − 1,5 + 14,2 = 34,5 CPU-h**, contra **29,8 CPU-h** planejados para D2-F A+B. Sobram **4,7 CPU-h de reserva**, antes de outros remanejamentos.

   Isso resolve o impedimento financeiro apontado na conversa night, **após a transferência ser registrada**. O código atual da D2-F ainda chama `budgeted_v3.execute`; o novo wrapper também está preso a `te.shard`. Portanto, a decisão de executar A precisa de um adaptador fixo próprio, preservando as regras científicas e a futilidade.

   **Texto:**

   > “D2-F A será executada com teto fixo protegido e a futilidade congelada. O financiamento de B fica reservado previamente; B somente executa se A não for fútil e os demais tetos permitirem.”

## Posição que sustentaria ao fim

**T2a-E:** manter parada até corrigir os bloqueios técnicos acima.

**D2-F:** executar A nas condições declaradas. O valor condicional disponível e as ações distintas em G1 sustentam esse julgamento de planejamento; não demonstram uma probabilidade para v2.

Se a divergência persistir ao término da terceira rodada, aplica-se a **não execução conservadora**, registrada como decisão de governança por consenso não alcançado. Não deve ser registrada como teto probabilístico demonstrado, aplicação automática de um limiar do estatuto ou conclusão de inviabilidade de D2.