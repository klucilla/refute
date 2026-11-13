**As seis alterações estão presentes. O núcleo estatístico sobrevive, dentro do escopo condicional declarado. Resta uma lacuna operacional na barreira de CPU.**

### Correções confirmadas

- **D1 conjunto:** a rota exige agora `1 − Σ(1 − p_f) ≥ 0,95`, sem depender de independência entre EB1 e EB2. As verificações individuais ficaram informativas. [step3_i3.py:471](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:471).
- **Relatórios e desconhecidos:** `_whole` inclui os critérios pontuais; `_separation` preserva os denominadores e separa EB1/EB2; não reproduzir B0 deixou de provocar parada e impede a rejeição daquela binária. [step3_i3.py:334](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:334), [step3_i3.py:354](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:354), [step3_i3.py:420](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:420).
- **Reservas:** declarar uma parte já não elimina sua reserva. Docstring e texto de `i_f` também foram corrigidos. Permanecem explícitos: inferência somente em `τ*`, PASS como não rejeição, ausência de sensibilidade e impossibilidade de conclusão negativa.

### Fraqueza restante e opção conservadora

**A barreira protege o consumo monitorado, mas não reserva a cobrança de uma interrupção.** O novo limite divide a margem por `OVERSHOOT`, porém não desconta o lote em andamento. O driver acrescenta, para um lote não encerrado:

`12 × (1.500 + 20) / 3.600 = 5,067 CPU-h`

Essa cobrança pode ultrapassar a margem de 40 CPU-h, embora o consumo monitorado estivesse dentro dela. O resumo também acrescenta CPU posteriormente. [step3_i3.py:268](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:268), [driver.py:375](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:375), [step3_i3.py:382](C:/Projetos/refute/docs/validation/v0.5.4/step3_i3.py:382).

**Opção mais conservadora:** descontar da margem, antes da admissão e do cálculo do limite, **5,067 CPU-h para uma interrupção**, mais a reserva das cobranças externas ainda disponíveis. Fazer a leitura das reservas e o cálculo sob o mesmo bloqueio da execução. Se a alocação não couber nessa margem, aplicar **STOP**, preservando os limites congelados.

Não encontrei outro problema material nas seis correções. A eventual rota continua sendo evidência sobre este classificador nas populações e hipóteses declaradas, sem certificar a bateria completa. Nenhum experimento foi executado nesta revisão.

**WEAKENED (com a correção restante: reservar a cobrança de interrupção e os custos externos também sob a barreira de 40 CPU-h).**