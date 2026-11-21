**Rodada 2: os bloqueios anteriores foram substancialmente resolvidos, mas a nova semântica contém erros materiais. O conjunto ainda não está pronto para construir o pacote cego.**

Conferi HEAD `14f8ba7` e os arquivos pertinentes por leitura local. Não executei scripts, testes ou rede. Os 13 testes aprovados e a checagem sem padrões encontrados são informações fornecidas por você.

| Item | Veredito | Resultado |
|---|---|---|
| 1. Vazamento e disclosure | **SURVIVED** | Não encontrei vazamento de resultados antes da disclosure. O inventário agora é identificável, com uma correção terminológica abaixo. |
| 2. B1 | **SURVIVED** | Primária (a), princípio 3 e custo de (e) estão corretamente separados. Resta uma precisão de redação. |
| 3. B2 | **SURVIVED** | Primária (a), variante condicionada à derivação e limites dos controles estão adequados. |
| 4. B3 | **SURVIVED** | Como proposta: requisito mantido, modelo conjunto condicionado e B3.3 explicitamente reconhecida como mudança de regra. |
| 5. Propostas operacionais | **SURVIVED** | Compatíveis com as salvaguardas, como preparação. Custos adiados estão corretamente identificados como obrigações. |
| 6. Dependências e adversariais | **WEAKENED** | As principais lacunas foram corrigidas; faltam alguns efeitos explícitos na linha do estimador. |
| 7. Pacote e construtor | **WEAKENED** | O construtor **SURVIVED** à inspeção estática. A descrição das regras na semântica está **REFUTED** nos pontos abaixo. |

Os **bloqueios para construir o pacote definitivo** estão concentrados na semântica. Não proponho alterar fontes congelados.

1. **Corrigir severidades e separar severidade de papel.**  
   Em [v0.5.5-r2-code-semantics.md:43](/C:/Projetos/refute/docs/plans/v0.5.5-r2-code-semantics.md:43), `secondary_eclipse` está incorretamente classificado como FATAL.

   A bateria v4 substitui esse resultado por `check_secondary_two_sided`, cuja severidade é **WARNING**, inclusive quando inconclusivo. Evidência: [pipeline_v52.py:113](/C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:113) e [battery_v5.py:55](/C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:55).

   **Correção concreta:** mover `secondary_eclipse` para WARNING. Retirar `period_alias` e `eb_catalog` da classificação exclusivamente fatal e acrescentar uma linha:

   > “Outcome-dependent severity: `period_alias` emits FATAL for the variability-explanation rejection and WARNING near known systematic periods; `eb_catalog` emits FATAL or WARNING according to the match branch.”

   Isso corresponde a `battery.py:865–892` e `ebcatalog.py:309–353`. A severidade emitida pelo resultado, não apenas o nome do teste, determina sua participação na agregação.

   Substituir a linha **46** por:

   > “B1 concerns decisive results whose emitted severity is WARNING. Severity and role are independent; this table is not a list of decisive tests. Roles and expected tests come from the resolved claim.”

   Acrescentar `duration_excess` como WARNING, distinguindo seu papel diagnóstico no plano correspondente, e mencionar `holdout_by_year` na descrição dos diagnósticos. Hoje o documento promete apresentar testes e papéis, mas omite esses casos.

2. **Descrever corretamente o ajuste e o certificado do sinusoid.**  
   Em [v0.5.5-r2-code-semantics.md:69](/C:/Projetos/refute/docs/plans/v0.5.5-r2-code-semantics.md:69), substituir a descrição simplificada por:

   > “The fit is joint: per-sector offsets, all applicable tested harmonics and the selected extra frequencies, using out-of-transit cadences and inverse-variance weights. The residual-noise factor beta scales the coefficient covariance and the residual error.”

   Isso importa diretamente para B3.2: a dependência não é a de ajustes isolados. Ver `battery_v52.py:309–337`.

   Nas linhas **80–83**, acrescentar:

   > “The flag alternative has semi-amplitude D, with the minimum simulated probability over the declared phase grid. The small-residual marginal assumes a zero residual mean under the explaining model. The block probability is max(0, p + q − 1) only when coverage is valid and FAIL is allowed; otherwise it is zero.”

   O último condicionante está explícito em [battery_v52.py:371](/C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:371), mas ausente da semântica. Sua ausência pode induzir uma leitura incorreta dos novos PASS de B3.3.

   Na descrição da sensibilidade, linha **26**, acrescentar:

   > “A PASS also requires at least one applicable sub-check.”

   E, entre sensibilidade e agregação, registrar:

   > “Tests deferred to a later stage become INCONCLUSIVE with zero coverage and retain their severity before role-based aggregation.”

