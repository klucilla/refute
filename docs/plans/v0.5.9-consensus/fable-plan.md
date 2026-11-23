# Plano da fase seguinte à v0.5.8: recomendação independente

Lido em `4a704f0f` (`/home/claude/wt-v059`), somente leitura, em 2026-11-23. Nada foi commitado, alterado ou enviado ao GitHub. O único arquivo escrito é este.

**Recomendação:** abrir a **v0.5.9 "Entrada por efeméride"** (bateria versão 5), com uma parte exploratória em TOIs já expostos e uma parte confirmatória sob lock em TOIs não expostos.

**Ressalvas sobre o que fiz**
- As recontagens são minhas, **exploratórias**, sem revisão do Codex, feitas com `python3 -I` (só biblioteca padrão) sobre `docs/validation/v0.5.8/stability-records.json`, `docs/validation/v0.5.6/part-a-records.json`, `part-b-records.json`, `part-a-frame.csv`, `part-b-exposure.json` e os dois sorteios.
- Não rodei código do projeto, testes nem downloads. Não há `.venv` aqui.
- GitHub só por `gh api` de leitura: #218, #59, #219, issues abertas, `main` e tags.
- Um fato externo, com URL e data, na seção 4.

## 1. Conferência do portão da v0.5.8

- **A revisão existe:** `docs/gates/v0.5.8-review.md`, veredito `WEAKENED`, um achado importante e nenhum crítico (linhas 18 e 69).
- **Achado importante rastreado:** issue #219, fechada como concluída em 2026-11-23T20:20:29Z (conferido por `gh api`), com a correção datada `docs/reports/v0.5.8-report-correction-2026-11-23.md`. O relatório aprovado não foi editado.
- **Achados menores:** estão no #59 (comentário 7112886489). O da verificação por tag foi respondido: `docs/gates/v0.5.8-verify-locked-tags.md`, PASS conjunto, 10 de 10.
- **Critérios de saída:** os cinco estão marcados, cada um com evidência (`ROADMAP.md:1178-1212`).
- **Fase atual:** "None open" (`ROADMAP.md:51`). A fase anterior é a v0.5.8.
- **Emenda de 2026-11-21** (`ROADMAP.md:28-34`): o avanço é permitido pelo caso **(a)**, porque a v0.5.8 cumpriu os próprios critérios. A bateria v0.5 segue no caso **(c)**: toda saída da fase nova carrega o rótulo 'WEAKENED; does not meet D1, D2, D4, T2a' e `method_status: not_validated`.
- **Conclusão:** não falta nada para planejar. Abrir a fase é decisão do mantenedor.

**Correções ao contexto recebido**
- **288 contra 47.** O 288 (`docs/validation/v0.5.6/part-b-prep.md:84`) vem da primeira varredura de exposição, substituída por `part-b-exposure.md:39`, que dá **197**. A parte B conferiu 153 e escolheu 150. Sobram **44 nunca conferidos** (47 não escolhidos, daí o "47").
- **PCs não expostos** da metade de confirmação: **2.098** (`part-b-exposure.md:41`), não 2.099.
- **"17/150 contra 1/150"** são eventos (REFUTED com o sinal casado com o TOI). REFUTED simples foi 38 contra 13 (`docs/reports/v0.5.6-report.md`, tabela "All outcomes").
- **Possível erro menor no relatório aprovado.** `docs/reports/v0.5.8-report.md:105` diz que, dos 15 SNRs que mudaram, 12 ficaram menores. Minha recontagem dá **13 menores e 2 maiores** (TOI-3060.01 e TOI-1267.01). O 12 coincide com a contagem da porta 3 no painel `same`. Não muda porta nem veredito. Sugiro conferir e, se valer, registrar no #59 com correção datada, sem editar o relatório.

## 2. Recomendação em um parágrafo

