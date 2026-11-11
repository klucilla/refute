**O desenho precisa de revisão antes do código.** A arquitetura proposta é viável, mas a recalibração e o forecast de T2a têm problemas que impedem suas conclusões planejadas.

Somente leitura. Não alterei arquivos, não executei forecasts nem acessei o diretório proibido. Fiz apenas contas pequenas para verificar os intervalos.

Referências `B1:linha` apontam para [v0.5.3-stageB1-design.md](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md).

### 1. Seção 0, candidato fora de `src/`

**Pode ficar fora de `src/`. Não precisa entrar em `src/` agora.** Isso atende à restrição explícita desta revisão. A formulação histórica da etapa A dizia “após o stop que aprova stage B”, portanto convém não atribuir ao documento antigo uma exigência específica de esperar o fim de B1 ([stageA/README.md:160](C:/Projetos/refute/docs/validation/v0.5.3/stageA/README.md:160)).

O patch em processo é verificável, com estas condições adicionais a [B1:26](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:26):

- Ativação explícita em **cada worker criado por Windows spawn**, por inicializador importável ou entrada do shard. Ativar apenas no controlador não basta.
- Registrar identidade, hash, configuração E1–E4 e **execução efetiva** dos caminhos usados. Identidade da função não prova que ela foi chamada.
- Restaurar integralmente v4 antes do comparador, inclusive constantes de configuração C, com teste v4 → candidato → v4.
- Fingerprint próprio cobrindo scripts externos, configuração e amostra. O hash padrão cobre `src/`, `pyproject.toml` e `uv.lock`, deixando o candidato externo de fora ([codehash.py:3](C:/Projetos/refute/src/refute/core/codehash.py:3)).

Os pontos de chamada permitem isso: [pipeline_v52.py:101](C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:101), [pipeline_v52.py:143](C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:143). Evitar patches globais que também alterem os consumidores declarados inalterados.

### 2. E1 a E4

**E1, pooling e PSD: não sobrevive como garantia conservadora.** [B1:81](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:81)

