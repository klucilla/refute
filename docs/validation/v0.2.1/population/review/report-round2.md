# Independent review (Phase G), round 2

- Review: independent review of the population study harness (Phase G), round 2.
- Commit reviewed: `a83e09a` (branch `claude/v0-2-1-gauntlet-fixes-13f5e7`).
- Date: 2026-10-12.
- Original language: Portuguese (not translated).
- Verbatim as delivered to the maintainer: the text below the end-of-header line is the delivered file `fase-g-report-round2.txt`, byte for byte (SHA-256 `8c273e81a1b0e7dc3a3debc7e0d6d7c870b8ded444f437a23cd4fd278cbb0031`, 11388 bytes), including the progress lines of the review session that come before the report itself. It uses LF line endings, as delivered.
- User-name check: the delivered file was searched for the Windows user name in paths before it was committed; see `README.md` of this folder.

<!-- End of header. The delivered file follows, byte for byte. -->
Primeiro recrio os verificadores em .cache/review-g/keep/, com o conteúdo exato da primeira revisão.

Interrupção e retomada confirmadas: os 2 resultados anteriores permaneceram intactos, sem temporários, pools com 1 thread cada e análise rodando no processo principal com 1 worker. Agora vou escrever os cenários negativos num script em keep/ e executá-lo.

Todos os cenários negativos da rodada 1 já são recusados corretamente. Agora vou testar o caminho de infraestrutura dentro do worker (registro interrupted), removendo uma entrada do cache de teste durante a execução.

Confirmei o caminho interrupted: o worker parou sem gravar resultado, o metrics registrou o caso como ausente no C6, e a retomada completou o run. Agora vou rodar de novo os quatro verificadores de keep/ contra o harness novo.

Os quatro verificadores reproduzem, com o harness novo, exatamente os números da primeira revisão. Agora vou comparar os resultados do selftest-2 com os do selftest-3 e com meus próprios runs, e verificar as provas do selftest-3 (registros de lote, N9, bindings).

Revisão das provas concluída. Agora registro os comandos da rodada 2 em keep/, copio as saídas essenciais e removo só os caches grandes.

Agora o estado final dos repositórios.

Relatório da Fase G (2ª rodada): revisão do delta 6e57b35..a83e09a

Base: o branch está em a83e09a6b60fcdf5ca0cc7fd6d0445c30431a0cf. O harness population.py tem SHA-256 33e2d4186ea4… e o points.json tem 7f26cc75bd96…. Tratei o harness como arquivo novo e li as 2434 linhas. O diff confirma que a geração e a serialização (linhas antigas 56–818, hoje 69–853) não mudaram. As mudanças estão no ambiente, no analyze, no metrics e no orchestrate.

Limite de execução: o orchestrate agora exige que --project seja o topo do repositório do harness (population.py:2242-2249). Isso põe o cache em <worktree>/.cache/population/, fora de .cache/review-g/. Por isso, do orchestrate executei só as duas recusas, que não gravam nada. O resto dele conferi pelo código e pelas provas do selftest-3.

1. Verificadores recriados

Em .cache/review-g/keep/ estão snr_check.py, ser_check.py, stats_check.py e seed_check.py, reconstruídos exatamente a partir do meu histórico (eu os tinha escrito por inteiro), além de round1-commands.md com os comandos dos cenários da 1ª rodada.

Não deu para reconstruir as saídas da 1ª rodada como arquivos, porque elas se perderam com a pasta. Os números estão no relatório anterior, e a rodada 2 os reproduz todos (item g).

2. Itens

a. C1, C2 e C3: conformes. Reproduzi os cenários, com saída em keep/outputs-round2/negatives.log.

