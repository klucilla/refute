**Rodada 1: não libero D1-P nem T2a-E neste estado.** Há um bloqueio comum no tratamento de locks e uma correção residual na função de decisão da D1-P. A D2-F permanece sem execução, mas a justificativa de “route implausível” ainda não está demonstrada.

Fiz somente leitura local, sem rede, testes ou execução dos scripts de checagem. Não acessei o caminho proibido. HEAD continua em `cd92c48`; há alterações locais. O JUnit apresentado registra **42 testes, zero falhas e zero erros**, sem certificar a correspondência com todos os bytes atuais.

**Vereditos por item**

| Item | Veredito | Fundamentação |
|---|---|---|
| **1. I4** | **SURVIVED** | Diagnóstico consistente com os registros: reprodução relativa a `1e-9`, mesmos passos, derivadas e tolerância `1e-2`; muda o domínio da comparação, com guarda de 25%. Continua sendo diagnóstico, sem conclusão sobre D2. Os contextos históricos restauram o estado por `finally` e recusam gravações no ledger durante a leitura declarada. |
| **2. D2-F** | **WEAKENED** | Contagem superior, potência inválida separada, variante 4, unidade própria e futilidade estão implementadas. Os números 11/14 conferem. A extrapolação das probabilidades para o gerador v2, como limites superiores, não foi demonstrada. |
| **2-plausibilidade** | **REFUTED** | Refutada a conclusão de que o cálculo apresentado basta para classificar “route” como implausível pelo estatuto. Cerca de 11% não recebe essa classificação automaticamente, sem critério previamente definido ou argumento de decisão adicional. Isso não libera a D2-F. |
| **3a. WEAKENED** | **SURVIVED** | `0,05` por teste, `0,10` apenas cenário e mudança de unidade estão explícitos. Não estabelece teto cumulativo da bateria. |
| **3b. REFUTED** | **SURVIVED** | Reproduz os limites estritos pedidos. Estender às linhas de PG/PV/PA da mesma tabela é aceitável como interpretação conservadora declarada, preservados também os limites integrais da bateria. |
| **3c. Geradores e ponte** | **WEAKENED** | Separação entre desenvolvimento v2 e confirmação v1 correta. A ponte usa as sementes certas, mas o resumo não publica uma comparação equivalente entre v1 e o subconjunto v2 correspondente. |
| **3d. Convenções** | **WEAKENED** | Inclui a correção da I4 com resultados conhecidos. Algumas direções são apresentadas categoricamente, embora não haja ordenação geral demonstrada, especialmente prior versus caixa. |
| **3e. Padrão de prova** | **SURVIVED** | Os quatro elementos novos reproduzem a decisão. Os 95% são por conjunto, como escrito, não uma garantia simultânea adicional. |
| **3f. R2** | **SURVIVED** | Especifica o mecanismo de cegueira e as duas agregações, sem escolher a futura regra de agregação. A eficácia dependerá da inspeção do bundle efetivamente entregue. |
| **4. D1-P** | **WEAKENED** | Distâncias para todos os elegíveis, duas visões, preços, cenários, retirada de `closed` e sinal de zero sobreviventes conferem. Restam a cobertura incompleta na função pura e a publicação da ponte. O prior de 15% a 30% é opinião de planejamento, não probabilidade calculada pelos registros citados. |
| **5. T2a-E** | **SURVIVED** | Conferi 102 entradas e 12 com menos de 12 fases. Usa período registrado e duração injetada como proxy declarado. Soupsieve e tornado são registrados por caso. O resultado geométrico vale sob esse proxy. |
| **6. Código** | **REFUTED** | `release_stale` pode apagar um lock novo e vivo por concorrência. `d1p_exit_outcome` ainda aceita cobertura parcial como `route`. As alocações do código satisfazem a margem; `ls-tree -z` corrige os espaços. A verificação de módulos é conservadora, mas não prova fechamento completo de imports. |
| **7. Testes** | **WEAKENED** | Cobrem os pontos nomeados em Q4.11. Não cobrem a corrida de recuperação do lock nem mapas parcialmente vazios. Os resumos falsos exercitam partes úteis, sem demonstrar o fluxo operacional completo. |
| **8. Revisão dos desenhos** | **WEAKENED** | Diagnóstico, geometria e tabela de alocações conferem com os respectivos dados/código. Há excesso na interpretação probabilística, comparação incompleta da ponte, erro na quantidade de chamadas do bootstrap e alocações antigas no ledger em disco. |

**Constatações que sustentam os vereditos**

Na I4, o registro contém **15 reproduções/15 correções de convergência no conjunto fresh**, e **14/14 no v052**. O outro inválido do v052 continua inválido por condicionamento. As maiores diferenças completas são aproximadamente `0,05968` e `0,04091`; as mascaradas ficam abaixo de `4,3e-7`. A maior exclusão do suporte é aproximadamente **2,60%**, abaixo da guarda de 25%. Isso sustenta a causa diagnosticada nesses casos, sem validar a D2.

