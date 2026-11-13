**A proposta atende ao item 4a em intenção, mas precisa de correções antes de qualquer leitura dos overlaps. O script não implementa integralmente o desenho.** Revisão estática em `9742a96`, sem execução, rede, alterações ou acesso aos registros vedados.

**1. Desenho e resultados já previsíveis**

A união por curva, os denominadores, a separação entre perda atual e limite informacional, o cenário C condicionado e a proibição de rascunho estão presentes em [v0.5.4-h2-step1-floor.md:50](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:50), [:65](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:65) e [:84](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:84).

Faltam, porém, estas ressalvas explícitas:

- **T2a em B já terá margem esgotada segundo DATA:** os 20 `systematics/not_enough_data` excedem 7, independentemente dos overlaps. Isso decorre das próprias definições e marginais divulgadas, [plano:17](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:17), [:41](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:41). Não é nova evidência de inviabilidade.
- **D2 não pode atingir o ramo `F_strict > 22` com esses marginais.** Mesmo somados conservadoramente, DATA e os limites I4 ficam abaixo de 23. A novidade possível está nas uniões e em `F_upper`, não nesse esgotamento. A divulgação também omite o DATA de `systematics`, [b1-blockers-decisive.json:87](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-blockers-decisive.json:87).
- **`F_upper` não é um limite superior demonstrado de perdas inevitáveis.** Exclui REC e PROC, embora potência permitida pelo bound e procedimento potencialmente corrigível não demonstrem recuperação conjunta. “Margem sob toda hipótese” exige assumir explicitamente essa recuperação ou manter `INCONCLUSIVE`, [plano:47](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:47), [:62](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:62), [:68](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:68).
- **Uma categoria por teste precisa de regra para causas simultâneas.** Há mensagens contendo tanto erro procedural quanto ausência de trânsito. Fixar apenas PROC pode apagar MSG. Esses casos já estão publicados, [i1-diagnosis.json:299](C:/Projetos/refute/docs/validation/v0.5.4/i1-diagnosis.json:299). A precedência deve ser congelada antes dos overlaps.

**2. Correções necessárias no script**

1. **Chamada inexistente, impede concluir a execução.**  
   [step1_floor.py:147](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:147) chama `b1_b14.b1_d2d4_rest.complete_records()`. `b1_b14` não expõe esse módulo. Usar `i4_bound.b1_d2d4_rest` ou importação explícita, como faz o próprio [i4_bound.py:40](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:40).

2. **Campo de classe da D2 incorreto.**  
   `_cls` procura `inconclusive_class` ou `metrics`, mas `v5_tests` grava **`class`**, [step1_floor.py:63](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:63), [forecast_v4.py:89](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_v4.py:89). Isso perde especialmente o DATA de `systematics`, que I1 não classifica na D2. O escritor tampouco preserva `inconclusive_detail`; a recuperação de RULE depende corretamente do `why` de I1.

3. **Recusa da T2a procurada no lugar errado.**  
   Está em **`brief["selection"]["refused"]`**, não na linha de `brief["tests"]`, [forecast_t2a.py:277](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a.py:277). Em [step1_floor.py:116](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:116), isso deixa recusas de `odd_even` como UNK, pois I1 só classifica `systematics` na T2a. Os briefs também não preservam `inconclusive_detail`; manter a ambiguidade da senoide como UNK é conservador, sem reconstruí-la pela classe genérica.

4. **Testes ocultos e ordem das categorias incompletos.**  
   A D2 acrescenta os testes de I1 atrás do fatal; a T2a não faz isso, [step1_floor.py:159](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:159), [:195](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:195). Além disso, DATA retorna antes da inspeção da mensagem, e PROC antes de MSG, [:71](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:71), [:114](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:114). Isso não preserva causas simultâneas nem produz a decomposição específica dos **24 não-grid classe (ii)** exigida pelo plano.

5. **Cenário das duas perdas adicionais calculado incorretamente.**  
   [step1_floor.py:220](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:220) subtrai de 2 o piso de todas as perdas, incluindo REFUTED. Deve comparar **somente o piso fora dos cinco REFUTED com 2**, ou comparar a união desse piso com os cinco REFUTED contra 7. A fórmula atual desconta novamente perdas já reservadas.

6. **Integridade, joins e stops ficam aquém do congelado.**  
   `verified_records` verifica SHA-256, mas não fingerprint, argumento, agenda nem completude, ao contrário de `driver.Run._done`, [step1_floor.py:45](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:45), [driver.py:335](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:335). Faltam rejeição de duplicatas I1/T2a, `kind` inesperado, whitelist de ausências e comparação dos bloqueadores reproduzidos com o agregado publicado. Na T2a, desconhecidos podem substituir perdas na checagem `559/228`, mas ficam fora dos pisos, [step1_floor.py:189](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:189), [:205](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:205). Isso pode diminuir artificialmente os totais.

**3. O que está correto e os limites de escrita**

Os joins pretendidos por `index`, `(key, slot)` e `kind` correspondem aos escritores. Os campos I1 `tests[name].class/why` e I4 `power_nuisance`, `sinusoid_small_at_bound`, `nuisance.invalid` estão nomeados corretamente. `non_detectable` não é usado. A checagem `178/37`, a manutenção de 3129 no denominador e o uso de `_ledger(ledger_b)` estão corretos, [step1_floor.py:146](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:146), [:237](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:237).

**Não há chamada de rerun, alteração deliberada de `src/` ou emissão de rascunho.** As escritas explícitas ficam nos dois destinos permitidos, [:248](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:248), [:269](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:269). Para garantir literalmente nenhuma escrita adicional, a execução documentada precisa de `python -B`, pois imports podem gerar `__pycache__` fora deles.

WEAKENED (corrigir chamada, campos, precedências, testes ocultos, cenário dos REFUTED, integridade e interpretação de F_upper; congelar novamente antes dos overlaps).