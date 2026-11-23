# Plan for the phase after v0.5.7: independent recommendation (Fable 5.2)

**Provenance (written by the maintainer's adviser).** One read-only session of Claude Fable 5.2, launched by the maintainer's adviser on 2026-11-23 with the maintainer's approval (13:08), on klucilla/refute at `4b57f7c`, with read-only `gh`. Its recounts are exploratory and were not reviewed by Codex. The report below is in Brazilian Portuguese, as asked, unchanged.

---

# Plano da fase seguinte à v0.5.7: recomendação independente

Lido em `4b57f7c` (`/home/claude/wt-next2`), somente leitura, em 2026-11-23. Nada foi escrito, alterado ou enviado.

**Recomendação:** a próxima fase mede a **estabilidade das saídas** da bateria v0.5, sem tocar em `src/`, antes de qualquer v3. O motivo é que os registros já commitados mostram que a proximidade do limiar explica pouco, e isso muda o que a v3 precisa fazer.

**Ressalvas sobre o que fiz**
- As recontagens abaixo são minhas, **exploratórias**, sem revisão do Codex, feitas sobre `docs/validation/v0.5.6/part-a-records.json` e `part-b-records.json`.
- O worktree não tem `.venv`; usei `python3 -I` só com a biblioteca padrão para ler JSON. Não rodei código do projeto.
- Conferência: meu Fisher para 17/150 contra 1/150 dá 4,726e-05, igual ao veredito (`calibration/v0.5.6/part-b-verdict.md:3`).
- Não usei fontes da web; o rascunho `docs/reports/v0.5.7-report.md` não está commitado e não foi lido.

## 1. O que os registros commitados já respondem (frente 2)

**Os campos existem.** Cada teste guarda `sensitivity.<bloco>.probability`, `required_probability` e `detectable`: 4.820 blocos nos 534 registros OK. As estatísticas dos testes (sigma, BIC) só existem no texto de `message`.

**Perto do limiar há pouca coisa.** As simulações usam 2.000 sorteios (`src/refute/core/sensitivity.py:58`), então 2 erros-padrão em 0,95 valem cerca de 0,01.

| Margem até o limiar | Blocos PASS perto | Recusas perto | SURVIVED com PASS perto (de 31) | WEAKENED com PASS perto (de 60) |
|---|---|---|---|---|
| 0,005 | 9 | 8 | 2 | 0 |
| 0,01 | 21 | 21 | 2 | 2 |
| 0,02 | 43 | 30 | 2 | 4 |

- Empates exatos: 3 (TOI-1062.01 em `systematics.background`; TOI-973.01 e TOI-4188.01 em `period_alias`).
- Nenhum dos 374 INCONCLUSIVE viraria decidido só por recusas a até 0,02 do limiar.

**A proximidade não explica os dois flips do piloto.**
- TOI-1062.01 caiu de 0,95 para 0,877 com 1,83 min de época (`docs/validation/v0.5.7/diagnostic-rerun.md:9-10`). São cerca de 15 erros-padrão: a própria potência muda com o ajuste, não é ruído de sorteio.
- TOI-506.01 foi de 0,9445 para 0,226, com SNR 15,5 contra 8,2 (`diagnostic-rerun.md:13-14`): outro ótimo do ajuste, longe de qualquer margem.
- A semente das simulações depende do período, da época e da profundidade ajustados (`src/refute/packs/tess/power.py:299-302`), então qualquer mudança de ajuste troca também os sorteios.

**O claim da v0.5.6 parece robusto a isso.** Dos 17 eventos em FP, 4 têm a estatística que falha a menos de 1 sigma do limiar (TOI-3165.01, 3753.01, 2208.01, 2111.01). Tirando os quatro, 13 contra 1 dá p = 7,3e-04. O veredito não muda; isto é só leitura.

**Conclusão:** os registros dão um piso (4 a 6 de 91 saídas positivas "frágeis"), mas o piloto viu 2 de 10. A parte que falta só se mede rodando de novo, e ela é barata.

## 2. Avaliação das frentes

| Frente | Juízo | Por quê |
|---|---|---|
| 1. Entrada por efeméride em `src/` | **Depois**, na fase +1 | Sem saber quanto a saída oscila com o ajuste, a v3 pode congelar um veredito de fio de navalha na efeméride do catálogo |
| 2. Estabilidade | **Agora** | Etapa 0 custa zero; etapa 1 cerca de 4 CPU-h; decide o desenho da v3 |
| 3. Meio período e fora do domínio | **Adiar** | Só afeta o modo de busca; a entrada por efeméride contorna para TOIs. Os 60 fora de 0,5 a 20 d: 0 casados, 16 REFUTED |
| 4. Segunda leitura prospectiva dos PCs | **Fase +2** | Travar saídas por TOI com bateria instável desperdiça o único teste de independência |

**Três fatos que o plano da v3 precisa conhecer**
- `discovery.version` 3 e 4 **já existem** (v0.5.1 e v0.5.2; `src/refute/packs/tess/params.py:406-409`). A versão nova seria a 5, ou um campo de modo de entrada separado.
- Qualquer mudança em `src/` torna o lock da v0.5.6 `TAMPERED` na árvore atual (`src/refute/core/lock_compat.py:10-12`; `docs/lock-format.md:271-282`). `scripts/verify_locked_tags.py:74-76` vai só até a v0.5: o lock da v0.5.6 precisa de tag e entrada lá **antes** do primeiro commit em `src/`.
- Os dois ERROR de `centroid_v5` são 2 em 540; a correção é pequena e viaja junto com a versão nova.

## 3. Próxima fase recomendada

**Nome:** v0.5.8 "Estabilidade das saídas".

**Objetivo:** medir quantas saídas e quantos status de teste da bateria v0.5 mudam quando o mesmo sinal do TOI é reajustado a partir de outra semente, e publicar isso por teste.

**Toca em `src/`?** Não. Nenhuma regra, limiar, recusa ou agregação muda. Nenhum veredito muda.

**Escopo**
- **Dentro:**
  - etapa 0: script commitado que reproduz as contagens da seção 1;
  - etapa 1: reexecução TOI-semeada pareada com o registro da v0.5.6, em TOIs já expostos;
  - relatório e tabela por teste.
- **Fora:** `src/`, alvos novos, correções do #59 em `src/`, meio período, PCs prospectivos, qualquer ajuste de limiar ou de semente.
- **Faxina do dia 1** (só `tests/`, fora do hash de código): dar margem ao `max_shard_seconds=1.0` de `tests/test_v054_budgeted_v3.py:58`, para o CI parar de ficar vermelho a cada push.

**Conjunto da etapa 1** (fixado antes de rodar)
- os 107 registros casados e decididos (28 SURVIVED, 53 WEAKENED, 26 REFUTED);
- 60 dos 257 casados INCONCLUSIVE, sorteados com semente commitada;
- opcional: uma segunda semente deslocada de um passo de 2 min, só nos 107.

**Decisão que cabe ao mantenedor:** isto reusa o modo TOI-semeado depois de o piloto ter parado a v0.5.7. A pergunta é outra (estabilidade, não equivalência), mas precisa ser dita assim na abertura. A guarda de parada do `seeded_run.py` (linha 1231) não deve ser editada; um script novo em `docs/validation/v0.5.8/` importa as mesmas funções.

**Portas, escritas antes da etapa 1** (exploratórias, nunca vereditos)
1. **Saída estável.** No máximo 5 dos 107 decididos mudam de classe de saída.
2. **Flip previsível pelos registros.** Pelo menos 80 % dos status que mudam estavam a até 0,02 do limiar de potência ou a até 0,5 sigma do limiar da estatística. Espero que **não** seja encontrada.
3. **Ajuste com mais de um ótimo.** Em pelo menos 5 % dos 167, o SNR reajustado difere mais de 10 % do registrado.
4. **Eventos do claim.** Dos 17 FPs e 1 planeta REFUTED casados da parte B, pelo menos 15 FPs continuam REFUTED e no máximo 2 planetas ficam REFUTED.

Cada porta é contada no total e só com proveniência `same`. A etapa 0 **não tem portas**: eu já vi esses números.

**O que cada resultado decide para a v3**
- Porta 2 encontrada: basta um rótulo "frágil" calculado dos registros.
- Porta 2 não encontrada ou porta 3 encontrada: a v3 precisa de efeméride sem reajuste, semente das simulações independente do ajuste, e saída avaliada num conjunto declarado de perturbações.

**Claim confirmatório que pode sair daqui** (fase +1, sob lock, em alvos não expostos): "com entrada por efeméride, pelo menos X % das saídas decididas mantêm a classe em todas as perturbações declaradas". O X sai desta fase.

**Critérios de saída**
1. Scripts, sorteio dos 60 e portas commitados antes do primeiro resultado.
2. Etapa 0 reproduz a tabela da seção 1 ou registra a diferença.
3. Os 167 registros existem, com `started_utc` de máquina, `mode: exploratory`, rótulo de limites, cobertura e proveniência.
4. Relatório com flips por teste e por saída, intervalos de Wilson e cada porta marcada.
5. Uma rodada do Codex no desenho e uma revisão de portão curta.

**Orçamento**

| Item | Estimativa | Teto |
|---|---|---|
| CPU | 4 CPU-h (107 custaram 2,3 na v0.5.6) | 8 |
| Downloads | 51 GB | 70 GB |
| Disco de pico | cerca de 2,5 GB, como no piloto | 20 GB |
| Mantenedor | 3 a 4 h, duas paradas (abrir e custo; texto público) | |
| Prazo | 7 a 10 dias corridos | 14 |

Até 10 workers em horário comercial, processadores 0 a 7 livres, execução retomável.

**Entrega externa:** nota pública curta "quão estável é uma saída do Refute", com a tabela por teste e o rascunho de dataset para o Zenodo. Só agregados no texto; o mantenedor publica.

## 4. As duas fases seguintes

**Fase +1: entrada por efeméride, versão nova da bateria (único pacote de `src/`).**
- Antes: tag e entrada do lock da v0.5.6 em `verify_locked_tags.py`, e teste de CI com `verify_claim`.
- Conteúdo: efeméride do TOI como candidato (sem reajuste ou com reajuste limitado e declarado), guardas de Cholesky no `centroid_v5`, e o que a v0.5.8 mandar sobre semente e perturbações.
- A versão 2 fica intacta; aceitação sintética antes do código.
- **Decisão:** claim sob lock em alvos não expostos, ou direto para o prospectivo. Contar o pool na abertura: `part-b-prep.md:83` mostra 288 planetas na metade de confirmação após exclusão, mas a recomendação anterior fala em 47 elegíveis restantes; **não conferi** qual vale.

**Fase +2: segunda leitura prospectiva dos PCs.**
- Travar as saídas por teste, com a versão nova, para uma amostra dos 2.099 PCs da metade de confirmação (`part-b-prep.md:85`).
- Pontuar quando o TFOPWG mudar a disposição, em 6 a 12 meses.
- **Decisão:** tamanho da amostra pelo custo medido (0,024 CPU-h e 0,34 GB por TOI).
- Meio período e domínio da busca só voltam se o modo `discover` voltar.

## 5. Os 5 maiores riscos

| # | Risco | Detecção precoce |
|---|---|---|
| 1 | Ler a fase como contorno da parada da v0.5.7 | Texto de abertura diz a pergunta nova; uma rodada do Codex no desenho; guarda do runner antigo intacta |
| 2 | Instabilidade encontrada vira ajuste de limiar na versão 2 (novo laço) | Regra da fase: nada muda na v0.5; proposta de limiar encerra a fase |
| 3 | Arquivos do MAST mudaram e confundem os flips | Proveniência por SHA-256; portas contadas também só em `same`. Parte A não tem hash de curva de luz, fica `unknown` |
| 4 | Números pequenos lidos demais (107 decididos) | Wilson em toda taxa; portas em contagens fixadas antes |
| 5 | Rede e disco: 51 GB, e 4 dos 5 ERROR da parte B foram de rede | Runner retomável, teto de perdas declarado, apagar píxeis por alvo |

## Incertezas que mantenho

- As margens de estatística vêm de texto de `message`, lido por expressão regular; é frágil.
- Não sei se o modo semeado aceita uma segunda semente deslocada sem script novo.
- O tamanho do pool não exposto está em aberto, como dito.