C1. O ambiente da M3 com --point M0 foi recusado antes do despacho; o run.json e os resultados ficaram intactos (population.py:1093-1114, :1557). O ponto M9 foi recusado. No metrics, um ponto M0 feito de metade do run M0 e metade do run M3 rotulado M0 foi recusado com 5 problemas (binding contra points.json, e checkout, plano e fingerprint diferentes). Recusou também quando forjei o commit do binding (:1676-1693, :2075-2079).
Não verificável por execução própria: a recusa de src/ sujo e de instalação não editável, porque exigiria editar um worktree. Fica conforme pelo código (:997, com --untracked-files=all, e :1016-1031) e pelo log do selftest-3 (linhas 236–254).
C2. O run com a tentativa recusada foi aceito pelo metrics, que a lista com "results": "none" (:1539-1555, :1698-1725).
C3.
Cache vazio: recusa antes do despacho e 0 resultados; com o cache certo, 6 analisados.
Hash divergente (último byte trocado): recusa, 0 resultados, execução parada (:1591-1601).
O caminho dentro do worker também foi exercitado: removi uma entrada durante a execução. A tentativa registrou interrupted e “no result written”, os 5 resultados anteriores foram mantidos, o metrics contou o caso como ausente no C6 (k=1), e a retomada completou o run (:1431-1440, :1626-1647).
Interrupção pelo PID: taskkill /PID 17324 /T /F com 2 resultados gravados. Não ficou temporário, os 2 resultados continuaram iguais após a retomada, e a tentativa morta (só started) é aceita pelo metrics.

b. N1: conforme.

As variáveis são definidas antes do import numpy (:47-59) e há recusa explícita se algum pool não tiver 1 thread (:939-953, :857-859, :1193, :1424-1426).
Com OPENBLAS_NUM_THREADS=2 e OMP_NUM_THREADS=4 herdados, 1 worker, os 44 casos saem idênticos ao manifesto do selftest-2 (harness antigo); o mesmo com 3 workers em ordem reversa. Com 24 workers e ordem embaralhada, saem idênticos ao manifesto do selftest-3.
Os pools ficam em ('openblas', 1) no processo principal e nos filhos. No analyze com 1 worker, a análise rodou no próprio PID principal com pool de 1. Nos 176 resultados do selftest-3, todos os workers têm pool 1.
Os registros de ambiente dos manifestos s2 e s3 diferem só em environment, generator e harness_sha256; os 44 casos são idênticos.

c. Conformes:

N3: aprovação global que inclui o C6, com a regra escrita no .md (:1885-1891, :2138).
N4: saída sem buffer (:2255, :2383) e contagens do check gravadas no registro 2-regenerated (:1254-1264, :2322-2332). A ordem do log do selftest-3 está correta (linhas 59–175).
N7: comparações pareadas por faixa e ruído nas condições (i) e (ii), e por variante na (ii); resultados por mecanismo nas duas condições; sorteios repetidos agregados; famílias nomeadas (:1892-1941, :1944-2003).
N8, todos recusados sem escrever saída (:1728-1744, :2027-2037, :2052-2073):
nome do arquivo diferente do caso;
id repetido no run;
--records com um veredito adulterado (aceito sem a adulteração);
saída já existente;
mesmo ponto duas vezes;
pastas com o mesmo nome.
N9: recusa de --project fora do topo e de cache fora de .cache/population, sem gravar nada (:2242-2249). A remoção não segue symlinks (:2273-2280). A correção do A2 (448f1e5, :2371-2373) aparece no registro lot-0001-…-4-inputs-deleted.json, que apaga também a lista e o relatório de check da tentativa interrompida, e o cache terminou vazio.
N10: exigência de instalação editável (:1022-1028); os erros de infraestrutura param a execução, e os de análise viram error permanente (:1286-1293, :1352-1355, :1460-1463).

d. points.json: conforme.

Tem 4 entradas, M0 a M3, com commits de 40 caracteres iguais aos HEADs dos worktrees.
Foi criado em 39d13f8 e não mudou depois (é o único commit no git log do arquivo).
O binding e o points_at_start estão em cada run.json: nos 4 do selftest-3 (commit 448f1e5, committed: true) e nos meus (a83e09a).
A conferência histórica de _load_run (:1117-1133) funciona: com o commit gravado apontando para 6e57b35, recusa (“not found at the recorded repository commit”); com o SHA-256 gravado alterado, recusa.

e. Emenda 2: conforme.

Só acréscimo: 108 linhas e 0 removidas, de population-study.md:537 em diante.
As regras de semente batem com o código: :136-143, :164-176, :689, :704, :736-739, :781, e synthetic.py:328 para o +1000. O seed_check recalcula com a fórmula escrita na emenda e confere as 10 444 sementes.
O N2 distingue os dois SNR e a conta 0,9565 está certa.
O N6 bate com :514-516 e :645: razão P_eclipse/P_var, q ≤ 4, p ≤ 80 e tolerância absoluta 0,01.

f. selftest-3: conforme.

