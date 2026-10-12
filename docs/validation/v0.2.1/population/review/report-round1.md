# Independent review (Phase G), round 1

- Review: independent review of the population study harness (Phase G), round 1.
- Commit reviewed: `6e57b35` (branch `claude/v0-2-1-gauntlet-fixes-13f5e7`).
- Date: 2026-10-12.
- Original language: Portuguese (not translated).
- Verbatim as delivered to the maintainer: the text below the end-of-header line is the delivered file `fase-g-report-round1.txt`, byte for byte (SHA-256 `51172b19a202bcff177cea14f9a22181699761faa63776f9a8781b43844adc47`, 14756 bytes), including the progress lines of the review session that come before the report itself. It uses LF line endings, as delivered.
- User-name check: the delivered file was searched for the Windows user name in paths before it was committed; see `README.md` of this folder.

<!-- End of header. The delivered file follows, byte for byte. -->
Hashes confirmados (392/392 OK), worktrees limpos e cada venv importando o refute do seu próprio worktree. Agora vou conferir as interfaces nos 4 commits e rodar verificações independentes (SNR, serialização, estatística, interrupção) em .cache/review-g/.

A primeira orquestração (6 casos, M0 e M3) terminou antes da interrupção; repito com 1 worker e encerro pelo PID no meio do lote 1.

Confirmei que a interrupção pelo PID e a retomada preservaram os resultados anteriores sem deixar temporários. Agora vou testar cenários negativos em cópias dentro de .cache/review-g/: arquivo truncado, condição faltando, retomada com outro commit e rótulo de ponto trocado.

Confirmado: o metrics aceita um ponto “M0” que mistura resultados de dois commits (f479823 e 9d3f369) sem recusar. Agora a estatística contra implementação independente.

Encontrei que o worker registra OPENBLAS_NUM_THREADS=1, mas o pool do OpenBLAS ainda usa 24 threads porque o init_worker roda tarde demais. Agora vou checar colisão de sementes (só as strings, sem gerar casos) e o comportamento com entrada ausente.

Testes de runtime concluídos: entrada ausente confirmadamente se torna refused permanente. Agora vou checar o .gitattributes/exclusões de lint das pastas de resultados e verificar um possível id duplicado dentro de um run.

Verificações encerradas; agora faço o inventário de .cache/review-g/ e apago a pasta.

Relatório da Fase G: revisão independente do harness da população (v0.2.1)

Commit sob revisão: git rev-parse HEAD = 6e57b358b3aa542f5feb5b11342a9af8a5f04a36 (branch claude/v0-2-1-gauntlet-fixes-13f5e7, no worktree .claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7; o checkout principal está em main, f14d480). O SHA-256 do harness é 376bd7f9e33f…, igual ao do README do selftest-2. O SHA256SUMS do selftest-2 confere 392/392, e a lista bate exatamente com os arquivos da pasta. Os quatro worktrees dos pontos estão limpos e nos commits esperados.

O trabalho foi só de leitura no repositório. Rodei apenas o autoteste (prefixo refute-v0.2.1-population-selftest), com saída em .cache/review-g/. Nenhum caso da população dev foi gerado ou analisado; no item 3 calculei só as strings de semente. Afinidade 8–31 em todos os processos. Encerrei um único processo, pelo PID que eu mesmo iniciei.

Conferência por item

1. Numeradores, denominadores e erros: conforme. run_metrics (population.py:1410-1478) e _outcomes (:1378-1398):

C1 é calculado por faixa e modelo de ruído, na condição (i).
C2 cobre os FP mensuráveis.
C3 cobre planetas e FP mensuráveis, com inconclusive = verdict == INCONCLUSIVE or not ok.
C4 cobre os casos sem trânsito.
C5 usa a condição (ii) e a variante own.
C6 cobre as duas condições.

Nenhum caso sai de um denominador. Os status refused, error e missing contam no C3 e no C6 e nunca contam como refutado, sinalizado ou alarme falso. Ver a NOTA N3.

2. Identidade do sinal e agregação: conforme.

