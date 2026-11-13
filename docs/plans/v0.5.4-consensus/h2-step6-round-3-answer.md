## Resultado da última rodada

**As correções centrais sobreviveram à leitura estática. Restam duas proteções pontuais para o congelamento.** HEAD `d5cfbee`, sem executar scripts, usar rede ou abrir os shards proibidos.

### Correções confirmadas

- **Constantes perfiladas:** a linearidade das inovações justifica a fórmula de `mu_s`; a função objetivo mantém o determinante da covariância e usa os resíduos perfilados. Agora corresponde à máxima verossimilhança anunciada, sem prior finita artificial. [step6_i2.py:178](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:178).
- **Transformação:** a diferença sobre o background real preserva NaNs, exige alinhamento e testa a resposta individual, combinada e GLS. O fallback constante e a verificação finita de `beta[0]` estão corretos. [step6_i2.py:351](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:351), [step6_i2.py:450](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:450).
- **Adequação:** contagens próprias por lag, mínimo de 30 pares e registro dessas contagens corrigem a aprovação sem cobertura temporal. Continua sendo um diagnóstico heurístico, com a aproximação OU explicitamente condicionada a `τ ≥ 3 bins`. [step6_i2.py:218](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:218).
- **Stop:** para as exceções capturadas, o driver encerra o despacho e fecha o lote; o novo handler recupera o consumo e grava stops vinculantes no ledger e no diretório. A lacuna operacional anterior foi corrigida. [step6_i2.py:535](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:535).
- **Resumo e escopo:** mantêm a contagem conjunta, as margens, a cobrança antes da escrita e as restrições ao modelo ajustado, sem conclusão sobre 615 ou draft. Os três pilotos e o custo ainda não medido dos limites estão divulgados. [step6_i2.py:560](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:560), [desenho:137](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:137).

## Proteções conservadoras restantes

### 1. Sobreposição e nuisances vizinhas

Cada contraste é verificado contra **sua própria baseline**, mas o GLS inclui todas as baselines. Havendo sobreposição, anular a própria não garante anular as vizinhas. A covariância branca compartilhada está correta, mas não resolve esse possível viés. [step6_i2.py:375](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:375).

**Opção mais conservadora:** marcar a injeção inteira como **UNK se quaisquer duas janelas compartilharem cadências**, preservando todos os eventos E4. Isso dispensa ampliar agora a prova de equivalência. Não afirmo que essa situação ocorra nas 102.

### 2. Identidade do shard em erros inesperados

Os erros explícitos incluem `key/slot`, mas uma exceção de NumPy, SciPy ou leitura pode chegar ao handler apenas como uma mensagem genérica. `why = str(exc)` não garante a identidade prometida pelo desenho. [step6_i2.py:497](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:497), [step6_i2.py:546](C:/Projetos/refute/docs/validation/v0.5.4/step6_i2.py:546).

**Opção mais conservadora:** contextualizar qualquer `Exception` dentro de `shard` com `key/slot` e tipo da exceção, relançando com encadeamento. Manter o handler persistente atual.

## Redação final

Alinhar três detalhes: o cabeçalho ainda excepciona apenas **um** status de piloto; a tolerância das nuisances usa a **soma dos valores absolutos** dos pesos; `g_sap` é conferido pela potência conjunta, não por `background_rise_err`. [desenho:8](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:8), [desenho:36](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:36), [desenho:86](C:/Projetos/refute/docs/plans/v0.5.4-h2-step6-i2-staged.md:86).

**WEAKENED (aplicar UNK às sobreposições, identificar o shard em toda exceção e alinhar os três detalhes de redação).**