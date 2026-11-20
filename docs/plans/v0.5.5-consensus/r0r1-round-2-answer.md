**As correções resolveram boa parte da rodada 1, mas ainda há bloqueios para congelar o código.** O principal é a identidade entre etapas: o hash de `src/` é registrado, porém não é comparado.

Conferência exclusivamente por leitura local. Não executei scripts ou testes, não usei rede e não acessei o diretório proibido.

**Vereditos da rodada 2**

| Item | Veredito | Resultado |
|---|---|---|
| **1a** | **SURVIVED** | Preços, limites de Wilson e condição integral de D2/D4 estão explícitos. O fatal ficou corretamente separado como cenário histórico. |
| **1b** | **WEAKENED** | Sorteio, independência declarada e aproximação de primeira ordem estão claros. Resta corrigir “strict and generous bounds”: não há ordenação garantida dessas leituras em relação ao prior. |
| **1c** | **SURVIVED** | Mantém os requisitos de prova, as revisões e a aprovação não delegada. |
| **1d** | **SURVIVED** | A afirmação excessiva sobre espúrios foi corrigida. As salvaguardas permanecem, sem decidir questões de R2. |
| **1e** | **SURVIVED** | As nove decisões continuam fiéis e justificadas por princípio. Persistem defeitos na implementação de identidade, isolamento e retomada. |
| **2** | **SURVIVED** | Sob uso serial declarado, o `finally` restaura a função; o fluxo estelar separado preserva os demais sorteios. Os testes novos cobrem exceção em `generate` e `forecast.planet_model` antes/depois. Avaliação estática, sem executá-los. |
| **3-D2F** | **WEAKENED** | A retirada de `closed`, a contagem superior e a nova futilidade estão corretas. A projeção GLS de `mu_box` está algebricamente correta, mas seu sinal de entrada ainda exige esclarecer unidades e tendência. Resta também uma frase que apresenta a contagem como independente de estimador. |
| **3-D1P** | **WEAKENED** | Três ajustes, limitações de calibração e preços foram corrigidos. Os limiares permanecem fiéis. A `truth` inteira ainda não é gravada, apesar do declarado. A interpretação probabilística precisa continuar explicitamente nominal. |
| **3-T2aE** | **WEAKENED** | Comparação histórica com I1, tolerâncias, paradas, placebos individuais e validações antes das divisões foram incorporados. Dependem ainda das correções de identidade e proveniência do replay. |
| **3-T3b** | **SURVIVED** | Adiamento continua sendo aplicação conservadora de (e). A distinção entre metadados atualizados, quadro congelado e quadro novo foi corrigida. |
| **3-comum** | **REFUTED** | `NO_PAUSE`, teto cumulativo e contador melhoraram. Ainda há comparação incompleta de identidade, bloqueio real usado pelos testes e preparação da execução fora do bloqueio que protege a execução. |
| **4** | **SURVIVED** | ROADMAP agora acrescenta somente o ponteiro histórico, preserva a regra de avanço e descreve T3b adiada. Os dois registros antigos continuam sem diff. A cópia da conferência factual mantém o SHA-256 da origem. |
| **pinned_hash** | **WEAKENED** | É defensável como mecanismo explícito para **localizar registros históricos**. Não certifica o ambiente histórico do replay. A implementação precisa restringir melhor o que aceita e separar identificação histórica de execução atual. |

**Sobre o `pinned_hash`**

Confirmei que `HEAD` é `5e5f40a`, que o diff de `uv.lock` altera soupsieve e tornado e que `src/` e `pyproject.toml` não diferem de `8653911`.

Não encontrei importações diretas de soupsieve, tornado, BeautifulSoup ou `bs4` em `src/`. Entretanto, os metadados locais mostram a cadeia **astroquery/lightkurve → beautifulsoup4 → soupsieve**. Portanto, ausência de importação direta não demonstra ausência de dependência transitiva.

**A solução pode ser honesta sem reinstalar o ambiente antigo**, desde que declare: registros históricos autenticados por sua identidade original; replay executado no ambiente atual; equivalência verificada apenas nos resultados e tolerâncias comparados. A reprodução desses números é evidência importante, mas não prova equivalência integral dos ambientes.

**Correções concretas restantes**