**v0.5.9 "Entrada por efeméride"** (no repositório: "v0.5.9 Ephemeris entry"). A v0.6 é o pack de estrelas variáveis (`ROADMAP.md:1227`) e não deve começar com saídas que mudam de classe em um caso a cada sete. **A pergunta:** quando a bateria entra pela efeméride do TOI, com um reajuste limitado e declarado, e a saída só vale se for a mesma num conjunto declarado de perturbações pequenas, a classe da saída deixa de depender de onde o ajuste começa? **Por que agora:** a v0.5.8 mediu três coisas que apontam para o mesmo lugar. A classe mudou em 15 de 107 saídas decididas (`docs/reports/v0.5.8-report.md:56`). A mudança não se prevê pelos registros (12 de 150, linha 57), então um rótulo "frágil" calculado depois não resolve: é preciso perturbar de fato. E o ajuste tem mais de um ótimo em 15 de 167 (linha 58). Sem tratar a entrada, qualquer leitura por TOI (inclusive a segunda leitura prospectiva dos PCs) travaria saídas instáveis.

### 2.1 O que os registros da v0.5.8 dizem sobre a causa (recontagem exploratória)

Olhei as 13 mudanças de classe decididas em execuções concluídas, mais a única INCONCLUSIVE que virou SURVIVED. Elas se dividem em dois grupos.

| Grupo | TOIs | O que aconteceu |
|---|---|---|
| **A. O ajuste semeado é pior** (SNR mais de 10 % abaixo do da busca) | 7: TOI-2427.01, 2407.01, 399.01, 357.01, 2111.01, 2193.01, 3165.01 | O ajuste semeado ficou preso perto do período do catálogo. Em 6 dos 7, o ajuste da busca estava pelo menos 4 vezes mais longe do período do catálogo, com SNR maior. Dois deles saíram da efeméride (2427.01 e 2193.01). |
| **B. O ajuste é quase o mesmo** (SNR dentro de 1 %; época a 2 até 8 minutos) | 6 decididas: TOI-2357.01, 1062.01, 1288.01, 3040.01, 5515.01, 3753.01 (mais 6450.01, sorteada) | Um único bloco de sensibilidade ou uma estatística cruzou o limiar. Quatro das seis foram em `systematics.background`. |

- **Grupo A, leitura.** O reajuste do modo semeado só anda um passo fino em torno do período de partida (`src/refute/packs/tess/search.py:205-208`), e a máscara do detrend usa a época de partida (`pipeline.py:230-231`). Com anos de dados, o período do catálogo pode estar fora desse passo, e o sinal dobra borrado. É inferência minha, a partir das diferenças de período e SNR. Não foi conferida nas curvas de luz.
- **Grupo B, leitura.** A sensibilidade de `systematics.background` (`power.py:205-226`) foi de 1,0 para 0,004 em TOI-2357.01, de 1,0 para 0,118 em TOI-3040.01 e de 0,9985 para 0,6575 em TOI-1288.01, com o SNR igual. Isso não é ruído de sorteio (2.000 sorteios, `core/sensitivity.py:58`): é o erro medido do fundo (`battery.py:73-108`) mudando muito com um deslocamento de época de um ou poucos passos.
- **No total,** o bloco de fundo ficou abaixo do exigido em 8 das 13 mudanças decididas.

**Onde discordo do plano anterior** (`/home/claude/out/plano-v0.5.8-fable.md`, seções 3 a 5)
- **"Efeméride sem reajuste": não recomendo.** O grupo A mostra que ficar preso ao período do catálogo piora o ajuste. O caminho é o reajuste limitado e declarado, largo o bastante para alcançar o ótimo dos dados dentro da regra de identidade.
- **Semente independente do ajuste: mantenho, mas não é a causa principal.** Em TOI-1062.01 a potência caiu de 0,95 para 0,877, cerca de 15 erros-padrão. A semente separa efeitos, não os remove.
- **PCs:** o plano anterior guardava os PCs para a fase +2. Proponho usá-los já como alvos do claim de estabilidade, que não precisa de disposição (seção 3 e decisão 2).
- **Faltava:** mudança de regra pede revisão cega (CLAUDE.md, "A blind review only for rule changes"). A versão 5 muda a regra da saída, então a revisão cega entra.

## 3. Exploratório ou confirmatório?

