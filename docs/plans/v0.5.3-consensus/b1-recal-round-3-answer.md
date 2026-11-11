**As correções estatísticas passaram nas verificações isoladas.** O bootstrap constante agora dá UNRESOLVED; o exemplo 300 + 150 informa disponibilidade `0,667`, sem PASS. A separação dos erros por estimador está correta.

Restam **duas correções na garantia de disco**:

1. **[P2] O limite do manifest mede outra serialização.** [b1_data.py:198](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:198) verifica `json.dumps(manifest)`, mas `write_json` grava JSON indentado. Na prova sintética, **800.011 bytes verificados viraram 2.080.020 bytes gravados**, ultrapassando 1 MiB.

   **Opção conservadora:** serializar uma única vez com o formato efetivamente usado, codificar em UTF-8, verificar esses bytes contra 1 MiB e a quota restante, e gravar exatamente esses bytes.

2. **[P2] Arquivos existentes incorretos ficam fora da reserva inicial.** [b1_data.py:112](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:112) reserva somente arquivos ausentes, mas [b1_data.py:134](/C:/Projetos/refute/docs/validation/v0.5.3/stageB/b1_data.py:134) substitui também os existentes com SHA divergente. Se a substituição aumentar o tamanho, pode consumir o espaço reservado aos manifests; a verificação por arquivo não preserva essa reserva.

   **Opção conservadora:** antes de qualquer escrita, validar SHA e tamanho dos arquivos existentes que serão reutilizados, inclusive origens dos hard links. Qualquer divergência causa **STOP, sem substituição automática nessa execução**.

Não encontrei outro bloqueio nos contrastes, critérios, composição, fingerprint ou divisão dos caps. Mantive a revisão somente leitura, sem adquirir locks ou executar B1.3. O procedimento continua condicionado ao registro no #217 e à liberação do ledger por B1.2.

**WEAKENED (com as duas correções conservadoras de quota aplicadas antes da execução).**

