# Por que os vetters maduros mantêm os planetas e o Refute os perde

Pesquisa independente, somente leitura. Repositório lido em `4a704f0f` (`/home/claude/wt-v059`), em 2026-11-23. Nada foi commitado, rodado ou enviado ao GitHub. O único arquivo escrito é este.

**Ressalvas sobre o que fiz**
- **Recontagens:** são minhas, **exploratórias**, sem revisão do Codex, feitas com `python3 -I` (só biblioteca padrão) sobre registros commitados. Nunca são vereditos.
- **Fontes externas:** todas lidas em 2026-11-23 pela ferramenta de leitura web, que entrega trechos e resumos da página. As citações literais são curtas. Antes de qualquer texto público, os números-chave devem ser conferidos no PDF.
- **Código de terceiros:** nenhum foi rodado. Só avaliei.
- `method_status: not_validated` vale para tudo aqui. Nenhum veredito, lock, meta ou registro antigo muda nesta proposta.

## 1. Resposta curta

- **Hipótese do assessor: parcialmente apoiada.** A perda vem mesmo da arquitetura de decisão: 96,5 a 99,7 % dos planetas perdidos estão INCONCLUSIVE, quase nunca REFUTED. Mas não é a composição uniforme 0,95^10. As perdas se concentram em 2 a 4 testes (`systematics`, `aperture_depth`, `sinusoid`, `odd_even`), e 6 ou 7 dos 11 testes não custam nada.
- **Por que eles mantêm e nós perdemos:** no Robovetter e no LEO-Vetter, "candidato" quer dizer "nenhum teste reprovou", com limiares ajustados na população (injeções e curvas embaralhadas). Teste que não pode rodar não reprova nem bloqueia. No Refute, SURVIVED é um certificado por candidato: cada teste precisa provar que tinha potência. São duas perguntas diferentes.
- **O outro lado:** hoje é o INCONCLUSIVE que segura os alarmes falsos. Passar por padrão, sozinho, devolveria os alarmes falsos da v0.4.
- **Arquitetura recomendada (versão 5):** saída em dois níveis. Nível 1, triagem calibrada na população (completude e efetividade pré-registradas, teste sem cobertura fica "não avaliado", nunca PASS). Nível 2, o veredito de hoje, sem mudar a regra. Mais testes próprios de alarme falso, que faltam.
- **Resultado independente, dois passos:** primeiro no tempo, a auditoria prospectiva de janelas de trânsito (rota e), que não depende da bateria nova e usa fótons que ainda não existem. Primeiro claim da bateria nova: falsos positivos do catálogo KELT-FP contra planetas achados fora do TESS (rota d1), com metade escondida.
- **Posicionamento** "camada pré-registrada de falsificação e auditoria sobre buscas e vetters existentes": apoiado pelo que li (seção 10.4).

## 2. O diagnóstico com os registros do Refute

**Onde os planetas se perdem** (bateria v0.5, `discovery.version: 2`)

| Conjunto | n | Mantidos | INCONCLUSIVE | REFUTED | Fonte |
|---|---|---|---|---|---|
| C1, família P (sintético, estágio 2) | 186 | 100 (0,538) | 83 | 3 | `calibration/v0.5/runs/c1-confirmation/report.json:82-88`; `docs/plans/v0.5.1-wp0/diagnosis.json:156-165` |
| C2, T2a (injeções em hospedeiras reais, estágio 1) | 637 | 270 (0,424) | 366 | 1 | `calibration/v0.5/runs/c2/report.json:248-252`; recontagem em `c2/records.jsonl` mais `c2-prefix/records.jsonl` |
| v0.5.6 parte B, braço planeta, sinal casado com o TOI | 100 | 23 (0,230) | 76 | 1 | recontagem em `docs/validation/v0.5.6/part-b-records.json`; o total de 150 está em `docs/reports/v0.5.6-report.md:117` |

- **Fração das perdas que é INCONCLUSIVE:** 83 de 86 (C1), 366 de 367 (C2), 76 de 77 (parte B). O próprio plano da v0.5.1 já dizia: "Planets are lost to the sensitivity rule of four decisive tests, not to refutation" (`docs/plans/v0.5.1-plan.md:47`).
- **Classe do INCONCLUSIVE** (parte B, 76 planetas casados, única fonte commitada com mensagens por teste):
  - 53 têm só recusas de sensibilidade ("PASS refused: insufficient sensitivity");
  - 11 têm recusa de sensibilidade mais outra causa;
  - 12 não têm recusa de sensibilidade: `sinusoid` fora do domínio (período de 10 dias ou mais, 18 ocorrências), `odd_even` com poucos trânsitos (7), raio estelar ausente (2).
  - Logo, 84 % envolvem ao menos uma recusa de sensibilidade e 70 % só recusas.
- **O C2 não permite essa divisão:** os registros commitados guardam só status e severidade.

**A hipótese da composição, em números** (recontagem exploratória)

"Taxa de passagem" é a fração de alvos em que o teste não ficou INCONCLUSIVE nem deu FAIL fatal.

| Teste | C2 T2a (637) | Parte B, planetas casados (100) | C1 P (186, só INCONCLUSIVE) |
|---|---|---|---|
| `systematics` | 0,487 | 0,42 | 0,849 |
| `aperture_depth` (estágio 2) | não roda | 0,61 | 0,651 |
| `sinusoid` | 0,876 | 0,81 | 0,823 |
| `odd_even` | 0,945 | 0,85 | 0,876 |
| `period_alias` | 0,947 | 0,97 | 0,995 |
| Os outros 6 ou 7 testes decisivos | 1,000 cada | 0,98 a 1,00 | sem bloqueio registrado |
| **Produto das taxas** | 0,381 | 0,168 | 0,397 |
| **Menor taxa** | 0,487 | 0,42 | 0,651 |
| **Conjunta observada** | 0,424 | 0,230 | 0,554 (não INCONCLUSIVE) |