| Parte | Modo | Codex | Alvos |
|---|---|---|---|
| Etapa 0: script commitado que refaz a tabela da seção 2.1 | Exploratório, sem portas | 1 rodada (junto com o desenho) | Só registros commitados |
| Documento de aceitação da versão 5 e seus testes sintéticos | **Confirmatório** (mudança de regra) | Até 3 rodadas, mais 1 revisão cega | Só dados sintéticos |
| Parte A: versão 5 em TOIs já expostos | Exploratório (nunca veredito) | 1 rodada | 108 TOIs, conjunto conhecido |
| Parte B: claim de estabilidade sob lock | **Confirmatório** | Até 3 rodadas no lock e no veredito | TOIs não expostos |

**Pool não exposto** (recontagem exploratória: quadro congelado, menos `exposed_tics`, menos todo TIC conferido nos sorteios A e B)

| Estrato | Metade de confirmação | Metade de exploração |
|---|---|---|
| Braço planeta | 44 | 141 |
| FP | 207 | 394 |
| KP | 170 | 138 |
| PC | 2.098 | 2.139 |
| APC | 257 | 217 |
| Total (com CP, FA e em branco) | 2.844 | 3.097 |

- A elegibilidade (SPOC de 2 minutos, pelo menos 2 trânsitos previstos) só se decide no sorteio. Taxas vistas: 150 de 204 em FP, 150 de 153 no braço planeta (parte B), 120 de 140 no braço aberto (parte A).
- Uma busca grosseira nos arquivos mudados desde a varredura (`c4d6fa3`) não achou TIC novo do quadro fora desse conjunto. A fase refaz a varredura no commit do lock.

**O claim da parte B (proposta)**
- **Conjunto:** PCs da metade de confirmação, não expostos, do quadro congelado da v0.5.6 (`part-a-frame.csv`, lido em 2026-11-22). Sorteio de **600 elegíveis**.
- **Semente nova:** uma rodada do drand fixada no claim antes do lock e publicada depois dele, como na v0.5.6. Regra: `sha256(randomness | v0.5.9 | part-b)`.
- **Duas entradas por TOI, mesma versão 5, mesmos arquivos:**
  - **E:** parte da efeméride do TOI;
  - **S:** parte da busca cega da própria bateria. Só roda quando a saída E é decidida.
- **Denominador:** saídas E decididas (SURVIVED, WEAKENED ou REFUTED) cuja busca casou com o TOI (regra de identidade da v0.5.6).
- **Evento (flip):** a classe da saída S difere da E. Uma execução S que não termina OK conta como flip, como na porta 1.
- **Critério primário:** limite superior de Wilson 95 % de flips sobre o denominador **no máximo 0,10**. É a porta 1 da v0.5.8 (5 de 107) escrita como claim. A versão 2 mediu 0,140 (0,087 a 0,218).
- **Guarda de decidibilidade:** saídas E decididas sobre TOIs rodados **pelo menos 0,10**. Sem ela, a estabilidade se alcança deixando tudo INCONCLUSIVE.
- **Mínimos:** denominador de pelo menos 60; perdas (ERROR ou sem registro) até 10 % dos sorteados.
- **Veredito:** SURVIVED (primário e guarda), WEAKENED (primário vale, guarda falha), REFUTED (primário falha), INCONCLUSIVE (mínimos, perdas ou execução incompleta).
- **Regra de parada:** uma só execução. Depois dos primeiros 200 TOIs, lê-se apenas a contagem de saídas E decididas no ledger: abaixo de 24, a execução para e o claim fica INCONCLUSIVE. Nenhum flip é lido antes do fim. O veredito sai só do script de avaliação.
- **Limiares fixados antes de qualquer alvo real:** todos os números acima entram no documento de aceitação, commitado antes do código e antes da parte A. Vêm da porta 1 e da família sintética S8 (seção 4), não das saídas da parte A.

## 4. Desenho da mudança em `src/`

**O que muda** (estimativa: 350 a 450 linhas, mais testes)

