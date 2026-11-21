## Parecer da rodada 2

**O complemento ainda exige correções no controle do teto e na publicação. D2-F não deve executar nesta rodada, por financiamento autorizado insuficiente e ausência do adaptador revisado.**

Corrijo minha posição operacional anterior: disponibilidade da reserva não equivale a autorização para utilizá-la na D2-F. A justificativa probabilística original continua refutada.

Somente leitura local, sem rede, scripts ou testes. Não acessei o caminho proibido. `HEAD` permanece `860f27d`; somente os dois arquivos revisados estão novos, sem commit. O resultado de pytest é informado por você, não reproduzido neste parecer.

## Vereditos por item

| Item | Veredito | Fundamentação |
|---|---|---|
| **1a. Teto fixo protegido** | **WEAKENED** | A fórmula reserva corretamente uma cobrança adicional de crash e a margem nominal de polling. Os tetos são **0,893561** e **2,034722 CPU-h**. Entretanto, o valor retornado por `lv.hard_cap` é descartado, preservando apenas sua recusa quando não há espaço. |
| **1b. Identidade operacional** | **SURVIVED** | Executor e parâmetros são vinculados antes do despacho; a retomada exige igualdade; o resumo confere o executor. A separação entre identidade científica e operacional está explicitamente declarada. |
| **1c. Parte nova e reserva** | **SURVIVED** | Nova parte de 1,5 CPU-h, redução correspondente da reserva, pasta própria e seleção dos ausentes. A parte antiga conserva seu stop. |
| **1d. Junção e resumo** | **WEAKENED** | Marcador após `finish`, conclusão do driver, cobranças fechadas, consumo reconciliado, gates, cobertura e leitor restaurado estão presentes. Restam uma corrida na escrita única e uma recuperação que contorna verificações e cobrança do resumo. |
| **1e. Estágio 2** | **WEAKENED** | O vínculo entre os dois registros, o executor e a futilidade estão protegidos. Falta reconciliar o teto novo com a projeção de **2,1 CPU-h** ainda documentada e a margem obrigatória de 1,3. |
| **1f. Testes sintéticos** | **WEAKENED** | Cobrem as principais correções anteriores e declaram corretamente seu alcance. Faltam regressões para os problemas restantes abaixo. Não demonstram limite físico estrito, conforme a própria docstring. |
| **2-i. 0,114 como teto** | **REFUTED** | Continua sendo estimativa condicional de **0,113865**, sem teto demonstrado para o gerador v2. |
| **2-ii. 14 em 178** | **SURVIVED** | Confere como contagem histórica derivada e registrada para v1, com as ressalvas Monte Carlo existentes. Não vincula deterministicamente futuros conjuntos v2. |
| **2-iii. Nove por conjunto** | **REFUTED** | A regra fixa admite até **14 individualmente e 18 no agregado**, sujeita ao limiar próprio mais estrito. Nove não é teto individual. |
| **2-iv. Não executar D2-F** | **WEAKENED** | **Sobrevive a não execução agora**, por financiamento autorizado insuficiente e implementação pendente. Não sobrevive atribuí-la automaticamente à implausibilidade pela regra (e)1. |

## Correções que bloqueiam o complemento T2a-E

1. **Aplicar o limite calculado para a linha, em vez de apenas consultá-lo.**

   Arquivos: [r1_fixed_cap.py:254](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:254) e [r1_fixed_cap.py:155](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:155).

   Atualmente, `lv.hard_cap(...)` pode devolver um teto positivo menor que o teto protegido, mas esse valor é ignorado. A guarda global continua existindo; ela não transforma esse retorno em limite do driver.

   **Correção concreta:** aplicar o menor entre o teto protegido e o teto permitido pela linha. Registrar o teto efetivamente aplicado e impedir sua elevação numa retomada.

   **Texto:**

   > “O teto efetivo é o menor entre o teto protegido da alocação e o teto cumulativo permitido pela linha. Uma retomada não eleva o teto anteriormente registrado.”

   Acrescentar teste em que o limite da linha seja **positivo, porém menor** que o teto protegido.

2. **Mover a verificação de escrita única para dentro do lock.**

   Arquivo: [r1_fixed_cap.py:383](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:383).

   Dois processos podem observar ausência do registro antes de adquirir o lock. O primeiro publica e libera; o segundo adquire depois, entra na recuperação e sobrescreve o registro final. A exclusão mútua durante a escrita não corrige a pré-condição verificada anteriormente.

   **Correção concreta:** verificar `COMPLETION_RECORD.exists()` dentro de `lv.Exclusive`, antes de qualquer processamento ou publicação.

   **Texto:**

   > “A existência do registro final é verificada sob o mesmo lock que protege sua publicação. Um registro final existente nunca é sobrescrito.”

   Acrescentar teste determinístico em que o registro apareça entre a verificação externa e a aquisição do lock.

3. **Manter caps e contabilidade também na recuperação do resumo.**

   Arquivo: [r1_fixed_cap.py:388](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:388).

   O ramo `recovered` não chama `te.summarize`, portanto pula suas verificações de caps, espaço das cobranças e cobrança de CPU.

   Existe um caminho especialmente relevante: `te.summarize` escreve `t2ae-1.json`, depois sua cobrança provoca STOP. Uma nova chamada entra na recuperação e publica o complemento sem reaplicar essa restrição. Uma interrupção anterior à cobrança também pode deixar consumo sem reconciliação.

   **Correção concreta:**

   - Aplicar as verificações de caps e espaço das cobranças nos dois caminhos.
   - Contabilizar o trabalho adicional do wrapper, evitando duplicar o custo já cobrado por `te.summarize`.
   - Exigir reconciliação da tentativa anterior quando sua cobrança não puder ser demonstrada.
   - Publicar `state: final` somente depois dessas condições.

   **Texto:**

   > “A recuperação preserva as verificações de caps e a contabilidade do resumo. A existência de um JSON não supera um STOP nem prova cobrança concluída. Contabilidade anterior incerta impede a publicação final.”

   Acrescentar testes para recuperação após cobrança que causou STOP e após interrupção sem cobrança demonstrável.

   **Estes problemas precisam ser corrigidos antes do primeiro despacho**, pois o hash do executor ficará congelado também para o resumo.