- **0,95^10 = 0,599 é coincidência numérica com o 0,538 da D2.** Nenhuma taxa por teste fica perto de 0,95: a maioria é 1,0 e uma ou duas ficam abaixo de 0,65. Em planetas reais conhecidos a taxa conjunta é 0,23.
- **0,95 não é a chance de um planeta passar.** É a potência exigida contra a alternativa declarada (`src/refute/core/sensitivity.py:56-58`). A chance de passar depende do ruído do alvo contra o tamanho da alternativa.
- **Os testes não são independentes, e a correlação é positiva:** a conjunta observada fica acima do produto nos três conjuntos. No C2, o phi entre `systematics` e `odd_even` é 0,23, e entre `systematics` e `sinusoid` 0,19.
- **Um teste domina.** No C2, `systematics` está em 327 dos 366 INCONCLUSIVE e é o único bloqueio em 238. Sem o bloqueio dele, seriam mantidos 508 de 637 (0,797). É um "e se" sobre status gravados, não uma previsão.
- **SNR alto não resolve.** No C2, com SNR de 50 ou mais, 221 de 357 mantidos (0,619). Na parte B, com SNR de 60 ou mais, 11 de 26.
- **O mecanismo dentro de `systematics`:** o subteste de fundo exige detectar, com probabilidade 0,95 e a 3 erros, uma subida do fundo de 0,8 da profundidade SAP (`src/refute/packs/tess/power.py:205-226`; `calibration/v0.5/claim.yaml:179`, `:251`). O erro medido do fundo tem mediana 23,2 vezes o erro branco (`docs/validation/v0.5.3/stageA/README.md:69-70`). Na parte B, 54 das 57 recusas de sensibilidade de `systematics` envolvem o fundo, e a potência do fundo tem mediana 0,76.
- **A regra que transforma recusa em perda:** qualquer teste decisivo INCONCLUSIVE dá veredito INCONCLUSIVE (`src/refute/core/verdict.py:243`, `:268-270`), inclusive teste de severidade "warning", cujo FAIL só daria WEAKENED.

**O que as cinco rodadas já mostraram**
- v0.5.1: no limite de Cramér-Rao quase todo planeta seria decidível, então a perda viria dos estimadores (`docs/validation/v0.5.1/feasibility/README.md:28-31`).
- v0.5.3: a T2a precisaria de "essentially every class at once" (`docs/validation/v0.5.3/closing-record.md:100-117`). Os estimadores novos recuaram ou não mudaram o resultado.
- v0.5.5: o censo T2a-E liberou 2 de 85 (`docs/plans/v0.5.5-v05-line-pause-record.md:31`). A combinação de regras defendida por princípio é "behaviour-identical to the frozen battery" (`docs/plans/v0.5.5-r2-closing-record.md:5-6`, `:30`).
- **Leitura minha:** cinco rodadas tentaram calcular melhor a mesma pergunta por candidato. Nenhuma mudou a pergunta.

**O outro lado da balança** (recontagem exploratória, "e se" sobre status gravados)

| Conjunto | Hoje (v0.5) | Se recusa de sensibilidade não bloqueasse |
|---|---|---|
| Parte B, planetas casados (100) | 23 mantidos | 76 mantidos (42 SURVIVED, 34 WEAKENED) |
| Parte B, FPs casados (86, passaram o gate) | 13 mantidos | 50 mantidos (3 SURVIVED, 47 WEAKENED) |
| C2, curvas invertidas que passam o gate (24) | 0 mantidas | 14 mantidas (todo INCONCLUSIVE tratado como PASS) |
| C2, curvas rotacionadas que passam o gate (40) | 0 mantidas | 22 mantidas (idem) |

- **Hoje é o INCONCLUSIVE que segura os alarmes falsos**, não um FAIL. O plano da v0.5.1 já avisava (`docs/plans/v0.5.1-plan.md:66-69`). A v0.4, sem a regra, deixava 8 detecções invertidas e 9 rotacionadas sobreviverem (`calibration/v0.5/runs/c2/report.json:254-264`).
- **A variante (e) do R2** (teste "warning" indeciso limita a WEAKENED) levaria os planetas casados de 23 para 43 de 100. Não resolve: `aperture_depth`, que pode ser fatal, segue bloqueando 39.
- **Conclusão do diagnóstico:** a arquitetura explica a perda de planetas e também é a proteção atual contra alarmes falsos. Trocar só a regra de agregação troca um problema pelo outro. Faltam testes que reprovem alarmes falsos por evidência.

## 3. Tabela de mapeamento

**3a. Teste por teste**

| Refute (severidade; limiar) | Robovetter DR25 | LEO-Vetter | SPOC DV |
|---|---|---|---|
| `snr` (gate; 7,1) | MES do pipeline; MES refeito sem trânsitos ruins abaixo de 7,1 reprova | SNR abaixo de 6,2 reprova (otimizado) | MES 7,1 na busca |
| Unicidade do sinal: **não existe** | Model-Shift MS1 a MS3 (otimizado) | MS1 a MS3 (otimizado) | bootstrap de alarme falso |
| `odd_even` (fatal; 3 sigma; alternativa = profundidade inteira) | sigma_OE acima de 1,1, ou 11,2 e 19,8 pelo Model-Shift; "only operates out to 90 days" | OE acima de 3 sigma em três ajustes; época acima de 10 sigma; fixo | estatística de profundidade par e ímpar |
| `secondary_eclipse` (warning; 3 sigma) | MS4 a MS6, com exceção para ocultação de Júpiter quente | MS4 a MS6, mesma exceção; fixo | MES do secundário |
| `plausibility` (raio e duração) | forma em V acima de 1,04; raio sozinho não reprova | raio acima de 22 raios terrestres; V de 1,5 ou mais; duração não física; fixos | sem equivalente |
| `aperture_depth` (fatal; estágio 2) | diagnóstico de halo (razão acima de 4,0) | sem equivalente em fluxo | diagnóstico de fantasma |
| `centroid_shift` (diagnóstico) | deslocamentos de centroide em imagens de diferença | deslocamento acima de 15 segundos de arco, pelo ajuste de PRF | centroide da imagem de diferença |
| `nearby_contamination`, `eb_catalog` (catálogo) | casamento de efemérides | conferência na literatura | sem equivalente |
| `period_alias` (caixa contra senoide) | SWEET e LPP; a flag PERIOD_ALIAS é só informativa | ajuste de modelo (AIC) e SWEET | sem equivalente |
| `sinusoid` (warning; significância 15; período abaixo de 10 dias) | SWEET (SNR acima de 50, período abaixo de 5 dias) | SWEET: os mesmos 15 e 10 dias (otimizado) | sem equivalente |
| `systematics` (warning; despejos, SAP contra PDCSAP, fundo) | Skye, Marshall, Rubble | artefatos por trânsito; teste de lacuna | bandas rolantes |
| `edge_events` (warning) | Rubble e eventos em lacunas | lacuna: metade dos trânsitos a 2 durações (otimizado) | sem equivalente |
| `single_event` (diagnóstico; 0,88) | SES máximo sobre MES acima de 0,8, só acima de 90 dias | acima de 0,88 no artigo, só com até 10 trânsitos | sem equivalente |
| `event_consistency` (diagnóstico) | Chases, Zuma, Tracker | CHI abaixo de 7,8; Chases | sem equivalente |
| `duty_cycle` (fatal; 0,5) | sem equivalente | o mesmo 0,5; fixo | sem equivalente |

