## Parecer

**A captura e a reprodução de E4 sobrevivem à leitura. O ajuste estatístico e a interpretação dos limites precisam de correções.** HEAD confirmado em `50810db`. Não executei os scripts, não usei rede nem abri os shards proibidos.

### 1. Captura e reprodução

**Correta na estrutura.** O wrapper é instalado antes de `t2a_one` ativar a versão 5, chama o original e recompõe `g_bkg` com E4 e `seed + 3`, e `g_sap` com o operador-base e `seed + 4`. Isso acompanha o despacho da bateria. [step6_i2.py:68](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:68), [battery_b1.py:644](C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:644).

**Ressalva:** a reprodução histórica compara candidato, veredicto, testes, setores e decisões com B1. Já `background_rise_err` é comparado com o resultado da própria reprodução atual. Isso verifica consistência da captura, não igualdade numérica com o antigo shard I1. Também falta uma comparação explícita da potência original, que verificaria conjuntamente `g_sap` e sua incerteza. [i1_diagnose.py:314](C:/Projetos/refute/docs/validation/v0.5.4/i1_diagnose.py:314), [step6_i2.py:313](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:313).

### 2. Série e janelas de E4

**Fiéis.** Filtros finitos, ordenação estável, máscara e `AdditiveDetrender.flat()` reproduzem o processamento interno. Os centros são exatamente `t0 + epoch × period`. Cobertura, extremidade direita exclusiva, pesos quadráticos e fallback de `e4_weights` acompanham `quadratic_box`. [step6_i2.py:105](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:105), [battery_b1.py:489](C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:489), [events.py:108](C:/Projetos/refute/src/refute/packs/tess/events.py:108).

Convém **recusar qualquer janela reconstruída ausente**, em vez de descartá-la silenciosamente, preservando exatamente os eventos de `g_bkg`. [step6_i2.py:256](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:256).

### 3. Família, ajuste e covariância

Há três correções materiais:

- **Agrupamento:** largura `duration/3`, exclusão das janelas completas e mínimo de duas cadências estão implementados. O termo branco `σ_w²/n` também está correto, pois o código parametriza **σ_w por cadência**. O documento usa outra parametrização, `σ_w,bin`, e precisa ser alinhado. [step6_i2.py:150](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:150), [desenho:57](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:57).
- **Verossimilhança:** o Kalman é exato para um OU observado nos tempos médios, mas as observações são **médias de cadências**. Sua covariância correta exige agregar o kernel, `K_bin = A K_cad Aᵀ`. Reutilizar diretamente os parâmetros OU nas cadências é aproximação, especialmente quando `τ` pode chegar à largura do bin. Além disso, subtrair a média aritmética por setor não equivale a ajustar sua constante por máxima verossimilhança com covariância irregular. [step6_i2.py:168](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:168), [step6_i2.py:193](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:193).
- **Adequação:** `df = lags − 3` está implementado, mas os produtos de autocorrelação atravessam setores e lacunas deixadas pelas exclusões. Nove posições não representam necessariamente três durações. É preciso preservar segmentos e distâncias temporais, tratar amostras insuficientes e denominador nulo, e apresentar esse p como diagnóstico heurístico. [step6_i2.py:212](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:212).

Os starts e limites numéricos estão fixos no script, mas o documento deve explicitar também os limites de `σ_w` e `σ_r`. [step6_i2.py:203](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:203).

### 4. Limites e potência

**As fórmulas são válidas condicionalmente ao modelo escolhido:** `σ_E4op` otimiza a combinação dos contrastes E4; `σ_full` é o erro GLS do degrau comum com nuisances quadráticas. Os testes de definitude e condicionamento são pertinentes. `background_block`, parâmetros e semente `seed + 5` são reutilizados corretamente. [step6_i2.py:237](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:237), [step6_i2.py:299](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:299).

**Faltam condições para chamá-los de limites da mesma amplitude:**

- Demonstrar resposta unitária e remoção das nuisances, incluindo a transformação interna.
- Tratar o fallback constante de E4, pois o GLS sempre impõe quadráticas.
- Recusar sobreposição ou contabilizar o ruído branco compartilhado entre janelas. Atualmente ele só entra na diagonal dos eventos.
- Verificar explicitamente ambas as sigmas e as probabilidades finais.

[step6_i2.py:264](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:264).

### 5. Regras, contagem e segurança

**Os limiares estão definidos**, e a recuperação conjunta exige todos os bloqueadores serem `systematics`. Conferi o hash do detalhe do passo 1: entre as 102, apenas **56** satisfazem essa condição. Mesmo recuperando todas, restariam **172 das 228 perdas**, com margens máximas de **−165 em B** e **−123 em C**. Isso descreve esta intervenção isolada. [step6_i2.py:466](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:466), [h2-step1-floor.json:71](C:/Projetos/refute/docs/validation/v0.5.4/h2-step1-floor.json:71).

Falta registrar por injeção os outros bloqueadores e sua classificação final. A cobrança do resumo usa nome único, ocorre em `finally` e precede a escrita, **ordem correta**. [step6_i2.py:404](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:404).

**O stop científico só acontece no resumo.** Erros e divergências viram bytes normais para o driver, permitindo continuar despachando trabalho. Isso precisa interromper novos despachos. Caps, afinidade, prioridade e prazo estão conectados ao driver. [step6_i2.py:350](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:350), [step6_i2.py:380](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:380).

### 6. Excesso de alcance

“Qualquer estimador” e “informação limitada” excedem um GLS com covariância estimada, degrau comum e nuisances escolhidas. Restrinja as conclusões a essa classe, sem propagar incerteza da covariância e sem conclusão sobre 615 injeções ou draft.

O piloto foi divulgado corretamente, mas contradiz “antes de qualquer número”. Seus 191 CPU-s terminaram antes dos limites densos, portanto **não medem o custo do caminho válido**. [desenho:8](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:8), [step6_i2.py:335](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:335).

**WEAKENED (corrigir ajuste e covariância agrupada, adequação temporal, equivalência da amplitude, sobreposições e stops; restringir as conclusões ao modelo).**