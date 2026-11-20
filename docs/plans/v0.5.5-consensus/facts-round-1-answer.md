**A ressalva central procede:** “nenhuma precisão basta” precisa ficar restrito a **α = 0,0027, sob as hipóteses de B0**. Em α = 0,05, todas as combinações do passo 4 deixam expectativas inferiores a 10. Isso não demonstra PASS da bateria nem controle conjunto dos falsos `REFUTED`.

Conferência exclusivamente local, sem rede, alterações ou execução dos experimentos. Recalculei apenas aritmética em memória. Opiniões, probabilidades opinativas e parâmetros propostos para trabalho futuro ficam fora dos vereditos.

Para compactar as referências, todos os caminhos abaixo partem de `C:\Projetos\refute`:

- `S/` = `src/refute/packs/tess/`
- `P/` = `docs/plans/`
- `V3/` = `docs/validation/v0.5.3/`
- `V4/` = `docs/validation/v0.5.4/`
- `R` = `calibration/v0.5/runs/c1-confirmation/report.json`
- `acc` = `P/v0.5-acceptance.md`
- `pause` = `V4/pause-record.md`
- `B0` = `V3/stageB/README.md`

**D1**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| D1 §1 | EB1: 35/190; EB2: 40/186; franquia 10; precisam sair pelo menos 25 e 30 | ACEITO | Contagens em `R:17-31`; franquia em `B0:54-56`. Subtrações conferidas. |
| D1 §1 | D1 conta somente `SURVIVED`; `SURVIVED + WEAKENED` não tem meta | ACEITO | `S/calib05/c1.py:641-649`; `acc:420-422`. |
| D1 §1 | FAIL fatal, FAIL warning ou INCONCLUSIVE retiram `SURVIVED` | ACEITO | São saídas suficientes; prevalecem as precedências do agregador. `src/refute/core/verdict.py:250-276`. |
| D1 §1 | REFUTED limitado a 0,05 em P e 0,10 em PG/PV/PA | ACEITO COM RESSALVA | São limites da **bateria na população elegível**, acompanhados por limites superiores de Wilson de 0,10 e 0,20. Não são níveis automaticamente atribuídos a cada teste. `S/calib05/c1.py:664-682`. |
| D1 §1 | INCONCLUSIVE custa retenção/D4; WEAKENED não tem teto | ACEITO COM RESSALVA | Correto para as regras C1 D1–D4 examinadas. D2 impõe retenção relativa à v0.4; D4 incide somente no subconjunto SNR ≥ 15. `S/calib05/c1.py:654-690`. |
| D1 §1 | Alternativa de odd/even = uma profundidade; contraste relativo EB2 = 0,105–0,667 | ACEITO COM RESSALVA | Alternativa confirmada em `calibration/v0.5/claim.yaml:246` e `S/battery_v52.py:151`. O contraste é `2(1−r)/(1+r)`, com `r∈[0,5;0,9]`, definido em `S/calib05/c1.py:290`. A referência `:289` aponta para SNR. |
| D1 §1 | PASS qualificado é compatível com qualquer membro EB2 | ACEITO COM RESSALVA | A qualificação testa potência para uma alternativa maior que os contrastes EB2; não garante detectabilidade desses contrastes. Isso também não significa que todos os EB2 recebam PASS. `S/battery_v52.py:151-157,176-186`. |
| D1 §1 | B0: 29,2/35,5 em 0,0027; 14,1/12,5 em 0,05; estrela conhecida: 4,6/4,1 | ACEITO | Valores publicados, arredondados, em `B0:63-68`. São expectativas de não rejeição, não contagens de SURVIVED. |
| D1 §1 | Passo 3: rejeição 44%/27%, com rejeição planetária 8,5%; oráculo acima de 92% em 0,05 | ACEITO | Valores realizados: 0,44094488; 0,27077748; 0,08510638 em `V4/h2-step3-i3.json:154-158`. Comparador do oráculo em `B0:65`, condicionado às suas hipóteses. |
| D1 §2 | C1 não mede falsos REFUTED decorrentes de excentricidade ou catálogo estelar deslocado | ACEITO COM RESSALVA | O gerador examinado não sorteia esses efeitos. Isso limita o domínio da validação; “fatal não pode ser validado em C1” é mais amplo que o demonstrado. `S/calib05/c1.py:77-92,205-221,366`. |
| D1 §2 | Distâncias B0 independem do nível; fornecem a fração mínima de SURVIVED | ACEITO COM RESSALVA | A distância pode ser relida em outros níveis, mas fornece um limite de **não rejeição sob hipóteses específicas**. Não é um mínimo atingível de SURVIVED para uma bateria composta. `B0:44-60,97-100`. |
| D1 §2 | Sob a caixa, em 0,05, ficam 12–14 contra franquias 10 ou 11 | ACEITO COM RESSALVA | O intervalo resume B0/B0b, mas omite a franquia **9 de EB2 em B0b**. B0b: expectativas 12,0/13,1 e franquias 11/9. `V3/stageB/b0b-record.md:22,30`. |
| D1 §2 | Resultado com prior gaussiano fica entre 4,6 e 14,1 | REJEITADO | Esses extremos pertencem a outros tratamentos da estrela. Os registros não demonstram esse intervalo para o procedimento gaussiano ainda não calculado. `B0:63-68`; `P/v0.5.5-fable-core-plan.md:63`. |
| D1 §2 | Âncoras de custo: B0 2,45 CPU-h/800; bateria aproximadamente 15 CPU-h/800 | ACEITO COM RESSALVA | Primeira âncora medida; segunda estimada. Para dois conjuntos de 800, a extrapolação simples soma aproximadamente 34,9 CPU-h. A faixa 35–45 continua sendo estimativa. `B0:16`; `P/v0.5.4-h2-step2-i3-increment.md:39-41`. |
| D1 §2 | Perfil trapezoidal, AR(1) com escala de uma hora; P teve 8/186 WEAKENED | ACEITO | `S/calib05/c1.py:47,242-249,380-384`; `R:620-627`. |
| D1 §2 | INCONCLUSIVE do novo teste bloqueia; massa/raio podem faltar em estrelas reais | ACEITO COM RESSALVA | Bloqueio e campos opcionais confirmados. O resultado de um futuro teste quando faltarem parâmetros ainda não está implementado. `src/refute/core/verdict.py:268-270`; `S/types.py:61-64`. |
| D1 §3 | Uma atribuição universal WEAKENED satisfaz D1–D4 | ACEITO COM RESSALVA | Correto como contraprova algébrica usando somente essas metas, com denominadores decidíveis. Não prova admissibilidade de tal bateria pelas demais regras. `S/calib05/c1.py:633-690`. |
| D1 §3 | Saída INCONCLUSIVE tem teto absoluto de 0,10 por D2 | REJEITADO | D2 permite queda de **0,10 relativamente à retenção v0.4**. Não fixa um teto absoluto de INCONCLUSIVE nem um orçamento isolado por teste. No conjunto de 178, são permitidas 22 perdas totais. `S/calib05/c1.py:654-669`; `V4/h2-step1-floor.json:22-36`. |
| D1 §3 | B0 exige controle por planeta na caixa; B0b exigiu os dois níveis e deu medianas 0,452/0,102 | ACEITO | `B0:44-50`; `V3/stageB/b0b-record.md:30,36-56`. A inversão da ordem das famílias entre conjuntos também está registrada. |
| D1 §3 | Passo 3 exigiu D1 sozinho; a bateria anterior já retirava 155/190 e 146/186 de SURVIVED | ACEITO COM RESSALVA | Subtrações corretas na confirmação v0.5. Os binários de B0 usados pelo passo 3 são outro conjunto; sua ajuda conjunta não foi medida. `R:17-31`; `P/v0.5.4-h2-step2-i3-increment.md:36-46`. |
| D1 §3, aritmética | 5% de EB1 têm razão > 0,96 e contraste abaixo de 0,6σ em SNR 30 | ACEITO COM RESSALVA | Parcela de 5% correta. Na fronteira 0,96, a fórmula usada dá **0,6122449σ**; para ficar abaixo de 0,6σ, exige `r>0,9607843`. Os 5% são da distribuição geradora, não necessariamente dos elegíveis. `S/calib05/c1.py:265`; `B0:54`. |
| D1 §3, aritmética | Aproximadamente metade de EB2 fica abaixo de 3σ | ACEITO COM RESSALVA | Integrando a fórmula branca declarada nas distribuições uniformes, obtenho **51,63324749%**. A expressão não constitui limite demonstrado para qualquer estimador ou para ruído correlacionado. `S/calib05/c1.py:285-292`. |
| D1 §3, aritmética | Alternativa 0,105 exige SNR ≈ 88; alternativa 0,667 perde aproximadamente 30% de P | ACEITO COM RESSALVA | Com erro do contraste `2D/SNR` e potência 0,95 a 3σ: SNR **88,25221891** para `2/19`; para `2/3`, SNR **13,93456088**, deixando **29,84524402%** abaixo. Premissas brancas simplificadas. `src/refute/core/sensitivity.py:264-276`; `acc:371`. |
| D1 §3 | Esses cálculos constituem um lema rigoroso de incompatibilidade com D2 | REJEITADO | Não demonstram um limite para todos os estimadores, a população elegível e as saídas conjuntas da bateria. A aritmética condicional não sustenta a generalização. `P/v0.5.5-fable-core-plan.md:83-85`. |
| D1 §3 | Passo 4 só congelou desfechos em 0,0027; em 0,05 fica entre 4,9 e 8,6 | ACEITO | `P/v0.5.4-h2-step4-b0-errors.md:49-58`; valores exatos na tabela final. Em 0,01 e precisão 1%, são 9,99543758 e 9,54784654. |
| D1 §3, aritmética | Limiares de impacto ≈ 0,61/0,27; parcelas 24%/67%; planeta mimético até ≈ 0,65 | ACEITO COM RESSALVA | Na aproximação geométrica usada: **0,60830870 / 0,26747015**, parcelas **23,9614% / 66,5662%**, máximo **0,65462632**. Conferi usando a caixa de raio efetivo. Não é igualdade exata da duração com raio finito nem da forma completa. `S/calib05/c1.py:83-91,239,287`; `docs/validation/v0.5.1/feasibility/d1_routes.py:81-84`. |
| D1 §3, aritmética | Multiplicar pela metade dá aproximadamente 12%/33%, comparável a B0 6%/19% | ACEITO COM RESSALVA | Produtos aproximados corretos: 11,98%/33,28%. B0 conhecido dá aproximadamente 6% em 0,0027; catálogo EB2, aproximadamente 19%. A comparação não demonstra indistinguibilidade conjunta. `B0:63-67`. |

