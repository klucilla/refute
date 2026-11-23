## 1. Números da nota · WEAKENED

Reconstituí as contagens a partir dos registros de `bbfdecc` e calculei os intervalos de Wilson de 95% antes do arredondamento. **Todas as contagens conferem. Um limite superior precisa mudar de 14% para 13%.** [Registros v0.5.8](C:/Projetos/refute/docs/validation/v0.5.8/stability-records.json) · [Relatório de contagem](C:/Projetos/refute/docs/validation/v0.5.8/stability-report.json:520)

| Medida | Contagem | Percentual e Wilson 95% arredondados |
|---|---:|---|
| Mudou de classe, incluindo `ERROR` | 19/167 | 11%, 7% a 17% |
| Tinha resultado decidido e mudou, incluindo `ERROR` | 15/107 | 14%, 9% a 22% |
| Mudou para `INCONCLUSIVE` entre as mudanças decididas em execuções concluídas | 12/13 | 92%, 67% a 99% |
| SNR variou mais de 10% em relação ao ajuste original | 15/167 | 9%, 6% a 14% |
| Mudança de status perto de um limiar segundo a regra do plano | 12/150 | **8%, 5% a 13%** |
| Execuções que falharam | 5/167 | 3%, 1% a 7%, se exibido como taxa |

O limite superior exato de 12/150 é **13,462136%**. O valor `0.135` no relatório é uma apresentação já arredondada. Para a nota, o arredondamento direto ao inteiro dá **13%**. Os 150 incluem 70 mudanças para `NOT OK` atribuídas às cinco falhas. Uma dessas 70 entra no numerador, `systematics` em `TIC-302895996`. Entre as execuções concluídas, são 11 de 80. O denominador de SNR inclui cinco registros sem SNR novo. `TIC-274138511` (TOI-506.01) é um dos 15 com diferença superior a 10%. [Plano, portas 2 e 3](C:/Projetos/refute/docs/plans/v0.5.8-plan.md:50) · [Relatório v0.5.8](C:/Projetos/refute/docs/reports/v0.5.8-report.md:72)

**As cinco falhas e suas categorias conferem.** Foram dois downloads, `TIC-317483660` (TOI-2346.01, conexão expirou no download da curva de luz) e `TIC-165598669` (TOI-7393.01, conexão reiniciada no download do arquivo de pixels), um limite de execução de 600 segundos, `TIC-302895996` (TOI-531.01), e dois erros numéricos, `TIC-146846569` (TOI-734.01, `OverflowError`) e `TIC-259172249` (TOI-5218.01, `LinAlgError: Singular matrix`). As cinco falhas entram nas 19 mudanças de classe. Duas entram nas 15 mudanças de resultados decididos. A outra mudança em execução concluída foi `INCONCLUSIVE` → `SURVIVED`, em `TIC-47244580`. [Registros v0.5.8](C:/Projetos/refute/docs/validation/v0.5.8/stability-records.json) · [Relatório v0.5.8](C:/Projetos/refute/docs/reports/v0.5.8-report.md:147)

**A segunda tabela confere inteira**, inclusive o limite de `odd_even`, cujo valor exato de 12,500152% arredonda para 13%. Os cinco testes destacados somam 66 das 80 mudanças de status nas 162 execuções concluídas. [Relatório v0.5.8, mudanças por teste](C:/Projetos/refute/docs/reports/v0.5.8-report.md:109)

| Teste | Mudanças em 162 | Percentual e Wilson 95% |
|---|---:|---|
| `event_consistency` | 18 | 11%, 7% a 17% |
| `centroid_shift`, `systematics` | 13 cada | 8%, 5% a 13% |
| `odd_even` | 12 | 7%, 4% a 13% |
| `aperture_depth` | 10 | 6%, 3% a 11% |
| `secondary_eclipse` | 7 | 4%, 2% a 9% |
| `period_alias` | 2 | 1%, 0,3% a 4% |
| `duty_cycle`, `edge_events`, `nearby_contamination`, `single_event`, `sinusoid` | 1 cada | 0,6%, 0,1% a 3% |
| `plausibility`, `snr` | 0 cada | 0%, 0% a 2% |

## 2. Frase 2a · SURVIVED

