A rodada 2 resolveu parte importante da revisão anterior, mas **ainda há bloqueios antes do código**, sobretudo na recalibração, no tratamento dos gaps de E3 e na conclusão sobre T2a.

Somente leitura, sem alterações, workloads pesados ou acesso ao diretório proibido. Abaixo, `B1:linha` refere-se ao [desenho revisado](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md).

### 1. E1, limite correto, com alcance condicional

**Quando todos os pares dentro da janela são limitados, o argumento está correto**, inclusive para pesos assinados e matriz estimada não PSD:

\[
V \leq \sum_i w_i^2\sigma_i^2+
2\sum_{(i,j)\in W}|w_iw_j|\sigma_i\sigma_j.
\]

Não é necessário que os máximos individuais sejam simultaneamente atingíveis. Isso apenas torna o limite potencialmente folgado. Valem os zeros fora da janela definidos pelo modelo ([B1:98](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:98)).

**Quando somente os termos indefinidos são limitados**, o resultado limita as completações compatíveis com os termos estimados mantidos. Não limita “quaisquer correlações verdadeiras”: estas podem diferir das estimativas conhecidas. Corrigir essa afirmação e “não precisa de calibração além de v4” ([B1:107](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:107)). O novo domínio continuava sem permissão calibrada em v4.

Para preservar todos os casos decididos por **E1 isoladamente**, congelar:

- Primeiro retornar exatamente o resultado finito de v4, com seu shortcut e sua tolerância PSD.
- Aplicar a extensão somente nas recusas previstas.
- Definir como detectar inconsistência quando existem simultaneamente termos ausentes e estimados.

O código atual retorna antes de construir toda a matriz quando encontra uma correlação ausente ([a0.py:297](C:/Projetos/refute/src/refute/packs/tess/a0.py:297)). A nova ordem precisa estar especificada.

### 2. E2, contraste correto, condição de uso incompleta

O modelo conjunto e a expressão da variância estão corretos. A retirada da baseline local preserva a família atual de boxes reais e pseudo-janelas ([B1:114](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:114)).

**“Completa e PSD” não basta para usar \(C^{-1}\).** Uma matriz PSD pode ser singular; uma positiva definida pode estar numericamente mal condicionada ([B1:126](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:126)).

Congelar condição de rank/condicionamento de `C` e do problema de dois parâmetros, solução numérica e fallback. A correção simples é voltar aos pesos v4 quando o GLS não for numericamente confiável, usando o resultado de E1 quando aplicável. Os limites escalares de Cauchy-Schwarz não devem ser transformados em uma matriz para inversão.

E2 pode mudar decisões anteriormente tomadas por v4, intencionalmente. A preservação discutida em E1 não se estende à bateria completa.

### 3. E3, momentos válidos, recursões ainda não especificadas suficientemente

As identidades estão corretas para branco independente mais AR(1) estacionário, sendo **\(\sigma_a^2\) a variância estacionária do componente latente**, não sua variância de inovação ([B1:139](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:139)).

Faltam congelar:

- Inicialização estacionária, ruído de observação `σw²` e inovação latente `(1−φ²)σa²`.
- Normalização dos momentos, contagens mínimas de pares/triplas válidos e fallback para valores não finitos.
- Tratamento distinto de gaps observacionais e máscaras OOT.