**D2**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| D2 §1 | 178 elegíveis, 37 perdas, máximo 22 | ACEITO | `V4/h2-step1-floor.json:22-36`; v0.4 retém 173 e versão 5 retém 141 em `V3/stageB/b1-forecast-d2d4-complete.json:18,52,63`. |
| D2 §1 | Oito perdas pelo ramo de sinusóide ambígua | ACEITO | Contagem em `V4/i1-diagnosis.json:119-121`; semântica em `S/battery_v52.py:411-430`. |
| D2 §1 | Nove certificados falham no oráculo; três incertos; warning INCONCLUSIVE bloqueia | ACEITO COM RESSALVA | Contagens corretas. Falha do certificado não equivale a perda inevitável de retenção. `V4/h2-step7-sinusoid.json:5-49`; `P/v0.5.4-h2-step7-sinusoid.md:67-79`. |
| D2 §1 | Somente dois planetas são limitados por informação de odd/even | ACEITO COM RESSALVA | Dois demonstrados entre 177 considerados por I4; há **15 inválidos**, além da exclusão de 3129 daquele L. “Somente” não resolve os desconhecidos. `V4/i4-bound.json:3,166-179`; `V4/record-defects.md:51-65`. |
| D2 §1 | 25 perdas classe (i), potência 0,63–0,95 | ACEITO | Valores exatos: mínimo 0,62529026, máximo 0,94547773. `V4/i1-diagnosis.json:3-9`. |
| D2 §1 | E2 mediana 1,44 do limite; janelas/caixa aproximadamente 1,17 | ACEITO COM RESSALVA | 1,44 refere-se a **28 razões finitas em perdas anteriores selecionadas**. O 1,17090143 vem de outra amostra e variante Fisher; não é decomposição quantitativa demonstrada daquele 1,44. `V3/closing-record.md:151-155`; `V4/h2-step5-gap.json:28-37`. |
| D2 §1 | Dois DATA e dois limites odd/even; pisos 8/16/21 | ACEITO COM RESSALVA | Contagens corretas, condicionadas às categorias e hipóteses. O INFO agregado tem oito bloqueadores em seis planetas. `V4/h2-step1-floor.json:23-33`; `P/v0.5.4-h2-step1-floor.md:61-87`. |
| D2 §1, aritmética | União dos passos 1 e 7 colocaria F_rule entre 19 e 22 | ACEITO COM RESSALVA | União conferida no arquivo por caso, com hash correspondente: **20**, ou **22 incluindo os incertos**. Continua sendo união condicional de classificações. `V4/h2-step1-floor.json:71`; `.cache/v054/step1/cases.json:142,224,320,342,498,520,542,579,616`; `V4/h2-step7-sinusoid.json:5-49`. |
| D2 §2 | Âncoras: 0,039 CPU-h/curva; passo 7 0,06; calibração ilustrativa 206 | ACEITO COM RESSALVA | Confirmadas, mas 0,039 cobre **três baterias**; 206 é ilustração sem dimensionamento completo. Para 600 curvas, a primeira taxa dá 23,4 CPU-h. `V3/stageB/b1-stop-report.md:167-169`; `V4/h2-step7-sinusoid.json:2`. |
| D2 §2 | E2 média/cauda não resolvidas; E3 entregou aproximadamente 15% | ACEITO | `V3/closing-record.md:158-161,232-233`: E3 entregou 51/339 = aproximadamente 15,04%. |
| D2 §2, aritmética | Recuperar as 16 perdas exclusivamente REC deixa 21 contra 22 | ACEITO COM RESSALVA | `37−16=21` correto; recuperação conjunta continua sendo hipótese. `V4/h2-step1-floor.json:36,45`. |
| D2 §2 | T2a tem 43 perdas odd/even de sensibilidade; ganho 81→86 virou 142→141 | ACEITO | `V3/closing-record.md:106,156-157`. |
| D2 §2 | Alternativa usa profundidade medida, que é enviesada para cima perto do limiar | ACEITO COM RESSALVA | Dependência confirmada em `S/battery_v52.py:151,363`. O viés afirmado não foi medido nesses registros; deve permanecer hipótese. |
| D2 §3 | Existem dois pisos estritos, 8 e 11 | REJEITADO | **8** é F_strict do passo 1. **11** é o piso **condicional aos estados registrados** do passo 7, explicitamente sem garantir perdas irrecuperáveis. `P/v0.5.4-h2-step7-sinusoid.md:67-79`. |
| D2 §3 | Fréchet não prova impossibilidade; F_upper não é limite superior demonstrado | ACEITO | `P/v0.5.4-h2-step7-sinusoid.md:43-45`; `P/v0.5.4-h2-step1-floor.md:84-87`. |

