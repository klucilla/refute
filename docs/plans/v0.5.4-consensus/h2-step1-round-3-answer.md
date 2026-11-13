**As três correções da rodada 2 estão aplicadas. Resta uma proteção numérica antes de congelar a leitura.** Conferência estática em `4755d79`, sem executar o script nem abrir registros por caso.

- **DATA na T2a:** agora exige INCONCLUSIVE e reconhece `inconclusive_class` ou `class`, [step1_floor.py:124](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:124).
- **INFO e REC na D2:** INFO independe da classe I1, exige a linha INCONCLUSIVE e preserva categorias simultâneas. REC exige classe (i) e bound disponível acima do limiar; ausência de bound produz UNK, [step1_floor.py:88](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:88).
- **Os 24 não-grid:** o filtro usa classe (ii) e recusa específica de grade, preserva PROC e MSG+PROC e para se o total divergir de 24, [step1_floor.py:242](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:242), [:259](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:259).

**Correção conservadora restante:** `_below_bound` compara a probabilidade com 0,95 sem verificar se ela é finita e pertence a `[0,1]`, [step1_floor.py:103](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:103). Para `NaN`, a comparação retorna falso, permitindo REC. O escritor protege `power_nuisance` contra valores não finitos, mas não faz a mesma verificação em `sinusoid_small_at_bound`, [i4_bound.py:258](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:258), [:278](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:278).

**Aplicar antes dos overlaps:** retornar `None` para probabilidade ausente, não numérica, não finita ou fora de `[0,1]`. Assim, classe (i) fica UNK, sem promover um bound inválido a INFO ou REC. Não afirmo que esses valores existam nos registros, que continuam fechados.

Nos demais pontos revisados, permanecem corretos a comparação publicada, o cenário fora dos REFUTED e os leitores sem escrita. Com `python -B`, as escritas identificadas continuam limitadas aos destinos previstos. Não identifiquei rerun, alteração de `src/` ou emissão de rascunho.

WEAKENED (validar probabilidades em `_below_bound`; valores inválidos devem resultar em bound indisponível e classe (i) UNK).