## Resultado da rodada 2

**As correções avançaram, mas ainda há quatro pendências materiais.** Revisão estática no HEAD atual `d5cfbee`, sem executar scripts, usar rede ou abrir os shards proibidos.

### Correções confirmadas

- **Captura e potência:** funções, sementes e ativação continuam coerentes. A recomposição da potência no erro registrado acrescenta a verificação conjunta de `g_sap`. [step6_i2.py:406](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:406).
- **Janelas e fallback:** nenhuma janela ausente é descartada silenciosamente; o fallback usa nuisance constante; a covariância branca das cadências compartilhadas entra corretamente em `V`. [step6_i2.py:333](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:333).
- **Precisão OU:** a álgebra de `precision_apply` está correta para tempos estritamente crescentes por setor: resolve `(σ_w²Q + σ_r²I)⁻¹ QX`, com `Q = K⁻¹`. As duas sigmas e potências recebem as verificações anunciadas. [step6_i2.py:299](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:299).
- **Resumo:** lista por injeção, bloqueadores conjuntos, margens, escopo e cobrança antes da escrita estão presentes. [step6_i2.py:513](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:513).

## Pendências materiais

### 1. O Kalman ainda não é exatamente difuso

`big = 1e6 × (...)` implementa uma **prior finita**, dependente dos dados e dos parâmetros. Omitir a primeira contribuição da verossimilhança não transforma essa inicialização em difusa exata. A atualização posterior ainda depende de `big`, inclusive do nível da série, que contém o deslocamento `1 + residual`. [step6_i2.py:178](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:178).

**Correção:** usar a atualização difusa analítica ou perfilar a constante por GLS. Também distinguir a verossimilhança difusa/integrada da máxima verossimilhança com constante perfilada, pois são critérios diferentes para estimar a covariância.

### 2. O degrau isolado não verifica suficientemente a transformação real

`e4_series(unit_step)` refaz o detrender sobre outra série. Ele pode mudar as escolhas adaptativas e, sobretudo, **reintroduz cadências cujo background original era não finito**. Depois, o código usa apenas `.flux`, sem conferir alinhamento de tempos e setores com a série real. [step6_i2.py:425](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:425).

O detrender tem clipping dependente dos valores e fallbacks por mediana. Portanto, testar `T(s)` não estabelece, sozinho, `T(b+s) − T(b)`. [detrend_fast.py:128](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:128), [detrend_fast.py:206](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:206).

**Correção:** verificar essa diferença no background real, preservando NaNs e alinhamento, ou demonstrar a equivalência com as escolhas congeladas. Conferir também:

- A resposta da **combinação ótima** E4op, pois pesos negativos podem amplificar desvios individuais de até 1%.
- A anulação das nuisances por seus contrastes, especialmente se houver sobreposição.
- `math.isfinite(beta[0])`, pois a comparação atual não rejeita NaN.

[step6_i2.py:338](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:338).

### 3. A adequação pode passar sem pares na escala exigida

Os índices corrigem a compressão das lacunas e os cruzamentos entre setores. Porém, o código não exige quantidade mínima de pares por lag e mantém o denominador `nz − k`, independentemente dos pares disponíveis. **Com 50 inovações suficientemente espaçadas, nenhum par pode existir nos lags testados: Q = 0 e p = 1.** [step6_i2.py:208](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:208).

**Correção:** congelar cobertura mínima de pares por lag, registrar essas contagens e retornar UNK quando insuficientes; adequar a normalização ao tratamento das lacunas. O rótulo “heurístico” deve permanecer. O veto `τ < 3 bins` está implementado, mas continua sendo uma regra de aceitação da aproximação.

### 4. Lançar erro interrompe o despacho, mas não produz um stop persistente

Quando `future.result()` lança, o driver sai do despacho, aguarda os trabalhos já enviados sob o watchdog e fecha a cobrança do lote. **Essa parte está correta.**

Depois, porém, ele relança a exceção sem `_record_stop`. Isso também pula a atualização final de `spent_hours` e `_ended` em `budgeted_v3`. Assim, o processo termina, mas o stop científico não fica vinculante para uma retomada, e o ledger pode permanecer desatualizado. [driver.py:519](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:519), [budgeted_v3.py:139](C:/Projetos/refute/docs/validation/v0.5.4/budgeted_v3.py:139).

**Correção:** persistir motivo, identidade do shard, consumo final e stop vinculante antes de propagar a falha.

## Ajustes no desenho

Ainda restam “any estimator” na pergunta, starts descritos em unidades diferentes das usadas pelo código e “small against the replay” sem medição do caminho dos limites. Alinhar esses trechos ao escopo restrito e ao custo ainda não medido. [desenho:15](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:15), [desenho:53](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:53), [desenho:126](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:126).

**WEAKENED (corrigir inicialização difusa, teste da transformação, cobertura dos pares e persistência do stop e da cobrança).**