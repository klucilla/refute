## 1. Definição e cálculo

**Corretos para os registros atuais, com uma correção necessária nos estados de E4.**

- **T2a:** usa `decisive − deferred`, respeita severidade e prioriza gate e fatal FAIL. B seleciona C até 20 setores medidos e A acima; a ausência de A acima de 20 é registrada como recusa. Conferido em [b1_blockers_decisive.py:76](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:76) e [linha 228](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:228).
- **D2:** o conjunto decisivo coincide com o plano; não há adiamentos, gates reprovados nem decisivos ausentes nos 178 elegíveis. A inferência sobre warning FAIL em perdas INCONCLUSIVE é válida. Nos REFUTED observados, há exatamente um FAIL decisivo por registro, tornando sua atribuição inequívoca. [b1_blockers_decisive.py:106](/C:/Projetios/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:106).
- **Consistência:** os quatro agregados comparados com `b1-forecast.json` conferem. Essa verificação cobre A, B e C nos agregados declarados, não cada célula por estrato. [b1_blockers_decisive.py:281](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:281).

Duas precisões: o código junta ausências e INCONCLUSIVE, enquanto `aggregate` retorna primeiro pelas ausências. Não afeta estes registros, pois nenhuma ocorre. E “único bloqueador” significa **único no ramo prioritário do veredito atual**: remover um fatal FAIL pode revelar INCONCLUSIVE antes encobertos.

## 2. Números e correções do adendo

Recalculei `t2a()` e `d2()` pelos leitores que verificam os registros e sidecars: **igualdade exata com o JSON entregue**. Também reagreguei independentemente os resultados normalizados da T2a, sem divergências.

Conferem:

| Resultado | Confirmado |
|---|---:|
| T2a B | `K_B = 331`, `U_B = 0`, resposta **não** |
| C | 373/615 mantidos |
| T2a B, bloqueadores | systematics 169; sinusoid 95; odd_even 89; period_alias 17 |
| Bloqueador único, pela prioridade definida | 121/228 |
| D2 versão 5 | 141/178 mantidos, **FAIL** |
| D4 versão 5 | 7/122 INCONCLUSIVE, **PASS** |

Os totais de A/C, recusas, conjuntos e what-ifs também conferem. Recalculei as recuperações T2a **72/124/211/228** e D2 **9/8/33/34**, considerando os demais resultados decisivos. A identificação como what-if está adequada. A conclusão D2/D4 coincide com a recomputação dos 200 registros.

**Correções necessárias:**

1. **E4 sem `measured` não significa fallback à versão 4.**  
   [_estimator_state:128](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:128) atribui esse rótulo indevidamente. E4 pode retornar `None`, sem chamar o estimador anterior. [battery_b1.py:602](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:602).  
   Na tabela do [adendo:157](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:157), substituir **17 T2a e 1 D2 “fell back”** por **“chamado, sem medição concluída”**. Todos esses 18 registros executaram janelas quadráticas. Manter fallback por janela como contador separado.

2. **O estado composto de `systematics` não demonstra que o background falhou em potência.**  
   Dos 110 com `e4.measured`, 107 ficaram `insufficient_sensitivity` e 3 `not_enough_data`. Isso não identifica qual subchecagem impediu o resultado. Restringir a conclusão do [adendo:163](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:163) ao que esses registros comprovam.

3. **E2/D2: são 21 INCONCLUSIVE e 1 FAIL entre os 22 atribuídos.**  
   Corrigir “INCONCLUSIVE in 22” no [adendo:173](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1-stop-report-addendum.md:173). O registro 3129 tem `e2.gls = 1` e `odd_even FAIL`.

## 3. Tabelas anteriores

**Não encontrei outra lista afetada pela inclusão de diagnósticos.** A classificação das duas listas B1 e a distinção do problema separado de warning FAIL estão corretas.

Para tornar o inventário completo, acrescentar **`stage2/forecast-paths.md`**, que apresenta contagens de bloqueadores e tabelas de remoção em [linha 42](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast-paths.md:42) e [linha 97](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast-paths.md:97). Classificação: **não afetado por diagnósticos**, deriva das leituras decisivas já relacionadas.

Nenhuma alteração foi feita.

**WEAKENED (com as correções acima).**

