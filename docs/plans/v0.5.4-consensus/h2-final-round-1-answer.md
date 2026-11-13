**1. Passo 4 e commit `ddd8dc7`: conferem.**

- Confirmei **77 shards únicos, distribuídos em 62 + 1 + 14**, com hashes válidos, 754 registros únicos e nenhum erro. O complemento consumiu 0,108763 CPU-h, dentro do teto de 1,0; as três partes somam 1,5179 CPU-h ([ledger.json:105](/C:/Projetos/refute/docs/validation/v0.5.4/ledger.json:105)).
- A checagem de 5 % concorda nos **20 casos**. O resultado final registra `errors: []` e `stops: []`. Os dois stops anteriores continuam documentados no ledger; “no stop” na mensagem corresponde à conclusão final ([registro:205](/C:/Projetos/refute/docs/validation/v0.5.4/h2-step4-b0-errors.json:205)).
- Recalculei as expectativas em α = 0,0027: **3 %: 19,1/21,0; 2 %: 16,8/16,4; 1 %: 13,8/13,7**, contra tolerância 10. Os resultados conferem: 2 e 3 % sem margem naquele cenário; 1 % `INCONCLUSIVE`, com medianas 0,081/0,100.
- Mensagem e registro limitam a conclusão a **nenhuma das três precisões demonstrou ser suficiente**, sob as hipóteses de B0. Não apresentam draft D1 nem método validado ([registro:209](/C:/Projetos/refute/docs/validation/v0.5.4/h2-step4-b0-errors.json:209)).

**2. ROADMAP: cumpre exatamente o item 4.**

- Encerra v0.5.4, pausa a linha v0.5 pela decisão de 13/11 e inclui o link do registro de pausa ([ROADMAP.md:43](/C:/Projetos/refute/ROADMAP.md:43), [ROADMAP.md:793](/C:/Projetos/refute/ROADMAP.md:793)).
- **Nenhuma caixa foi alterada.** A regra de avanço e todo o texto das demais fases permanecem idênticos.
- Os resumos são fiéis: I1 = 103/169 e I4 = `route` ([primeira metade:18](/C:/Projetos/refute/docs/validation/v0.5.4/h1-stop-report.md:18)); resultados da segunda metade ([relatório:20](/C:/Projetos/refute/docs/validation/v0.5.4/h2-stop-report.md:20)); conclusão posterior do passo 4 ([pause-record.md:52](/C:/Projetos/refute/docs/validation/v0.5.4/pause-record.md:52)); déficit T3b = 9 ([t3b-count.json:38](/C:/Projetos/refute/docs/validation/v0.5.4/t3b-count.json:38)). O relatório anterior à conclusão mantém corretamente seu caráter histórico.

SURVIVED