**D4**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| D4 §1 | Falhou com 48/147 = 0,327; forecasts 0,057 e 0,122 | ACEITO | `R:110-113`; `V3/closing-record.md:65`. A fração original é 0,3265306122. |
| D4 §1 | Forecast não constitui aceitação/confirmação; não é reconsiderado sozinho | ACEITO | `pause:157-168`. “Resolvido em desenvolvimento” só pode significar PASS nesses forecasts. |
| D4 §2 | Passo 2 adotou incremento INCONCLUSIVE 0,05; custo marginal ≈ 5 CPU-h | ACEITO COM RESSALVA | Orçamento incremental confirmado. Os 5 CPU-h citados abrangem **D2/D4, 200 curvas e duas baterias**, não uma medição isolada de D4. `P/v0.5.4-h2-step2-i3-increment.md:66-69`; `V3/stageB/b1-stop-report.md:169`. |

**T2a**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| T2a §1 | B precisa de 552/559 e mantém 331 | ACEITO | `pause:173-176`. A exigência original é sobre 615; a recusa dos 56 acima de 20 setores deixa essa margem nos 559. |
| T2a §1 | Background deve detectar 0,8 da profundidade com potência 0,95 | ACEITO | `0,5+0,3=0,8`: `S/params.py:153,317`; `S/battery_v51_diff.py:649-656`; probabilidade exigida em `src/refute/core/sensitivity.py:56`. |
| T2a §1 | Warning INCONCLUSIVE bloqueia; acima de 20 setores há recusa; grade 2–4 recusou 42 | ACEITO | `src/refute/core/verdict.py:268-270`; `S/battery_v52.py:32-34,74-87`; `V3/closing-record.md:104-110`. |
| T2a §1 | 102 casos background têm mediana de potência 0,371 | ACEITO COM RESSALVA | O JSON informa **102 abaixo de 0,95 entre 103**, com mediana 0,371 calculada sobre os **103**. Não fornece a mediana separada dos 102. `V4/i1-diagnosis.json:31-37`. |
| T2a §1 | Passo 6 não encontrou modelo adequado; E3 voltou ao anterior em 547/559 | ACEITO | Zero casos válidos e 102 desconhecidos no passo 6. `V4/h2-step6-i2.json:737-752`; `V3/closing-record.md:158-161`. Isso não estabelece limite de informação. |
| T2a §2 | Certificação acima de 20 aumenta margem 7→49; recuperações 72/124/207/223 | ACEITO COM RESSALVA | A margem 49 condiciona-se aos **42 mantidos entre os 56 acima de 20**. Recuperações referem-se apenas aos INCONCLUSIVE, preservando cinco REFUTED. `V3/closing-record.md:66,111-121`. |
| T2a §2 | Background erro 23,2 vezes branco; requisito ≈ 0,17 contra mediana 0,41 | ACEITO COM RESSALVA | Valores constam das fontes, mas 0,17/0,41 vêm de **subconjunto selecionado**, não de todos os 102 ou 615. `V3/closing-record.md:82-83`; `V3/closing-review.md:91`. |
| T2a §2 | Passo 6 custou 3,78; certificações 135/380; aceitação 2.824–3.446 CPU-h | ACEITO COM RESSALVA | 3,7825 é consumo registrado; os demais são estimativas provisórias herdadas. Os 135 já estão dentro do cronograma de aceitação, portanto não são parcela adicional independente. `V4/h2-step6-i2.json:2`; `V3/closing-record.md:180-187`. |
| T2a §3 | Inviabilidade exigiria pelo menos 64/615 irrecuperáveis | ACEITO | `615−552=63` perdas permitidas; 64 excedem a margem. `V3/closing-review.md:89-90`. |
| T2a §3 | Os 20 do passo 1 não são limite independente de estimador; 56 recusas são procedurais | ACEITO | DATA usa o resultado `not_enough_data` da bateria, e todos os 20 também têm MSG. `P/v0.5.4-h2-step1-floor.md:61-64`; `V4/h2-step1-floor.json:79-85`; `V3/closing-review.md:89`. |
| T2a §3 | Piso branco seria limite independente de estimador | ACEITO COM RESSALVA | Isso exige declarar modelo de ruído e classe de estimadores. Os registros examinados não demonstram um limite universal para os hospedeiros reais. `V4/h2-step6-i2.json:737`; `P/v0.5.4-h2-step7-sinusoid.md:85-89`. |

