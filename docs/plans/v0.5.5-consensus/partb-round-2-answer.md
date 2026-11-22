## Rodada 2 de até 3

**Pare antes do lock.** O pool corrigido confere. Ainda há caminhos em que o runner aceita um sorteio alterado ou o avaliador interpreta incorretamente o fim do run.

| Bloco | Veredito | Resultado |
|---|---|---|
| **A. Passo exploratório** | **SURVIVED** | Reproduzi as evidências dos 4.385 arquivos do commit histórico e os 16 caminhos de cache registrados. São **973 expostos**, com **197 planetas e 411 FPs** no pool. `part-b-prep.json` conserva os bytes, e os 14 casos e as tabelas continuam válidos. |
| **B. Emenda e plano de lock** | **WEAKENED** | O viés da exclusão está declarado. A divulgação, a concordância, o rótulo de limites, o Fisher, a guarda e a política de ultrapassagem dos tetos estão definidos. Faltam critérios executáveis para validar o sorteio publicado e o encerramento do run. |
| **C. Claim e anexos** | **REFUTED** | O schema `discover` aceita os 608 alvos e os seis anexos. A cadeia da bateria foi preservada. Os testes adicionais reproduziram as falhas abaixo. |

## Bloqueantes antes do lock

1. **A rodada é revalidada na geração, mas perde essa garantia no consumo.** `draw()` barrou uma rodada incorreta antes de consultar o beacon. Porém, aceitou ID e hash da resposta do CI alterados quando o `created_at` coincidia. Já `validate_draw`, usado pelo runner e pelo avaliador, só confere `SHA-256(signature) == randomness`. Ele aceitou um beacon sintético sem assinatura BLS válida e aceitou trocar simultaneamente o número da rodada e o commit declarado. Verificar a assinatura e a rodada derivada da evidência do CI, e exigir que o runner consuma o sorteio publicado antes do primeiro download. [Recomputação](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:353), [Validação offline](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:427)

2. **A trilha permite recontar os trânsitos, mas os campos usados no run podem divergir dela.** Mantive o TIC escolhido e alterei sua época, período, duração, setores e produtos. O validador aceitou. Também aceitou uma listagem com TIC errado, cadência de 1.800 s e setor 108 após recalcular o hash. A disjunção por produto consulta a lista redundante em `chosen`. Validar os filtros da listagem e reconstruir `chosen` a partir do quadro congelado e da trilha, incluindo efemérides, setores e produtos. [Validação da trilha](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:459), [Entrada do runner](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:133)

3. **Registros e manifestos ainda podem vir de outra execução.** O avaliador confere claim, modo e chave do alvo, mas os registros e lotes não carregam o hash do sorteio. A avaliação também deixa de chamar `verify_claim` e lê o manifesto de curvas que estiver no cache naquele momento, sem vínculo com o registro produzido pelo worker. Vincular registros, ledger e manifestos ao lock e ao sorteio, e verificar esses vínculos antes de retomar ou avaliar. A comparação de produtos pode continuar sendo apenas um relatório. [Registros e ledger](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:274), [Manifestos e entrada da avaliação](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:313)

4. **O código que registra o STOP e o código que o interpreta discordam.** Com **14,999 CPU-h** e um alvo que já não cabia, `_pick` retornou `no remaining target fits`, e a avaliação recusou o encerramento por teto. Se o CPU já chega ao teto na entrada do lote, o retorno ocorre antes de gravar o STOP no ledger. No sentido inverso, o avaliador aceitou um STOP antigo seguido de um lote sem STOP e aceitou todos os registros com ledger de lotes vazio. Gravar um estado terminal explícito após a drenagem e usar esse estado para decidir quando ausências contam como perdas. A política de tetos do mantenedor pode ser aplicada como documentada. [Admissão e STOP](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:606), [Estado do run](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:292)

O padrão legado de exposição ainda casa `statisTIC 12345` dentro de palavra. Testei a correção da fronteira contra as evidências registradas e **nenhuma exposição mudou**. Localizei **21 funções de teste** em `test_part_b.py`, e todas passaram em memória com fixtures de arquivo simuladas e o entry point TESS fornecido em memória. Lint, formatação, diff da bateria e importação como `__mp_main__` também passaram.

Revisão somente leitura, sem lock, consultas ao GitHub, drand ou MAST, abertura de fotometria ou acesso ao caminho proibido.

