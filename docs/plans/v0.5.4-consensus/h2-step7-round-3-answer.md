## 1. Passo 7

**As correções metodológicas pendentes foram resolvidas.** O Gram residual agora é validado antes da inversão, sua σ é comparada com stage A, e qualquer parada registrada força `INCONCLUSIVE`. [step7_sinusoid.py:89](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:89), [step7_sinusoid.py:282](C:/Projetos/refute/docs/validation/v0.5.4/step7_sinusoid.py:282).

A leitura permanece corretamente limitada ao certificado da bateria, com piso condicionado aos status registrados e T2a diagnóstica. Parte, transferência, fingerprint, caps e corte de despacho continuam corretamente conectados. **Isso aprova o desenho, não fornece resultado científico nem comprova o custo total.**

Restam apenas limpezas documentais: retirar driver/população da lista de paradas *dentro* do registro, pois já estão classificados como anteriores à escrita; trocar “drained by 19:30” por “sem novos despachos após 19:30”. [Desenho:103](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:103), [desenho:113](C:/Projetos/refute/docs/plans/v0.5.4-h2-step7-sinusoid.md:113).

**Item 1: SURVIVED.**

## 2. Passo 5

As derivadas multiplicativas foram corrigidas, e o registro de σ original, resposta, σ convertida, desconhecidos e paradas melhorou. **Ainda não está demonstrada a equivalência de amplitude necessária à comparação com E2.**

- **`r_E2` continua sendo uma aproximação inadequada para decidir.** A média global do trapézio não incorpora eventos efetivamente mantidos, cobertura, candidato final, pesos/covariâncias do GLS e detrending. A simetria da forma contínua não garante simetria das amostras. Com respostas médias ímpares/pares de 0,8 e 0,6, profundidades iguais produzem contraste `0,2D`; dividir pela média global não elimina esse vazamento. [step5_gap.py:170](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:170), [GLS:172](C:/Projetos/refute/docs/validation/v0.5.3/stageB/battery_b1.py:172).
- **A mesma ressalva vale para a caixa:** a resposta direcional `r` está calculada, mas não demonstra resposta nula à profundidade comum. Portanto, `σ/r` ainda não estabelece equivalência com o contraste físico completo. [step5_gap.py:104](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:104).
- **A justificativa de colinearidade é falsa em geral.** Offsets e retas por janela absorvem constantes e termos lineares, não a curvatura quadrática. A opção conservadora é manter V_all como combinação parcial e retirar essa justificativa. [Desenho:74](C:/Projetos/refute/docs/plans/v0.5.4-h2-step5-gap.md:74).
- **Fechar a verificação de V0:** referências ausentes ou inválidas atualmente escapam da comparação. Registrar quantos planetas foram comparados e impedir desfecho positivo quando a reprodução exigida não puder ser verificada. Acrescentar também `inflation_denominator`. [step5_gap.py:284](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:284), [step5_gap.py:310](C:/Projetos/refute/docs/validation/v0.5.4/step5_gap.py:310).

**Opção conservadora para encerrar esta rodada:** preservar as inflações de Fisher e os diagnósticos brutos, tratar a resposta efetiva de E2 como desconhecida e suprimir razões E2 convertidas, shares e decisões baseadas nelas. Manter o desfecho do gap em `INCONCLUSIVE`; as potências convertidas da caixa também ficam sem interpretação equivalente até validar resposta ao contraste e vazamento comum. Os controles operacionais continuam adequados, mas não resolvem essa limitação científica.

**Item 2: WEAKENED, aplicar a opção conservadora acima e corrigir colinearidade e completude da comparação V0.**