| # | Arquivo e linha | Mudança |
|---|---|---|
| 1 | `src/refute/packs/tess/params.py:409` | `Literal[1, 2, 3, 4]` ganha o 5 |
| 2 | `params.py:373-383` (ao lado de `V052Params`), `:497-515`, `:519-556` | Seção nova `entry`, presente só na versão 5 e ausente do dump nas outras (tupla da linha 513). A linha 529 passa a valer só para as versões 3 e 4 |
| 3 | `src/refute/packs/tess/entry.py` (novo) | Reajuste limitado em duas passadas, medida numa efeméride fixa, lista de perturbações, regra de consenso |
| 4 | `pipeline.py`, depois de `attack_candidate` (`:192-333`) | Função nova `attack_ephemeris`, que reusa o bloco de testes (`:275-289`) e `v05_tests` (`:335-468`) |
| 5 | `power.py`, depois de `:299-302` | `target_seed(nome, target_key)`: semente das simulações sem período, época ou profundidade ajustados. `pipeline.py:364` escolhe a semente pela versão |
| 6 | `centroid_v5.py:184-196` e `:322-328`; `battery.py:111-127` | Caminho conferido só para a versão 5: covariância que não é positiva definida ou qui-quadrado negativo dão `centroid_shift` INCONCLUSIVE com o motivo, nunca ERROR |
| 7 | `pipeline.py`, ao lado de `v05_record` (`:785`) | Registro da versão 5 com os blocos `entry` e `stability` |

**As regras da versão 5**
- **Reajuste limitado e declarado:** período dentro de 0,001 relativo do de partida e época final a até meia duração do TOI. É a regra de identidade da v0.5.6, agora como limite do ajuste. Duas passadas: máscara pela efeméride de partida, ajuste na janela, máscara refeita pelo ajuste, ajuste fino.
- **Entrada não resolvida:** ótimo na borda da janela ou fora da regra de identidade dá INCONCLUSIVE com o motivo. Cobre os 4 ajustes que saíram da efeméride na v0.5.8.
- **Perturbações declaradas** (seis, uma por vez, testes avaliados na efeméride fixa, sem novo reajuste):
  - época: mais e menos D/20, o passo de época do ajuste (`final_oversample: 20`, `calibration/v0.5.6/claim.yaml:125`);
  - período: mais e menos um passo fino, D·P/(6·T)/10 (`search.py:205-208`; `claim.yaml:122`);
  - duração: mais e menos 5 %, um passo da grade de 21 pontos (`search.py:200`; `claim.yaml:124`).
- **Por que esses tamanhos:** são a resolução do próprio ajuste. Uma saída que muda com menos do que o ajuste consegue distinguir não é propriedade do sinal.
- **Consenso:** a saída vale se a classe for a mesma na base e nas seis. Senão, INCONCLUSIVE com a perturbação que discordou. A regra só rebaixa, nunca promove. Perturbação que não roda (cobertura zero) também dá INCONCLUSIVE.
- **Custo:** as perturbações só rodam quando a saída base é decidida.

**O que fica idêntico**
- Todas as funções de teste, limiares e valores de `stronger`; a regra de sensibilidade (0,95; 2.000 sorteios, `core/sensitivity.py:56-58`); papéis e estágios; a agregação (`core/verdict.py:235-270`); o detrend; a busca.
- As versões 1 a 4: `attack_candidate`, `candidate_seed` e `combine` não mudam para elas.
- O rótulo: a versão 5 usa os mesmos testes e carrega 'WEAKENED; does not meet D1, D2, D4, T2a'. Ela **não foi medida** contra D1, D2, D4 e T2a. Espero igual ou pior em D2, D4 e T2a, porque o consenso só tira saídas decididas (expectativa, não fato).

