## A. Passo 1 e contagem T3b

**Os dois resultados seguem os desenhos congelados.** Reproduzi as leituras locais, sem executar os experimentos: hashes, registros por caso e resultados coincidem integralmente; os leitores de I1/I4 não recusaram a montagem.

- **D2:** `8 / 16 / 21`, contra 22. A margem de **1 em F_upper está explicitamente condicionada à recuperação de todas as perdas REC/PROC**. Não demonstra recuperação conjunta nem viabilidade. [Desenho:84](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:84), [resultado:51](C:/Projetos/refute/docs/validation/v0.5.4/h2-step1-floor.json:51).
- **T2a B:** `F_strict = F_rule = 20 > 7`; os 24 casos não grid conferem. O desfecho apenas confirma a previsão divulgada antes da leitura. As sobreposições são novas; a conclusão de esgotamento sob essas premissas não é. Nenhum rascunho de inviabilidade foi produzido. [Divulgação:24](C:/Projetos/refute/docs/plans/v0.5.4-h2-step1-floor.md:24), [resultado:115](C:/Projetos/refute/docs/validation/v0.5.4/h2-step1-floor.json:115).
- **T3b:** conferem 2/22, rejeições `6/8/3/3`, total histórico 13/63 e falta de 9. O log contém 22 tentativas e 66 consultas, sem repetição ou erro. A leitura preserva a ressalva temporal e não transforma contagem em seleção ou inviabilidade. [Resultado:11](C:/Projetos/refute/docs/validation/v0.5.4/t3b-count.json:11), [regra:56](C:/Projetos/refute/docs/plans/v0.5.4-t3b-eligibility-count.md:56).

**Nenhuma nova parada não delegada identificada em A.**

**A: SURVIVED.**

## B. Passo 7 antes da execução

**O cálculo serve como diagnóstico otimista da regra, mas precisa das correções abaixo antes de rodar.**

- **Oracle:** usa efeméride/profundidade verdadeiras, covariância do gerador, normalização setorial fixa e Gram fora do trânsito com offsets e harmônicos aplicáveis. A tendência é tratada como conhecida. Omitir frequências extras reduz a covariância nesse modelo linear. A chamada `_sinusoid_power(cov, depth, depth, sp, seed)` também coincide com a bateria. [Script:67](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:67), [bateria:363](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:363).

- **Corrigir a inferência central:** Fréchet abaixo de 0,95 indica falha desse certificado, não impossibilidade universal. Por exemplo, marginais 0,97 dão limite inferior 0,94, mas admitem probabilidade conjunta 0,97. Retirar “nenhum estimador honesto” e o desfecho “exhausted under the oracle”; a condição congelada permite margem condicional ou `INCONCLUSIVE`. [Desenho:40](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:40), [script:195](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:195), [condição:60](C:/Projetos/refute/docs/plans/v0.5.4-audit-check.md:60).

- **Separar sensibilidade de retenção:** o mínimo dos blocos reproduz a exigência para um PASS quando `can_fail` vale. O script não verifica cobertura/`fail_allowed`, nem apresenta as sobreposições entre PASS qualificado, FAIL warning e INCONCLUSIVE. Um warning FAIL preserva retenção; portanto `DATA ∪ L_oe ∪ L_sin` não está demonstrado como piso inevitável de perdas. [Bateria:334](C:/Projetos/refute/src/refute/packs/tess/battery_v52.py:334), [agregação:183](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:183).

- **Fixar precisão e validade numérica:** são 2.000 sorteios por fase, mínimo entre oito fases, sem tratamento da incerteza perto de 0,95. Faltam critérios para Gram/covariância válida e probabilidades finitas; Cholesky inválida retorna potência zero. Esses casos precisam virar UNK/parada conforme regra prospectiva. [Potência:472](C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:472), [sorteios:58](C:/Projetos/refute/src/refute/core/sensitivity.py:58).

- **Cumprir as paradas:** exceções atualmente viram ERROR e o trabalho continua; o resumo pode declarar margem com esses UNK. A comparação com I4 permite nenhuma comparação e grava o resultado antes de verificar divergência. Exigir completude e registrar a parada explicitamente. Vincular também os insumos I4/passo 1 ao fingerprint. [Exceções:112](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:112), [fingerprint:127](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:127), [saída:227](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:227).

- **T2a e execução:** `INCONCLUSIVE` por ausência de covariância verdadeira é honesto. Parte, transferência, driver v3 e hard cap estão previstos. Corrigir `check_caps` para `in_h1=False`, reservar o orçamento restante e resolver a contradição entre parar acima de 0,5 ou 1,5 vezes essa alocação. O piloto sustenta apenas uma estimativa de custo. O launcher previsto é adequado; 19h30 interrompe novos despachos, permitindo concluir shards em voo. [Caps:148](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:148), [default:312](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:312), [limiares:77](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:77).

Os defeitos identificados acionam a **parada não delegada** definida na [auditoria:43](C:/Projetos/refute/docs/plans/v0.5.4-audit-check.md:43).

**B: WEAKENED, com as correções acima antes da execução.**