**T3b**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| T3b §1 | T3b passou na v0.5 com 0/8 SURVIVED | ACEITO | `calibration/v0.5/results/closing-record.md:24-26`. |
| T3b §1 | Quadro 63, 13 elegíveis no total, 11 já usados, dois restantes para 11 necessários | ACEITO COM RESSALVA | Correto; os 13 combinam consultas de datas diferentes, não um recenso simultâneo. `V4/t3b-count.json:2-16,38`. |
| T3b §2, aritmética | Definição A: 39 passam proxy; taxa 11/25 implica aproximadamente 17 | ACEITO COM RESSALVA | `39×11/25=17,16`. Extrapolação condicional, não 17 estrelas qualificadas. Custos perto de zero CPU e 1–2 dias são estimativas, com adjudicação humana não medida. `V3/stageB/b1-stop-report.md:201-242`. |
| T3b §2 | Emenda prospectiva, sem cegamento | ACEITO | `P/v0.5.3-design-questions.md:149-153`. |
| T3b §3 | O quadro só cresce por novas disposições FP em binárias catalogadas | REJEITADO | Exclusividade não demonstrada: a seleção também depende de pertencimento ao catálogo, exclusões e outros critérios; disponibilidade pode mudar com elegibilidade de membros existentes. `S/calib05/c3select.py:180-192`; `P/v0.5.4-t3b-eligibility-count.md:36-63`. |