As **ressalvas abaixo não invalidam o mecanismo do construtor**, mas devem ser corrigidas ou registradas.

3. **B1(a): preservar explicitamente a precedência de REFUTED.**  
   Em [v0.5.5-r2-arguments.md:70](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:70), “no verdict short of INCONCLUSIVE” é absoluto demais: um fatal FAIL pode produzir REFUTED mesmo com outro ataque inconclusivo.

   Substituir por:

   > “No SURVIVED or WEAKENED verdict is issued while an expected decisive attack is undecided; gate and fatal-FAIL precedence remain unchanged.”

   A sequência correta já está descrita na seção 2. Esta é uma correção de consistência, sem reabrir a escolha conservadora de (a).

4. **Completar a linha de dependências do estimador.**  
   Em [v0.5.5-r2-arguments.md:258](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:258), acrescentar:

   > “D4 through changed INCONCLUSIVE classifications; T2b through additional retained transformed detections; T2c where original cases become SURVIVED.”

   Incluir esses mesmos alvos nas checagens da linha. C7 já exige T2b e a avaliação conjunta das famílias pertinentes, portanto não há autorização implícita para omiti-los; falta tornar a dependência explícita.

   Na linha **259**, nomear também **T3a** quando o eventual teste de D1 depender de catálogo e puder afetar planetas reais.

5. **B3.2: especificação não basta para sustentar o modelo.**  
   Em [v0.5.5-r2-arguments.md:199](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:199), tornar a condição mais precisa:

   > “The simulated joint probability is proposed only with a common generative model specified, supported by a derivation and accepted in the independent review; otherwise Fréchet remains primary.”

   Na linha **201**, substituir “answers a different question” por:

   > “Fréchet supplies a conservative certificate for the same joint probability; a supported dependence model may permit a tighter certificate.”

   Isso evita transformar uma escolha conservadora de certificado em erro conceitual.

6. **Corrigir a população descrita na disclosure.**  
   Em [v0.5.5-r2-arguments.md:298](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:298), substituir:

   > “on those planets”

   por:

   > “on those eclipsing-binary samples”

   A ponte usa EB1/EB2. Os números de diferenças de elegibilidade e veredito conferem com o registro. O erro fica fora do pacote, mas merece correção pela distinção entre populações.

Quanto ao **construtor**, confirmei estaticamente:

- allowlist com os **12 arquivos de conteúdo**, incluindo semântica;
- argumentos cortados antes da disclosure;
- manifesto escrito antes dos arquivos do pacote e antes da revisão;
- recusa de construção sobre pacote ou manifesto existente;
- comparação da cópia entregue do manifesto;
- inclusão de manifestos aninhados no inventário verificado.

Não encontrei nos fontes adicionados comentários com resultados empíricos das metas. Números de parâmetros, alternativas e procedimentos fazem parte das regras congeladas. A checagem por padrões continua corretamente descrita como auxiliar à leitura contextual.

**Registro de divergência:** a divergência substantiva sobre B1 foi resolvida pela primária (a). B2 mantém (a), e B3.2 conserva Fréchet sem modelo sustentado. As condições futuras não equivalem à adoção dessas variantes.

**O construtor está pronto sob inspeção estática; o documento e a semântica ainda não estão prontos para a construção única do pacote cego, por causa dos bloqueios 1 e 2.**