Na D2-F, `min(p_flag, p_small)` é um limite superior correto para a interseção, usando as probabilidades do mesmo experimento. Conferi **178 índices distintos**, todos com status `OK`, nos registros do passo 7. Os nove índices estritos já contêm os dois INFO; acrescentar os dois DATA resulta em **11**. Os três adicionais da faixa resultam em **14** na contagem superior.

Há, porém, três limites dessa interpretação:

- `p_flag` e a futura probabilidade conjunta são estimados por Monte Carlo. A desigualdade entre probabilidades verdadeiras não transforma estimativas independentes em limites determinísticos da classificação implementada.
- O cálculo preditivo pressupõe uma taxa compartilhada com distribuição Beta e **dois conjuntos de exatamente 178 elegíveis**. A execução admite outra quantidade de elegíveis.
- O gerador v2 altera duração, profundidade e outras grandezas. Não foi demonstrado que essa alteração apenas aumenta os bloqueios.

O JSON registra **0,113865** e **0,314705**. Portanto, nem literalmente são `≤ 0,11` e `≤ 0,31`. São estimativas condicionais, aproximadamente **11,4% e 31,5%**.

**Uma chance próxima de uma em nove pode ser relevante para uma decisão.** Um limite superior baixo pode fundamentar uma regra de futilidade, mas “baixo o suficiente” precisa de justificativa. O estatuto não fornece essa fronteira. A opção conservadora nesta rodada é **não executar a D2-F enquanto o valor de decisão não estiver sustentado**, sem registrar inviabilidade de D2.

O preço também limita o plano: aproximadamente **14,9 CPU-h por conjunto**, incluindo margem e overshoot. A reserva de **21,8 CPU-h comporta A**, mas não os dois conjuntos. Uma futura execução precisa prever como B seria financiado.

**Correções que bloqueiam D1-P e T2a-E**

1. **Eliminar a corrida na recuperação do lock.**  
   Arquivo: [ledger_v055.py:187](C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:187), especialmente a remoção na linha 204.

   Intercalação possível: dois processos leem o lock antigo; o primeiro remove e adquire um novo; o segundo termina sua verificação antiga e apaga o novo lock pelo mesmo caminho.

   **Correção concreta:** serializar aquisição, recuperação e liberação com um mecanismo estável do sistema operacional, verificando a identidade do arquivo protegido antes da remoção. Apenas reler o texto antes de `unlink()` continua deixando uma janela de corrida.

   **Texto do contrato:**  
   “A recuperação remove exclusivamente a instância do lock cuja identidade foi verificada, sob exclusão mútua também respeitada pela criação e liberação. Qualquer dúvida preserva o lock e causa STOP.”

   Registrar a remoção como concluída somente depois de ela ocorrer. Acrescentar teste determinístico dessa intercalação. **Bloqueia ambas as checagens.**

2. **Completar as declarações das funções Win32.**  
   Arquivo: [ledger_v055.py:166](C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:166).

   `OpenProcess` está tipado, mas `GetProcessTimes`, `GetExitCodeProcess` e `CloseHandle` não têm assinaturas explícitas. Isso deixa a passagem de handles dependente das conversões padrão do `ctypes`.

   **Correção concreta:** declarar `argtypes` e `restype` para as três funções, com `HANDLE`, ponteiros de `FILETIME`, ponteiro de `DWORD` e retorno `BOOL`, conforme aplicável. Falha de consulta deve continuar preservando o lock. **Integra a correção do bloqueio comum.**

**Correções que bloqueiam D1-P**

3. **Recusar cobertura parcial nas regras puras.**  
   Arquivo: [r1_common.py:246](C:/Projetos/refute/docs/validation/v0.5.5/r1_common.py:246).

   `cells` ignora mapas vazios. Assim, um conjunto com mapa de famílias vazio pode desaparecer da decisão, enquanto os demais valores permitem `route`. Uma única visão completa também pode retornar `route`.

   **Correção concreta:** exigir as duas visões, os conjuntos A/B e EB1/EB2 em cada conjunto antes de avaliar unanimidade.

   **Texto:**  
   “Cobertura ausente ou incompleta retorna INCONCLUSIVE; route exige as oito células previstas, todas com route.”

   Aplicar a validação correspondente em `d1p_futile_after_first`: uma saída incompleta não pode justificar executar B. Acrescentar testes de mapa interno vazio, visão ausente e família ausente.

4. **Publicar a comparação da ponte no mesmo subconjunto.**  
   Arquivo: [d1p_price.py:563](C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:563).

   Atualmente esse ramo publica o resumo v1 e referencia o resumo A, que contém até 200 tentativas por família. Não produz a leitura v2 restrita aos índices `0..99`.

   **Correção concreta:** ler os registros A desses mesmos índices e publicar v1 e v2 lado a lado, nas duas visões e em todos os preços, incluindo diferenças de elegibilidade. Não restringir silenciosamente a comparação aos elegíveis comuns.

   **Texto:**  
   “A ponte compara os mesmos 100 índices tentados por família em v1 e v2; diferenças de elegibilidade são publicadas. Não produz outcome.”

   Fazer antes de A evita precisar alterar depois o código cuja identidade será comparada entre os registros.

