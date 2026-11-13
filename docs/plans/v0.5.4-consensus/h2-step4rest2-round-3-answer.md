**As quatro correções fecham os pontos da rodada 2. Não encontrei outro bloqueador material**, considerando a premissa operacional de latência agora explícita.

- **Exceção e consumo:** `_record_exception()` lê `spent_seconds()`, preserva o maior consumo registrado e grava o stop. Se a leitura falhar, registra `charge_unknown`; o `unresolved_stop` impede o resumo. A cobrança de batch aberto inclui o crash. [step4_rest2.py:116](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:116), [driver.py:379](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:379).

- **Conferência final:** `_check_fixed_cap()` soma o consumo da parte, registra `fixed_cap_passed` e recusa acima de 1,0 CPU-h. É chamado após o retorno do driver e novamente antes da montagem do resumo. Na exceção, o stop já bloqueia a publicação. [step4_rest2.py:135](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:135), [step4_rest2.py:206](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:206), [step4_rest2.py:219](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:219).

- **Latência:** a documentação distingue corretamente os **198,33 CPU-s de margem operacional** de uma prova de reação máxima. A conferência posterior detecta uma ultrapassagem e impede o resumo; não desfaz consumo ocorrido. [step4_rest2.py:31](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:31).

- **Ordem do orçamento:** o termo da fase é conferido antes de reconciliar, fechar ou transferir. Para esta parte nova, o termo próprio é `1,5 / 1,1 ≈ 1,364`, superior ao cap de `0,550926`. A verificação posterior permanece. [step4_rest2.py:178](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:178), [step4_rest2.py:190](C:/Projetos/refute/docs/validation/v0.5.4/step4_rest2.py:190).

Continuam preservados o cálculo científico, as linhas, o fingerprint e o resumo das três partes. Morte externa exige o registro manual de stop **e consumo**, como documentado. Nada foi executado ou alterado nesta revisão.

SURVIVED