- O Refute já usa quatro limiares do LEO-Vetter (`src/refute/packs/tess/battery_v5.py:122`, `:254`, `:372`, `:520`). A diferença está na regra em volta do limiar, não no limiar.
- Não achei, em nenhum dos três, um teste de fundo por candidato com exigência de potência, como o subteste que mais bloqueia no Refute.

**3b. Como o limiar foi fixado, e o que acontece quando o teste não roda**

| | Como fixa os limiares | Quando a métrica não pode ser calculada |
|---|---|---|
| **Refute v0.5** | Fixos de antemão (3 sigma, valores da literatura). Cada teste ainda precisa de potência 0,95 em 2.000 sorteios | **INCONCLUSIVE, e o veredito inteiro fica INCONCLUSIVE.** Cobertura zero nunca é PASS |
| **Robovetter DR25** | Otimização automática (Nelder-Mead, a melhor de 2.000 partidas), minimizando a distância a efetividade 1 e completude-alvo 0,8; depois ajuste manual para manter a completude de longo período acima de 70 % | **Passa, às vezes com aviso.** CENT_NOFITS é aviso, "not an FP". Marshall com falha do ajuste fica "always pass". Vários testes só valem num domínio (Chases com até 5 trânsitos, Skye acima de 45 dias). Sem curva e sem ajuste nos dois tratamentos, reprova |
| **LEO-Vetter** | Otimização (`differential_evolution`) só dos testes de alarme falso, sobre injeções e curvas embaralhadas; os de falso positivo astrofísico são fixados à mão em binárias conhecidas | **Em geral não reprova.** Fora do domínio o teste não se aplica. No código, comparação com NaN não marca. Exceções que reprovam: ajuste de trânsito que falha e alguns NaN do secundário |
| **SPOC DV** | Não fixa disposição: "specifically not tasked with rating, ranking or otherwise classifying" | Reporta diagnósticos; valores indefinidos são ignorados; testes de centroide podem não rodar por falta de tempo |

Fontes da seção 3: Thompson et al. 2018, https://ar5iv.labs.arxiv.org/html/1710.06758 (apêndice A e seção V); Kunimoto et al. 2025, https://arxiv.org/html/2509.10619v1 (seções 3 a 6); código em https://github.com/mkunimoto/LEO-vetter/blob/main/leo_vetter/thresholds.py; Twicken et al. 2018, https://ar5iv.labs.arxiv.org/html/1803.04526 (seções 1.3, 2 e 3.2).

## 4. Por que eles mantêm os planetas

1. **A pergunta é outra.** No DR25, "If a TCE passes all tests [...] it is dispositioned as a PC" (legenda da figura 4). No LEO-Vetter, o resultado é o OU das marcas de reprovação: sem marca, o sinal segue. Ninguém exige que cada teste prove que poderia ter reprovado aquele candidato.
2. **O limiar é ajustado na população, não por teste.**
   - DR25: completude medida em trânsitos injetados e efetividade em curvas invertidas e embaralhadas. Resultado: 85,2 % dos injetados recuperados saem como candidato, e 99,6 % dos alarmes falsos simulados são reprovados (seções V e VII.3).
   - LEO-Vetter: 91,00 % de completude, 99,91 % dos alarmes falsos simulados reprovados e 96,97 % de confiabilidade (seção 6.1).
3. **Teste que não roda não reprova e não bloqueia** (tabela 3b). Não existe um terceiro estado que contamine a disposição.
4. **A perda de planetas é aceita, medida e publicada.** "We accept certain amounts of collateral damage (i.e., exoplanets dispositioned as FP)" (DR25, seção I.3). No pior canto do DR25 (200 a 500 dias, MES abaixo de 10), a completude é 76,7 % e a confiabilidade 50,5 %. No LEO-Vetter, três TOIs com disposição CP do TFOPWG reprovam (seção 6.1).
5. **Eles têm testes dedicados a alarme falso** (unicidade pelo Model-Shift, consistência de SNR, forma, testes por trânsito), que é onde o ajuste populacional funciona. O Refute tem poucos, e nenhum de unicidade.
6. **Nos testes de falso positivo astrofísico, o limiar é frouxo de propósito.** O LEO-Vetter relaxou a forma em V para 1,5 "to avoid failing high-impact-parameter gas giants" e deixa passar ocultações de Júpiter quente.
7. **A confiabilidade medida vale só contra ruído e sistemáticos.** Contra binárias, os limiares do LEO-Vetter são fixos e conferidos em casos conhecidos. A dificuldade do Refute com binárias dobradas na metade do período (D1) também existe lá: só são pegas se as profundidades forem "dissimilar enough" (DR25, A.4.1.4; `docs/plans/v0.5.1-plan.md:82-83`).

**Uma nuance honesta:** o DR25 diz que sua escolha "is no longer based on the philosophy of 'innocent until proven guilty'". Ele equilibra completude e confiabilidade de propósito. Mesmo assim, a mecânica segue sendo "passa se nada reprovou".

## 5. Arquitetura proposta para a versão 5

**5.1 Regra de decisão: saída em dois níveis**

| Nível | O que afirma | Regra | Onde se mede |
|---|---|---|---|
| **1. Triagem** (campo novo, por exemplo `screen`; não é veredito) | "Nenhum teste avaliado reprovou" | Gate PASS, todos os testes de alarme falso do núcleo avaliados, nenhum FAIL. Cada teste devolve PASS, FAIL ou "não avaliado", com motivo e cobertura | Na população: completude, efetividade, confiabilidade |
| **2. Veredito** (SURVIVED, WEAKENED, REFUTED, INCONCLUSIVE) | O certificado de hoje | `aggregate` sem mudança: SURVIVED só com todos os testes decididos, com cobertura e sensibilidade | Por candidato, mais a decidibilidade na população |