_identity (:1068-1074) usa f em (1, 2, 0,5), tolerância relativa 0,001 com <=, e trata candidato ausente como falso.
O C2 usa o signal_verdict importado da versão medida (:1095, :1130).
O C5 (:1395-1397, :1445-1453) exige REFUTED e fatal == ["eb_catalog"], sobre planetas own, cuja única linha de catálogo é TESS-EB sob o próprio TIC. Na versão M3, same_photometry_catalogs vale ["TESS-EB"] por padrão. Isso equivale à definição literal.

3. Geração: conforme, com as NOTAs N2, N5 e N6.

SNR por cálculo independente (script meu, sem importar o harness; fórmula fechada s²m + a²(m + 2Σ(m−k)φᵏ) por trânsito). Testei 8 casos do selftest: planeta two_years white, three_years correlated, few_train correlated, variability white, odd/even correlated, secondary correlated, blend white e blend correlated. A maior diferença relativa nos SNR unitários (global, train e hidden por ano) foi 4,9e-12. Em todos, depth × min_ratio = r_target.
Monte Carlo do AR(1) com ruído branco (400 mil tentativas): razões 1,0020 e 0,9985 (m = 75) e 1,0012 (m = 112).
Diluição do blend recalculada com erf: igual à do harness (0,134993 e 0,024775).
T14 e fração de ingresso recalculados com a profundidade final: diferença de até 3e-5 h, efeito das três passadas do ponto fixo.
Mecanismos e catálogo pelo índice: na população dev, contei few_train com distâncias 17/17/16 e trânsitos 25/25; FP 63/63/62/62 e 25×4; sem trânsito 880/660/660 e 240/180/180; variantes 60/20/20 %.
Limites físicos (:595-599) e sorteios repetidos (:653-665) seguem a seção 4.6.
Sementes: dev (5200), selftest (44) e uma confirmação simulada (5200) dão 41 776 sementes derivadas distintas (caso, ruído, aux e aux+1000), sem nenhuma colisão e nenhuma abaixo de 1000.

4. Serialização e hashes: conforme. Um leitor meu, independente, conferiu 3 casos regenerados (planeta, blend e sem trânsito):

linha mágica + LF, tamanho em 8 bytes little-endian e JSON canônico (a recodificação devolve os mesmos bytes);
floats em repr, sementes como strings decimais, ordem e dtypes dos arrays conforme a Amendment, booleanos 0/1, nenhum byte sobrando;
nenhum caminho, data ou hora nos metadados (retrieved_utc é None);
SHA-256 igual ao do manifesto.

A geração com 3 workers em ordem de índice e com 1 worker em ordem reversa deu bytes idênticos (cmp), e os lotes de 2 do orchestrate também conferiram. Entrada divergente é recusada (:1212-1216). O --check é conservador: um caso ausente do manifesto congelado sai como DIVERGED.

5. Código certo em cada ponto: proveniência conforme, imposição divergente (achado C1 abaixo).

Cada venv tem um _editable_impl_refute.pth apontando para o src do próprio worktree. refute.__file__, os commits e src_dirty=False estão corretos nos run.json do selftest-2.
PYTHONPATH está vazio, e o harness não mexe em sys.path.
matching_factor e conclude_analysis aparecem só na docstring (:23-24).

6. Robustez: conforme, com os achados C2 e C3.

write_atomic (:958-973): temporário na mesma pasta, fsync, modo exclusivo e os.replace.
Interrupção reproduzida. Rodei orchestrate com 6 casos, pontos M0 e M3, lotes de 2 e 1 worker, e encerrei a árvore pelo PID no meio do lote 1 (taskkill /PID 37600 /T /F, que encerrou também o filho 44452). Não ficou nenhum .tmp. O lote 1 ficou só com os registros started e regenerated. Na retomada:
o lote 0 foi pulado;
no lote 1, M0 tinha “1 already valid, 1 to analyze”;
os 5 resultados anteriores ficaram intactos (sha256sum -c OK);
os registros 3-results-reread saíram antes de 4-inputs-deleted.
Arquivo truncado na metade: a retomada parou com “not valid JSON” e não mudou nada.
Condição ii removida de um resultado: a retomada parou com “conditions [‘i’] are not [‘i’,’ii’]”.
Retomada com o venv da M3 sobre um run da M0: recusada (“checkout differs”).
O ambiente efetivo é registrado no worker (:1185-1187). Ver a NOTA N1, que esse registro revelou.

