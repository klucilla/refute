**Correções confirmadas. Não encontrei novo erro no escopo desta rodada.**

- **E4:** a classificação agora distingue corretamente chamada sem medição concluída de fallback. Reconfirmei **17 casos T2a e 1 D2**, além da execução de janelas quadráticas nos 17 T2a. [b1_blockers_decisive.py:132](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:132), [adendo:160](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:160).
- **Limite da evidência:** conferem os **107 insufficient sensitivity e 3 not enough data** entre as 110 medições. O texto corretamente evita atribuir o resultado à potência do background. [adendo:166](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:166).
- **E2/D2:** confirmados **21 INCONCLUSIVE e 1 FAIL**, este no planeta **3129**, entre as 22 perdas atribuídas em que E2 operou. [adendo:178](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:178).
- **Inventário:** `forecast-paths.md` foi acrescentado com classificação correta, sem diagnósticos contados como bloqueadores. [adendo:195](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:195).
- **Bloqueador único:** a definição agora explicita sua relação com o ramo aplicado de `aggregate`; a ressalva sobre ausências também está registrada. [script:33](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:33), [adendo:73](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:73).

A recomputação reproduziu **exatamente** as seções T2a e D2 do JSON atualizado. Permanecem `K_B = 331`, `U_B = 0`, C = 373/615 e D2 FAIL/D4 PASS no conjunto completo. Nenhum arquivo foi alterado nesta revisão.

SURVIVED