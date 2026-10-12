# Independent review (Phase G), round 3

- Review: independent review of the population study harness (Phase G), round 3.
- Commit reviewed: `b7c724c` (branch `claude/v0-2-1-gauntlet-fixes-13f5e7`).
- Date: 2026-10-12.
- Original language: Portuguese (not translated).
- Verbatim as delivered to the maintainer: the text below the end-of-header line is the delivered file `fase-g-report-round3.txt`, byte for byte (SHA-256 `448432cdfe3d73ab25a69c142f426b367a154a5476a7e4a9717b97444e29a3fb`, 7824 bytes), including the progress lines of the review session that come before the report itself. It uses CRLF line endings (89 lines), as delivered.
- User-name check: the delivered file was searched for the Windows user name in paths before it was committed; see `README.md` of this folder.

<!-- End of header. The delivered file follows, byte for byte. -->
Confirmei que harness_commit só é gravado, nunca comparado — as validações usam harness_sha256 e RESUME_KEYS. Já tenho um caso real para o item d (selftest-4 em 1692d99 vs HEAD b7c724c com mesmo harness); agora vou checar o SHA256SUMS e as provas do R1.

Executado 2 comandos
As provas dos três estados do R1 batem com o código. Confiro o estado c (registro 3 adulterado) e depois rodo os testes do item d e do R2 em .cache/review-g/r3/.

Executado 2 comandos
Confirmei os casos do item d: --check aceita o manifesto de 1692d99, e metrics --records aceita os runs de 1692d99 com HEAD em b7c724c. Agora vou verificar a retomada de um analyze após a troca de HEAD, e o R2 com uma cópia não rastreada do harness.

Resume across a HEAD change and test an untracked harness copy
Item d confere, inclusive na prática: a retomada após a troca de HEAD foi aceita e o harness_commit gravado corresponde ao HEAD, e R2 está conforme para cópia não rastreada nos três modos. Vou rodar de novo os verificadores de keep/.

Executado 4 comandos
Relatório da Fase G (3ª rodada): revisão do delta a83e09a..b7c724c
Base: o branch está em b7c724cd91be…. O harness population.py tem SHA-256 408020676340…, e o points.json continua igual (7f26cc75bd96…).

O delta tem dois commits:

1692d99: só o population.py, com 112 linhas novas e 14 removidas.
b7c724c: só a pasta selftest-4/, com 272 arquivos.
O protocolo não mudou. O SHA256SUMS do selftest-4 confere 271 de 271, e a lista bate exatamente com os arquivos da pasta.

Itens
a. R1: conforme. Agora um lote só é pulado se todos os resultados forem válidos e os registros 3 e 4 existirem e baterem com eles:

Os resultados precisam ser válidos (population.py:2349-2358).
O código procura o registro 3 mais recente do lote (:2361-2362, com _lot_record_kinds em :2280-2287).
Se os resultados estiverem incompletos, ou se os hashes não baterem com o registro 3, a execução para sem gravar nem apagar nada (:2369-2379).
O lote só é pulado quando o registro 4 já existe com o mesmo prefixo do registro 3 (:2380-2382).
Se o registro 4 falta, o código apaga as entradas e grava o registro 4 com o prefixo do registro 3 (:2383-2385, função finish em :2339-2350).
Se o registro 3 também falta, grava os dois, com a marca written_on_resume (:2386-2398).
Os três estados do selftest-4 batem com esse código. Conferi os snapshots de antes e depois e os registros do lote 0 (outputs-round3/r1-evidence.txt):

Estado	O que entrou	O que saiu	O que mudou
(a) sem registro 3	registros 3 e 4	as 2 entradas .rpc e o arquivo de lote	nada
(b) sem registro 4	só o registro 4, com o prefixo do registro 3	as mesmas 3 entradas de cache	nada
(c) registro 3 adulterado (um hash com o último caractere trocado, …f80 para …f84)	nada	nada	nada
No estado (c), o log mostra a parada: “record … and the results on disk diverge (1 files)” (linha 226). No estado final, os três lotes são pulados com “equal to record 3, record 4 present” (linhas 114–116).

Execução própria: não verificável, porque o orchestrate exige o cache dentro do worktree, fora de .cache/review-g/. Fica conforme pelo código e pelas provas.

b. R2: conforme. A checagem está em harness_problems (:1147-1169). Ela recusa nestes casos:

harness não rastreado;
git diff --quiet HEAD com qualquer retorno diferente de 0, o que inclui erro do git;
SHA-256 diferente do arquivo HEAD:<caminho>;
arquivo alterado em disco depois que o processo começou.
Os bytes de referência são lidos no início do processo (:96-97). A checagem é chamada em generate (:1219-1221), analyze (:1565-1566, com recusa registrada como tentativa) e orchestrate (:2296-2298).