7. Origem no metrics: divergente em commits misturados (achado C1). Os demais casos são recusados sem escrever saída: outro manifesto, o mesmo ponto passado duas vezes (6 ids repetidos), e harness diferente (já testado no selftest-2, :1529-1534).

8. Estatística: conforme. Comparei cp_upper e cp_lower com uma bisecção minha sobre a CDF binomial exata e com o binomtest(...).proportion_ci(0.90, "exact") do scipy, em 17 casos: k = 0 e k = n com n = 1, 10 e 250, (1, 2), e todos os limiares da seção 2. A maior diferença foi 1,35e-14, e os valores da tabela da seção 2 conferem (por exemplo, 16/250 → 0,0956 e 21/600 → 0,050011). O McNemar exato (:1504) bate com o cálculo exato por frações em 10 pares: (0,0), (0,1), (0,5), (5,0), (3,3), (2,9), (10,30), (0,40) e outros.

9. Log: NOTA N4.

Achados

BLOQUEANTE: nenhum.

C1. CORRIGIR ANTES: o rótulo de ponto não está amarrado ao commit, e o metrics mistura commits dentro de um ponto.

mode_analyze (:1257-1295) aceita qualquer ambiente com qualquer --point e não recusa src_dirty.
mode_metrics (:1535-1545) junta todos os runs com o mesmo point sem comparar os commits, e publica só o checkout do primeiro run (:1565).
Reprodução: analisei 3 casos com o python da M3 e --point M0; numa cópia do run M0, apaguei esses 3 casos; rodei metrics --runs <cópia M0> <run M3 rotulado M0> <run M3>. Resultado: exit 0, o ponto M0 sai com 6 casos de dois commits, rotulado f479823.
Correção sugerida:
uma tabela fixa ponto → commit no harness;
recusa no analyze e no orchestrate quando o commit não bate ou o src/ está sujo;
recusa no metrics quando os runs de um mesmo ponto têm checkouts diferentes.

C2. CORRIGIR ANTES: uma retomada recusada inutiliza o run para sempre no metrics.

A recusa grava attempt-…-refused.json com a impressão digital do ambiente errado (:1290).
Depois, _load_run (:1356-1359) recusa o run inteiro com “attempt commit differs from the run”, mesmo sem nenhum caso analisado naquela tentativa.
Reprodução: retome um run M0 com o python da M3 (é recusada), depois rode metrics com esse run: “REFUSED … attempt commit differs”, exit 2.
A falha é fechada (conservadora), mas, como resultados nunca são editados, um engano de operador obriga a refazer o ponto inteiro, com issue de rerun.
Correção sugerida: no metrics, conferir só as tentativas started e finished, ou listar as recusadas como informação.

C3. CORRIGIR ANTES: entrada ausente no cache vira resultado refused permanente.

Em :1206-1207, o caso recebe “input file missing from the cache”, conta como válido em validate_result, e a retomada nunca o refaz.
Reprodução: analyze com cache vazio dá 6 refused; repetir com o cache certo dá “6 already valid, 0 to analyze”; o metrics sai com C6 k=6, passes=False.
Isso é estado de infraestrutura, e a seção 9 só permite retomar casos sem resultado.
Correção sugerida: abortar antes de despachar se faltar entrada, ou não gravar resultado nesse caso. A recusa por hash divergente deve continuar permanente, como está.

NOTAs

