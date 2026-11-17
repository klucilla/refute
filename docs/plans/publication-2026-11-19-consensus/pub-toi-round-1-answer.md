Conferi o HEAD `3757b7f`, somente com arquivos locais, sem rede e sem alterações. **Os cálculos conferem; o escopo precisa de correções.**

1. **Números e cálculos.** Efemérides, erros, durações, profundidades, coordenadas, datas cadastrais, setores, câmeras/CCDs e os seis SHA-256 correspondem às cópias locais, com os arredondamentos apresentados ([efemérides](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:64), [hashes](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:216)).

   Recalculei os **12 mid-times**, ambas as incertezas e todos os segmentos da [tabela](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:94). Os três eventos destacados resultam em:

   | Candidato, n | BJD recalculado | σ / σ_max, minutos | Segmento |
   |---|---:|---:|---|
   | .02, 102 | 2461364.7583246 | 2.692873 / 3.215520 | 2b |
   | .02, 103 | 2461367.9411124 | 2.694135 / 3.221280 | 2b |
   | .01, 30 | 2461368.2463480 | 2.666860 / 3.155040 | 2b |

   Os demais enquadramentos também conferem, inclusive `.02/n=100` no intervalo entre 1b e 2a e `n=104` após o setor. Reproduzindo a conversão geocêntrica com Astropy offline, **assumindo BJD_TDB**, todos os UTC apresentados ficam a menos de um minuto dos recalculados.

2. **Item 3a: transparência boa, conclusão excessiva e parada desrespeitada.** A página informa corretamente que o setor 110 começou e que 1a está público, incluindo câmera 1/CCD 2 ([linhas 36 e 109](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:36)). Prefira “um dos quatro segmentos” a uma fração exata de imagens, cuja contagem não foi verificada.

   Entretanto, o formulário oficial local declara atualização para **108–121** ([fonte:70](/C:/Projetos/refute/.cache/pub1119/toi7930/wtv-form.html:70)). Uma sondagem retornar até 120 não demonstra que 121 não seja calculado. Corrigir as [afirmações sobre o alcance da ferramenta](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:38) e preservar “nenhuma cobertura futura confirmada”, sem transformar isso em ausência comprovada até setembro de 2028.

   Além disso, a própria página reconhece a parada e depois desenvolve a “leitura 2” ([linhas 46–54](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:46)). **Isso ultrapassa a condição do item 3a** ([decisão:27](/C:/Projetos/refute/.cache/v054/issue-217-decisions-1116.md:27)). Registrar o resultado e submeter a dúvida ao mantenedor antes de desenvolver esse escopo alternativo.

3. **#24 e #25: citações fiéis.** Hit, miss, not evaluable, manutenção dos denominadores e ausência de confirmação planetária estão corretamente descritos ([texto:120](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:120); [#24:1](/C:/Projetos/refute/.cache/pub1119/issues/24.json:1), [#25:1](/C:/Projetos/refute/.cache/pub1119/issues/25.json:1)). Os parâmetros permanecem indefinidos, portanto não há regra operacional desenhada. Corrigir apenas “three windows combined per candidate”: em 2b são **duas para .02 e uma para .01** ([texto:135](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:135)).

4. **Limites e perguntas.** A página não mede fotometria, seleciona alvo para execução, cria lock ou chama candidatos de planetas. A pergunta sobre exceção de fase é expressamente autorizada e não executa um contorno. Porém, a pergunta 3 incorpora a conclusão excessiva sobre setembro de 2028; a pergunta 4 precisa preservar que os controles positivos de #25 são **planetas conhecidos**, condição não estabelecida aqui ([perguntas:197](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:197)).

5. **Calendário, preço e exageros.** O preço e a previsão de avaliação estão identificados como estimativas. Corrigir:

   - Os prazos de [23/11 no calendário](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:169) usam mid-times. Nesse instante parte do trânsito já existe; eles não garantem antecedência à janela inteira.
   - “Cada segmento aparece em cerca de uma semana” generaliza um único caso ([texto:112](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:112)); manter como hipótese.
   - As fontes não demonstram que o SNR agrega todos os trânsitos dos três setores. Os exemplos SNR≈10/6 são aritmeticamente coerentes com as contagens supostas, mas **“not evaluable provável” não se sustenta sem potência e limiar definidos** ([texto:145](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:145)).
   - “Só três janelas ainda podem preceder seus dados” é amplo demais: em 16/11, o evento de 17/11 também era futuro. Distinguir janela futura de segmento ainda não iniciado ([texto:114](/C:/Projetos/refute/docs/plans/toi-7930-prediction-scope.md:114)).

**WEAKENED (corrigir a parada do item 3a, o alcance do WTV, os prazos pelo mid-time e as afirmações de potência/disponibilidade).**

