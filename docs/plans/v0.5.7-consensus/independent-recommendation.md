# Next-phase plan: independent recommendation (Fable 5.2)

**Provenance (written by the maintainer's adviser).** One read-only session of Claude Fable 5.2, launched by the maintainer's adviser on 2026-11-23 at the maintainer's request (10:06), on klucilla/refute at `8d51c13`, with read-only `gh` and web search; 185,834 tokens, 22 tool calls, about 4.4 minutes. The report below is in Brazilian Portuguese, as asked; its recounts are exploratory and were not reviewed by Codex.

---

# Plano da próxima fase do Refute: recomendação independente

Lido no commit `8d51c13`, somente leitura, em 2026-11-23. Nada foi escrito, alterado ou enviado. As recontagens abaixo são minhas, feitas a partir de `docs/validation/v0.5.6/part-a-records.json` e `part-b-records.json`. São **exploratórias**: nenhuma é veredito e nenhuma foi revisada pelo Codex.

**Recomendação em uma frase:** a próxima fase deve atacar o **sinal do próprio TOI** (efeméride fixada), sem mexer em `src/` e sem tocar nas regras da bateria, e publicar o resultado por teste como dataset aberto. Mais dados por estrela (opção a) não é o gargalo que os registros mostram.

## 1. Diagnóstico

**O que a v0.5.6 estabelece**

- **Concordância, não detecção.** Nos 300 TOIs sorteados, a bateria refuta no sinal do TOI 17/150 FPs contra 1/150 planetas (`calibration/v0.5.6/part-b-verdict.md:7-8`). O relatório diz que isso não mede detecção independente (`docs/reports/v0.5.6-report.md:137`) e que os estratos são populações diferentes, sem ajuste por profundidade ou período (`:140`).
- **O processo de confirmação funciona.** Lock, drand, sorteio e execução única foram reproduzidos pelo portão (`docs/gates/v0.5.6-review.md`, seção 4). Este é o ativo mais sólido do projeto hoje.
- **A guarda só vale para o sinal casado.** O REFUTED simples em planetas confirmados é 13/150 (8,7 %, Wilson superior 0,143), e 12 desses 13 são em sinal que não é o do TOI (`docs/reports/v0.5.6-report.md:121`).

**Os dois gargalos, em ordem**

1. **Identidade do sinal: em boa parte é o domínio da busca, e tem conserto barato.**
   - A busca só cobre 0,5 a 20 dias (`src/refute/packs/tess/params.py:51-52`).
   - Nos 534 registros OK de A e B, 60 TOIs têm período fora desse domínio: **0 casados, 16 REFUTED**. Exemplos: TOI-1859.01 (63,5 d, achado em 5,29 d, `odd_even` fatal) e TOI-1758.01 (20,7 d, achado em 10,35 d).
   - Com período entre 0,5 e 15 d: 447 registros, 346 casados (77 %), 30 sem sinal na porta de SNR, 30 com período certo e época fora da tolerância, 41 em outro sinal.
   - Os 30 de "época fora" têm fator 1,0 e falham só na regra de meia duração (`calibration/v0.5.6/part_b_run.py:319`). Ex.: TOI-5300.01, SNR 121, 1,21 h de diferença contra 1,96 h de duração. A causa provável é a deriva da efeméride do TOI, mas não verifiquei.
   - Os casos de meio período do #59 (comentário 7081325757) são a mesma família: parte B tem 12 registros com fator 0,5.

2. **Decidibilidade: é a regra de agregação e de recusa por sensibilidade, não a falta de dados.**
   - Mesmo com o sinal casado, INCONCLUSIVE é 76/100 (planetas B), 57/87 (FP B), 59/87 (planetas A) e 65/90 (aberto A).
   - **Mais setores não mexem nisso** nos planetas casados da parte B: 0,78 (até 2 setores), 0,76 (3 a 5), 0,75 (6 ou mais). Na parte A há uma queda (0,76 para 0,56), então a evidência é mista, mas fraca.
   - O bloqueador dominante é `systematics`, de severidade *warning*: sozinho bloqueia 20 dos 76 (planetas B). Qualquer teste INCONCLUSIVE torna o resultado INCONCLUSIVE (`src/refute/core/verdict.py`, regra 3 de `aggregate`, linha ~243).
   - A recusa ocorre com SNR alto: TOI-1138.01 (SNR 113, 5 setores) tem potência 0,013 contra 0,95 exigidos para "subida de fundo de 0,8 da profundidade". A alternativa é simulada em `src/refute/packs/tess/power.py:205-228`.
   - Só `systematics` e `aperture_depth` explicam 45 dos 76 INCONCLUSIVE de planetas casados na parte B.
   - Esse é o mesmo muro de D2, D4 e T2a, que cinco fases não passaram sem relaxar regra. Atacá-lo de frente é polir a lente.

**Conclusão do diagnóstico.** O maior gargalo para valor externo é a identidade do sinal: sem ela, nenhuma saída por TOI é defensável. A decidibilidade é o maior gargalo científico, mas é o que tem maior risco de novo laço interno. A saída é mudar o ponto de vista: parar de exigir um veredito único por TOI e medir o que **cada teste** diz no sinal certo.

## 2. Avaliação das opções

Custos de referência medidos: A e B somaram 12,8 CPU-h e cerca de 185 GB para 540 TOIs, ou seja, 0,024 CPU-h e 0,34 GB por TOI. Cerca de 96 % dos bytes são arquivos de píxeis.

| Opção | O que entrega | Custo | O que pode dar errado | Mexe em `src/`? |
|---|---|---|---|---|
| **(a) Mais dados** (mais setores, 20 s, FFI) | Talvez alguma decisão a mais | Alto: adaptador novo, mais downloads | Os registros não mostram ganho com setores; 20 s não traz fótons novos; FFI não tem os mesmos produtos de píxel. Risco alto de laço | Sim |
| **(b) Efeméride do TOI** | Elimina o sinal errado; cobre períodos fora de 0,5 a 20 d | Baixo: um script, cerca de 13 CPU-h, cerca de 180 GB | Os testes podem se comportar diferente com candidato fixado; não resolve INCONCLUSIVE | **Não**, no modo exploratório (ver seção 3) |
| **(c) Bugs do #59** | Tira 2 ERROR em 540; teste de CI para os locks | 2 a 4 h de código | Sozinho não entrega nada visível | Sim: nova versão da bateria |
| **v0.6 Estrelas variáveis** | Domínio novo | Semanas; catálogos com licença restrita (TESS-EB, citado no CLAUDE.md) | Abandona a linha TOI antes de entregar valor; repete "fixar alvos antes de explorar" | Sim, pack novo |
| **Replicar artigos (v0.3)** | Ideia original | Alto por artigo; código de terceiros é parada do mantenedor | A v0.3 fechou `WEAKENED`, com 4 de 5 claims indecidíveis (`ROADMAP.md`, seção v0.3) | Provável |
| **v0.8 Refute@Home** | Computação voluntária | Muito alto | Não há carga para distribuir: a fase inteira custou 12,8 CPU-h | Sim |
| **Benchmark contra outro vetter** | Posição frente ao estado da arte | Médio; código de terceiros | Comparação desfavorável em decidibilidade | Não, mas é parada |
| **Triagem prospectiva de PCs** | O único teste de independência real: prever antes de a disposição existir | Cerca de 15 CPU-h e 200 GB para 600 PCs; espera de meses | Poucas mudanças de disposição no período | Não |

**Sobre o estado da arte** (lido em 2026-11-23): o LEO-Vetter se descreve como público e totalmente automático, com 91 % de completude e 97 % de confiabilidade em dados simulados (https://arxiv.org/abs/2509.10619). O ExoMiner++ publica um catálogo de classificações para TCEs de 2 minutos (https://arxiv.org/abs/2502.09790). O Refute não vai ganhar deles em decidibilidade. O diferencial dele é o processo auditável (lock, drand, cobertura, recusa por sensibilidade), e é isso que vale mostrar para fora.

## 3. Próxima fase recomendada

**Nome:** v0.5.7 "O sinal do próprio TOI" (efeméride fixada).

**Objetivo:** rodar os testes da bateria v0.5, sem mudança e com o rótulo de limites, na efeméride publicada do TOI em vez do sinal mais forte da busca, e publicar o que cada teste diz.

**Escopo**

- **Dentro:**
  - um script de execução em `docs/validation/v0.5.7/`, no molde de `part_a_run.py`;
  - os mesmos 540 TOIs de A e B, já expostos, o que dá uma comparação pareada "busca contra efeméride fixada";
  - um relatório e um dataset por TOI e por teste.
- **Fora:**
  - qualquer mudança em `src/`, em regras, limiares ou na agregação;
  - alvos novos da metade de confirmação;
  - correções do #59;
  - mais setores ou outra cadência.

**Por que não precisa de `src/`:** `attack_candidate` já recebe o candidato pronto (`src/refute/packs/tess/pipeline.py:192`), e `finalize_candidate` avalia um período dado (`src/refute/packs/tess/search.py:189`). Como fixar a época e medir profundidade e SNR nesse ponto é a pergunta de desenho para a rodada única do Codex. **Não verifiquei** se todos os testes aceitam períodos acima de 20 d ou abaixo de 0,5 d; o piloto responde.

**Portas, escritas antes de rodar** (exploratórias, nunca vereditos):

1. **Identidade resolvida.** No modo fixado, entre planetas confirmados com porta de SNR aprovada, REFUTED cai de 22 (9 em A, 13 em B) para no máximo 4 em 270.
2. **Teste discriminador.** Algum teste fatal falha em pelo menos 10 FPs e em no máximo 1 planeta (os FPs vêm só da parte B). Candidatos pelo que já se viu: `aperture_depth` e `odd_even` (`docs/reports/v0.5.6-report.md:125`).
3. **Fora do domínio da busca.** Nos 60 TOIs com período fora de 0,5 a 20 d, pelo menos 20 % terminam com resultado diferente de INCONCLUSIVE.
4. **Decidibilidade.** INCONCLUSIVE em planetas cai para 50 % ou menos. Espero que **não** seja encontrada. Se não for, fica registrado que o limite é a regra de recusa, e nada é ajustado nesta fase.

**Claim confirmatório que pode sair daqui** (fase seguinte, sob lock): "na efeméride do TOI, a taxa de REFUTED simples em FPs supera a de planetas, e a taxa em planetas fica em até 0,05 com Wilson superior até 0,10". É a guarda que o modo de busca não cumpre hoje (8,7 %, 0,143), sem a ressalva de "sinal casado".

**Critérios de saída verificáveis**

1. Script, portas e script de relatório commitados antes do primeiro resultado (achado do portão, #59, comentário 7101747897, item 2).
2. Piloto de 10 TOIs que casaram no modo de busca: o modo fixado reproduz o resultado teste a teste em pelo menos 9. Se não, parar e relatar.
3. Os 540 registros existem, cada um com `mode: exploratory`, rótulo de limites, cobertura e `started_utc` de máquina.
4. Relatório com a tabela pareada e cada porta marcada como encontrada ou não.
5. Uma rodada do Codex e uma revisão de portão curta.

**Orçamento**

- CPU: cerca de 13 CPU-h, com teto de 20.
- Downloads: cerca de 180 GB em duas noites. Os arquivos de píxeis foram apagados por alvo; se as curvas de luz ainda estão em cache, **não confirmei**.
- Horas do mantenedor: 4 a 6, em duas paradas (aprovar conjunto e custo; aprovar o texto público).
- Prazo: 10 dias corridos. Se estourar, parar e relatar.

**Entrega externa**

- Relatório público em `docs/reports/`.
- Uma página no site com as tabelas agregadas.
- Rascunho de dataset no Zenodo com os registros por TOI e por teste. São resultados do próprio Refute, permitidos pela regra de publicação de dados do CLAUDE.md; o mantenedor publica.
- Texto com o rótulo de limites, "exploratório" e o agradecimento do ExoFOP (`docs/plans/sources/v0.5.6-nexsci-answer-2026-11-22.md`).

## 4. As 2 a 3 fases seguintes

**Fase +1: confirmação do modo fixado, com o único pacote de `src/`.**
- Uma parada só do mantenedor para `src/`: entrada por efeméride como `discovery.version: 3`, guardas de covariância do `centroid_v5` (#59, comentários 7081325757 e 7099778438) e teste de CI com `verify_claim`.
- A versão 2 fica intacta, então os vereditos da v0.5 não mudam.
- Claim sob lock e drand em alvos não expostos.
- **Ponto de decisão:** sobram só 47 planetas confirmados não usados no pool (197 menos 150), contra 261 FPs. Com 47, um único evento já estoura a guarda de Wilson. O mantenedor escolhe entre incluir os KP (295 na metade de confirmação) ou ir para o prospectivo.

**Fase +2: segunda leitura prospectiva dos PCs.**
- Travar hoje as saídas por teste para uma amostra de cerca de 600 dos 2.100 PCs da metade de confirmação.
- Pontuar quando o TFOPWG mudar a disposição (PC para FP ou CP), em 6 a 12 meses.
- É o único desenho que responde a "concordância não é independência".
- Custo: cerca de 15 CPU-h e 200 GB.

**Fase +3: depende das portas.**
- Se a porta 2 foi encontrada: comparação com um vetter público (código de terceiros, parada do mantenedor) ou com o catálogo do ExoMiner++.
- Se a porta 4 não foi encontrada e o mantenedor quiser atacar decidibilidade: uma saída "perfil de evidência por teste" como formato novo, em vez de mexer nas regras de recusa.
- v0.6, v0.7 e v0.8 ficam onde estão até a linha TOI ter uma entrega externa usada por alguém.

**O que muda o rumo**
- Piloto falha (critério 2): o modo fixado precisa de `src/`; vira decisão do mantenedor antes de qualquer execução.
- Porta 1 não encontrada: o problema de identidade não é só o domínio da busca; investigar antes de qualquer claim.
- Porta 2 não encontrada: não há claim confirmatório útil; pular para a fase +2 ou encerrar a linha TOI com limites declarados.

## 5. Os 5 maiores riscos e como detectar cedo

| # | Risco | Detecção precoce |
|---|---|---|
| 1 | O candidato fixado muda a semântica dos testes (porta de SNR, pré-branqueamento, domínio de período) | Piloto pareado de 10 TOIs, antes da execução completa |
| 2 | INCONCLUSIVE não se move e surge a tentação de ajustar a regra de recusa (novo laço) | Porta 4 escrita antes; regra da fase: nenhuma mudança de regra. Se alguém propuser limiar novo, a fase parou |
| 3 | Faltam planetas não expostos para a confirmação (47) | Contar o pool na abertura da fase +1 e decidir KP ou prospectivo antes de escrever o claim |
| 4 | Saída por TOI lida como disposição ("o Refute diz que o TOI-X é falso positivo") | No site, só tabelas agregadas; por TOI apenas no dataset, com rótulo; texto aprovado pelo mantenedor; nada submetido |
| 5 | Excesso de processo e prazo | Plano de uma página, uma rodada do Codex, duas paradas, 10 dias. Estouro de qualquer um vira relatório curto, não nova rodada |

Risco menor: falhas de rede no MAST (4 dos 5 ERROR da parte B). O runner já é retomável; o teto de perdas fica declarado.

## Incertezas que mantenho

- As recontagens não foram conferidas por segunda pessoa nem pelo Codex.
- Não rodei código do projeto: a viabilidade do modo fixado sem `src/` vem da leitura das assinaturas, não de execução.
- A causa da "época fora" (deriva da efeméride) é hipótese.
- Os números do LEO-Vetter e do ExoMiner++ vêm dos resumos, não de leitura completa.