- Padronizar setores elimina diferenças de localização e escala, **não diferenças de correlação**. Pooling entre estratos ou setores pode subestimar a correlação relevante. A primeira alternativa também contorna a condição de equivalência exigida pelo shortcut atual ([a0.py:227](C:/Projetos/refute/src/refute/packs/tess/a0.py:227)).
- `max(repaired, diagonal)` não limita superiormente a variância verdadeira. Para erros unitários, contraste `(1, −1)` e correlação verdadeira `−0,5`, a variância é `3`, enquanto o piso diagonal é `2`.
- Distância Frobenius ≤0,10 controla a alteração numérica, não a incerteza estatística. Higham resolve proximidade entre matrizes, sem fornecer esse conservadorismo ([fonte do autor](https://nhigham.com/2013/02/13/the-nearest-correlation-matrix/)).

**Correção:** declarar pooling/reparo como modelos candidatos, congelar condições de uso, convergência e tratamento de singularidade, e testar cobertura por ramo, estrato e contraste assinado. Preservar indisponibilidade onde não houver sustentação.

**E2, família box: sim; proximidade ao bound: não estabelecida.** [B1:105](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:105)

GLS sobre profundidades box e baseline linear continuam na família box, desde que eventos reais e pseudo-janelas usem exatamente o mesmo operador. É necessário refazer também a medição real, atualmente recebida pronta pelo teste ([pipeline_v52.py:64](C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:64)).

O ganho da reta existe para cobertura assimétrica, mas deve prever a baseline **nos tempos efetivamente observados dentro do evento**. Com cobertura simétrica e tendência linear, não há ganho; curvatura permanece.

GLS separado por grupo minimiza cada média condicionalmente à covariância, mas não necessariamente o contraste conjunto quando há covariância odd/even. Usar a covariância completa para sua variância. O bound usa template verdadeiro, não boxes locais, portanto não prometer sua atingibilidade ([d2_bounds.py:131](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:131)).

**E3, GLS: direção plausível, estimador ainda incompleto.** [B1:123](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:123)

“Branco + AR(1), ambos estimados por lag 1” não identifica claramente amplitudes e coeficiente. A autocorrelação lag 1 da mistura é atenuada pelo branco; não é diretamente o coeficiente AR(1). Além disso, resíduos após ajuste podem reduzir a potência estimada do ruído.

Congelar estimação, correção pelos parâmetros ajustados, tratamento dos gaps e fallback. O `H` precisa ajustar **somente OOT e prever toda a série**, como no código atual ([battery_v52.py:235](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:235)). A fórmula é correta para modelo linear e covariância conhecidos, mas o plug-in não inclui automaticamente incerteza da covariância nem seleção de frequências.

**Retirar “This is stage A’s oracle”**: o bound é de um ajuste conjunto com coluna box; o procedimento proposto mantém ajuste OOT e contraste residual ([d2_bounds.py:147](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:147)). Especificar implementação sem matrizes densas por cadência.

**E4, spline: viável somente com contrato de máscara completo.** [B1:138](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:138)

“Mesma série residual” não basta. O spline deve ser **reajustado por comb**, mascarando eventos reais e pseudo-janelas, incluindo as bandas prometidas pelo desenho. Caso contrário, pseudo-janelas influenciam seu próprio modelo, enquanto eventos reais não influenciam, reproduzindo a assimetria que v4 corrigiu ([a0_v4.py:4](C:/Projetos/refute/src/refute/packs/tess/a0_v4.py:4)).

Knots espaçados não garantem ausência de absorção. Uma elevação confinada inteiramente à máscara fica protegida do ajuste linear fixo; uma elevação larga, rampas e erros de efeméride podem ser absorvidos parcialmente.

Congelar knots, gaps, bordas, rank e fallback. Exigir injeções que meçam preservação da elevação e a validade do bloco de sensibilidade, que pressupõe a alternativa na escala original ([battery_v51_diff.py:649](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:649)). Wotan recomenda mascaramento, mas também reconhece risco de remoção do sinal, não certifica esta construção ([documentação](https://wotan.readthedocs.io/en/latest/Interface.html#choosing-the-right-window-size)).

### 3. B1.2, screening

**Não contamina automaticamente o forecast**, desde que parâmetros, regras de fallback e decisões de inclusão permaneçam congelados ([B1:163](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:163)).

Qualquer correção motivada pelos resultados exige emenda prospectiva e novos dados para a avaliação afetada. Screening só de perdas não mede regressões gerais. Registrar também PASS → INCONCLUSIVE e mudanças de sensibilidade, não apenas PASS → FAIL.

### 4. B1.3, nulidade e tamanho

**O deslocamento de um quarto de período não garante nulidade.** [B1:174](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:174)

- Verificar ausência de sobreposição com trânsitos verdadeiros e respectivas bandas; manter suas máscaras no preprocessing.
- E1/E2 produzem um contraste odd/even por conjunto, não um contraste independente por evento.
- E3 precisa de esperança conhecida e tratamento da variabilidade residual e da seleção de frequências.
- E4, nas auxiliares padrão de C1, recebe background essencialmente constante com ruído branco. Isso não testa a variabilidade lenta que motivou a mudança ([synthetic.py:358](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:358)).

**Os critérios são razoáveis como tolerâncias, mas incompatíveis com 100 contrastes independentes.** Mesmo idealmente, com Bonferroni sobre quatro:

| Resultado ideal em 100 valores | Intervalo aproximado |
|---|---|
| Média observada zero | ±0,250 |
| Desvio observado 1 | [0,848; 1,212] |
| Zero excedências de 3σ | limite superior unilateral 0,043 |

Nenhum demonstra as tolerâncias propostas. Muitas janelas da mesma curva não podem ser contadas como independentes.

Congelar inferência por curva, tamanho/poder e simultaneidade também entre os três critérios e células. Separar **FAIL de UNRESOLVED**. Não usar um estimador não aprovado é correto como bloqueio, mas a combinação resultante precisa ser definida e verificada, especialmente E2 dependente de E1 ([B1:180](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:180)).

### 5. B1.4, forecast

**Seeds:** não encontrei reutilização das faixas propostas nos scripts inspecionados. Isso ainda precisa de verificação executável contra manifestos anteriores, incluindo smokes e seeds efetivamente usados ([B1:171](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:171)).

**D2/D4:** os limites numéricos permanecem, mas exigir intervalos para retenção/D4 acrescenta uma condição ao critério congelado. Reportar separadamente regra original e diagnóstico conservador. Preservar piso de elegibilidade 20, tratamento de erros e comparador v0.4, necessário para D2 ([c1.py:633](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:633)).

**T2a tem dois bloqueios centrais.** [B1:202](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:202)

1. Excluídas as 110 antigas, a amostra vem das populações restantes **262/217/26**, não diretamente de **302/257/56**. Não reutilizar os intervalos originais sobre 615. Uma solução é medir as 110 antigas sob o candidato congelado como parcela censitária e inferir separadamente o complemento. Dados antigos v4 não substituem resultados v5.
2. **B não pode obter PASS com 80+80**, mesmo ignorando o problema anterior: com todos os 160 sucessos, os limites hipergeométricos originais dão `(287+245)/615 ≈ 0,865`, abaixo de 0,89675. Dimensionar isso antes da execução.

**A configuração B responde à pergunta certa**, condicional à certificação até 20 setores. Contudo, `UNRESOLVED` significa margem não demonstrada, não certificação acima de 20 comprovadamente necessária. B favorável também não aprova A.

O smoke deve medir **C**, incluindo o caminho liberado acima de 20. A/B continuam perdas conhecidas por regra; apenas C fica desconhecida se não medida. Uma execução curta não garante todas abaixo de 30 minutos; congelar tratamento de overrun e stop ([B1:218](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:218)).

Não chamar `fetch()` antigo literalmente: ele seleciona a amostra antiga e escreve seus relatórios. Reutilizar a lógica com amostra e destinos próprios de B1, preservando URLs e hashes ([forecast_t2a.py:156](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a.py:156)).

### 6. Caps, ledger e stop

A tabela soma **120 CPU-h**, e o lock durante toda a execução é adequado ([B1:233](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:233)). Acrescentar:

- Limite global, consumo anterior, reserva em voo e recusa de nova identidade antes de executar.
- Preço dos comparadores v0.4/v4/v5 e configurações realmente executadas.
- Cap numérico de disco, ausente apesar da promessa.
- Reprecificação por disponibilidade e tamanho da nova família, não apenas multiplicação dos custos antigos.

O stop cobre os entregáveis pedidos, mas T3b não pode pressupor que A, B ou C preserva a classe. O registro anterior concluiu **nenhuma como escrita**, e C não demonstrou maior pureza ([t3b-status.md:56](C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b-status.md:56)). Trazer recomendação condicionada à qualificação e seu preço, sem transformar contagens em preservação demonstrada.

**REFUTED, como desenho pronto para código: corrigir os modelos de erro, dimensionar a recalibração e reparar a amostragem e a capacidade decisória de T2a antes de implementar.**