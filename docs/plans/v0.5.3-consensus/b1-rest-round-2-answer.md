**As correções principais funcionam, mas resta uma falha de recuperação em `run 2`.**

- **Argumentos e retomadas:** somente `1` e `2` são aceitos; partes existentes passam pela verificação de identidade. O fingerprint continua `5bb3277e4a908c18`, com 181 shards originais válidos. [b1_d2d4_rest.py:106](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:106).
- **Orçamento e fechamento:** a margem é aplicada corretamente. Em simulações em memória, `complete_records()` aceitou 200 registros válidos e recusou parada do driver, gate falho, consumo acima de 1,5, duplicação e linha ausente. A integração do novo script usa essa função. [b1_d2d4_rest.py:169](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:169), [b1_d2d4_rest.py:209](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:209), [b1_blockers_decisive.py:254](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_blockers_decisive.py:254).

**Defeito restante:** a reconciliação do ledger ainda precede a reconciliação do driver e a criação da segunda parte. Se houver interrupção ou falha nesse intervalo, a causa fica reconciliada, mas `rest2` ainda não existe. A próxima chamada exige novamente `unresolved_stop` e recusa continuar. Além disso, transferência, declaração, `hard_cap` e gates ainda podem recusar depois da reconciliação. [b1_d2d4_rest.py:124](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:124), [b1_d2d4_rest.py:154](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:154).

Reproduzi dois casos com mocks: transferência recusada e falha ao arquivar a parada do driver. Ambos deixam a chamada seguinte bloqueada.

**Correção:** reconhecer a reconciliação autorizada persistida também quando `rest2` ainda não existe, permitindo concluir sua preparação e qualquer reconciliação pendente do driver, com validação da causa e sem autorizar outra tentativa. Antecipar também as recusas previsíveis restantes.

Nenhuma curva foi executada e nenhum arquivo foi alterado.

WEAKENED (tornar recuperável a preparação de run 2 entre reconciliação e criação da parte).