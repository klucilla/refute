A página atende à estrutura pedida, mas **as regras de inviabilidade ainda precisam de correções**. Revisão somente leitura, sem executar medições, alterar arquivos ou acessar a pasta proibida.

1. **Atendimento ao pedido**

   Sim: I1 → I2 → I3 → I4 reproduz os quatro primeiros itens da revisão ([closing-review.md:129](/C:/Projetos/refute/docs/validation/v0.5.3/closing-review.md:129)). A pausa descreve pendências, as três questões de `7896ba7` aparecem apenas listadas, e T3b preserva a recomendação condicionada de A. O documento se apresenta corretamente como material para decisão, sem autorização de execução ([página:3](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:3), [54](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:54), [70](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:70), [80](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:80)).

2. **Regras de I1 a I4**

   - **I1, adequada como diagnóstico.** Populações e contagens conferem: 169 perdas de `systematics`, incluindo as 110 com medição, e 37 perdas da D2. Não permite rascunho de inviabilidade. Falta apenas explicitar que a classe de sensibilidade encaminha a I2/I4 e que reprodução divergente, classificação impossível ou defeito termina em **unresolved**, sem excluir silenciosamente casos ([página:29](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:29); [addendum:160](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:160)).

   - **I2, limiar correto, inferência insuficiente.** Precisar de 552/615 significa que **64 perdas comprovadamente irrecuperáveis** bastam, deixando no máximo 551. Porém, poder abaixo de 0,95 impede certificar PASS, não demonstra sozinho impossibilidade de retenção: `systematics` é warning, e um FAIL admissível pode produzir WEAKENED. É necessário demonstrar impossibilidade de **ser mantido**, ou limitar a conclusão à impossibilidade de PASS qualificado ([página:30](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:30); [battery_v51_diff.py:573](/C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:573); [verdict.py:238](/C:/Projetos/refute/src/refute/core/verdict.py:238)).

     Além disso, definir separadamente o conjunto limitado em cada família e sua interseção. Hoje `U` já significa “sob todas”, mas reaparece “sob cada família”, deixando ambígua a divergência. Congelar ordens ARMA, kernels, seleção, adequação e tratamento de ajustes inválidos antes da leitura. **O condicionamento ao modelo e a recuperação otimista dos demais bloqueadores estão corretamente declarados**, mas não resolvem o problema warning.

   - **I3, incompleta para rascunho de D1.** Acerta ao recuperar a cláusula “não mais SURVIVED que v0.4” e reconhecer que warning FAIL pode preservar planetas na D2. Entretanto, o gatilho fatal pode declarar rascunho enquanto essa alternativa permanece aberta. **Uma possibilidade warning ou INCONCLUSIVE ainda admissível deve impedir o rascunho geral de D1**, mesmo que sua construção volte ao mantenedor ([página:31](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:31); [closing-review.md:67](/C:/Projetos/refute/docs/validation/v0.5.3/closing-review.md:67)).

     Também faltam D4, uma definição inequívoca da probabilidade de satisfação **conjunta** e o alcance da grade. Três níveis não esgotam automaticamente as abordagens possíveis; B0 contém ainda 0,00135 ([d1_bound.py:62](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_bound.py:62)). A conclusão negativa precisa ficar restrita à classe examinada, salvo demonstração de que ela cobre as alternativas restantes.

   - **I4, limiar correto, contador incorreto.** Para 178 elegíveis, são necessários 156 mantidos; **23 irrecuperáveis** deixam no máximo 155. Mas somar perdas do residual `sinusoid` a `L` confunde PASS qualificado com retenção. A etapa A diz expressamente que esse warning permanece recuperável para retenção ([página:32](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:32); [d2_bounds.py:5](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:5)). Separar os dois contadores.

     Acrescentar **unresolved** para Fisher singular, modelo inadequado ou cálculo inválido, evitando que “otherwise route” absorva esses casos. Repetir explicitamente o condicionamento ao modelo e às hipóteses de Cramér–Rao, incluindo a classe de estimadores. A recuperação otimista dos demais bloqueadores está declarada corretamente.

   **Nenhuma dessas correções exige mudar metas, severidades ou regras congeladas.**

3. **Preços e calendário**

   **Ordem de grandeza plausível, sem validação dos novos custos.** I1 é compatível com os aproximadamente 95–267 CPU-s por injeção/bateria e 140 CPU-s por curva para três baterias, embora dividir esses custos não isole a versão 5 ([stop-report:149](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report.md:149), [166](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report.md:166)). I3 tem boa referência nos 2,451 CPU-h por 800 binárias ([b0b-record:60](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b0b-record.md:60)). I2 com duas famílias e I4 continuam estimativas de engenharia.

   Os totais conferem: CPU soma 14,5–34 h, arredondada para 15–35; tokens, 1,6–2,6 M; dias-agente, 5,5–8,5. Os tokens são compatíveis com conversas históricas de aproximadamente 87–286 mil, mas convém declarar quantas revisões sustentam a projeção ([caps.json:1173](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/caps.json:1173)).

   O calendário é honestamente chamado de estimativa e condiciona a retomada à liberação. Corrigir ou fundamentar **“4,5 dias úteis”**: de sexta 13/11 a quarta 18/11 há quatro datas úteis. Explicitar horário inicial, horas por dia-agente e a regra segunda a sexta, 08–18h. Pausa em 18/11 às 20h e retomada somente mediante liberação estão preservadas ([página:39](/C:/Projetos/refute/docs/plans/v0.5.3-after-round3-decision.md:39); [desenho B1:492](/C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:492)).

4. **Fontes**

   Não encontrei erro material de título, autoria ou URL nas quatro referências. Jones e Foreman-Mackey informam adequadamente as famílias de modelos; Carter traz corretamente a ressalva sobre limb darkening; Seager usa o título publicado em 2003, embora o preprint tenha título diferente. São referências de desenho, **não validação dos limites propostos**. Conferência: [Jones](https://www.tandfonline.com/doi/abs/10.1080/00401706.1980.10486171), [Carter](https://arxiv.org/abs/0805.0238), [Seager](https://doi.org/10.1086/346105).

**WEAKENED (corrigir os contadores de retenção de I2/I4, completar a regra conjunta e as alternativas de I3, explicitar saídas unresolved e fundamentar os 4,5 dias úteis).**