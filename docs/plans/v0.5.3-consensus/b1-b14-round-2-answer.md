**As três correções estão presentes. Restam dois problemas no novo caminho parcial.**

1. **[P1] D2/D4 podem emitir PASS com o run incompleto.** [b1_b14.py:402](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:402) também aplica `_records_or_partial` a D2/D4 e calcula os resultados normalmente. Reproduzi: **40 registros favoráveis dos 200 previstos produzem D2=PASS e D4=PASS**, mesmo faltando 160. `part_state` informa a interrupção, mas não impede apresentar esses resultados como o forecast.

   **Correção:** para D2/D4 incompletos, reportar contagens diagnósticas e estado incompleto, sem emitir o PASS/FAIL final do forecast. Manter a leitura parcial de T2a, cujos limites incorporam explicitamente os desconhecidos.

2. **[P2] O fallback também contorna uma recusa de integridade.** [b1_b14.py:285](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:285) captura qualquer `SystemExit`; a leitura seguinte percorre somente os shards esperados. Assim, uma recusa por **sidecar fora do schedule**, exigida em [driver.py:342](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:342), vira um resumo parcial com registros utilizáveis. Reproduzi esse caso em filesystem virtual.

   **Correção:** preservar também a verificação de sidecars inesperados, preferencialmente reutilizando as verificações de `_done`. Ausência ou STOP permite diagnóstico parcial; corrupção ou identidade inconsistente deve continuar sendo recusa.

**Demais pontos conferidos:**

- Os shards esperados têm fingerprint, hash do argumento e SHA-256 verificados; o fallback não reconcilia nem retoma ([b1_b14.py:295](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:295)).
- O guard de índices funciona; o smoke 3000 está explicitado no código e no resumo, preservando o intervalo congelado ([b1_b14.py:191](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:191)).
- Os cinco inputs adicionais existem e entram no fingerprint de T2a ([b1_b14.py:229](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:229)).
- Permanecem corretos os limiares, desconhecidos, derivação de B e resgate por C. Não identifiquei nova seleção baseada em B1.2/B1.3. Caps, lock e STOP de 1.700 s permanecem conectados.

Verificação somente leitura, com reproduções leves em memória. Nenhum run iniciado ou lock alterado.

**WEAKENED, corrigir os dois pontos antes de executar B1.4, após B1.3 e o procedimento exato em #217.**