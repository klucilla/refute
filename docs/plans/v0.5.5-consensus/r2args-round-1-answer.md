**Rodada 1: o documento ainda não está pronto para o pacote cego.** Há vazamentos indiretos, justificativas que excedem o que o código sustenta e lacunas no conteúdo e na verificação do pacote.

Base: HEAD `6d9bae3`. Fiz inspeção local, sem editar arquivos, executar scripts ou testes, usar rede ou acessar o diretório proibido.

| Item | Veredito | Conclusão |
|---|---|---|
| 1. Vazamento e disclosure | **REFUTED** | Há premissas retrospectivas antes da disclosure. A lista do conhecimento prévio não é suficientemente identificável. |
| 2. B1 | **REFUTED** | A demonstração de que (e) preserva integralmente a exigência de evidência não procede. A opção continua admissível como proposta de mudança. |
| 3. B2 | **WEAKENED** | A condicional e o fallback são adequados; a interpretação física e a proteção contra contaminação parcial estão sobreafirmadas. |
| 4. B3 | **WEAKENED** | B3.1 sobrevive. B3.2 exige uma hipótese conjunta explícita. B3.3 muda a regra e precisa declarar isso diretamente. |
| 5. Propostas operacionais | **WEAKENED** | C2(a) está correto. Faltam precisão em publicação, confirmação, custos e tratamento da eventual rota de D1. |
| 6. Dependências e adversariais | **REFUTED** | Faltam efeitos e há checagens apresentadas como capazes de testar mecanismos que o gerador não representa. |
| 7. Construtor cego | **REFUTED** | A estrutura básica é adequada, mas a allowlist não entrega semântica suficiente; `check()` deixa conteúdo fora da verificação. |

Os **bloqueios abaixo impedem liberar um pacote cego válido**. O construtor pode materialmente escrever os arquivos atuais, mas isso não demonstraria conformidade.

1. **Eliminar as referências retrospectivas anteriores à disclosure.**  
   Em [v0.5.5-r2-arguments.md:20](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:20), “the two targets whose route, if any, needs a change” repete uma conclusão histórica mais forte que o parecer r2choice. Substituir por:

   > “R2 examines prospective test-rule changes relevant to D2 and T2a. This scope does not establish that estimator improvements under the current rules are impossible.”

   Na linha **195**, retirar “the objections in the record”:

   > “The separate questions are how the joint probability is computed and how an unresolved residual is classified.”

   Na linha **267**, substituir “where the background sub-check lacked power” por:

   > “when the proposed alternative changes the sensitivity classification”

   Na linha **268**, substituir “where Fréchet was the limit” por:

   > “when the joint probability meets the sensitivity requirement but its Fréchet lower bound does not”

   Esses últimos enunciados são condições matemáticas prospectivas. As redações atuais apontam para diagnósticos conhecidos. **Datas, identificadores, fórmulas, inventário de locks e custos operacionais não são, por si, vazamentos de resultados.**

2. **Completar e corrigir a disclosure, mantendo todo esse conteúdo fora do pacote.**  
   Em [v0.5.5-r2-arguments.md:287](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:287), acrescentar:

   > “The limit of 13 is D2-F’s route-certificate threshold, including its estimator reserve, not D2’s total loss allowance. The upper counts include unknowns. Neither the upper nor strict counts establish unavoidable retention losses.”

   Isso preserva a distinção exigida pelo r2choice e pelo próprio [d2f-A.json:114](/C:/Projetos/refute/docs/validation/v0.5.5/d2f-A.json:114).

   Nas linhas **305–306**, substituir a referência genérica a “every earlier record” por inventário datado e identificável. Há conhecimento documentado não enumerado, por exemplo:

   - D2-F: v0.4 reteve **178/182**, versão 5 **135/182**.
   - A ponte D1-P entre geradores, explicitamente conhecida no relatório G1.
   - As previsões históricas de D2 e a disponibilidade histórica de T3b reproduzidas nos relatórios.
   - O rascunho das perguntas, que seu próprio C6 inclui no conhecimento a divulgar.

   Não consigo verificar a memória privada do autor. Consigo afirmar que **a declaração atual de completude não é auditável**.