## Pendência exclusiva do estágio 2

4. **Reconciliar projeção, margem e teto antes de executar o estágio 2.**

   Referências: [r1_fixed_cap.py:73](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:73) e [revisão:185](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:185).

   O teto novo é **2,034722 CPU-h**. Para a projeção documentada de **2,1**, a margem exige **2,73**, portanto não cabe.

   A estimativa nova de aproximadamente **1,52** exigiria **1,976**, que cabe. Entretanto, essa substituição não está reconciliada com o planejamento registrado.

   **Texto a registrar prospectivamente:**

   > “O teto protegido do estágio 2 é 2,034722 CPU-h. Ele não satisfaz a margem de 1,3 sobre a projeção anterior de 2,1 CPU-h. A execução depende de revisão expressamente registrada da projeção, com sua fundamentação, ou de nova decisão sobre financiamento e teto.”

   **Não bloqueia o complemento das 14 injeções.** Não alterar os arquivos científicos congelados para fazer essa reconciliação.

## Ressalvas e ajustes não bloqueantes

5. **Distinguir CPU de tempo decorrido e corrigir um comentário.**

   Arquivos: [r1_fixed_cap.py:72](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:72) e [test_r1_fixed_cap.py:105](C:/Projetos/refute/tests/v055/test_r1_fixed_cap.py:105).

   O driver verifica o limite do shard pelo **tempo decorrido desde o despacho**, incluindo inicialização. O máximo observado de 215 CPU-s não demonstra duração inferior a 600 segundos.

   **Texto:**

   > “O limite operacional é 600 segundos decorridos desde o despacho. Os 215 CPU-s observados são referência de custo, sem demonstrar esse limite temporal. Sua ultrapassagem continua causando STOP.”

   No teste, dez workers com limite de **600 segundos** reservam **1,722222 CPU-h**, não 3,39. A recusa continua correta.

6. **Validar os campos decisórios na recuperação.**

   Arquivo: [r1_fixed_cap.py:390](C:/Projetos/refute/docs/validation/v0.5.5/r1_fixed_cap.py:390).

   Além de identidade e contagens, conferir `stage == "1"`, presença e coerência de `futile_after_1` e eventual `outcome`, usando as funções congeladas.

   O teste atual aceita deliberadamente um documento contendo apenas identidade e contagens. Isso verifica uma recuperação mais permissiva que um resumo completo.

## D2-F: financiamento e decisão

**(a) Não mantenho a recomendação de executar A nesta rodada sob o financiamento autorizado.**

A aritmética é:

| Quantidade | CPU-h |
|---|---:|
| Projeção: 200 × 0,052 | **10,4** |
| Teto mínimo: 1,3 × 10,4 | **13,52** |
| Máximo com alocação 14,2, sem nenhuma reserva | **12,909091** |
| Alocação necessária, quatro workers, limite 1.200 s | **16,228111** |
| Alocação necessária, dez workers, limite 1.200 s | **18,262278** |

**(b) Não existe configuração que satisfaça essas condições somente com 14,2 CPU-h.** Reduzir workers não resolve: até o limite idealizado sem reserva já é insuficiente.

Com quatro workers e limite de 1.200 segundos, faltariam **2,028111 CPU-h além dos 14,2**. Isso exigiria decisão adicional do mantenedor, além do adaptador e sua revisão. Não considero essa transferência autorizada.

O preço de 0,052 permanece **estimado, sem medição auditável apresentada**. Os valores acima são condições de planejamento, não garantia do custo real.

**(c) Texto exato proposto para o registro:**

> **D2-F not run: authorized funding insufficient; fixed-cap adapter pending.**
>
> D2-F permanece sem execução nesta decisão de governança. A transferência autorizada limita-se a 14,2 CPU-h da parte B da D1-P. A projeção estimada de 10,4 CPU-h para A exige teto de driver de pelo menos 13,52 CPU-h pela margem de 1,3. Mesmo sem reservas, 14,2/1,10 permite apenas 12,909091 CPU-h. Com quatro workers, limite de shard de 1.200 segundos, reserva de crash e margem nominal de polling, seriam necessários 16,228111 CPU-h. Não está autorizada a complementação pela reserva. O adaptador de teto fixo também permanece pendente de implementação e revisão.
>
> O valor histórico 0,113865 é estimativa preditiva condicional, sem teto demonstrado para o gerador v2. A contagem histórica superior derivada é 14/178; no cenário fixo, route admite até 14 por conjunto e até 18 no agregado, sujeitos aos limiares próprios mais estritos. Não foi demonstrado que route seja implausível pela regra (e)1. Esta não execução não constitui resultado experimental nem conclusão de inviabilidade de D2.

**Não recomendo o título “D2-F not run by the decision-value rule”**, pois atribuiria a parada a uma fundamentação que continua sem demonstração. Nesta rodada, a não execução já tem motivo suficiente e verificável no financiamento autorizado.