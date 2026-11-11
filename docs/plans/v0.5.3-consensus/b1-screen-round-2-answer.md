**Restam duas correções antes do run:**

- **[P1] E1 ainda pode contar tentativa como conclusão.** Em [b1_forecast.py:703](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:703), basta um contador `completion_*` positivo. Porém, [battery_b1.py:137](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:137) incrementa esse contador mesmo quando o resultado continua `None`, registrando também `e1.still_undefined`. Na contraprova sintética, todas as tentativas continuaram indefinidas e `stops=[]`. **Exigir conclusão bem-sucedida**, descontando `still_undefined` ou contando explicitamente retornos válidos.

- **[P2] O relatório ainda não fornece as razões de erro exigidas.** [b1_forecast.py:714](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:714) extrai valores como `0.998`, que são **probabilidades arredondadas**, não limites de erro. Os erros numéricos estão nos registros brutos da stage A, como `sigma_bound_ppm` e `sigma_box_bound_ppm`. Carregar e selar esses registros, guardar o erro efetivamente usado pela v5, inclusive nos fallbacks, e calcular as razões. Além disso, [_detail:120](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:120) continua omitindo `aperture_depth`, cuja sensibilidade pode mudar por E1.

**As demais correções conferem:**

- O conjunto histórico permanece com 112 elegíveis. Contraprovas isoladas de erros, duplicação, divergência v4 e ausência global de GLS agora produzem STOP.
- `RefusalProbe` intercepta o ponto comum aos três testes e restaura a função original. A população E2 continua corretamente excluindo recusa do seletor e `not_enough_data`.
- A geração compartilhada permanece equivalente por inspeção. O rerun v4 acrescenta uma verificação útil contra os status históricos.
- Shards, índices e referências entram nas verificações propostas. Não encontrei novo problema nos mecanismos de cap, disco ou lock, nem seleção de parâmetros ou invasão de B1.3/B1.4. A projeção de 2,3 CPU-h permanece uma estimativa.
- `screen` ainda termina antes do validador separado. **B1.2 só pode ser considerado concluído após `screen-summarize` sem STOP.**

Usei apenas leitura e contraprovas pequenas das funções puras, sem executar ataques, adquirir o lock ou acessar o caminho proibido.

**WEAKENED (corrigir a conclusão efetiva de E1 e completar o relatório antes do run).**