3. **Reformular B1 como escolha normativa, sem apresentá-la como consequência necessária dos princípios.**  
   Em [v0.5.5-r2-arguments.md:55](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:55), substituir o princípio 3 por:

   > “Preserve partial evidence in the dossier. Whether unresolved warning attacks block the categorical verdict is a separate policy choice; INCONCLUSIVE does not erase the decided tests.”

   O código distingue **consequência de uma falha** de **incapacidade de decidir**. Não estabelece uma ordenação única na qual INCONCLUSIVE deva ter efeito menor que warning FAIL. A regra atual está expressa em [verdict.py:238](/C:/Projetos/refute/src/refute/core/verdict.py:238).

   Nas linhas **93–102**, substituir a alegação de preservação automática do princípio 2 por:

   > “Option (e) changes aggregation and broadens WEAKENED to include unresolved warning attacks. It lowers the evidential requirement for a retained and decidable verdict, while preserving the requirement for SURVIVED. This trade-off requires an independent justification.”

   **Não é um afrouxamento inteiramente oculto**, pois as linhas 95–97 reconhecem a ampliação do significado. Entretanto, dizer que isso apenas corrige uma violação lógica mascara o custo real. A opção (a) também respeita o princípio 2; logo, “the only option” é falso.

   Na definição de (e), explicitar:

   > “All expected decisive tests must be present, every gate must PASS, and every fatal test must PASS. Missing expected tests remain blocking. Existing gate and fatal-FAIL precedence is preserved.”

4. **Resolver T2b e especificar a medida adversarial de B1.**  
   Em [v0.5.5-r2-arguments.md:111](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:111), retirar “unconfirmed” e substituir por:

   > “T2b counts gated detections whose verdict is SURVIVED or WEAKENED, separately for inverted and rotated curves. Option (e) can increase that count and is directly tested by T2b’s frozen comparison.”

   Evidência: [c2.py:32](/C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:32), [c2.py:311](/C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:311) e [c2.py:389](/C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:389).

   Nas linhas **116–119**, acrescentar:

   > “Report paired INCONCLUSIVE-to-WEAKENED transitions over the fixed eligible denominator, alongside SURVIVED and SURVIVED + WEAKENED rates.”

   A participação “among WEAKENED” sozinha tem denominador móvel. D1, que conta apenas SURVIVED, **não limita sozinho** esse custo de B1.

5. **Restringir B2 ao mecanismo efetivamente medido.**  
   Em [v0.5.5-r2-arguments.md:130](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:130), substituir a interpretação abrangente por:

   > “The sub-check measures a positive in-transit background rise relative to the measured SAP dip. Its connection to a false-positive mechanism depends on a specified measurement model.”

   O código usa `rise = -g_bkg.mean`, dividido por `g_sap.mean`, e simula a região composta de rejeição. Não demonstra que esse mecanismo representa genericamente uma queda causada por outra estrela.

   Nas linhas **145–147**, substituir “partial contamination ... stays covered” por:

   > “The unchanged FAIL threshold still flags sufficiently strong observed effects. It does not certify sensitivity to partial contamination below the proposed alternative.”

   Manter o fallback, acrescentando às linhas **157–161**:

   > “Without a supplied derivation of sign, scale, aperture coupling and model uncertainty, (a) remains the primary. A PASS certifies the declared sensitivity under that model, not the absence of background contamination.”

   Aumentar a alternativa pode facilitar o certificado de potência. Isso precisa ser reconhecido como redução do conjunto de efeitos contra os quais o PASS é certificado.

6. **Retirar a suficiência indevida atribuída às famílias para B2.**  
   Em [v0.5.5-r2-arguments.md:166](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:166), substituir a afirmação sobre binárias de fundo por:

   > “C1 EB1 and EB2 test eclipsing-binary survival, not background-binary coupling. They do not validate the proposed background measurement model.”

   Os EB1/EB2 são inseridos na curva e recebem auxiliares por `make_aux`; o background padrão é gerado separadamente. Ver [c1.py:263](/C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:263), [c1.py:363](/C:/Projetos/refute/src/refute/packs/tess/calib05/c1.py:363) e [synthetic.py:357](/C:/Projetos/refute/src/refute/packs/tess/synthetic.py:357).

   Nas linhas **170–172**, acrescentar:

   > “The frozen families remain mandatory non-regression checks. Validation of B2 additionally requires controls that explicitly couple the contaminating process to SAP and the background estimate, including partial contamination.”

   Isso propõe uma obrigação futura, sem autorizar executar controles agora.