- **"Não avaliado" nunca é PASS.** O registro lista quantos testes foram avaliados de quantos, e quais não.
- **Sem o núcleo de alarme falso avaliado, não há triagem** (fica "não triado"). Assim a triagem não passa por omissão.
- **Todo INCONCLUSIVE ganha o rótulo de relatório que o R2 já defendeu** ("warning-only gaps" ou "fatal or gate gaps", `docs/plans/v0.5.5-r2-closing-record.md:24`).
- **Precedente de saída em níveis:** o TESS-ExoClass separa triagem, nível 1, nível 2 (candidato com ressalva e lista de flags) e nível 3 (https://github.com/christopherburke/TESS-ExoClass).

**5.2 O que precisa ser construído**
- **Testes de alarme falso com limiar ajustável:** unicidade (Model-Shift), consistência de SNR entre trânsitos, forma, assimetria. Implementação própria ou motor permissivo (seção 6).
- **O procedimento de ajuste**, determinístico e pré-registrado: objetivo fixado antes (por exemplo, a distância usada pelo DR25 e pelo LEO-Vetter), sementes fixas, limiares resultantes gravados no claim e no lock.
- **Os testes de falso positivo astrofísico de hoje ficam** como estão, com limiares fixos, e continuam decidindo REFUTED.

**5.3 Conjuntos de calibração viáveis no TESS com os meios do Refute**

| Conjunto | Como o LEO-Vetter faz | O que o Refute já tem | Proposta |
|---|---|---|---|
| **Injeção em hospedeiras reais** | Uma injeção por curva, no nível de fluxo, não de píxel (seções 5.3 e 5.6) | C2: 10 injeções por estrela em 87 hospedeiras, dependentes entre si | Uma injeção por hospedeira; estrelas SPOC de 2 minutos sem TOI |
| **Embaralhamento** | Troca a ordem das órbitas dentro do setor e a ordem dos setores (seção 5.4) | Duas rotações por setor (T2b) | Adotar a troca de órbitas e setores; manter as rotações como comparação |
| **Inversão** | Descartada no TESS: a luz espalhada não é simétrica (seção 5.4) | Uma inversão por estrela, reportada à parte (`docs/plans/v0.5-plan.md:176-181`) | Manter reportada à parte, nunca como nulo validado |

- **Custo estimado:** o C2 gastou 39,1 CPU-h em 1.400 curvas com duas baterias (`calibration/v0.5/runs/c2/report.json:246`). Com 600 hospedeiras de ajuste e 600 de confirmação, três curvas cada, são 3.600 curvas: perto de 100 CPU-h. Só curvas de luz, sem píxeis: da ordem de 10 GB (estimativa minha, não medida).
- **Limite estatístico:** no C2, 64 de 300 curvas transformadas passaram o gate. Com cerca de 250 detecções nulas por metade, zero mantidas daria um limite superior perto de 1,5 %. Não dá para afirmar os 99,6 % da literatura, que usa mais de 15 mil sinais.
- **Limite de método:** injeção no fluxo não calibra testes de píxel. O LEO-Vetter declara o mesmo limite.

**5.4 Metas pré-registradas da versão nova** (proposta; os números são fixados no documento de aceitação, antes de qualquer dado)

| Meta | Definição | Valor proposto | Âncora |
|---|---|---|---|
| **Completude da triagem** | "Não reprovado" entre injeções recuperadas que passam o gate | Limite inferior de Wilson 95 % de pelo menos 0,85 | DR25 85,2 %; LEO-Vetter 91 %; Dallas et al. 0,89 |
| **Planeta reprovado** | REFUTED entre as mesmas injeções | No máximo 0,05, com limite superior de até 0,10 | Segunda cláusula da D2, que a v0.5 cumpriu |
| **Efetividade** | Reprovado entre detecções em curvas embaralhadas que passam o gate | Limite inferior de pelo menos 0,90; invertidas à parte | O que o tamanho da amostra permite |
| **Confiabilidade** | Fórmula do DR25 (equação 8) | Reportada com intervalo, sem meta na primeira versão | Thompson et al. 2018 |
| **Decidibilidade** | Veredito diferente de INCONCLUSIVE entre os "não reprovados" | Reportada; guarda de não inferioridade pareada contra a versão 2 | Sem meta de retenção no nível do veredito |
| **Integridade do certificado** | SURVIVED com algum teste "não avaliado" | Zero, por regra do motor, com caso de sabotagem | `tests/test_sensitivity.py` |

**5.5 Como os inegociáveis ficam de pé**
- **Nenhum PASS sem evidência:** o estado "não avaliado" é novo e nunca vira PASS. `enforce_coverage` e `enforce_sensitivity` não mudam.
- **Cobertura zero é INCONCLUSIVE:** igual a hoje no veredito. Na triagem, vira "não avaliado" e aparece na contagem.
- **Veredito só de código determinístico:** o ajuste dos limiares é um script com sementes, rodado na metade de exploração. Os limiares entram no claim antes do lock.
- **Locks e dado escondido:** hospedeiras de confirmação e parâmetros de injeção sorteados por uma rodada do drand posterior ao lock, e rodados uma vez.
- **Nada retroativo:** as metas D1, D2, D4 e T2a continuam falhadas para a bateria v0.5. Enquanto a versão 5 usar aqueles testes, carrega o rótulo 'WEAKENED; does not meet D1, D2, D4, T2a'.

**5.6 O conflito, dito com todas as letras**
- "Não testável = INCONCLUSIVE" somado a "todo teste precisa decidir" limita a retenção no nível do veredito à decidibilidade conjunta dos piores testes: 0,23 em planetas conhecidos. Não vejo cálculo melhor da mesma regra que mude isso (seção 2).
- **Resolução proposta:** separar "mantido" (nível 1) de "decidido" (nível 2). A retenção passa a ser medida onde a literatura a mede. A decidibilidade vira número declarado, não meta de retenção falhada.
- **Alternativa B (mudança de regra, pede revisão cega):** redefinir SURVIVED como "passou numa bateria com completude e efetividade medidas". O R2 rejeitou algo próximo por princípio (`docs/plans/v0.5.5-r2-arguments.md:73-75`). Sugiro decidir só depois de existirem os números do nível 1.
- **Alternativa (e) do R2:** ajuda pouco (23 para 43 de 100) e mistura três coisas sob WEAKENED.

## 6. LEO-Vetter como comparação ou motor, e os outros candidatos

| Ferramenta | Licença | Entradas | Estado | Papel sugerido |
|---|---|---|---|---|
| **LEO-Vetter** | GPL-3.0 (li o cabeçalho do LICENSE: "GNU GENERAL PUBLIC LICENSE, Version 3") | Tempo, fluxo bruto e destendenciado, erro, período, época, duração, propriedades da estrela; para píxel, lista de setores | 70 commits, 2 issues abertas; último push em 2026-07-29 (varredura do assessor) | **Comparador externo**, nunca motor |
| **exoVetter** | BSD-3-Clause (li o texto de `LICENSE.rst`) | Objeto TCE e curva `lightkurve`; para centroide, série de píxeis | 326 commits, 21 issues abertas; versão 0.0.16 no Zenodo | **Candidato a motor** das métricas de alarme falso |
| **TRICERATOPS** | MIT (pela página; texto do LICENSE não lido, **não confirmado**) | TIC, setores, curva dobrada | 194 commits, 10 issues abertas | Informação (probabilidade de falso positivo), issue #12; nunca decide |
| **TESS-ExoClass** | MIT (pela página, **não confirmado**) | Tabelas de TCE do SPOC | "very, very much work in progress"; push em 2024-03 | Referência de desenho, não motor |
| **ExoMiner** | NASA Open Source Agreement, segundo o README; sem arquivo LICENSE na raiz | Produtos SPOC, tabelas de TCE | Ativo | No máximo comparador: é rede neural, e o veredito do Refute sai de teste determinístico |
| **transit-diffImage** | GPL-3.0 (li o cabeçalho do LICENSE) | Efeméride e setores; baixa recortes de FFI | 17 commits; push em 2026-05-15 | Comparador externo do centroide (seção 6.2) |

**6.1 LEO-Vetter**
- **Linguagem e dependências:** Python, `pip install leo-vetter`; o nível de píxel pede o `transit-diffImage`, instalado do GitHub. A lista completa de dependências não foi lida (**não confirmado**).
- **Rodar nas entradas congeladas do Refute:** o nível de fluxo é simples, basta passar os vetores da curva e a efeméride. O nível de píxel baixa recortes de FFI pela rede, fora das entradas congeladas.
- **Ressalva de domínio:** os limiares foram ajustados em curvas de FFI do QLP de anãs M, com SNR acima de 9 e pelo menos 3 trânsitos. O README avisa que outros usos podem pedir outros limiares. O Refute usa curvas SPOC de 2 minutos.
- **Licença, consequência prática:** a Apache diz que "GPLv3 software cannot be included in Apache projects" (https://www.apache.org/licenses/GPL-compatibility.html). Importar o LEO-Vetter como biblioteca e distribuir junto traria os termos da GPL para a distribuição. Rodá-lo como ferramenta separada (outro ambiente, outro processo, commit fixado, saídas com hash) e só comparar resultados não mistura código. **É leitura minha, não parecer jurídico: a decisão é do mantenedor.**
- **Recomendação:** comparador externo, nas mesmas curvas e efemérides, com a concordância reportada. Rodar código de terceiros pela primeira vez é parada do mantenedor.

**6.2 exoVetter como motor, e o centroide**
- **A favor do exoVetter:** licença permissiva, mantido no STScI, com as métricas que faltam ao Refute (LPP, Model-Shift, SWEET, par e ímpar, e as do LEO-Vetter: SHP, MES, DMM, CHI) e um vetter de centroide.
- **Contra:** entrega métricas, não disposições. Os limiares de Dallas et al. são "in-sample calibration results rather than independent performance estimates". MES e Model-Shift "can return NaNs". O Refute teria de embrulhar cada métrica com cobertura, "não avaliado" e limiar próprio.
- **Centroide:** o `centroid_v5` do Refute usa centroides ponderados por fluxo, qualificados por setor, e deu `LinAlgError` e `OverflowError` na v0.5.8. O método de imagem de diferença com ajuste de PRF é o padrão do SPOC DV, do Robovetter e do LEO-Vetter, e já é a issue #11 do Refute.
- **O `transit-diffImage` suporta TESS:** o LEO-Vetter o usa com o método `tess_PRF_centroid`. O README cita uma dependência só para Kepler. Não achei artigo próprio do pacote (**não confirmado**); o uso no TESS está descrito em Kunimoto et al. 2025, seção 4.5.
- **Recomendação para o centroide:** `transit-diffImage` como comparador externo (GPL-3.0, mesma consequência do item 6.1). Como motor, o caminho permissivo é o vetter de centroide do exoVetter. Ele achou 162 dos 281 deslocamentos conhecidos do Kepler (58 %), e os autores dizem que abaixo de 0,2 píxel ele "should not be trusted".
- **TESS-plots** (https://github.com/mkunimoto/TESS-plots, BSD-3-Clause pela página): gráficos de diagnóstico. A ferramenta de imagem de diferença está marcada "No longer maintained" e aponta para o `transit-diffImage`. Serve só para revisão humana. Gráfico nunca decide veredito.

**6.3 Modelo físico de trânsito**
- **A versão 5 proposta não precisa de biblioteca nova.** O pack já tem o trapézio próprio (`src/refute/packs/tess/battery_v51.py:225-251`), e a forma em V e a duração não física do LEO-Vetter saem do trapézio mais as relações de duração com a estrela.
- **Se um modelo com escurecimento de limbo for desejado depois:** PyTransit aparece como GPL-2.0 (varredura do assessor) e batman como GPL-3.0 (página do repositório, https://github.com/lkreidberg/batman; texto do LICENSE não lido). As duas têm o mesmo problema de distribuição do item 6.1 dentro de um projeto Apache-2.0. O `exoplanet-core` oferece a curva com limbo quadrático, mas a página não mostrou a licença (**não confirmado**, https://github.com/exoplanet-dev/exoplanet-core). Qualquer escolha passa pelo registro em `sources/` e pelo mantenedor.

## 7. Relação com a v0.5.9

A pesquisa não muda a pergunta da v0.5.9 (a classe da saída depende de onde o ajuste começa?), mas muda três coisas na entrega. **Primeiro,** o subteste que mais muda de classe na v0.5.8 (fundo de `systematics`, 8 de 13 mudanças no plano anterior) é o mesmo que mais bloqueia planetas: vale registrar por teste, em cada registro, o motivo e a classe de todo "não decidido", para a fase seguinte ter linha de base. **Segundo,** a regra de consenso proposta (saída instável vira INCONCLUSIVE) só rebaixa, e a decidibilidade já é 0,23: a parte A deveria medir também quantos alvos ficam "não reprovados", como coluna exploratória. **Terceiro,** travar 600 PCs (190 GB) num claim de estabilidade sobre uma regra de decisão que deve mudar tem vida curta. Recomendo entregar a v0.5.9 como protótipo exploratório (etapa 0 e parte A) e guardar o lock para a bateria nova.

## 8. Plano de fases enxuto

| Fase | Pergunta | Tamanho | Paradas do mantenedor |
|---|---|---|---|
| **1. Contagem e protótipo** (exploratória) | Os números da seção 2 se reproduzem por script commitado? Quantos alvos do KELT-FP e quantos planetas achados fora do TESS têm dados SPOC de 2 minutos? O campo de triagem, calculado sobre registros já existentes, separa planetas de FPs? | Até 5 CPU-h; só metadados; 1 rodada do Codex; 3 a 5 dias | Abrir a fase; registros de licença (`sources/`); primeira execução do LEO-Vetter ou do exoVetter, se entrar |
| **2. Versão 5 e calibração** (confirmatória) | A triagem em dois níveis cumpre completude e efetividade pré-registradas em hospedeiras reais nunca usadas? | Cerca de 100 a 150 CPU-h; cerca de 10 GB; 2 a 3 semanas; até 3 rodadas do Codex e revisão cega | Documento de aceitação antes do código; mudança em `src/`; dependências; lock e rodada do drand; nenhuma reexecução |
| **3. Primeiro claim independente da bateria** (confirmatória, rota d1) | Em dados TESS de 2 minutos, a versão 5 reprova mais os falsos positivos do KELT-FP do que os planetas achados fora do TESS, no sinal do próprio objeto, com guarda de planeta? | Cerca de 150 por braço: perto de 6 CPU-h e 100 GB pelas taxas da v0.5.8; 1 a 2 semanas | Lock e drand; texto público; rascunho do Zenodo; prazo de resposta, se algum resultado negativo tocar um artigo |

- **Trilha paralela, que pode começar já na fase 1 (rota e):** auditoria prospectiva de janelas de trânsito. Não usa a bateria, só o avaliador de holdout. Passos: aceitação sintética do avaliador, contagem de alvos visíveis nos setores novos, lock antes de os dados saírem, pontuação quando saírem. Paradas: lock e drand; uso de lista de terceiros (licença e aviso aos autores); texto público.
- **Também em paralelo e barato:** travar as saídas da versão 5 para PCs não expostos e pontuar quando o TFOPWG mudar disposições (rota b).
- **Regra de parada:** se a fase 1 achar menos de 60 alvos por braço com dados de 2 minutos, a fase 3 troca de rota (campo Kepler, rota a, com adaptador de FFI) antes de qualquer lock.
- **Coerência com "explore livremente, conclua com rigor":** a fase 1 não produz veredito. As fases 2 e 3 só confirmam em alvos não usados para escolher.

## 9. Riscos e incertezas

- **A triagem pode não atingir efetividade com os testes de hoje.** O "e se" da seção 2 mostra 14 de 24 detecções invertidas mantidas. Sem testes novos de alarme falso, o nível 1 repete a v0.4.
- **Dois níveis podem ser lidos como relaxar a regra.** Não é: o veredito não muda. Mas o texto público precisa dizer que "não reprovado" não é SURVIVED.
- **O ajuste de limiares pode sobreajustar.** Por isso metade escondida, sorteio pelo drand e uma só execução.
- **Os "e se" são contas sobre status gravados.** Uma execução real pode dar outro número.
- **As leituras externas vieram por resumo de página.** Os limiares da tabela 3a podem ter erro de transcrição: o corte de evento único do LEO-Vetter saiu 0,88 no artigo e 0,8 na leitura do código.
- **Populações fáceis:** planetas de levantamentos de solo são na maioria Júpiteres quentes. Reter esses não diz nada sobre planetas pequenos.

**O que não consegui verificar**
1. Os registros por curva do C1 (`records.jsonl` não está no git, `calibration/v0.5/runs/c1-confirmation/files.json`). Usei as contagens de `diagnosis.json`.
2. A classe do INCONCLUSIVE no C2 (sem mensagens nos registros).
3. O PDF de Thompson et al. 2018 e o de Kunimoto et al. 2025 página a página. Li as versões HTML por trechos.
4. Li et al. 2019 (DV, parte II), Coughlin et al. 2016 (DR24), KSCI-19114 e Bryson et al. sobre confiabilidade: não lidos.
5. O texto do LICENSE do TRICERATOPS e do TESS-ExoClass (limite de leitura do GitHub). O repositório do SHERLOCK não abriu.
6. As dependências exatas do LEO-Vetter, do exoVetter e do `transit-diffImage`, e se são determinísticos entre máquinas.
7. Quantos alvos do KELT-FP têm dados SPOC de 2 minutos, e quantos já são TOIs.
8. A faixa de magnitude do KELT-FP: saiu "6<V<10" numa leitura e "6<V<13" em outra.
9. A divisão entre candidatos e falsos positivos nos 931 KOIs de Dallas et al. O artigo não dá.
10. Os nomes das tabelas do NASA Exoplanet Archive no serviço de consulta e uma declaração explícita de licença para as tabelas KOI. A página de agradecimentos só pede a citação.
11. A taxa real de mudança de disposição do TFOPWG por ano. A estimativa da seção 10 é minha.
12. As licenças listadas pelo assessor para wotan, tls, tess-point, WATSON, `vetting` e DAVE: não li os textos.
13. A data de submissão e a revista de arXiv:2610.32949.
14. Quais estrelas das listas públicas (eumemic, CTOIs) o TESS observa nos setores 110 a 120, e em que produto (2 minutos ou só FFI). Não rodei a ferramenta de visibilidade.
15. O prazo entre o fim de um setor e a liberação dos dados no MAST, e as datas dos setores 111 em diante.
16. O conteúdo de `candidates/predictions.csv` do eumemic e a data do commit dele. Li só o README.

## 10. Um resultado científico independente

O único resultado confirmatório do Refute (v0.5.6, SURVIVED) é concordância com o TFOPWG, não independência (`docs/reports/v0.5.6-report.md:137`).

**10.1 As rotas, em ordem de recomendação**

| Rota | Independência | Custo | Tempo até o primeiro lock e resultado | Risco |
|---|---|---|---|---|
| **(e) Auditoria prospectiva de janelas de trânsito** em setores novos | **Alta, de outro tipo:** fótons que não existiam quando o sinal foi achado; nenhum rótulo. Testa se o sinal se repete, não se é planeta | Baixo: usa o avaliador de holdout, não a bateria | Lock em 1 a 2 semanas; primeira pontuação em cerca de 2 a 4 meses (estimativa) | O holdout fechou a v0.2.1 sem aprovação; poucos alvos; pouca potência por setor; auditoria de terceiros |
| **(d1) Sinais de levantamentos de solo em dados TESS de 2 minutos:** KELT-FP contra planetas achados fora do TESS | **Alta.** Rótulos vêm de fotometria e espectroscopia de solo, e de um processo que não é o TFOPWG | Baixo a médio: mesmo adaptador; falta a contagem | 2 a 3 semanas depois da versão 5 | Amostra de tamanho desconhecido; sinais fundos e fáceis; parte dos alvos já é TOI |
| **(d2) Injeções e curvas embaralhadas** (a calibração da seção 5) | Alta em relação a qualquer rótulo; os planetas são sintéticos | Cerca de 100 CPU-h | 1 a 2 semanas | Não cobre falso positivo astrofísico |
| **(a) Campo Kepler** (Dallas et al.) | **A mais alta para classificação:** outro instrumento, quatro anos de dados | Alto: adaptador de FFI novo, e os testes que usam produtos SPOC ficam sem dado | 4 a 8 semanas | Estrelas fracas, um setor por ano, decidibilidade perto de zero; lado planeta pequeno |
| **(b) Pontuação prospectiva de PCs** | Só temporal: o rótulo ainda é do TFOPWG | Baixo para travar | Lock imediato; resultado em 1 a 2 anos | Lenta; depende de a comunidade resolver os alvos |
| **(c) TRICERATOPS e validação estatística** | Nenhuma: usa a mesma curva TESS | Baixo | Não se aplica | É estocástico; dá probabilidade, não verdade |
| **(d3) Gaia DR3, binárias não resolvidas** | Alta (astrometria e velocidade radial) | Baixo | Só como rótulo auxiliar | Poucos casos; os termos de uso do Gaia já restringem publicação no projeto |

**10.2 Detalhes por rota**

**Rota (a), campo Kepler** (arXiv:2610.32949, https://arxiv.org/html/2610.32949)
- **O que o artigo fez:** busca BLS em 324.530 curvas TGLC (de FFI) de 185.422 estrelas do Kepler, nos setores 14, 15, 16 e 26. Resultado: 1.976 sinais casados com 931 KOIs. Com SNR acima de 7 e período até 12 dias: completude 0,89 (665 de 748), efetividade 0,9998, confiabilidade 0,81.
- **Limites que os autores declaram:** o conjunto de referência "includes eclipsing binaries, thereby contaminating our true positives". Os limiares são "in-sample". As estrelas têm magnitude TESS de 12 a 16.
- **Dá para pré-registrar um claim do Refute?** Em princípio sim, com metade escondida. Na prática, hoje não:
  - o Refute só lê curvas SPOC de 2 minutos, e nesses dados só 26 planetas e candidatos do Kepler tinham sinal suficiente (Battley et al. 2021, https://arxiv.org/abs/2103.03259);
  - com curvas de FFI, `systematics`, `aperture_depth` e `centroid_shift` não têm seus dados de entrada.
- **Rótulos:**
  - tabela DR25: uniforme e automática. O próprio arquivo diz que é "a statistical result" e que alguns planetas validados saem como falso positivo. Boa para taxas, ruim por objeto;
  - DR25 Supplemental: melhor disposição por objeto (4.717 candidatos e 4.847 falsos positivos em 9.564 KOIs);
  - Certified False Positives: o rótulo de falso positivo mais limpo, revisado por pessoas;
  - para o lado planeta, a tabela de planetas do arquivo.
  - Fonte: https://exoplanetarchive.ipac.caltech.edu/docs/PurposeOfKOITable.html.
- **Contaminação:** resolve-se usando as disposições e as flags (eclipse estelar, deslocamento de centroide), nunca "KOI = planeta".
- **Lado planeta provavelmente pequeno:** o artigo não dá a divisão. No subconjunto do teste de centroide, só 27 de 807 KOIs são candidatos sem deslocamento. É indício, não contagem.
- **Acesso e licença:** arquivo público, com pedido de citação (https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html). O projeto já tem registros de licença para tabelas do mesmo arquivo (`docs/third-party-data.md`). TGLC está no registro de dados abertos da AWS.

**Rota (d1), a recomendada para o primeiro claim da bateria nova**
- **Lado falso positivo:** catálogo KELT-FP (Collins et al. 2018, https://arxiv.org/abs/1803.01869): 1.128 estrelas brilhantes com sinal de trânsito que o acompanhamento de solo mostrou serem falsos positivos astrofísicos. O título diz "Pre-vetted False Positives for TESS".
  - Tipos: 378 binárias eclipsantes vizinhas, 307 binárias espectroscópicas de uma linha, 140 de duas linhas, 130 e 25 binárias eclipsantes no alvo, 90 misturadas, 29 gigantes.
  - Colunas: TIC, período, instante do trânsito, duração, profundidade, tipo, e uma flag de presença na lista de alvos do TESS. Isso permite a regra de identidade da v0.5.6.
  - Disponível como tabela legível por máquina com o artigo. Termos de uso a registrar em `sources/` antes de qualquer uso.
- **Lado planeta:** os TOIs com disposição KP (planetas achados antes ou fora do TESS). O quadro congelado tem 561, com 170 não expostos na metade de confirmação e 138 na de exploração (recontagem do plano da v0.5.9). Melhor definir o braço pela instalação de origem no arquivo da NASA, não pela sigla do TFOPWG.
- **Por que é um bom desenho:** os dois braços vêm do mesmo tipo de seleção (sinais que um levantamento de solo detectou). Isso reduz a diferença de populações que a v0.5.6 declarou como limite.
- **Cuidados:** teste de catálogo desligado; excluir alvos já expostos; tirar ou estratificar alvos que são TOI com disposição FP por causa do próprio KELT; metade escondida por sorteio do drand.

**Rota (b), pontuação prospectiva de PCs**
- **Tamanho e prazo (estimativa minha, grosseira):** o quadro tem 1.298 FP, 86 FA e 572 CP acumulados em cerca de 8 anos de TOIs, perto de 5 % do conjunto de PCs resolvido por ano. Com os 2.098 PCs não expostos da metade de confirmação travados, seriam da ordem de 100 resoluções por ano. Um teste do tamanho da parte B (150 por braço) levaria 1 a 2 anos.
- **Vale travar agora** porque custa pouco, mas não serve como primeiro resultado.

**Rota (e), auditoria prospectiva de janelas de trânsito**
- **O claim:** antes de os dados de um setor novo ficarem públicos, o Refute trava a regra: os trânsitos previstos aparecem nas janelas previstas, contra janelas de controle? É o componente 4 do motor (holdout cego), aplicado a dados que ainda não existem. Encaixa nas issues #24 e #25.
- **De onde vêm as previsões:**
  - **eumemic/exoplanets:** cerca de 38 sinais sem relato anterior, com `candidates/predictions.csv` (instantes previstos até junho de 2027, 1 sigma de 5 a 15 minutos). Resultados em CC BY 4.0;
  - **Avril:** ainda não publica lista;
  - **CTOIs do ExoFOP:** o projeto já guarda uma cópia com 5.139 linhas (`calibration/v0.4/inputs/ctoi.csv`), mas a política de uso do ExoFOP é condição aberta;
  - **as do próprio Refute:** efemérides de saídas já travadas.
- **Calendário do TESS** (https://tess.mit.edu/observations/, lido em 2026-11-23): a página diz que o TESS está no setor 109 e que "Sector 110 begins on October 31, 2026". No ano 9, os setores 108 a 114 são os últimos sete setores "rolados" do sul, 115 e 116 cobrem partes da eclíptica, e 117 a 120 abrem a campanha norte.
- **Sobreposição provável, não conferida:** a amostra do eumemic são anãs com curvas QLP nos setores 97 a 105, da mesma campanha rolada do sul. Parte deve cair de novo nos setores 110 a 114. A conferência por estrela se faz com a ferramenta de visibilidade do TESS, que tem a opção "Find if Targets are Observable in Cycle 9" (https://heasarc.gsfc.nasa.gov/wsgi-scripts/TESS/TESS-point_Web_Tool/TESS-point_Web_Tool/wtv_v2.0.py/, lida em 2026-11-23). Não rodei essa conferência.
- **Tempo até a primeira pontuação:** um setor dura cerca de 27 dias, e os dados costumam sair no MAST alguns meses depois (**não confirmado**; a página não dá o prazo). Para um lock em dezembro de 2026, estimo a primeira pontuação entre fevereiro e abril de 2027.
- **Limites do que ela prova:** um acerto diz que o sinal se repetiu na hora prevista. Não diz que é planeta: uma binária eclipsante também se repete. A rota mata alarmes falsos e sistemáticos, não falsos positivos astrofísicos.
- **Riscos:**
  - **o holdout não está validado.** A v0.2.1 fechou sem aprovação, e seu registro diz que nenhum texto pode afirmar que o holdout é seguro (`docs/validation/v0.2.1/closing-2026-10-27.md:80-85`). O lock precisa de aceitação sintética própria do avaliador (sinais injetados em segmentos "futuros", com janelas de controle);
  - **potência:** esses sinais foram achados somando vários setores. Num setor só, muitos ficam "não avaliáveis". O claim deve ser populacional (profundidade somada nas janelas previstas contra as de controle), com mínimo de alvos avaliáveis fixado antes;
  - **produto de dados:** muitas dessas estrelas só têm FFI. O adaptador do Refute lê SPOC de 2 minutos. Os hospedeiros que já são TOI têm mais chance de ter 2 minutos;
  - **terceiros:** o veredito é sobre o claim "o sinal se repete nas janelas previstas", nunca sobre os autores. Recomendo avisar os autores antes do lock, citar a lista com a licença dela e dar prazo de resposta antes de publicar um resultado negativo. Usar as previsões como entrada não as torna candidatos do Refute, e nada é submetido.
- **Contra a rota (a), como primeiro claim confirmatório:**
  - a rota (e) é mais barata e mais rápida, não depende da versão 5 e independe tanto do TFOPWG quanto dos dados da busca;
  - a rota (a) testa a classificação contra outro instrumento, que é a pergunta mais forte, mas pede um adaptador novo e deixa metade da bateria sem dado;
  - **elas respondem perguntas diferentes** (repetição do sinal contra natureza do sinal). Não se substituem.

**Outras rotas consideradas**
- **K2:** sobreposição com setores eclípticos do TESS; catálogos menos uniformes. Não li fonte (**não confirmado**).
- **Registros de acompanhamento do TFOP no ExoFOP:** não são independentes do TFOPWG, e a política de uso é condição aberta no projeto.

**10.3 Recomendação**
- **Primeiro claim confirmatório no tempo: a rota (e).** Pode ser travada antes de a versão 5 existir, porque usa o avaliador de holdout e não a bateria. Condição: a aceitação sintética do avaliador passar antes do lock.
- **Primeiro claim confirmatório da bateria nova: a rota (d1),** precedida pela contagem da fase 1. É a que testa classificação com rótulos independentes sem adaptador novo.
- **A rota (d2) vem junto,** porque é a calibração que a arquitetura exige.
- **A rota (a) fica como fase posterior,** se um adaptador de FFI for construído. É a mais independente para classificação e a mais cara.
- **A rota (b) roda em paralelo,** sem esperar por ela.

**10.4 O ecossistema e o posicionamento**

| Projeto | O que é | Relação sugerida com o Refute |
|---|---|---|
| **Avril** (https://github.com/Avril-Exoplanet/Avril, Apache-2.0, 433 estrelas, 3 commits) | Busca local em dados TESS com registro de auditoria e manifestos congelados. Sem pré-registro. Lista como trabalho futuro "TIC-disjoint sealed split", injeção e recuperação, e controles negativos. Diz que suas checagens "do not establish population-level completeness or false-positive calibration". Não publica lista de candidatos | **Colaborador ou fonte de claims.** O que falta a ele é o que o Refute tem. Hoje ainda não há lista para auditar |
| **eumemic/exoplanets** (https://github.com/eumemic/exoplanets, MIT; resultados CC BY 4.0) | Busca em cerca de 9.979 anãs K e M, com `candidates.csv` e `predictions.csv` (instantes de trânsito previstos até junho de 2027). Usa os testes do LEO-Vetter (13 de alarme falso e 4 de falso positivo), centroide por imagem de diferença e TRICERATOPS em média de 10 execuções. Sem pré-registro. Injeção com SNR 10: 52 a 62 % de recuperação | **Lista pública que o Refute pode auditar prospectivamente** (rota e): as previsões já existem com data |
| **TESS-ExoClass** | Métricas do Robovetter sobre TCEs do SPOC, ajustadas à mão para imitar a triagem manual de TOIs | Referência de desenho (saída em níveis) |
| **SHERLOCK** (MIT, segundo o assessor; não li) | Pipeline de busca com vetting e TRICERATOPS | Comparador ou fonte de claims; **não confirmado** |
| **nasa/ziggy** | Infraestrutura de pipeline herdada do SPOC | Não relevante |
| **pearsonkyle/Exoplanet-Artificial-Intelligence** | Parado desde 2020 | Não relevante |
| **MakazhanAlpamys/NASA-Exoplanet-Detection-AI** | Sem licença | Não relevante |
| **oscaribv/tango**, **orionlee/PH_TESS_I_LightCurveViewer** | Animações e visualizador | Não relevantes |

**O posicionamento "Refute = camada pré-registrada de falsificação e auditoria sobre buscas e vetters existentes" é apoiado?** Sim, com duas condições.
- **Apoiam:**
  - nenhum dos vetters lidos tem pré-registro, lock ou dado escondido;
  - Dallas et al. declaram seus números como "in-sample";
  - o Avril lista como faltantes exatamente o conjunto selado e a injeção em ruído real;
  - já existem listas públicas de candidatos com previsões datadas.
- **Condição 1:** a autoridade da camada vem do processo (lock, metade escondida, pontuação determinística), não da bateria, que segue `not_validated`. Auditar um claim alheio não exige que a bateria do Refute seja melhor que o vetter auditado.
- **Condição 2:** valem as regras de sempre. Vereditos são sobre claims, nunca sobre autores. Resultado negativo sobre trabalho de terceiros só sai depois do prazo de resposta. Nada é submetido automaticamente.
