## Rodada 2 de 3 · WEAKENED

**O pacote de `c1d5691` ainda não pode ser construído para a segunda revisão cega.** O `MANIFEST.json` republica o comentário histórico removido de `values.py`. A regra pareada também promete 80% de poder onde seu próprio corte de discordância limita o poder a cerca de 52%.

Conferi o diff de `f8f8db1` para `c1d5691` em leitura estática. A checagem dos 19 arquivos e os 18 testes JUnit são informações fornecidas por você.

## Vereditos

| Item desta rodada | Veredito | Conclusão |
|---|---|---|
| **1. Não inferioridade e B1 (e)** | **REFUTED** para a garantia de poder. **SURVIVED** para B1 (e). | A aproximação dá cerca de 1.546 pares, mas não dimensiona a regra exata completa. O limite sobre **SURVIVED + WEAKENED** agora está explícito em toda família espúria. |
| **2. B3.3 e VN** | **WEAKENED** | A regra e as guardas estão prontas para julgamento cego. O desenho de VN ainda não fecha o item 5 para B3.3 entrar como decisiva. |
| **3. B2 e confirmação** | **SURVIVED** | A semântica de B2(b) inclui o sorteio conjunto e mantém a opção inelegível. A confirmação explicita tiro único, consequências de FAIL e NOT DECIDABLE, e a regra de avanço. |
| **4. Cegueira e construtor** | **REFUTED** | O parágrafo e a tabela foram neutralizados. A cópia de `values.py` está correta. O campo `replaced` devolve ao revisor o texto removido. |
| **5. Definição das metas** | **SURVIVED** | T2b explicita os grupos e o numerador, T2c exclui as estrelas de desenvolvimento e T3a/T3b exigem leitura no estágio 2 sem o catálogo e grupos completos com identidade qualificada. |
| **6. Ressalvas da rodada 1** | **SURVIVED** | (a′) usa o conjunto decisivo e classifica teste esperado ausente. As variantes inelegíveis ficam registradas como tais. A docstring aponta para os caminhos da segunda rodada. |

Os itens originais **1, 2, 6 e 10** permanecem **SURVIVED**.

## Bloqueios para construir o pacote

1. **Retirar o resultado histórico do manifesto.** Em `r2_bundle.py:194–197`, remover `replaced` do manifesto entregue. Texto suficiente para `review_copy`: “Comentário imediatamente anterior a `V05_DECISIVE` substituído na cópia de revisão.” Manter o hash da origem e o hash do arquivo entregue. Em `r2_bundle.py:164–167` e `:212–219`, incluir o conteúdo do manifesto na checagem antes da primeira gravação, com metadados de exclusão e corte em texto neutro. Em `test_r2_bundle.py:117–127`, trocar a asserção que **exige** o texto antigo no manifesto por uma que confirme sua ausência em ambos os artefatos entregues. Hoje a checagem roda antes de o manifesto existir, e `check()` confirma integridade, inclusive a de um manifesto que contenha o vazamento. [Construtor](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:160) · [Teste da cópia](/C:/Projetos/refute/tests/v055/test_r2_bundle.py:117)

2. **Corrigir a regra de poder antes de apresentar 1.550 como tamanho suficiente.** Para pares independentes, com discordância verdadeira \(\pi\), a variância é \((\pi-d^2)/n\). Em \(d=0\), ela é exatamente \(\pi/n\). **A aproximação está no cálculo normal do tamanho**, e a aritmética de 1.546 está correta para esse cálculo. Já com o corte observado em 0,10, se a discordância verdadeira for 0,10, o PASS exige no máximo 155 discordâncias em 1.550 pares. Mesmo que o intervalo sempre passasse, o poder seria no máximo \(\Pr[\operatorname{Bin}(1550,0{,}10)\le155]\), cerca de **52%** pela aproximação normal. Aumentar \(n\) mantendo o mesmo corte na fronteira dessa população leva esse teto a 50%.

   Em `argumentos:225–235`, usar: “1.550 é uma estimativa inicial. Antes do congelamento, fixar a ordenação do teste e o menor tamanho válido que demonstre pelo menos 80% de poder em \(d=0\) para toda a faixa de discordância de desenho. Calcular o poder da regra completa por enumeração exata ou por garantia analítica conservadora. Se houver corte de discordância observada, fixá-lo separadamente e incluí-lo no cálculo de poder.” Para **T2b**, também falta definir a estatística e o método exato para as rotações da mesma estrela. Se a seção 7 mantiver o teste trinomial, uma opção é pré-especificar uma rotação por estrela **para essa salvaguarda pareada**, preservando todas as rotações na métrica congelada de T2b. A margem, o tamanho e o poder-alvo continuam sendo números de desenho permitidos. O tamanho definitivo precisa ser demonstrado **antes do congelamento**, sem exigir execução nesta rodada. [Argumentos](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:221) · [C2](/C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:1)

3. **Para enviar B3.3 como candidata decisiva, tornar VN reproduzível e exigir que ela exercite o ramo.** Em `metas:50–67`, usar: “Definir a lei das fases relativas para cada forma e sortear uma fase global. Sortear independentemente o tipo com probabilidade \(1/3\) por curva se for usado o teste trinomial agregado. Usar \(a_1/\sigma_w\) log-uniforme em \([0{,}5,5]\), explicitando que essa é a escala de amplitude de V1/V2. Aplicar a busca e o gate congelados e registrar o alinhamento encontrado. Fixar previamente um mínimo de casos ambíguos elegíveis com domínio, cobertura e detectabilidade válidos. Abaixo dele, a salvaguarda de VN é NOT DECIDABLE.” Hoje, a mesma lei de amplitudes e fases aleatórias não distingue as três formas, e um total de zero casos no ramo ainda poderia produzir um resultado agregado favorável. Se essa definição ficar em aberto, registrar antes da construção **o ramo congelado como decisivo e B3.3 apenas como variante**. A segunda revisão cega já consegue julgar a desigualdade e as guardas com o texto atual. [Metas de VN](/C:/Projetos/refute/docs/plans/v0.5.5-r2-targets.md:47) · [Amplitude em C1](/C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:310) · [Argumentos de B3.3](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:148)

## Ressalvas

- Em `r2_bundle.py:26–29`, ajustar “byte for byte” para “byte for byte, exceto pela cópia de revisão declarada no manifesto”. [Construtor](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:23)
- Em `argumentos:333`, registrar na disclosure que a revisão independente anterior também era conhecida na segunda revisão dos argumentos. A primeira revisão cega já está listada. [Disclosure](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:333)

**Decisão da rodada 2: o pacote novo ainda não pode ser construído.** Corrigir o manifesto e a especificação de poder. Para B3.3, fechar VN ou registrar a variante com o ramo congelado como decisivo.

