## Rodada 5

**A, B e C: SURVIVED. Nenhum bloqueante no escopo revisado.** O commit `8b8cce5` fecha os quatro itens da rodada 4 e atende ao critério do mantenedor para prosseguir conforme o plano de lock.

| Bloco | Veredito | Resultado |
|---|---|---|
| **A. Passo exploratório** | **SURVIVED** | Os artefatos e o pool conferidos nas rodadas anteriores permanecem idênticos. |
| **B. Emenda e plano de lock** | **SURVIVED** | A emenda, o plano e o claim concordam. Se a rodada selada for igual ou anterior ao horário do lock no GitHub, a execução para antes do sorteio e vai ao mantenedor. O relock foi removido do fluxo. |
| **C. Claim e anexos** | **SURVIVED** | O gerador recusa número manual e qualquer reescrita com lock ou sorteio presente. `check` e `draw` verificam o lock primeiro e param antes de consultar o beacon se a rodada venceu. Setor booleano é rejeitado, e falha registrada prevalece como `other` na retomada. |

**Não bloqueante para o #59.** Numa retomada com todos os registros presentes e uma falha anterior, o ledger pode mostrar `state: complete` junto de `kind: other`, e o runner pode sair com sucesso. O avaliador recusa esse ledger, preservando o veredito e a regra de perdas. Vale alinhar o estado e a saída do runner ao `kind`. [Runner](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:819), [Avaliador](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:305)

Conferi os JUnit locais e repeti em memória os **36 testes**, todos aprovados. O gerador reproduziu o runner e o diff versionados. A revisão foi somente leitura, sem lock, consultas externas ou acesso ao caminho proibido.