7. **Qualificar B3.2 e declarar explicitamente a mudança de regra em B3.3.**  
   Em [v0.5.5-r2-arguments.md:202](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:202), substituir a afirmação de dependência conhecida por:

   > “A joint probability is determined only after specifying a common generative model for the fitted coefficients and residual statistic. Agreement of marginal probabilities is necessary but does not validate their dependence.”

   A proposta deve preservar a alternativa, o tratamento das fases e a região de rejeição. A decisão precisa usar o **limite inferior da banda simulada**, com regra conservadora quando a banda cruza o requisito. O código atual calcula as marginais e aplica Fréchet em [battery_v52.py:363](/C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:363); a simulação da marginal do flag está em outro arquivo, ausente da allowlist.

   Na linha **218**, substituir o título por:

   > “B3.3 The ambiguous-cause branch: a proposed decision-rule change”

   Na linha **229**, acrescentar:

   > “Let r be box_after, sigma_r its error, and f and k the frozen FAIL constants. Shown small means r + k sigma_r < fD; shown large means r - k sigma_r > fD; otherwise the result remains INCONCLUSIVE. Any new PASS retains the applicable coverage, domain and sensitivity requirements and carries valid sensitivity blocks.”

   **B3.3 muda a regra**, pois transforma determinados INCONCLUSIVEs em PASS. A simetria é uma convenção defensável, mas não prova exclusão de variabilidade fora do modelo ajustado. O ramo INCONCLUSIVE atual também não entrega os blocos de sensibilidade que um novo PASS precisará carregar.

8. **Completar a tabela de dependências e corrigir suas garantias.**  
   Em [v0.5.5-r2-arguments.md:264](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:264):

   - **B2, B3.2 e B3.3:** incluir D4 entre os alvos afetados; possíveis novos SURVIVED também afetam D1 e T2c.
   - **B3.2:** substituir “none by construction if the model holds” por “additional spurious survivors may be admitted when sensitivity-blocked cases become PASS”.
   - **B3.3:** incluir T2a como alvo potencialmente beneficiado.
   - **`odd_even`:** incluir falsos FAILs em planetas, prejudicando D2/T2a e os respectivos controles de REFUTED; manter perdas de detecção de binárias contra D1.
   - **Eventual teste novo de D1:** acrescentar linha condicional com efeitos sobre D2, D4 e T2a; se fatal, incluir os orçamentos de REFUTED. Se depender de catálogo, incluir entradas ausentes ou inadequadas.

   Nas linhas **235–237**, substituir “no effect expected” sobre EB1/EB2 por:

   > “The sinusoid test does not inspect family labels. Changes may affect eclipsing-binary verdicts and must be measured.”

   Manter SE, V1, V2, ER, NR e T2b obrigatórios. Incluir as demais famílias pertinentes na avaliação conjunta. **D3 de PV conta REFUTED**, portanto não detecta sozinho uma mudança warning de INCONCLUSIVE para PASS; as transições em PV precisam aparecer separadamente.

9. **Entregar a semântica ausente no pacote.**  
   Em [r2_bundle.py:39](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:39), a allowlist atual não basta. Exemplos:

   - `power.py` declara registros, mas a aplicação está em `core/sensitivity.py`.
   - `pipeline.py` delega a bateria v4 a `pipeline_v52.py`, ausente.
   - `battery_v52.py` importa `_sinusoid_power`, `_wls` e outras operações de arquivos ausentes.
   - Parâmetros, papéis e escalas de medição não estão completamente definidos nos cinco fontes.

   Incluir um documento limpo, por exemplo `r2-code-semantics.md`, ou expandir os argumentos com conteúdo equivalente:

   > “This document specifies the frozen execution path, expected decisive tests, severities, roles, coverage and sensitivity enforcement, parameter values, measurement units and proposed branch changes. It contains no empirical outcomes or result-record references.”

   Não é obrigatório existir um arquivo separado chamado “semântica”. **É obrigatório entregar esse conteúdo.** Ampliar a allowlist também é possível, após inspecionar os novos arquivos.