**Seção 8, pontos 1 a 14**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| 8.1 | Frases gerais omitem que os resultados citados usam 0,0027 | ACEITO COM RESSALVA | Os números 11,9/11,2 são daquele nível. Em 0,05, B0 conhecido dá 4,6/4,1. B0b conhecido dá 9,3 e mediana 0,915 **em 0,0027**, não em 0,05. `pause:63-64,112-114`; `ROADMAP.md:66-67`; `B0:65-67`; `V3/stageB/b0b-record.md:31-32`. |
| 8.2 | 0,0027 não é regra congelada das metas; passo 4 congelou desfechos nesse nível | ACEITO COM RESSALVA | Correto. A regra congelada de D2 combina fração REFUTED ≤ 0,05 com Wilson superior ≤ 0,10; não identifica automaticamente α com esse orçamento. `acc:423-424`; `P/v0.5.4-h2-step4-b0-errors.md:49-58`. |
| 8.3 | Estrela geradora exata; gatilho pede fonte para população de hospedeiros | ACEITO COM RESSALVA | Fato confirmado; a população C1 é sintética. Contudo, a massa/raio verdadeiros solares já estão explicitados no documento de aceitação. `S/calib05/c1.py:77-92,366`; `acc:344-348`; `pause:108-113`. |
| 8.4 | Passo 3 exigiu mais que a contribuição incremental necessária a D1; consumiu 6,55 CPU-h | ACEITO COM RESSALVA | Exigência isolada explícita; consumo 3,7871+2,7657=6,5528. Os 35/40 sobreviventes são da confirmação antiga, não dos binários de B0. `P/v0.5.4-h2-step2-i3-increment.md:36-46`; `V4/h2-step3-i3.json:54-57`. |
| 8.5 | Calibração permitia aproximadamente três FAIL; avaliação só um | ACEITO COM RESSALVA | `floor(141×0,025)=3`; CP superior com um FAIL = **0,04979629**, com dois = **0,06224247**. Assimetria confirmada; não impossibilidade de retornar route. O P calibrado teve dois FAIL, não três. `V4/h2-step3-i3.json:25-30`; `pause:75-79`. |
| 8.6 | Passo 3 não tinha bloco de sensibilidade | ACEITO COM RESSALVA | Explicitamente declarado. Faltava essa condição para transportar o teste como PASS qualificado; isso já estava divulgado, não era omissão escondida. `P/v0.5.4-h2-step3-i3-population.md:46-48`; `V4/h2-step3-i3.json:98`. |
| 8.7 | F_strict de T2a não é independente do estimador; “no procedure fixes” generaliza | ACEITO | DATA deriva de `not_enough_data`; não há limite de informação T2a estabelecido. `P/v0.5.4-h2-step1-floor.md:61-68`; `pause:182-195`. |
| 8.8 | Os pisos completos dos passos 1 e 7 não foram unidos | ACEITO COM RESSALVA | O passo 7 já une DATA do passo 1 com odd/even e certificado sinusoid; não incorpora o F_rule completo. A afirmação só procede nesse segundo sentido. `V4/step7_sinusoid.py:235-264`; `pause:127-131`. |
| 8.9 | Um certificado falha no oráculo enquanto a bateria registrou PASS | ACEITO COM RESSALVA | Cruzamento confirmado. Erro otimista ou profundidade elevada são hipóteses; também há diferença entre efeméride/profundidade verdadeiras e candidato medido. Nenhuma causa foi estabelecida. `V4/h2-step7-sinusoid.json:33-42`; `P/v0.5.4-h2-step7-sinusoid.md:21-31`. |
| 8.10 | Cruzamentos combinados são null; janelas acrescentariam três perdas, 8→11 | ACEITO COM RESSALVA | Três de 21 REC em V_win confirmados. O 11 é condicional à classe restrita e às hipóteses Fisher. Os null são **deliberados**, pois a equivalência da caixa e a resposta E2 não foram demonstradas. `V4/h2-step5-gap.json:28-37,61-80`; `V4/step5_gap.py:295-309`. |
| 8.11 | Stop report está desatualizado sobre passo 4 e consumo | ACEITO | Ainda diz parado/sem resumo e 29,04 CPU-h. Há resumo concluído e total do ledger **29,15485677 CPU-h**, arredondado 29,15. A referência correta do consumo antigo é `:52`, não `:101`. `V4/h2-stop-report.md:22,52,101-103`; `pause:65-66,242-244`; `V4/ledger.json:25-39,43-170`. |
| 8.12 | Linha T3b omite PASS histórico da v0.5 | ACEITO COM RESSALVA | Omissão contextual confirmada. A tabela não rotula literalmente T3b como FAIL; registra “none as written” da fase posterior. `pause:26-32`; `calibration/v0.5/results/closing-record.md:24-26`. |
| 8.13 | Gatilho D1 exige D2, atualmente falho por outros bloqueios | ACEITO COM RESSALVA | Exigência conjunta e falha atual confirmadas. Isso não torna o gatilho definitivamente inalcançável; restringe-o a uma bateria com os demais problemas resolvidos. `pause:104-107,119-121`. |
| 8.14 | Gatilho T2a pede validade, não injeções liberadas | ACEITO COM RESSALVA | Os ≥82 dizem respeito à validade do modelo. Cumprir isso, isoladamente, não demonstra recuperação nem altera uma margem contada. Também não prova que uma avaliação subsequente liberaria zero. `pause:200-205`; `V4/h2-step6-i2.json:6-17,752`. |

