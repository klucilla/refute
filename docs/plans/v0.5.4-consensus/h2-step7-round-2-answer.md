## 1. Passo 7, correções da rodada 1

**As correções principais foram aplicadas:** Fréchet, banda de incerteza, cruzamento com os status registrados, dois desfechos, fingerprint e caps da fase. A leitura da T2a continua honesta.

**Concordo com sua interpretação da parada.** Minha formulação anterior foi ampla demais: corrigir achados nesta revisão prospectiva não exige uma parada operacional adicional. Defeitos encontrados durante a execução ou nos registros, divergências e caps continuam sujeitos à parada.

Restam dois ajustes:

- **Validar também o Gram do resíduo.** `p_small` ainda vem de `sa.sinusoid_bound`, que inverte seu próprio Gram sem verificar condicionamento ou positividade. `_invalid_matrix` valida apenas o Gram do flag e suas covariâncias. Um resíduo numericamente inválido pode produzir uma probabilidade aparentemente válida. [step7_sinusoid.py:89](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:89), [d2_bounds.py:147](C:/Projetos/refute/docs/validation/v0.5.3/stageA/d2_bounds.py:147).
- **Coerência das paradas:** `stops` pode acompanhar um resultado de “margem condicional”. Nesse caso, marcar o desfecho como inválido/`INCONCLUSIVE`. A promessa de escrever *todas* as paradas nesse campo também não cobre população incorreta, recusas dos leitores ou parada do driver, que encerram antes da escrita. Distinguir esses registros no desenho. [step7_sinusoid.py:248](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:248), [desenho:108](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:108).

O “piso” permanece **condicionado aos status registrados**, não um piso de perdas irrecuperáveis: retirar apenas os warning FAIL já registrados não exclui futuros warning FAIL entre os demais casos. [Desenho:67](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:67).

**Item 1: WEAKENED, validar o Gram residual e harmonizar desfechos e registros de parada.**

## 2. Passo 5, primeira revisão

**A base algébrica está correta:** `precision_apply` implementa o mesmo Σ⁻¹ de `mahalanobis2`; conferi com matrizes pequenas e solução densa, sem gerar planetas. V0 reproduz as colunas de stage A. A expressão de `r` está correta como resposta direcional do ajuste GLS da caixa. [step5_gap.py:54](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:54), [step5_gap.py:103](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:103).

**Correções necessárias antes do congelamento:**

- **Tendência multiplicativa:** as derivadas precisam incluir o modelo de trânsito, `(1 − D·shape)·∂trend/∂θ`. Hoje são apenas derivadas da senoide. Assim, V_trend/V_all não são o Fisher do gerador anunciado. Alternativamente, declarar explicitamente outro modelo aditivo. [step5_gap.py:140](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:140), [gerador:374](C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:374).
- **Amplitude comum ainda falta:** divide-se `σ_box` por `r`, mas compara-se esse valor com o erro registrado de E2 sem demonstrar sua resposta equivalente. Corrigir também a resposta de E2, incluindo eventual vazamento da profundidade comum para o contraste, e usar a mesma amplitude nas potências. Guardar `r`, σ original e σ convertido. A ressalva textual de equivalência não resolve essa comparação. [step5_gap.py:105](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:105), [step5_gap.py:281](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:281).
- **Variantes são aproximações de E2:** quadrática por setor não reproduz o detrending local; V_all omite as quadráticas de V_trend. As janelas usam todas as cadências interiores, enquanto E2 mede médias com bandas e lacuna de baseline. Esses modelos podem fornecer diagnósticos, mas coincidência de medianas não demonstra a causa do gap. Completar as combinações ou restringir a conclusão a “compatível em mediana”. [step5_gap.py:168](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:168), [events.py:100](C:/Projetos/refute/src/refute/packs/tess/events.py:100).
- **UNK e denominadores:** ausência do erro de E2 não incrementa `unknown`; uma variante pode vencer com pouquíssimos pares disponíveis. Congelar cobertura mínima, validar referências finitas/positivas e informar os denominadores das razões, shares e cruzamentos. [step5_gap.py:275](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:275).
- **Paradas:** uma divergência válida de V0 é tolerada silenciosamente; reconciliar isso com a regra de reprodução. A monotonicidade por inclusão de nuisances também não justifica automaticamente declarar defeito nas variantes de caixa sem demonstrar equivalência. [step5_gap.py:269](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:269), [step5_gap.py:300](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:300).

Parte, transferência, caps, reserva de tokens e driver estão corretamente conectados. O piloto sustenta uma estimativa de custo. **19h30 é corte de novos despachos**, com conclusão dos shards em voo, não garantia de drenagem completa nesse instante. [step5_gap.py:212](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:212), [i4_rest.py:22](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest.py:22).

**Item 2: WEAKENED, corrigir tendência, equivalência de amplitude, alcance das variantes e tratamento de UNK/paradas.**