N1. Threads do BLAS nos workers. Nos 176 resultados do selftest-2 (e nos meus), o worker registra OPENBLAS_NUM_THREADS=1, mas o threadpoolctl mostra 24 threads. O init_worker (src/refute/core/runner.py:31-37, igual em v0.2.0 e M3) define as variáveis depois que o numpy já foi importado. Com 24 workers, são 24×24 threads em 24 processadores lógicos. O determinismo não é afetado (bytes conferidos). O manifesto registra o ambiente do processo pai, antes do init_worker (:1006-1008). Decida antes da geração se o harness deve fixar as variáveis antes de importar o numpy, porque o fingerprint inclui os threadpools.
N2. SNR esperado do blend sem o ruído de pixel. O ruído de pixel (5e-5 × √N_ap / F_t) dá cerca de 183 ppm depois da correção de crowding. O sigma branco efetivo previsto é 627 ppm; o espalhamento medido fora do trânsito num blend regenerado foi 631 ppm. Assim, o SNR esperado dos blends fica superestimado em cerca de 4–5 % (r real ≈ 0,957 × r). Está conforme à letra (“under the chosen noise model”), mas os relatórios devem declarar isso.
N3. C1 e C4 podem sair passes: True com erros no conjunto. Um erro não conta como refutado nem como alarme falso; a proteção é só o C6. O metrics.md deveria mostrar que a aprovação depende do C6.
N4. Ordem do log. Confirmei: em orch-3.out, a linha “lot 0: … skipped” (:1652, sem flush) saiu depois das linhas do lote 1. Isso não prejudica a auditoria, porque a trilha com horário UTC está em records/ e attempts/. Mas o log não tem horário, e o resultado do --check (“N identical, 0 diverged”) existe só no log, não no registro 2-regenerated. Recomendo rodar com -u ou PYTHONUNBUFFERED=1 e gravar as contagens do check no registro.
N5. Detalhes das sementes que não estão no texto do protocolo:
primeiros 8 bytes do SHA-256 em big-endian;
banda none para os casos sem trânsito;
strings de classe e de ruído;
textos das sub-sementes seed|noise e seed|aux, mais o +1000 do make_aux;
prefixo da confirmação = string da aleatoriedade do drand.

Convém documentar isso numa emenda antes de fixar a rodada drand.

N6. _commensurate (:479-481) usa a razão P_eclipse/P_var com p ≤ 80. O protocolo não diz em que sentido a razão é tomada.
N7. Lacunas de publicação no metrics (podem vir depois, num arquivo novo):
paired usa só a condição (i), agregada entre faixas e ruídos, sem os pares da condição (ii), que é onde está a hipótese da M3;
by_mechanism usa só a condição (i);
os sorteios repetidos não são agregados por classe, faixa e mecanismo (seção 4.6);
as famílias piores que o limite não são nomeadas automaticamente (seção 4.8).
N8. O metrics não revalida o conteúdo dos resultados.
Ele não chama validate_result.
Não confere o nome do arquivo contra o campo case: um id duplicado dentro de um run vira missing e cai no C6 (falha fechada). Testado.
Não confere contra o results_sha256 dos registros.
Se a pasta de --out não existir, quebra com FileNotFoundError depois de calcular, sem escrever saída.
N9. A raiz da limpeza vem do argumento --project (:1623-1626). A remoção continua restrita a <id>.rpc dentro de uma pasta .cache/population. Os arquivos lot-*.txt nunca são removidos do cache.
N10. Robustez das verificações de ambiente:
refute_checkout (:926, parents[2]) só é confiável com instalação editável; confirmei que é o caso nos 4 venvs;
exceções de infraestrutura dentro da análise (MemoryError, OSError) viram error permanente, e o protocolo não define como um erro do C6 é “resolvido”.
Limpeza

Apaguei C:\Projetos\refute\.cache\review-g\ inteira: 247 arquivos, 47 pastas, 3,8 GB.

Pasta	Arquivos
cache6/	44
gen-a/	3
gen-b/	3
neg/	89
out/	8
proj/	7
records/	12
records2/	14
runs/	26
runs2/	27

Mais 15 arquivos soltos na raiz da pasta: manifest-6.json, orch-1.err, orch-1.out, orch-1.pid, orch-2.err, orch-2.out, orch-3.err, orch-3.out, seed_check.py, ser-cases.txt, ser_check.py, snap-after-kill.txt, snr_check.py e stats_check.py.

Depois disso, o repositório e os 5 worktrees estão limpos, e .cache/population/ não foi tocado (0 arquivos).

Não apto para a primeira geração: não há bloqueante, mas há três itens CORRIGIR ANTES (C1, rótulo de ponto e commits misturados; C2, retomada recusada que inutiliza o run; C3, entrada ausente gravada como resultado permanente). Como o harness congela na primeira geração, eles precisam ser corrigidos antes, com um novo autoteste. Depois disso, o harness fica apto.

Fora do relatório: depois que você negou o comando com /tmp, salvei na minha memória a regra de não escrever temporários fora do projeto. Desde então, tudo foi gravado só em .cache/review-g/.