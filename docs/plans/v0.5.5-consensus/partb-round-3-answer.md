## Rodada 3 de 3

**Veredito final: pare antes do lock.** O pool corrigido conferiu. Restam três bloqueantes que podem mudar a amostra ou o tratamento das perdas.

| Bloco | Veredito | Resultado |
|---|---|---|
| **A. Passo exploratório** | **SURVIVED** | Os artefatos permanecem idênticos aos da rodada 2. Valem os **973 TICs expostos**, o pool de **197 planetas e 411 FPs** e os 14 casos exploratórios conferidos. |
| **B. Emenda e plano de lock** | **WEAKENED** | O desenho estatístico, a divulgação e o escopo de concordância estão definidos. Ainda falta garantir que a rodada consumida venha da execução de CI correta e que uma falha durante a drenagem prevaleça sobre o STOP por teto. |
| **C. Claim e anexos** | **REFUTED** | O schema aceita o claim e os seis anexos. A bateria da parte A foi preservada. Os testes em memória reproduziram as brechas abaixo. |

## Bloqueantes antes do lock

1. **A assinatura BLS valida o beacon, mas a origem da rodada ainda depende do próprio draw.** A geração consulta o GitHub e compara os campos da execução de CI. No consumo, o validador aceita o `created_at` embutido no draw como premissa. Com a leitura do commit simulada, um `created_at` inventado e um beacon histórico com assinatura BLS autêntica passaram nas duas verificações. A publicação do draw confirma sua presença no Git, sem confirmar o horário do CI. O consumo precisa vincular a rodada à execução de CI por evidência independente do próprio draw. [Geração](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:363), [Validação da rodada](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:455)

2. **A trilha ainda pode sobrescrever as efemérides congeladas.** Alterei período, época e duração simultaneamente em `trail` e `chosen`. `validate_draw` aceitou: a reconstrução só copia do quadro os campos ausentes na trilha. Assim, a elegibilidade é recontada com a efeméride congelada, enquanto o runner recebe a alterada. O validador também aceitou setor zero e cadência `NaN`. Reconstruir os campos científicos diretamente do quadro e rejeitar setores e cadências inválidos antes de recontar a elegibilidade. [Filtros](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:500), [Reconstrução](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:575)

3. **Uma falha após o STOP por teto pode virar perda elegível.** Simulei um STOP por disco seguido de falha de um worker em voo. O ledger registrou a falha, mas o terminal ficou `cap_disk`, e o avaliador aceitou a ausência como perda. Isso permite que um alvo **admitido e sem registro por falha** entre na regra reservada aos alvos não admitidos. Além disso, uma exceção na leitura do manifesto de curvas escapa de `_finish` antes do tratamento de falha. Fazer a falha prevalecer como `other` e encaminhar erros de manifesto pelo mesmo fluxo. [Gravação do registro](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:600), [Drenagem](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:706), [Avaliação do terminal](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:305)

As **23 funções de teste** que localizei em `test_part_b.py` passaram em memória, com fixtures de arquivo simuladas e o entry point TESS fornecido em memória. Lint, formatação e importação como `__mp_main__` também passaram. A revisão termina em somente leitura, sem lock, consultas externas, abertura de fotometria ou acesso ao caminho proibido.

