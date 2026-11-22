## Rodada 1 de até 3

**Pare antes do lock.** O pool inclui **286 TICs com exposição anterior documentada**, e a execução aceita um sorteio sem verificar sua origem.

| Bloco | Veredito | Resultado |
|---|---|---|
| **A. Passo exploratório** | **REFUTED** | Os 14 casos e as sete tabelas conferem. A varredura de exposição deixa TICs inelegíveis nos dois estratos. |
| **B. Emenda e plano de lock** | **WEAKENED** | A divulgação, o uso da disposição congelada, o texto de concordância, o rótulo de limites e as regras estatísticas estão definidos. O plano ainda deixa margem para escolher entradas ou encerrar a avaliação após o lock. |
| **C. Claim e anexos** | **REFUTED** | O schema `discover` aceita o pool e a cadeia da bateria foi preservada. O sorteio, o runner e a avaliação deixam de verificar vínculos que podem mudar a amostra ou o veredito. |

## Bloqueantes antes do lock

1. **A exposição anterior muda o pool.** O scanner herda os padrões textuais da parte A e ignora a chave JSON `"tic"`. O `geometry-list.json` da v0.2.1 registra a avaliação de geometrias a partir de metadados MAST por TIC. Só esse arquivo acrescenta **796 exposições** no quadro e retira **91 planetas e 195 FPs** do pool publicado. Com esse ajuste isolado, **288/606 passam a 197/411**, ainda antes da elegibilidade MAST. A regra por pasta também classifica como cópias os CSVs `inputs-references` consultados para controles já selecionados. Nesse segundo caso, os TICs já estavam excluídos por outras evidências. Corrigir a leitura, classificar as exceções por arquivo e regenerar as contagens, o pool e os hashes dependentes. [Scanner](/C:/Projetos/refute/docs/validation/v0.5.6/part_b_prep.py:178), [Registro de geometria](/C:/Projetos/refute/docs/validation/v0.2.1/reopen/stage-1/viability-cd/geometry-list.json:58)

2. **O sorteio aceita uma rodada sem vínculo com o lock em uso.** `round` calcula corretamente a regra dos 600 segundos a partir do CI. Já `draw` usa diretamente `part-b-round.json`. Em memória, confirmei que ele encaminha ao verificador um número associado a outro commit e a margem zero. A assinatura BLS autentica o beacon daquela rodada. Vincular o SHA-256 do lock aos bytes no commit publicado, preservar a evidência do CI e recomputar a rodada no sorteio. [Rodada](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:231), [Consumo da rodada](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:307)

3. **A amostra e os insumos precisam de uma trilha reproduzível.** O sorteio lê apenas metadados, mas reutiliza qualquer JSON MAST presente no cache e guarda nomes e hashes sem preservar as janelas usadas para contar trânsitos. Também lê o `part-a-draw.json` sem conferir o hash declarado no claim. Depois, o runner consulta MAST de novo, registra setores extras e guarda no registro os hashes dos TPFs. Os hashes das curvas ficam no manifesto local do adaptador. Congelar e preservar as listagens efetivas e a versão do Python, conferir o draw da parte A pelo hash e reconciliar os produtos efetivamente usados com a trilha publicada. [Walk MAST](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:259), [Disjunção](/C:/Projetos/refute/calibration/v0.5.6/part_b_draw.py:321), [Manifestos no runner](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:234)

4. **O runner e o avaliador confiam no sorteio e em registros sem validar o estado final.** O runner aceitou em memória um `short` com um TIC total. O avaliador aceitou `short` com 119 em um estrato e produziu `REFUTED` para um `complete` vazio. Também agrupa registros por `target_key`, sobrescrevendo duplicatas, e trata qualquer ausência como perda, inclusive antes do fim do run. Para fechar essa margem, validar o sorteio publicado, recomputar tamanhos e unicidade, vincular cada record ao lock e ao draw e exigir conclusão ou STOP por cap documentado para usar ausências. [Runner](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:112), [Avaliador](/C:/Projetos/refute/calibration/v0.5.6/part_b_evaluate.py:186)

5. **Os tetos têm margem de ultrapassagem.** Os 15 CPU-h usam estimativas na admissão. Os 20 GB são amostrados e, após um STOP, os workers em voo ainda terminam. O plano precisa explicitar como uma ultrapassagem encerra o run e afeta a avaliação, ou o runner precisa impor os tetos como escritos. [Admissão](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:586), [STOP](/C:/Projetos/refute/calibration/v0.5.6/part_b_run.py:681)

## Verificações que passaram

- **Parte A:** conferi os 240 registros. Entre os `REFUTED`, a identidade bate em **1/9 no braço planeta** e **5/5 nos FPs**. Os dois meios-períodos conferem. Os **263 TICs consultados** pela parte A pertencem à metade exploratória. A inspeção só de nomes reproduziu os **1.316 FITS** no padrão SPOC fora de `.cache/v056`.
- **Runner e estatística:** o `run_one` difere da parte A apenas nos campos de identificação do registro. O diff confere e a importação como `__mp_main__` disponibiliza `run_one` e o inicializador. Com entradas válidas, Fisher unilateral exato, Wilson, guarda e mapeamento conferem. `ERROR` conta como não-evento e perda. Em 120 sorteados, **12 perdas são aceitas e 13 dão `INCONCLUSIVE`**. Empate de taxas ficou acima de alfa.
- **Escopo do lock:** validei em memória o claim resolvido, os seis anexos e o fingerprint de `src/`, `pyproject.toml` e `uv.lock`. Os hashes em `discovery.inputs` são valores selados no claim. A verificação genérica não relê os arquivos externos que eles descrevem. As **15 funções de teste passaram em memória** com o entry point oficial do pack TESS fornecido em memória, pois a instalação editável estava inacessível no sandbox. Também passaram lint e formatação.

A revisão foi somente leitura, sem lock, consulta ao drand ou MAST, abertura de fotometria ou acesso ao caminho proibido.