1. **Comparar a identidade completa entre etapas.**  
   [d1p_price.py:312](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:312), [d2f_floor.py:476](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:476), [t2ae_census.py:362](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:362).

   `code_identity()["sha256"]` cobre somente `FROZEN`. O `src_code_hash` está em outro campo e fica fora dessas comparações. Uma mudança em `src/` ou `uv.lock` pode permitir combinar A e B sob identidades diferentes.

   **Correção:** comparar o documento completo de identidade, ou criar um digest que inclua `src_code_hash`, manifesto externo e identidade histórica aplicável.

   **Texto:** “The second stage refuses any difference in the complete code identity, including the current source/dependency hash.”

2. **Separar busca histórica e proveniência da execução atual.**  
   [pinned_hash.py:9](/C:/Projetos/refute/docs/validation/v0.5.5/pinned_hash.py:9), [t2ae_census.py:211](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:211), [desenhos:304](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:304).

   O contexto atualmente substitui globalmente `compute_code_hash` durante todo o replay. Isso pode apresentar o hash histórico a chamadas que pretendam identificar a execução atual.

   **Correção:** restringir a substituição aos leitores que efetivamente precisam recomputar a localização antiga. Registrar separadamente hash histórico, hash atual, intérprete e versões efetivamente usadas no replay.

   **Texto:** “The pinned hash authenticates historical record lookup. The replay runs in the current environment; matching recorded outputs establishes agreement only for the quantities and tolerances checked.”

3. **Restringir o que `pinned_code_hash()` aceita.**  
   [pinned_hash.py:40](/C:/Projetos/refute/docs/validation/v0.5.5/pinned_hash.py:40).

   Hoje qualquer alteração **commitada** futura em `uv.lock` é aceita, desde que `src/` e `pyproject.toml` permaneçam iguais. Isso ultrapassa a exceção descrita, limitada à atualização `5e5f40a`.

   Além disso, `git diff` e `git status` não demonstram igualdade de todos os arquivos cobertos por `compute_code_hash`: este também pode incluir arquivos ignorados pelo Git.

   **Correção:** conferir o manifesto normalizado de arquivos contra `8653911` e aceitar somente o lock histórico ou o lock explicitamente aprovado de `5e5f40a`. Recusar outras diferenças.

   Acrescentar testes isolados para restauração após exceção, mudança de fonte, lock não aprovado e arquivo adicional coberto pelo hash.

4. **Completar o manifesto executado pela T2a-E.**  
   [t2ae_census.py:313](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:313).

   Ainda faltam dependências chamadas pelo caminho de execução, por exemplo:

   - `docs/validation/v0.5.2/stage2/forecast_t2a.py`;
   - `docs/validation/v0.5.2/stage2/forecast_v4.py`;
   - `docs/validation/v0.5.3/stageB/b1_data.py`;
   - `docs/validation/v0.5.3/stageB/b1_d2d4_rest.py`;
   - `calibration/v0.4/claim.yaml`.

   `i1_diagnose.t2a_one` chama `ft.targets()` e `ft._plans()`; portanto esses arquivos não são apenas importações sem uso. Incluir também os insumos congelados pertinentes, diretamente ou por um manifesto autenticado.

5. **Gravar a verdade inteira na D1-P.**  
   [d1p_price.py:217](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:217).

   A correção foi aplicada à D2-F, mas a D1-P continua guardando apenas alguns campos da verdade.

   **Correção concreta:** acrescentar `truth=truth` ao registro. Manter a limitação declarada dos parâmetros devolvidos pelos ajustes legados de B0.

6. **Fazer o teste do ledger usar também um bloqueio temporário.**  
   [ledger_v055.py:103](/C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:103), [test_ledger_v055.py:27](/C:/Projetos/refute/tests/v055/test_ledger_v055.py:27).

   `path: Path = LOCK` captura o caminho quando a função é definida. Trocar posteriormente `ledger_v055.LOCK` não altera esse argumento padrão. Assim, os testes podem criar/remover o **lock real** em `.cache/v055/`, mesmo usando ledger temporário.

   **Correção:**
   ```python
   def __init__(self, step: str, path: Path | None = None):
       self.step = step
       self.path = LOCK if path is None else path
   ```
   Acrescentar uma asserção de que o bloqueio efetivo fica dentro de `tmp_path`.

