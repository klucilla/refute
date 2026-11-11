**As correções da rodada 2 conferem. Resta uma falha de completude nas referências.**

- **[P2] `stage_a_raw` aceita shards ausentes.** Em [b1_forecast.py:621](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:621), verifica os arquivos encontrados, mas não exige os 31 índices esperados nem rejeita duplicatas. Confirmei isoladamente: sem shards, retorna `{}`. Depois, [linha 783](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:783) produz `error_ratios=null`, sem STOP. **Opção conservadora:** antes do dispatch, exigir exatamente os 31 índices das perdas históricas, únicos, `OK`, com os limites utilizados finitos e positivos. Ausência ou inconsistência deve parar B1.2.

**Verificado nesta rodada:**

- A subtração de `e1.still_undefined` agora distingue tentativa de conclusão. A contraprova com todas as conclusões indefinidas gera STOP.
- As razões usam corretamente o erro GLS ou o erro reconstruído no fallback. `aperture_depth` e as profundidades odd/even estão incluídos.
- Os **31 registros brutos atuais** estão completos, todos `OK`, sem quarentena, com limites numéricos e SHA-256 conferindo com os sidecars.
- Para `difference_sigma=0`, retornar `null` é conservador. Esse caso deve permanecer indeterminado, sem inferir ganho.
- Não encontrei novo bloqueio no candidato compartilhado, caps, fingerprint, disco ou isolamento de B1.3/B1.4. A conclusão continua dependendo de `screen-summarize` sem STOP.

Somente leitura e verificações pequenas de funções isoladas. Nenhum ataque executado, lock adquirido ou acesso ao caminho proibido.

**WEAKENED (exigir a completude dos registros brutos antes do run).**