**Ainda há um bloqueio antes do smoke.**

1. **[P1] O validador rejeita a recusa legítima de T2a A.** [b1_forecast.py:340](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:340) exige todos os wrappers em cada ataque. Porém, A recusa o seletor acima de quatro setores e [pipeline_v52.py:99](C:/Projetos/refute/src/refute/packs/tess/pipeline_v52.py:99) retorna o resultado sem chamar E2. Portanto, o smoke de 5–20 setores será rejeitado mesmo com comportamento correto. **Minha recomendação anterior foi ampla demais:** os contadores devem respeitar as recusas estruturais. Exigir a recusa esperada em A e chamadas positivas nos caminhos elegíveis de D2/C, sem alterar o seletor.

2. **[P2] A validação ainda aceita evidência incompleta.** Em [b1_forecast.py:325](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:325), não há conferência da quantidade e identidade dos registros; em [linha 334](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:334), somente os nomes das substituições são comparados; em [linha 338](C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_forecast.py:338), contadores ausentes são ignorados. **Reproduzi em memória a aceitação de:** resultados vazios, contadores ausentes e configuração/hashes incorretos. Exigir exatamente os registros e ataques previstos, comparar a ativação completa e verificar contadores inteiros positivos quando aplicáveis.

**Correções confirmadas:**

- Limite final: 200.000 bytes aceitos; 200.001 convertidos em `ERROR`.
- Alterar somente as linhas altera o fingerprint.
- Reserva adicional de disco e medição posterior estão conectadas ao fluxo.
- O novo teste executa chamadas reais v4 → v5 → v4 pelo atributo de A0.
- **11 testes passaram novamente**, com sockets bloqueados. Eles ainda não cobrem o validador do runner.

Não encontrei nova regressão nos estimadores. Os helpers antigos permanecem inalterados. Nenhum arquivo foi modificado e nenhum smoke foi executado.

**REFUTED, quanto à prontidão do código para o smoke.**