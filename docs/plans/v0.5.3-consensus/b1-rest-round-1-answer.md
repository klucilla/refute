O caminho nominal respeita a retomada autorizada, mas **há correções necessárias antes de executar**. Revisei somente em leitura, com simulações em memória, sem executar curvas nem acessar a pasta proibida.

**1. Escopo e orçamento**

- **Código, fingerprint e linhas: conferidos.** `_schedule()` recalcula `5bb3277e4a908c18`; a execução usa `b1_b14.shard` e filtra as linhas originais. Validei os 181 sidecars, faltam exatamente `d03180` a `d03198`. [b1_d2d4_rest.py:67](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:67), [b1_d2d4_rest.py:110](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:110), [b1_d2d4_rest.py:134](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:134).
- **A parada original permanece registrada.** `reconcile` move mensagem e justificativa para `reconciled`; os resultados originais não são reescritos. [budgeted.py:191](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:191).
- **A álgebra nominal do teto está correta:** para consumo anterior `C`, o cap adicional satisfaz `H ≤ (1,5 − C)/1,1`. A dupla contagem em retomadas reduz a folga disponível. Porém, **1,1 não é um limite físico estrito**: o watchdog consulta a cada 0,5 segundo e mata depois de ultrapassar o limiar. Reserve margem adicional e confira o consumo agregado também no fechamento e no ramo sem linhas. Atualmente ambos podem aceitar consumo acima de 1,5. [b1_d2d4_rest.py:115](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:115), [ledger_b.py:221](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/ledger_b.py:221), [driver.py:485](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:485).

**2. Defeitos e verificações**

- **Validar `attempt` antes de indexar.** `run -1` seleciona a primeira parte, entra no ramo de reexecução e permite reconciliá-la repetidamente. Reproduzi três despachos com mocks. Isso contorna o limite de uma reexecução. Aceitar somente `1` ou `2`. [b1_d2d4_rest.py:88](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:88).
- **Tornar a preparação de `run 2` recuperável.** A reconciliação ocorre antes de fingerprint, sidecars, identidade, disco e cap. Uma recusa posterior remove a condição exigida para tentar novamente; uma pausa da segunda tentativa também impede sua retomada. Validar antes e reconhecer uma segunda tentativa já autorizada pela reconciliação persistida, preservando sua identidade. [b1_d2d4_rest.py:101](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:101).
- **Fechamento ignora estados impeditivos do driver e gates.** Os checks de sidecars, duplicação entre partes e cobertura dos 200 IDs estão corretos. Entretanto, `_done()` não verifica `stop.json`, e `summarize()` não consulta `_open_gates`. O ramo sem linhas reconcilia somente o ledger. Exigir ausência de impedimentos ou uma reconciliação explícita, correspondente à parada autorizada, preservada em novo registro. [b1_d2d4_rest.py:75](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:75), [b1_d2d4_rest.py:147](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_d2d4_rest.py:147), [budgeted.py:305](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:305).

A ordem **transfer → declare está correta**, e o `Exclusive` externo cobre toda a operação, com reentrada nas chamadas internas. `MECHANICS` corresponde às mensagens locais de cap/projeção e exclui as mensagens explícitas de total, contabilidade e shard lento.

**3. Alternativa conservadora**

**Reduzir a concorrência** diminui trabalho em voo e desperdício numa interrupção, sem mudar função, fingerprint ou linhas. Isso ajuda a proteger o orçamento, mas não resolve a projeção baseada em uma curva.

Com as regras atuais, 19 linhas produzem inevitavelmente um checkpoint de uma linha, sem parâmetro público para ampliá-lo. Reproduzi os riscos empíricos de **28,7% e 10,5%**; não são probabilidades calibradas para estas 19 curvas. Não há uma redução garantida desse risco mantendo também esse protocolo de checkpoint. [budgeted.py:210](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:210).

WEAKENED (corrigir argumento, recuperação de run 2, impedimentos no fechamento e margem/verificação do teto agregado).