Dos 105 registros antes decididos que concluíram a nova execução, **13 mudaram de classe**. A frase reproduz as 13 transições exatamente. Também conferi que nenhuma saída passou de `SURVIVED` ou `WEAKENED` para `REFUTED`. [Registros v0.5.8](C:/Projetos/refute/docs/validation/v0.5.8/stability-records.json) · [Matriz de transições](C:/Projetos/refute/docs/reports/v0.5.8-report.md:79)

| Transição | Chaves dos registros |
|---|---|
| `SURVIVED` → `INCONCLUSIVE` (6) | `TIC-124206468`, `TIC-142937186`, `TIC-153078576`, `TIC-299799658`, `TIC-365733349`, `TIC-55275863` |
| `WEAKENED` → `INCONCLUSIVE` (4) | `TIC-219388773`, `TIC-220016044`, `TIC-372596795`, `TIC-401604346` |
| `REFUTED` → `INCONCLUSIVE` (2) | `TIC-356235833`, `TIC-419858461` |
| `REFUTED` → `WEAKENED` (1) | `TIC-467783290` |

## 3. Frase 2b · WEAKENED

**Os 18 eventos são exatamente os da claim travada.** Cruzei os braços `fp` e `planet` da Parte B com `status: OK`, `outcome: REFUTED`, `identity.matched: true` e cobertura positiva em pelo menos um teste decisivo. Todos os 18 foram reexecutados com proveniência `same` e mantiveram `identity.matched: true`. Dos 17 FPs, 14 mantiveram `REFUTED`, `TIC-356235833` e `TIC-419858461` passaram a `INCONCLUSIVE`, e `TIC-467783290` passou a `WEAKENED`. O evento planetário, `TIC-331691841` (TOI-5947.01), manteve `REFUTED`. [Claim](C:/Projetos/refute/calibration/v0.5.6/claim.yaml:30) · [Registros da Parte B](C:/Projetos/refute/docs/validation/v0.5.6/part-b-records.json) · [Porta 4](C:/Projetos/refute/docs/plans/v0.5.8-plan.md:63)

**O escopo de “no other planet” precisa ser explícito.** A v0.5.8 reexecutou **40 dos 150** registros do braço `planet` da Parte B, ou **40 dos 100** com `identity.matched: true` na v0.5.6. São 24 da lista `decided` e 16 da lista `inconclusive_drawn`. Todos os 40 concluíram, 39 mantiveram o match no novo ajuste e só `TIC-331691841` terminou `REFUTED`. O único que perdeu o match, `TIC-142937186`, terminou `INCONCLUSIVE`. A frase é verdadeira para os 40, mas sua redação permite que o leitor a aplique aos 150. Entre os 110 ausentes estão os 12 registros planetários originalmente `REFUTED` cujo sinal não correspondia ao TOI. [Conjunto da etapa 1](C:/Projetos/refute/docs/validation/v0.5.8/stage1-set.json) · [Parte B original](C:/Projetos/refute/docs/reports/v0.5.6-report.md:93) · [Porta 4, contagem](C:/Projetos/refute/docs/validation/v0.5.8/stability-report.json:567)

As duas versões de 2b são idênticas à decisão registrada. Ambas preservam expressamente o veredito travado **`SURVIVED`** da claim e apresentam os resultados por TOI como saídas da bateria. A comparação mostra o que aconteceu com esses eventos sob a nova inicialização do ajuste. O `git diff HEAD -- docs/reports/v0.5.6-report.md` saiu vazio, com código 0. [Decisão de 23/11](C:/Projetos/refute/.cache/v058/comment-decisions-stage1-end.md) · [Veredito travado](C:/Projetos/refute/calibration/v0.5.6/part-b-verdict.md)

## 4. Demais fatos · WEAKENED