**Como a versão 2 e os locks antigos continuam reproduzíveis**
- **Versão 2:** registros "dourados" da versão 2 em curvas sintéticas, gerados em `4a704f0f` e commitados com SHA-256 **antes** do código. Depois da mudança, igualdade byte a byte.
- **Locks antigos:** qualquer commit em `src/` muda o hash de código, e os 10 locks ficam `TAMPERED` na árvore atual, só no componente de código (`src/refute/core/lock_compat.py:10-12`; `docs/lock-format.md:255-282`). A verificação completa é por tag, no ambiente de cada tag: `scripts/verify_locked_tags.py` (entrada da v0.5.6 em `:79-81` e `:185`), já com PASS 10 de 10.
- **Nesta fase:** rodar o script de novo logo depois do primeiro commit em `src/` e antes do lock novo, guardando a saída.
- **Risco específico:** se a seção nova vazar para o dump de claims antigos, o componente de claim também quebra (issue #30). Um teste de CI sem rede confere, para cada lock commitado, que o hash do claim resolvido ainda é o do lock (#59, comentário 7101747897, item 5).
- **Lock novo:** tag `v0.5.9-partb-lock` e entrada em `DIRECT_LOCKS`, no mesmo bloco do lock.

**Aceitação sintética, escrita antes do código** (sinais injetados, sem rede)

| # | Caso | Passa quando |
|---|---|---|
| S1 | Planeta injetado; 20 efemérides de partida espalhadas na janela, com lacuna de mais de 300 dias nos dados | Todas chegam ao mesmo ótimo (a até um passo fino) e à mesma classe |
| S2 | Período de partida fora da janela | INCONCLUSIVE "entrada não resolvida", nunca outro sinal em silêncio |
| S3 | Semente | Igual entre perturbações do mesmo alvo e teste; diferente entre alvos e entre testes |
| S4 | Consenso | Tabela de combinações: nunca promove; uma discordância dá INCONCLUSIVE e nomeia a perturbação |
| S5 | Covariância singular e não positiva definida | Versão 5: `centroid_shift` INCONCLUSIVE com motivo e cobertura. Versão 2: comportamento igual ao de hoje |
| S6 | Regressão da versão 2 | Registros dourados idênticos byte a byte |
| S7 | Locks | Hash do claim resolvido de todo lock commitado inalterado |
| S8 | Família sintética nova, semente nova (200 curvas: planetas e binárias eclipsantes, efeméride de "catálogo" com erro) | Flips E contra S: Wilson superior no máximo 0,10 com denominador de pelo menos 60; fração decidida da versão 5 pelo menos a da versão 2 menos 0,10; REFUTED em planetas sintéticos no máximo 0,05 |

- S1 a S7 são testes de unidade e entram no CI. S8 roda uma vez, com o código congelado.
- O conjunto de confirmação C1 da v0.5 já foi gasto e não é reusado.

**Fato externo que apoia o reajuste.** Dragomir e colegas simularam o envelhecimento das efemérides do TESS e estimam que, um ano depois das observações, cerca de quatro em cada cinco planetas simulados já teriam incerteza de trânsito acima de 30 minutos (https://arxiv.org/abs/1906.02197, lido em 2026-11-23 pelo resumo; não conferi no PDF).

## 5. As 5 execuções em ERROR da v0.5.8

| TOI | Parte | v0.5.6 | Causa (do registro) | Tipo |
|---|---|---|---|---|
| TOI-734.01 | B, FP | WEAKENED | `OverflowError` em `battery.py:123`, via `centroid_v5.py:328` | Numérico, depois do ajuste |
| TOI-5218.01 | A, planeta | INCONCLUSIVE | `LinAlgError: Singular matrix` em `centroid_v5.py:187` | Numérico, depois do ajuste |
| TOI-531.01 | A, aberto | REFUTED | Tempo esgotado de 600 s na consulta ao MAST | Rede, antes do ajuste |
| TOI-2346.01 | A, planeta | INCONCLUSIVE | Download da curva de luz falhou | Rede |
| TOI-7393.01 | A, planeta | INCONCLUSIVE | Download do arquivo de píxeis falhou | Rede |

- **Não repetir os cinco no procedimento da v0.5.8.** Nenhuma porta mudaria (`docs/reports/v0.5.8-report.md`, "The five failed runs do not decide any mark"), e cada reexecução pede aprovação própria.
- **Os dois numéricos são corrigidos na versão 5** (item 6 da seção 4) e entram na parte A como casos nomeados. Nos dois, o mesmo TOI rodou sem erro na v0.5.6: o defeito depende do ajuste.
- **Os três de rede não são defeito de código.** Nada muda em `src/`. O runner novo declara novas tentativas com espera, no script.
- **Aprovação:** a parte A roda TOIs já expostos com uma versão nova. Para não haver dúvida sobre a regra de reexecução, a decisão de abertura no #218 registra o conjunto, o motivo e o procedimento exato **antes** de rodar, como na v0.5.7 e na v0.5.8.
- Os registros da v0.5.8 ficam como estão: 5 ERROR, não repetidos.

## 6. Escopo

**Dentro**
- Etapa 0, documento de aceitação, versão 5 (seção 4), parte A, parte B, relatório e rascunho local de dataset.
- **Parte A:** os 107 decididos da v0.5.8 mais TOI-5218.01 (108 TOIs), entradas E e S.
- **Do #59:**
  - `OverflowError` e `LinAlgError` do `centroid_v5` (comentários 7081325757, item 2, e 7099778438);
  - higiene dos runners (comentário 7101747897, itens 1 a 5): `started_utc` de máquina, scripts de relatório commitados antes do primeiro resultado, `mode` e rótulo em todo registro, exclusão por exposição reproduzível sem `.cache` (ou o limite declarado), teste de CI dos locks;
  - JSON com `newline="\n"` (7104810173); janela de admissão e escoamento nomeados à parte (7100100258); estado terminal coerente (7086792355).
- **Do portão da v0.5.8** (comentário 7112886489): segunda rodada do Codex quando a rodada de desenho voltar `REFUTED`; conferir o SHA enviado com `gh api` antes de rodar.
- **Do #219:** nenhum texto diz "só a semente mudou". Toda comparação nomeia as duas entradas.

**Fora (ficam para depois)**
- D1, D2, D4 e T2a (#201, #202, #211): não são alvo. O rótulo fica.
- **A sensibilidade de `systematics.background`** (seção 2.1): registrar no #59 como achado exploratório. Nenhum teste, limiar ou regra de sensibilidade muda. Proposta nesse sentido encerra a fase, como na v0.5.8.
- Defeito de meio período da busca (#59, 7081325757, item 1); #204, #203, #200, #183; #212 (picos diferentes entre máquinas).
- Segunda leitura prospectiva dos PCs (#24, #25), publicação no Zenodo, deploy do site, T3b (resposta do NExScI até 2026-12-05), v0.6.
- A segunda semente deslocada da v0.5.8 (não rodada): o conjunto de perturbações a substitui.

## 7. Critérios de saída e portas

**Critérios de saída**
1. O script da etapa 0 e seu registro estão commitados antes de qualquer código, reproduzindo a tabela da seção 2.1 ou registrando a diferença.
2. O documento de aceitação (S1 a S8, tamanhos das perturbações, janela e limiares da parte B) está commitado antes do primeiro commit em `src/`, com as rodadas do Codex, a revisão cega e a aprovação do mantenedor no #218.
3. Depois da mudança: registros dourados da versão 2 idênticos; suíte afetada passando (contagens do JUnit XML); teste de CI dos locks passando; `verify_locked_tags.py` com PASS 10 de 10, saída guardada.
4. S1 a S8 rodados e relatados como vieram, cada um com evidência. Nenhum alvo relaxado.
5. Parte A: os registros das 108 existem por entrada, com `started_utc` de máquina, `mode: exploratory`, rótulo, cobertura e proveniência. As portas P1 a P4 estão marcadas. Os scripts foram commitados, e o SHA conferido, antes do primeiro resultado.
6. Parte B: ou o claim foi travado antes de seus alvos serem sorteados ou lidos, rodou uma vez e o veredito está relatado como veio; ou uma porta não foi encontrada e a fase fecha com limites declarados, sem lock.
7. Relatório em rascunho para aprovação, com o rótulo e os alvos falhados da v0.5 à vista, e o tratamento dos 5 ERROR registrado.
8. Revisão do Codex da rodada e revisão de portão independente.

**Portas, escritas antes dos resultados** (marcas exploratórias, nunca vereditos; execução que não termina OK conta contra)
- **G0, aceitação:** S8 falhou, não há lock. Uma revisão do desenho é permitida, com família sintética nova. Segunda falha fecha a fase com limites declarados.
- **P1, convergência:** nos 7 TOIs do grupo A, o SNR da entrada E fica a até 10 % do SNR da entrada S em pelo menos 6.
- **P2, independência da partida:** no máximo 5 saídas E decididas mudam de classe na entrada S.
- **P3, decidibilidade:** pelo menos 80 dos 107 seguem decididos na entrada E.
- **P4, sem erro numérico:** zero ERROR numérico; TOI-734.01 e TOI-5218.01 terminam com status e motivo.
- **Regra:** P2 ou P3 não encontrada, não há lock (mesma regra de G0). P1 e P4 não encontradas são relatadas e decididas pelo mantenedor.

## 8. Orçamento

| Item | Estimativa | Teto |
|---|---|---|
| CPU | 56 CPU-h (aceitação 8; parte A 18; parte B 30) | 95 |
| Downloads | 224 GB (parte A 34; parte B 190) | 280 GB |
| Disco de pico | 13 GB | 20 GB |
| Mantenedor | 6 a 8 h, em 7 paradas | |
| Prazo | 10 a 14 dias corridos | 21 (até 2026-12-14) |
| Codex | Desenho até 3 rodadas; código 1; parte A 1; lock até 3; veredito e relatório até 3 | Uma conversa por tema |
| Subagentes Claude | 2: revisão cega da regra e revisão de portão (cerca de 200 mil tokens cada) | Aprovação prévia |

- **Base:** a v0.5.8 gastou 3,24 CPU-h e 52,6 GB em 167 TOIs, com pico de 6,60 GB a 10 workers (`docs/reports/v0.5.8-report.md:175-177`). Isso dá 0,019 CPU-h e 0,315 GB por TOI.
- **Não medido:** o custo de cada avaliação perturbada. Supus 60 % de uma execução inteira. O piloto de 10 TOIs da parte A mede isso antes do resto.
- **Ledger de tetos:** obrigatório (acima de 5 CPU-h).
- **Máquina:**
  - processadores 0 a 7 sempre livres (afinidade 8 a 31), prioridade BelowNormal;
  - segunda a sexta, das 8h às 18h: no máximo 10 workers e 2 downloads; fora disso, até 20 workers e 6 downloads;
  - lotes de até 30 minutos; tudo retomável (um registro por alvo, lock do sistema operacional, escrita atômica);
  - píxeis apagados por alvo com manifesto; curvas de luz apagadas ao fim, só dentro de `.cache/v059`.
- **Tempo de download:** a v0.5.8 baixou 52,6 GB em cerca de 2 horas de lotes com 2 downloads. 224 GB pedem cerca de 8,5 horas em horário comercial, menos à noite.

## 9. Paradas do mantenedor (não delegadas)

| Parada | Onde cai na fase |
|---|---|
| **Abrir a fase** | Dia 0. Decisão no #218 com: tetos, as 3 decisões da seção 11, o conjunto e o procedimento da parte A (regra de reexecução) e os 2 subagentes |
| **Mudança em `src/`** | Duas vezes: aprovar o documento de aceitação (antes do código) e aprovar o primeiro commit em `src/` (depois do Codex) |
| **Dependências** | Antes do lock. Recomendo registrar "nenhuma mudança nesta fase", para o diff ficar pequeno |
| **Lock e rodada do drand** | Depois de G0 e das portas da parte A: texto do claim, rodada, tag e entrada em `DIRECT_LOCKS` |
| **Reexecuções** | Nenhuma além do conjunto aprovado na abertura. A parte B roda uma vez. Os 5 ERROR da v0.5.8 não se repetem |
| **Texto público e site** | No fim: aprovar o relatório. O status no site vai por PR; merge e deploy são do assessor |
| **Zenodo** | No fim: só rascunho local em `.cache/v059/zenodo/`. O mantenedor publica, se quiser |
| **Código de terceiros** | Nenhum previsto. Se aparecer, para |
| **Exclusões fora de `.cache`** | Nenhuma prevista |
| **Fechamento** | Marcar critérios no ROADMAP e lançar a revisão de portão |

## 10. Os 5 maiores riscos

| # | Risco | Detecção precoce |
|---|---|---|
| 1 | O consenso derruba a decidibilidade (piora D2, D4, T2a) e a estabilidade vira "tudo INCONCLUSIVE" | Guarda de S8 e porta P3, as duas antes de qualquer lock; guarda no próprio claim |
| 2 | A janela mais larga escolhe outro alias de período ou outro sinal | S1 e S2 com lacunas de anos; campos `entry` (borda, distância ao catálogo); porta P1 |
| 3 | A fase vira a quarta rodada de correção disfarçada (alguém "conserta" `systematics.background`) | Lista fechada de arquivos da seção 4; regressão dourada da versão 2; regra de encerramento por proposta de limiar |
| 4 | A seção nova vaza para o dump de claims antigos e quebra o componente de claim dos locks | Teste S7 no CI antes do commit em `src/`; `verify_locked_tags.py` depois dele |
| 5 | Denominador pequeno (menos de 60 decididas) depois de gastar 190 GB, ou perdas de rede acima de 10 % | Parada declarada aos 200 TOIs, lendo só a contagem; novas tentativas no runner; tetos no ledger |

## 11. Decisões em aberto para o mantenedor

**Decisão 1: formato da fase**
- **(a) Recomendado: v0.5.9 completa** (versão 5 em `src/`, parte A, parte B sob lock). Responde à pergunta de uma vez. Custa as paradas da seção 9.
- **(b) Só protótipo fora de `src/`:** um script em `docs/validation/v0.5.9/` faz o reajuste largo e chama a bateria versão 2. Mais barato, sem lock. Não testa o consenso nem a semente, e não produz uma versão travável.
- **(c) Ir para a v0.6 com o rótulo:** permitido pela emenda. O pack novo herdaria o mesmo ajuste instável.

**Decisão 2: alvos do claim**
- **(a) Recomendado: 600 PCs da metade de confirmação** (2.098 disponíveis). Estabilidade não precisa de disposição. Não gasta o braço planeta (44) nem os FPs (207). As saídas travadas servem depois de linha de base para a leitura prospectiva.
- **(b) Só estratos rotulados da metade de confirmação** (planeta, FP, KP, APC: cerca de 560 elegíveis esperados). Preserva os PCs intocados. Gasta quase todo o pool rotulado num claim que não usa os rótulos.
- **(c) Misto, incluindo a metade de exploração não sorteada.** Mais alvos. Foge da regra "confirmar só na metade de confirmação".

**Decisão 3: o que o consenso faz**
- **(a) Recomendado: regra.** Saída instável vira INCONCLUSIVE. É mudança de regra: pede revisão cega e custa decidibilidade.
- **(b) Só rótulo:** o registro ganha `stability: fragile` e a saída não muda. Processo mais leve. Um SURVIVED instável continua SURVIVED.
- **(c) Regra com 4 perturbações** (sem a duração): cerca de um terço a menos de CPU nas decididas. Deixa a duração sem teste.

## 12. O que vem depois

- **Se o claim sobreviver:** fase seguinte de segunda leitura prospectiva dos PCs, com a versão 5 travada, pontuada quando o TFOPWG mudar disposições.
- **Se não:** nota de limites declarados, e a escolha entre corrigir o erro de fundo de `systematics` num teste próprio ou seguir para a v0.6.

## 13. Incertezas que mantenho

- A leitura dos grupos A e B é inferência sobre registros. Não vi as curvas de luz, e o papel da duração de partida não foi separado do papel do período.
- Não sei se os testes podem ser avaliados numa efeméride fixa sem tocar em mais código do que a seção 4 lista. Não prototipei.
- Não conferi se a família sintética do pack cobre arquivos de píxeis. Se não cobrir, S8 fica no estágio 1, e `centroid_shift` e `aperture_depth` só são exercitados na parte A.
- A fração decidida da versão 5 é desconhecida. O sorteio de 600 e o mínimo de 60 dependem dela.
- A contagem do pool vale para a varredura em `c4d6fa3`. Minha busca posterior foi por TIC, não por número de TOI.
- O quadro congelado não tem incerteza de período (a consulta em `part-a-frame.json` não pede esse campo). A janela, por isso, usa a regra de identidade e não o erro do catálogo.
- As linhas citadas valem para `4a704f0f`.
- A divergência 13 contra 12 da seção 1 é recontagem minha, não revista.
- Os números da seção 3 (0,10; 60; 600; 24) são proposta. Quem os fixa é o documento de aceitação, com o Codex e a revisão cega.
