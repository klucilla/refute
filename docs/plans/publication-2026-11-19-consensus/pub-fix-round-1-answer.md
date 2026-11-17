**Os três pontos estão corretos no HEAD `346c9f9`. Nenhuma correção necessária.**

**1. Fonte e equivalência dos números**

Sim. `originals_all` registra 100 estrelas, com `SURVIVED` **4 → 0** em `v04_stage_verdicts` e `v05_stage_verdicts`: [report.json:152](C:/Projetos/refute/calibration/v0.5/runs/c2/report.json:152), valores nas linhas 189 e 195. Confirmei que o arquivo é idêntico ao registrado em `a9ec11a`.

`originals_subset` registra 97 estrelas e **2 → 0**, concordando com [T2c, report.json:266](C:/Projetos/refute/calibration/v0.5/runs/c2/report.json:266). Ambos medem **somente `SURVIVED`, sem somar `WEAKENED`, nas curvas originais**, comparando os mesmos veredictos de estágio. O [agregador, c2.py:343](C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:343) confirma a seleção das curvas originais e a exclusão das três estrelas de desenvolvimento apenas no subconjunto.

A frase é fiel nas duas versões: [EN:44](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.en.md:44) e [PT:46](C:/Projetos/refute/.cache/v05/release/release-notes-v0.5.0.pt.md:46). **O parêntese pode permanecer**, como contagem descritiva da população completa, não como resultado de T2c. Os quatro antigos `SURVIVED` passaram a `INCONCLUSIVE`, não a `REFUTED` ([report.json:173](C:/Projetos/refute/calibration/v0.5/runs/c2/report.json:173)).

**2. Formulação do README**

Sim. [README.draft.md:56](C:/Projetos/refute/.cache/v05/release/README.draft.md:56) reproduz exatamente [README.md:37](C:/Projetos/refute/README.md:37), inclusive a quebra de linha. A formulação redundante foi retirada; o texto preservado nega descoberta confirmada e mantém candidatos e veredictos sem certeza. Essas linhas não aparecem no [README.diff](C:/Projetos/refute/.cache/v05/release/README.diff:1).

**3. Registro da alteração**

[metadata-changes.md:34](C:/Projetos/refute/.cache/v05/release/metadata-changes.md:34), seção 2, está correto: identifica as duas fontes numéricas, distingue a contagem descritiva de 100 estrelas da meta T2c e registra fielmente a preservação do texto atual do README.

SURVIVED
