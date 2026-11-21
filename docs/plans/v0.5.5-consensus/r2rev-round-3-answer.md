## Rodada 3 de 3 · SURVIVED para construção

**Sim. O pacote de `5bbd8b3` pode ser construído uma vez para a segunda revisão cega. A B3.3 pode seguir como candidata decisiva condicionada.** Aceito a definição de VN para esse julgamento. Não resta divergência que exija registrar a opção conservadora antes da construção. Se a segunda revisão cega deixar qualquer condição de B3.3 em aberto, **o ramo atual fica decisivo e a divisão por evidência fica só como variante relatada**. [Argumentos:168](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:168)

| Item | Veredito | Evidência |
|---|---|---|
| **1. Manifesto** | **SURVIVED** | O texto removido sai dos artefatos entregues. O manifesto registra a transformação e os hashes de origem e entrega. O construtor verifica o JSON serializado antes da primeira gravação. Os testes adicionados cobrem a ausência do texto e a recusa de manifesto contaminado. [Construtor:193](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:193) · [Testes:117](/C:/Projetos/refute/tests/v055/test_r2_bundle.py:117) |
| **2. Poder** | **SURVIVED para revisão cega** | 1.550 está identificado como estimativa. O corte na discordância observada saiu. Ordenação e tamanho definitivo ficam sujeitos à demonstração de 80% de poder em toda a faixa de desenho antes do congelamento. A salvaguarda pareada de T2b usa uma rotação pré-especificada por estrela e a métrica congelada usa todas. [Argumentos:220](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:220) |
| **3. VN e B3.3** | **SURVIVED para julgamento condicionado** | VN especifica a mistura independente, as leis de fase e amplitude, a busca, a elegibilidade e o comparador pareado. A exigência de **100 casos ambíguos elegíveis** impede um PASS da salvaguarda quando o ramo foi pouco exercitado. Abaixo do mínimo, VN fica NOT DECIDABLE e B3.3 não é adotada. Os 100 casos são um limiar de desenho, com a demonstração de poder tratada separadamente na seção 7. [Metas:50](/C:/Projetos/refute/docs/plans/v0.5.5-r2-targets.md:50) · [Argumentos:163](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:163) |
| **4. Docstring e disclosure** | **SURVIVED** | A docstring declara a exceção da cópia de revisão. A disclosure registra a primeira revisão cega e as revisões independentes dos argumentos. O corte exclui essa seção do pacote. [Construtor:23](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:23) · [Disclosure:341](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:341) |

## Bloqueios e ressalvas

**Construção do pacote: sem bloqueios.** Antes do **congelamento**, ainda é obrigatório fixar a ordenação do teste exato, demonstrar o tamanho válido para o poder exigido e aplicar o mesmo critério de poder a T2b. O pacote pode seguir com essas condições explícitas. [Argumentos:230](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:230)

**Ressalva editorial em VN.** Em `metas:58–59`, prefira “perfil multiharmônico com fases relativas fixas”. Na convenção de seno usada em C1, as fases do terceiro tipo resultam numa soma de cossenos deslocada e simétrica. A fórmula continua sendo um controle periódico não senoidal, suficiente para a revisão cega. [Metas:58](/C:/Projetos/refute/docs/plans/v0.5.5-r2-targets.md:58) · [C1:201](/C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:201)

Conferi `HEAD` e `main` em `5bbd8b3` por leitura estática. A checagem dos 19 arquivos e os 19 testes JUnit são evidências informadas por você. O pacote permanece por construir.

