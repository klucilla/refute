**Rodada 2: os bloqueios técnicos da rodada 1 foram resolvidos.** Não identifiquei bloqueio remanescente à D1-P ou à T2a-E no escopo revisado. Permanecem duas correções de descrição, sem impacto identificado nos resultados ou no orçamento planejado.

A **D2-F continua sem execução**. A insuficiência da justificativa de plausibilidade foi corretamente registrada, sem concluir inviabilidade de D2.

Fiz somente leitura local. O [JUnit apresentado](C:/Projetos/refute/.cache/v055/junit-v055-h.xml:1) registra **47 testes, zero falhas, zero erros e zero pulados**. Não executei testes nem scripts. HEAD permanece em `cd92c48`; não existem os diretórios de shards das três checagens.

**Vereditos por item**

| Item | Veredito | Fundamentação |
|---|---|---|
| **1. I4** | **SURVIVED** | Mantidos diagnóstico restrito, reprodução, tolerância, passos, derivadas e guarda de suporte. Leitura histórica protegida e restaurada por `finally`, sob uso serial. |
| **2. D2-F** | **SURVIVED** | Como redesenho diagnóstico não executado. Correção INFO agora exige exclusivamente a falha de convergência. Desconhecidos, potência inválida separada, variante combinada, unidade própria e futilidade preservados. As probabilidades estão expressamente retificadas como estimativas condicionais. |
| **2-plausibilidade** | **SURVIVED** | Sobrevive o texto corrigido: **não foi demonstrado que route seja implausível**. A conclusão anterior foi retirada; execução e financiamento permanecem pendentes da decisão reservada ao mantenedor. |
| **3a. WEAKENED** | **SURVIVED** | `0,05` por teste, `0,10` apenas cenário e mudança de unidade explícita. |
| **3b. REFUTED** | **SURVIVED** | Orçamento estrito e residual mantidos conjuntamente, com os tetos pontuais e Wilson da bateria. A extensão às linhas PG/PV/PA continua conservadora e declarada. |
| **3c. Geradores e ponte** | **SURVIVED** | Confirmação futura com v1 preservada. Ponte compara os mesmos índices `0..99`, publica as duas versões e diferenças de elegibilidade/veredito, sem selecionar apenas elegíveis comuns ou produzir outcome. |
| **3d. Convenções** | **SURVIVED** | Direção prior versus caixa agora qualificada; comparação entre orçamentos corrigida; alteração da I4 com resultados conhecidos permanece divulgada. |
| **3e. Padrão de prova** | **SURVIVED** | Quatro elementos adicionais preservados, sem substituir a regra de avanço. |
| **3f. R2** | **SURVIVED** | Cegueira por bundle controlado e duas agregações preservadas. Não decide a futura regra. |
| **4. D1-P** | **SURVIVED** | Oito células obrigatórias; cobertura incompleta retorna INCONCLUSIVE. B exige as quatro células de A. Ponte, preços, cenários e zero sobreviventes conferem. Prior de planejamento identificado como opinião. |
| **5. T2a-E** | **SURVIVED** | Contagem geométrica permanece 12/102 sob o proxy declarado. Registro dos pacotes por caso preservado. |
| **6. Código** | **SURVIVED** | Guarda estável serializa criação, recuperação e liberação; identidade é reconferida; remoção é registrada depois; Win32 está tipado e falhas mantêm o lock. A corrida anterior está fechada entre participantes que respeitam esse protocolo. |
| **7. Testes** | **SURVIVED** | Cobrem Q4.11 e as regressões de cobertura, ponte, identidade e guarda. Ressalva: o teste anunciado como concorrência entre processos usa dois descritores no mesmo processo. |
| **8. Revisão dos desenhos** | **WEAKENED** | Retificações probabilísticas, proveniência e ledger antigo estão corretamente documentados. Resta divergência no custo do resumo da ponte: o código atualmente calcula três blocos, não dois. |

**Bloqueios à D1-P e à T2a-E**

**Nenhum identificado nesta rodada.** Permanecem aplicáveis o congelamento da identidade e o procedimento já determinado antes de cada execução, dez workers, afinidade, tetos e uma retomada por parte. Este parecer não executa nenhuma etapa.

**Correções restantes, não bloqueantes**

1. **Corrigir a estimativa do resumo da ponte.**  
   Arquivos: [d1p_price.py:557](C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:557), [d1p_price.py:517](C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:517) e [revisão:192](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:192).

   `_summarize("bridge")` calcula as famílias v1 no fluxo geral. Depois `_bridge` calcula novamente v1 e calcula v2. Com ambas as visões disponíveis, são até **720.000 CDFs**, aproximadamente **432 CPU-s** na extrapolação declarada.

   **Texto substituto:**

   > “Cada resumo ordinário calcula até 240.000 CDFs, aproximadamente 144 CPU-s. Na implementação atual, o resumo da ponte calcula três blocos, incluindo a repetição de v1: até 720.000 CDFs, aproximadamente 432 CPU-s.”

   Isso não estoura a reserva no plano apresentado: A, B e ponte somam aproximadamente **0,20 CPU-h** de bootstrap; com as cobranças atuais de **0,112426 CPU-h**, ficam aproximadamente **0,312426 CPU-h**, antes dos demais custos de resumo, dentro dos `0,5 CPU-h`. É extrapolação, não medição do resumo completo.

2. **Descrever corretamente o teste da guarda.**  
   Arquivo: [test_ledger_v055.py:114](C:/Projetos/refute/tests/v055/test_ledger_v055.py:114).

   O teste abre outro descritor e chama `_try_lock` no mesmo processo. Não cria um segundo processo.

   **Texto substituto para o docstring:**

   > “Durante a recuperação, uma segunda abertura independente do arquivo de guarda, no mesmo processo, não consegue adquirir a guarda já mantida. Este teste não executa concorrência entre dois processos.”

   A exclusão entre processos é sustentada aqui pela implementação da primitiva do sistema operacional e pela revisão estática, sem um ensaio entre processos neste teste.

3. **Manter explícito o alcance da retificação da D2-F.**  
   A [retificação na revisão:104](C:/Projetos/refute/docs/plans/v0.5.5-r1-designs-revision-1.md:104) está adequada. Os nomes antigos do JSON e suas afirmações devem continuar sendo interpretados por ela. **Não é necessário reescrever o registro.**

**Registro conservador desta rodada:** correções impeditivas da D1-P e T2a-E **SURVIVED**; custo da ponte deve ser descrito conforme o código; D2-F permanece sem execução, sem classificação demonstrada de “route implausível” e sem conclusão sobre inviabilidade de D2.