SHA256SUMS: 567/567 OK, e a lista é exatamente a pasta menos o próprio arquivo.
As provas sustentam o README: registros de lote, tentativa started sem finished na M1 (a morta), tentativa recusada na M0, ordem do log, e “files left: 0”.
Os resultados de análise dos 44 casos são idênticos ao selftest-2 nos 4 pontos, comparando todos os campos usados pelo metrics (keep/compare_outcomes.py). Os meus runs M0 e M3 também são idênticos aos do selftest-3.

g. Comportamento já aprovado: inalterado. Os verificadores de keep/ rodados contra o harness novo dão exatamente os números da 1ª rodada:

SNR: maior diferença 4,9e-12 em 8 casos; Monte Carlo com razões 1,0020, 0,9985 e 1,0012.
Serialização: 3 casos sem nenhum problema; ruído do blend 631 ppm.
Estatística: maior diferença 1,35e-14; o McNemar bate em 10 pares.
Sementes: 41 776 distintas, 0 colisões.

h. O status refused de resultado não existe mais: conforme.

A única gravação de resultado é :1467, alcançada só depois do arquivo presente e do hash conferido (:1431-1440, mais a conferência antes do despacho em :1591-1601).
validate_result rejeita qualquer status que não seja analyzed ou error (:1399-1400).
Um grep mostra "refused" só nos registros de tentativa (:1544).
Achados

BLOQUEANTE: nenhum. CORRIGIR ANTES: nenhum.

NOTAs

R1 (recomendo corrigir antes, porque é barato e o harness congela). O orchestrate pula um lote “completo” sem conferir se ele tem os registros 3 e 4 (:2283-2293).
Se uma interrupção cair entre o fim do último analyze e o registro 3-results-reread, aquele lote nunca recebe o registro, e metrics --records recusa seus resultados para sempre (“not in any results-reread record”, :2058-2059).
Se cair entre os registros 3 e 4, as entradas (até cerca de 5,6 GB por lote) e os arquivos de lote ficam no cache.
A falha é fechada, e o metrics sem --records contorna. Não reproduzi, porque exigiria rodar o orchestrate; é leitura de código.
R2. O points.json precisa estar commitado sem alterações (:1099-1103), mas o próprio harness não. O SHA-256 dele é gravado e comparado entre runs, mas um harness editado e não commitado rodaria.
R3. OSError conta como infraestrutura (:1293). Um OSError determinístico vindo do código de análise faria a execução parar sempre no mesmo caso, em vez de virar resultado. A falha é fechada e está declarada na Emenda 2.
R4. O teste de src/ sujo do selftest-3 editou o worktree da M3 e depois o restaurou, com o restauro conferido no log. Hoje esse worktree está limpo (abaixo).
Limpeza

Removi só os caches grandes de .cache/review-g/r2/:

Pasta	Conteúdo
cache/	8 .rpc, 540 MB
neg/racecache/	8 .rpc, 540 MB
neg/badcache/	2 .rpc, 126 MB
nostore/	vazia
neg/emptycache/	vazia

Os nomes de cada arquivo estão no inventário da sessão. Não restou nenhum .rpc.

Ficaram em .cache/review-g/:

r2/ (153 arquivos, 1,1 MB: runs, cópias negativas, saídas do metrics);
keep/ (29 arquivos): os 4 verificadores, compare_outcomes.py, round1-commands.md, round2-commands.md, round2-negatives.sh e outputs-round2/, mais um SHA256SUMS que confere.

Nada foi gravado no repositório.

Estado final
git status --porcelain (checkout principal, main)                    -> vazio
git status --porcelain (.claude/worktrees/v0-2-1-gauntlet-fixes-13f5e7) -> vazio
git status --porcelain (.worktrees/v0.2.0)                           -> vazio
git status --porcelain (.worktrees/M1-3217db7)                       -> vazio
git status --porcelain (.worktrees/M2-78d79f5)                       -> vazio
git status --porcelain (.worktrees/M3-9d3f369)                       -> vazio
git log -1 --format=%H claude/v0-2-1-gauntlet-fixes-13f5e7           -> a83e09a6b60fcdf5ca0cc7fd6d0445c30431a0cf

Apto para a primeira geração: C1, C2 e C3 estão corrigidos e reproduzidos, as NOTAs da 1ª rodada estão implementadas, os bytes gerados e os resultados de análise não mudaram, e não restou bloqueante nem item CORRIGIR ANTES. Recomendo fechar o R1 antes de congelar o harness, porque é barato, mas ele não impede a geração.