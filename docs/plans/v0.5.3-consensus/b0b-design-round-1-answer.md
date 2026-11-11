São necessárias **duas correções no orçamento** antes de considerar o conjunto pronto.

1. **[P1] O ledger não suporta B0b e B1 simultâneos.** `budgeted.execute` conserva uma cópia do ledger e depois a grava inteira ([budgeted.py:231](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:231), [budgeted.py:244](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:244)). Assim, pode apagar transferências, charges ou consumo registrados por outro processo. A gravação atômica em [ledger_b.py:69](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:69) não evita essa perda. **Correção:** serializar todos os escritores durante a execução inteira, ou implementar transações com reservas das execuções ativas. Um lock apenas no `replace` não basta.

2. **[P2] Os 6 CPU-h não são acumulados entre tentativas.** [ledger_b.py:167](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:167) limita cada tentativa a `1,5 × allocation / 1,10`, sem descontar tentativas anteriores desse teto. Uma mudança de fingerprint arquiva o consumo anterior ([budgeted.py:238](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:238)): após 2 CPU-h, outra tentativa ainda pode receber 6, totalizando 8. **Correção:** descontar tentativas anteriores do teto acumulado de B0b e recusar automaticamente uma identidade nova sem a aprovação exigida. A retomada com fingerprint idêntico permanece conservadora.

Os demais pontos passaram:

- **Critério:** [d1_infeasibility.py:146](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:146) exige as duas condições nos **dois níveis, na mesma família**, e depois aceita EB1 **ou** EB2. É fiel ao procedimento registrado. Exigir ambos protege contra concluir inviabilidade apenas no nível mais restritivo. A condição adicional sobre a esperança é conservadora. Não encontrei ajuste numérico aos resultados de B0; a origem histórica da escolha depende da decisão documentada. A divulgação está explícita em [design:73](C:/Projetos/refute/docs/plans/v0.5.3-stageB0b-design.md:73).

- **Mesma medição e seeds:** `d1_bound.py` está inalterado frente a `b00a78d`. O wrapper e a atribuição no nível do módulo ([script:52](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:52)) alcançam os workers sob Windows `spawn`. Verifiquei 800 seeds distintos, sem interseção com B0 e seus smokes. Não há seeds de confirmação definidos para comparar; isso está explicado em [design:35](C:/Projetos/refute/docs/plans/v0.5.3-stageB0b-design.md:35).

- **Desfechos:** a precedência de (D), depois (I), senão (N), está correta ([script:160](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:160)). Rascunho, revisão, parada e autoridade do mantenedor estão preservados em [design:81](C:/Projetos/refute/docs/plans/v0.5.3-stageB0b-design.md:81).

- **Demais limites:** a transferência preserva a alocação total. Para a primeira tentativa, o teto nominal é **5,4545 CPU-h**, chegando a 6 com os 10%. Restam **0,08207 CPU-h** para charges, acima da reserva de resumo de 0,03. O prefixo `b0-b0b-…` entra nos dois limites de tokens ([ledger_b.py:202](C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:202)).

- **Resumo e fingerprint:** cobertura adequada; remoção dos campos A/B/C correta ([script:182](C:/Projetos/refute/docs/validation/v0.5.3/stageB/d1_infeasibility.py:182)). O smoke terminou `OK`. Fiz somente leituras e checks leves em memória.

**WEAKENED, corrigir a concorrência do ledger e o teto acumulado entre tentativas antes de commit e execução.**