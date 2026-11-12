**A dupla contagem foi corrigida, mas restam duas divergências no Run 3.** Verifiquei somente em leitura e em memória, sem executar lotes.

- **Fechamento correto:** preserva identidade, consumo, alocação e projeção original; é idempotente. Reproduzi **48,2611 CPU-h no Run 2** e **48,3611 no cenário do Run 3**, mantendo 49,9 alocados e subteto de 30 apenas após seu registro ([i4_rest2.py:152](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:152)).

1. **`left2` pode ser arredondado acima do saldo.** Em [i4_rest2.py:294](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:294), `round(..., 6)` arredonda ao mais próximo. Reproduzi uma parada por projeção autorizada com consumo de **0,5000043403 CPU-h**: saldo **6,4999956597**, débito arredondado **6,499996**. Isso deixa menos que o consumo, e o check do doador corretamente recusa. **Correção conservadora:** arredondar o débito para baixo, preservando o check.

2. **Parte fechada ainda pode passar pela autorização de retomada.** Se essa transferência falhar, `rest2` já estará reconciliada e fechada, mas `rest3` ainda não existirá. A guarda de [i4_rest2.py:254](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:254) não bloqueia `run 2`, e `refuse_new_identity` aceita a identidade preservada ([273](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:273)). Reproduzi essa aceitação. Como a projeção agora corresponde ao consumo, o cap efetivo permite margem para novo despacho: **0,7500065 contra 0,5000043 consumidos**. **Correção conservadora:** recusar explicitamente executar qualquer destino que tenha `projection_at_stop`, antes de iniciar uma tentativa.

**Nesta última rodada, a opção conservadora é manter o Run 3 bloqueado como está.** Após qualquer falha nessa transição, PARE e traga ao mantenedor, sem retomar com `run 2`.

SHA-256 revisado: `8500c2a77a3c56148a6516cfe56b1e9505d22e9b13809230554c52a934069822`.

WEAKENED (arredondar o débito para baixo e bloquear a execução de partes fechadas).