- **Seleção e ordem.** Reproduzi o sorteio com a semente registrada. Os 167 correspondem exatamente aos 107 registros com sinal correspondente ao TOI e resultado decidido, sendo 28 `SURVIVED`, 53 `WEAKENED` e 26 `REFUTED`, mais 60 sorteados dos 257 `INCONCLUSIVE` com sinal correspondente. A nota omite esse critério de entrada. O plano, o conjunto e os scripts da etapa 1 já estavam no commit `1f3e5f9`, anterior ao primeiro `started_utc` dos 167 registros. [Conjunto da etapa 1](C:/Projetos/refute/docs/validation/v0.5.8/stage1-set.json) · [Plano](C:/Projetos/refute/docs/plans/v0.5.8-plan.md:28)
- **Modo e dados.** O modo usa período e duração da efeméride e refina a época dentro de ± uma duração, com retorno à época propagada quando necessário. A bateria faz novo ajuste antes dos testes e mantém testes, limiares e regras. Os produtos são do SPOC no MAST. A identidade dos arquivos foi verificada em **83 registros** e ficou **desconhecida em 84**, como `TIC-1003831`. Quatro dos 162 ajustes concluídos perderam a correspondência com a efeméride do TOI, incluindo `TIC-142937186` com proveniência `same`. Além disso, os dois erros de download e o timeout ocorreram antes da inicialização do ajuste. [Runner TOI-seeded](C:/Projetos/refute/docs/validation/v0.5.7/seeded_run.py:535) · [Proveniência no relatório](C:/Projetos/refute/docs/reports/v0.5.8-report.md:35)
- **Links, rótulos e créditos.** Todos os destinos relativos existem na árvore de trabalho, inclusive a seção “The four doors” citada no adendo. O caminho da URL GitHub existe na referência local `origin/main` em `bbfdecc`. A URL pública e a issue `#218` ficaram sem verificação externa, conforme o escopo sem rede. Os rótulos `exploratory`, `method_status: not_validated` e `WEAKENED; does not meet D1, D2, D4, T2a` conferem. Os três agradecimentos institucionais da nota coincidem com os da v0.5.7, e a nota credita as mesmas três bibliotecas, com a única omissão da referência ao README raiz. [Relatório v0.5.7](C:/Projetos/refute/docs/reports/v0.5.7-report.md:106) · [Nota](C:/Projetos/refute/docs/reports/v0.5.8-stability-note.md:76) · [Adendo](C:/Projetos/refute/docs/reports/v0.5.6-report-addendum-2026-11-23.md:20)

## BLOCKING

1. **Nota, intervalo de Wilson de 12/150.** De `12 of 150 (8 %; 5 % to 14 %)` para `12 of 150 (8 %; 5 % to 13 %)`.
2. **Nota e adendo, escopo da frase 2b.** De “its one planet event stayed REFUTED, and no other planet became REFUTED.” para “The record for its one planet event stayed REFUTED. Of the 40 Part B planet records rerun in v0.5.8, that was the only REFUTED output.” Substituir também o ponto e vírgula imediatamente anterior por um ponto. Preservar o restante da passagem.
3. **Nota, critério de seleção e proveniência.** De “167 TOIs that v0.5.6 had already run, using the same public SPOC data at MAST:” para “167 TOIs selected from v0.5.6 records whose fitted signals matched the TOI ephemerides. The reruns used public SPOC products from MAST. File hashes matched for 83 records. File identity was unverified for 84. The set comprised:”
4. **Nota, alcance da comparação.** De “if the same signal is refitted from a different starting point, does the answer stay the same?” para “When the battery starts from the TOI ephemeris, how often does its output differ from the v0.5.6 search-mode output?” No resumo, trocar “About one decided output in seven moved when only the starting point of the fit changed. Almost all of those moves were toward INCONCLUSIVE, not between SURVIVED and REFUTED.” por “About one in seven previously decided records changed class in the rerun. This count includes two runs that ended in ERROR.” A frase 2a, logo abaixo, já descreve a direção das mudanças concluídas.
5. **Adendo, execuções que chegaram ao ajuste.** De “Each run was seeded by the TOI's published ephemeris, and each output was compared with its v0.5.6 record.” para “Runs that reached the fitting step used the TOI's published ephemeris to seed the refit. Each run record was compared with its v0.5.6 record.”

## Não bloqueantes

- Explicitar a regra por trás dos 8% com “Under the predefined threshold rule, 12 of 150 status changes were near a threshold in the first run. The denominator includes 70 changes to NOT OK from five failed runs.”
- A linha de falhas traz a contagem correta. Para explicitar sua taxa com a mesma convenção das demais linhas, usar `5 of 167 (3 %; 1 % to 7 %)`.
- Para reproduzir também a referência bibliográfica da v0.5.7, restaurar “, cited as in the root README” após “Lightkurve, Astropy and Astroquery”.

**OVERALL: WEAKENED**

