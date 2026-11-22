## Rodada 4

**Pare antes do lock.** A regra nova elimina a dependência da cópia de CI no sorteio, mas o relock previsto para uma rodada vencida não funciona.

| Bloco | Veredito | Resultado |
|---|---|---|
| **A. Passo exploratório** | **SURVIVED** | Os artefatos e o pool permanecem idênticos aos já conferidos. |
| **B. Emenda e plano de lock** | **WEAKENED** | O fluxo inicial fixa a rodada antes do lock. O fluxo de descarte e relock descrito no plano não é executável como escrito. |
| **C. Claim e anexos** | **REFUTED** | A adulteração das efemérides foi fechada. Restam falhas no relock, na validação estrita da listagem e na classificação terminal. |

## Bloqueantes

1. **O relock documentado é recusado.** `refute lock --force --reason` substitui o arquivo existente. `lock_commit()` procura apenas commits que **adicionaram** o arquivo, então retorna o commit original. `github_time()` compara os bytes antigos com os novos e para. Também simulei remover e adicionar de novo, o que é recusado por haver duas adições. O check precisa localizar o commit que publicou os bytes do **lock vigente** e consultar o CI desse commit. [Plano de lock](/C:/Projetos/refute/docs/plans/v0.5.6-part-b-lock-plan.md:39), [Seleção do commit](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:307)

2. **A troca de rodada ainda pode contornar a condição de descarte.** O gerador aceita `--drand-round N` com lock existente sem comprovar que a rodada anterior venceu. `check` também retornou sucesso em memória para um claim alterado, pois não verifica o lock antes de ler a rodada. O sorteio verifica o lock, mas a preparação do relock ainda precisa exigir a expiração da rodada selada. Além disso, a suíte completa rejeita o estado legítimo entre `auto` e `lock`, porque um teste exige `unset` enquanto o lock ainda não existe. [Gerador](/C:/Projetos/refute/calibration/v0.5.6/part_b_claim.py:184), [Check](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:354), [Teste](/C:/Projetos/refute/tests/v056/test_part_b.py:458)

3. **A listagem ainda aceita setor booleano.** As efemérides alteradas em `trail` e `chosen`, o setor zero, a cadência `NaN` e a janela não finita foram recusados. Já `sector: true` passou pela validação completa em memória, pois `bool` é subtipo de `int` em Python. O filtro precisa exigir um inteiro de setor. [Filtro de listagem](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:545)

4. **Uma falha registrada ainda pode resultar em terminal `complete`.** O caso de falha durante STOP por disco agora dá `other`, e manifesto ilegível segue o caminho de falha. Porém, numa retomada com todos os registros presentes e uma falha já anotada, `terminal("complete", ...)` retornou `complete`. O avaliador recusou o ledger, como deve. Para cumprir a regra acordada, a falha precisa prevalecer também sobre `complete`. [Terminal](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:858), [Avaliação](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:305)

As **27 funções de teste** presentes no arquivo passaram em memória com o claim ainda no estado de template. Lint e formatação passaram. A revisão foi somente leitura, sem lock, consultas externas ou acesso ao caminho proibido.