10. **Corrigir a verificação do manifesto e o alcance da checagem de vazamento.**  
    Em [r2_bundle.py:142](/C:/Projetos/refute/docs/validation/v0.5.5/r2_bundle.py:142), substituir a exclusão por nome por exclusão apenas do caminho exato:

    ```python
    if p.is_file() and p != OUT / "MANIFEST.json"
    ```

    Antes da comparação dos arquivos, exigir:

    ```python
    if (OUT / "MANIFEST.json").read_bytes() != MANIFEST.read_bytes():
        raise SystemExit("the delivered manifest differs: a STOP")
    ```

    Hoje, qualquer `subpasta/MANIFEST.json` fica invisível ao inventário, podendo carregar conteúdo adicional. A cópia do manifesto entregue ao revisor também não é conferida.

    Em **`LEAKS`, linha 46**, ampliar a detecção das referências retrospectivas identificadas e exigir inspeção contextual dos bytes finais. Os padrões atuais deixam passar “where Fréchet was the limit”. Expressões regulares continuam sendo guarda auxiliar, não prova de cegamento.

As **ressalvas seguintes precisam ficar registradas**, mas não exigem resolver agora todas as decisões futuras.

11. **C1, C2 e custos.**  
    [v0.5.5-r2-arguments.md:252](/C:/Projetos/refute/docs/plans/v0.5.5-r2-arguments.md:252): C1 e C2(a) são compatíveis com o estatuto e o r2choice. A sequência impede pilotos e números antes do congelamento.

    Acrescentar ao quadro:

    > “Deferred costs are unpriced obligations, not zero-cost commitments. Commands, environments, caps and measured-cost assumptions must be specified before the corresponding phase is frozen or released.”

    “Small”, “part of the estimate” e “priced later” identificam custos, mas ainda não constituem orçamento executável.

12. **C3 e C4: revisão contaminada e publicação posterior.**  
    Na linha **254**, acrescentar:

    > “Contamination voids the review; a different reviewer receives the corrected bundle.”

    Na linha **255**, substituir o limite “every number R3 publishes” por:

    > “The current and proposed variants are registered and published side by side in every subsequent evaluation and confirmation. Every future D2, D4 and T2a result also reports both aggregations.”

    As duas agregações já estão corretamente preservadas. Falta igual clareza para as demais variantes depois de R3.

13. **C5, ordem de construção e parada de R3.**  
    Na linha **256**, explicitar:

    > “Confirmation uses frozen C1 generator version 1. Version 2 is restricted to R1 development checks unless a separate change is approved.”

    Isso acompanha a emenda 1(c).

    Na linha **259**, acrescentar:

    > “If the maintainer selects a new D1 test, its design, price and non-regression step enter the build order before the joint evaluation; otherwise that step is explicitly absent.”

    Na linha **260**, indicar onde ficam transcritos o teto e o limiar operacional congelados de R3. “A declared threshold” não deve permitir escolher outro posteriormente.

14. **Fontes congelados e ordem do manifesto.**  
    Não encontrei, nos cinco fontes permitidos, comentários com resultados empíricos ou previsões de metas. Há referências históricas a revisões, por exemplo `pipeline.py:392`, `pipeline.py:1166` e `power.py:180`. São histórico de revisão, não contagens experimentais. O “45 of 50” em `power.py:40` descreve uma regra, não um resultado observado.

    A escrita do manifesto antes dos arquivos, em `r2_bundle.py:125`, está correta quanto à precedência pretendida. Isso não comprova construção ou entrega, que não executei. Também não recomendo editar fontes congelados para limpar comentários.

**Divergência registrada nesta rodada:** B1(e) não está demonstrada como mera preservação de evidência sem afrouxamento; recomendo B1(a) enquanto essa justificativa permanecer. Para B2 e B3.2, mantenho os fallbacks atuais quando os modelos necessários não forem apresentados e sustentados. Isso não altera a conclusão do r2choice de que B pode prosseguir como preparação.

**O documento não está pronto para o pacote cego.**