**Remover um trânsito do ajuste não torna independentes os dados antes e depois dele.** O filtro deve propagar o estado sem incorporar a observação mascarada. Reiniciar a cada trecho OOT mudaria a covariância. O próprio gerador preserva dependência pelos intervalos temporais, inclusive gaps ([synthetic.py:121](C:/Projetos/refute/src/refute/packs/tess/synthetic.py:121)). Essa distinção corresponde ao tratamento de observações ausentes em [modelos de espaço de estados](https://www.statsmodels.org/stable/statespace.html).

Também distinguir **whitening/precisão** de multiplicação por `Σ`: “as mesmas recursões” não especifica ambos. Exigir comparação determinística com uma matriz densa pequena, incluindo máscaras interiores, para o ajuste e para `vᵀΣv` ([B1:145](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:145)).

O `H` OOT → todos, a ausência de `beta` adicional e a retirada da alegação de oracle estão corrigidos.

### 4. E4, família coerente, preservação e sensibilidade ainda abertas

**O operador local pode ser aplicado consistentemente aos dois lados.** A previsão média nos tempos efetivamente observados dentro do evento está correta ([B1:166](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:166)).

O preprocessing v4 continua exigindo seus refits por comb. Apenas o novo ajuste local dispensa um refit global adicional ([detrend_fast.py:318](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:318)).

Ainda é necessário:

- Congelar solução numericamente estável e fallback por condicionamento, além de singularidade.
- Usar o mesmo fallback geométrico para reais e pseudo-janelas.
- Não apresentar o erro branco da média das bandas como erro branco do novo operador quadrático, cuja previsão tem incerteza adicional.

A preservação de uma elevação confinada ao evento vale quando o preprocessing também a protege. Para elevações largas, **reportar absorção não faz automaticamente aparecer a perda de potência no bloco atual**: ele simula a alternativa diretamente como `frac_alt * sap_depth`, sem fator de resposta do operador ([battery_v51_diff.py:654](C:/Projetos/refute/src/refute/packs/tess/battery_v51_diff.py:654)).

Congelar o perfil temporal da alternativa e critérios de preservação. Se os perfis absorvidos pertencem à alternativa protegida, a sensibilidade precisa refletir essa resposta ou bloquear a permissão. “Reportado, não corrigido” é insuficiente ([B1:178](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:178)).

### 5. B1.2 e B1.3, screening útil, mas ainda incompleto

O screening D2 agora inclui regressões entre os 81 anteriormente mantidos. A regra de emenda prospectiva está adequada ([B1:209](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:209)).

Na recalibração:

- **Falta definir o contraste específico de E1.** Os bullets definem E2 e E3, mas não E1 ([B1:224](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:224)).
- **O critério da média não tem consequência FAIL.** Um viés demonstrado fora de ±0,15 não pode ficar automaticamente UNRESOLVED enquanto apenas dispersão e caudas excluem o estimador ([B1:244](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:244)).
- Congelar os métodos dos intervalos, indisponibilidades e composição final dos estimadores antes do forecast.

**Há uma impossibilidade residual no tamanho:** com 400 contrastes e intervalo exato bilateral de Clopper–Pearson, Bonferroni sobre 12, zero excedências dá limite superior **0,015316**, acima de 0,015. Portanto esse PASS permanece impossível. São necessários pelo menos 409 apenas para tornar possível o caso de zero excedências, sem ainda dimensionar poder.

**UNRESOLVED esperado não torna o screening inútil.** Ele pode detectar desvios grosseiros, desde que se declare que ausência de FAIL não demonstra calibração nem conservadorismo.

Para E4, a disjunção dos 16 hosts está correta, mas **janelas disjuntas e separação de dois dias não garantem independência**. Há preprocessing, estimativas de erro e variabilidade compartilhados. Definir inferência por clusters de host, dependência instrumental comum e a distribuição congelada de períodos/durações ([B1:232](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:232)). O transporte desses hosts gate-positive aos 84 gate-negative também não está demonstrado.

### 6. T2a, censo correto, conclusão sobre C incorreta

O censo resolve o problema amostral. Com `K` mantidos e `U` desconhecidos entre os 559:

- **YES:** `K ≥ 552`.
- **NO:** `K + U ≤ 551`.
- **UNRESOLVED:** nos demais casos.

Isso mantém os 56 acima de 20 perdidos em B e a certificação até 20 como condição ainda devida ([B1:301](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:301)).

**A linha 310 está errada:** B falhar mesmo no limite superior não impede C de resgatar T2a. Exemplo: 540 mantidos abaixo de 20, mais 12 acima, dão 552 em C. A impossibilidade deve vir do **limite superior de C**, ou de `B_upper + 56 < 551,5` quando esses 56 permanecem todos desconhecidos.

**O tratamento de overrun contradiz o controlador.** O desenho permite continuar após 1.700 s ([B1:298](C:/Projetos/refute/docs/plans/v0.5.3-stageB1-design.md:298)); o driver registra stop obrigatório ([driver.py:547](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:547)). Manter esse stop é a correção direta. O smoke de 20 minutos não garante o limite de todos os shards.

### 7. Custos e demais correções

A conta nominal é coerente: **33,54 CPU-h** para os 559, mais **22,40** acima de 20, total **55,94**, dentro da alocação 60. Porém `0,06` por injeção continua sendo estimativa, exigindo projeção medida por estrato e accounting integral.

Ativação por worker, comparadores desativados, regras D2/D4, fetch próprio, lock, repricing e T3b condicionado à qualificação estão substancialmente corrigidos. O limite de disco precisa reservar espaço **antes** da escrita para realmente ser máximo.

Pequena correção factual: são **25 INCONCLUSIVE e 1 FAIL** de `odd_even`, não 26 INCONCLUSIVE ([forecast-v4.json:90](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast-v4.json:90)).

**REFUTED, como desenho pronto para código: corrigir as condições numéricas, a recalibração, a sensibilidade de E4 e as regras de conclusão e overrun de T2a.**