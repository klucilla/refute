**As duas correções estão resolvidas. Resta uma fraqueza no histórico de tentativas.**

### Confirmado

- **Manifesto vinculado ao freeze:** `inputs.json` é comparado byte a byte e recebe SHA-256 antes da leitura de S_max. A verificação offline confirmou `{63,41,11}` e 22 restantes. [t3b_count.py:79](/C:/Projetos/refute/docs/validation/v0.5.4/t3b_count.py:79), [t3b_count.py:160](/C:/Projetos/refute/docs/validation/v0.5.4/t3b_count.py:160).
- **Consultas parciais preservadas:** cada busca registra hash ou erro, inclusive quando uma busca posterior falha. Os wrappers não se acumulam entre estrelas e são restaurados em `finally`. [t3b_count.py:128](/C:/Projetos/refute/docs/validation/v0.5.4/t3b_count.py:128), [t3b_count.py:200](/C:/Projetos/refute/docs/validation/v0.5.4/t3b_count.py:200).
- **Simulações em memória:** sucesso, recuperação após falha e cinco tentativas esgotadas preservaram todas as buscas. As paradas não produziram agregado.

### Fraqueza restante e opção conservadora

**Uma falha permanente após uma transitória perde o histórico em `attempts`.** Reproduzi: timeout na primeira tentativa, `ValueError` na segunda. As seis buscas ficaram registradas, com os dois erros, mas a parada gravou `attempts: []`. Isso ocorre porque a exceção permanente não carrega `.attempts`; o fallback vazio mascara a tentativa anterior. [t3b_count.py:179](/C:/Projetos/refute/docs/validation/v0.5.4/t3b_count.py:179), [walk.py:109](/C:/Projetos/refute/src/refute/selection/walk.py:109).

**Opção conservadora:** acumular explicitamente cada tentativa de triagem no callback executado por `with_retries`, com número, UTC e resultado/erro. Persistir esse histórico em qualquer saída, mantendo a parada atual e a ausência de agregado em caso de falha.

Continua sendo contagem de metadados, sem seleção para execução. A dúvida documental sobre a disposição ExoFOP permanece não confirmada.

WEAKENED (preservar o histórico de tentativas quando uma falha permanente sucede uma transitória).