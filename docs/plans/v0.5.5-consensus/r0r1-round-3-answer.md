**Não identifiquei bloqueio remanescente ao congelamento dos desenhos R0/R1 no escopo diagnóstico declarado.** Isso não valida o método nem libera a execução de R1.

Fiz somente leitura local. O [JUnit informado](/C:/Projetos/refute/.cache/v055/junit-v055c.xml:1) registra **25 testes, zero falhas e zero erros**. Não executei os testes nem certifiquei sua correspondência com cada byte atualmente presente.

**Vereditos finais**

| Item | Veredito | Fundamentação |
|---|---|---|
| **1a** | **SURVIVED** | Preços por saída, limites de Wilson e condições integrais de D2/D4 preservados. Fatal permanece cenário, sem margem disponível presumida. |
| **1b** | **SURVIVED** | Convenções adicionais estão declaradas. Caixa e estrela conhecida agora são referências sem ordenação garantida em torno do prior. |
| **1c** | **SURVIVED** | Padrão de prova e aprovação não delegada preservados. Nenhuma checagem R1 substitui essa demonstração. |
| **1d** | **SURVIVED** | Salvaguardas prospectivas completas, sem decidir questões reservadas a R2. |
| **1e** | **SURVIVED** | Nove mudanças reproduzidas. Identidade completa, bloqueio único, teto cumulativo e contagem persistente por inícios corrigem os bloqueios anteriores. |
| **2** | **SURVIVED** | Restauração por `finally`, isolamento entre processos e fluxo aleatório separado corretos sob uso serial. Grandezas derivadas das durações estão corretamente reconhecidas. |
| **3-D2F** | **SURVIVED** | Como diagnóstico aproximado: contagem superior, limiar `14/178`, futilidade pela rota e ausência de `closed` conferem. Covariância cruzada e simulação permanecem coerentes com o modelo declarado. |
| **3-D1P** | **SURVIVED** | Como leitura nominal para G1: três ajustes, `truth` completa, preços e limiares conferem. Calibração planetária continua explicitamente não demonstrada. |
| **3-T2aE** | **SURVIVED** | Referência histórica de I1, tolerâncias, paradas, registros dos placebos e piso branco corrigidos. Limiares `0,8V`, `0,4V` e `UNK>20` preservados. |
| **3-T3b** | **SURVIVED** | Adiamento conservador correto. Não equivale a uma constatação atual de indisponibilidade. |
| **3-comum** | **SURVIVED** | Digest inclui a identidade completa e é comparado entre etapas. Execução protegida por bloqueio único; uma retomada contada por inícios; dez workers em qualquer horário. Alocações e tetos conferem. |
| **4** | **SURVIVED** | Correções históricas preservadas como novo registro. ROADMAP mantém somente o ponteiro no trecho antigo e não altera a regra de avanço. |
| **pinned_hash** | **SURVIVED** | Uso restrito à localização histórica, manifesto normalizado conferido e somente dois locks admitidos. Replay ocorre fora da substituição, no ambiente atual, com versões registradas por caso. |

**Bloqueios ao congelamento**

**Nenhum identificado nesta revisão estática**, consideradas as interpretações conservadoras abaixo. Os desenhos ainda precisam do commit de congelamento; a execução continua condicionada à revisão independente e à liberação do mantenedor.

**Ressalvas finais a registrar**

Estas limitações permanecem obrigatórias, independentemente dos resultados futuros:

- **D1-P:** `route` e `closed` são leituras do substituto de oráculo. Não demonstram calibração planetária, viabilidade de uma bateria ou inviabilidade de D1.
- **D2-F:** não produz `closed`. As contagens não são pisos demonstrados de perdas inevitáveis. `RULE_3` usa uma aproximação em unidades normalizadas, sem a tendência multiplicativa física.
- **T2a-E:** a inflação χ² é heurística, sem cobertura de 95% demonstrada. O piso branco restringe-se aos contrastes E4 e ao modelo declarado.
- **`pinned_hash`:** autentica a localização dos registros antigos. A reprodução dos números verifica somente as grandezas e tolerâncias comparadas, não equivalência integral dos ambientes.
- **Operação:** máximo de dez workers em qualquer horário; um início adicional por parte é a única retomada pré-aprovada. Tetos de parada: **64 CPU-h, 2,4 M tokens, 7,2 dias-agente e 4 GB**.

**Ajustes documentais não bloqueantes**

1. [r1_common.py:129](/C:/Projetos/refute/docs/validation/v0.5.5/r1_common.py:129): esclarecer o uso da função pela D1-P, alinhando o docstring ao desenho:  
   **Texto:** “For D1-P, this formula supplies a nominal surrogate score; planet-side calibration is not established.”

2. [desenhos:152](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:152) e [d2f_floor.py:17](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:17): substituir “under the true trapezoid” pela descrição já presente nas limitações:  
   **Texto:** “under the normalized transit approximation, omitting the generator’s multiplicative stellar trend.”

3. [desenhos:326](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:326): distinguir onde cada informação é gravada. Os dois hashes ficam no resumo; as versões ficam nos registros por caso.  
   **Texto:** “Each summary holds both code hashes; each case records the interpreter and numerical-package versions used by its replay.”

**Registro final da rodada 3:** ficam aceitas as opções conservadoras já incorporadas: referências estelares sem ordenação, D1-P nominal, D2-F sem fechamento, placebo heurístico, hash histórico apenas para busca e máximo de dez workers. Não permaneceu divergência impeditiva. `method_status: not_validated` e o veredito histórico `WEAKENED` da v0.5 permanecem inalterados.