Por execução própria, testei uma cópia não rastreada do harness em .cache/review-g/r3/copy/. Os três modos recusaram com “the harness is not tracked in a git repository”:

o analyze gravou só a tentativa refused;
o orchestrate não gravou nada.
O caso de harness alterado, que também fica diferente do HEAD, eu não pude reproduzir, porque exigiria editar o arquivo versionado. Fica conforme pelo código e pelo log do selftest-4 (linhas 238–248).

c. Nada fora do delta mudou: conforme.

O diff fora do selftest-4/ atinge só o population.py, e nos trechos de R1 e R2 (docstring, constantes de harness, harness_problems, início dos modos, orchestrate).
Os verificadores de keep/ (SNR, serialização, estatística e sementes) rodados contra o harness 40802067 deram saídas idênticas às da 2ª rodada (diff vazio).
Os resultados dos 6 casos curtos do selftest-4 são idênticos aos do selftest-3 nos 4 pontos.
O generate --check dos 44 casos deu 44 idênticos tanto contra o manifesto do selftest-4 quanto contra o do selftest-3.
d. harness_commit contra harness_sha256: conforme. Testei o cenário real: o selftest-4 rodou em 1692d99, o HEAD agora é b7c724c, e o harness é o mesmo.

A identidade do harness é comparada pelo SHA-256 em todos os pontos. O harness_commit aparece só em gravações (:1266, :1573, :1610) e nunca é comparado:
retomada do analyze: RESUME_KEYS (:1529-1537) não inclui harness_commit nem points_at_start;
_load_run: compara as tentativas pelo harness_sha256;
metrics: :2090 e :2121;
validate_result e _lot_results: usam CONTEXT_KEYS.
Retomada depois da troca de HEAD. Copiei o run M0 do selftest-4, removi um resultado e retomei com o HEAD em b7c724c. A retomada foi aceita, analisou só aquele caso, e o resultado saiu idêntico ao original. O run.json manteve 1692d99, e a tentativa nova registrou b7c724c.
metrics depois da troca de HEAD. Rodando agora com --records sobre os 4 runs gravados em 1692d99, o metrics aceitou.
generate --check contra manifesto de commit anterior. Contra o manifesto do selftest-4 (harness_commit 1692d99), deu 44 idênticos com exit 0. O --check compara só as entradas dos casos.
O harness_commit gravado é o HEAD, não o último commit que alterou o population.py. Um run novo de agora grava b7c724c…, enquanto o último commit que mexeu no harness é 1692d99. Como o R2 exige que o arquivo seja igual ao do HEAD, esse commit sempre contém os bytes do harness, mas não é necessariamente o commit que o alterou.
Achados
BLOQUEANTE: nenhum. CORRIGIR ANTES: nenhum.

NOTAs

N-a. O nome harness_commit sugere “o commit do harness”, mas o valor é o HEAD do momento da execução. Vale documentar isso no relatório da medição. A identidade do harness é o harness_sha256.
N-b. O generate --check não compara o harness_sha256 do manifesto congelado com o do harness em execução. Isso é coerente, porque o que importa ali são os bytes dos casos, e o analyze e o metrics amarram o manifesto pelo SHA-256 dele.
N-c. O R2 é conferido só no processo principal. Os workers, criados logo depois, reimportam o harness do disco sem comparar o SHA-256 com o do pai. Uma edição do arquivo nessa janela de segundos não seria detectada pelos workers. O risco é baixo; para fechar, bastaria passar o SHA-256 do pai na tarefa e comparar no worker.
Saídas e limpeza
As saídas novas estão em .cache/review-g/keep/outputs-round3/, com um README.txt, e o SHA256SUMS de keep/ foi atualizado: 40 arquivos, todos OK.

Removi só os caches grandes de .cache/review-g/r3/:

cache/: 6 .rpc, 432 MB;
cache2/: 2 .rpc, 144 MB;
nostore/: vazia.
Não restou nenhum .rpc. A pasta .cache/review-g/ ficou com 292 arquivos e 2,0 MB.

Apto para a primeira geração: R1 e R2 estão corretos pelo código e pelas provas, e o comportamento já aprovado não mudou. A identidade do harness é comparada pelo SHA-256, não pelo commit; por isso, commitar o manifesto congelado, que muda o HEAD, não trava os runs de M0 a M3. Não há bloqueante nem item CORRIGIR ANTES.