**Achado c1.py**

| Seção/ponto | Afirmação (resumo curto) | Veredito | Motivo e evidência (arquivo:linha) |
|---|---|---|---|
| Achado c1.py | A estrela usada na geometria das durações é exatamente 1 M☉ e 1 R☉ | ACEITO | Constantes solares entram diretamente em `a_over_rstar`; `durations` usa essa função. Não existe sorteio de massa/raio nessa cadeia. `S/calib05/c1.py:48-49,77-92,145`. |
| Achado c1.py | Catálogo declara centros 1/1 e erros de 5% em massa e raio | ACEITO | Chamada sem argumentos em `S/calib05/c1.py:366`; padrões e campos em `S/synthetic.py:203-217`. PX também usa `make_star()` em `S/calib05/c1.py:531`. |
| Achado c1.py | A verdade está sempre no centro; “precisão” não é erro realizado sorteado | ACEITO COM RESSALVA | Correto para a geometria gerada. Os erros declarados continuam tendo efeito nos modelos que os utilizam como caixa ou outra convenção. O fato gerador já aparece em `acc:344-348`. |

**(a) Correções factuais nos registros existentes**

São textos para correção documental, sem alteração de regras ou decisões de desenho.

| Ponto aceito | Registro e frase exata a corrigir | Texto factual correto |
|---|---|---|
| 8.1–8.2 | `pause:63-64`: “So none of 1, 2 or 3 % is shown to be enough. B0's oracle with the star known exactly gives 11.9 and 11.2, also above 10.” | “At α = 0.0027, under B0's assumptions, none of the three settings meets the frozen step-4 margin criterion. The star-known expectations 11.9 and 11.2 also refer to α = 0.0027. At α = 0.05, the three settings give expectations below 10 in both families; B0's star-known expectations are 4.6 and 4.1. These are oracle non-rejection forecasts, not battery PASS results.” |
| 8.1–8.2 | `pause:112-113`: “Under B0's model and population, a finer stellar precision alone would not do: even the star known exactly leaves expectations of 11.9 and 11.2, above 10.” | “At α = 0.0027, B0's star-known expectations are 11.9 and 11.2, above 10. This does not extend to α = 0.05, where they are 4.6 and 4.1, or establish a general impossibility.” |
| 8.1–8.2 | `ROADMAP.md:66-67`: “Step 4 found that no stellar precision of 1, 2 or 3 % is shown to be enough for D1 under B0's oracle.” | “At its frozen outcome level α = 0.0027, step 4 found no margin under B0's criterion for the 1, 2 or 3 % settings. At α = 0.05, all six expected non-rejection counts are below 10; no battery PASS was demonstrated.” |
| 8.3 | `pause:110-111`: “It also needs a documented source of that information for the binaries' host population, with its URL and retrieval date.” | Acrescentar a precisão factual: “C1's binary hosts are synthetic: the duration generator uses exactly 1 M_sun and 1 R_sun, while the catalog declares 5 % errors centered on those same values. A real-host source concerns an additional population assumption.” |
| 8.7 | `pause:182`: “20 losses that no procedure fixes (`F_strict`), against B's 7.” | “20 recorded losses classified as DATA under the current battery's `not_enough_data` results, against B's allowance of 7. This classification is not an estimator-independent information bound.” |
| 8.7 | `V4/h2-stop-report.md:81-83`: “20 losses that no procedure fixes, under the stated rules and assumptions, against a margin of 7.” | “20 recorded losses fall in step 1's DATA category, against B's margin of 7. Their classification depends on the current battery's results and does not demonstrate that every procedure must lose them.” |
| 8.11 | `V4/h2-stop-report.md:22`: “There is no summary.” | “Step 4 was subsequently completed; the summary is `h2-step4-b0-errors.json`, recording 1.5179 CPU-h for the computation and no stops in the completed record.” |
| 8.11 | `V4/h2-stop-report.md:52`: “29.04 CPU-h (first half 17.17; second half 11.87)” | “29.15 CPU-h (first half 17.17; second half 11.98), including step 4's completion and the recorded summary charges.” |
| 8.11 | `V4/h2-stop-report.md:101-102`: “Open for the maintainer: step 4's stop (63 of 77 shards), and the decision between going on and pausing.” | “The historical step-4 stops were followed by an approved completion. The completed summary is `h2-step4-b0-errors.json`; the maintainer subsequently paused the line, as recorded in `pause-record.md`.” |
| 8.12 | `pause:32`, estado T3b: “"none as written" (v0.5.2)” | “PASS in v0.5: 0 of 8 SURVIVED. For a new confirmation, the later frame count leaves 2 domain-eligible unused stars against 11 needed, a shortage of 9.” |