**Ressalvas e correções documentais a registrar**

5. **Reclassificar o resultado probabilístico da D2-F.**  
   Arquivos: [d2f_decision_value.py:19](C:/Projetos/refute/docs/validation/v0.5.5/d2f_decision_value.py:19), `d2f-decision-value.json:12` e [revisão:92](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:92).

   **Texto substituto:**  
   “Estimativa preditiva condicionada ao modelo Beta compartilhado, às classificações históricas utilizadas e a dois conjuntos de 178 elegíveis: aproximadamente 0,113865 na contagem superior e 0,314705 na estrita. Não foi demonstrado limite superior para a execução com gerador v2.”

   Retirar a afirmação de que a mudança do gerador “só pode reduzir” P(route). Preservar o registro atual e publicar a retificação separadamente.

6. **Registrar a decisão de plausibilidade sem criar retrospectivamente um limiar.**  
   Arquivo: [revisão:103](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:103).

   **Texto:**  
   “Não foi demonstrado que route seja implausível pelo estatuto. D2-F permanece sem execução enquanto a justificativa de valor de decisão e o financiamento das duas etapas não forem resolvidos. Esta parada não constitui conclusão sobre a viabilidade de D2.”

7. **Alinhar a condição da correção INFO com a descrição.**  
   Arquivo: [d2f_floor.py:341](C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:341).

   **Correção:** usar `if invalid == [CONVERGENCE_REASON]:`.

   Hoje a checagem mascarada também é calculada quando existem outros motivos inválidos. Eles permanecem, portanto não encontrei conversão indevida para INFO válido, mas o código difere da condição anunciada.

8. **Precisar as direções e preservar explicitamente os limites integrais.**  
   Arquivos: [emenda:49](C:/Projetos/refute/docs/plans/v0.5.5-charter-amendment-1.md:49), linhas 63 e 92.

   **Acrescentar:**  
   “Os tetos pontuais integrais da bateria permanecem P ≤ 0,05 e PG/PV/PA ≤ 0,10, além dos limites superiores de Wilson.”

   Na direção prior versus caixa, usar:  
   “Tendência favorável a route nos resultados históricos citados; sem ordenação geral demonstrada.”

   A comparação entre orçamento residual e orçamento estrito também depende da fração já consumida. Evitar “mais estrito em qualquer caso” sem explicitar a manutenção conjunta das restrições.

9. **Limitar a promessa da verificação FROZEN.**  
   Arquivo: [r1_common.py:65](C:/Projetos/refute/docs/validation/v0.5.5/r1_common.py:65).

   As omissões nomeadas pela revisão foram incluídas, junto da emenda e da revisão. Entretanto, a busca considera módulos carregados globalmente e imports estáticos, inclusive ramos não executados. Pode recusar um processo contaminado por imports alheios à checagem; imports relativos, pacotes locais e carregamentos dinâmicos não são resolvidos integralmente pelo passe estático.

   **Texto:**  
   “Esta é uma guarda conservadora de módulos carregados e imports estáticos reconhecidos, não uma prova geral de fechamento das dependências.”

   No lançamento separado apresentado, não identifiquei um falso bloqueio específico. Manter esse isolamento.

10. **Corrigir custo do bootstrap e distinguir ledger atual de alocação proposta.**  
    Arquivo: [revisão:166](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:166).

    Há **10 níveis distintos**, portanto até **240.000 CDFs por resumo**, não 264.000. A `0,6 ms` por chamada, a extrapolação é aproximadamente **144 CPU-s**.

    A tabela de alocações confere com `ALLOCATIONS`, mas o ledger atual ainda contém `16/16`, `11/11`, `2,5/2,5` e reserva `4,5`, sem a ponte. `guarded_run` chama `declare()` antes do despacho, o que permite atualizar esse estado sem consumo anterior.

    **Texto:**  
    “A tabela descreve as alocações do código revisado. O ledger em disco ainda contém a declaração anterior e será reconciliado sob lock antes do despacho.”

11. **Registrar as três divulgações como proveniência.**  
    Arquivo: `docs/plans/v0.5.5-r1-designs-revision-1.md:10`.

    Registrar os comandos sem afinidade como desvio operacional, sem presumir efeito científico; a estimativa de bootstrap sem afinidade como medição nessa condição; e a substituição do rascunho do JSON como quebra da narrativa de escrita única, embora anterior ao congelamento e sem mudança declarada de 11/14. A versão apagada não pode ser auditada nesta leitura.

**Opção conservadora registrada nesta rodada:** ambas as execuções permanecem paradas pelo lock; D1-P também aguarda as correções de cobertura e ponte. A geometria da T2a-E passou sob o proxy declarado. D2-F permanece sem execução, sem converter essa parada em conclusão de inviabilidade.