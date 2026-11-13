**A maioria dos pontos da rodada 1 foi resolvida, mas restam três correções no script.** Revisão estática, sem execução nem leitura dos registros vedados. O HEAD observado agora é `4755d79`.

**Correções necessárias**

1. **T2a ainda lê o campo de classe errado.**  
   [step1_floor.py:110](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:110) consulta `row["class"]`. Os briefs da T2a preservam **`inconclusive_class`**, escrito em [paired.py:92](C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:92). `class` está correto apenas para a D2, [forecast_v4.py:92](C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_v4.py:92).  
   **Correção:** reconhecer `inconclusive_class == "not_enough_data"` na T2a, com status INCONCLUSIVE. Sem isso, os 20 DATA publicados não entram por esse campo, contrariando o resultado previsível divulgado.

2. **INFO continua indevidamente condicionado à classe (i) de I1.**  
   Em [step1_floor.py:89](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:89), o bound só é consultado quando aparece `REC?`. Entretanto, a tabela define INFO por **teste INCONCLUSIVE e bound válido abaixo de 0,95**, independentemente da classe I1, [plano:64](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:64).  
   **Correção:** avaliar INFO independentemente das demais categorias nesses testes. Um INCONCLUSIVE classificado como RULE, por exemplo, deve poder receber também INFO se satisfizer o bound. Manter REC restrito à classe (i). O marcador `hidden` deve acrescentar o teste à análise, sem substituir a verificação do status exigido para INFO.

3. **“Não-grid” ainda não corresponde aos 24 casos solicitados.**  
   [step1_floor.py:240](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:240) exclui qualquer PROC. Isso elimina também os erros não relacionados à grade: quatro mensagens apenas de erro não mensurável e quatro combinando esse erro com ausência de trânsito, [i1-diagnosis.json:298](C:/Projetos/refute/docs/validation/v0.5.4/i1-diagnosis.json:298).  
   **Correção:** selecionar `systematics` com I1 classe (ii), excluir especificamente **recusa fora da grade** e contabilizar todos os conjuntos restantes, inclusive PROC e MSG+PROC. Verificar o total esperado de 24.

**Pontos resolvidos**

- Divulgação dos resultados previsíveis e ressalva sobre `F_upper`, [plano:24](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:24), [:84](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:84).
- Importação de `b1_d2d4_rest`, campos D2 e localização de `selection.refused` na T2a.
- Categorias simultâneas, inclusão dos testes ocultos disponíveis em I1 e sua exclusão da comparação publicada.
- Margens contra 2 calculadas fora dos REFUTED, [step1_floor.py:260](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:260).
- **A chave publicada de T2a B está correta:** `t2a.B.by_stratum[s].decisive_blockers_by_test`, somada com `Counter.update`, [step1_floor.py:293](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:293).
- Os leitores agora verificam proveniência e completude; I4 também rejeita chaves duplicadas ou desconhecidas, [i4_rest2.py:351](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:351).

**Leitura e escrita**

`i1_diagnose._read` e `i4_rest2._records` **não escrevem**, inclusive nos caminhos de recusa, [i1_diagnose.py:490](C:/Projetos/refute/docs/validation/v0.5.4/i1_diagnose.py:490), [i4_rest2.py:331](C:/Projetos/refute/docs/validation/v0.5.4/i4_rest2.py:331). Não chamam `run`, reconciliação ou `summarize`. Com `python -B`, as escritas identificadas ficam nos dois destinos permitidos, [step1_floor.py:295](C:/Projetos/refute/docs/validation/v0.5.4/step1_floor.py:295). Não identifiquei rerun, alteração de `src/` ou emissão de rascunho.

WEAKENED (corrigir o campo da T2a, avaliar INFO independentemente da classe I1 e contabilizar corretamente os 24 não-grid).