Os pontos 8.4–8.6, 8.8–8.10 e 8.13–8.14 pedem contextualização conforme as ressalvas da tabela. Não demonstram, por si, erro numérico adicional ou obrigação factual de mudar os gatilhos.

**(b) Números exatos do passo 4 por nível**

Campo **`expected_non_rejected_at_projection`**, preservando os dígitos do JSON. Precisão significa erro declarado de **massa e raio**, ambos com o percentual indicado. Projeções: EB1 = 190; EB2 = 186; franquia = 10 em ambas.

| Família | Precisão | α = 0,0027 | α = 0,01 | α = 0,05 | Evidência |
|---|---:|---:|---:|---:|---|
| EB1 | 1% | 13,830445908175742 | 9,995437577606772 | 5,362720674989048 | `V4/h2-step4-b0-errors.json:21-34` |
| EB1 | 2% | 16,836312113354168 | 12,606305617584674 | 7,25146380289708 | `V4/h2-step4-b0-errors.json:51-64` |
| EB1 | 3% | 19,0651161868452 | 14,409863698623521 | 8,578275505864186 | `V4/h2-step4-b0-errors.json:81-94` |
| EB2 | 1% | 13,668806544718311 | 9,547846539136902 | 4,908288758632289 | `V4/h2-step4-b0-errors.json:119-132` |
| EB2 | 2% | 16,383979783635894 | 11,255070020414713 | 5,655121920891972 | `V4/h2-step4-b0-errors.json:149-162` |
| EB2 | 3% | 20,953239316926638 | 14,395589439972714 | 7,163986611561091 | `V4/h2-step4-b0-errors.json:179-192` |

**Regra congelada de REFUTED:** em P, fração observada ≤ **0,05**, com limite superior de Wilson ≤ **0,10**, além da retenção relativa à v0.4. Está em `S/calib05/c1.py:664-669` e `acc:423-424`. **α = 0,0027 pertence à convenção de B0 e ao desfecho congelado do passo 4; α = 0,05 no oráculo não comprova o cumprimento conjunto daquela regra.**