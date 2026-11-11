**Ainda há três correções necessárias antes de rodar.** Os exemplos anteriores passaram, mas as provas isoladas encontraram:

1. **[P1] A degeneração do bootstrap depende de igualdade exata entre floats.** Em [b1_recal.py:456](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:456), arredondamento pode impedir a salvaguarda. Com oito hosts contendo respectivamente 1 a 8 valores, todos `z=4`, a média das réplicas varia apenas por arredondamento, mas recebe **FAIL**, excluindo E4. Com 13 hosts e 103 contrastes constantes, média e cauda recebem FAIL. **Detectar degeneração com tolerância numérica explícita**, preservando UNRESOLVED nesses casos.

2. **[P1] Exceções em C1 ainda apagam elegibilidade e resultados parciais.** [b1_recal.py:299](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:299) substitui todo o registro por ERROR; [b1_recal.py:498](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_recal.py:498) depois exclui esses registros das populações. Uma falha em E3 pode apagar um E2 já executado. No exemplo com 300 sucessos e 150 erros após a chamada, o resumo informou 300 tentativas, disponibilidade `1,0` e **PASS no desvio**, embora a disponibilidade fosse `0,667`. **Preservar os resultados e a elegibilidade por estimador; elegibilidade desconhecida deve bloquear PASS ou interromper o resumo.**

3. **[P2] A quota ainda não cobre todas as escritas do fetch.** O catálogo estático é escrito sem reserva em [b1_data.py:104](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:104), e os manifests também, em [b1_data.py:183](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:183). Os FITS podem caber e os manifests ultrapassarem a quota antes do `disk_after()`. **Reservar previamente os bytes desses metadados**, além dos arquivos de dados.

**Correções confirmadas:** pesos iguais por host nas estimativas e réplicas; salvaguardas incondicionais no caso numericamente exato; `ContrastProbe` restrito à primeira chamada; denominadores incluindo `not_enough_data` e retornos antecipados; oito propostas mantidas para host E4 com erro; download limitado e limpeza do `.part`; lock compartilhado com os runs; fingerprint ampliado e ativação registrada nos contrastes disponíveis. Confirmei os **783 registros com tamanho positivo, nenhum ausente**.

Não executei B1.3, alterei arquivos, adquiri locks ou acessei o caminho proibido.

**REFUTED: a versão atual ainda não está pronta para executar B1.3; corrigir os três pontos antes do procedimento no #217.**