7. **Proteger preparação, contador e execução com o mesmo bloqueio.**  
   [d1p_price.py:326](/C:/Projetos/refute/docs/validation/v0.5.5/d1p_price.py:326), [d2f_floor.py:490](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:490), [t2ae_census.py:376](/C:/Projetos/refute/docs/validation/v0.5.5/t2ae_census.py:376).

   `begin_run`, verificações e cálculo do teto acontecem antes do `Exclusive` que envolve `execute`. Outro processo pode alterar o consumo ou consumir a retomada nesse intervalo.

   **Correção:** um `Exclusive` externo deve envolver validações finais, cálculo do teto, registro da tentativa e execução. Fazer as recusas de pré-condições antes de consumir a retomada.

   Em [ledger_v055.py:156](/C:/Projetos/refute/docs/validation/v0.5.5/ledger_v055.py:156), não depender exclusivamente de `spent_hours>0` para reconhecer uma retomada: uma interrupção pode deixar cobrança no driver antes da atualização desse campo. Persistir o estado da tentativa e considerar as cobranças existentes.

8. **Não garantir drenagem às 08h com um prazo apenas declarado.**  
   [r1_common.py:92](/C:/Projetos/refute/docs/validation/v0.5.5/r1_common.py:92), [desenhos:46](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:46).

   Antecipar o último despacho para 07h40 corrige o caso normal. Um shard que exceda 1.200 segundos ainda pode atravessar as 08h com mais de dez trabalhadores, pois o driver só detecta o excesso após terminar.

   **Opção conservadora simples:** limitar R1 a dez trabalhadores também fora do horário comercial. “Até 22” é um teto, não obrigação de usar 22.

   Se mantiver 22, implementar uma proteção efetiva da transição e registrar a parada quando não conseguir drenar. Não escrever “drain before 08:00” como garantia do mecanismo atual.

9. **Esclarecer a média física usada em `mu_box`.**  
   [d2f_floor.py:162](/C:/Projetos/refute/docs/validation/v0.5.5/d2f_floor.py:162).

   A projeção `inv2 @ X2'Σ^-1μ` está correta. Contudo, `scale` é a mediana setorial usada na conversão de unidades das colunas. O gerador aplica uma **tendência multiplicativa temporal**, em `c1.py:375`. Essas duas grandezas não são intercambiáveis.

   **Correção:** derivar `mu_planet` do modelo gerador sem ruído, subtraindo o fundo conhecido e colocando sinal, colunas e covariância nas mesmas unidades. Se conservar `-trapezoid*scale`, descrevê-lo como uma aproximação de trânsito em unidades normalizadas, sem afirmar que é exatamente a média física do gerador.

   Acrescentar uma verificação algébrica com escala não unitária e tendência não constante.

10. **Retirar as duas generalizações estatísticas restantes.**  
    [estatuto:114](/C:/Projetos/refute/docs/plans/v0.5.5-charter.md:114), [desenhos:186](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:186), [desenhos:228](/C:/Projetos/refute/docs/plans/v0.5.5-r1-designs.md:228).

    **Para caixa/conhecido:**  
    “These are reference oracle readings under their respective stellar assumptions. No ordering around the primary surrogate is established.”

    Isso é especialmente necessário agora que a distribuição estelar pode sair da caixa de 3σ.

    **Para D2-F:**  
    “These counts combine model-based oracle calculations and blockers observed under version 5. A small count motivates further design; it does not establish an estimator-independent retention margin.”

    A frase atual, “a count is a property of the rules, not of any estimator”, continua incompatível com `DATA` e `RULE`.

    **Para D1-P:** trocar “is not rejected with probability” por “is assigned the nominal surrogate non-rejection score”. Preservar os limiares como regras de leitura para G1, sem atribuir cobertura ou calibração que o próprio desenho declara não demonstradas.

Os tetos continuam coerentes: **64 CPU-h, 2,4 M tokens, 7,2 dias-agente e 4 GB**. Não encontrei alteração da regra de avanço, mudança em `src/` nesta proposta ou artefatos experimentais R1 nos diretórios inspecionados. A execução permanece dependente da revisão independente e da liberação do mantenedor.