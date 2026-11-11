**As duas correções funcionam. Resta um ponto no filtro de recusas.**

- **D2/D4 incompletos:** o resumo preserva as contagens e substitui D2/D4 das três baterias por `NOT DECIDED: the part did not complete`. Confirmei esse comportamento em execução isolada. [b1_b14.py:416](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:416)
- **Integridade:** recusas explícitas são propagadas; sidecars fora do schedule também são recusados quando existe STOP. Fingerprint, argumento e SHA-256 continuam verificados. [b1_b14.py:288](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_b14.py:288)

**[P2] A mensagem não distingue STOP de gate falho.** O filtro aceita qualquer exceção contendo `under a stop`, mas `budgeted.assembled` emite **a mesma mensagem** quando existe apenas um gate falho, sem STOP: `refused under a stop or a failed gate`. Assim, essa outra recusa ainda permite leitura parcial. Confirmei o caminho com dados virtuais. [budgeted.py:308](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:308)

**Opção mais conservadora:** verificar o estado persistido antes do fallback. Havendo gate bloqueante, propagar a recusa, inclusive quando também houver STOP. Permitir leitura parcial somente para STOP comprovado ou shards ausentes, mantendo todas as verificações de integridade. Não alterar `budgeted.py`, reconciliar ou retomar.

Não encontrei outra falha nova nos limiares, desconhecidos de T2a, derivação de B, resgate por C ou isolamento de B1.2/B1.3. Verificação somente leitura, com checks leves em memória.

**WEAKENED, adotar a correção conservadora do filtro antes de executar B1.4, após B1.3 e o procedimento exato em #217.**