**Há bloqueios antes do run.**

- **[P1] Erros podem produzir sucesso vazio.** [b1_forecast.py:587](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:587) exclui registros v5 não `OK` antes de verificar as populações. Reproduzi isoladamente: **120 `ERROR` → `eligible=0`, `stops=[]`**. Fixar os 112 elegíveis históricos e gerar STOP por falha, ausência ou duplicação. Validar também ativação e contadores, como no smoke.

- **[P1] A população de E1 está incompleta.** [b1_forecast.py:621](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:621) considera somente `odd_even.class == insufficient_sensitivity`. Nesse cache, isso identifica os cinco casos de `odd_even`, mas ignora recusas em `aperture_depth` e `systematics`. Há exemplos concretos adicionais em **1088 e 1104**, registrados no diagnóstico da stage A. Usar as recusas reais de `group_variance`, com contexto por teste, independentemente dos contadores de conclusão da v5. Uma população apenas de aperture/systematics com E1 zerado atualmente passa sem STOP.

- **[P2] O relatório não entrega todo o B1.2.** [b1_forecast.py:115](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:115) guarda detalhes apenas da v5; [b1_forecast.py:618](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:618) acrescenta descrições dos blockers, sem os limites numéricos. Faltam **mudanças dos blocos de sensibilidade e razões de erro contra os bounds**. Além disso, `_detail.status` é anterior à aplicação da sensibilidade, podendo mostrar PASS enquanto `v5_tests` mostra INCONCLUSIVE. Identificar explicitamente ambas as etapas.

- **[P2] As referências externas não estão seladas.** [b1_forecast.py:548](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:548) lê shards diretamente, sem verificar sidecars; a pré-checagem compara somente quantidade. O [fingerprint:304](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:304) não inclui esses registros nem os bounds. Validar integridade, índices exatos e esquema, e incluir os hashes das referências usadas.

**Os demais pontos estão coerentes:**

- **E2:** [linha 610](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:610) interpreta corretamente os registros atuais: exclui recusa do seletor e `not_enough_data`. `e2.calls` prova entrada; `e2.gls` distingue uso efetivo de GLS dos fallbacks.
- **Candidato e comparação histórica:** [linha 148](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:148) repete a geração compartilhada de `forecast_v4.one`. Recalculei exatamente o fingerprint antigo: **`729b7c6bf362170c`**, e os 60 shards conferem com seus sidecars. Portanto, neste checkout, reutilizar os status v4 é justificável sem rerun. A diferença do fingerprint B1 não invalida isso.
- **Escopo e recursos:** nenhuma seleção de parâmetro ou execução de B1.3/B1.4. Alocação de 6 CPU-h, cap, reserva, limite de registro e quota estão conectados aos mecanismos existentes. O lock cobre ambos os comandos. `screen` termina antes da validação separada; seu sucesso sozinho não pode liberar a próxima etapa.

Revisão somente leitura, sem workload científico, alterações, aquisição do lock ou acesso ao caminho proibido.

**REFUTED**